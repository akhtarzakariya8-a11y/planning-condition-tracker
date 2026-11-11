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
| 2 | App smoke test: load `app.py` against the saved fixtures with no API call, so a broken page fails CI | GREEN | 1 | In review (https://github.com/akhtarzakariya8-a11y/planning-condition-tracker/pull/7) |
| 3 | "Try a sample notice" button: run the Lambeth 38-condition example from fixtures, no upload, no API cost | GREEN | 2 | Ready |
| 4 | Landing page v1 in `site/`: what it does, three real outputs from the sample, the fee-rise hook, one button to the tool | GREEN | 3, GitHub Pages on | Ready |
| 5 | README screenshots of the real outputs | GREEN | 3 | Ready |
| 6 | Move the practice scripts out of the repo root (the repo is public and is a portfolio piece) | AMBER | none | Ready |
| 7 | Prospect list and message drafts for the fee-rise outreach (scout, PROSPECTS step) | Scout | none; Zak sends on 7 Dec 2026 | Ready |
| 8 | Privacy policy as a draft page (`legal/`, not published) | AMBER | Zak publishes by 16 Dec 2026 | In review (https://github.com/akhtarzakariya8-a11y/planning-condition-tracker/pull/8) |
| 8b | Terms of use as a draft page (`legal/`, not published) | AMBER | Zak publishes by 16 Dec 2026 | Ready |
| 9 | Free-tier limit using `store.usage_count()` | AMBER | Saved projects live (Zak's keys, 19 Nov 2026) | Ready |
| 10 | Stripe checkout behind a switch, hidden until keys exist | AMBER | Zak's Stripe account; live by 31 Jan 2027 | Ready |
| 11 | Save drafts inside saved projects | AMBER | 9 | Ready |
| 12 | Deadline reminder emails | AMBER | An email provider account (Zak) | Ready |
| 13 | Trial a newer Sonnet model through the eval | AMBER | Zak runs the eval (about $0.50) | Ready |
| 14 | Client-ready report a consultant can send under their own name | GREEN | 3 | Ready |
| 15 | Lender pack: one page showing what is cleared and what blocks drawdown | AMBER | HYPOTHESIS: needs 3 lenders or monitoring surveyors to confirm first (Zak) | Waiting on Zak |
| 16b | Old name left only in places users barely see: `mcp_server/README.md` heading, `mcp_server/server.py` docstring, the `.ics` PRODID in `ct/programme.py`, `ct/__init__.py` docstring, `supabase/schema.sql` comment. Keep the MCP identifier `name="planning-condition-tracker"` (Zak's configs point at it) | AMBER | none; low value | Ready |
| 17 | Turn off Streamlit usage statistics (`[browser] gatherUsageStats = false` in `.streamlit/config.toml`); found writing ticket 8: the default sets a one-year `ajs_anonymous_id` cookie | AMBER | none | Ready |
| 18 | Host the Google Fonts in `theme/` so visitors' IPs are not sent to Google (found writing ticket 8) | GREEN | none | Ready |
| 19 | "Delete all my data": remove a user's projects and usage records; wrap `store.delete_project` in error handling (found writing ticket 8) | AMBER | 9 | Ready |
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

- [ ] **Review and merge PR #7 (ticket 2) first: it unblocks tickets 3, 4, 5 and 14, the top of the plan.** https://github.com/akhtarzakariya8-a11y/planning-condition-tracker/pull/7
- [ ] Privacy policy draft (PR #8): fill the placeholders, make the decisions in its "Notes for Zak" section, check the UNVERIFIED items, ideally have it reviewed. https://github.com/akhtarzakariya8-a11y/planning-condition-tracker/pull/8
- [ ] Check on the ICO website whether Aftergrant must pay the data protection fee, and pay it if so (money, so only Zak).
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

- **P1 (scout, 2026-11-10) "Scope for your quote" block at the top of the PDF summary.** One
  block a consultant uses to price a discharge job: conditions needing discharge; number of
  applications by stage; council fee per application and in total, today and for applications
  made on or after 8 Dec 2026; specialist reports to commission, by discipline; earliest
  commission-by date. Built only from existing outputs (`build_discharge_plan`, `build_specialists`,
  the programme). No new rule, number or caveat.
  - Evidence: small firms quote a fixed price after reading the notice, publish no discharge price,
    and bill discharge outside the planning-stage fee. Half the firm pages that state the council fee
    get it wrong. `team/research/2026-11-10-how-small-firms-discharge-conditions.md`
  - Who it helps: group 1 in `team/MARKET.md` section 4 (small consultancies and architects), at the
    unpaid quoting step. HYPOTHESIS that quoting time is unpaid; Zak's interviews can test it.
  - Smallest version: one block in `ct/reports.py build_pdf` above the existing discharge plan. Excel
    and the page can come later. Could be the first slice of ticket 14.
  - Expected lane: GREEN (layout in `ct/reports.py` only, no rule change); AMBER while `autonomy: calibration`.

- **P2 (coach, 2026-11-10) Put the TECHNIQUE ON TRIAL lines in the build log entry.** In
  `team/RUNBOOK.md` step 8, extend the entry format to end with
  `| trial: builder <TECHNIQUE ON TRIAL line>; reviewer <TECHNIQUE ON TRIAL line>`.
  - Evidence: `.claude/agents/coach.md` step 3a judges each trial only from those lines "in the newest
    build entry of `team/LOG.md`". The runbook's entry format has no field for them, so a conductor
    that follows the format exactly drops them. The coach also cannot fall back on the PR page:
    github.com did not load in the 2026-11-10 coach run. Without this field the daily trial cannot
    be judged, and every technique ends up dropped as "untested".
  - What changes: one line of `team/RUNBOOK.md`. No code, no tool, no new dependency.
  - Lane: AMBER (`team/RUNBOOK.md` is off-limits to agents and needs Zak).
  - Seen again 2026-11-11: github.com refused again. The conductor's manual copy into the 10 Nov entry
    worked, which is the case for making it the format. Consider adding the FIX count to the same field.

- **P3 (scout, 2026-11-11) Show the Planning Portal service charge next to the council fee.** The
  Discharge Planner and the PDF give the council fee per application (£309 / £89) and a total. Add one
  dated line under the total: submitting through the Planning Portal adds a service charge of up to
  £99 inc VAT per application where the council fee is over £100 (Band 1, from 3 Sep 2026); applying
  direct to the council may avoid it. Optionally show "up to £408 per application via the Portal".
  - Evidence: the Portal's FAQ (charge only where the planning fee is over £100; Band 1 £99, Band 2 £149)
    and banding guide (discharge "Band 0 or Band 1 – depends on development type/scale"). The Portal
    handles over 90% of applications. `team/research/2026-11-11-how-many-buyers-and-where-they-gather.md`
    and `team/EVIDENCE.md` 2026-11-11.
  - Who it helps: anyone using the fee and batching advice, mainly group 1 when quoting a client (P1).
    Each extra application costs up to about £408 today, not £309, so batching is worth more than the
    tool now says. The fee rise makes this bigger: about £534 per application after 8 Dec 2026.
  - Smallest version: one constant with a source comment and one caveat line in the Discharge Planner
    panel and the PDF. Do not add it into the council-fee total, because applicants can avoid it.
    Householder discharge (£89) is under the threshold today; at £125 how the Portal will band it is
    UNVERIFIED, so say "up to" and do not compute it for householders.
  - Expected lane: AMBER (a new number and caveat, in `ct/logic.py` or `ct/panels.py` and `ct/reports.py`).

- **P4 (coach, 2026-11-11) Let the reviewer apply adopted techniques.** Add one line to
  `.claude/agents/reviewer.md`: "Read the 'Adopted' section of `team/PLAYBOOK.md` and carry out every
  reviewer step listed there; report each under CHECKS." Do not let it read the builder's reasoning; the
  playbook is shared team rules, not the builder's work.
  - Evidence: Red/green proof was adopted on 2026-11-11 with a reviewer step (re-run one new test against
    `main`'s code and confirm it fails). The reviewer file gives it only the ticket, diff and test output,
    and `.claude/agents/product-lead.md` step 5 attaches only "Trial today". Once a technique leaves
    "Trial today", its reviewer half stops, and that half is what made the reviewer rate ticket 2 "better
    than usual" (`team/LOG.md`, 2026-11-10).
  - What changes: one line of one agent file. No code, no tool, no new dependency.
  - Interim: the product lead copies each adopted reviewer step into ACCEPTANCE CHECKS (`team/LESSONS.md`).
  - Lane: AMBER (`.claude/` is off-limits to agents and needs Zak).

## Inbox (Zak's ideas, unsorted)

_None yet._

## Done

| # | Ticket | Date | PR |
| --- | --- | --- | --- |
| 1 | Team setup: `team/` files, agent files, runbook, lanes in `CLAUDE.md`, CI | 2026-11-09 | https://github.com/akhtarzakariya8-a11y/planning-condition-tracker/pull/1 |
| 16 | Rename to Aftergrant everywhere a user sees it (leftovers moved to 16b) | 2026-11-10 | https://github.com/akhtarzakariya8-a11y/planning-condition-tracker/pull/5 and https://github.com/akhtarzakariya8-a11y/planning-condition-tracker/pull/6 |
