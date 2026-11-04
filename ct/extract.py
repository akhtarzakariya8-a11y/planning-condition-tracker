"""PDF in, analysis JSON out. The one place that talks to Claude for extraction."""
import base64
import io
import json
import os

import anthropic
import pdfplumber

from ct import config

# Set locally after extraction — never comes from the model.
FROM_SCAN_KEY = "_from_scan"
USAGE_KEY = "_usage"
COST_KEY = "_cost_usd"


class ExtractionError(Exception):
    """The model answered, but twice we couldn't use the answer.

    kind is "truncated" (the answer was cut off at the token ceiling) or "malformed" (not JSON).
    API failures (bad key, rate limit, outage) are NOT wrapped: they are anthropic.* errors, so
    the page can tell the user "it's us, not your file".
    """

    def __init__(self, kind, message):
        super().__init__(message)
        self.kind = kind


def get_client(api_key=None):
    key = api_key or os.environ.get("ANTHROPIC_API_KEY")
    return anthropic.Anthropic(api_key=key) if key else None


def strip_fences(text):
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip()


def system_prompt():
    # Read on every call rather than once at import: a long-running process (the MCP server,
    # a Streamlit session) then picks up prompt edits without a restart.
    return config.EXTRACTION_PROMPT_FILE.read_text(encoding="utf-8")


def pdf_to_content(file_bytes):
    """Return (user_content, is_scan).

    Digital PDFs send their text (fast, cheap). A scan has no text layer, so the PDF itself is
    sent and Claude reads it with vision — and every source_quote is then a transcription of an
    image rather than a copy, which the page has to tell the user.
    """
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        text = "".join(page.extract_text() or "" for page in pdf.pages)
    if len(text.strip()) >= 100:
        return text, False
    pdf_b64 = base64.standard_b64encode(file_bytes).decode("utf-8")
    return [
        {"type": "document",
         "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_b64}},
        {"type": "text", "text": "Analyse this planning decision notice."},
    ], True


def call_claude(client, system, user_content, max_tokens, temperature=0):
    """One call. Returns the raw message so the caller can inspect stop_reason and usage.

    Streamed rather than a plain create(): the SDK refuses a non-streaming request whose
    max_tokens could take it past ten minutes, which is exactly what the retry budget does.
    """
    with client.messages.stream(
        model=config.MODEL,
        max_tokens=max_tokens,
        # Extraction and classification, not creative writing: always take the most likely
        # reading so the same notice gives the same answer twice. The retry nudges this off zero
        # only because repeating an identical request reproduces an identical malformed response.
        temperature=temperature,
        system=system,
        messages=[{"role": "user", "content": user_content}],
    ) as stream:
        return stream.get_final_message()


def analyse_notice(client, user_content, max_tokens, temperature=0):
    """Kept for callers that want a single raw extraction call."""
    return call_claude(client, system_prompt(), user_content, max_tokens, temperature)


def call_for_json(client, system, user_content, budgets):
    """Call until the answer parses, trying each (max_tokens, temperature) in `budgets`.

    Two things can go wrong, and both are worth one retry rather than an apology.
      Truncation: verbatim source quotes roughly double the conditions array, so a very large
        notice can hit the ceiling and return JSON cut off mid-array.
      Malformed JSON: clause text contains quotation marks, and the model occasionally emits one
        unescaped. This is intermittent, so the same call usually succeeds second time.
    Returns (data, usage). Every attempt is billed, including the ones thrown away.
    """
    usage = {"input_tokens": 0, "output_tokens": 0}
    kind = "malformed"
    for max_tokens, temperature in budgets:
        msg = call_claude(client, system, user_content, max_tokens, temperature)
        usage["input_tokens"] += msg.usage.input_tokens
        usage["output_tokens"] += msg.usage.output_tokens
        if msg.stop_reason == "max_tokens":
            kind = "truncated"
            continue  # never parse a response that was cut off
        kind = "malformed"
        try:
            return json.loads(strip_fences(msg.content[0].text)), usage
        except json.JSONDecodeError:
            continue
    raise ExtractionError(kind, f"no usable answer after {len(budgets)} attempts ({kind})")


def extract(file_bytes, client):
    """Analyse one decision notice. Returns the analysis dict with _from_scan/_usage/_cost_usd."""
    user_content, is_scan = pdf_to_content(file_bytes)
    data, usage = call_for_json(
        client, system_prompt(), user_content,
        ((config.MAX_TOKENS, 0), (config.MAX_TOKENS_RETRY, 0.2)))
    data[FROM_SCAN_KEY] = is_scan
    data[USAGE_KEY] = usage
    data[COST_KEY] = round(config.cost_usd(usage), 4)
    return data
