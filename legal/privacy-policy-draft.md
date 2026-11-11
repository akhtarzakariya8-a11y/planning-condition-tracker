> **DRAFT: not legal advice, not published, review before publishing.**
> Prepared by the Aftergrant build team on 11 Nov 2026 from the code on `main` at that date.
> Nothing in this file is shown to users. Before publishing: fill every `[PLACEHOLDER]`, make
> each `[ZAK TO DECIDE]` choice, check every item marked UNVERIFIED against the provider's own
> pages, ideally have a qualified person review it, then delete the "Notes for Zak" section at
> the end. Publishing is Zak's step. HTML comments (`<!-- ... -->`) show the code each statement
> rests on; they do not appear when the page is rendered.

# Aftergrant privacy policy

**Effective date:** [EFFECTIVE DATE]
**Version:** draft 1

This policy explains what happens to the information you give Aftergrant, the web app that
reads UK planning decision notices and lists their conditions. It covers the Aftergrant web app
only.

<!-- The optional MCP server (mcp_server/) runs on the user's own computer with the user's own
Anthropic key (ct/extract.py:31-33, mcp_server/server.py:161), caches results on that computer
(mcp_server/server.py:174) and does not import ct/storage (mcp_server/server.py:74-78), so
Aftergrant receives nothing from it. If you want this covered, add a sentence; it is left out
here to keep the policy about the hosted app. -->

## 1. Who we are and how to contact us

Aftergrant is run by [CONTROLLER NAME] ("we", "us"). We are the controller of the personal
information described in this policy, except where section 6 says otherwise.

- Email: [CONTACT EMAIL]
- Post: [POSTAL ADDRESS]
- ICO registration number: [ICO REGISTRATION NUMBER]

We have not appointed a data protection officer. [ZAK TO DECIDE: confirm, or add DPO details.]

## 2. The short version

- When you upload a decision notice, its text (or, for a scanned notice, the PDF itself) is sent
  to Anthropic, the company whose AI model reads it.
- If you do not sign in, we do not save your notice or its results. They are held only in
  memory for your browser session.
- If you sign in, we record your email address with each analysis and draft you run, so we can
  track costs and usage limits. If you also press **Save to My projects**, we store that
  project's results until you delete it. **Delete project** removes the project but not the
  usage records (section 11).
<!-- Usage row with the signed-in email on every analysis and draft, saved or not: app.py:83-90
(owner = user, app.py:88), app.py:180, app.py:272; ct/storage.py:171-173;
supabase/schema.sql:22-28. Saved project: app.py:421-426, ct/storage.py:148-154. Delete removes
only the projects row: ct/storage.py:167-169; usage_events untouched. -->
- The page also loads fonts from Google, and the software the app is built on (Streamlit) may
  send usage statistics from your browser. Section 5 explains both.

## 3. What happens when you upload a decision notice

**What you give us.** One or more PDF decision notices (up to 10 at a time, each up to about
24MB).
<!-- app.py:459-460 (file_uploader, PDF, multiple files); ct/config.py:22 (BATCH_MAX_FILES = 10),
app.py:468-471; ct/config.py:26 (MAX_PDF_BYTES), .streamlit/config.toml:20 (maxUploadSize = 24). -->

**What is sent to Anthropic.** To read the notice we send it to Anthropic's API:

- For a normal (digital) PDF, we take out the text of every page and send that text.
- For a scanned PDF with no readable text, we send the whole PDF file so the model can read
  the page images.
- If the first answer cannot be used, the same content is sent once more.

<!-- ct/extract.py:59-62 (text of every page sent when it has 100+ characters);
ct/extract.py:63-68 (otherwise the whole PDF, base64, as a "document"); ct/extract.py:77-87
(the call to client.messages, model from ct/config.py:11); ct/extract.py:107-118 and 125-127
(up to two attempts). Called from app.py:172. -->

