# OpenSSF Best Practices — Passing

## Scope

Use section `passing`. Passing has 67 criteria and no prerequisite badge. Its achievement also satisfies Silver's `achieve_passing` requirement.

`{repo}` = repository URL. Categories: (M) MUST, (S) SHOULD, (G) SUGGESTED. `URL!` = justification must include a URL. `N/A?` = N/A allowed.

## Basics

- `description_good` (M) — README opening describes what/for whom.
- `interact` (M) — README/site says how to obtain, give feedback, contribute.
- `contribution` (M, URL!) — CONTRIBUTING.md describes the process.
- `contribution_requirements` (S, URL!) — CONTRIBUTING states standards.
- `floss_license` (M) / `floss_license_osi` (G) — check LICENSE (MIT/Apache-2.0 → both Met).
- `license_location` (M, URL!) — cite the license file, such as `{repo}/blob/main/LICENSE`. An adequate complete-tree search finding no qualifying license file or `LICENSES/` directory supports `Unmet`; a limited inspection that merely misses the file leaves the answer inconclusive.
- `documentation_basics` (M, N/A?) — document installation, startup, use, and secure use where relevant. A README, other media, or linked material can suffice; a `docs/` directory is not required.
- `documentation_interface` (M, N/A?) — API/endpoint/CLI reference docs.
- `sites_https` (M) — all project URLs https.
- `discussion` (M) — GitHub issues/discussions suffice.
- `english` (S) — docs in English.
- `maintained` (M) — the project is maintained: at minimum, it attempts to respond to significant problem and vulnerability reports. The details note that pursuing a badge probably indicates maintenance. Recent commits or releases can be useful leads, but a stable, responsive project need not manufacture activity; limited resources or rejected proposals do not establish abandonment. Known cessation of maintenance is Unmet.

## Change Control

- `repo_public` (M), `repo_track` (M), `repo_distributed` (G) — a publicly readable Git repository with a URL and change/author/date history can satisfy all three. GitHub hosting alone does not establish public access.
- `repo_interim` (M) — interim versions are available in the source repository for collaborative review between releases; a development branch can satisfy this.
- `version_unique` (M), `version_semver` (G), `version_tags` (G) — check that every user release has a unique identifier, uses SemVer or CalVer, and is identified in version control, respectively. Tags and release history are useful leads: `{repo}/tags`.
- `release_notes` (M, URL!, N/A?) — every release needs a human-readable summary of major changes and upgrade impact. Check GitHub Releases or CHANGELOG.md; a release tool or raw commit log alone is insufficient. N/A is permitted for single-location software using continuous delivery.
- `release_notes_vulns` (M, N/A?) — if no publicly known vulnerabilities have ever been fixed in a release, N/A; explain that history.

## Reporting

- `report_process` (M, URL!) — CONTRIBUTING/README says how to file bugs.
- `report_tracker` (S) — issue tracker exists.
- `report_responses` (M) — check the tracker: majority of bug reports in the last 2–12 months acknowledged. Young/empty tracker: still Met, but note the basis. Ask the user about response history if the tracker and conversation leave it unclear.
- `enhancement_responses` (S) — same for feature requests.
- `report_archive` (M, URL!) — issue history at `{repo}/issues`.
- `vulnerability_report_process` (M, URL!) — publish the vulnerability-reporting process on the project site. SECURITY.md is one suitable location; offer to document the process if none is published.
- `vulnerability_report_private` (M, URL!, N/A?) — GitHub Private Vulnerability Reporting enabled and/or security email in SECURITY.md.
- `vulnerability_report_response` (M, N/A?) — every vulnerability report received in the last 6 months had an initial response within 14 days. Choose N/A if none were received. Use the actual response history; a policy promise alone does not establish this.

## Quality

