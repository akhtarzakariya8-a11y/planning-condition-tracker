# Team log

## Status (the conductor rewrites this block every run)

WATCH (fee fact, unverified): the England discharge fee rise to £435 / £125 on 8 Dec 2026 is still not confirmed as made. 2026-11-11: the House of Lords approved the draft SI on 14 Oct 2026; Commons approval and the made SI could not be confirmed (Parliament and legislation.gov.uk pages failed to load), and the Planning Portal still calls the rise conditional. `ct/logic.py` says the Commons approved it on 27 Oct. If it is not made by 8 Dec, the automatic switch will show the wrong fee. Re-check 1 to 8 Dec (agenda item).
Last run: 2026-11-11, build run: ticket 8 draft privacy policy (unpublished, `legal/`) parked for Zak as PR #8.
Waiting on Zak: 0 pull requests (Zak merged PR #7 and PR #8 on 2026-11-11; ticket 3 is now unblocked).

## Entries (newest first)

`YYYY-MM-DD | ticket | lane | verdict | PR link | what changed, one line | anything that failed`

2026-11-11 | 8 Privacy policy draft (first slice; terms split to 8b) | AMBER | PASS after one FIX | https://github.com/akhtarzakariya8-a11y/planning-condition-tracker/pull/8 | new legal/privacy-policy-draft.md: plain-English draft, every own-data claim cited to code, third-party claims UNVERIFIED, placeholders for controller details; nothing links to it; 26 tests pass | add_repo tool not offered (repo was already attached with push access); builder had no web access so all provider facts are UNVERIFIED; reviewer FIX round 1 (email recorded with every signed-in analysis, not only on Save; database security overstated), PASS round 2; spotted Streamlit usage-stats cookie on by default, new tickets 17-19 | trial: builder User-journey check not applied (no page change); reviewer not applied (no page change)

2026-11-11 | scout + coach | how many small planning consultancies and SME developers there are, and where they gather: team/research/2026-11-11-how-many-buyers-and-where-they-gather.md | facts: unchanged; unverified: Commons approval and making of the 8 Dec fee SI (Lords approved 14 Oct), Wales fees (page refused) | last trial: Red/green proof ADOPTED (one ticket of evidence) | technique on trial next: User-journey check | items proposed: P3 show Planning Portal service charge beside the council fee (AMBER), P4 reviewer reads the playbook's Adopted section (AMBER), note added to P2 | several legislation.gov.uk and Parliament pages refused; coach had no shell so could not read git log or PR #7; github.com/streamlit/agent-skills refused; ticket 7 prospects not started (due before 7 Dec)

2026-11-10 | 2 App smoke test (E2) | GREEN files, AMBER under calibration | PASS | https://github.com/akhtarzakariya8-a11y/planning-condition-tracker/pull/7 | new tests/test_app_smoke.py loads the home page and the Lambeth notice from fixtures with no API call; 28 tests pass, CI green | builder commit trailer used session attribution lines instead of the routine's single Co-Authored-By line (not amended: no force-push) | trial: builder Red/green proof helped a little (both tests shown to fail on a deliberate break; tightened one loose assertion); reviewer Red/green proof better than usual (repeated the red step, both tests failed)

2026-11-10 | scout + coach | how small firms discharge conditions and what they charge: team/research/2026-11-10-how-small-firms-discharge-conditions.md | facts: unchanged; unverified: Parliament approval of the 8 Dec fee regs, DMPO Sch 6 exclusions | last trial: none (no build yet) | technique on trial next: Red/green proof | items proposed: P1 scope-for-your-quote block in PDF (GREEN, AMBER under calibration), P2 trial lines in build log format (AMBER) | some pages blocked (fetch approval not answered); youtube-transcriber needs Chrome, 2 videos parked for Zak's computer

2026-11-09 | 1 Team setup | AMBER | n/a | https://github.com/akhtarzakariya8-a11y/planning-condition-tracker/pull/1 | team files, agents, runbook, lanes and CI added | nothing
