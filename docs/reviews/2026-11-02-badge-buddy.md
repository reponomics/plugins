# Badge Buddy quality review — 2026-11-02

Reviewed from commit `0f1e07e` on `polishing`, using verbosity-scope-guard as a retrospective pass over completed text. Scope: all 33 authored Markdown documents inside Badge Buddy, its three engineering templates, and the supporting repository documents listed below. The plugin's symlinked third-party notices were also read. Runtime code, catalog records, fixtures, and existing tests supplied evidence for documented behavior.

Each document was reviewed for audience, section purpose, reading order, accuracy, duplication, and necessary constraints. The README is human-facing and is not automatically loaded into a skill. Useful overlap between that audience and skill instructions was retained, including direct-controller examples. Required skill reading paths remain self-contained in `SKILL.md` and its references.

## Findings fixed

| Finding | Effect | Change |
| --- | --- | --- |
| Workflow references were listed after inspection/reporting and mainly triggered by edits. | Audits could produce recommendations before reading the relevant procedures. | Moved conditional reading instructions before inspection; pin and permission guides now explicitly apply to audits, and validation is read before editing to preserve a baseline. |
| Scorecard's numbered workflow obscured direct routes for questions, supplied JSON, and comparisons. | Narrow tasks could fetch unnecessary data or drift toward publication. | Added request-specific entry points and conditional remediation/publication reads. |
| Coverage reference lists described subjects without clear timing; static-analysis guides were scattered through the workflow. | Readers could load too much or miss prerequisites. | Added explicit reading paths for measurement, native language recipes, licenses, reporting, baseline/triage, and templates. |
| Best Practices startup prerequisites were implicit in the operation table. | An operation could be attempted before selecting paths and a working assessment. | Made invocation-path resolution and Start or resume prerequisites; later operation reads remain conditional. |
| Some Passing summaries equated tools or files with compliance. | GitHub hosting, tags, a release tool, a test directory, or ignore rules could produce unjustified Met answers. | Corrected public-access, release/version, test, vulnerability-fix, and credential summaries against the bundled catalog. Replaced prescribed `docs/` and SECURITY.md locations with actual content requirements. |
| Silver DCO instructions implied that publishing instructions establishes contributor assertions. | Documented intent could be mistaken for an implemented practice. | Required checking both the mechanism and its use. |
| Gold guidance called security review quickly fixable by an assistant, and suggested generic source-header edits. | Could overlook required human review or apply incorrect holders/licenses to third-party files. | Clarified human participation, acceptable license-statement formats, and correct attribution/license selection per file. |
| Shared Metal answers and controller validation limits were underexplained. | Existing answers or successful commands could be mistaken for compliance at a higher level. | Explicitly require reassessment against the selected level and distinguish synchronization/field validation from practice compliance. |
| Scorecard claimed that all commands emit JSON. | Callers could attempt to parse failures as JSON. | Matched the implementation: successful commands emit JSON; failures use stderr and a nonzero exit status. |
| Scorecard missing-result advice did not qualify GitHub Action publication by forge. | GitLab result/import users could be sent to an inapplicable setup path. | Kept Action publication conditional on GitHub and linked the appropriate diagnostic guidance. |
| Badge motivation, license details, controller summaries, and policy procedures repeated within runtime documents. | Added reading and maintenance without changing the decision. | Trimmed repeated encouragement; kept licensing details in their existing tables and controller/policy details at their operational locations. Converted plain sibling filenames into links. Removed an unused Makefile example variable and unsupported effort predictions. |
| Criteria maintenance said ordinary use did not download the website. | Contradicted public-answer synchronization. | Distinguished bundled criterion pages from the public project-answer API. |
| Implemented ADRs retained active handoff language and former operating-document names. | Historical plans could be mistaken for current work or current reading paths. | Marked the original plan as historical and linked the current application guide, preserving the decision record. |
| Root README linked to absent SECURITY.md and CHANGELOG.md files; the release guide also implied a checked-in changelog exists. | Readers were directed to nonexistent documents. | Removed the links and clarified that release automation does not maintain a repository changelog. |

## Open findings