- `build` (M, N/A?) — build command exists (npm run build / make / cargo). Pure-interpreted no-build projects: N/A.
- `build_common_tools` (G, N/A?), `build_floss_tools` (S, N/A?) — standard FLOSS toolchain → Met.
- `test` (M) — use an automated test suite publicly released as FLOSS, with clear instructions or configuration showing how to run it. Name the suite and its entry point.
- `test_invocation` (S) — standard single command (`npm test`, `make test`, `pytest`), documented.
- `test_most` (G) — the suite covers most code branches, input fields, and functionality. Use coverage reports and test scope; this criterion sets no numerical threshold.
- `test_continuous_integration` (G) — CI workflow on push/PR. Cite the workflow file URL.
- `test_policy` (M) — a general policy says tests should be added to the automated suite for major new functionality. An informal, even word-of-mouth policy is sufficient; use the maintainer's account. Silver adds a formal written policy requiring those tests.
- `tests_are_added` (M) — evidence from the most recent major changes shows that the policy is followed in practice. Release notes and associated test changes are useful leads; tests should typically accompany major functionality, but perfection is not required.
- `tests_documented_added` (G) — the change-proposal instructions document the test-adding policy, for example in CONTRIBUTING. Documentation is SUGGESTED at Passing; its absence does not negate an informal `test_policy` or tests actually added.
- `warnings` (M, N/A?) — enable at least one compiler warning flag, safe language mode, or linter for code quality/common mistakes if a FLOSS tool can do so in the language. Examples: `-Wall`, JavaScript strict mode, ESLint, ruff; cite the relevant configuration. Maximum strictness belongs to `warnings_strict`.
- `warnings_fixed` (M, N/A?) — address warnings from `warnings`: fix them or mark false positives in source. The details allow some accepted warnings (typically fewer than one per 100 lines or fewer than ten); these are typical quantities, not fixed limits. A CI gate can help, but warnings-as-errors is not required.
- `warnings_strict` (G, N/A?) — strive for maximum strictness where practical (for example, `-Wextra`); some warnings cannot be effectively enabled for a particular project. Describe the enabled checks and any practical limits.

## Security

