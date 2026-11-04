"""Condition Tracker core — everything that is NOT the web page.

app.py (the Streamlit page), eval/run_eval.py (the accuracy test) and mcp_server/server.py
(the version Claude Desktop can call) all import from here, so a rule changed once is
changed everywhere. Nothing in this package imports Streamlit, except ct.panels, which only
builds HTML strings with the theme helpers.

    ct.config     model, token budgets, prices
    ct.extract    PDF -> text -> Claude -> JSON (with retries and cost)
    ct.logic      the rules: gates, start deadline, fees, discharge plan, flags, specialists
    ct.programme  sequencing, deadlines worked back from your dates, calendar (.ics) export
    ct.drafting   auto-drafted discharge submissions (second prompt) + Word export
    ct.reports    Excel tracker, PDF summary, portfolio workbook
    ct.panels     the HTML panels the page shows
    ct.storage    saved projects and the living tracker (Supabase, or a local file in dev)
"""
