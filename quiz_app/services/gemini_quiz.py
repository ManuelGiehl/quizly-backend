"""Gemini quiz JSON from a Whisper transcript (``google-genai`` SDK)."""

import json
import re

from django.conf import settings
from google import genai


class GeminiQuizError(Exception):
    """Gemini request failed or the model returned unusable quiz JSON."""


_QUIZ_PROMPT_HEAD = """Based on the following transcript, generate a quiz in valid JSON format.

The quiz must follow this exact structure:
{
  "title": "Create a concise quiz title based on the topic of the transcript.",
  "description": "Summarize the transcript in no more than 150 characters. Do not include any quiz questions or answers.",
  "questions": [
    {
      "question_title": "The question goes here.",
      "question_options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "The correct answer from the above options"
    }
  ]
}

Requirements:
- Include exactly 10 questions in the "questions" array.
- Each question must have exactly 4 distinct answer options in "question_options".
- Each question must have exactly one correct answer in "answer", which must be identical to one of the strings in "question_options".
- Output must be valid JSON parseable with Python json.loads without any preprocessing.
- Do not include markdown code fences (no ```), explanations, or any text outside the JSON object.

Transcript:
"""


def build_gemini_quiz_prompt(transcript: str) -> str:
    """Append the transcript after the fixed instruction block."""
    return f"{_QUIZ_PROMPT_HEAD}{transcript}"


def strip_code_fences(raw: str) -> str:
    """Remove leading/trailing Markdown ``` / ```json wrappers if present."""
    text = raw.strip()
    if not text.startswith("```"):
        return text
    text = re.sub(r"^```(?:json)?\s*", "", text, count=1, flags=re.IGNORECASE)
    text = re.sub(r"\s*```\s*$", "", text, count=1)
    return text.strip()


def _slice_json_object(text: str) -> str:
    i = text.find("{")
    j = text.rfind("}")
    if i == -1 or j < i:
        return text
    return text[i : j + 1]


def _decoded_quiz_dict(raw: str) -> dict:
    base = strip_code_fences(raw)
    for cand in (base, _slice_json_object(base)):
        try:
            out = json.loads(cand)
        except json.JSONDecodeError:
            continue
        if isinstance(out, dict):
            return out
    raise GeminiQuizError("Gemini returned invalid JSON.")


def _validated_title(raw) -> str:
    if not isinstance(raw, str) or not (t := raw.strip()):
        raise GeminiQuizError("Invalid or empty title.")
    return t[:255]


def _validated_description(raw) -> str:
    if not isinstance(raw, str) or not (d := raw.strip()):
        raise GeminiQuizError("Invalid or empty description.")
    return d[:150]


def _four_option_strings(raw_opts: object, idx: int) -> list[str]:
    if not isinstance(raw_opts, list) or len(raw_opts) != 4:
        raise GeminiQuizError(f"Question {idx}: need 4 options.")
    out = []
    for j, o in enumerate(raw_opts, start=1):
        if not isinstance(o, str) or not (s := o.strip()):
            raise GeminiQuizError(f"Question {idx}: invalid option {j}.")
        out.append(s)
    if len(set(out)) != 4:
        raise GeminiQuizError(f"Question {idx}: options must be distinct.")
    return out


def _validated_one_question(obj: object, idx: int) -> dict:
    if not isinstance(obj, dict):
        raise GeminiQuizError(f"Question {idx} must be an object.")
    opts = _four_option_strings(obj.get("question_options"), idx)
    qt = obj.get("question_title")
    if not isinstance(qt, str) or not (t := qt.strip()):
        raise GeminiQuizError(f"Question {idx}: missing title.")
    ans = obj.get("answer")
    if not isinstance(ans, str) or not (a := ans.strip()):
        raise GeminiQuizError(f"Question {idx}: missing answer.")
    if a not in opts:
        raise GeminiQuizError(f"Question {idx}: answer must match an option.")
    return {"question_title": t[:500], "question_options": opts, "answer": a[:500]}


def _validated_questions(raw) -> list[dict]:
    if not isinstance(raw, list) or len(raw) != 10:
        raise GeminiQuizError("Expected exactly 10 questions.")
    return [_validated_one_question(q, i) for i, q in enumerate(raw, start=1)]


def parse_validated_quiz_payload(data: object) -> dict:
    """Return ``title``, ``description``, ``questions`` ready for ORM create."""
    if not isinstance(data, dict):
        raise GeminiQuizError("Root value must be a JSON object.")
    title = _validated_title(data.get("title"))
    desc = _validated_description(data.get("description"))
    questions = _validated_questions(data.get("questions"))
    return {"title": title, "description": desc, "questions": questions}


def _response_text_from_client(client: genai.Client, prompt: str) -> str:
    try:
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
        )
    except Exception as exc:
        raise GeminiQuizError("Gemini request failed.") from exc
    text = (getattr(response, "text", None) or "").strip()
    if not text:
        raise GeminiQuizError("Empty response from Gemini.")
    return text


def _call_gemini_text(prompt: str) -> str:
    key = (settings.GEMINI_API_KEY or "").strip()
    if not key:
        raise GeminiQuizError("GEMINI_API_KEY is not set.")
    client = genai.Client(api_key=key)
    return _response_text_from_client(client, prompt)


def generate_quiz_from_transcript(transcript: str) -> dict:
    """Ask Gemini for quiz JSON and validate structure (10 MC questions)."""
    prompt = build_gemini_quiz_prompt(transcript)
    raw = _call_gemini_text(prompt)
    data = _decoded_quiz_dict(raw)
    return parse_validated_quiz_payload(data)
