import json
import os
import re
import time
from typing import Any, Dict

from loguru import logger
from openai import OpenAI

MODEL_NAME = os.environ.get("OPENAI_VISION_MODEL", "gpt-4o-mini")
OPENAI_TIMEOUT = float(os.environ.get("OPENAI_TIMEOUT_SECONDS", 30))
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2

_client: OpenAI | None = None


def _get_client() -> OpenAI:
  global _client
  if _client is None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
      raise RuntimeError("OPENAI_API_KEY is not configured")
    _client = OpenAI(api_key=api_key, timeout=OPENAI_TIMEOUT)
  return _client


SYSTEM_PROMPT = """
You are CityLens, an urban infrastructure analyst focused on Dubai. Your job:
1. Examine a citizen photo and classify the municipal issue.
2. Output JSON only, matching the required schema below.
3. Consider Dubai context: Arabic + English signage, desert climates, coastal humidity, luxury districts, construction zones.

Guidelines:
- Issue types: pothole, illegal_waste, broken_streetlight, graffiti, flooding, traffic_congestion, damaged_signage, tree_damage, unclear_issue.
- severity: 1 (minimal) to 10 (critical) reflecting urgency + safety.
- confidence: 0.0-1.0.
- description: concise 25 words max referencing Dubai landmarks if visible.
- safety_risk: true if could harm people/traffic.
- estimated_affected_people: rough count of people impacted in next 24h.
- recommended_action: specific municipal response referencing Dubai departments (e.g., RTA, DEWA, Dubai Municipality).

Edge cases:
- Nighttime, glare, rain: note low visibility.
- Non-urban or unclear: set issue_type "unclear_issue", severity 1, confidence <= 0.5, explain uncertainty.
- Multiple issues: describe the dominant hazard.

Return ONLY valid JSON.
""".strip()

USER_INSTRUCTIONS = """
Classify the issue in this photo. Consider:
- Surface damage vs water accumulation vs obstructions.
- Lighting for broken streetlights at night.
- Illegal waste piles near alleys/desert perimeters.
- Sand-damaged signage or palm/ghaf tree damage from storms.
- Traffic congestion indicators (long queues, signal outages).

JSON schema:
{
  "issue_type": "...",
  "severity": 1-10,
  "confidence": 0-1,
  "description": "...",
  "safety_risk": true/false,
  "estimated_affected_people": int,
  "recommended_action": "..."
}

If confidence < 0.6, set issue_type to "unclear_issue".
""".strip()


def _default_response() -> Dict[str, Any]:
  return {
    "issue_type": "unclear_issue",
    "severity": 1,
    "confidence": 0.0,
    "description": "Unable to determine issue from the provided image.",
    "safety_risk": False,
    "estimated_affected_people": 0,
    "recommended_action": "Request a clearer photo or add textual context.",
  }


def classify_urban_issue(image_url: str) -> Dict[str, Any]:
  """
  Analyze an image via GPT-4 Vision and classify the detected urban issue.
  """
  client = _get_client()
  last_error: Exception | None = None

  for attempt in range(1, MAX_RETRIES + 1):
    try:
      logger.info("Classifying urban issue (attempt {}): {}", attempt, image_url)

      response = client.responses.create(
        model=MODEL_NAME,
        temperature=0.2,
        max_output_tokens=500,
        input=[
          {
            "role": "system",
            "content": [{"type": "input_text", "text": SYSTEM_PROMPT}],
          },
          {
            "role": "user",
            "content": [
              {"type": "input_text", "text": USER_INSTRUCTIONS},
              {"type": "input_image", "image_url": image_url},
            ],
          },
        ],
      )

      content = ""
      if response.output:
        first_chunk = response.output[0].content[0]
        if hasattr(first_chunk, "text"):
          content = first_chunk.text
        elif isinstance(first_chunk, dict):
          content = first_chunk.get("text", "")
      logger.debug("Raw OpenAI response: {}", content)

      match = re.search(r"\{.*\}", content, re.DOTALL)
      json_blob = match.group(0) if match else content
      data = json.loads(json_blob)
      confidence = float(data.get("confidence", 0))
      if confidence < 0.6:
        data["issue_type"] = "unclear_issue"

      data["severity"] = max(1, min(10, int(data.get("severity", 1))))
      data["confidence"] = max(0.0, min(1.0, confidence))
      data["estimated_affected_people"] = max(0, int(data.get("estimated_affected_people", 0)))

      logger.info("Classification success: {}", data)
      return data
    except Exception as exc:  # noqa: BLE001
      last_error = exc
      logger.warning("Classification attempt {} failed: {}", attempt, exc)
      if attempt < MAX_RETRIES:
        time.sleep(RETRY_DELAY_SECONDS * attempt)

  logger.error("All classification attempts failed: {}", last_error)
  fallback = _default_response()
  if last_error:
    fallback["error"] = str(last_error)
  return fallback

