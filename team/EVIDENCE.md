# Evidence

Dated, linked observations about the market, the facts the tool relies on, and usage.
Newest first. Anything not checked against a primary source is marked UNVERIFIED.

## Facts the code relies on

Facts check 2026-11-11: nothing CHANGED. Fee rise: Lords approval now found; Commons approval
and "made" status COULD NOT VERIFY. Several legislation.gov.uk and Planning Portal pages were
refused today (permission not answered); the ones below were read.

- 2026-11-11 | England rise to £435 / £125 on 8 Dec 2026: House of Lords APPROVED the draft on
  14 Oct 2026 ("Question on motion to approve the instrument put", "Instrument approved (House of
  Lords)"), after a Grand Committee debate on 13 Oct. Laid 1 Sep 2026.
  https://api.parliament.uk/procedure-browser/business-items/8afUQG38
  · https://api.parliament.uk/procedure-browser/business-items/pVe1ouRC
  · https://api.parliament.uk/procedure-browser/business-items/9t0MRKDv
- 2026-11-11 | COULD NOT VERIFY: Commons approval (the `ct/logic.py` comment says 27 Oct 2026) and
  whether the regulations are made. Procedure-browser items JweVFUQ8, WnVZU9LK, P7eeBW70, JG3ert1n,
  GsUA6JWc failed to load twice; the draft's legislation.gov.uk page was refused. Planning Portal
  fee PDF (V2026(2) FC) still says "if the draft amending legislation is approved by Parliament";
  its 23 Oct 2026 blog post says the change takes effect "once the legislation has gained
  parliamentary approval". Fees £309 / £89 now and £435 / £125 in the draft: UNCHANGED.
  https://ecab.planningportal.co.uk/uploads/forthcoming_english_application_fees.pdf
  · https://blog.planningportal.co.uk/ . Re-check 1 to 8 Dec (agenda).
- 2026-11-11 | LBC condition discharge exempt (England): UNCHANGED (same Planning Portal PDF).
- 2026-11-11 | 8-week period: UNCHANGED. DMPO 2015 art 27(2) "within a period of 8 weeks beginning
  with the day immediately following that on which the application is received", or longer if
  agreed in writing. https://www.legislation.gov.uk/uksi/2015/595/pdfs/uksi_20150595_en.pdf
  Art 28 (deemed discharge): no outstanding effects. https://www.legislation.gov.uk/uksi/2015/595/article/28
  Schedule 6 exemptions: still COULD NOT VERIFY (heading only in the PDF text, pages 65 to 67).
- 2026-11-11 | Start deadline: UNCHANGED. s91(5) 3 years England, 5 Wales; s92 outline 3 years for
  reserved matters, start within 2 years of final approval (England). Text up to date to 7 Nov 2026.
  https://www.legislation.gov.uk/ukpga/1990/8/part/III/crossheading/duration-of-planning-permission
- 2026-11-11 | NOTE (not a change to our rule): s91(3A) to (3BF), England, substituted by the
  Planning and Infrastructure Act 2025 s56 from 18 Feb 2026, extend the start period when a court
  allows a validity challenge: +1 year (High Court permission), +1 year (Court of Appeal), +2 years
  (Supreme Court). The app does not mention this. Its computed date would then be earlier than the
  true one (the safe direction). https://www.legislation.gov.uk/ukpga/1990/8/section/91
- 2026-11-11 | Wales £242 / £123: NOT RE-CHECKED today (Planning Portal Welsh PDF refused). Last
  checked UNCHANGED 2026-11-10.
- 2026-11-11 | NEW, not in code: Planning Portal service charge from 3 Sep 2026: Band 0 £0, Band 1
  £99, Band 2 £149 (inc VAT), only where the planning fee is over £100. Discharge of conditions is
  "Band 0 or Band 1 – depends on development type/scale". So £309 + up to £99 via the Portal today.
  https://www.planningportal.co.uk/services/help/faq/applications/planning-applications/why-is-there-a-service-charge-for-submitting-planning-applications
  · https://ecab.planningportal.co.uk/uploads/Planning-Portal-Application-Types-Banding-Guide.pdf

- 2026-11-10 | England fee now £309 other / £89 householder per application: UNCHANGED.
  https://ecab.planningportal.co.uk/uploads/forthcoming_english_application_fees.pdf
- 2026-11-10 | England rise to £435 / £125 on 8 Dec 2026: UNCHANGED in the draft. Draft regs
  reg 1(2) "come into force on 8th December 2026"; reg 6 amends reg 16(1) to £125 and £435.
  Still "a draft item ... not yet made" on legislation.gov.uk. Planning Portal: "if the draft
  amending legislation is approved by Parliament". The 1 Sep 2026 draft replaced a 16 Jul draft.
  https://www.legislation.gov.uk/ukdsi/2026/9780348286625/contents
  · https://www.legislation.gov.uk/ukdsi/2026/9780348286625/regulation/6
- 2026-11-10 | COULD NOT VERIFY: the `ct/logic.py` comment that the Commons approved the rise on
  27 Oct 2026. Parliament's procedure browser shows only laying on 1 Sep 2026 and a government
  approval motion, with no approval by either House. Re-check after 1 Dec; if it is not made by
  8 Dec, the automatic switch would show the wrong fee.
  https://api.parliament.uk/procedure-browser/work-packages/1D26TITE
- 2026-11-10 | Wales £242 / £123 from 1 Dec 2025: UNCHANGED.
  https://ecab.planningportal.co.uk/uploads/welsh_application_fees.pdf
