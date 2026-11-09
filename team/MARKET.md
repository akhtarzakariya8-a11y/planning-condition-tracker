# Market study

Researched 9 Nov 2026 from public sources (listed at the end). The product lead reads this
before every ticket. The scout keeps it current: dated additions under "Updates", never
silent rewrites. Anything marked HYPOTHESIS has not been tested with a real person.

## The short version

1. The problem is real and measured. Councils decide only about half of discharge
   applications inside the 8-week limit, and small developers are hit hardest.
2. But most of that measured pain is council slowness, which this tool cannot fix. What it
   can fix is the applicant's side: missing a true pre-commencement condition, submitting
   late, paying for more applications than needed, and not knowing what to commission.
3. Competitors already track conditions. None of the pages read described this tool's
   combination: reads the PDF, says what blocks start on site, batches applications by fee,
   works back from programme dates, and drafts the submission. That combination is the edge.
4. Planning professionals do pay monthly for software, at £29 to £195 a month.
5. The warning sign: a funded London startup in this space (Tract) closed with no revenue,
   blaming a conservative sector with low willingness to pay. Nobody has yet told us they
   would pay for this tool. That is the first thing to find out, ahead of any feature.

## 1. The problem, in numbers

- **Half of discharge decisions are late.** A Home Builders Federation and Paragon Bank
  study (Oct 2026, FOI data, more than 14,000 discharge applications) found 50.8% decided
  within 8 weeks across three years: 55.6% in 2023/24, 51.8% in 2024/25. Median time was
  105 days in 2023/24 and 95 days in 2024/25, against a 56-day limit. The report calls
  itself an indicative snapshot; 30 councils gave timing data.
- **Small developers suffer most.** The same study says the impact is most acute for SME
  builders with limited finance and few sites.
- **Conditions per permission.** A government-commissioned study of the applications
  process found an average of 6.3 pre-commencement and 11.9 other conditions per
  permission in its sample. One case in the HBF study had 25 conditions on 14 homes.
- **Getting it wrong can cost the permission.** Under the Whitley principle, work started
  in breach of a true pre-commencement condition may not count as lawful commencement, so
  the permission can lapse. The High Court applied this in 2024 (West Oxfordshire).
  This is the legal risk the Safety Gate addresses.
- **Lenders care.** Development finance lenders report that some SME developers do not
  consider pre-commencement conditions until lawyers raise them, and that funding can be
  held back until they are signed off (trade press, older article, UNVERIFIED as current).

What the numbers do not show: how much delay is caused by applicants rather than councils.
The applications-process study lists "applicant time to provide further or correct
information" among the top causes, without a figure.

## 2. How big is it

- England granted 254,100 planning decisions in the year to June 2026.
- About half of all decisions are householder applications. Householders have few
  conditions and little reason to pay. They are not the target.
- 28,100 residential applications (major and minor) were granted in the year to March 2026.
  Add commercial schemes and the pool of condition-heavy permissions is in the tens of
  thousands a year.
- About 22,000 planners work in the UK, roughly half of them at least partly for councils
  (RTPI, 2019; a 2023 update says the total is largely unchanged).
- NOT FOUND: a current count of SME developers, or of small planning consultancies.

Arithmetic for the £50k a year goal (not a forecast):

| Price | Customers needed |
| --- | --- |
| £29 a month | about 144 subscribers |
| £79 a month | about 53 subscribers |
| £20 per notice | 2,500 notices a year, around 9% of residential permissions |

Subscriptions from repeat users are the plausible route. Pay-per-notice alone would need
an unrealistic share of the market.

## 3. Who else is here

| Tool | What it does with conditions | Price seen | Gap versus this tool |
| --- | --- | --- | --- |
| PlanningCore Condition Manager | Paste the condition text; classifies, checks the six tests, manual discharge tracker. One tool in a large planning suite | Free registration; pricing page not read | No PDF upload, programme, fee batching or drafting described |
| DevTrack | Development management for small developers; conditions entered and tracked by hand | Free for 1 project; £79 a month Pro | No automatic reading of the notice described |
| Avoice Practice | AI workspace for architecture practices (Y Combinator backed); conditions and S106 tracker with the 8-week date | Not on the page read | Extraction from the notice not described |
| PlanTrack | Watches 300+ council portals; delivers decision notices as they issue | £29 a month plus £5 per council (waitlist) | Monitoring, not analysis |
| Remindax | Reminder dates for permissions and conditions | Not read | Dates only |
| Searchland, LandTech, Glenigan | Land sourcing and planning data | Searchland from £195 a licence a month, 12-month minimum; Glenigan reported at £500+ | Different job; useful as price anchors |
| PlanWatch, Planning Signal | Application alerts | From £4.99 a month; PlanWatch's trade plan is £149 | Different job; crowded and cheap |

Based only on the pages read. A product can do more than its page says.

Government activity to watch:
- **Extract** (MHCLG): AI that digitises councils' historic planning documents, launched
  to all English councils on 4 June 2026. For councils, not applicants.
