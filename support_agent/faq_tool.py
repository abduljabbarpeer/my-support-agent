"""
The FAQ tool.

The agent calls get_faq() to read DemoKart's FAQ from a Google Sheet.
The Sheet must be shared as "anyone with the link can view".
"""

import csv
import io
import os
import re

import requests
from dotenv import load_dotenv

# Read the settings in the .env file (FAQ_SHEET_URL is the Sheet's normal link).
load_dotenv()


def _csv_link(sheet_url: str) -> str:
    """Turn the Sheet's normal link into a link that downloads it as CSV."""
    # The Sheet's ID is the long piece between /d/ and the next slash.
    match = re.search(r"/d/([a-zA-Z0-9_-]+)", sheet_url)
    if not match:
        return ""
    link = f"https://docs.google.com/spreadsheets/d/{match.group(1)}/export?format=csv"
    # If the link points to one particular tab, keep that tab.
    tab = re.search(r"gid=(\d+)", sheet_url)
    if tab:
        link += f"&gid={tab.group(1)}"
    return link


def get_faq() -> str:
    """Returns all of DemoKart's FAQ questions and answers.

    Call this for any question about DemoKart's business, such as delivery,
    returns, payments, products or policies, and answer only from what it returns.
    """
    sheet_url = os.environ.get("FAQ_SHEET_URL", "")
    if not sheet_url:
        return "Error: the FAQ is not set up (FAQ_SHEET_URL is missing)."

    link = _csv_link(sheet_url)
    if not link:
        return "Error: FAQ_SHEET_URL does not look like a Google Sheets link."

    # Download the Sheet as CSV (wait at most 10 seconds).
    try:
        response = requests.get(link, timeout=10)
        response.raise_for_status()
    except requests.RequestException:
        return "Error: could not load the FAQ right now."

    # Read the rows. The first row has the column names.
    rows = list(csv.reader(io.StringIO(response.content.decode("utf-8"))))
    if len(rows) < 2:
        return "The FAQ is empty."

    # Find the question and answer columns by their names; default to the first two.
    header = [name.strip().lower() for name in rows[0]]
    q_col = next((i for i, n in enumerate(header) if "question" in n), 0)
    a_col = next((i for i, n in enumerate(header) if "answer" in n), 1)

    # Build one "Q: ... A: ..." pair per row, skipping rows that are incomplete.
    pairs = []
    for row in rows[1:]:
        if len(row) > max(q_col, a_col) and row[q_col].strip():
            pairs.append(f"Q: {row[q_col].strip()}\nA: {row[a_col].strip()}")
    return "\n\n".join(pairs) if pairs else "The FAQ is empty."
