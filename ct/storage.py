"""Phase 4: saved projects, the living tracker, and usage counts.

Two interchangeable back ends with the same methods:

  SupabaseStore  production. Talks to Supabase's REST API (PostgREST) with the service key, so
                 it needs no extra package. Run supabase/schema.sql once to create the tables.
                 Row Level Security is ON with no policies: the public "anon" key can read
                 nothing, and only this server (holding the service key) can. Every query is
                 also filtered by owner in code, so one user can never load another's project.
  LocalStore     development only. One JSON file per user under .ct_data/ (git-ignored). On
                 Streamlit Cloud the disk is wiped on every restart, so it is never used there.

A project = one analysed notice + its tracker (status per condition) + its programme dates.
"""
import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx

from ct.config import ROOT

TRACKER_STATUSES = ["not-started", "in-progress", "submitted", "discharged", "complied",
                    "not-applicable"]
DONE_STATUSES = ("discharged", "complied", "not-applicable")


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _clean_owner(owner):
    owner = (owner or "").strip().lower()
    if not owner:
        raise ValueError("a signed-in owner is required")
    return owner


class StorageError(Exception):
    pass


# ---------------------------------------------------------------------------------------------
class LocalStore:
    kind = "local"

    def __init__(self, folder=None):
        self.folder = Path(folder or ROOT / ".ct_data")
        self.folder.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _file(self, owner):
        safe = "".join(ch if ch.isalnum() or ch in "@._-" else "_" for ch in _clean_owner(owner))
        return self.folder / f"{safe}.json"

    def _load(self, owner):
        f = self._file(owner)
        if not f.exists():
            return {"projects": {}, "usage": []}
        return json.loads(f.read_text(encoding="utf-8"))

    def _save(self, owner, db):
        f = self._file(owner)
        tmp = f.with_suffix(".tmp")
        tmp.write_text(json.dumps(db, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
        tmp.replace(f)

    def list_projects(self, owner):
        db = self._load(owner)
        rows = [{k: p[k] for k in ("id", "name", "summary", "tracker", "programme",
                                   "created_at", "updated_at")} for p in db["projects"].values()]
        return sorted(rows, key=lambda r: r["updated_at"], reverse=True)

    def get_project(self, owner, project_id):
        return self._load(owner)["projects"].get(project_id)

    def create_project(self, owner, name, analysis, summary, programme=None, tracker=None):
        with self._lock:
            db = self._load(owner)
            pid = str(uuid.uuid4())
            db["projects"][pid] = {
                "id": pid, "owner": _clean_owner(owner), "name": name, "analysis": analysis,
                "summary": summary, "tracker": tracker or {}, "programme": programme or {},
                "created_at": _now(), "updated_at": _now()}
            self._save(owner, db)
            return pid

    def update_project(self, owner, project_id, **fields):
        with self._lock:
            db = self._load(owner)
            p = db["projects"].get(project_id)
            if not p:
                raise StorageError("project not found")
            p.update({k: v for k, v in fields.items()
                      if k in ("name", "tracker", "programme", "summary", "analysis")})
            p["updated_at"] = _now()
            self._save(owner, db)

    def delete_project(self, owner, project_id):
        with self._lock:
            db = self._load(owner)
            db["projects"].pop(project_id, None)
            self._save(owner, db)

    def log_usage(self, owner, kind, cost_usd=0.0):
        with self._lock:
            db = self._load(owner)
            db["usage"].append({"kind": kind, "cost_usd": round(cost_usd, 4), "created_at": _now()})
            self._save(owner, db)

    def usage_count(self, owner, kind, since_iso):
        return sum(1 for u in self._load(owner)["usage"]
                   if u["kind"] == kind and u["created_at"] >= since_iso)


# ---------------------------------------------------------------------------------------------
class SupabaseStore:
    kind = "supabase"
    LIST_FIELDS = "id,name,summary,tracker,programme,created_at,updated_at"

    def __init__(self, url, service_key, timeout=20):
        self.base = url.rstrip("/") + "/rest/v1"
        self.http = httpx.Client(timeout=timeout, headers={
            "apikey": service_key, "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json"})

    def _check(self, r):
        if r.status_code >= 400:
            # Never echo headers (they hold the key); the body is PostgREST's own error message.
            raise StorageError(f"Supabase {r.status_code}: {r.text[:300]}")
        return r

    def list_projects(self, owner):
        r = self._check(self.http.get(f"{self.base}/projects", params={
            "owner": f"eq.{_clean_owner(owner)}", "select": self.LIST_FIELDS,
            "order": "updated_at.desc"}))
        return r.json()

    def get_project(self, owner, project_id):
        r = self._check(self.http.get(f"{self.base}/projects", params={
            "owner": f"eq.{_clean_owner(owner)}", "id": f"eq.{project_id}", "select": "*"}))
        rows = r.json()
        return rows[0] if rows else None

    def create_project(self, owner, name, analysis, summary, programme=None, tracker=None):
        r = self._check(self.http.post(
            f"{self.base}/projects", headers={"Prefer": "return=representation"},
            content=json.dumps({"owner": _clean_owner(owner), "name": name, "analysis": analysis,
                                "summary": summary, "tracker": tracker or {},
                                "programme": programme or {}}, default=str)))
        return r.json()[0]["id"]

    def update_project(self, owner, project_id, **fields):
        body = {k: v for k, v in fields.items()
                if k in ("name", "tracker", "programme", "summary", "analysis")}
        body["updated_at"] = _now()
        r = self._check(self.http.patch(
            f"{self.base}/projects",
            params={"owner": f"eq.{_clean_owner(owner)}", "id": f"eq.{project_id}"},
            headers={"Prefer": "return=representation"}, content=json.dumps(body, default=str)))
        if not r.json():
            raise StorageError("project not found")

    def delete_project(self, owner, project_id):
        self._check(self.http.delete(f"{self.base}/projects", params={
            "owner": f"eq.{_clean_owner(owner)}", "id": f"eq.{project_id}"}))

    def log_usage(self, owner, kind, cost_usd=0.0):
        self._check(self.http.post(f"{self.base}/usage_events", content=json.dumps(
            {"owner": _clean_owner(owner), "kind": kind, "cost_usd": round(cost_usd, 4)})))

    def usage_count(self, owner, kind, since_iso):
        r = self._check(self.http.get(
            f"{self.base}/usage_events",
            params={"owner": f"eq.{_clean_owner(owner)}", "kind": f"eq.{kind}",
                    "created_at": f"gte.{since_iso}", "select": "id"},
            headers={"Prefer": "count=exact", "Range": "0-0"}))
        total = r.headers.get("content-range", "*/0").split("/")[-1]
        return int(total) if total.isdigit() else len(r.json())


# ---------------------------------------------------------------------------------------------
def get_store(secret=lambda name: os.environ.get(name)):
    """Supabase when its URL + service key are configured; a local file in development; else None.

    `secret` looks a setting up by name (the page passes one that checks st.secrets too).
    """
    url, key = secret("SUPABASE_URL"), secret("SUPABASE_SERVICE_KEY")
    if url and key:
        return SupabaseStore(url, key)
    if secret("CT_LOCAL_STORE"):
        return LocalStore()
    return None


# ----- tracker helpers (pure) -----
def tracker_progress(analysis, tracker):
    """(done, total) over the conditions that need action: discharge-required or gating work."""
    action = [c for c in analysis.get("conditions", [])
              if c.get("discharge_required") or c.get("gate") not in (None, "ongoing", "none")]
    done = sum(1 for c in action
               if (tracker.get(str(c["condition_number"])) or {}).get("status") in DONE_STATUSES)
    return done, len(action)


def outstanding_blockers(analysis, tracker):
    """Pre-start blockers not yet discharged — what still stops you starting on site."""
    out = []
    for c in analysis.get("conditions", []):
        if c.get("gate") in ("blocks-any-commencement", "blocks-demolition"):
            if (tracker.get(str(c["condition_number"])) or {}).get("status") not in DONE_STATUSES:
                out.append(c)
    return out


def deemed_discharge_candidates(analysis, tracker, today, england=True, weeks=8):
    """Submitted more than 8 weeks ago with no decision recorded (England only)."""
    from ct.logic import parse_date
    if not england:
        return []
    out = []
    for c in analysis.get("conditions", []):
        t = tracker.get(str(c["condition_number"])) or {}
        sub = parse_date(t.get("submitted"))
        if t.get("status") == "submitted" and sub and (today - sub).days > weeks * 7:
            out.append((c, (today - sub).days // 7))
    return out
