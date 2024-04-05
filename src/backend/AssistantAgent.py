from typing import Iterable
import os
import io
import uuid
import time
import logging
from datetime import datetime
from pathlib import Path
from AgentSettings import AgentSettings

from openai import AzureOpenAI
from openai.types.beta.assistant import Assistant
from openai.types.beta.threads.text_content_block import TextContentBlock
from openai.types.beta.threads.image_file_content_block import ImageFileContentBlock
from openai.types.beta.threads.messages import MessageFile
from openai.types import FileObject
from PIL import Image
from ArgumentException import ArgumentExceptionError


class AssistantAgent:
    def __init__(self, settings:AgentSettings, client:AzureOpenAI, name :str, instructions:str, data_folder:str, tools_list, keep_state: bool = False, fn_calling_delegate=None, assistant=None):
        if name is None:
            raise ArgumentExceptionError("name parameter missing")
        if instructions is None:
            raise ArgumentExceptionError("instructions parameter missing")
        if tools_list is None:
            raise ArgumentExceptionError("tools_list parameter missing")

        self.assistant :Assistant = assistant
        self.settings : AgentSettings= settings
        self.client : AzureOpenAI = client
        self.name = name
        self.instructions = instructions
        self.data_folder = data_folder
        self.tools_list = tools_list
        self.fn_calling_delegate = fn_calling_delegate
        self.keep_state = keep_state
        self.ai_threads = []
        self.ai_files = []
        self.file_ids = []
        self.get_agent()

    def upload_file(self, path: str) -> FileObject:
        print(path)
        with Path(path).open("rb") as f:
            return self.client.files.create(file=f, purpose="assistants")

    def upload_all_files(self):
        files_in_folder = os.listdir(self.data_folder)
        local_file_list = []

        for file in files_in_folder:
            filePath = os.path.join(self.data_folder,file)
            assistant_file = self.upload_file(filePath)
            self.ai_files.append(assistant_file)
            local_file_list.append(assistant_file)

        self.file_ids = [file.id for file in local_file_list]

    def get_agent(self):
        # If the assistant is already created, return
        if self.assistant is not None:
            return
        
        if self.data_folder is not None:
            self.upload_all_files()
            self.assistant = self.client.beta.assistants.create(
                name=self.name,  # "Sales Assistant",
                # "You are a sales assistant. You can answer questions related to customer orders.",
                instructions=self.instructions,
                tools=self.tools_list,
                model=self.settings.model_deployment,
                file_ids=self.file_ids
            )
        else:
            self.assistant = self.client.beta.assistants.create(
                name=self.name,  # "Sales Assistant",
                # "You are a sales assistant. You can answer questions related to customer orders.",
                instructions=self.instructions,
                tools=self.tools_list,
                model=self.settings.model_deployment
            )

    def delete_thread(self,thread):
        if not self.keep_state:
            self.client.beta.threads.delete(thread.id)
            logging.info("Deleted thread: ", thread.id)



    def process_prompt(self, user_name: str, user_id: str, prompt: str) -> list:

        # if keep_state:
        #     thread_id = check_if_thread_exists(user_id)

        #     # If a thread doesn't exist, create one and store it
        #     if thread_id is None:
        #         print(f"Creating new thread for {name} with user_id {user_id}")
        #         thread = self.client.beta.threads.create()
        #         store_thread(user_id, thread)
        #         thread_id = thread.id
        #     # Otherwise, retrieve the existing thread
        #     else:
        #         print(
        #             f"Retrieving existing thread for {name} with user_id {user_id}")
        #         thread = self.client.beta.threads.retrieve(thread_id)
        #         add_thread(thread)
        # else:
        thread = self.client.beta.threads.create()

        self.client.beta.threads.messages.create(
            thread_id=thread.id, role="user", content=prompt)

        run = self.client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=self.assistant.id,
            instructions= "The current date and time is: " + datetime.now().strftime("%x %X") + ".",
        )

        #print("processing ...")
        while True:
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread.id, run_id=run.id)
            if run.status == "completed":
                # Handle completed
                messages = self.client.beta.threads.messages.list(
                    thread_id=thread.id)
                items= self.print_messages(user_name, messages)                
                self.delete_thread(thread)
                return items
            if run.status == "failed":
                messages = self.client.beta.threads.messages.list(
                    thread_id=thread.id)
                items = self.print_messages(user_name, messages)
                self.delete_thread(thread)
                return items
                # Handle failed                
            if run.status == "expired":
                # Handle expired
                self.delete_thread(thread)
                return
            if run.status == "cancelled":
                # Handle cancelled
                self.delete_thread(thread)
                return
            if run.status == "requires_action":
                if self.fn_calling_delegate:
                    self.fn_calling_delegate(self.client, thread, run)
            else:
                time.sleep(5)

        if not self.keep_state:
            self.client.beta.threads.delete(thread.id)
            print("Deleted thread: ", thread.id)

    def read_assistant_file(self, file_id: str):
        response_content = self.client.files.content(file_id)
        return response_content.read()

    def print_messages(self, name: str, messages: Iterable[MessageFile]) -> list:
        message_list = []

        # Get all the messages till the last user message
        for message in messages:
            message_list.append(message)
            if message.role == "user":
                break

        # Reverse the messages to show the last user message first
        message_list.reverse()
        output_list = []

        # Print the user or Assistant messages or images
        for message in message_list:
            for item in message.content:
                # Determine the content type
                logging.info(type(item))
                if isinstance(item, TextContentBlock):
                    if message.role == "user":
                        #print(f"user: {name}:\n{item.text.value}\n")
                        #{'role':'assistant','user_name':user_name,'user_id':user_id,'content':content,'columns':[],'rows':[]}
                        #output_list.append({"role": "user", "content": item.text.value})
                        output_list.append({'role':'user','user_name':'','user_id':'','content':item.text.value,'columns':[],'rows':[]})
                    else:
                        #print(f"{message.role}:\n{item.text.value}\n")
                        output_list.append({'role':'assistant','user_name':'','user_id':'','content':item.text.value,'columns':[],'rows':[]})
                    file_annotations = item.text.annotations
                    if file_annotations:
                        for annotation in file_annotations:
                            file_id = annotation.file_path.file_id
                            content = self.read_assistant_file(file_id)
                            print(f"Annotation Content:\n{str(content)}\n")
                elif isinstance(item, ImageFileContentBlock):
                    # Retrieve image from file id
                    data_in_bytes = self.read_assistant_file(
                        item.image_file.file_id)
                    # Convert bytes to image
                    #readable_buffer = io.BytesIO(data_in_bytes)
                    # write bytes to file

                    # create a folder if it does not exit
                    image_folder_path = "wwwroot/images"
                    if not os.path.exists(image_folder_path):
                        os.makedirs(image_folder_path)

                    # create a file
                    file_name = uuid.uuid4().hex + ".png"
                    fullFilePath = os.path.join(image_folder_path, file_name)
                    
                    with open(fullFilePath, "wb") as f:
                        f.write(data_in_bytes)

                    url_content = f"/images/{file_name}"
                    output_list.append({'role':'image','user_name':'','user_id':'','content':url_content,'columns':[],'rows':[]})
        return output_list

    def cleanup(self):
        try:
            print(self.client.beta.assistants.delete(self.assistant.id))
            print("Deleting: ", len(self.ai_threads), " threads.")
        except:
            print("Error deleting assistant")
        try:
            for thread in self.ai_threads:
                print(self.client.beta.threads.delete(thread.id))
        except:
            print("Error delete threads")
        try:
            print("Deleting: ", len(self.ai_files), " files.")
            for file in self.ai_files:
                print(self.client.files.delete(file.id))
        except:
            print("Error deleting files")
