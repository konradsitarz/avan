"""
Seed script — feeds test messages into the Avan API via POST /api/messages.

Usage:
    python seed_data.py                  # default: http://localhost:8000
    python seed_data.py http://host:port # custom API URL

Messages arrive without priority — the backend triage engine classifies them.
"""

import requests
import sys
import time

API_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

MESSAGES = [
    {
        "type": "email",
        "sender": "john.smith@gmail.com",
        "content": "Subject: Broken garage gate — urgent\n\nThe underground garage gate has been open for 3 days. Anyone can walk in. I've called twice, no response.",
        "followup_count": 0,
    },
    {
        "type": "sms",
        "sender": "+1 555 234 567",
        "content": "Hey, the ceiling is leaking in the stairwell on the 3rd floor, getting worse",
        "followup_count": 0,
    },
    {
        "type": "email",
        "sender": "m.williams@yahoo.com",
        "content": "Subject: Missing March statement\n\nNeither I nor my neighbor in 14B received the March expense statement. Please send it.",
        "followup_count": 0,
    },
    {
        "type": "sms",
        "sender": "+1 555 112 233",
        "content": "Apartment 4B is renting on Airbnb again. This violates the building rules. What are you going to do about it?",
        "followup_count": 0,
    },
    {
        "type": "email",
        "sender": "board@oakridge-hoa.com",
        "content": "Subject: Board decision — roof repair\n\nWe received three quotes for the roof repair. The board needs to decide before the April meeting. Please prepare a summary and recommendation.",
        "followup_count": 0,
    },
    {
        "type": "sms",
        "sender": "+1 555 887 001",
        "content": "Anna hasn't responded to my emails about the repair fund for a week",
        "followup_count": 0,
    },
    {
        "type": "email",
        "sender": "p.johnson@gmail.com",
        "content": "Subject: Noise complaints — apartment 12A\n\nThis is the fourth complaint about this apartment. Loud music every night after midnight. Nothing has been done.",
        "followup_count": 3,
    },
    {
        "type": "sms",
        "sender": "+1 555 332 119",
        "content": "Elevator broken again in building B. Third time this month.",
        "followup_count": 2,
    },
    {
        "type": "email",
        "sender": "r.davis@outlook.com",
        "content": "Subject: Insurance renewal\n\nThe building insurance expires April 30. I don't see it on the meeting agenda. Who's handling this?",
        "followup_count": 0,
    },
    {
        "type": "sms",
        "sender": "+1 555 201 445",
        "content": "Can someone confirm my maintenance fee payment went through? I paid 3 weeks ago.",
        "followup_count": 0,
    },
    {
        "type": "email",
        "sender": "john.smith@gmail.com",
        "content": "Subject: RE: Broken garage gate\n\nI'm writing for the THIRD TIME. Gate is still open. If nothing changes by end of week, I'm reporting this to the building authority.",
        "followup_count": 3,
    },
    {
        "type": "sms",
        "sender": "+1 555 234 567",
        "content": "About that stairwell leak I mentioned — it's now dripping onto the electrical panel. That seems dangerous?",
        "followup_count": 1,
    },
    {
        "type": "voice",
        "sender": "+1 555 100 200",
        "content": "[Whisper transcription, ~72% confidence] Hello, I'm calling... I think it's Mrs. Lewis from... [unintelligible]... there's water in the basement about... I don't know... twenty centimeters? Maybe more. And it smells. Please... [unintelligible]... as soon as possible.",
        "followup_count": 0,
    },
    {
        "type": "email",
        "sender": "office@buildserv.com",
        "content": "Subject: Invoice #INV/2024/0892\n\nPlease find attached the invoice for the gas installation inspection (buildings A–C). Amount: $3,200 net. Please confirm or report corrections within 7 business days.",
        "followup_count": 0,
    },
    {
        "type": "email",
        "sender": "tom.green@outlook.com",
        "content": "Subject: Quick question about the parking spot\n\nHi, I just moved in (apt 7C). Is there a way to rent an additional parking spot in the garage? Also the intercom doesn't seem to work for my unit. Thanks!",
        "followup_count": 0,
    },
    {
        "type": "sms",
        "sender": "+1 555 999 111",
        "content": "Hey, the lady in 8A also has a flooded ceiling, seems like the same issue as mine on the 3rd floor. Maybe worth checking the whole riser?",
        "followup_count": 0,
    },
]


def main():
    url = f"{API_URL}/api/messages"
    print(f"Seeding {len(MESSAGES)} messages to {url}\n")

    for i, msg in enumerate(MESSAGES, 1):
        resp = requests.post(url, json=msg)
        if resp.ok:
            priority = resp.json().get("priority", "?")
            status = f"OK -> {priority.upper()}"
        else:
            status = f"FAIL ({resp.status_code})"
        label = msg["sender"][:30]
        print(f"  [{i:>2}/{len(MESSAGES)}] {msg['type']:>5} | {label:<30} | {status}")
        time.sleep(0.3)

    print(f"\nDone. {len(MESSAGES)} messages sent (priority assigned by triage engine).")


if __name__ == "__main__":
    main()
