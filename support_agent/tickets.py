"""
The ticket tool.

When the agent hands a customer over to a person, it saves a support ticket
as one row in tickets.csv (in the project folder). Only Python's built-in
modules are used.
"""

import csv
from datetime import datetime
from pathlib import Path

# tickets.csv lives in the project folder (one level above this file's folder).
TICKETS_FILE = Path(__file__).resolve().parent.parent / "tickets.csv"

# The column names written on the first row of a new file.
HEADER = ["ticket_id", "date_time", "name", "contact", "order_id", "reason", "summary"]

# The only reasons a hand-over can have.
REASONS = ["no answer", "refund", "angry customer", "asked for a person"]


def _next_ticket_id() -> str:
    """Return the next ID: T-1001 for a new file, otherwise one higher than the last ticket."""
    if not TICKETS_FILE.exists():
        return "T-1001"
    with open(TICKETS_FILE, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    # rows[0] is the header, so a file with only a header has no tickets yet.
    if len(rows) < 2:
        return "T-1001"
    last_number = int(rows[-1][0].split("-")[1])
    return f"T-{last_number + 1}"


def create_ticket(
    name: str, contact: str, reason: str, summary: str, order_id: str = ""
) -> str:
    """Save a support ticket when handing the customer over to a person.

    Only call this after the customer has given their name and a contact.

    Args:
        name: The customer's name.
        contact: The customer's phone number or email.
        reason: Why we are handing over. Must be one of: "no answer", "refund",
            "angry customer", "asked for a person".
        summary: A one-line summary of the problem.
        order_id: The order ID if the customer gave one, otherwise leave empty.

    Returns:
        The new ticket ID, for example T-1001.
    """
    # Check the reason so the file only ever holds the four allowed values.
    if reason not in REASONS:
        return f"Error: reason must be one of {REASONS}. Please try again."

    is_new_file = not TICKETS_FILE.exists()
    ticket_id = _next_ticket_id()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(TICKETS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if is_new_file:
            writer.writerow(HEADER)  # header row only for a brand-new file
        writer.writerow([ticket_id, now, name, contact, order_id, reason, summary])

    return ticket_id
