# Safety Constraints

## Prohibited Techniques
- Process injection into Warcraft III.
- Memory editing or direct game state reads from process memory.
- Anti-cheat bypass or tampering.
- Unattended live matchmaking operation.

## Allowed Techniques in MVP
- Replay analysis.
- Offline and local AI match experimentation.
- Supervised dry-runs without queue automation.

## Runtime Safeguards
- Manual kill switch must always be available.
- Active-window checks before any control action.
- Rate-limited control actions.
- Explicit mode flag to block online queue behavior.
