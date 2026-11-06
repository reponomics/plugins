# OpenSSF Best Practices — Gold

## Scope

Use section `gold`. Gold has 23 criteria. The badge and its tiered percentage credit require Silver, but the user can work on Gold answers before earning it. Use the saved project data for `achieve_silver`.

`{repo}` = repository URL. Categories: (M) MUST, (S) SHOULD, (G) SUGGESTED. `URL!` = justification must include a URL. `N/A?` = N/A allowed. `J!` = written justification required for Met. `N/A-J!` = written justification required for N/A.

## Basics

### Prerequisites

- `achieve_silver` (M) — the project must hold a silver badge. Use the saved project data. If silver is not yet achieved, record `Unmet` here and continue with whatever gold work the user has chosen; the gold badge itself waits on silver.

### Project oversight

- `bus_factor` (M, URL!) — losing any one member must not stall the project for lack of knowledgeable or competent personnel (bus factor ≥2). Use the maintainer's account of who could continue the work, supported where useful by contribution history. Merge rights or recent activity alone do not define this; competent project members need not all be maintainers. One knowledgeable person is Unmet, but the label “single-maintainer” does not decide it. When distinguishing personnel requirements from access continuity or review, use [Continuity and people](silver.md#continuity-and-people).
- `contributors_unassociated` (M, URL!) — at least two unassociated people made non-trivial contributions in the past year; they need not be maintainers. The details give 1,000 lines of code, 50 commits, or 20 pages of documentation as useful indicators, not mandatory numerical thresholds. Contributors are associated if the same organization pays them to work (as employees or contractors) and benefits from the project's results; the definition is not limited to payment for this project. Grants passing through different organizations from a common government/NGO source do not by themselves associate contributors. Use contributions and the maintainer's account of affiliations; maintainer count alone does not answer this.

### Other

- `copyright_per_file` (M, J!) — every source file carries a copyright statement identifying the holder; the official text permits "Copyright the [project name] contributors." near the top. Inspect project, generated, and vendored sources. When adding missing headers, preserve existing third-party attribution and identify the correct holder for each file.
- `license_per_file` (M, J!) — every source file carries a license statement, such as an SPDX identifier, license text, or stable license URL. An SPDX-only search can miss valid statements. If adding headers, use the license applicable to each file, including third-party files.

## Change Control

- `repo_distributed` (M, J!) — repo uses common distributed VCS. GitHub + git → Met, with a written justification.
- `small_tasks` (M, URL!) — project clearly identifies small tasks for new/casual contributors — issue labels like `good first issue`, `help wanted`, `first-timers-only`. Evidence: labeled issues actually exist ({repo}/labels, {repo}/issues?q=label:"good first issue"). Quickly fixable: label currently open tasks suitable for new contributors; documentation and test work can qualify.
- `require_2FA` (M, J!) — the project requires 2FA for developers changing the central repo or accessing private vulnerability reports. Achievable at any team size: every committer's GitHub account has 2FA enabled (GitHub has required 2FA for active contributors since 2023; an org can enforce it in settings). Use the user's account of these settings, or ask if they have not described them; account security settings are not publicly visible.
- `secure_2FA` (S, J!) — the 2FA mechanism uses cryptographic mechanisms; SMS alone explicitly does not qualify. TOTP apps, security keys, and passkeys do (official details note GitHub supports TOTP). Ask which second factor they use if they have not already said.

## Quality

### Coding standards

- `code_review_standards` (M, URL!, N/A?, N/A-J!) — documented code review requirements: how review is conducted, what must be checked, what is acceptable. Evidence: CONTRIBUTING.md / docs/ review section, or a REVIEWING.md. Quickly fixable: write the standards even if today only one person applies them (self-review checklist + CI gates); the criterion asks for the documentation, unlike two_person_review.
- `two_person_review` (M, J!) — another person reviews ≥50% of all proposed modifications before release, considering whether each is worthwhile and free of known issues arguing against inclusion. Use the project's review practice and history; merged-PR approvals are useful leads but need not describe all proposals or other review channels. A sole maintainer can review others' contributions, and an external collaborator can review the maintainer's changes. Neither reviewer must be a second maintainer; self-review, AI review, and CI do not supply another person.

### Working build system

- `build_reproducible` (M, URL!, N/A?, N/A-J!) — bit-for-bit reproducible build. N/A precondition per the official text: "no building occurs (e.g., scripting languages where the source code is used directly)". A pure-interpreted no-build project → N/A with that wording. If there is a build (bundling, compilation, wheels), the criterion applies: check for pinned toolchains/lockfiles, stripped timestamps, and ideally a documented rebuild-and-compare procedure. Use available rebuild results and the user's account of reproducibility. If the result is unclear, leave the status as `?` and ask. Record `Unmet` when a controlled independent rebuild using the same declared source and build inputs produces non-identical artifacts, the user reports that independent builds do not reproduce bit-for-bit, or other information establishes non-reproducibility.

