from __future__ import annotations

import os

from prof_emailer.json_utils import parse_json_object
from prof_emailer.professors import Professor
from prof_emailer.prompts import build_generation_prompt, build_refinement_prompt, SYSTEM_PROMPT


def generate_email(
    *,
    professor: Professor,
    resume_text: str,
    mode: str,
    primary: str,
    gemini_model: str,
    groq_model: str,
) -> dict:
    if mode == "gemini":
        return _with_provider("gemini", professor, resume_text, gemini_model, None)
    if mode == "groq":
        return _with_provider("groq", professor, resume_text, groq_model, None)

    first_provider = primary
    second_provider = "groq" if primary == "gemini" else "gemini"
    first_model = gemini_model if first_provider == "gemini" else groq_model
    second_model = gemini_model if second_provider == "gemini" else groq_model

    try:
        first = _with_provider(first_provider, professor, resume_text, first_model, None)
    except Exception as first_error:
        fallback = _with_provider(second_provider, professor, resume_text, second_model, None)
        fallback["provider"] = f"{second_provider} fallback"
        fallback["warning"] = f"{first_provider} failed before initial draft: {type(first_error).__name__}"
        return fallback

    try:
        refined = _with_provider(second_provider, professor, resume_text, second_model, first)
        refined["provider"] = f"{first_provider}+{second_provider}"
        return refined
    except Exception as refinement_error:
        first["provider"] = f"{first_provider} only"
        first["warning"] = f"{second_provider} refinement failed: {type(refinement_error).__name__}"
        return first


def _with_provider(
    provider: str,
    professor: Professor,
    resume_text: str,
    model: str,
    prior_draft: dict | None,
) -> dict:
    if prior_draft:
        prompt = build_refinement_prompt(professor, resume_text, prior_draft)
    else:
        prompt = build_generation_prompt(professor, resume_text)

    if provider == "gemini":
        text = _call_gemini(prompt, model)
    elif provider == "groq":
        text = _call_groq(prompt, model)
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    parsed = parse_json_object(text)
    parsed["provider"] = provider
    parsed.setdefault("subject", f"Research Internship Inquiry - {professor.name}")
    parsed.setdefault("body", "")
    parsed.setdefault("fit_reason", "")
    return parsed


def _call_gemini(prompt: str, model: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set.")

    try:
        from google import genai
    except ImportError as exc:
        raise RuntimeError("Gemini dependency missing. Run: pip install -r requirements.txt") from exc

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=f"{SYSTEM_PROMPT}\n\n{prompt}",
    )
    return response.text or ""


def _call_groq(prompt: str, model: str) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set.")

    try:
        from groq import Groq
    except ImportError as exc:
        raise RuntimeError("Groq dependency missing. Run: pip install -r requirements.txt") from exc

    client = Groq(api_key=api_key)
    completion = client.chat.completions.create(
        model=model,
        temperature=0.25,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    return completion.choices[0].message.content or ""