- 2026-11-10 | LBC condition discharge free (England and Wales): UNCHANGED. Both Planning Portal
  fee schedules above exempt "a condition or conditions on an application for Listed Building Consent".
- 2026-11-10 | 8-week decision period: UNCHANGED. DMPO 2015 art 27(2): 8 weeks from the day
  after receipt, or longer if agreed in writing. https://www.legislation.gov.uk/uksi/2015/595/article/27
- 2026-11-10 | Deemed discharge, England: UNCHANGED. DMPO 2015 art 29: notice no earlier than
  6 weeks after receipt; takes effect no earlier than the end of the 8 weeks or 14 days after the
  notice. No outstanding changes. https://www.legislation.gov.uk/uksi/2015/595/article/29
  COULD NOT VERIFY the excluded types (Schedule 6 is published only as images):
  https://www.legislation.gov.uk/uksi/2015/595/schedule/6 . A drainage firm says flood-risk and
  most surface-water conditions are excluded (UNVERIFIED). The app already caveats "excluded types".
- 2026-11-10 | Start deadline: UNCHANGED. TCPA 1990 s91(5): 3 years in England, 5 in Wales; s92
  outline: reserved matters within 3 years, start within 2 years of the last approval (England).
  https://www.legislation.gov.uk/ukpga/1990/8/section/91 · https://www.legislation.gov.uk/ukpga/1990/8/section/92
- 2026-11-10 | WATCH (Wales): the Planning (Consequential Provisions) (Wales) Act 2026 (asc 7)
  will omit the Welsh text of s91 and s92, including s91(5), on a day Welsh Ministers appoint. It
  is not yet in force for these sections. Welsh time limits will then sit in a new Welsh Act.
  https://www.legislation.gov.uk/asc/2026/7/section/5
- 2026-11-09 | UNVERIFIED against the regulations (taken from law-firm and consultancy
  summaries, not legislation.gov.uk): discharge-of-conditions fees in England are due to
  rise on 8 Dec 2026 from £309 to £435 per application (£89 to £125 householder), subject
  to Parliamentary approval. Matches `ct/logic.py FEE_SCHEDULE`.
  Sources: https://www.burges-salmon.com/articles/102nhy4/upcoming-changes-to-planning-application-fees-response-to-consultation-and-draft
  · https://lichfields.uk/blog/2026/april/02/the-proposed-path-to-planning-fee-cost-recovery
  · https://www.planninggeek.co.uk/2026/planning-fees-2026-december-increase/
  **Scout: check the made regulations on legislation.gov.uk and whether Parliament has approved them.**
- 2026-11-09 | WATCH: the government has said it is considering charging condition-discharge
  fees per condition rather than per application. That would change the fee logic.
  Source: https://lichfields.uk/blog/2026/july/16/further-fee-uplifts-by-year-end-with-more-to-come

## Market

- 2026-11-11 | Buyer pool, UK: about 2,400 self-employed planners (2,000 England; RTPI 2019 Table 12);
  about 3,700 RIBA chartered practices, about 81% under 10 staff (RIBA Benchmarking 2024); 2,423
  active housebuilders (UK Housebuilder Directory Q3 2024 via Savills); FMB about 6,500 member firms.
  Detail: `team/research/2026-11-11-how-many-buyers-and-where-they-gather.md`
- 2026-11-11 | Small RIBA practice average profit 2024: £26k (one person) to £95k (5 to 10 staff).
- 2026-11-11 | SME surveys: HBF 2025 (n=225) 94% cite "planning permission / discharging conditions"
  delays (one combined answer); FMB Dec 2025 (n=169) 47% say planning is the greatest constraint, 64%
  feel certain about planning outcomes.
- 2026-11-11 | Planning Portal SmartApply (3 Sep 2026): AI guidance, completeness checks (Oct 2026),
  Project Workspaces planned; nothing post-decision. Sponsors the RTPI ICN conference. Re-check monthly.
- 2026-11-11 | Gathering places: RTPI ICN (email forum, conference 8 May 2025 with an AI tools session);
  FMB conference 9 to 10 Jul 2026 (156 delegates, software exhibitors); Planning Portal webinar 800+
  professionals (6 Oct 2026); Planning Resource £2,395 a year for 5 users.
- 2026-11-10 | Small firms rarely publish a discharge price. 1 of 11 firm pages did:
  DrawingsDirect, pack "from £345". Others quote fixed prices on request. Discharge is billed outside
  planning-stage fees. Detail: `team/research/2026-11-10-how-small-firms-discharge-conditions.md`
- 2026-11-10 | Councils charge for advice on discharge: Southwark £419.40 per condition for minor
  schemes (from 1 Apr 2024); Haringey £498 fixed, PPAs from £1,000 per condition. Links in the file above.
- 2026-11-10 | 3 of 6 firm pages from 2025 to 2026 that state the council discharge fee get it wrong
  (one says "per condition"). Links in the file above.
- 2026-11-10 | Hourly rates: architects £55 to £99+ (RIBA Journal Fees Bureau); planning consultancy
  £275 (4D Planning, 2026). Links in the file above.
- 2026-11-10 | West Suffolk, Sep 2020 to Aug 2021: 70 agents with 5+ applications, median 10 a year,
  median about 67% valid on receipt (all application types).

## Usage

- 2026-11-11 | no data. Phase 4 (Supabase) is still not live; nothing the team can read records usage.
- 2026-11-10 | no data. Phase 4 (Supabase) is not live, so `store.usage_count()` has nothing the team can read.
- 2026-11-09 | no data. The app does not report usage or sign-ups anywhere the team can read.