Anthropic sends back a structured reading of the notice: the council, application reference,
site address, applicant's name, description of the development, decision date, and each
condition with the wording quoted from the notice.
<!-- prompt_v4_production.txt:16-17 and 34-35 (site_address, applicant); field list in CLAUDE.md
"Data shape". The result is parsed at ct/extract.py:116. -->

**Drafting an application.** If you press **Draft application**, we send Anthropic a second
request containing the notice details listed above (including the site address and applicant's
name) and the wording of the conditions in that application. This only happens when you press
the button.
<!-- app.py:263-272 (only on click); ct/drafting.py:25-45 (build_request: local_authority,
application_reference, site_address, applicant, development_description, decision_date, nation,
document_type, and per condition its number, summary, source_quote, specialists);
ct/drafting.py:71-73 (the call, up to two attempts). -->

**What we keep.** If you are not signed in to saved projects, the results are kept only in your
browser session's memory on the server, so that clicking a button does not send the notice
again. The app's own code does not write the notice or its results to a file or database.
<!-- app.py:44-46 (st.session_state "analyses" and "drafts"); app.py:145-146, 179 (results
cached under a hash of the file, by file name); app.py:276-277 (drafts kept in session).
No store configured -> ct/storage.py:186-196 returns None; app.py:85-86 (usage not logged),
app.py:410-411 (no save button), app.py:671 (no sidebar). -->

The Streamlit software that runs the app holds uploaded files in memory, not on disk, and is
designed to clear a session's uploaded files when the session is closed. A session whose browser
tab has disconnected may be kept for at least 2 minutes (its default setting) in case you
reconnect.
<!-- Primary source read 11 Nov 2026: the Streamlit 1.58.0 package pinned in requirements.txt:4,
installed source. streamlit/runtime/memory_uploaded_file_manager.py:33-39 (in-memory dict) and
74-76 (remove_session_files); streamlit/runtime/app_session.py:287-297 (shutdown removes the
session's files); streamlit/config.py:1063-1076 (server.disconnectedSessionTTL default 120
seconds, "may choose to clean up ... at any point after this time"). How Streamlit Community
Cloud configures or logs this: UNVERIFIED. -->

Whether our hosting provider keeps its own technical logs, and for how long, is set out in its
own policy (see section 8). [UNVERIFIED: check before publishing.]

**Downloads.** The Excel tracker, PDF summary, calendar file and Word draft are created in
memory and sent straight to your browser. We do not keep a copy.
<!-- ct/reports.py:67-70 and 496-510 (BytesIO, returned as bytes); ct/drafting.py:171-173;
ct/programme.py:336 build_ics; served by st.download_button at app.py:292-296, 391-404, 496-500. -->

## 4. If you sign in and save projects

Saved projects are optional. [ZAK: keep this section only once sign-in is switched on in
production. Until the Supabase and Google sign-in secrets are set, none of this happens.]
<!-- app.py:50-55 (sign-in only if [auth] is in secrets); ct/storage.py:186-196 (storage only if
SUPABASE_URL and SUPABASE_SERVICE_KEY are set); CLAUDE.md "Phase 4 goes live only when these
secrets are set". -->

**Signing in.** You sign in with your Google account. We receive and use your email address to
identify your projects. It is shown to you in the sidebar.
<!-- .streamlit/secrets.toml.example:16-21 (Google OpenID Connect); app.py:63-66 (email from
st.user, lower-cased); app.py:679 (shown as "Signed in as"). Which other profile fields Google
passes to Streamlit's st.user (for example name, picture): UNVERIFIED; the app reads only
"email". -->

**What a saved project contains.** When you press **Save to My projects**, we store:

- your email address (to link the project to you);
- the project name (the application reference and site address, which you can rename);
- the full reading of the notice from section 3, including the site address, applicant's name
  and the quoted condition wording;
- a short summary (council, dates, counts and fees);
- any programme dates you enter (start on site, piling, above-ground works, occupation, and two
  planning assumptions);