| Finding | Evidence and next step |
| --- | --- |
| Missing internal agent instructions | Root AGENTS.md and CLAUDE.md point to `INTERNAL/AGENTS.md`. It was absent from this checkout, other local Codex worktrees, and all local Git history. Restore the intended instructions or update the root pointers. This review followed the user-supplied instructions. |
| Unexplained website-generated `[osps_…]` markers | The prior maintainer feedback records these markers in imported justifications; the current application guide does not explain them. Verify the site's generation behavior before adding a concise explanation beside synchronization. No semantics were inferred from the marker spelling. |
| Missing plugin icon | `make plugin-validate` passed but reported `ICON_MISSING` for Badge Buddy (and the two sibling plugins). Supply approved square artwork if preparing a directory listing; banner artwork was not repurposed during this documentation pass. |

## Document coverage and section purposes

Skill paths below are relative to `plugins/badge-buddy/skills/`. Retained sections have a distinct reader need; unchanged files were reviewed, not skipped.

### Best Practices (`ossf-bp-badges/`)

| Document | Section purpose and disposition |
| --- | --- |
| `SKILL.md` | Opening establishes scope and self-reporting stance; badge choice routes to the selected level; interpretation defines response semantics and selected-record lookup; drafting routes to style and peer review; application table routes by operation; invocation section resolves executable/data/repository paths. Retained this organization and all contracts. Clarified startup ordering and reassessment of shared fields. |
| `README.md` | Human introduction, peer-review expectations, reference index, and independence/licensing notice. Retained unchanged. |
| `references/application.md` | Startup and storage selection; repository working-copy/writeback rules; recording and preview isolation; export; transfer-method selection and individual method semantics; saving; API diagnostics; cleanup. All sections have distinct operation needs. Retained detailed proposal semantics and conditional API loading. Added explicit field-validation versus compliance boundary at startup. |
| `references/passing.md` | Scope/legend plus six official category groups provide lookup guidance for all 67 criteria. Thematic cryptographic scope distinguishes software/library use from independent hosting. Kept targeted thematic reading. Corrected overly compressed evidence shortcuts and preserved category/applicability requirements. |
| `references/silver.md` | Scope/legend plus official category groups cover all 55 criteria. Continuity/people comparison prevents conflating access, competence, independent contributions, and review. Retained detailed tricky cases. Corrected DCO shortcut and removed unsupported effort claim. |
| `references/gold.md` | Scope/legend and category/subcategory sections cover all 23 criteria. Kept prerequisite, coverage, reproducibility, and human-review distinctions. Clarified source-file licensing/attribution checks and human participation in security review. |
| `references/baseline.md` | Scope explains cumulative levels and field IDs; eight control-family sections cover all 64 controls; related-Metal table identifies differences when reusing facts. Retained requirements and conditional comparisons; removed an effort prediction from a heading. |
| `references/justification-style.md` | Voice/detail, links, four short worked answers, and example lookup routing each support drafting. All four quotes match bundled `project.json` exactly. Retained unchanged; examples illustrate different answer shapes and attribution remains adjacent. |
| `references/peer-review.md` | Review scope, supplied inputs, correction checklist, self-reporting stance, and output contract. Short and operational; retained unchanged. |
| `references/badgeapp-example.md` | Targeted field lookup, display-ID syntax, dated-example limitation, and separation from current assessment. Five lines with a distinct conditional purpose; retained unchanged. |

### Workflow maintenance and Scorecard

| Document | Section purpose and review outcome |
| --- | --- |
| `github-workflow-maintenance/SKILL.md` | Frontmatter scopes activation; opening bounds maintenance; Establish identifies request/authorization; new Reading path routes references before decisions; Inspect defines evidence/report; Implement summarizes changes; Actions settings separates policy selection; Validate defines completion evidence. Retained necessary constraints and shortened duplicated policy detail. |
| `github-workflow-maintenance/references/actions-settings.md` | Introduction establishes live/inherited policy authority; SHA policy explains compatibility; token default section distinguishes defaults from explicit scopes; allowlist section explains inventory and maintenance choices; Apply sequences proposal, deployment of compatible files, readback, rollback. Retained: each section has a distinct operational purpose. |
| `github-workflow-maintenance/references/permissions.md` | Evidence inventory, permission semantics/table, credential distinction, reusable workflow chains, untrusted events, and removal validation all serve concrete decisions. Only tangential App tutorial instruction shortened. |
| `github-workflow-maintenance/references/pinning-and-updates.md` | Resolve section covers ref kinds, annotated tags, selected-version semantics, comments; Updates covers configuration integration, coverage gaps, review responsibility, exact-SHA policy upkeep. Retained; details prevent distinct failure modes. |
| `github-workflow-maintenance/references/validation.md` | Baseline/patch preservation; ordered post-edit checks; Scorecard return path; final evidence report. Retained. Its baseline obligation justified earlier loading from SKILL.md. |
| `ossf-scorecard/SKILL.md` | Activation remains unchanged; purpose shortened; new routing identifies conceptual/import/repository/publication/diagnostic paths; setup owns executable and output contract; Coaching establishes evidence/authorization; five workflow steps own acquisition, publication, interpretation, implementation, comparison. Removed duplicate command catalog and diagnostic section after moving unique information into setup/routing or retaining it in references. |
| `ossf-scorecard/references/action-publication.md` | Opening scopes invocation; Prepare defers current restrictions to upstream and workflow edits to maintenance skill; Verify separates local/run/API outcomes; Badge defines endpoint and verification. Retained structure; linked conditional credential read. |
| `ossf-scorecard/references/authentication-and-results.md` | Evidence section preserves snapshots and missing data; Failures separates missing/service/auth/input errors; Credentials scopes optional access; Diagnostics bounds user-established CLI usage. Corrected GitLab routing and linked publication guide; retained diagnostic limitations. |
| `ossf-scorecard/references/remediation-playbook.md` | Introduction bounds qualitative leads; workflow, dangerous-workflow, policy/content, branch/review, analysis/vulnerabilities, release, and historical/external sections map observed findings to investigations. Retained all sections; sibling cross-references now clickable. |

