"""Model settings and prices. Change the model here and every caller follows."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # the repo folder
EXTRACTION_PROMPT_FILE = ROOT / "prompt_v4_production.txt"
DRAFTING_PROMPT_FILE = ROOT / "prompt_drafting.txt"

# Sonnet 4.5's output ceiling is 64k. Verbatim source quotes are the first feature big enough to
# threaten the old 8k budget on a large notice, so there is deliberate headroom here.
MODEL = os.environ.get("CT_MODEL", "claude-sonnet-4-5")
MAX_TOKENS = 20000
MAX_TOKENS_RETRY = 32000
DRAFT_MAX_TOKENS = 12000

# Claude Sonnet 4.5 list price, US dollars per million tokens. Only used to report what each
# notice costs to analyse — the floor under any price you charge. Update if you change MODEL.
PRICE_IN_PER_MTOK = 3.0
PRICE_OUT_PER_MTOK = 15.0

# A batch upload runs notices in parallel; this caps how many at once and in total.
BATCH_MAX_FILES = 10
BATCH_WORKERS = 4

# Anthropic request limit is ~32MB; base64 inflates ~33%, so cap the raw file.
MAX_PDF_BYTES = 24_000_000


def cost_usd(usage):
    """Dollar cost of a usage dict {"input_tokens", "output_tokens"}."""
    if not usage:
        return 0.0
    return (usage.get("input_tokens", 0) * PRICE_IN_PER_MTOK
            + usage.get("output_tokens", 0) * PRICE_OUT_PER_MTOK) / 1_000_000
