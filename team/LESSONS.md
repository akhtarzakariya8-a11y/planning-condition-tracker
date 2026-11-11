# Lessons

What went wrong or right in our own runs. One dated line each, newest first.
A KILL always adds a line here. Read before planning.

2026-11-11 | coach | Adopted techniques reach the builder (it reads `team/PLAYBOOK.md`) but not the reviewer (it gets only the ticket, diff and test output), and the product lead attaches only "Trial today". So the reviewer half of Red/green proof would silently stop. Fix proposed as P4. Until then, product lead: copy each reviewer step under "Adopted" into ACCEPTANCE CHECKS.
2026-11-11 | coach | Seen twice: the coach cannot see pull requests (github.com refused 10 and 11 Nov; no shell for `git log` on 11 Nov), so reviewer notes reach it only through `team/LOG.md`. The conductor's copy of both trial lines into the 10 Nov build entry worked and let the trial be judged; keep doing it, plus the FIX count, until P2 lands.

2026-11-10 | coach | Trial verdicts can get lost. The coach judges a trial from the TECHNIQUE ON TRIAL lines in `team/LOG.md`, but the build-entry format in `team/RUNBOOK.md` has no field for them. The coach's cloud run also could not open the PR page on github.com. Fix proposed as P2 in `team/BACKLOG.md`. Until then, the conductor should copy both lines into the log entry.
