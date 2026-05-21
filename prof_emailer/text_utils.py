from __future__ import annotations

import re


def safe_filename(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._ -]+", "", value).strip()
    value = re.sub(r"\s+", "_", value)
    return value[:80] or "draft"
