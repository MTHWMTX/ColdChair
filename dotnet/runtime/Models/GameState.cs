using System.Text.Json.Serialization;

namespace ColdChair.Runtime.Models;

public sealed class GameState
{
    [JsonPropertyName("tick")]
    public int Tick { get; init; }

    [JsonPropertyName("resources")]
    public required ResourceState Resources { get; init; }

    [JsonPropertyName("supply")]
    public required SupplyState Supply { get; init; }

    [JsonPropertyName("units")]
    public required List<UnitState> Units { get; init; }
}

public sealed class ResourceState
{
    [JsonPropertyName("gold")]
    public int Gold { get; init; }

    [JsonPropertyName("lumber")]
    public int Lumber { get; init; }
}

public sealed class SupplyState
{
    [JsonPropertyName("used")]
    public int Used { get; init; }

    [JsonPropertyName("cap")]
    public int Cap { get; init; }
}

public sealed class UnitState
{
    [JsonPropertyName("id")]
    public required string Id { get; init; }

    [JsonPropertyName("owner")]
    public required string Owner { get; init; }

    [JsonPropertyName("type")]
    public required string Type { get; init; }

    [JsonPropertyName("hp")]
    public double Hp { get; init; }

    [JsonPropertyName("position")]
    public required UnitPosition Position { get; init; }
}

public sealed class UnitPosition
{
    [JsonPropertyName("x")]
    public double X { get; init; }

    [JsonPropertyName("y")]
    public double Y { get; init; }
}
