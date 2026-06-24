using System.Text.Json;
using System.Text.Json.Nodes;
using ColdChair.Runtime.Contracts;
using ColdChair.Runtime.Models;

var usage = "Usage: dotnet run --project dotnet/runtime -- [validate-game-state|validate-action-intent] --file <json-file>";

if (args.Length < 3 || args[1] != "--file")
{
    Console.WriteLine(usage);
    return 1;
}

var mode = args[0];
var filePath = args[2];

if (!File.Exists(filePath))
{
    Console.WriteLine($"Input file not found: {filePath}");
    return 1;
}

var repoRoot = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "..", "..", "..", "..", ".."));
var contractsRoot = Path.Combine(repoRoot, "contracts");

var json = File.ReadAllText(filePath);
JsonNode? payloadNode = JsonNode.Parse(json);

if (payloadNode is null)
{
    Console.WriteLine("Invalid JSON payload.");
    return 1;
}

switch (mode)
{
    case "validate-game-state":
    {
        var state = JsonSerializer.Deserialize<GameState>(json);
        if (state is null)
        {
            Console.WriteLine("Could not deserialize GameState payload.");
            return 1;
        }

        var schemaPath = Path.Combine(contractsRoot, "game_state.schema.json");
        var valid = ContractValidator.ValidateRequiredProperties(payloadNode, schemaPath, out var errors);
        if (!valid)
        {
            Console.WriteLine("GameState contract validation failed:");
            foreach (var error in errors)
            {
                Console.WriteLine($"- {error}");
            }
            return 1;
        }

        Console.WriteLine("GameState contract validation passed.");
        return 0;
    }

    case "validate-action-intent":
    {
        var intent = JsonSerializer.Deserialize<ActionIntent>(json);
        if (intent is null)
        {
            Console.WriteLine("Could not deserialize ActionIntent payload.");
            return 1;
        }

        var schemaPath = Path.Combine(contractsRoot, "action_intent.schema.json");
        var valid = ContractValidator.ValidateRequiredProperties(payloadNode, schemaPath, out var errors);
        if (!valid)
        {
            Console.WriteLine("ActionIntent contract validation failed:");
            foreach (var error in errors)
            {
                Console.WriteLine($"- {error}");
            }
            return 1;
        }

        Console.WriteLine("ActionIntent contract validation passed.");
        return 0;
    }

    default:
        Console.WriteLine(usage);
        return 1;
}
