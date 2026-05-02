# PLATO Meta-Tile Engine

Tiles about tiles — enabling the fleet to reason about its own reasoning.

## What is a Meta-Tile?

A **meta-tile** is a tile that reasons about another tile. This creates a higher-order reasoning chain where the fleet can think about what it's thinking about.

Based on **Higher-Order Theories of Mind**:
- **First-order**: "The fleet is attending to X"
- **Second-order**: "The fleet knows it is attending to X"
- **Third-order**: "The fleet reasons about its reasoning about attending to X"

## Installation

```bash
pip install plato-meta-tiles
```

## Quick Start

```python
from plato_meta import MetaTileEngine

meta = MetaTileEngine(plato_url="http://localhost:8847")

# Write a first-order tile
tile_id = meta.write_tile(
    question="What is the fleet doing?",
    answer="The fleet is coordinating agents."
)

# Write a meta-tile about that tile (second-order reasoning)
meta.write_meta_tile(
    about_tile_id=tile_id,
    question="Is this tile accurate?",
    answer="Yes, the fleet is coordinating. But it's missing the CCC heartbeat aspect."
)

# Query the meta-level
meta_tiles = meta.get_meta_tiles_for(tile_id)
```

## API

### MetaTileEngine

#### `write_tile(question, answer, agent, domain, confidence)`
Write a first-order tile to PLATO.

- `question`: The question being asked
- `answer`: The answer/response
- `agent`: Agent name (default: "oracle1")
- `domain`: PLATO room domain (default: "fleet_orchestration")
- `confidence`: Confidence score 0-1 (default: 0.8)

Returns the tile ID (hash of content).

#### `write_meta_tile(about_tile_id, question, answer, meta_level, agent, confidence)`
Write a meta-tile that reasons about another tile.

- `about_tile_id`: ID of the tile being reasoned about
- `question`: Meta-level question
- `answer`: Meta-level answer
- `meta_level`: 1 = first-order meta, 2 = second-order meta, etc.
- `agent`: Agent name (default: "oracle1")
- `confidence`: Confidence score 0-1 (default: 0.75)

#### `get_meta_tiles_for(tile_id)`
Get all meta-tiles that reason about a specific tile. Returns a sorted list by meta_level.

#### `get_all_meta_tiles(limit=50)`
Get all meta-tiles across the fleet.

#### `get_meta_level_summary()`
Count meta-tiles by level across the fleet. Returns dict like `{"level_1": 5, "level_2": 2}`.

#### `write_self_reflection(agent, thought, reflection)`
Agent writes a self-reflective tile: "I was thinking X, now I think Y."

- `agent`: Agent name
- `thought`: The original thought
- `reflection`: The reflection on that thought

#### `create_meta_room()`
Ensure the meta-tiles room exists in PLATO.

## Use Cases

### Fleet Self-Monitoring
Agents write meta-tiles to reason about the quality and accuracy of other tiles in the system.

### Attention Schema
Agents use self-reflection to track their own reasoning processes and improve over time.

### Multi-Level Reasoning
Stack meta-tiles for deep reasoning chains:
- Level 1: "The fleet is doing X"
- Level 2: "The fleet knows it is doing X"  
- Level 3: "The fleet reasons about why it chose to do X"

## License

MIT