### Coverage and static analysis

| Document | Section purposes and review disposition |
| --- | --- |
| `coverage-baseline/SKILL.md` | Introduction states the task; scope establishes authorization and preserves project tooling; reading path routes references; measurement defines valid evidence; publication covers integration; test improvement prioritizes behavior; thresholds describe policy; validation reports measured outcomes and handoffs. Shortened repetition and made reading conditions explicit. |
| `coverage-baseline/references/measurement.md` | Python and JS sections provide adaptable configuration/commands and accurate metric interpretation; baseline record defines reproducible evidence. Retained technical detail, removed unused Makefile variable and rhetorical conclusion. |
| `coverage-baseline/references/languages.md` | Opening and format table select native reports; each ecosystem section explains its runner/build-specific recipe and limitations; final section covers mixed reports and publication. Shortened repeated badge motivation; preserved all language recipes and metric distinctions. |
| `coverage-baseline/references/licenses.md` | Intro establishes use/date; table supplies tool licenses; exception paragraphs distinguish runtime exceptions and PHP drivers; final paragraph distinguishes hosted Codecov. Shortened intro; retained necessary qualifications and upstream sources. |
| `coverage-baseline/references/reporting.md` | Opening gives setup order; options table supports service choice; template section states assumptions; authentication section separates default-branch/PR paths; baseline/status section explains processing and gates; badge/evidence section defines truthful claims and OpenSSF handoff; checklist checks observed behavior. Shortened repeated motivation/authorization language. |
| `coverage-baseline/assets/templates/workflows/python-coverage.yml` | Adaptation comments identify prerequisites; coverage job runs tests/reports; separate Codecov job limits upload authority to default-branch reporting. Reviewed against reporting guide; retained unchanged. |
| `static-analysis/SKILL.md` | Intro states outcome; reading path selects references by stage; choice table separates tools and boundaries; scan section covers execution/security; badge section explains status; triage section handles findings and handoffs. Shortened motivation and added explicit reading route. |
| `static-analysis/references/bandit.md` | Overview sets scanner limits; configuration section defines scope and narrow suppressions; baseline/enforcement section separates findings from operational errors and keeps provenance. No edit warranted. |
| `static-analysis/references/codeql.md` | Opening selects default/advanced setup; availability/licensing establishes suitability; language/build table guides extraction; advanced setup covers triggers, uploads, and permissions; verification separates execution from enforcement. Shortened intro and consolidated licensing detail into linked table. |
| `static-analysis/references/snyk.md` | Product table prevents dependency/SAST confusion; suitability/data transfer section handles account and source transfer; scan section defines status/report handling; credential section covers untrusted execution; conclusion links truthful badge guidance. Shortened motivation and licensing duplication; retained operational distinctions. |
| `static-analysis/references/languages.md` | Intro routes to the right recipe and badge semantics; ecosystem sections preserve native builds and explain scope/enforcement; conclusion connects CI to badge. Shortened motivational prose; retained recipes and limitations. |
| `static-analysis/references/licenses.md` | Intro defines OSI/date/scope; local-tool table and exception notes establish licensing; product table distinguishes engines, queries, clients, and services. Shortened intro/conclusion without changing license claims. |
| `static-analysis/references/baseline-and-gates.md` | Intro identifies when used; baseline steps require complete scans and triage; gate section separates execution/upload/policy; badge section defines badge claims and OpenSSF/Scorecard handoffs. Replaced generic encouragement with a direct purpose statement. |
| `static-analysis/assets/templates/bandit.yaml` | Comments explain explicit configuration, exclusions, and retained tests/scripts; config excludes only virtual environments. Retained unchanged. |
| `static-analysis/assets/templates/workflows/codeql-python.yml` | Comments identify Python/advanced/default-setup prerequisites; triggers support PR/default/scheduled analysis; job permissions and steps initialize/analyze/upload. Retained unchanged. |