- **Augmented Planning Decisions**: AI support for officers on householder applications,
  contract awarded February 2026, trials in Camden, Barnet and Dorset from May 2026.
- **National model conditions**: the draft NPPF proposed national model conditions, and
  since the final NPPF (17 August 2026) the government has said further model obligations
  and planning conditions will be published.
  Standard wording makes extraction easier for everyone, so the lasting value is in the
  workflow after extraction: gates, programme, drafting, tracking.

Cautionary case: **Tract** (London, 2023 to 2025) raised £744,000, built several planning
products including a document-drafting tool that was well received, and closed with no
revenue. The founders blamed a conservative, fragmented sector with low willingness to pay,
and advised being commercial from day one and learning from customers constantly.

## 4. Who to sell to first (HYPOTHESIS, ranked)

1. **Small planning consultancies and architects who discharge conditions for clients.**
   Repeat use, they bill by the hour, and a drafted submission saves billable time.
2. **SME developers with one to five live sites.** Sharpest pain, but few permissions a
   year each and price sensitive. Best reached through people they already listen to.
3. **Development finance lenders and their monitoring surveyors.** They need proof that
   pre-commencement conditions are cleared before releasing money. Few buyers, higher value.
4. **QS and project management firms** acting as employer's agent. Zak's own field.
5. **Householders.** Not a target.

## 5. What to build, in order

1. **A 60-second trial**: sample notice and landing page (tickets 3 and 4). Nothing else
   can be tested without this.
2. **Hosting that does not fall asleep** before anyone pays (see `team/ENGINEERING.md`).
3. **The living tracker with reminders**: the 8-week clock, deemed-discharge prompt,
   status per condition (tickets 11 and 12). Every competitor centres on tracking, and it
   is what brings a user back.
4. **A client-ready report** a consultant can send under their own name.
5. **A lender pack**: one page showing what is cleared and what blocks drawdown.
   HYPOTHESIS. Build only after three lenders or monitoring surveyors say they want it.

Do not build yet: more extraction features (already strong), a six-tests validator
(PlanningCore has one), council portal monitoring (crowded and cheap).

## 6. What only conversations can answer

Desk research cannot tell us whether anyone will pay. Ask five people in group 1 or 2:

1. Talk me through the last decision notice you received. What did you do with it first?
2. Have you ever missed or nearly missed a pre-commencement condition? What happened?
3. How long does building the conditions tracker and the first discharge submission take?
4. What do you use today, and what does it cost?
5. If this did that job in two minutes, what would it be worth per notice or per month?

A "yes, I would pay" from three of five is the signal to build item 3 onward. Silence or
polite interest from all five means stop building and rethink the buyer.

## Updates (scout adds dated lines here)

_None yet._

## Sources

- HBF and Paragon, Condition Impossible, Oct 2026: https://www.hbf.co.uk/research-insight/condition-impossible/
- Building Design on the same study: https://www.bdonline.co.uk/news/half-of-councils-failing-to-hit-deadline-for-approving-planning-conditions-says-housing-body/5144787.article
- Planning applications in England, April to June 2026 (MHCLG): https://www.gov.uk/government/statistics/planning-applications-in-england-april-to-june-2026/planning-applications-in-england-april-to-june-2026-statistical-release
- Planning applications in England, January to March 2026 (MHCLG): https://www.gov.uk/government/statistics/planning-applications-in-england-january-to-march-2026/planning-applications-in-england-january-to-march-2026-statistical-release
- Planning Applications Process, final report: https://assets.publishing.service.gov.uk/media/697234b9a1311bdcfa0ed8cd/Planning_Applications_Process_Final_report.pdf
- Whitley principle, West Oxfordshire case note: https://www.localgovernmentlawyer.co.uk/planning/401-planning-news/58483-claimant-group-wins-judicial-review-over-retrospective-effect-of-quashing-of-pre-commencement-condition-discharge
- Lenders and pre-commencement conditions: https://developmentfinancetoday.co.uk/article-desc-5102_
- RTPI, the UK planning profession: https://rtpi.org.uk/4344.aspx
- PlanningCore: https://planningcore.uk/condition_tracker.php
- DevTrack: https://devtrack.co.uk/
- Avoice: https://www.avoice.co/guides/discharge-of-planning-conditions-guide
- PlanTrack: https://plantrack.uk/
- Searchland pricing: https://searchland.co.uk/pricing
- PlanWatch: https://planwatch.co.uk/
- Glenigan price as reported by a competitor: https://planwire.io/compare
- Extract and Augmented Planning Decisions: https://ai.gov.uk/our-work/planning/
- Model conditions in the new NPPF: https://www.gov.uk/government/consultations/standard-planning-agreements-for-medium-sized-sites/standard-planning-agreements-for-medium-sized-sites
- Tract closure: https://techfundingnews.com/london-based-ai-startup-tract-shuts-down-is-the-uk-proptech-sector-dead/
