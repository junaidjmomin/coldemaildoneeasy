# Cold Email Done Easy

Local MVP for creating reviewed, personalized research internship email drafts from:

- a resume PDF
- a professor/faculty spreadsheet, CSV, or JSON file
- Gemini and/or Groq-hosted Llama
- Gmail draft creation after review

The app saves local previews first. Gmail drafts are created only when explicitly requested.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a local `.env` file:

```text
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key
```

For Gmail drafts, download a Google OAuth desktop-client JSON file and save it as `credentials.json` in this folder, or pass its path with `--gmail-client-secret`.

## Validate Professor Data

```powershell
python main.py --professors "data\professors.xlsx" --validate-only
```

## Generate Local Draft Previews

```powershell
python main.py `
  --professors "data\professors.xlsx" `
  --resume "data\resume.pdf" `
  --mode both `
  --output-dir output
```

This writes `output\drafts.json` plus one `.txt` preview per recipient.

## Create Gmail Drafts

Review the local previews first, then run:

```powershell
python main.py `
  --professors "data\professors.xlsx" `
  --resume "data\resume.pdf" `
  --mode both `
  --output-dir output `
  --create-gmail-drafts
```

Rows without an email address are skipped during Gmail draft creation.

## Supported Professor Columns

- `Professor Name` -> professor name
- `Email` -> recipient email
- `University`, `Institute`, or `IIT` -> university/institute
- `Department` -> department
- `Website` -> website/profile page
- `Lab` -> lab or research group
- `Specialities / Research Focus` -> research focus
- `Past Research & Key Works` -> past work
- `Recent Papers` -> recent papers or selected publications
- `Alignment to Applicant Interests` -> alignment note
- `Additional details` -> extra context and possible contact/email
- `Openings / Internship Page` -> opportunities page
- `Priority` -> manual fit/priority
- `Status` -> outreach status

See [schema.example.json](schema.example.json) for a JSON input example.
