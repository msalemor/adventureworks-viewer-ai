using System.Text;
using System.Text.Json;
using Azure;
using Azure.AI.OpenAI.Assistants;
using models;

namespace agents;

public delegate ToolOutput GetResolvedToolOutput(RequiredToolCall toolCall);

public class AssistantsAPIAgent : IAgent
{
    public AgentSettings Settings { get; set; }
    public AssistantsClient Client { get; set; }
    public Assistant Assistant { get; set; } = null!;
    public KCVStore KCVStore { get; set; } = null!;
    public GetResolvedToolOutput? GetResolvedToolOutput { get; set; }
    public bool KeepState { get; set; } = false;

    public AssistantsAPIAgent(AgentSettings? settings, AssistantsClient? client, KCVStore kCVStore)
    {
        Settings = settings ?? new AgentSettings();
        Client = client ?? new AssistantsClient(new Uri(Settings.API_Endpoint), new AzureKeyCredential(Settings.API_Key));
        KCVStore = kCVStore;
    }

    private async Task<List<OpenAIFile>> FileIdsInFolder(string folder)
    {
        List<OpenAIFile> fileIds = [];
        foreach (var file in Directory.GetFiles(folder))
        {
            Response<OpenAIFile> uploadAssistantFileResponse = await Client.UploadFileAsync(
                localFilePath: file,
                purpose: OpenAIFilePurpose.Assistants);
            fileIds.Add(uploadAssistantFileResponse.Value);
        }
        return fileIds;
    }

    public async Task<BinaryData> GetFileContent(string id)
    {
        var fileContentResponse = await Client.GetFileContentAsync(id);
        var fileContent = fileContentResponse.Value;
        return fileContent;
    }

    public async Task CreateAssistantAsync(string assistant_name, string instructions, List<ToolDefinition> tools, string? fileFolder, bool keepState = false)
    {
        var opts = new AssistantCreationOptions(Settings.GPT_Model_Deployment_Name)
        {
            Name = assistant_name,
            Instructions = instructions
        };

        if (tools.Count == 0)
        {
            tools.Add(new CodeInterpreterToolDefinition());
        }
        else
        {
            foreach (var tool in tools)
            {
                opts.Tools.Add(tool);
            }
        }

        if (fileFolder is not null)
        {
            var files = await FileIdsInFolder(fileFolder);
            foreach (var file in files)
            {
                opts.FileIds.Add(file.Id);
            }
            await KCVStore.Set("assistant", "files", JsonSerializer.Serialize(files));
        }

        Response<Assistant> assistantResponse = await Client.CreateAssistantAsync(
            opts
        );

        await KCVStore.Set("assistant", "id", assistantResponse.Value.Id);

        Assistant = assistantResponse.Value;
    }


    private async Task<List<ChatMessage>> ProcessMessagesAsync(IReadOnlyList<ThreadMessage> messages)
    {
        List<ThreadMessage> localList = [];
        foreach (ThreadMessage threadMessage in messages)
        {
            localList.Add(threadMessage);
            if (threadMessage.Role == "user")
            {
                break;
            }
        }
        localList.Reverse();

        List<ChatMessage> chatMessages = [];

        // Note: messages iterate from newest to oldest, with the messages[0] being the most recent
        foreach (ThreadMessage threadMessage in localList)
        {
            //Console.Write($"{threadMessage.CreatedAt:yyyy-MM-dd HH:mm:ss} - {threadMessage.Role,10}: ");
            foreach (MessageContent contentItem in threadMessage.ContentItems)
            {
                if (contentItem is MessageTextContent textItem)
                {
                    //Console.Write(textItem.Text);
                    chatMessages.Add(new ChatMessage(threadMessage.Role.ToString(), "", "", textItem.Text, [], []));
                    var annotations = textItem.Annotations;
                    if (annotations != null && annotations.Count > 0)
                    {
                        foreach (var annotation in annotations)
                        {
                            if (annotation is MessageTextFileCitationAnnotation textCitation)
                            {
                                chatMessages.Add(new ChatMessage(threadMessage.Role.ToString(), "", "", textCitation.Text, [], []));
                            }
                            else if (annotation is MessageTextFilePathAnnotation filCitation)
                            {
                                var content = await GetFileContent(filCitation.FileId);
                                if (content is not null)
                                {
                                    chatMessages.Add(new ChatMessage(threadMessage.Role.ToString(), "", "", Encoding.UTF8.GetString(content), [], []));
                                }
                            }
                        }
                    }

                }
                else if (contentItem is MessageImageFileContent imageFileItem)
                {
                    // If it is an image
                    // Save the file to a URL and return the URL

                    // Get the image content
                    var imageBytes = await GetFileContent(imageFileItem.FileId);

                    // Create a folder to save the image
                    const string imageFolder = "wwwroot/images";
                    var imageFolderExists = Directory.Exists(imageFolder);
                    if (!imageFolderExists)
                    {
                        Directory.CreateDirectory(imageFolder);
                    }

                    // Create a file name and a full path
                    var fileName = new Guid().ToString() + ".png";
                    var fullFilePath = Path.Combine(imageFolder, fileName);

                    if (imageBytes is not null)
                    {
                        // Save the image to the file
                        await File.WriteAllBytesAsync(fullFilePath, imageBytes.ToArray());

                        // Return the URL
                        var urlContent = $"/images/{fileName}";
                        chatMessages.Add(new("image", "", "", urlContent, [], []));
                    }

                }
            }
        }
        return chatMessages;
    }


