"""
Seed script — feeds test messages into the Nava API via POST /api/messages.

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
        "sender": "jan.kowalski@gmail.com",
        "content": "Temat: Zepsuta brama — pilne\n\nBrama do garażu podziemnego jest otwarta od 3 dni. Może wejść każdy. Dwa razy dzwoniłem, brak odpowiedzi.",
        "followup_count": 0,
    },
    {
        "type": "sms",
        "sender": "+48 601 234 567",
        "content": "Hej, przecieka sufit na klatce schodowej 3. piętro, robi się coraz gorzej",
        "followup_count": 0,
    },
    {
        "type": "email",
        "sender": "m.wisniewska@wp.pl",
        "content": "Temat: Brak rozliczenia za marzec\n\nAni ja, ani sąsiadka z 14B nie dostałyśmy rozliczenia za marzec. Proszę o przesłanie.",
        "followup_count": 0,
    },
    {
        "type": "sms",
        "sender": "+48 799 112 233",
        "content": "Mieszkanie 4B znowu wynajmuje na Airbnb. To jest niezgodne z regulaminem wspólnoty. Co z tym będziecie robić?",
        "followup_count": 0,
    },
    {
        "type": "email",
        "sender": "zarzad@wspolnota-mokotow.pl",
        "content": "Temat: Decyzja zarządu — remont dachu\n\nOtrzymaliśmy trzy oferty na remont dachu. Zarząd musi podjąć decyzję przed kwietniowym zebraniem. Proszę o podsumowanie i rekomendację.",
        "followup_count": 0,
    },
    {
        "type": "sms",
        "sender": "+48 512 887 001",
        "content": "Pani Ania nie odpowiada od tygodnia na moje maile w sprawie funduszu remontowego",
        "followup_count": 0,
    },
    {
        "type": "email",
        "sender": "p.nowak@gmail.com",
        "content": "Temat: Skargi na hałas — mieszkanie 12A\n\nTo już czwarta skarga na to mieszkanie. Głośna muzyka każdą noc po północy. Nic nie zostało zrobione.",
        "followup_count": 3,
    },
    {
        "type": "sms",
        "sender": "+48 604 332 119",
        "content": "Winda znowu zepsuta w budynku B. Trzeci raz w tym miesiącu.",
        "followup_count": 2,
    },
    {
        "type": "email",
        "sender": "r.dabrowska@onet.pl",
        "content": "Temat: Odnowienie ubezpieczenia\n\nUbezpieczenie budynku kończy się 30 kwietnia. Nie widzę tego w agendzie zebrania. Kto się tym zajmuje?",
        "followup_count": 0,
    },
    {
        "type": "sms",
        "sender": "+48 733 201 445",
        "content": "Czy ktoś może potwierdzić, że moja wpłata na fundusz eksploatacyjny dotarła? Zapłaciłem 3 tygodnie temu.",
        "followup_count": 0,
    },
    {
        "type": "email",
        "sender": "jan.kowalski@gmail.com",
        "content": "Temat: RE: Zepsuta brama\n\nPiszę PO RAZ TRZECI. Brama nadal otwarta. Jeśli do końca tygodnia nic się nie zmieni, zgłaszam sprawę do nadzoru budowlanego.",
        "followup_count": 3,
    },
    {
        "type": "sms",
        "sender": "+48 601 234 567",
        "content": "O tej przeciekającej klatce schodowej co pisałem — teraz leje się na skrzynkę elektryczną. To chyba groźne?",
        "followup_count": 1,
    },
    {
        "type": "voice",
        "sender": "+48 888 100 200",
        "content": "[Transkrypcja Whisper, pewność ~72%] Dzień dobry, dzwonię... chyba Lewandowska z... [nieczytelne]... bo proszę pani, w piwnicy jest woda na... nie wiem... dwadzieścia centymetrów? Może więcej. I śmierdzi. Proszę o... [nieczytelne]... jak najszybciej.",
        "followup_count": 0,
    },
    {
        "type": "email",
        "sender": "biuro@bud-serwis.pl",
        "content": "Temat: Faktura nr FS/2024/0892\n\nW załączniku przesyłam fakturę za przegląd instalacji gazowej (budynki A–C). Kwota 8.200 zł netto. Proszę o potwierdzenie lub zgłoszenie korekt w ciągu 7 dni roboczych.",
        "followup_count": 0,
    },
    {
        "type": "email",
        "sender": "tomek.zielinski@outlook.com",
        "content": "Temat: Quick question about the parking spot\n\nHi, I just moved in (apt 7C) and my Polish is still not great. Is there a way to rent an additional parking spot in the garage? Also the intercom doesn't seem to work for my unit. Thanks!",
        "followup_count": 0,
    },
    {
        "type": "sms",
        "sender": "+48 606 999 111",
        "content": "Cześć, z tego co wiem to pani z 8A też ma zalany sufit, chyba ten sam problem co u mnie na 3 piętrze. Może warto sprawdzić całą pionówkę?",
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
