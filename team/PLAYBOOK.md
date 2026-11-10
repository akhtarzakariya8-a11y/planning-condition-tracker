# Playbook

How this team builds, beyond `CLAUDE.md`. Rule: **learn, trial, adopt.** A technique from
outside is tried on the next day's ticket, compared with how we worked before, and kept
only if it helped. Adopted techniques are dropped again if they later cause a FIX or KILL. Keep this file under 60 lines: to add one, merge or remove one.

## Adopted (with the evidence)

_None yet._

## Trial today (one at a time, a new one each day)

**Red/green proof** (set 2026-11-10; first day). Every new test is seen to fail before it is trusted.
Sources: https://simonwillison.net/guides/agentic-engineering-patterns/red-green-tdd/ ·
"show evidence rather than asserting success", https://code.claude.com/docs/en/best-practices
- Builder: write the new test first and run it before changing product code; paste the failing
  line (red). Make the change; paste the passing line (green). A guard test that already passes
  on today's code (e.g. the ticket 2 smoke test) is proved by breaking the page on purpose, seeing
  red, then reverting. Both lines go under TESTS in the hand-over.
- Reviewer: check both lines are there; re-run one new test against `main`'s product code and confirm it fails.
- Helped if: a test was corrected because the red step showed it could not fail, or the reviewer
  rates it "better". No new test that passes without the change. Same with no gain: drop.

## Candidates (the coach adds these, one line each, with a source link)

- **Reviewer flags only gaps that break correctness or the ticket's checks**; style goes in an "optional" list that never triggers FIX. With one FIX round then KILL, a reviewer chasing preferences can kill sound work; the docs warn a reviewer asked for gaps always finds some. https://code.claude.com/docs/en/best-practices#add-an-adversarial-review-step
- **A lesson seen twice becomes a check**: the next E-ticket turns it into a test, lint rule or agent-file line, not another note. Volkov, AI Engineer World's Fair 2026 (written version): https://ai.engineer/talks/the-z-l-continuum-should-ai-engineers-still-read-code ; the docs say the same of CLAUDE.md rules ("convert it to a hook").
- **Error analysis before new eval fields** (E7): read the raw model output on each new notice and name the failure types seen before writing answer-key fields; no rubric before data. Hamel Husain (teaches an AI evals course): https://hamel.dev/notes/llm/ai-product-engineering/evals-error-analysis.html
- **Every ticket ends with one end-to-end check** a user would recognise (e.g. with `CT_FIXTURE_DIR`, upload the Lambeth PDF, see the result) on top of the unit checks. https://code.claude.com/docs/en/best-practices#let-claude-interview-you
- **Tool, not yet proposed (UNVERIFIED):** Streamlit's own `agent-skills` (`developing-with-streamlit`, 17 sub-skills: performance, code organisation, design, session state). It could stop agents writing deprecated Streamlit calls. No measured evidence. A mirror says it runs `scripts/discover.py` and needs Streamlit 1.57+. Read the repo itself before proposing it. https://www.snowflake.com/en/developers/guides/build-streamlit-apps-with-agent-skills/

## To study (Zak, the scout or the coach can add links, including YouTube videos)

_None yet._

## To study (needs Zak's computer)

Videos the coach found but could not read in a cloud run. Zak can ask Claude on his own
computer to transcribe these and add the notes here.

- https://www.youtube.com/watch?v=ZpK5PWX2YRM Alex Volkov, "The Z/L Continuum: should AI engineers still read code?" Written version read; the transcript would show his rule for which changes need line-by-line human review (compare with our lanes).
- https://www.youtube.com/watch?v=so9l_MwS2yg Zack Proser (WorkOS), "Your attention is the bottleneck". Three verification gates (code, behaviour, requirements review) and mining session logs for new skills. Mostly anecdotal by his own account.

## Dropped (one line each, with the reason)

_None yet._
