# OpenSSF Best Practices — Silver

## Scope

Use section `silver`. The Silver badge and its tiered percentage credit require Passing, but the user can work on Silver answers before earning it. Use the saved project data for `achieve_passing`.

`{repo}` = repository URL. Categories: (M) MUST, (S) SHOULD, (G) SUGGESTED. `URL!` = justification must include a URL. `J!` = a Met answer requires a written justification. `N/A?` = N/A allowed; `N/A?*` = N/A allowed but requires a written justification.

## Basics

- `achieve_passing` (M) — passing-level badge achieved.
- `contribution_requirements` (M, URL!) — CONTRIBUTING states requirements for acceptable contributions (e.g. reference to the coding standard). SHOULD at passing, MUST here.
- `dco` (S, URL!) — developers of non-trivial amounts of software assert they are legally authorized to contribute, using a DCO, CLA, or another legal mechanism. Check the contribution process and its use; adding DCO instructions alone does not establish that contributors make the assertion.
- `governance` (M, URL!) — documented governance model: how decisions are made, key roles. The details explicitly allow small-project governance — "the project owner and lead makes all final decisions" written down counts. Document the project's actual decision-making model at any team size.
- `code_of_conduct` (M, URL!) — CoC posted in a standard location. Contributor Covenant in CODE_OF_CONDUCT.md is the norm.
- `roles_responsibilities` (M, URL!) — key roles + their responsibilities documented, and it's clear who holds which. May share a file with governance.
- `access_continuity` (M, URL!) — within a week after confirming the loss of any one person's support, the project must be able to create/close issues, accept changes, and release software. Necessary keys, passwords, and legal rights must remain accessible; upstream permits an individual maintainer's lockbox and will arrangement. An arrangement must actually enable that continuity. No arrangement → Unmet; N/A is unavailable. When distinguishing access continuity from personnel or review requirements, use [Continuity and people](#continuity-and-people).
- `bus_factor` (S, URL!) — the project should have a bus factor ≥2: losing any one member does not stall it for lack of knowledgeable or competent personnel. Use the maintainer's account of who could continue the work; contribution history can help. Merge rights alone do not establish competence, and competent people need not all be maintainers. Only one such person → Unmet; N/A is unavailable. Recruiting or mentoring another contributor can help share the knowledge needed to continue the project.
- `documentation_roadmap` (M, URL!) — documented roadmap: what the project intends to do and not do for the next year. Need not be detailed and need not be achieved. ROADMAP.md, docs/roadmap, or a pinned/milestoned plan.
- `documentation_architecture` (M, URL!, N/A?*) — high-level design doc: major components, relationships, key properties. docs/architecture.md or an ARCHITECTURE section. N/A only if the project produces no software.
- `documentation_security` (M, URL!, N/A?) — documented security requirements: what users can and cannot expect from the software. A "Security model"/"Security requirements" section in SECURITY.md or docs. Distinct from how-to-report (passing) — this is the promises.
- `documentation_quick_start` (M, URL!, N/A?*) — quick-start guide that gets a new user doing something fast. README "Quick start" section.
- `documentation_current` (M, J!, N/A?*) — docs kept consistent with the current version; known doc defects fixed (treated as bugs). Evidence: docs updated alongside recent feature commits; no stale open "docs are wrong" issues.
- `documentation_achievements` (M, URL!) — the repository front page and/or project website identifies and links achievements (including this badge) within 48 hours of public recognition. A README badge row or a suitable website page can satisfy this.
- `accessibility_best_practices` (S, J!, N/A?*) — accessibility best practices where reasonable. Details: most CLI apps are "fairly accessible as-is" (Met with that reasoning); web UIs need WCAG-minded effort; program libraries are the canonical N/A.
- `internationalization` (S, J!, N/A?*) — software internationalized to enable localization. N/A when it produces no end-user-facing text and doesn't sort human-readable text (details' own carve-out). Libraries and dev tools emitting only technical/log output commonly justify N/A.
- `sites_password_security` (M, J!, N/A?*) — project-site passwords stored as salted iterated hashes. Details state outright: using GitHub meets this.

## Change Control

- `maintenance_or_update` (M, J!, N/A?*) — maintain the most-used older versions OR provide an upgrade path; difficult upgrades must be documented. Evidence: CHANGELOG breaking-change notes, UPGRADING.md, SemVer policy. A single-supported-latest-version project with easy documented upgrades → Met with that justification, not N/A.

## Reporting

- `report_tracker` (M, J!, N/A?*) — issue tracker for individual issues (SHOULD at passing, MUST here).
- `vulnerability_report_credit` (M, URL!, N/A?*) — credit reporters of all vulns resolved in the last 12 months (unless anonymity requested). If none resolved in 12 months, N/A; explain that no reports were resolved in that period.
- `vulnerability_response_process` (M, URL!) — documented process for responding to vulnerability reports: triage, fix, disclose. Goes beyond passing's how-to-report; add a "What happens after you report" section to SECURITY.md.

## Quality

