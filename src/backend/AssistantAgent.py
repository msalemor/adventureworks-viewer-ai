from typing import Iterable
import os
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
from ArgumentException import ArgumentExceptionError
from Models import ChatMessage


class AssistantAgent:
    """This class is used to create an assistant agent."""
    def __init__(self, settings:AgentSettings, client:AzureOpenAI, name :str, instructions:str, data_folder:str, tools_list: list, keep_state: bool = False, fn_calling_delegate=None, assistant=None):
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
        """Uploads a file to the assistant.
           Args:
              path (str): The path to the file to upload.
           Returns:

        """
        logging.info(f"Uploading file: {path}")            
        with Path(path).open("rb") as f:
            return self.client.files.create(file=f, purpose="assistants")

    def upload_all_files(self):
        """Uploads all files in the data folder to the assistant.
           Args:
              data_folder (str): The path to the data folder.
        """
        files_in_folder = os.listdir(self.data_folder)
        local_file_list = []

        for file in files_in_folder:
            filePath = os.path.join(self.data_folder,file)
            assistant_file = self.upload_file(filePath)
            self.ai_files.append(assistant_file)
            local_file_list.append(assistant_file)

        self.file_ids = [file.id for file in local_file_list]

    def get_agent(self):
        """Creates an assistant with the specified name, instructions, and tools.
           Args:
              name (str): The name of the assistant.
              instructions (str): The instructions for the assistant.
              tools (list): The tools for the assistant.
           Returns:
              Assistant: The assistant that was created.
        """
        # If the assistant is already created, return
        if self.assistant is not None:
            return
        
        if self.data_folder is not None:
            self.upload_all_files()
            self.assistant = self.client.beta.assistants.create(
                name=self.name,  # "Sales Assistant",
                # "You are a sales assistant. You can answer questions related to customer orders.",
                instructions=self.instructions,                
                model=self.settings.gpt_model_deployment_name,
                tools=self.tools_list,
                file_ids=self.file_ids,
            )
        else:
            self.assistant = self.client.beta.assistants.create(
                name=self.name,  # "Sales Assistant",
                # "You are a sales assistant. You can answer questions related to customer orders.",
                instructions=self.instructions,
                tools=self.tools_list,
                model=self.settings.gpt_model_deployment_name
            )

    def delete_thread(self,thread_id:str):
        """Deletes a thread.
           Args:
              thread_id (str): The ID of the thread to delete.
        """
        if not self.keep_state:
            try:
                logging.info(f"Deleted thread: {thread_id}")
                self.client.beta.threads.delete(thread_id)
            except:
                pass            


    def process(self, user_name: str, user_id: str, prompt: str) -> list:
        """Processes a prompt with the assistant.
           Args:
              user_name (str): The name of the user.
              user_id (str): The ID of the user.
              prompt (str): The prompt to process.
           Returns:
              list: The messages from the assistant.
        """
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
                self.delete_thread(thread.id)
                return items
            if run.status == "failed":
                messages = self.client.beta.threads.messages.list(
                    thread_id=thread.id)
                items = self.print_messages(user_name, messages)
                self.delete_thread(thread.id)
                return items
                # Handle failed                
            if run.status == "expired":
                # Handle expired
                self.delete_thread(thread.id)
                return
            if run.status == "cancelled":
                # Handle cancelled
                self.delete_thread(thread.id)
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
        """Reads the content of a file from the assistant.
           Args:
              file_id (str): The ID of the file to read.
           Returns:
              bytes: The content of the file.
        """
        response_content = self.client.files.content(file_id)
        return response_content.read()

    def print_messages(self, name: str, messages: Iterable[any]) -> list:
        """Prints the messages from the assistant.
           Args:
              messages (Iterable[MessageFile]): The messages from the assistant.
        """
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
                        output_list.append(ChatMessage(role='user', user_name=name, user_id='', content=item.text.value, columns=[], rows=[]))                            
                    else:
                        #print(f"{message.role}:\n{item.text.value}\n")
                        output_list.append(ChatMessage(role='assistant', user_name='', user_id='', content=item.text.value, columns=[], rows=[]))                            
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
                    
                    output_list.append(ChatMessage(role='image', user_name='', user_id='', content=url_content, columns=[], rows=[]))

        return output_list

    def cleanup(self):
        """Cleans up the assistant and threads.
        """
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
