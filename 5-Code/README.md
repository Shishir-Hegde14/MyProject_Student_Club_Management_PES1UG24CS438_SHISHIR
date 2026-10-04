# Portal prototype

Shishir Hegde | PES1UG24CS438 | Section 5H

This is a small Flask and SQLite implementation of the student club portal. Python was chosen for the web forms and QR generation. The business rules are in `services.py`, the routes are in `app.py`, and the database definition is in `schema.sql`.

## Setup

Use Python 3.12 or newer. Run these commands from the repository root on Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r 5-Code/requirements-dev.txt
cd 5-Code
..\.venv\Scripts\python.exe -m flask --app app seed-demo
..\.venv\Scripts\waitress-serve.exe --host=127.0.0.1 --port=5000 --threads=16 --call app:create_app
```

Linux/macOS:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r 5-Code/requirements-dev.txt
cd 5-Code
../.venv/bin/python -m flask --app app seed-demo
../.venv/bin/waitress-serve --host=127.0.0.1 --port=5000 --threads=16 --call app:create_app
```

Open `http://127.0.0.1:5000`. For a quick development run, `python app.py` also starts a localhost server. Keep it local; the demo is not configured for public deployment.

The first run creates `instance/portal.sqlite3` and a random signing key in `instance/secret.key`. Both stay out of Git. An optional `PORTAL_SECRET` environment variable overrides the key. Keep a stable secret while tickets are in use; replacing it invalidates existing signatures and sessions.

`seed-demo` only works on an empty user table and never replaces existing users. It creates a sample club with Rs 1,00,000 allocation and these accounts, all using the local demo password `club-demo-2026`:

| Username | Role |
| --- | --- |
| lead | Club Lead |
| faculty | Faculty Coordinator |
| finance | Finance Officer |
| dean | Dean |
| student, student2 | Attendees |
| gate | Check-in Staff |

## Walkthrough

1. Log in as `lead`. Create an event with today or a future date, a venue, capacity and budget lines such as `Materials | 2500`.
2. Save the proposal, check it, and request budget allocation. If the amount is too high, edit the draft and try again.
3. Log in as `faculty`, then `finance`, then `dean`. Review and approve at each stage. A reviewer can reject with a reason instead.
4. Log in as `student`, open the approved event and register. The ticket page shows the actual QR and its encoded text.
5. Copy the ticket text. Log in as `gate`, select the event and paste the text into check-in. The first attempt succeeds and the second is rejected.
6. Log in as `lead` to check the registration count and approval status. The dashboard polls every three seconds.

## Important choices

- Amounts use integer paise, avoiding floating-point rounding for money.
- Pending requests reserve allocation. Rejecting a request releases it.
- Ownership and role checks are enforced on the server, not just by hiding buttons.
- The database prevents duplicate event/attendee tickets.
- HMAC-SHA256 protects ticket data. Check-in updates only an unused ticket in a transaction.
- A sign-off is an authenticated approval record, not a certificate-based digital signature.
- Expiry uses the event date and server local time. There is one configured allocation period, with no automatic annual rollover.

There is no camera scanner, payment gateway, email delivery, university single sign-on or administrative account-management screen. A keyboard-type QR reader could supply the text, but the recorded walkthrough used copy and paste.

## Code evidence

The code was prepared with Codex assistance. No GitHub Copilot session was available, so this folder is not presented as proof of Copilot usage. If the lecturer requires that specific tool, its evidence remains an open submission item.

Tests, performance measurements and the real bug-fix record are in [6-Testing](../6-Testing/).
