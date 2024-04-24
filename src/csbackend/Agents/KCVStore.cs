namespace agents;
using Microsoft.Data.Sqlite;

public class KCVStore(string connStr)
{
    public string CONNECTION_STRING { get; set; } = connStr;

    public async Task<string> Get(string key, string category)
    {
        using var conn = new SqliteConnection(CONNECTION_STRING);
        await conn.OpenAsync();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"
            SELECT value FROM kcvstore WHERE key = @key AND category = @category
        ";
        cmd.Parameters.AddWithValue("@key", key);
        cmd.Parameters.AddWithValue("@category", category);
        var row = cmd.ExecuteScalar();
        return row?.ToString() ?? string.Empty;
    }

    public async Task Set(string key, string category, string value)
    {
        using var conn = new SqliteConnection(CONNECTION_STRING);
        await conn.OpenAsync();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"
            INSERT OR REPLACE INTO kcvstore (key, category, value)
            VALUES (@key, @category, @value)
        ";
        cmd.Parameters.AddWithValue("@key", key);
        cmd.Parameters.AddWithValue("@category", category);
        cmd.Parameters.AddWithValue("@value", value);
        cmd.ExecuteNonQuery();
    }

    public async Task Delete(string key, string category)
    {
        using var conn = new SqliteConnection(CONNECTION_STRING);
        await conn.OpenAsync();
        using var cmd = conn.CreateCommand();
        cmd.CommandText = @"
            DELETE FROM kcvstore WHERE key = @key AND category = @category
        ";
        cmd.Parameters.AddWithValue("@key", key);
        cmd.Parameters.AddWithValue("@category", category);
        cmd.ExecuteNonQuery();
    }
}
