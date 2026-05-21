from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from prof_emailer.config import load_env_file
from prof_emailer.gmail import create_gmail_draft, get_gmail_service
from prof_emailer.llm import generate_email
from prof_emailer.professors import load_professors
from prof_emailer.resume import extract_resume_text
from prof_emailer.text_utils import safe_filename


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate personalized research internship Gmail drafts."
    )
    parser.add_argument("--professors", required=True, help="Path to .xlsx, .csv, or .json professor data.")
    parser.add_argument("--resume", help="Path to resume PDF.")
    parser.add_argument("--resume-text-file", help="Path to an already-extracted resume text file.")
    parser.add_argument("--mode", choices=["gemini", "groq", "both"], default="both")
    parser.add_argument("--primary", choices=["gemini", "groq"], default="gemini")
    parser.add_argument("--gemini-model", default="gemini-2.5-flash")
    parser.add_argument("--groq-model", default="llama-3.3-70b-versatile")
    parser.add_argument("--output-dir", default="output")
    parser.add_argument("--limit", type=int, help="Generate only the first N drafts.")
    parser.add_argument("--validate-only", action="store_true", help="Only parse and summarize professor data.")
    parser.add_argument("--create-gmail-drafts", action="store_true", help="Create Gmail drafts after generating local previews.")
    parser.add_argument("--gmail-client-secret", default="credentials.json", help="Google OAuth client secret JSON.")
    parser.add_argument("--gmail-token", default="token.json", help="Local Gmail OAuth token cache.")
    parser.add_argument("--env-file", default=".env", help="Optional dotenv-style file.")
    return parser.parse_args()


def read_resume(args: argparse.Namespace) -> str:
    if args.resume_text_file:
        return Path(args.resume_text_file).read_text(encoding="utf-8")
    if args.resume:
        return extract_resume_text(Path(args.resume))
    raise SystemExit("Provide --resume path/to/resume.pdf or --resume-text-file path/to/resume.txt.")


def print_validation(professors) -> None:
    print(f"Parsed {len(professors)} professor rows.")
    missing_email = [p.name for p in professors if not p.email]
    print(f"Rows with email: {len(professors) - len(missing_email)}")
    print(f"Rows missing email: {len(missing_email)}")
    if missing_email:
        print("Missing email:")
        for name in missing_email:
            print(f"  - {name}")
    print("\nFirst parsed row:")
    print(json.dumps(professors[0].to_dict(), indent=2, ensure_ascii=False) if professors else "No rows found.")


def write_local_outputs(output_dir: Path, draft: dict) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    name = safe_filename(draft["professor"]["name"] or "professor")
    txt_path = output_dir / f"{name}.txt"
    txt_path.write_text(
        "\n".join(
            [
                f"To: {draft.get('to') or '[missing email]'}",
                f"Subject: {draft['subject']}",
                "",
                draft["body"],
                "",
                f"Fit reason: {draft.get('fit_reason', '')}",
                f"Provider: {draft.get('provider', '')}",
                f"Warning: {draft.get('warning', '')}",
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    args = parse_args()
    load_env_file(Path(args.env_file))

    professors = load_professors(Path(args.professors))
    if args.limit:
        professors = professors[: args.limit]

    if args.validate_only:
        print_validation(professors)
        return 0

    resume_text = read_resume(args)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    drafts: list[dict] = []
    errors: list[dict] = []
    for index, professor in enumerate(professors, start=1):
        print(f"[{index}/{len(professors)}] Generating draft for {professor.name}...")
        try:
            email = generate_email(
                professor=professor,
                resume_text=resume_text,
                mode=args.mode,
                primary=args.primary,
                gemini_model=args.gemini_model,
                groq_model=args.groq_model,
            )
        except Exception as exc:
            print(f"  Error: {type(exc).__name__}. Skipping {professor.name}.")
            errors.append(
                {
                    "professor": professor.to_dict(),
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )
            continue
        draft = {
            "to": professor.email,
            "subject": email["subject"],
            "body": email["body"],
            "fit_reason": email.get("fit_reason", ""),
            "provider": email.get("provider", args.mode),
            "warning": email.get("warning", ""),
            "professor": professor.to_dict(),
        }
        drafts.append(draft)
        write_local_outputs(output_dir, draft)

    (output_dir / "drafts.json").write_text(json.dumps(drafts, indent=2, ensure_ascii=False), encoding="utf-8")
    if errors:
        (output_dir / "errors.json").write_text(json.dumps(errors, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {len(drafts)} local draft preview(s) to {output_dir.resolve()}")
    if errors:
        print(f"Skipped {len(errors)} row(s). See {output_dir / 'errors.json'}")

    if args.create_gmail_drafts:
        service = get_gmail_service(Path(args.gmail_client_secret), Path(args.gmail_token))
        created = 0
        skipped = 0
        for draft in drafts:
            if not draft["to"]:
                skipped += 1
                print(f"Skipping Gmail draft for {draft['professor']['name']}: missing email.")
                continue
            create_gmail_draft(service, to=draft["to"], subject=draft["subject"], body=draft["body"])
            created += 1
        print(f"Created {created} Gmail draft(s). Skipped {skipped} missing-email row(s).")

    return 0


if __name__ == "__main__":
    sys.exit(main())
