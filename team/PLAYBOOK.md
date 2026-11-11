# Playbook

How this team builds, beyond `CLAUDE.md`. Rule: **learn, trial, adopt.** A technique from
outside is tried on the next day's ticket, compared with how we worked before, and kept
only if it helped. Adopted techniques are dropped again if they later cause a FIX or KILL. Keep this file under 60 lines: to add one, merge or remove one.

## Adopted (with the evidence)

- **Red/green proof** (trial 2026-11-10 on ticket 2; adopted 2026-11-11). Every new test is seen to fail
  before it is trusted. Builder: paste the failing line (red) and the passing line (green) under TESTS; a
  guard test that already passes is proved by a deliberate break, then revert. Reviewer: re-run one new
  test against `main`'s product code and confirm it fails. Evidence (ticket 2, PR #7): builder "helped a
  little", both smoke tests failed on a deliberate break and one loose assertion was tightened; reviewer
  "better than usual", repeated the red step and both failed. One ticket of evidence only.
  https://simonwillison.net/guides/agentic-engineering-patterns/red-green-tdd/

## Trial today (one at a time, a new one each day)

**User-journey check** (set 2026-11-11; first day). Each ticket that changes the page gets one test that
does what a user does, checks what they would see, then does one more thing and checks it is still there.
Why: a Streamlit button is True only on the rerun its own click causes, so a result shown inside
`if st.button(...)` vanishes at the next click anywhere (https://docs.streamlit.io/develop/concepts/design/buttons);
an unguarded session-state line resets a callback's value, also inside AppTest
(https://discuss.streamlit.io/t/session-state-changes-within-button-onclick-not-making-it-back-to-apptest-instance/65127).
- Builder: in AppTest with `CT_FIXTURE_DIR`, do the user's action (ticket 3: click "Try a sample notice"),
  assert on text a planning consultant would recognise (condition count, start deadline), rerun once more
  without clicking, assert it is still shown. Red/green applies. UNVERIFIED that a bare `.run()` resets the
  button in AppTest; if not, interact with another widget instead.
- Reviewer: say whether the test checks what a user sees, not internals; move the result inside
  `if st.button` on the branch and confirm the test fails.
- Helped if: it catches a bug the other tests missed, or the reviewer rates it "better". No page change: untested.

## Candidates (the coach adds these, one line each, with a source link)

- **Reviewer flags only gaps that break correctness or the ticket's checks**; style goes in an "optional" list that never triggers FIX. With one FIX round then KILL, a reviewer chasing preferences can kill sound work; the docs warn a reviewer asked for gaps always finds some. https://code.claude.com/docs/en/best-practices#add-an-adversarial-review-step
- **A lesson seen twice becomes a check**: the next E-ticket turns it into a test, lint rule, agent-file line or project verify skill, not another note. Try Claude Code's built-in `/verify` ("builds, runs, and observes the changes") before writing our own; no measured results given. Volkov: https://ai.engineer/talks/the-z-l-continuum-should-ai-engineers-still-read-code · Claude Code team: https://claude.com/blog/building-verification-loops-in-claude-code-with-skills
- **Error analysis before new eval fields** (E7): read the raw model output on each new notice and name the failure types seen before writing answer-key fields; no rubric before data. Hamel Husain (teaches an AI evals course): https://hamel.dev/notes/llm/ai-product-engineering/evals-error-analysis.html
- **First-screen check on landing page work** (ticket 4): headline, one real output and the button visible without scrolling at 1920x1080, nothing that looks like the page ends there. NN/g eyetracking 2018 (120 people): 57% of viewing time above the fold, 74% in the first two screens. Phone: UNVERIFIED by this study. https://www.nngroup.com/articles/scrolling-and-attention/
- **Tool, not yet proposed (UNVERIFIED):** Streamlit's own `agent-skills` (`developing-with-streamlit`). Could stop agents writing deprecated Streamlit calls. No measured evidence. skills.sh lists publisher `streamlit`, needs Streamlit 1.57+ (we pin 1.58.0), runs `scripts/discover.py`. github.com/streamlit/agent-skills refused to load 2026-11-11; read it before proposing. https://www.snowflake.com/en/developers/guides/build-streamlit-apps-with-agent-skills/

## To study (Zak, the scout or the coach can add links, including YouTube videos)

_None yet._

## To study (needs Zak's computer)

Videos the coach found but could not read in a cloud run. Zak can ask Claude on his own
computer to transcribe these and add the notes here.

- https://www.youtube.com/watch?v=ZpK5PWX2YRM Alex Volkov, "The Z/L Continuum: should AI engineers still read code?" Written version read; the transcript would show his rule for which changes need line-by-line human review (compare with our lanes).
- https://www.youtube.com/watch?v=so9l_MwS2yg Zack Proser (WorkOS), "Your attention is the bottleneck". Three verification gates (code, behaviour, requirements review) and mining session logs for new skills. Mostly anecdotal by his own account.

## Dropped (one line each, with the reason)

_None yet._
