# Evidence

Dated, linked observations about the market, the facts the tool relies on, and usage.
Newest first. Anything not checked against a primary source is marked UNVERIFIED.

## Facts the code relies on

Facts check 2026-11-10: nothing CHANGED. One part COULD NOT VERIFY (Parliament's approval of the 8 Dec fee rise).

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

- 2026-11-10 | no data. Phase 4 (Supabase) is not live, so `store.usage_count()` has nothing the team can read.
- 2026-11-09 | no data. The app does not report usage or sign-ups anywhere the team can read.