- `coding_standards` (M, URL!, N/A?*) — identify the specific style guide(s) per primary language and require compliance. CONTRIBUTING naming PEP 8/ruff, ESLint+Prettier, gofmt, rustfmt counts; cite the config file.
- `coding_standards_enforced` (M, J!, N/A?*) — style automatically enforced if a FLOSS tool exists for the language: lint/format job that fails CI. Documented rare exceptions allowed. Cite the workflow file.
- `build_standard_variables` (M, J!, N/A?*) — native-binary builds honor CC/CFLAGS/CXX/CXXFLAGS/LDFLAGS (extend, never replace). No native binaries produced (pure Python/JS/etc.) → N/A.
- `build_preserve_debug` (S, J!, N/A?*) — build/install preserves debug info when requested (no forced strip). N/A if there is no build or installation system — details name "typical JavaScript libraries".
- `build_non_recursive` (M, J!, N/A?*) — no recursive per-subdirectory builds across cross-dependent subdirs. Single-pass builders (npm, cargo, gradle, single Makefile) → Met; no build system → N/A.
- `build_repeatable` (M, J!, N/A?*) — rebuilding from the same source yields bit-for-bit identical results. N/A when no building occurs (interpreted source used directly). Embedded timestamps/paths can break repeatability. Use existing build comparisons and the user's account; if unclear, ask and leave the answer `?`. Offer to build twice and compare results when the user wants help checking repeatability.
- `installation_common` (M, J!, N/A?*) — easy install AND uninstall via a common convention: language/system package manager, standard container image.
- `installation_standard_variables` (M, J!, N/A?*) — installation honors standard location conventions (e.g. DESTDIR on POSIX). Package-manager installs follow their ecosystem's conventions → Met; no installation system or no applicable convention → N/A.
- `installation_development_quick` (M, J!, N/A?*) — quick, conventional dev-environment setup including tests: "git clone; npm ci; npm test" documented in CONTRIBUTING, or a devcontainer/setup script.
- `external_dependencies` (M, URL!, J!, N/A?*) — dependencies listed in a computer-processable way: package.json, pyproject.toml, go.mod, or Cargo.toml and the lockfile.
- `dependency_monitoring` (M, J!, N/A?*) — dependencies (including vendored copies) monitored for known vulns; exploitable ones fixed. Dependabot alerts/updates config, osv-scanner or audit job in CI.
- `updateable_reused_components` (M, J!, N/A?*) — make reused externally maintained components easy to identify and update, or use standard system/language components. Package management is a common approach. Vendored copies, including forks, can qualify when easy to identify and update; updating a system library does not update a separately bundled copy.
- `interfaces_current` (S, J!, N/A?*) — avoid deprecated/obsolete functions and APIs where FLOSS alternatives are broadly available. Evidence: no deprecation warnings in CI logs, current major versions of runtime/APIs.
- `automated_integration_testing` (M, J!) — automated test suite applied on each check-in to a shared repo for at least one branch, producing a pass/fail report. CI test workflow triggered on push satisfies this. N/A is not available; no CI-run tests means Unmet. Cite the workflow file URL.
- `regression_tests_added50` (M, J!, N/A?*) — regression tests added for ≥50% of bugs fixed in the last 6 months. Sample closed bug-labeled issues/PRs and check for accompanying tests. No bugs fixed in the window → N/A.
- `test_statement_coverage80` (M, J!, N/A?*) — FLOSS test suite(s) reach ≥80% statement coverage, if a FLOSS tool can measure it in the language. Use measured results supplied by the maintainer or an existing report. A project that does not measure the required coverage is Unmet, subject to the no-FLOSS-measurement-tool exception; if only the assistant lacks the existing measurement, leave `?` and ask for it. Below 80% is Unmet, not N/A.
- `test_policy_mandated` (M, J!, N/A?*) — formal written policy that tests must be added with major new functionality (passing accepted informal; silver wants it in writing). A sentence in CONTRIBUTING satisfies it.
- `tests_documented_added` (M, J!, N/A?*) — the documented change-proposal instructions include that policy (SUGGESTED at passing, MUST here). Same CONTRIBUTING section usually covers both — cite it for each criterion separately.
- `warnings_strict` (M, J!, N/A?*) — maximally strict warnings where practical (SUGGESTED at passing, MUST here): "strict": true tsc, broad ruff/ESLint rule sets, -Wall -Wextra, clippy. Cite the config and note any documented practicality exceptions.

## Security

