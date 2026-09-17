# Expansion Chess AI API

A Python (FastAPI) service that calculates AI moves for Expansion Chess, a three-sided chess variant with walls and upgrade squares.

## Features

- **Fast AI**: Python-based implementation that's significantly faster than Ruby
- **Multiple AI Types**: Support for smart2 (intelligent) and greedy (material-focused) AI
- **REST API**: Simple HTTP interface for integration
- **Validation**: Comprehensive board state and move validation
- **Extensible**: Easy to add new AI types

## Setup

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the API server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Health Check
```
GET /health
```
Returns API status and health information.

### Get AI Types
```
GET /api/v1/ai/types
```
Returns available AI types and default recommendation.

### Calculate AI Move
```
POST /api/v1/ai/move
```

**Request Body:**
```json
{
  "board_state": {
    "width": 8,
    "height": 8,
    "pieces": [
      {
        "id": "w_pawn_1",
        "type": "pawn",
        "side": "white",
        "posx": 0,
        "posy": 1,
        "has_moved": false
      }
    ],
    "walls": [
      {
        "posx": 3,
        "posy": 3
      }
    ],
    "upgrade_squares": [
      {
        "posx": 0,
        "posy": 0
      }
    ]
  },
  "ai_type": "smart2",
  "side": "white",
  "game_id": "optional_game_id"
}
```

**Response:**
```json
{
  "move": {
    "piece_id": "w_pawn_1",
    "from_posx": 0,
    "from_posy": 1,
    "to_posx": 0,
    "to_posy": 2,
    "killed_piece": null,
    "promotion_type": null
  },
  "score": 150,
  "thinking_time_ms": 45,
  "ai_type": "smart2",
  "side": "white"
}
```

## AI Types

### Smart2 (Default)
- **Strategy**: Intelligent evaluation considering piece type, position, protection, and advancement
- **Best for**: Competitive play, strategic thinking
- **Performance**: Fast with good move quality

### Greedy
- **Strategy**: Always chooses the highest material value move
- **Best for**: Testing, simple scenarios
- **Performance**: Very fast, predictable

## Testing

Install the dev dependencies and run the unit tests:

```bash
pip install -r requirements-dev.txt
pytest
```

This covers board validation, AI move generation, move validation, and the AiSmartFast agent. The test files can also be run directly as scripts (`python test_ai.py`).

`test_api_server.py` is an integration check against a running server and is excluded from `pytest` by default. Start the server with `python main.py`, then run `python test_api_server.py`.

## Integration with Rails

The API is designed to be easily integrated with your Rails application:

1. **Replace Ruby AI calls** with HTTP requests to this API
2. **Add fallback logic** to use Ruby AI if the API is unavailable
3. **Monitor performance** and reliability

## Performance

- **Move calculation**: < 100ms for most positions
- **API response**: < 50ms including network latency
- **Concurrent requests**: Handles 10+ simultaneous calculations

## Development

### Adding New AI Types

1. Create a new AI class inheriting from `AIBase`
2. Implement the `select_move()` method
3. Add the AI type to `AIEngine.ai_types`
4. Update validation in `models.py`

### Project Structure

```
./
├── main.py          # FastAPI application
├── models.py        # Pydantic models and validation
├── ai_engine.py     # Main AI engine and routing
├── ai_base.py       # Base AI class with common functionality
├── ai_smart2.py     # Smart AI implementation
├── ai_greedy.py     # Greedy AI implementation
├── test_ai.py       # Test suite
├── requirements.txt # Python dependencies
└── README.md        # This file
```

## Troubleshooting

### Common Issues

1. **Import errors**: Make sure all dependencies are installed
2. **Validation errors**: Check board state format and piece positions
3. **No moves found**: Verify the board has valid pieces for the requested side

### Logs

The API provides detailed logging for debugging:
- AI calculation steps
- Move validation results
- Error details and stack traces

## Origin

This service was extracted from the Expansion Chess Reborn monorepo. The Rails application reaches it over HTTP via `AI_API_URL` (see `app/services/ai_api_service.rb` there).
