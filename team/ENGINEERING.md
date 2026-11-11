# Engineering upgrade plan

Researched 9 Nov 2026 from the Claude Code and Streamlit documentation (sources at the
end). The product lead takes one upgrade ticket from here for every two product tickets
until Level 3 is done.

## The principle

The model is the same in every run. What makes a team of agents build like strong
engineers is the checking around it: tests that fail loudly, real examples to check
against, an independent review, and small changes. Plugins help only where they add one of
those. So this plan adds feedback loops first and tools second.

## Level 1: use what is already installed (done in this pull request)

- Builder and reviewer can now load skills. Before this they had no Skill tool, so the
  instruction to use the design skills could never work.
- Reviewer loads a code-review skill when one is available and runs at high effort.
- Builder loads testing, debugging and front-end design skills when the ticket calls for them.
- Product lead reads `team/MARKET.md` and this file, and pulls from Zak's Inbox.

## Level 2: guardrails in CI (each one an AMBER ticket)

| Ticket | What it adds | Why |
| --- | --- | --- |
| E1 | `ruff` lint and format check in CI | Catches dead code, unused imports and style drift on every pull request |
| E2 | App smoke test in CI with Streamlit's AppTest (this is ticket 2) | A page that crashes on load fails the build |
| E3 | Test coverage report with a floor that can only rise | Stops new code arriving untested |
| E4 | `pip-audit` on dependencies, plus Dependabot | Known-vulnerable packages are flagged automatically |
| E5 | GitHub secret scanning and push protection (Zak switches on, one setting) | A key can never reach this public repo |

## Level 3: prove the answers are right (the product is accuracy)

| Ticket | What it adds | Why |
| --- | --- | --- |
| E6 | Golden-file tests: the full rule output for each of the 7 saved notices is stored, and any change shows as a diff | Any change to gates, fees or dates becomes visible line by line before merge |
| E7 | Grow the notice set from 7 to 25+, across more councils and permission types | Seven notices is thin evidence for a tool people will rely on. The scout finds public notices; Zak confirms the answer key, because that judgement is the QS expertise |
| E8 | Run the eval in CI when a prompt file changes, using a repo secret with a spend cap (Zak adds the secret) | Prompt changes get scored automatically instead of waiting for a manual run |
| E9 | Property tests for the date maths | Dates are where silent errors hide: leap years, bank holidays, month ends |

## Level 4: see what users see

| Ticket | What it adds | Why |
| --- | --- | --- |
| E10 | Playwright screenshots of the landing page and app, desktop and phone, attached to each visual pull request | The reviewer and Zak judge the real page, not the code |
| E11 | Automated accessibility and performance check on the landing page | A professional page has to be readable and fast |

## Level 5: Claude Code mechanics (trial one at a time)

- **A hook that blocks edits to protected paths.** Today the off-limits rule
  (`.claude/`, the runbook, the lanes) is an instruction. The Claude Code docs say a rule
  that must hold every time belongs in a hook. Trial first: hooks in project agent files
  need the folder to be trusted, which may not hold in an unattended cloud run.
- **A hook that formats code after every edit**, once `ruff` is in.
- **A Python code-intelligence plugin** so agents find definitions and usages without
  reading whole files. From the official marketplace only.
- **Package the team as a plugin** when a second repo needs it (for example agency-radar).

Rule for anything installed: official marketplace or Zak's own only, one at a time,
through an AMBER pull request, after a one-ticket trial. Third-party plugins and
connectors run code and read the repo, so each one is a way for bad code to get in.

## Level 6: hosting, before anyone pays

Streamlit Community Cloud is where the app runs today. For a paid product it has hard
limits:

- Apps go to sleep after 12 hours without a visitor, and the next visitor sees a wake-up
  page. A paying customer should never see that.
- There is no paid tier to remove the limit (Streamlit staff, community forum).
- No custom domain, and about 1 GB of memory (third-party guides, UNVERIFIED against
  current official docs).
