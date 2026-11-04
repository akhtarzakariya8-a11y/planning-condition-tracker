"""Fast tests for the rules — no API calls, no browser. Run with:

    python3 -m pytest tests/ -q

They use the saved analyses in eval/fixtures (real extractions of the test notices), so they
check the code, not the model. eval/run_eval.py checks the model.
"""
import json
from datetime import date
from pathlib import Path

import httpx
import pytest

from ct import drafting, logic, programme, reports, storage

FIX = Path(__file__).resolve().parent.parent / "eval" / "fixtures"


def load(name):
    return json.loads((FIX / f"{name}.json").read_text(encoding="utf-8"))


LAMBETH = "21_04939_FUL--3474437"
HOUSEHOLDER = "26_01199_FUL--3568317"
LBC = "25_AP_3061-DECISION_NOTICE_-_LBC_-_GRANT-4184773"
REFUSAL = "26_01309_FUL--3573081"
DISC = "25_01905_DISC-APPROVED__DISC__CON_DISCHARGE_-_DEC_NOT-4319058"


# ----- start deadline: the most expensive thing to get wrong -----
def test_full_permission_deadline_is_computed():
    sd = logic.start_deadline(load(LAMBETH))
    assert sd["date"] == date(2028, 11, 10) and sd["basis"] == "computed"


def test_outline_permission_is_not_computed():
    d = load(LAMBETH)
    d["permission_type"] = "outline"
    assert logic.start_deadline(d) == {"date": None, "basis": "outline", "condition": 1}


def test_reserved_matters_wording_is_not_computed_even_if_type_says_full():
    d = load(LAMBETH)
    d["conditions"][0]["source_quote"] = ("Development shall begin no later than two years from the "
                                          "approval of the last of the reserved matters.")
    assert logic.start_deadline(d)["basis"] == "outline"


def test_variation_without_stated_date_is_not_computed():
    d = load(LAMBETH)
    d["permission_type"] = "variation"
    assert logic.start_deadline(d)["date"] is None


def test_variation_with_stated_date_uses_it():
    d = load(LAMBETH)
    d["permission_type"] = "variation"
    d["conditions"][0]["source_quote"] = "The development shall be begun before 3rd March 2027."
    sd = logic.start_deadline(d)
    assert sd["date"] == date(2027, 3, 3) and sd["basis"] == "stated"


def test_expired_message():
    msg = logic.start_deadline_message(load(LAMBETH), today=date(2029, 1, 1))
    assert msg["kind"] == "expired"


# ----- fees switch on their date -----
def test_fees_before_and_after_8_december_2026():
    assert logic.fee_scale("england", date(2026, 12, 7))["other"] == 309
    assert logic.fee_scale("england", date(2026, 12, 8))["other"] == 435
    assert logic.fee_scale("england", date(2026, 12, 8))["householder"] == 125
    assert logic.next_fee_rise("england", date(2026, 12, 8)) is None
    assert logic.fee_scale("scotland") is None


def test_discharge_plan_prices_by_date():
    d = load(LAMBETH)
    before = logic.build_discharge_plan(d, on=date(2026, 11, 4))
    after = logic.build_discharge_plan(d, on=date(2027, 1, 1))
    assert (before["fee"], before["applications"], before["cost"]) == (309, 2, 618)
    assert after["fee"] == 435 and after["next_rise"] is None
    assert before["deemed_discharge"] is True


def test_listed_building_consent_is_free():
    plan = logic.build_discharge_plan(load(LBC))
    assert plan["fee_payable"] is False and plan["fee"] is None


def test_discharge_approval_imposes_nothing():
    assert logic.build_discharge_plan(load(DISC))["applies"] is False


# ----- programme -----
def test_programme_works_back_from_dates():
    d = load(LAMBETH)
    prog = programme.build_programme(d, {"start": date(2027, 3, 1), "above_ground": date(2027, 7, 1)},
                                     today=date(2026, 11, 4))
    groups = programme.submission_groups(prog)
    first = groups[0]
    assert first["submit_by"] == date(2026, 12, 21)            # 1 Mar 2027 - 10 weeks
    assert first["commission_by"] == date(2026, 11, 9)         # minus 6 weeks
    assert {c["condition_number"] for c in first["discharge"]} >= {13, 16}   # 16 = piling, same day
    assert first["fee"] == 435                                  # submitted after the rise
    saving = programme.fee_rise_saving(d, prog)
    assert saving["new"] - saving["old"] == 126


def test_programme_flags_late_and_lapse():
    d = load(LAMBETH)
    prog = programme.build_programme(d, {"start": date(2029, 1, 1)}, today=date(2028, 12, 1))
    assert prog["start_after_lapse"] is True
    assert prog["steps"][0]["status"] == "late"