- `implement_secure_design` (M, J!, N/A?*) — secure design principles implemented (fail-safe defaults, complete mediation, deny by default), not just known. Describe concrete design choices in this codebase, using the user's explanations where helpful. N/A only if not producing software.
- Crypto block (all J!, all N/A?): When deciding whether a mechanism belongs to the produced software or independent hosting infrastructure, use [Cryptographic scope](passing.md#cryptographic-scope) to determine applicability. Use the maintainer's description and existing project information. Answer each applicable question; credentials or network use can make individual criteria relevant even without an in-house crypto implementation.
  - `crypto_weaknesses` (M) — default security mechanisms must avoid algorithms/modes with known serious weaknesses (SHA-1 as a security hash, CBC in SSH). Silver makes Passing's SHOULD a MUST; it is not limited to algorithms already completely broken.
  - `crypto_algorithm_agility` (S) — support multiple cryptographic algorithms so users can quickly switch if one breaks. Library support helps when the project exposes usable alternatives; a dependency listing algorithms does not alone establish that users can switch.
  - `crypto_credential_agility` (M) — support storing authentication credentials and private cryptographic keys in files separate from other information, including ordinary configuration, databases, and logs, and let users update/replace them without recompilation. Reading a replaceable dedicated secret/key file is one implementation. This is a required capability, not a mandate that every deployment use it; environment-variable-only support or absence of hardcoded secrets does not establish separate-file support. N/A if the project never processes either credentials or private keys.
  - `crypto_used_network` (S) — support secure protocols for all the produced software's network communications (for example, TLS 1.2+/HTTPS or SSHv2+). Insecure protocols should be disabled by default and enabled only by explicit user configuration. No network communications → N/A.
  - `crypto_tls12` (S) — if the software supports or uses TLS, support at least TLS 1.2. Use the actual runtime/library capabilities and project configuration; no TLS use → N/A.
  - `crypto_certificate_verification` (M) — if TLS is supported/used, verify certificates by default, including subresources. Delegation can implement this; confirm the behavior used by the application. Default disablers such as `rejectUnauthorized: false`, `verify=False`, or `InsecureSkipVerify` are useful leads. No TLS use → N/A.
  - `crypto_verification_private` (M) — if TLS is supported/used, verify certificates before sending HTTP headers containing private information, such as secure cookies or authentication headers. Explain the behavior of the library/configuration used. No TLS use → N/A.
- `signed_releases` (M, J!, N/A?*) — sign project results released for widespread use, including source and generated deliverables such as packages, executables, or containers. A signed git tag covers the results in its tree; generated results distributed separately from git must be separately signed. Identify what is distributed, which signature covers each result, and the documented process to obtain public signing keys and verify signatures. Keep private signing keys off sites directly distributing software to the public. Signed tags and artifact signatures (for example, using Sigstore) are options for their respective results; a signed source tag alone does not cover a separately published binary. N/A if releases are not intended for widespread use.
- `version_tags_signed` (G, J!) — important version tags cryptographically signed and verifiable. Check `git tag -v` / GitHub "Verified" badge on tags.
- `input_validation` (M, J!, N/A?*) — check inputs from potentially untrusted sources against their allowed patterns or ranges and reject invalid input wherever restrictions apply. Intentionally unrestricted content, such as file-upload contents, need not acquire format restrictions. Denylists are normally insufficient. Point to the schema validation layer (zod/pydantic/JSON Schema) or parser.
- `hardening` (S, J!, N/A?*) — hardening mechanisms so defects are less likely to become vulnerabilities: CSP and security headers (web), hardening compiler flags (native). Least privilege explicitly does not count here.
- `assurance_case` (M, URL!) — documented assurance case with all four parts: threat model, trust boundaries, argument that secure design principles are applied, argument that common implementation weaknesses (OWASP Top 10 / CWE Top 25) are countered. N/A is not available. If missing, offer to draft docs/security/assurance-case.md with the user.

## Analysis

- `static_analysis_common_vulnerabilities` (M, J!, N/A?*) — at least one static analysis tool with rules that look for common vulnerabilities (SUGGESTED at passing, MUST here): CodeQL security queries, bandit, brakeman, gosec. Same taxonomy caution as passing: SCA/dependency scanners and Scorecard are not static analysis of the code. N/A only if no FLOSS tool can implement this for the language. Cite the workflow.
- `dynamic_analysis_unsafe` (M, J!, N/A?*) — if the produced software includes memory-unsafe language code (such as C/C++), routinely combine a dynamic tool with memory-safety detection (for example, ASAN, MemorySanitizer, valgrind, or suitable widespread assertions). MUST here vs SUGGESTED at Passing. If no memory-unsafe software is produced → N/A; use the project's language and native-code information.

## Continuity and people

These criteria ask different questions. Use the project's arrangements and the maintainer's account; a contributor graph or a count of maintainers alone cannot answer all four.

| Criterion | What matters |
| --- | --- |
| Silver `access_continuity` (MUST) | Necessary access and legal rights allow issues, changes, and releases to resume within a week after any one person's loss of support is confirmed. Upstream explicitly permits an individual maintainer's lockbox and will arrangement when it meets this condition. |
| Silver `bus_factor` (SHOULD); Gold `bus_factor` (MUST) | Losing any one project member does not stall the project through lack of knowledgeable or competent personnel. A second account with permissions is not itself a second knowledgeable person. |
| Gold `contributors_unassociated` (MUST) | At least two significant contributors in the past year are unassociated under the criterion's organization/payment definition. They need not both be maintainers. |
| Gold `two_person_review` (MUST) | Another person reviews at least half of all proposed modifications before release. The reviewer need not be a maintainer; self-review and automated checks do not supply another person. |

A continuity arrangement does not by itself establish the bus factor, and one maintainer can still work with significant contributors and reviewers. Assess the stated conditions rather than assigning a status from the label “single-maintainer.”
