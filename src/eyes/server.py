"""Eyes MCP server — gives AI agents live computer vision."""

from __future__ import annotations

import asyncio
import logging
import time

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, ImageContent, Tool

from .capture import capture_screen, capture_camera, compute_frame_diff, image_to_base64
from .ocr import extract_text
from .vision import describe_image

logger = logging.getLogger("eyes")

app = Server("eyes")

_last_frame = None
_last_frame_time: float = 0


def _screen_region_from_args(args: dict) -> dict | None:
    if all(k in args for k in ("x", "y", "width", "height")):
        return {
            "x": int(args["x"]),
            "y": int(args["y"]),
            "width": int(args["width"]),
            "height": int(args["height"]),
        }
    return None


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="capture_screen",
            description=(
                "Take a screenshot of the current screen. "
                "Optionally specify a region with x, y, width, height."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "Left edge of capture region"},
                    "y": {"type": "integer", "description": "Top edge of capture region"},
                    "width": {"type": "integer", "description": "Width of capture region"},
                    "height": {"type": "integer", "description": "Height of capture region"},
                    "max_dimension": {
                        "type": "integer",
                        "description": "Max width/height in pixels (default 1920)",
                        "default": 1920,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="capture_camera",
            description=(
                "Capture a single frame from the webcam. "
                "Requires opencv-python to be installed."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "device_index": {
                        "type": "integer",
                        "description": "Camera device index (default 0)",
                        "default": 0,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="watch_screen",
            description=(
                "Monitor the screen for changes. Returns a screenshot only when "
                "significant visual change is detected compared to the last capture. "
                "Use this to wait for something to happen on screen."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "threshold": {
                        "type": "number",
                        "description": "Change threshold 0.0-1.0 (default 0.05, ~5% pixel change)",
                        "default": 0.05,
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Max seconds to wait for a change (default 30)",
                        "default": 30,
                    },
                    "interval": {
                        "type": "number",
                        "description": "Seconds between checks (default 1.0)",
                        "default": 1.0,
                    },
                },
                "required": [],
            },
        ),
        Tool(
            name="read_text",
            description=(
                "Extract text from the screen using OCR. "
                "Optionally specify a region to read from. "
                "Requires pytesseract to be installed."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "Left edge of region"},
                    "y": {"type": "integer", "description": "Top edge of region"},
                    "width": {"type": "integer", "description": "Width of region"},
                    "height": {"type": "integer", "description": "Height of region"},
                },
                "required": [],
            },
        ),
        Tool(
            name="describe_scene",
            description=(
                "Take a screenshot and send it to Claude for a detailed visual "
                "description. Useful for understanding complex UI states, diagrams, "
                "or anything that needs semantic understanding beyond OCR."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Custom prompt for the vision model (default: describe what you see)",
                    },
                    "x": {"type": "integer", "description": "Left edge of region"},
                    "y": {"type": "integer", "description": "Top edge of region"},
                    "width": {"type": "integer", "description": "Width of region"},
                    "height": {"type": "integer", "description": "Height of region"},
                },
                "required": [],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent | ImageContent]:
    global _last_frame, _last_frame_time

    if name == "capture_screen":
        region = _screen_region_from_args(arguments)
        max_dim = arguments.get("max_dimension", 1920)
        img = await asyncio.to_thread(capture_screen, region)
        _last_frame = img
        _last_frame_time = time.time()
        b64 = await asyncio.to_thread(image_to_base64, img, "PNG", max_dim)
        return [
            ImageContent(type="image", data=b64, mimeType="image/png"),
            TextContent(
                type="text",
                text=f"Screenshot captured ({img.size[0]}x{img.size[1]})",
            ),
        ]

    elif name == "capture_camera":
        device = arguments.get("device_index", 0)
        img = await asyncio.to_thread(capture_camera, device)
        b64 = await asyncio.to_thread(image_to_base64, img, "PNG", 1920)
        return [
            ImageContent(type="image", data=b64, mimeType="image/png"),
            TextContent(
                type="text",
                text=f"Camera frame captured ({img.size[0]}x{img.size[1]})",
            ),
        ]

    elif name == "watch_screen":
        threshold = arguments.get("threshold", 0.05)
        timeout = arguments.get("timeout", 30)
        interval = arguments.get("interval", 1.0)

        if _last_frame is None:
            _last_frame = await asyncio.to_thread(capture_screen)
            _last_frame_time = time.time()

        deadline = time.time() + timeout
        while time.time() < deadline:
            await asyncio.sleep(interval)
            current = await asyncio.to_thread(capture_screen)
            diff = await asyncio.to_thread(compute_frame_diff, _last_frame, current)
            if diff >= threshold:
                _last_frame = current
                _last_frame_time = time.time()
                b64 = await asyncio.to_thread(image_to_base64, current, "PNG", 1920)
                return [
                    ImageContent(type="image", data=b64, mimeType="image/png"),
                    TextContent(
                        type="text",
                        text=f"Change detected (diff={diff:.3f}, threshold={threshold})",
                    ),
                ]

        return [
            TextContent(
                type="text",
                text=f"No significant change detected within {timeout}s (threshold={threshold})",
            ),
        ]

    elif name == "read_text":
        region = _screen_region_from_args(arguments)
        img = await asyncio.to_thread(capture_screen, region)
        text = await asyncio.to_thread(extract_text, img, region=None)
        return [
            TextContent(type="text", text=text if text else "(no text detected)"),
        ]

    elif name == "describe_scene":
        region = _screen_region_from_args(arguments)
        prompt = arguments.get("prompt", "Describe what you see in this image in detail.")
        img = await asyncio.to_thread(capture_screen, region)
        description = await asyncio.to_thread(describe_image, img, prompt)
        return [
            TextContent(type="text", text=description),
        ]

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def run():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def main():
    logging.basicConfig(level=logging.INFO, format="%(name)s - %(message)s")
    asyncio.run(run())


if __name__ == "__main__":
    main()
