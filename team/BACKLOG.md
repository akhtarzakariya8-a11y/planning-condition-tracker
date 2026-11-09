# Backlog

autonomy: calibration

`calibration` = every finished ticket is parked as a pull request for Zak, even GREEN ones.
Zak changes this line to `autonomy: on` when he is happy for GREEN work to merge itself.

**Target:** by 31 Jan 2027, five people outside Zak's circle have run their own decision
notice through the tool, and paying is possible. Features are a means to that, not the goal.

Status values: Ready, In review (PR link), Waiting on Zak, Done.
Zak can add ideas under "Inbox" at any time, in plain words.

## Ready (in order)

| # | Ticket | Lane | Depends on | Status |
| --- | --- | --- | --- | --- |
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

## Waiting on Zak

The complete list of things the team cannot do. Everything else it does.

- [ ] Switch on GitHub Pages for the repo (Settings, Pages, Source: GitHub Actions). Needed for ticket 4.
- [ ] Add the Supabase and Google sign-in keys in Streamlit Cloud (planned 19 Nov 2026). Needed for ticket 9.
- [ ] Send the fee-rise messages the scout drafts (7 Dec 2026).
- [ ] Publish the privacy policy and terms (16 Dec 2026).
- [ ] Open a Stripe account and add its keys (by 31 Jan 2027). Needed for ticket 10.
- [ ] Run `python3 eval/run_eval.py --jobs 7` when a pull request says EVAL NEEDED.

## Proposed (scout adds here, with an evidence line each)

_None yet._

## Inbox (Zak's ideas, unsorted)

_None yet._

## Done

| # | Ticket | Date | PR |
| --- | --- | --- | --- |
| 1 | Team setup: `team/` files, agent files, runbook, lanes in `CLAUDE.md`, CI | 2026-11-09 | setup pull request |
