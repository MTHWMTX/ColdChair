"""Guide: Importing Warcraft III Replay Data for Training

This guide walks you through downloading and importing professional replay data
from Warcraft III community sources into your training system.

## Quick Start

The fastest way to set up training with replay data:

1. **Download replays** (see sources below)
2. **Extract game states** from replay files
3. **Register as dataset** for training
4. **Start training** with one command

## Replay Sources

### 📺 epicwar.com
- **URL**: https://epicwar.com/replays
- **Type**: Community replay database
- **Quality**: Professional tournaments, professional players
- **Download**: Use filter for "tournament" or "pro player" replays
- **Format**: .w3g files

**How to download:**
1. Go to https://epicwar.com/replays
2. Filter by map, player, or tournament
3. Download .w3g files
4. Place in a local directory (e.g., `replays/epicwar/`)

### 🎮 eso.gg
- **URL**: https://eso.gg/replays
- **Type**: Ranked ladder replays
- **Quality**: Competitive games, pro matches
- **Download**: May require account; check their ToS
- **Format**: .w3g files

**How to download:**
1. Go to https://eso.gg/replays
2. Browse recent or pro player replays
3. Download and save to directory (e.g., `replays/eso/`)

### 🏆 Tournament Archives
Other sources:
- **WCG Archives**: WC3 World Cup replays
- **BlizzCon VODs**: Occasional professional replays
- **Personal Replays**: Your own Battle.net games (once integrated)

## Importing Replays

### Option 1: Extract Single Replay

Extract game states from a single .w3g file:

```bash
python -m python.replay.import_replays extract path/to/replay.w3g
```

This creates `replay.json` with extracted game states.

### Option 2: Batch Import Directory

Convert all replays in a directory:

```bash
python -m python.replay.import_replays batch path/to/replay/directory
```

Creates `path/to/replay/directory/extracted_states.json` with all game states.

### Option 3: Using Import Tool Programmatically

```python
from pathlib import Path
from python.replay.import_replays import import_replays_from_directory

# Convert all replays in directory
count = import_replays_from_directory(
    replay_dir=Path("replays/epicwar"),
    output_file=Path("datasets/epicwar_replays.json"),
    tag="epicwar"
)
print(f"Extracted {count} game states")
```

## Workflow: Download → Extract → Train

### Step 1: Create Replay Directory

```bash
mkdir replays/epicwar
mkdir replays/eso
```

### Step 2: Download Replays

Download .w3g files from epicwar.com or eso.gg into these directories.

### Step 3: Extract Game States

```bash
# Extract from epicwar replays
python -m python.replay.import_replays batch replays/epicwar \
  -o datasets/epicwar_extracted.json \
  -t "epicwar"

# Extract from eso replays
python -m python.replay.import_replays batch replays/eso \
  -o datasets/eso_extracted.json \
  -t "eso"
```

### Step 4: Register as Datasets

```bash
# Register epicwar dataset
python -m python.replay.import_replays register datasets/epicwar_extracted.json \
  --dataset-id epicwar_pro \
  --name "Professional Replays from epicwar" \
  --tags "epicwar,professional"

# Register eso dataset
python -m python.replay.import_replays register datasets/eso_extracted.json \
  --dataset-id eso_ladder \
  --name "Competitive Replays from eso.gg" \
  --tags "eso,competitive"
```

### Step 5: Train Policy on Real Data

```bash
# Create or update policy version
python -m python.training.orchestrate init-policy \
  --version v2.0 \
  --description "Trained on professional replays"

# Train on real replay data
python -m python.training.orchestrate train \
  --policy-version v2.0 \
  --dataset-id epicwar_pro
```

### Step 6: Compare Results

```bash
python -m python.training.orchestrate status
```

Shows:
- Best performing policy version
- Metrics from training runs
- Historical accuracy/execution rates

## Advanced: Combine Multiple Sources

### Mixed Dataset Training

```bash
# Extract from multiple sources
python -m python.replay.import_replays batch replays/epicwar -o data1.json
python -m python.replay.import_replays batch replays/eso -o data2.json

# Merge datasets
python -c "
import json
data1 = json.load(open('data1.json'))
data2 = json.load(open('data2.json'))
combined = data1 + data2
json.dump(combined, open('datasets/all_pro_replays.json', 'w'), indent=2)
"

# Register combined dataset
python -m python.replay.import_replays register datasets/all_pro_replays.json \
  --dataset-id all_pro \
  --name "All Professional Replays" \
  --tags "professional,combined"
```

## Testing & Validation

### Quick Test: Parse Single Replay

```python
from python.replay.w3g_parser import W3GParser

parser = W3GParser()
result = parser.parse("path/to/replay.w3g")
samples = parser.to_game_state_samples(result)

print(f"Extracted {len(samples)} game states")
print(f"First state: tick={samples[0]['tick']}, gold={samples[0]['resources']['gold']}")
```

### Verify Extracted States

```python
import json
from pathlib import Path

# Load extracted states
states = json.load(open("datasets/extracted.json"))

print(f"Total states: {len(states)}")
print(f"Sample structure: {states[0]}")

# Check contract compliance
from jsonschema import validate
from python.contracts import game_state_schema

for i, state in enumerate(states[:5]):
    validate(instance=state, schema=game_state_schema())
    print(f"State {i}: ✓")
```

## Troubleshooting

### "No replay files found"
- Check directory path is correct
- Ensure .w3g or .json files are present
- Use absolute path: `python -m python.replay.import_replays batch /full/path/to/replays`

### "Failed to parse replay"
- Some .w3g files may be corrupted or very old format
- Parser generates synthetic fallback states
- Check parser logs for specific error

### "No game states extracted"
- Verify replay file is valid Warcraft III replay
- Try manual test: `python -c "from python.replay.w3g_parser import W3GParser; print(W3GParser().parse('file.w3g'))"`

### Dataset registration fails
- Verify extracted JSON file exists and is readable
- Check dataset directory has write permissions
- Ensure dataset-id is unique (no spaces or special chars)

## Next Steps

Once training is working with real replay data:

1. **Iterate on policies**: Create new versions with different parameters
2. **A/B test**: Compare versions on same dataset
3. **Expand data**: Add more replays for better coverage
4. **Local testing**: Phase 6 integration for local game loop
5. **Live deployment**: Phase 7 Battle.net live testing

## File Structure

After importing replays:

```
project2/
├── replays/
│   ├── epicwar/          # Downloaded .w3g files
│   └── eso/
├── datasets/
│   ├── epicwar_extracted.json      # Extracted states
│   ├── eso_extracted.json
│   ├── all_pro_replays.json        # Combined
│   └── index.json                  # Dataset metadata
├── policies/
│   ├── v1.0.json                   # Baseline policy
│   └── v2.0.json                   # Trained on pro replays
└── reports/
    ├── training_log.json           # Training history
    └── training_result_v2.0.json   # Metrics from v2.0 training
```

## Performance Tips

- **Batch download**: Download 10-20 replays at a time to populate datasets
- **Incremental training**: Start with 5 replays, expand to 50+
- **Dataset organization**: Use tags (epicwar, eso, tournament, ladder) for tracking
- **Monitor metrics**: Check training_log.json for convergence

## Legal/Safety Notes

- **Personal use**: Downloading replays for personal training is typically allowed
- **ToS compliance**: Check website ToS before bulk downloading
- **Rate limiting**: Space out downloads to avoid rate limits
- **Attribution**: Consider noting source when sharing results

Good luck with your training! 🎮
"""

# This module serves as documentation; run from CLI directly
