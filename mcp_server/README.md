# Planning Condition Tracker — MCP server

The planning tool, exposed over the Model Context Protocol so an AI assistant (Claude Desktop,
Claude Code, Cursor, ChatGPT…) can call it as tools in the middle of a conversation.
Same brain as the Streamlit app (`../prompt_v4_production.txt`) and the same rules: it imports
the project's `ct/` package, so it can never drift out of step with the web page.

| Kind | Name | What it does |
|---|---|---|
| Tool | `list_notices` | Lists the PDFs in `notices/` |
| Tool | `begin_by_date` | Decision date + time limit → start-by date (no AI) |
| Tool | `analyse_notice` | Extracts every condition (calls Claude; cached in `.cache/` until the prompt changes) |
| Tool | `what_blocks_start` | The Safety Gate: hard blockers, piling, above-ground only, ambiguous |
| Tool | `discharge_plan` | How many discharge applications, bundled by stage, and the council fees |
| Tool | `plan_programme` | Your dates in → submit-by and commission-by deadlines, late flags, fee-rise saving (no AI) |
| Tool | `draft_discharge_application` | First draft of one application: covering letter + what to submit per condition (one paid call) |
| Resource | `notice://{filename}` | Raw text of a notice |
| Prompt | `site_start_briefing` | One-page "can we start on site?" briefing |

## Set up (Mac, once)

```bash
cd ~/summer-project/mcp_server
python3 --version                      # needs 3.10 or newer
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python test_client.py        # lists tools, calls the free ones
.venv/bin/python test_client.py --analyse   # real run on the Lambeth notice (uses the API key in ../.env)
```

## Connect to Claude Desktop

Claude menu → Settings… → Developer → Edit Config, add this inside `"mcpServers"`, save, then quit
and reopen Claude Desktop:

```json
"planning-condition-tracker": {
  "command": "/Users/zakariyaakhtar/summer-project/mcp_server/.venv/bin/python",
  "args": ["/Users/zakariyaakhtar/summer-project/mcp_server/server.py"]
}
```

Logs: `~/Library/Logs/Claude/mcp-server-planning-condition-tracker.log`

## Connect to Claude Code

```bash
claude mcp add planning-condition-tracker -- \
  /Users/zakariyaakhtar/summer-project/mcp_server/.venv/bin/python \
  /Users/zakariyaakhtar/summer-project/mcp_server/server.py
```

## Add notices

Drop any decision-notice PDF into `notices/`. The AI can only see that folder.

## After changing the prompt or the rules

Quit and reopen Claude Desktop so it restarts the server. Saved analyses in `.cache/` are keyed
to the prompt's fingerprint, so a changed prompt re-analyses each notice once, automatically.
