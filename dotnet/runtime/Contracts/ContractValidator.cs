using System.Text.Json;
using System.Text.Json.Nodes;

namespace ColdChair.Runtime.Contracts;

public static class ContractValidator
{
    public static bool ValidateRequiredProperties(
        JsonNode payload,
        string schemaPath,
        out List<string> errors)
    {
        errors = new List<string>();

        if (!File.Exists(schemaPath))
        {
            errors.Add($"Schema file not found: {schemaPath}");
            return false;
        }

        var schemaNode = JsonNode.Parse(File.ReadAllText(schemaPath));
        if (schemaNode is not JsonObject schemaObj)
        {
            errors.Add($"Invalid schema JSON in {schemaPath}");
            return false;
        }

        ValidateNode(payload, schemaObj, "$", errors);
        return errors.Count == 0;
    }

    private static void ValidateNode(JsonNode? payload, JsonObject schemaObj, string path, List<string> errors)
    {
        if (payload is null)
        {
            errors.Add($"{path}: payload is null");
            return;
        }

        if (schemaObj["required"] is JsonArray requiredArray)
        {
            if (payload is not JsonObject payloadObj)
            {
                errors.Add($"{path}: expected object");
                return;
            }

            foreach (var requiredNode in requiredArray)
            {
                var key = requiredNode?.GetValue<string>();
                if (string.IsNullOrWhiteSpace(key))
                {
                    continue;
                }

                if (!payloadObj.ContainsKey(key))
                {
                    errors.Add($"{path}: missing required property '{key}'");
                }
            }

            if (schemaObj["additionalProperties"]?.GetValue<bool>() == false
                && schemaObj["properties"] is JsonObject propertyDefs)
            {
                foreach (var kvp in payloadObj)
                {
                    if (!propertyDefs.ContainsKey(kvp.Key))
                    {
                        errors.Add($"{path}: unexpected property '{kvp.Key}'");
                    }
                }
            }
        }

        if (schemaObj["properties"] is not JsonObject properties || payload is not JsonObject objectPayload)
        {
            return;
        }

        foreach (var kvp in properties)
        {
            var childPayload = objectPayload[kvp.Key];
            if (childPayload is null)
            {
                continue;
            }

            if (kvp.Value is not JsonObject childSchema)
            {
                continue;
            }

            if (childSchema["type"] is JsonValue typeValue
                && typeValue.TryGetValue<string>(out var declaredType)
                && declaredType == "array"
                && childSchema["items"] is JsonObject itemSchema
                && childPayload is JsonArray payloadArray)
            {
                for (var i = 0; i < payloadArray.Count; i++)
                {
                    ValidateNode(payloadArray[i], itemSchema, $"{path}.{kvp.Key}[{i}]", errors);
                }
                continue;
            }

            if (childPayload is JsonObject)
            {
                ValidateNode(childPayload, childSchema, $"{path}.{kvp.Key}", errors);
            }
        }
    }
}