### Automated test suite

- `test_invocation` (M, URL!) — test suite invocable in the standard way for the language (`npm test`, `pytest`, `go test`, `make check`). Note this is a MUST at gold (it was SHOULD at passing). Cite where it's documented.
- `test_continuous_integration` (M, URL!) — CI: new/changed code is frequently integrated and automated tests run on the result. The Gold details say full-time developers integrate "at least daily" — the emphasis is frequent integration to a central repo + automated testing, not merely having a workflow file. Evidence: {repo}/actions, workflow triggers on push/PR, recent runs.
- `test_statement_coverage90` (M, J!, N/A?, N/A-J!) — FLOSS automated test suite(s) reach ≥90% statement coverage. N/A only if no FLOSS tool can measure this for the language. Below 90%, or the project not measuring the required coverage, is Unmet subject to that exception. Use existing reports or measured results supplied by the maintainer. If only the assistant lacks an existing measurement, leave `?` and ask for it; offer help measuring coverage or improving tests when useful.
- `test_branch_coverage80` (M, J!, N/A?, N/A-J!) — FLOSS automated test suite(s) reach ≥80% branch coverage if a FLOSS tool can measure it in the language. Use the branch result; statement coverage does not answer this. Below 80%, or not measuring required branch coverage, is Unmet subject to the no-FLOSS-measurement-tool exception. If the assistant lacks an existing measurement, leave `?` and ask for it.

## Security

### Use basic good cryptographic practices

- `crypto_used_network` (M, J!, N/A?) — the produced software supports secure protocols (TLS 1.2+/HTTPS, SSHv2+, SFTP, SNMPv3) for all its network communications, and insecure ones (HTTP, FTP, telnet, SSLv3, SSHv1) are disabled by default (user opt-in only). N/A precondition: the software has no network communications at all. Grep for http:// URLs in code paths, ftp/telnet clients, TLS-verification-disabling flags.
- `crypto_tls12` (M, J!, N/A?) — if the software supports/uses TLS, it supports at least TLS 1.2. No TLS use → N/A. Use the actual runtime/library capabilities and project configuration, including any protocol restrictions; a platform name alone does not settle the answer.
- Section note: When deciding whether network or TLS use belongs to the produced software or independent hosting infrastructure, use [Cryptographic scope](passing.md#cryptographic-scope) to determine applicability. These two criteria turn on network/TLS use specifically; absence of an in-house crypto implementation does not establish N/A.

### Secured delivery against man-in-the-middle (MITM) attacks

- `hardened_site` (M, URL!) — project website, repo, and download site serve key hardening headers with nonpermissive values: CSP, HSTS, X-Content-Type-Options: nosniff, X-Frame-Options. Official details: GitHub and GitLab are known to meet this, and static sites are not exempt. Verify any separate site (GitHub Pages needs checking — it does not send CSP by default; a custom host may need header config). https://securityheaders.com/ gives a citable result.

### Other security issues

- `security_review` (M, J!) — a security review performed within the last 5 years, covering the security requirements and security boundary. Project members may conduct it, but human review is required, especially for design. If missing, help a human reviewer prepare and document the review; an assistant-only report does not satisfy it. Describe the completed review, its scope, and findings. N/A is unavailable.
- `hardening` (M, URL!, N/A?, N/A-J!) — hardening mechanisms in the produced software so defects are less likely to become vulnerabilities. The official details give examples: HTTP headers such as CSP, compiler flags that mitigate attacks (such as `-fstack-protector`), and compiler flags that eliminate undefined behavior. Least privilege explicitly does not count here. Describe the mechanisms used and link to the relevant code or configuration.

## Analysis

### Dynamic code analysis

- `dynamic_analysis` (M, J!, N/A?, N/A-J!) — apply at least one dynamic analysis tool to each proposed major production release before release. The tool must execute the software and either vary inputs to look for problems (for example, fuzzing, a web scanner, or suitable property-based testing) or be an automated test suite with ≥80% **branch coverage**. A security-specific focus is optional. `test_branch_coverage80` can establish the coverage alternative, but the qualifying suite must also run on the proposed release before release; a coverage result or static-analysis score alone does not satisfy this. Explain applicability when using N/A.
- `dynamic_analysis_enable_assertions` (S, J!, N/A?, N/A-J!) — many run-time assertions in the produced software, checked during dynamic analysis. Evidence: assert density in source, validation/invariant checks, tests executing with assertions enabled (Python asserts on by default under pytest; C builds without NDEBUG in test config).