- Payment notifications from Stripe cannot be received reliably by an app that sleeps.

| Ticket | What it adds | Lane |
| --- | --- | --- |
| E12 | A Dockerfile so the same app runs on any host | AMBER |
| E13 | Choose and move to a host that stays awake, with a custom domain | RED for the account and cost; the team prepares everything |

Do E12 now. Do E13 when the first real user appears, and before ticket 10 (Stripe).
NOT RESEARCHED: host prices. The scout should compare three before E13.

## Updates (scout adds dated lines here)

- 2026-11-10 (coach) | E2 / ticket 2, the smoke test: give `at.secrets` dummy values before the
  first `.run()`, because Streamlit says a missing secret may stop the app from running. Keep
  every API call out by using `CT_FIXTURE_DIR`. Show the test fail against a deliberately broken
  page before trusting it, because a smoke test that cannot fail proves nothing.
  https://docs.streamlit.io/develop/concepts/app-testing/beyond-the-basics
- 2026-11-10 (coach) | Level 5: add a **Stop hook that runs `pytest`** as the first hook to trial.
  The Claude Code docs now describe a Stop hook as a deterministic gate: the agent cannot end
  its turn until the check passes. In an unattended run that is stronger than the written
  "run pytest before hand-over". The same trusted-folder caveat as the protected-paths hook
  applies, so trial it first, through an AMBER pull request.
  https://code.claude.com/docs/en/best-practices#give-claude-a-way-to-verify-its-work
- 2026-11-11 (coach) | E2 carried into ticket 3 and every new button: a Streamlit button is True only
  on the rerun its own click causes, so a result shown inside `if st.button(...)` disappears at the next
  click anywhere on the page. Keep the sample result in `st.session_state`, set it in an `on_click`
  callback, and initialise it behind an `if "key" not in st.session_state` guard; a forum case shows an
  unguarded initialisation line resetting the value on every rerun, inside AppTest too. The test should
  click, rerun once more and check the result is still on screen.
  https://docs.streamlit.io/develop/concepts/design/buttons ·
  https://discuss.streamlit.io/t/session-state-changes-within-button-onclick-not-making-it-back-to-apptest-instance/65127
- 2026-11-11 (coach) | Level 4, E10: the screenshots should also be judged on the first screen, not only
  "does it render". NN/g eyetracking (2018, 120 people, 1920x1080): 57% of viewing time above the fold,
  74% in the first two screens; keep the main call to action above the fold and avoid layouts that look
  finished before they are. For ticket 4: headline, one real output and the button visible without
  scrolling on desktop. https://www.nngroup.com/articles/scrolling-and-attention/
- 2026-11-11 (coach) | Level 5: Claude Code now ships a built-in `/verify` that "builds, runs, and
  observes the changes in your application" (also in the changelog, 2.1.309). The Claude Code team
  suggests trying it before writing project verify skills; they give no measured results. Trial `/verify`
  in one build run before writing any project skill. UNVERIFIED whether it works in an unattended cloud
  subagent. https://claude.com/blog/building-verification-loops-in-claude-code-with-skills ·
  https://code.claude.com/docs/en/changelog

## Sources

- Claude Code subagents (tools, skills, effort, hooks): https://code.claude.com/docs/en/sub-agents
- Claude Code skills: https://code.claude.com/docs/en/skills
- Claude Code hooks: https://code.claude.com/docs/en/hooks-guide
- Claude Code plugins: https://code.claude.com/docs/en/plugins
- Streamlit app testing: https://docs.streamlit.io/develop/concepts/app-testing
- Streamlit tests in CI: https://docs.streamlit.io/develop/concepts/app-testing/automate-tests
- Streamlit Community Cloud sleep: https://docs.streamlit.io/streamlit-cloud/get-started/manage-your-app
- No paid tier (forum): https://discuss.streamlit.io/t/stripe-webhook/120588
