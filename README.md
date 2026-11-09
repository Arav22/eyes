# eyes

MCP server that gives AI coding agents live computer vision. Capture your screen, read text via OCR, watch for visual changes, and get AI-powered scene descriptions — all as tools your agent can call.

The counterpart to [earshot](https://github.com/nichochar/earshot). Earshot gave agents ears; **eyes** gives them sight.

## Features

- **`capture_screen`** — Screenshot the full screen or a specific region
- **`capture_camera`** — Grab a frame from your webcam
- **`watch_screen`** — Wait for visual changes (motion-triggered capture)
- **`read_text`** — Extract text from the screen via OCR
- **`describe_scene`** — Send a screenshot to Claude for semantic understanding

## Quick Start

```bash
# Install
pip install -e .

# Or with all optional dependencies
pip install -e ".[all]"
```

### Use with Claude Code

Add to your MCP config (`~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "eyes": {
      "command": "python",
      "args": ["-m", "eyes.server"]
    }
  }
}
```

### Use standalone

```bash
# Run the MCP server
eyes

# Or
python -m eyes.server
```

## Tools

### capture_screen

Take a screenshot of the current screen.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| x | int | — | Left edge of capture region |
| y | int | — | Top edge of capture region |
| width | int | — | Width of capture region |
| height | int | — | Height of capture region |
| max_dimension | int | 1920 | Max width/height in pixels |

### capture_camera

Capture a frame from the webcam. Requires `opencv-python`.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| device_index | int | 0 | Camera device index |

### watch_screen

Monitor the screen and return a capture only when significant change is detected.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| threshold | float | 0.05 | Change sensitivity (0.0–1.0) |
| timeout | int | 30 | Max seconds to wait |
| interval | float | 1.0 | Seconds between checks |

### read_text

Extract text from the screen using OCR. Requires `pytesseract` and Tesseract installed on your system.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| x | int | — | Left edge of region |
| y | int | — | Top edge of region |
| width | int | — | Width of region |
| height | int | — | Height of region |

### describe_scene

Take a screenshot and send it to Claude (via AWS Bedrock) for a detailed description.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| prompt | string | "Describe what you see" | Custom vision prompt |
| x | int | — | Left edge of region |
| y | int | — | Top edge of region |
| width | int | — | Width of region |
| height | int | — | Height of region |

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `EYES_MODEL_ID` | `us.anthropic.claude-opus-4-6-v1` | Bedrock model for `describe_scene` |
| `AWS_REGION` | `us-east-1` | AWS region for Bedrock |
| `AWS_PROFILE` | — | AWS credentials profile |

## Requirements

- **macOS** or **Linux** (screen capture uses native tools)
- Python 3.10+
- For camera: `pip install eyes-mcp[camera]`
- For OCR: `pip install eyes-mcp[ocr]` + [Tesseract](https://github.com/tesseract-ocr/tesseract)
- For `describe_scene`: AWS credentials with Bedrock access

## License

MIT