- `know_secure_design` (M) / `know_common_errors` (M) — the primary developer understands secure design principles and common implementation errors (for example, least privilege, fail-safe defaults, OWASP Top 10, and CWE Top 25). Use what the user has told you about their knowledge and experience; ask if they have not addressed it. Practical, self-directed learning qualifies; formal training and credentials are not required. Explain unfamiliar principles such as least common mechanism or separation of privilege when useful. The referenced OpenSSF Fundamentals course (free to audit, by David A. Wheeler — author of these criteria) is an optional learning resource and preparation for Silver.
- Crypto block (all N/A?): When deciding whether a mechanism belongs to the produced software or independent hosting infrastructure, use [Cryptographic scope](#cryptographic-scope) to determine applicability. Crypto called through dependencies is still relevant; independent hosting infrastructure can be outside the produced application's scope. Use the maintainer's description and existing project information; source searches such as `crypto|hmac|jwt|sign|digest|timingSafe|subtle|private.?key` can locate uses when needed. The form's whole-section “no crypto” shortcut is appropriate only when no included criterion applies; otherwise answer individually.
  - `crypto_published` (M, N/A?) — default cryptographic protocols and algorithms must be publicly published and expert-reviewed. A standard library is a useful lead; identify the protocols and algorithms actually used by default, since delegation alone does not establish this.
  - `crypto_call` (S, N/A?) — if the produced software is an application or library whose primary purpose is not implementing cryptography, it should call software designed for cryptography instead of implementing its own. Runtime crypto modules, OpenSSL, or libsodium are examples of suitable delegation.
  - `crypto_floss` (M, N/A?) — every crypto-dependent feature must be implementable using FLOSS. Identify the available FLOSS implementation; requiring a proprietary-only implementation would fail this condition.
  - `crypto_keylength` (M, N/A?) — defaults meet the criterion's NIST-through-2030 minimums: symmetric key 112 bits, factoring modulus 2048, discrete-log key 224 and group 2048, elliptic curve 224, hash 224. Password hashes are explicitly excluded from that hash minimum; use `crypto_password_storage`. Smaller keylengths must be completely disableable, though optional smaller values are permitted. Check the mechanisms used, generated key sizes, and configuration.
  - `crypto_working` (M, N/A?) — defaults must avoid broken algorithms (MD4, MD5, single DES, RC4, Dual_EC_DRBG) and modes inappropriate to their context. The interoperability exception requires the most recent protocol version broadly supported by the ecosystem, that ecosystem requiring the broken mechanism, and no more secure alternative there; document relevant risks and known mitigations. Optional user-enabled compatibility mechanisms are allowed. ECB and unauthenticated CTR are warning signs, not a context-free list of forbidden modes.
  - `crypto_weaknesses` (S, N/A?) — defaults avoid algorithms/modes with known serious weaknesses (SHA-1 as a security hash, CBC mode in SSH).
  - `crypto_pfs` (S, N/A?) — the produced software's key-agreement mechanisms should provide perfect forward secrecy: later compromise of long-term keys does not compromise earlier session keys. Identify the actual protocol/configuration; a modern platform name alone does not establish this. Independent external web-server TLS can be outside the application's scope, as in the BadgeApp example.
  - `crypto_password_storage` (M, N/A?) — if the software causes passwords to be stored for authenticating external users (inbound authentication), use a key-stretching/iterated hash such as Argon2id, bcrypt, scrypt, or PBKDF2 with a per-user salt. Plain or fast hashes are Unmet. Stored credentials used to authenticate to other systems (outbound authentication) are outside this criterion; no inbound password storage → N/A.
  - `crypto_random` (M, N/A?) — keys and nonces come from a CSPRNG (`secrets`, `crypto.randomBytes`, `SecureRandom`, `window.crypto.getRandomValues`); grep security paths for insecure generators (`Math.random`, `java.util.Random`, bare `random.random`).
- `delivery_mitm` (M) — use a delivery mechanism that counters MITM attacks, such as HTTPS or SSH/SCP.
- `delivery_unsigned` (M) — a hash retrieved over HTTP must have its cryptographic signature checked before use.
- `vulnerabilities_fixed_60_days` (M) — no medium-or-higher vulnerability remains unpatched after more than 60 days of public knowledge. Check advisories and release history; a fix must be released, and a vulnerability need not have a CVE to be publicly known.
- `vulnerabilities_critical_fixed` (S) — none reported, or fixed timeline.
- `no_leaked_credentials` (M) — public repositories must not leak valid private credentials intended to restrict access. Ignore rules and secret scanning help prevent leaks; they do not by themselves establish that no credentials are exposed.

## Analysis

- `static_analysis` (M, N/A?, justification required either way) — CodeQL, ESLint/Semgrep, etc.; cite workflow URL and triggers. Compiler warnings and "safe"/strict language modes do not count here (they belong under `warnings`) — do not cite tsc strict/-Wall. The FLOSS mention is a conditional: the MUST binds only if a FLOSS analyzer exists for the language (so N/A is possible for niche languages); the tool actually used may be proprietary (CodeQL is fine). Note the release linkage: analysis on every push/PR + releases cut from the analyzed branch satisfies "applied before release".
- `static_analysis_common_vulnerabilities` (G, N/A?) — CodeQL security queries, bandit, brakeman. Dependency/SCA scanners (OSV-Scanner, Dependabot) examine manifests, not code — cite them under `vulnerabilities_fixed_60_days`, not here. OpenSSF Scorecard audits repo practices, not code — it is not static analysis evidence at all.
- `static_analysis_fixed` (M, N/A?) — fix confirmed, exploitable vulnerabilities of medium or higher severity found by static analysis in a timely way. Use the findings and remediation history.
- `static_analysis_often` (G, N/A?) — runs on every push/PR (+ schedule).
- `dynamic_analysis` (G) — apply a tool to each proposed major production release before release. It must execute the software and either vary inputs to look for problems (for example, fuzzing, a web scanner, or suitable property-based testing) or be an automated test suite with at least 80% **branch coverage**. The coverage route is an explicit alternative, not a static-analysis score or an exemption from running before release. Use the measured coverage and release practice; tool names, staging deployments, or production monitoring alone do not establish this. A security-specific focus is optional.
- `dynamic_analysis_unsafe` (G, N/A?) — if produced software includes memory-unsafe code, routinely combine dynamic analysis with a mechanism that detects memory-safety problems, such as ASAN, MemorySanitizer, valgrind, or suitable widespread assertions. The criterion prescribes N/A if no such memory-unsafe software is produced; use the project's language and native-code information.
- `dynamic_analysis_enable_assertions` (G) — use a configuration for at least some dynamic analysis, including testing or fuzzing, that enables many assertions. Describe the assertions enabled and the analysis that checks them; an assertion count in test files alone is not an automatic Met. Production assertion settings are a separate choice, and the details explain why disabling them there can be appropriate. Gold explicitly adds many runtime assertions in the produced software.
- `dynamic_analysis_fixed` (M, N/A?) — fix all confirmed medium-or-higher severity exploitable vulnerabilities found by dynamic analysis in a timely way. No dynamic analysis → N/A; qualifying analysis with no such findings can be Met, as can timely fixes of findings. Use the actual findings and response history; the details define severity using CVSS.

## Cryptographic scope

Start with the software the project produces and the mechanism each criterion addresses. Calling a cryptographic library remains use by that software: for example, password hashing delegated to a library can satisfy `crypto_call`, while the hashing and randomness requirements still apply. An independent hosting server that terminates HTTPS can put its TLS key agreement outside the application's own scope. The word “platform” alone does not settle this boundary; application calls to a runtime's cryptographic or TLS APIs remain relevant.

BadgeApp's bundled example illustrates the distinction. It records `Met` for delegated bcrypt password hashing and secure salt generation, but `N/A` for `crypto_pfs` because forward secrecy belongs to its external web server. It also records `N/A` for `crypto_keylength` in its password-hashing context; the exact criterion excludes password hashes from the 224-bit hash minimum. These are explanations of that application's answers, not defaults for other projects. Use each criterion's own scope, including inbound-user authentication for `crypto_password_storage`.