- the tracker you fill in: status, submitted and approved dates, the council's reference and
  any notes you type for each condition;
- when the project was created and last changed.

We do not store the PDF file itself, and we do not store drafted applications.
<!-- app.py:421-426 (create_project with notice_title, analysis, summary, programme dates);
ct/logic.py:92-98 (notice_title = reference + site address); ct/logic.py:395-409 (summarise);
ct/storage.py:148-154 (fields posted: owner, name, analysis, summary, tracker, programme);
supabase/schema.sql:7-17 (projects table columns incl. created_at, updated_at);
app.py:363-373 (programme dates saved as you type, incl. prep_weeks, buffer_weeks);
app.py:637-647 (tracker: status, submitted, approved, reference, notes);
app.py:656-659 (rename). No PDF bytes and no draft are passed to create_project or
update_project (ct/storage.py:151-153, 157-158); drafts live only in st.session_state
(app.py:271). -->

**Usage records.** When saved projects are switched on, each analysis and each draft adds a
record of what kind of action it was, what it cost us, and when. If you are signed in, the record
carries your email address; if not, it is recorded as "anonymous". We use these to see what the
service costs and, in future, to apply a free-use limit.
<!-- app.py:83-90 (log_usage; owner = user or "anonymous" at app.py:88); called at app.py:180
(analysis) and app.py:272 (draft); ct/storage.py:171-173; supabase/schema.sql:22-28 (owner,
kind, cost_usd, created_at). Monthly count shown at app.py:681-684. Free-tier limit is
backlog ticket 9, not built. -->

## 5. Other information collected when you visit

**Fonts from Google.** Each page asks your browser to load fonts from Google Fonts
(fonts.googleapis.com and fonts.gstatic.com). Like any web request, this tells Google your IP
address and browser details. What Google does with this is set out in Google's own policy.
[UNVERIFIED: check Google's Fonts privacy statement before publishing. ZAK TO DECIDE: keep this,
or host the fonts ourselves and delete this paragraph.]
<!-- theme/ct_theme.py:34-36 (FONTS URL) and 170-173 (link tags injected into every page by
inject_theme, called at app.py:41). -->

**Streamlit usage statistics.** [ZAK TO DECIDE, see Notes item 1. If usage statistics are
switched off before publishing, delete this paragraph.] Aftergrant is built with Streamlit. With
its default setting, the Streamlit page in your browser can send usage events to Streamlit. The
code that does this includes the page address and title, the referring page, your browser
language and browser details, and a random identifier stored in a cookie named
`ajs_anonymous_id` that lasts one year. We do not see this data.
<!-- .streamlit/config.toml:1-20 has no [browser] section, so browser.gatherUsageStats keeps its
default. Primary source read 11 Nov 2026: Streamlit 1.58.0 installed source,
streamlit/config.py:1125-1131 (default_val=True); frontend bundle
streamlit/static/static/js/index.dkY5s53S.js, MetricsManager: fetches its endpoint from
https://data.streamlit.io/metrics.json, getContextData (page URL, title, path, referrer, query
string, language, user agent), getAnonymousId (cookie ajs_anonymous_id, expiry one year, also
copied to localStorage). Whether Streamlit Community Cloud overrides this, and what Streamlit
does with the data: UNVERIFIED. -->

**Cookies.** If you sign in, Streamlit sets a cookie to keep you signed in. [UNVERIFIED: its
name and how long it lasts; check Streamlit's authentication documentation.] Our hosting provider
may set its own cookies. [UNVERIFIED.]
<!-- .streamlit/secrets.toml.example:18 (cookie_secret in the [auth] block, which Streamlit uses
to sign its identity cookie). -->

## 6. Other people's information in decision notices

Decision notices often contain personal information about people other than you: the
applicant's name (which may be a private individual), the site address (which may be someone's
home), and sometimes an agent's name and address. When you upload a notice, all of its text is
sent to Anthropic as described in section 3, and, if you save the project, the applicant's name
and site address are stored with it.
<!-- ct/extract.py:59-62 (the text of every page, not only the fields extracted);
prompt_v4_production.txt:35 (applicant extracted, "Not the agent", but the agent's details are
still in the text that is sent); ct/drafting.py:31-32 (site address and applicant sent when
drafting); supabase/schema.sql:11 and ct/logic.py:92-98 (stored in analysis and project name). -->

