# Student Club Event Ticketing and Budget Portal

**Name:** Shishir Hegde

**SRN:** PES1UG24CS438

**Section:** 5H

**Course:** Software Engineering

**Individual project:** Problem Statement 10

This project brings club event proposals, budget approvals and entry tickets into one portal. A Club Lead submits an event budget, the Faculty Coordinator, Finance Officer and Dean review it in order, and students register after approval. Check-in staff validate each QR ticket once.

## Submission folders

| Guideline item | Folder | Contents and status |
| --- | --- | --- |
| 1. Requirements Engineering | [1-Requirements-Engineering](1-Requirements-Engineering/) | Five FRs, two NFRs, acceptance criteria, RTM, use-case diagram and core flow. Complete documents. |
| 2. Architecture | [2-Architecture](2-Architecture/) | Comparison, component diagram, interface definitions and one-page justification. Complete documents. |
| 3. GitHub and Jira evidence | [3-Project-Evidence](3-Project-Evidence/) | Actual GitHub and application screenshots, plus a Jira task import CSV. Jira setup and its screenshot are pending. |
| 4. SRS and work breakdown | [4-SRS-and-Work-Breakdown](4-SRS-and-Work-Breakdown/) | SRS, business rules, data design and task breakdown. Complete documents. |
| 5. Code and Copilot evidence | [5-Code](5-Code/) | Runnable Python portal and setup instructions. Genuine GitHub Copilot evidence is pending. |
| 6. Testing and fixes | [6-Testing](6-Testing/) | 20 passing portal tests, a real failure/fix/retest record and measured load results. The lecturer's separate game exercise is pending. |

## Start with these files

- [Requirements and use-case flow](1-Requirements-Engineering/requirements-and-use-case.pdf)
- [Requirements traceability matrix](1-Requirements-Engineering/traceability-matrix.pdf)
- [Component diagram](2-Architecture/component-diagram.pdf)
- [Architecture justification](2-Architecture/architecture-justification.pdf)
- [SRS](4-SRS-and-Work-Breakdown/software-requirements-specification.pdf)
- [Work breakdown](4-SRS-and-Work-Breakdown/work-breakdown.pdf)
- [Test report](6-Testing/test-report.pdf)
- [Submission status and remaining items](SUBMISSION_STATUS.md)

Editable Word documents are next to their PDF copies. Requirements and the RTM also have CSV copies. The original Lab 1 document and image are kept in [originals](1-Requirements-Engineering/originals/) without changes. The assignment documents are in [references](references/).

## Run the prototype

Python was used because the browser forms, SQLite storage and QR generation are simpler to put together than in C or C++ for this project. JavaScript is only used for dashboard refresh, with plain HTML and CSS for the pages.

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r 5-Code/requirements-dev.txt
cd 5-Code
..\.venv\Scripts\python.exe -m flask --app app seed-demo
..\.venv\Scripts\waitress-serve.exe --host=127.0.0.1 --port=5000 --threads=16 --call app:create_app
```

Open `http://127.0.0.1:5000`. The local demo usernames are `lead`, `faculty`, `finance`, `dean`, `student`, `student2` and `gate`. The demo password is `club-demo-2026`. These are sample accounts, not university credentials. Keep the demo on localhost.

The code README includes Linux/macOS commands and a walkthrough. From the repository root, run the tests with:

```powershell
.\.venv\Scripts\python.exe -m pytest 6-Testing/test_portal.py -q
```

## Current limits

The functional test suite passes. The final local benchmark completed all 500 page requests, but not every response stayed below two seconds. Sequential check-ins were below 100 ms; the concurrent check-in test exceeded that target. The performance requirements are therefore not marked fully satisfied.

The repository does not claim that a Jira project was created or that GitHub Copilot generated the code. The implementation and documents were prepared with AI assistance using Codex; actual test outputs and application screenshots are included. The separate game-testing repository has not been supplied, so the portal tests do not replace that assignment.
