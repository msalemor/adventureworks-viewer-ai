namespace models;
public record ChatRequest(string input, float temperature = 0.2f, int max_tokens = 500);

public record ChatMessage(string role, string userName, string userId, string content, List<object> columns, List<object> rows);