def test_cross_reference_pulls_condition_forward():
    d = {"conditions": [
        {"condition_number": 5, "gate": "before-occupation", "discharge_required": True,
         "source_quote": "Details of the remediation verification shall be submitted."},
        {"condition_number": 6, "gate": "blocks-any-commencement", "discharge_required": True,
         "source_quote": "No development shall commence until the strategy approved under condition 5 "
                         "has been implemented."},
        {"condition_number": 2, "gate": "ongoing", "source_quote": "In accordance with the plans."},
    ]}
    seq = programme.build_sequence(d)
    assert seq["pulled"] == {5: ("occupation", "start", 6)}
    assert [c["condition_number"] for c in seq["stages"]["start"]] == [5, 6]


def test_ics_is_well_formed():
    d = load(LAMBETH)
    prog = programme.build_programme(d, {"start": date(2027, 3, 1)}, today=date(2026, 11, 4))
    ics = programme.build_ics(d, prog).decode("utf-8")
    assert ics.startswith("BEGIN:VCALENDAR\r\n") and ics.endswith("END:VCALENDAR\r\n")
    assert ics.count("BEGIN:VEVENT") == ics.count("END:VEVENT") >= 3
    assert all(len(line.encode("utf-8")) <= 75 for line in ics.split("\r\n"))


# ----- downloads build for every test notice -----
@pytest.mark.parametrize("name", [p.stem for p in FIX.glob("*.json")])
def test_reports_build(name):
    d = load(name)
    prog = programme.build_programme(d, {"start": date(2027, 3, 1)})
    assert reports.build_excel(d, prog, tracker={})[:2] == b"PK"
    assert reports.build_pdf(d, prog)[:4] == b"%PDF"


def test_portfolio_workbook():
    items = [(p.name, load(p.stem)) for p in FIX.glob("*.json")]
    assert reports.build_portfolio_excel(items)[:2] == b"PK"


# ----- drafting safety net -----
def test_invented_reference_is_caught():
    draft = {"covering_letter": "Enclosed: drawing 1916/PL2 09E and drawing XYZ-999-P-01 Rev C. [DOCUMENT REFERENCE]"}
    found = drafting.unverified_references(draft, "approved plans 1916/PL2 09E")
    assert "XYZ-999-P-01" in found and not any("1916" in f for f in found)


# ----- storage -----
def test_local_store_isolates_users(tmp_path):
    s = storage.LocalStore(tmp_path)
    d = load(HOUSEHOLDER)
    pid = s.create_project("A@x.com", "p", d, {})
    assert s.get_project("a@x.com", pid)["name"] == "p"
    assert s.get_project("b@x.com", pid) is None
    assert s.list_projects("b@x.com") == []


def test_tracker_helpers():
    d = load(HOUSEHOLDER)
    tracker = {"4": {"status": "submitted", "submitted": "2026-08-01"}, "6": {"status": "complied"}}
    assert [c["condition_number"] for c in storage.outstanding_blockers(d, tracker)] == [4]
    assert [c["condition_number"] for c, _ in
            storage.deemed_discharge_candidates(d, tracker, date(2026, 11, 4))] == [4]
    assert storage.deemed_discharge_candidates(d, tracker, date(2026, 11, 4), england=False) == []


def test_supabase_store_requests():
    """A stand-in for Supabase's REST API, checking every request is filtered by owner."""
    rows, seen = {}, []

    def handler(request):
        seen.append(request)
        assert request.headers["apikey"] == "svc"
        q = dict(request.url.params)
        if request.url.path.endswith("/projects"):
            if request.method == "POST":
                body = json.loads(request.content)
                body["id"] = "p1"
                rows["p1"] = body
                return httpx.Response(201, json=[body])
            assert q.get("owner") == "eq.zak@x.com"
            if request.method == "GET":
                return httpx.Response(200, json=list(rows.values()))
            if request.method == "PATCH":
                rows["p1"].update(json.loads(request.content))
                return httpx.Response(200, json=[rows["p1"]])
            if request.method == "DELETE":
                rows.clear()
                return httpx.Response(204)
        if request.url.path.endswith("/usage_events"):
            if request.method == "POST":
                return httpx.Response(201)
            return httpx.Response(200, json=[{"id": 1}], headers={"content-range": "0-0/7"})
        return httpx.Response(404)

    s = storage.SupabaseStore("https://demo.supabase.co", "svc")
    s.http = httpx.Client(transport=httpx.MockTransport(handler),
                          headers=dict(s.http.headers))
    pid = s.create_project("Zak@X.com", "Lambeth", {"conditions": []}, {})
    assert pid == "p1"
    assert s.list_projects("zak@x.com")[0]["name"] == "Lambeth"
    s.update_project("zak@x.com", pid, tracker={"6": {"status": "submitted"}})
    assert rows["p1"]["tracker"] == {"6": {"status": "submitted"}}
    s.log_usage("zak@x.com", "analysis", 0.18)
    assert s.usage_count("zak@x.com", "analysis", "2026-11-01T00:00:00") == 7
    s.delete_project("zak@x.com", pid)
    assert rows == {}
    with pytest.raises(ValueError):
        s.list_projects("")
