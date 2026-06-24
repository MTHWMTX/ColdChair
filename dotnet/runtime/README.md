# Runtime Module (C#)

This folder contains the C# runtime parity skeleton.

Implemented components:
- Contract-aligned models for game state and action intent.
- Schema-aware validator that checks required and unexpected properties.
- CLI entry points for validating payloads against shared contracts.

## Build

```bash
dotnet build dotnet/runtime/ColdChair.Runtime.csproj -c Release
```

## Validate Contracts

```bash
dotnet run --project dotnet/runtime/ColdChair.Runtime.csproj -- validate-game-state --file examples/sample_game_state.json
dotnet run --project dotnet/runtime/ColdChair.Runtime.csproj -- validate-action-intent --file examples/sample_action_intent.json
```

This module remains local and supervised during MVP.
