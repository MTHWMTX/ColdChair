using System.Text.Json.Serialization;

namespace ColdChair.Runtime.Models;

public sealed class ActionIntent
{
    [JsonPropertyName("type")]
    public required string Type { get; init; }

    [JsonPropertyName("priority")]
    public int Priority { get; init; }

    [JsonPropertyName("target_id")]
    public string? TargetId { get; init; }

    [JsonPropertyName("position")]
    public ActionPosition? Position { get; init; }
}

public sealed class ActionPosition
{
    [JsonPropertyName("x")]
    public double X { get; init; }

    [JsonPropertyName("y")]
    public double Y { get; init; }
}