### Plugin and supporting documents

| Document | Section purposes and disposition |
| --- | --- |
| `plugins/badge-buddy/README.md` | Installation and prompts introduce the product; preparation, storage/preview, and submission explain the user experience; independent skill sections help choose a task; Development supplies human-oriented CLI examples and maintainer links; notices establish attribution and independence. Retained the separate-audience explanations and direct-use examples; shortened one internally repetitive peer-review paragraph. |
| `plugins/badge-buddy/assets/examples/badgeapp/README.md` | Dates and scopes the worked example; identifies data/provenance/license files; distinguishes questionnaire licensing from the project's software license. Retained; data and license checksums match provenance. |
| `THIRD_PARTY_NOTICES.md` and the plugin symlink | Separate third-party components, sources, copyright, and licenses. Retained verbatim notices. The plugin-root path resolves through `../../THIRD_PARTY_NOTICES.md` in this checkout. |
| `docs/criteria-maintenance.md` | Explains bundled data, change detection, accepted-revision updates, guidance review, and release verification. Preserved the source inventory and version/provenance distinctions; corrected the ordinary-use network statement. |
| `docs/badgeapp-maintenance.md` | Records source revisions and upstream documentation/code discrepancies for transfer/API and Baseline interpretation. Kept these maintainer details out of mandatory skill reading; retained unchanged. |
| `docs/adr/0001-unify-assessment-views.md` | Historical renderer-consolidation decision, context, implementation contract, acceptance criteria, and consequences. Preserved superseded requirements as history; removed active session-handoff wording and linked current instructions. |
| `docs/adr/0002-list-based-preview-review.md` | Current interaction decision and its rationale; revision scope, user flow, views/order, refresh, presentation, validation/transfer concerns, and historical verification. Retained design detail; explained where the former operating documents now live. Historical test counts are not this review's results. |
| `tests/badge-buddy/engineering-skill-evals.md` | Defines behavior cases, expected outcomes, and evaluation records for coverage/static analysis. Retained; explicitly distinguishes proposed cases from evidence of executed evaluations. |
| Root `README.md` | Marketplace selection, installation, layout, development entry points, and licensing. Removed broken SECURITY/CHANGELOG links; retained other sections. |
| `CONTRIBUTING.md` | Contribution/issue guidance, conduct link, and artwork maintenance. Read for repository conventions; retained unchanged. |
| `docs/releases.md` | Version policy, trial/bootstrap procedures, normal releases, criteria verification, failure recovery, and local publishing commands. Clarified that automation does not maintain a repository changelog. No remote trial state was verified or publication performed. |

## Verification

- `make check`: passed 234 tests (142 Badge Buddy, 17 Repo Starter Kit, 3 Release Buddy, 72 maintenance), followed by Python compilation using the existing `venv`.
- `make plugin-validate`: all three plugins passed; missing-icon warnings are recorded above.
- Ad hoc local Markdown check: 155 file/heading targets resolved across the 33 authored plugin documents and six supporting documents. This was a local target check, not an external-URL availability test.
- All 209 criterion entries are represented in the badge references: Passing 67, Silver 55, Gold 23, and Baseline 24 + 19 + 21.
- All four quoted BadgeApp answers match the bundled JSON; the questionnaire and license SHA-256 values match their provenance record.
- Existing documentation-integrity checks exercised controller command examples without Claude shell variables and parsed Scorecard examples. Existing template checks verified SHA pins, read-only defaults, and disallowed privileged triggers.
- Re-read the completed edits and ran `git diff --check`; no runtime, template behavior, or catalog changes were made.

This pass did not execute fresh model-session evaluations, hosted integrations, live BadgeApp writes, or a new upstream version/license freshness audit. Existing dated external-source claims remain dated, with version-specific verification required when adopting tools. Static checks establish document and command integrity, not agent adherence or current hosted-service behavior.
