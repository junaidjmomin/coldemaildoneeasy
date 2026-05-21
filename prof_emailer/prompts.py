from __future__ import annotations

import json

from prof_emailer.professors import Professor


SYSTEM_PROMPT = """You write concise, factual research internship outreach emails.
Only mention professor facts that are present in the provided professor data.
Only mention applicant facts that are present in the provided resume text.
Do not invent papers, awards, institutions, dates, or technical experience.
Return one valid JSON object and no markdown."""


def build_generation_prompt(professor: Professor, resume_text: str) -> str:
    return f"""
Task: Write a personalized cold email for a research internship inquiry.

Return exactly this JSON shape:
{{
  "subject": "short email subject",
  "body": "complete email body",
  "fit_reason": "one sentence explaining why this professor is a fit"
}}

Email rules:
- 160 to 230 words.
- Professional, specific, and not overly flattering.
- Mention 1-2 concrete professor research themes from the professor data.
- Connect those themes to 1-2 concrete applicant experiences from the resume.
- Ask politely about possible research internship opportunities.
- Do not say that anything is attached unless the resume text explicitly says so.
- No placeholders like [Your Name].
- Sign off with the applicant name if it can be inferred from the resume, otherwise use "Best regards".

Professor data:
{json.dumps(professor.to_dict(), ensure_ascii=False, indent=2)}

Resume text:
{resume_text[:18000]}
""".strip()


def build_refinement_prompt(professor: Professor, resume_text: str, prior_draft: dict) -> str:
    return f"""
Task: Refine this research internship email draft.

Return exactly this JSON shape:
{{
  "subject": "short email subject",
  "body": "complete email body",
  "fit_reason": "one sentence explaining why this professor is a fit"
}}

Refinement rules:
- Preserve factual accuracy.
- Make it specific to the professor.
- Keep it within 160 to 230 words.
- Remove generic phrasing and unsupported claims.
- Do not add facts not present in the professor data or resume text.

Professor data:
{json.dumps(professor.to_dict(), ensure_ascii=False, indent=2)}

Resume text:
{resume_text[:18000]}

Draft to refine:
{json.dumps(prior_draft, ensure_ascii=False, indent=2)}
""".strip()
