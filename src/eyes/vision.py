"""Send images to Claude for visual understanding via AWS Bedrock."""

from __future__ import annotations

import json
import os

import boto3

from .capture import image_to_base64


def describe_image(
    img,
    prompt: str = "Describe what you see in this image in detail.",
    model_id: str | None = None,
    region: str | None = None,
) -> str:
    model_id = model_id or os.environ.get(
        "EYES_MODEL_ID", "us.anthropic.claude-opus-4-6-v1"
    )
    region = region or os.environ.get("AWS_REGION", "us-east-1")

    b64 = image_to_base64(img, fmt="PNG", max_dim=1024)

    client = boto3.client("bedrock-runtime", region_name=region)

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": b64,
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
    }

    response = client.invoke_model(
        modelId=model_id,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(body),
    )

    result = json.loads(response["body"].read())
    return result["content"][0]["text"]
