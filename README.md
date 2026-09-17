# OtherChess AI Service

A Python (FastAPI) service that chooses moves for [OtherChess](https://otherchess.com), a chess variant played on configurable boards with walls, upgrade squares, and omnidirectional pawns. The rules are in [RULES.md](RULES.md). The game itself is a separate Rails application; it calls this service over HTTP and falls back to its own Ruby AI if the service is unavailable.

## Goal

A correct move generator for the variant rules, and on top of it a basic, functional, variable depth minimax (alpha beta) player with a time budget. The current code does not reach that goal: it is a one ply evaluator ported from the Ruby AI, the move generator is missing several variant rules, and the tests do not agree with the rules. See [Status](#status).

## Quickstart

```bash
make setup     # pip install -r requirements.txt -r requirements-dev.txt
make test      # pytest
make run       # python main.py, serves on http://localhost:8000
```

Python 3.10 or newer. No environment variables, no database, no external services.

## Status

What works and what does not, measured against [RULES.md](RULES.md).

| Area | State |
| --- | --- |
| Board model (`models.py`) | Pieces, walls, upgrade squares, bounds and duplicate checks. Uses Pydantic v1 style validators, which warn under Pydantic 2. |
| Move generation (`ai_base.py`) | Pawn single step in four cardinal directions and diagonal capture; sliding pieces stopped by walls; knight; king single step. Missing: pawn two square first move, promotion on upgrade squares, castling. |
| Move validation (`AIEngine.validate_move`) | Implements standard chess pawn rules, which contradict the variant. Not exposed by any endpoint. |
| `greedy` | Picks the highest material capture. Works. |
| `smart2` | One ply heuristic evaluation. Works but shallow. |
| `smart_fast` | Exists with its own tests but is not registered with the engine or accepted by the API. |
| `random` | `ai_random.py` is empty. |
| Search | No lookahead of any depth. |
| Tests | `pytest` on a clean checkout: 2 failed, 2 passed. The failures reference a side (`BLACK`) that does not exist. Coverage of the variant rules is thin. |

## Layout

```
main.py             FastAPI app: /health, /api/v1/ai/types, /api/v1/ai/move
models.py           Pydantic models: BoardState, Piece, Wall, UpgradeSquare, Move, MoveRequest, MoveResponse
ai_engine.py        AIEngine: routes ai_type to an AI class, converts results, validate_move
ai_base.py          AIBase: occupancy registry, move generation per piece type, material scoring
ai_greedy.py        AiGreedy
ai_smart2.py        AiSmart2 (default)
ai_smart_fast.py    AiSmartFast (not registered)
ai_random.py        empty
test_ai.py          engine and board validation tests
test_smart_fast.py  AiSmartFast tests (currently failing)
test_api_server.py  integration check against a running server; excluded from pytest
RULES.md            the variant rules this service must implement
```

Modules import each other by bare name (`from models import ...`), so run everything from the repo root.

## Working on this repo

- Test command: `pytest` from the repo root. `test_api_server.py` needs a live server; run it by hand with `python main.py` in another terminal, then `python test_api_server.py`.
- Add tests next to the code they cover, as `test_*.py` files with `test_*` functions. Fixtures that build boards belong in `conftest.py` once one exists.
- The rules in `RULES.md` are authoritative. When code, tests, and RULES.md disagree, RULES.md wins; if RULES.md is wrong, fix RULES.md in the same change and say so.
- The HTTP API shape (request and response models in `models.py`, the three endpoints) is consumed by the Rails app and must not change without a version bump.
- Keep dependencies to standard, pip installable packages. There is no lockfile yet.

## API

### `GET /health`

Returns `{"status": "healthy", "ai_engine": "ready"}`.

### `GET /api/v1/ai/types`

Returns the registered AI types and the default:

```json
{ "ai_types": ["smart2", "greedy"], "default": "smart2" }
```

### `POST /api/v1/ai/move`

Request:

```json
{
  "board_state": {
    "width": 8,
    "height": 8,
    "pieces": [
      { "id": "r_pawn_1", "type": "pawn", "side": "red", "posx": 0, "posy": 1, "has_moved": false }
    ],
    "walls": [ { "posx": 3, "posy": 3 } ],
    "upgrade_squares": [ { "posx": 0, "posy": 0 } ]
  },
  "ai_type": "smart2",
  "side": "red",
  "game_id": "optional"
}
```

Response:

```json
{
  "move": {
    "piece_id": "r_pawn_1",
    "from_posx": 0, "from_posy": 1,
    "to_posx": 0, "to_posy": 2,
    "killed_piece": null,
    "promotion_type": null
  },
  "score": 150,
  "thinking_time_ms": 45,
  "ai_type": "smart2",
  "side": "red"
}
```

`400` for an invalid board state (out of bounds or overlapping pieces), `422` for a request that fails model validation (unknown `ai_type`, negative coordinates), `500` if the AI finds no move.

## Origin

Extracted from the Expansion Chess Reborn monorepo, where it lived as `ai_api/`. The Rails side reaches it through `AI_API_URL` (default `http://ai-api:8000` in Docker, `http://localhost:8000` otherwise) with a Ruby fallback when the service is down.
