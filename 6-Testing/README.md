# Testing and defect correction

Shishir Hegde | PES1UG24CS438 | Section 5H

- [Test plan and execution report PDF](test-report.pdf) / [Word](test-report.docx)
- [Automated tests](test_portal.py)
- [Initial test output](results/initial-tests.txt): 19 passed, 1 failed
- [Fix](results/ticket-validation-fix.patch)
- [Retest output](results/final-tests.txt): 20 passed
- [Final performance measurements](results/performance.json)

## Reproduce the tests

From the repository root, after installing `5-Code/requirements-dev.txt`:

```powershell
.\.venv\Scripts\python.exe -m pytest 6-Testing/test_portal.py -q
.\.venv\Scripts\python.exe 6-Testing/benchmark.py --output 6-Testing/results/performance-new-run.json
```

On Linux/macOS, use `.venv/bin/python` instead. The benchmark creates a temporary database and uses an unused loopback port. It does not modify the normal demonstration database. Results vary by machine and current load.

## Actual defect and patch

TC17 sent a malformed signature containing non-ASCII characters. Before the fix, `hmac.compare_digest` raised `TypeError`. The code now checks signature length and hexadecimal characters before comparing it. The failure came from the first real test run; the saved patch and subsequent passing results show the correction.

The pre-fix version is commit `50bfb25`. To inspect it without changing current work, use a separate checkout/worktree. Do not reverse the patch on the submitted working copy just to reproduce the issue.

## What the performance test measures

The final test uses Waitress with 16 threads and 500 distinct pre-authenticated clients released together. It measures a complete HTML response on loopback. It does not include browser painting, real network delay, a physical scanner or 500 simultaneous registrations. Check-in requests use actual signed tickets and exercise staff checks, CSRF validation and the database update.

| Final local workload | Successes | Median | P95 | Maximum |
| --- | --- | --- | --- | --- |
| 500 concurrent page requests | 500 / 500 | 1287.16 ms | 1946.67 ms | 2167.95 ms |
| 50 sequential check-ins | 50 / 50 | 27.44 ms | 29.61 ms | 33.97 ms |
| 50 check-ins with 20 workers | 50 / 50 | 171.32 ms | 411.50 ms | 715.13 ms |

The sequential check-in target passed. The peak check-in target and the requirement that every page complete below two seconds did not. Neither NFR is marked fully met.

Earlier diagnostic runs are also retained. Their default Windows proxy lookup added overhead, so they should not be used as direct application-speed comparisons. The final benchmark explicitly uses a direct loopback connection. `python-packages.txt` records the installed versions.

## Lecturer-supplied game exercise

The individual-project guidelines mention a separate game repository with four test cases. That repository was not included in the supplied files. This folder contains testing of the club portal only. When the lecturer provides the game, its original tests, actual failure, patch, retest and repository link must be added separately.
