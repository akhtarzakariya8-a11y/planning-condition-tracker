-- Condition Tracker — run once in Supabase: Dashboard → SQL Editor → New query → paste → Run.
-- Safe to run again: everything is "if not exists".

create extension if not exists pgcrypto;

-- One row per saved notice: the analysis, the living tracker and the programme dates.
create table if not exists public.projects (
  id          uuid primary key default gen_random_uuid(),
  owner       text not null,                         -- the signed-in user's email, lower-case
  name        text not null,
  analysis    jsonb not null,                        -- what the extraction prompt returned
  summary     jsonb not null default '{}'::jsonb,    -- the numbers the project list shows
  tracker     jsonb not null default '{}'::jsonb,    -- {"6": {"status": "submitted", ...}}
  programme   jsonb not null default '{}'::jsonb,    -- {"start": "2027-03-01", ...}
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);
create index if not exists projects_owner_idx on public.projects (owner, updated_at desc);

-- One row per paid-for action (an analysis, a draft) — what each user costs you, and the
-- count a free-tier limit will check.
create table if not exists public.usage_events (
  id          bigserial primary key,
  owner       text not null,
  kind        text not null,                         -- "analysis" | "draft"
  cost_usd    numeric(10, 4) not null default 0,
  created_at  timestamptz not null default now()
);
create index if not exists usage_owner_idx on public.usage_events (owner, kind, created_at);

-- Lock both tables. With RLS on and NO policies, the public anon key can read and write
-- nothing. The app uses the service_role key on the server (it bypasses RLS) and filters
-- every query by owner itself. Never put the service_role key in front-end code.
alter table public.projects enable row level security;
alter table public.usage_events enable row level security;
