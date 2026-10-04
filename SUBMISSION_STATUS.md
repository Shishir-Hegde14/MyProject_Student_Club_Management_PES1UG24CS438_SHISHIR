# Individual project submission status

Shishir Hegde | PES1UG24CS438 | Section 5H

This list follows the individual-project section of the supplied submission guidelines. It does not include the team mini-project's deployment or demo-video requirements.

## Completed

- Numbered folders, root README and folder-level instructions.
- Revised requirements with exactly five FRs and two NFRs, including type, priority, acceptance criteria and rationale.
- Requirements traceability matrix in Word, PDF and CSV.
- Revised use-case diagram and a one-page core flow within the requirements document.
- Architecture comparison, seven-component diagram with provided/required interfaces, and a one-page justification.
- SRS and work breakdown documents.
- Working local portal for proposals, approvals, registration, signed QR tickets and check-in.
- Automated functional, security and concurrency tests: 20 passed.
- An actual malformed-ticket failure, the code patch and a complete retest.
- Real screenshots from the browser walkthrough and the organised GitHub repository.
- Original repository files preserved byte-for-byte in their new folders.

## Prepared but not completed externally

| Item | What is available | What is still needed |
| --- | --- | --- |
| Jira project evidence | `3-Project-Evidence/jira-tasks.csv`, containing the work breakdown as importable tasks | Access to the correct Jira site, creation/import of tasks and an actual screenshot. A CSV is not evidence that this happened. |
| GitHub Copilot evidence | Working code in `5-Code`, with its origin stated | A real GitHub Copilot session or verifiable Copilot-generated code, if that specific tool is required. Codex work is not labelled as Copilot work. |
| Lecturer-supplied game testing | A completed portal testing exercise showing the same test/fix/retest process | The supplied game repository and its four test cases. No substitute game or invented results have been added. |

## Verification still open

- NFR-001: concurrent check-in did not meet the under-100 ms target in the final local run.
- NFR-002: all 500 page requests completed, but some exceeded two seconds. Browser-render timing and physical mobile-device testing remain open.
- QR scanning was demonstrated by pasting real ticket data into the running application. A physical scanner was not used.
- The GitHub screenshot records the repository's current state. It is not presented as a screenshot of the original repository-creation moment.

Details, timings and the test method are in `6-Testing/results/performance.json` and `6-Testing/test-report.pdf`.
