# Backlog

autonomy: calibration

`calibration` = every finished ticket is parked as a pull request for Zak, even GREEN ones.
Zak changes this line to `autonomy: on` when he is happy for GREEN work to merge itself.

**Target:** by 31 Jan 2027, five people outside Zak's circle have run their own decision
notice through the tool, and paying is possible. Features are a means to that, not the goal.

Status values: Ready, In review (PR link), Waiting on Zak, Done.
Zak can add ideas under "Inbox" at any time, in plain words.

## Ready

Order: product tickets follow section 5 of `team/MARKET.md`; after every two product
tickets, one E ticket from `team/ENGINEERING.md`, lowest level first.

| # | Ticket | Lane | Depends on | Status |
| --- | --- | --- | --- | --- |
| 16 | Rename the product to Aftergrant everywhere a user sees it: app title and page text, README, exports (Excel, PDF, Word), MCP server descriptions. Tagline: "From planning permission to start on site". Leave the repo name, file names and live URL alone | AMBER | none. Do this before ticket 4 so the landing page launches with the right name | Ready |
| 2 | App smoke test: load `app.py` against the saved fixtures with no API call, so a broken page fails CI | GREEN | 1 | Ready |
| 3 | "Try a sample notice" button: run the Lambeth 38-condition example from fixtures, no upload, no API cost | GREEN | 2 | Ready |
| 4 | Landing page v1 in `site/`: what it does, three real outputs from the sample, the fee-rise hook, one button to the tool | GREEN | 3, GitHub Pages on | Ready |
| 5 | README screenshots of the real outputs | GREEN | 3 | Ready |
| 6 | Move the practice scripts out of the repo root (the repo is public and is a portfolio piece) | AMBER | none | Ready |
| 7 | Prospect list and message drafts for the fee-rise outreach (scout, PROSPECTS step) | Scout | none; Zak sends on 7 Dec 2026 | Ready |
| 8 | Privacy policy and terms as draft pages | AMBER | Zak publishes by 16 Dec 2026 | Ready |
| 9 | Free-tier limit using `store.usage_count()` | AMBER | Saved projects live (Zak's keys, 19 Nov 2026) | Ready |
| 10 | Stripe checkout behind a switch, hidden until keys exist | AMBER | Zak's Stripe account; live by 31 Jan 2027 | Ready |
| 11 | Save drafts inside saved projects | AMBER | 9 | Ready |
| 12 | Deadline reminder emails | AMBER | An email provider account (Zak) | Ready |
| 13 | Trial a newer Sonnet model through the eval | AMBER | Zak runs the eval (about $0.50) | Ready |
| 14 | Client-ready report a consultant can send under their own name | GREEN | 3 | Ready |
| 15 | Lender pack: one page showing what is cleared and what blocks drawdown | AMBER | HYPOTHESIS: needs 3 lenders or monitoring surveyors to confirm first (Zak) | Waiting on Zak |
| E1 | `ruff` lint and format check in CI | AMBER | none | Ready |
| E3 | Coverage report with a floor that can only rise | AMBER | E1 | Ready |
| E4 | `pip-audit` and Dependabot | AMBER | none | Ready |
| E6 | Golden-file tests over the 7 saved notices | GREEN | none | Ready |
| E7 | Grow the notice set from 7 to 25+ (scout finds public notices; Zak confirms the answer key) | AMBER | Zak confirms answers | Ready |
| E8 | Run the eval in CI when a prompt changes | AMBER | Zak adds an API key secret with a spend cap | Waiting on Zak |
| E9 | Property tests for the date maths | AMBER | E6 | Ready |
| E10 | Playwright screenshots attached to visual pull requests | AMBER | 4 | Ready |
| E11 | Accessibility and performance check on the landing page | AMBER | 4 | Ready |
| E12 | Dockerfile so the app runs on any host | AMBER | none | Ready |
| E13 | Move to a host that stays awake, with a custom domain | RED | First real user; before ticket 10. Scout compares three hosts first | Waiting on Zak |

## Waiting on Zak

The complete list of things the team cannot do. Everything else it does.

- [ ] Aftergrant name checks before spending on it: search Companies House and the UK trade mark register for "Aftergrant", then buy the domain.
- [ ] Renaming the GitHub repo or the Streamlit URL: tell Claude first, because the scheduled runs point at the current repo name.
- [ ] Switch on GitHub Pages for the repo (Settings, Pages, Source: GitHub Actions). Needed for ticket 4.
- [ ] Add the Supabase and Google sign-in keys in Streamlit Cloud (planned 19 Nov 2026). Needed for ticket 9.
- [ ] Send the fee-rise messages the scout drafts (7 Dec 2026).
- [ ] Publish the privacy policy and terms (16 Dec 2026).
- [ ] Open a Stripe account and add its keys (by 31 Jan 2027). Needed for ticket 10.
- [ ] Run `python3 eval/run_eval.py --jobs 7` when a pull request says EVAL NEEDED.
- [ ] Talk to five consultants or developers using the questions in `team/MARKET.md` section 6. This is the most valuable item on the list.
- [ ] Switch on GitHub secret scanning and push protection (Settings, Code security). Ticket E5.
- [ ] Confirm the answer key for new test notices (ticket E7).
- [ ] Add an API key as a repo secret with a spend cap (ticket E8).
- [ ] Pick and pay for a host that stays awake (ticket E13), when the first real user appears.

## Proposed (scout adds here, with an evidence line each)

_None yet._

## Inbox (Zak's ideas, unsorted)

_None yet._

## Done

| # | Ticket | Date | PR |
| --- | --- | --- | --- |
| 1 | Team setup: `team/` files, agent files, runbook, lanes in `CLAUDE.md`, CI | 2026-11-09 | https://github.com/akhtarzakariya8-a11y/planning-condition-tracker/pull/1 |