    public async Task<List<ChatMessage>> ProcessAsync(string user_name, string user_id, string prompt, int max_tokens = 500, float temperature = 0.3f, string context = "")
    {
        // Create a thread
        Response<AssistantThread> threadResponse = await Client.CreateThreadAsync();
        AssistantThread thread = threadResponse.Value;

        // Create a message
        Response<ThreadMessage> messageResponse = await Client.CreateMessageAsync(
        thread.Id,
        MessageRole.User,
        prompt);
        ThreadMessage message = messageResponse.Value;

        // Create a run
        // Response<ThreadRun> runResponse = await Client.CreateRunAsync(
        //     thread.Id,
        //     new CreateRunOptions(Assistant.Id)
        //     {
        //         AdditionalInstructions = "Please address the user as Jane Doe. The user has a premium account.",
        //     });
        // Create a run
        Response<ThreadRun> runResponse = await Client.CreateRunAsync(thread, Assistant);
        ThreadRun run = runResponse.Value;

        // Process the run
        do
        {
            await Task.Delay(TimeSpan.FromMilliseconds(500));
            runResponse = await Client.GetRunAsync(thread.Id, runResponse.Value.Id);

            if (GetResolvedToolOutput is null) continue;

            // Process function calling
            if (runResponse.Value.Status == RunStatus.RequiresAction
                && runResponse.Value.RequiredAction is SubmitToolOutputsAction submitToolOutputsAction)
            {
                List<ToolOutput> toolOutputs = [];
                foreach (RequiredToolCall toolCall in submitToolOutputsAction.ToolCalls)
                {
                    toolOutputs.Add(GetResolvedToolOutput(toolCall));
                }
                runResponse = await Client.SubmitToolOutputsToRunAsync(runResponse.Value, toolOutputs);
            }
        }
        while (runResponse.Value.Status == RunStatus.Queued
            || runResponse.Value.Status == RunStatus.InProgress);

        // Process the result
        Response<PageableList<ThreadMessage>> afterRunMessagesResponse = await Client.GetMessagesAsync(thread.Id);
        IReadOnlyList<ThreadMessage> messages = afterRunMessagesResponse.Value.Data;

        // // Note: messages iterate from newest to oldest, with the messages[0] being the most recent
        // foreach (ThreadMessage threadMessage in messages)
        // {
        //     Console.Write($"{threadMessage.CreatedAt:yyyy-MM-dd HH:mm:ss} - {threadMessage.Role,10}: ");
        //     foreach (MessageContent contentItem in threadMessage.ContentItems)
        //     {
        //         if (contentItem is MessageTextContent textItem)
        //         {
        //             Console.Write(textItem.Text);
        //         }
        //         else if (contentItem is MessageImageFileContent imageFileItem)
        //         {
        //             Console.Write($"<image from ID: {imageFileItem.FileId}");
        //         }
        //         Console.WriteLine();
        //     }
        // }

        var chatMessages = await ProcessMessagesAsync(messages);

        // Delete the thread
        if (!KeepState)
        {
            try
            {
                await Client.DeleteThreadAsync(thread.Id);
            }
            catch (RequestFailedException ex)
            {
                Console.WriteLine($"Failed to delete thread: {ex.Message}");
            }
        }


        return chatMessages;
    }

    public async Task CleanupAsync()
    {
        try
        {
            var id = await KCVStore.Get("assistant", "id");
            await Client.DeleteAssistantAsync(id);
        }
        catch (RequestFailedException ex)
        {
            Console.WriteLine($"Failed to delete assistant: {ex.Message}");
        }
        try
        {
            var filesJson = await KCVStore.Get("assistant", "files");
            if (string.IsNullOrEmpty(filesJson)) return;
            var files = JsonSerializer.Deserialize<List<OpenAIFile>>(filesJson);
            if (files is not null && files.Count > 0)
                foreach (var file in files)
                {
                    await Client.DeleteFileAsync(file.Id);
                }
        }
        catch (RequestFailedException ex)
        {
            Console.WriteLine($"Failed to delete files: {ex.Message}");
        }
    }
}