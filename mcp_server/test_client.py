"""
A tiny MCP CLIENT. It starts server.py and talks to it over stdio — exactly what Claude Desktop
does behind the scenes, just without the chat window and without an AI choosing the tools.

  .venv/bin/python test_client.py              quick check: lists everything, calls the free tools
  .venv/bin/python test_client.py --analyse    also runs the Safety Gate on the Lambeth notice
                                               (calls the Anthropic API once, then it's cached)
"""
import asyncio
import json
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters

SERVER = Path(__file__).resolve().parent / "server.py"
LAMBETH = "21_04939_FUL--3474437.pdf"


def show(result):
    """Print a tool result: the structured data if there is any, otherwise the text."""
    if result.is_error:
        print("  ERROR:", result.content[0].text)
    elif result.structured_content is not None:
        print(json.dumps(result.structured_content, indent=2)[:4000])
    else:
        print(" ", result.content[0].text)


async def main():
    # "Launch this command and talk to it over stdin/stdout" — the same thing the
    # "command" + "args" lines in claude_desktop_config.json tell Claude Desktop to do.
    params = StdioServerParameters(command=sys.executable, args=[str(SERVER)])

    async with Client(params) as client:
        print("Connected to:", client.server_info.name if client.server_info else "?")

        tools = await client.list_tools()
        print("\nTOOLS the AI can call:")
        for t in tools.tools:
            print(f"  - {t.name}: {t.description.splitlines()[0]}")
            print(f"      input schema: {json.dumps(t.input_schema.get('properties', {}))}")

        templates = await client.list_resource_templates()
        print("\nRESOURCE TEMPLATES:", [t.uri_template for t in templates.resource_templates])

        prompts = await client.list_prompts()
        print("PROMPTS:", [p.name for p in prompts.prompts])

        print("\nCALL begin_by_date('10 November 2025', 3):")
        show(await client.call_tool("begin_by_date",
                                    {"decision_date": "10 November 2025", "time_limit_years": 3}))

        print("\nCALL list_notices():")
        show(await client.call_tool("list_notices", {}))

        print("\nCALL analyse_notice('../.env')  <- should be refused:")
        show(await client.call_tool("analyse_notice", {"filename": "../.env"}))

        print(f"\nREAD resource notice://{LAMBETH}  (first 300 characters):")
        res = await client.read_resource(f"notice://{LAMBETH}")
        print(" ", res.contents[0].text[:300].replace("\n", " "), "...")

        print("\nGET prompt site_start_briefing:")
        prompt = await client.get_prompt("site_start_briefing", {"filename": LAMBETH})
        print(" ", prompt.messages[0].content.text[:200], "...")

        if "--analyse" in sys.argv:
            print(f"\nCALL what_blocks_start('{LAMBETH}')  (first run takes a minute or two):")
            show(await client.call_tool("what_blocks_start", {"filename": LAMBETH}))


if __name__ == "__main__":
    asyncio.run(main())