Please only upload notices you are entitled to use for your work.

[ZAK TO DECIDE, with your reviewer: who is responsible for this third-party information. Two
common models:
(a) the user (for example a consultant uploading a client's notice) is the controller and
Aftergrant processes it on their behalf, which normally needs a data processing agreement
(out of scope for this draft); or
(b) Aftergrant is a controller in its own right and relies on legitimate interests.
Also ask the reviewer whether UK GDPR Article 14 (information to give people whose data you did
not collect from them) applies to applicants named in notices. Rewrite this section once
decided.]

## 7. Why we use your information and our lawful basis

[ZAK TO CONFIRM each lawful basis with your reviewer. These are proposals, not advice.]

| What we do | Why | Proposed lawful basis (UK GDPR Article 6) |
| --- | --- | --- |
| Send your notice to Anthropic and show you the results (section 3) | To provide the service you asked for | Contract (6(1)(b)); for other people named in the notice, legitimate interests (6(1)(f)) |
| Draft an application when you press the button | To provide the service you asked for | Contract (6(1)(b)) |
| Sign-in and saved projects (section 4) | To keep your projects and tracker for you | Contract (6(1)(b)) |
| Usage records (section 4) | To understand our costs and apply fair-use limits | Legitimate interests (6(1)(f)) |
| Fonts from Google (section 5) | To display the page as designed | Legitimate interests (6(1)(f)) |
| Streamlit usage statistics (section 5), if kept | Streamlit's product statistics | [ZAK TO DECIDE: possibly consent, because it sets a non-essential cookie; UNVERIFIED, see Notes item 1] |

We do not sell your information and we do not use it for advertising.
<!-- No advertising or sales code anywhere in app.py or ct/. The only third-party calls from the
app are Anthropic (ct/extract.py:77), Supabase (ct/storage.py:125-128), Google sign-in via
st.login (app.py:414, 692) and the browser-side font and Streamlit metrics requests above. -->

## 8. Who receives your information

We use these service providers. Each receives only what is described.

| Provider | What they receive | Their privacy information |
| --- | --- | --- |
| Anthropic (AI model) | Notice text or PDF; for drafts, notice details and condition wording (section 3) | [UNVERIFIED, to check: https://www.anthropic.com/legal/privacy and https://www.anthropic.com/legal/commercial-terms, including how long API inputs and outputs are kept and whether they are used for training] |
| Streamlit Community Cloud (hosting) [UNVERIFIED: name the company that operates it] | Everything you upload and everything the app shows you, while it runs | [UNVERIFIED, to check: https://streamlit.io/privacy-policy and the Community Cloud terms] |
| Supabase (database, only if saved projects are on) | Saved projects and usage records (section 4) | [UNVERIFIED, to check: https://supabase.com/privacy and https://supabase.com/legal/dpa] |
| Google (sign-in, only if saved projects are on) | The fact that you sign in to Aftergrant with your Google account | [UNVERIFIED, to check: https://policies.google.com/privacy] |
| Google (fonts) | Your IP address and browser details (section 5) | [UNVERIFIED, to check: https://developers.google.com/fonts/faq/privacy] |

<!-- Recipients from code: Anthropic ct/extract.py:77-87, ct/drafting.py:71-73; Supabase
ct/storage.py:124-183; Google sign-in .streamlit/secrets.toml.example:16-21 and app.py:414,
692; Google Fonts theme/ct_theme.py:34-36, 170-173. Hosting on Streamlit Community Cloud:
CLAUDE.md "Live on Streamlit Community Cloud". The operating company is UNVERIFIED in this run. -->

We may also share information if the law requires it.

## 9. International transfers

Some of these providers may process information outside the UK, for example in the United
States. [UNVERIFIED for every provider. ZAK: for each provider, check where it processes data and
what safeguard covers the transfer (for example a UK adequacy decision, the UK Extension to the
EU-US Data Privacy Framework, or the UK International Data Transfer Agreement or Addendum). For
Supabase, the region is chosen when the project is created: choose a UK or EU region if
available and write it here: [SUPABASE REGION].]

## 10. How long we keep it

| Information | How long |
| --- | --- |
| A notice and its results when you are not using saved projects | Only while your session is open, as described in section 3 |
| Information sent to Anthropic | As set by Anthropic's terms [UNVERIFIED, see section 8] |
| A saved project | Until you delete it, or [RETENTION PERIOD FOR SAVED PROJECTS] after your last sign-in [ZAK TO DECIDE; the app does not yet delete anything automatically] |
| Usage records | [RETENTION PERIOD FOR USAGE RECORDS] [ZAK TO DECIDE; the app does not yet delete these at all] |
| Emails you send us | [RETENTION PERIOD FOR CORRESPONDENCE] |

<!-- Session-only: app.py:44-46, 179 and section 3 comments. No automatic deletion: the only
delete code is delete_project (ct/storage.py:102-106, 167-169); there is no expiry job and no
delete for usage_events anywhere in app.py, ct/ or supabase/. -->

## 11. How to delete your information

- **A saved project:** open it in **My projects**, open **Rename or delete this project**, tick
  the box and press **Delete project**. This deletes the project, with its results, dates and
  tracker, from our database.
- **Everything else** (your usage records, or all your data at once): email [CONTACT EMAIL] and
  we will delete it within the time set out in section 12.
- **Information Anthropic or other providers hold:** handled under their terms (section 8).
  Copies in a provider's backups may last longer than the live record. [UNVERIFIED: check
  Supabase's backup retention.]

<!-- app.py:655-664 (expander, confirmation checkbox, Delete project button calls
store.delete_project); ct/storage.py:167-169 (HTTP DELETE on the projects row filtered by owner
and id); local development store ct/storage.py:102-106. Usage records are a separate table
(supabase/schema.sql:22-28) that delete_project does not touch. -->

## 12. Your rights

You have the right to:

- **access** the personal information we hold about you;
- **rectification**: have inaccurate information corrected (you can also rename a project and
  edit its tracker yourself);
- **erasure**: have your information deleted (see section 11);
- **restriction**: ask us to limit how we use your information;
- **object** to our use of your information where we rely on legitimate interests;
- **data portability**: receive the information you gave us in a structured, machine-readable
  form (each project's Excel tracker is one way; ask us for the full saved record).

Where we rely on consent, you can withdraw it at any time.

To use any of these rights, email [CONTACT EMAIL]. We will reply within one month. [UNVERIFIED:
check the response time and any extensions in the ICO guidance before publishing.]
<!-- Rename and tracker edits: app.py:656-659, 625-647. Excel export of a project: app.py:391-394
(reports.build_excel with the tracker). -->

## 13. Complaints

If you are unhappy with how we use your information, please contact us first at
[CONTACT EMAIL]. You also have the right to complain to the Information Commissioner's Office
(ICO), the UK data protection regulator: ico.org.uk. [UNVERIFIED, to check: the ICO's current
complaints page and phone number, https://ico.org.uk/make-a-complaint/]

## 14. Do you have to give us your information?

No law requires you to give us any information. You need to upload a decision notice for
Aftergrant to read it. You only need to sign in (and so give us your email address) if you want
to save projects. You can use the analysis without signing in.
<!-- Analysis without sign-in: page_analyse (app.py:434-505) has no user check; only
save_button (app.py:409-416) and the projects page (app.py:694) need a signed-in user. -->

## 15. Automated decisions

Aftergrant uses an AI model to read notices and suggest dates, fees and drafts. It does not make
decisions about you that have legal or similarly significant effects. Its results are planning
aids that you should check against the notice; they are not legal advice.
<!-- Matches the app footer caveat, app.py:703-704. -->

## 16. Security

- Our database is locked so that the public access key can read nothing; the app reads it only
  from our server, and only we, as administrators, have other access.
- The server key stays on the server and is never sent to your browser.
- Every database request is limited to the signed-in user's own projects.
- Our keys are kept in the hosting provider's secrets settings, never in our code.

No system is completely secure. If we learn of a breach that puts your information at risk, we
will tell you and the ICO where the law requires.
<!-- supabase/schema.sql:31-35 (RLS on, no policies); ct/storage.py:5-9 and 124-128 (service key
used only in server-side httpx headers); ct/storage.py:132-133 (key never echoed in errors);
owner filter ct/storage.py:138, 144, 162, 169, 178; secrets from environment or st.secrets,
app.py:24-32 and .streamlit/secrets.toml.example:1-3; .gitignore lists .env and
.streamlit/secrets.toml. -->

## 17. Changes to this policy

We will update this page when Aftergrant changes how it uses information, and change the
effective date at the top. If a change matters to you, we will tell you in the app [or by email,
ZAK TO DECIDE].

---

## Notes for Zak (delete this whole section before publishing)

**Decisions only you can make**

1. **Streamlit usage statistics.** `.streamlit/config.toml` does not set
   `[browser] gatherUsageStats = false`, so Streamlit's default (on) applies. Its code sets a
   one-year identifier cookie and sends page details to Streamlit. UK cookie rules (PECR) may
   require consent for a cookie like this (UNVERIFIED, to check: the ICO's guidance on cookies,
   https://ico.org.uk/for-organisations/direct-marketing-and-privacy-and-electronic-communications/guide-to-pecr/cookies-and-similar-technologies/).
   The simplest fix is to switch it off, which is a
   one-line AMBER change the team has not made. Then delete the paragraph in section 5 and the
   row in section 7. Whether Community Cloud overrides the setting: UNVERIFIED.
2. **Google Fonts.** Keep and disclose (section 5), or host the two fonts in `theme/` and delete
   the paragraph.
3. **Who is responsible for third-party data in notices** (section 6), and whether business
   users need a data processing agreement (out of scope here).
4. **Lawful bases** (section 7).
5. **Retention periods** for saved projects, usage records and emails (section 10). The code
   deletes nothing on a timer today.
6. **Controller identity**: you as a sole trader or a company, plus contact email, postal
   address, and whether to pay the ICO data protection fee (to check:
   https://ico.org.uk/for-organisations/data-protection-fee/). Paying is a RED step.

**Things the code does not do yet that a good policy would want** (not fixed, listed for the
backlog)

- No way to delete your usage records or your whole account from the app.
- No automatic deletion of old projects or usage records.
- Usage records keep the signed-in email even after every project is deleted.

**Third-party facts still UNVERIFIED** (no web access in this run): Anthropic API retention and
training use; Streamlit Community Cloud hosting location, logs, cookies and whether it changes
the usage-statistics setting; Supabase region, backups and DPA; which Google profile fields
Streamlit's sign-in receives; Google Fonts logging; transfer safeguards for each provider; the
ICO's complaint contact and response-time guidance. UK GDPR Article 13 text, to check:
https://www.legislation.gov.uk/eur/2016/679/article/13 . ICO guidance on the right to be
informed, to check: https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/individual-rights/the-right-to-be-informed/

**Read as primary sources on 11 Nov 2026:** the Aftergrant code on `main` (commit c4bc127) and
the installed Streamlit 1.58.0 package source (the version pinned in `requirements.txt`).
