# OpenSSF Security Baseline

## Scope

Use `baseline-1`, `baseline-2`, or `baseline-3`. These sections contain 24, 19, and 21 criteria respectively. Maturity levels are cumulative: Level 1 requires 24 criteria, Level 2 requires 43 across the first two sections, and Level 3 requires all 64. A completed higher section alone does not establish that maturity level. `[L1]`, `[L2]`, and `[L3]` below identify the section containing each control.

Every control is mandatory and permits `N/A` with a written justification when its triggering condition is absent. Recommendations in a control's details remain recommendations.

Use lowercase underscore IDs such as `osps_ac_01_01` in application fields. The public API may return display IDs such as `OSPS-AC-01.01`; the controller handles that mapping during synchronization.

## AC — Access Control (organization and repository settings)

- `osps_ac_01_01` [L1] — MFA required to read/modify sensitive resources in the authoritative repo; passkeys are accepted. Use the user's account of the relevant settings. BadgeApp's GitHub-based suggestion does not query private MFA settings or establish the configuration of other hosts used by the project; ask about those settings when they affect the answer.
- `osps_ac_02_01` [L1] — new collaborators get manual permission assignment or the lowest available privileges by default. These are alternatives: manual assignment need not grant the lowest role. Use the project's described invitation and role-assignment process.
- `osps_ac_03_01` [L1] — an enforcement mechanism prevents direct commits to the primary branch. GitHub branch-protection settings or rulesets can describe this enforcement. The details also accept a decentralized arrangement where changes are proposed in another repository and merging into the authoritative repository requires a separate act. If branch protection is absent and the arrangement is unknown, ask how direct commits are prevented; a voluntary practice alone does not provide the required enforcement.
- `osps_ac_03_02` [L1] — attempts to delete the primary branch require explicit confirmation of intent. The details recommend preventing deletion through branch protection; protection is an implementation option, not a separate MUST.
- `osps_ac_04_01` [L2] — CI/CD tasks with no permissions specified default to the lowest granted in the pipeline. Evidence: top-level `permissions:` blocks in workflows, or the org/repo default workflow token set to read-only (the default is an organization or repository setting; workflow permissions are in the repository files).
- `osps_ac_04_02` [L3] — permissions assigned to a CI/CD job are limited to what its activity needs. A read-only default plus job-level elevation is a useful GitHub Actions pattern; account for inherited workflow, repository, or organization settings as well as explicit job settings.

## BR — Build & Release (workflows + releases)

- `osps_br_01_01` [L1] — when pipelines use untrusted metadata, it must be sanitized and validated before use. Direct `${{ github.event.* }}` interpolation inside `run:` scripts is a common hazard. For inline shell scripts, pass metadata through environment variables, quote expansions, validate values for their intended use (including any required restricted form), and avoid evaluating them as code. The variable alone is insufficient. When helping fix an unsafe workflow, use [GitHub's script-injection guidance](https://docs.github.com/en/actions/reference/security/secure-use#good-practices-for-mitigating-script-injection-attacks) to choose a suitable mitigation.
- `osps_br_01_03` [L1] — when pipelines operate on untrusted code snapshots, that code cannot reach privileged CI/CD credentials or assets. Look for `pull_request_target` jobs that execute unreviewed PR code, and credentials or assets exposed to fork-triggered workflows.
- `osps_br_01_04` [L3] — trusted collaborator input (e.g. `workflow_dispatch` inputs) is sanitized and validated too.
- `osps_br_02_01` [L2] — every official release has a unique version identifier (SemVer, CalVer, or commit id). Evidence: releases and tags pages.
- `osps_br_02_02` [L3] — every asset in an official release is clearly associated with the release identifier or its own unique identifier.
- `osps_br_03_01` [L1] — official project channel URIs are delivered exclusively over encrypted channels. Check the listed URLs and search documentation for `http://`.
- `osps_br_03_02` [L1] — official distribution channels resist adversary-in-the-middle: HTTPS downloads, signed releases, or a trusted package manager.
- `osps_br_04_01` [L2] — official releases carry a descriptive log of functional and security changes. Release notes or a CHANGELOG can supply it; generated notes need the relevant content too.
- `osps_br_05_01` [L2] — when build/release pipelines ingest dependencies, they use standardized tooling where available. A package manager or dependency-management tool is a typical choice; dependency files, manifests, and lockfiles are possible inputs, not an additional requirement to use all three.
- `osps_br_06_01` [L2] — official releases are signed or covered by a signed manifest containing each asset's cryptographic hash. Signatures or signed attestations such as GPG, Sigstore, or SLSA provenance must cover the released assets; identify that coverage in publish workflows or release metadata.
- `osps_br_07_01` [L1] — prevent unintentional storage of unencrypted sensitive data in the VCS. Ignoring sensitive files, pre-commit scanning, and push protection are possible measures; a `.gitignore` entry alone does not cover other ways a secret may be committed.
- `osps_br_07_02` [L3] — define a policy for managing project secrets and credentials. Guidance on storage, access, and rotation is recommended policy content. Help document the project's actual practices if needed.

## DO — Documentation (repo files)

- `osps_do_01_01` [L1] — user guides for all basic functionality once a release exists (install, configure, use; visible warnings for dangerous actions). README plus docs/.
- `osps_do_02_01` [L1] — once the project has made a release, document how to report defects, for example in README or CONTRIBUTING. Triage and resolution expectations are recommended, not an additional MUST.
- `osps_do_03_01` [L3] — once a release exists, document how to verify the integrity and authenticity of its assets. The details recommend identifying the technology, commands, and expected output.
- `osps_do_03_02` [L3] — once a release exists, document how to verify the expected identity of the person or process authoring it (signing key IDs, Sigstore issuer/identity).
- `osps_do_04_01` [L3] — once a release exists, state the scope and duration of support per release (SUPPORT.md or a Support section in SECURITY.md).
- `osps_do_05_01` [L3] — once a release exists, state when releases or versions stop receiving security updates.
- `osps_do_06_01` [L2] — once a release exists, document how the project selects, obtains, and tracks its dependencies.
- `osps_do_07_01` [L2] — build instructions including required libraries, frameworks, SDKs (CONTRIBUTING or documented make targets).

When documentation is missing, offer to help write it using the project's actual practices.

## GV — Governance (documented roles and practices)

- `osps_gv_02_01` [L1] — public mechanism for discussing proposed changes and usage obstacles (issues, discussions, mailing list).
- `osps_gv_03_01` [L1] — document the contribution process, or clearly state that public contributions are not accepted. CONTRIBUTING.md is a suitable location.
- `osps_gv_01_01` [L2] — documented list of members with access to sensitive resources (MAINTAINERS, governance.md; names or handles suffice for a small project).
- `osps_gv_01_02` [L2] — documented roles and responsibilities for project members.
- `osps_gv_03_02` [L2] — contributor guide states requirements for acceptable contributions (coding standards, testing, submission).
- `osps_gv_04_01` [L3] — documented policy that code collaborators are reviewed before they receive escalated permissions to sensitive resources.

A single maintainer can document project roles, access, and decision-making. Additional people are required only where a control says so; the non-author approval in `osps_qa_07_01` can come from a reviewer who is not another maintainer. Use `N/A` when the control's own triggering condition is absent.

## LE — Legal (license files)

- `osps_le_02_01` [L1] — source-code license meets the OSI Open Source Definition or FSF Free Software Definition (MIT, BSD, Apache-2.0, LGPL, GPL all qualify). The details also accept public-domain release if no other encumbrances, such as patents, remain.
- `osps_le_02_02` [L1] — the released software assets' license meets the same definitions; it may differ from the source-code license.
- `osps_le_03_01` [L1] — license maintained in the repo's LICENSE file, COPYING file, LICENSES/ directory, or LICENSE/ directory (every repo, if there are several). A filename extension is allowed.
- `osps_le_03_02` [L1] — license included in released source or alongside release assets — an npm tarball or container image may need the license file added; check the package build.
- `osps_le_01_01` [L2] — every commit asserts the contributor is legally authorized: DCO with a status check, or a CLA; the official details note that some platforms' terms of service (e.g. GitHub's) may cover this. The released Baseline guidance also recognizes that projects with a long history before adopting Baseline may be unable to enforce this retroactively. BadgeApp omits that qualification; account for it when explaining the project's current practice and earlier contributions.

## QA — Quality Assurance (repo + CI)

- `osps_qa_01_01` [L1] — repo publicly readable at a static URL.
- `osps_qa_01_02` [L1] — public record of all changes, their authors, and dates; avoid history rewriting that obscures authorship.
- `osps_qa_02_01` [L1] — when the package management system supports it, list direct language dependencies (package.json, go.mod, pyproject.toml, Gemfile).
- `osps_qa_04_01` [L1] — multi-repo projects document their codebase list; for a single-repo project the triggering condition is absent — `N/A` with that justification.
- `osps_qa_05_01` [L1] — no generated executable artifacts in the VCS (generate at build time or fetch in a documented pipeline step).
- `osps_qa_05_02` [L1] — no unreviewable binary artifacts in the VCS (images, sound, and similar media are explicitly fine).
- `osps_qa_03_01` [L2] — automated status checks must pass (or be manually bypassed) before merging to the primary branch. Rulesets / required-checks evidence.
- `osps_qa_06_01` [L2] — CI runs at least one automated test suite before a commit is accepted. The details recommend contributor-visible results, a consistent environment, and a way to run tests locally. Having a suite alone does not establish when CI runs it.
- `osps_qa_02_02` [L3] — once a release exists, all compiled released assets ship with an SBOM. Generating SPDX/CycloneDX in CI is an option; the requirement is limited to compiled assets.
- `osps_qa_04_02` [L3] — subprojects in a multi-repo release enforce security requirements as strict as the primary codebase; single-repo releases lack the triggering condition.
- `osps_qa_06_02` [L3] — clearly document when and how tests run. The details recommend explaining local and CI execution, what the tests cover, and how to read results.
- `osps_qa_06_03` [L3] — documentation MUST include a policy that all major changes should add or update automated tests. The details recommend explaining what constitutes a major change and the relevant tests; a brief policy can suffice if it covers the project's practice.
- `osps_qa_07_01` [L3] — the VCS requires at least one non-author human approval before each primary-branch merge. One maintainer can use another human reviewer; record `Unmet` when the required approval or enforcement is absent. When reusing a Gold `two_person_review` answer, use the [Metal comparison](#related-metal-criteria) to account for Baseline's different threshold and timing.

## SA — Security Assessment (docs + practice; L2/L3)

- `osps_sa_01_01` [L2] — once a release exists, design documentation covers all actions and actors within the system, including subsystems or entities that influence another segment. Keep it current with new features or breaking changes.
- `osps_sa_02_01` [L2] — once a release exists, describe all external software interfaces of the released assets, including expected and produced data (API reference).
- `osps_sa_03_01` [L2] — once a release exists, perform a security assessment of the most likely and impactful potential problems. The details call for updating it for new features or breaking changes.
- `osps_sa_03_02` [L3] — once a release exists, perform threat modeling and attack-surface analysis covering critical code paths, functions, and interactions. If needed, offer to help perform and document this work with the user; keep it current with new features or breaking changes.

## VM — Vulnerability Management (SECURITY.md + trackers)

- `osps_vm_02_01` [L1] — security contacts published (SECURITY.md or similarly named file).
- `osps_vm_01_01` [L2] — publish a coordinated vulnerability disclosure policy with a clear response timeframe. The policy is required even if no vulnerability reports have arrived.
- `osps_vm_03_01` [L2] — document a private vulnerability reporting channel that reaches the project's security contacts (GitHub Private Vulnerability Reporting, a security email, or another private method).
- `osps_vm_04_01` [L2] — publicly publish data about discovered vulnerabilities. A predictable channel such as advisories, CVEs, or a blog helps users find it; affected versions, ways to identify exposure, and remediation guidance are recommended to the degree possible.
- `osps_vm_04_02` [L3] — when vulnerabilities in software components do not affect the project, account for them in a VEX document with non-exploitability details; a VEX feed is one approach.
- `osps_vm_05_01` [L3] — documented remediation threshold for SCA findings (vulnerabilities and licenses).
- `osps_vm_05_02` [L3] — document a policy to address SCA violations before any release. The details describe status checks to verify compliance; `osps_vm_05_03` separately requires automatic evaluation and blocking.
- `osps_vm_05_03` [L3] — automatically evaluate every codebase change against a documented policy for malicious dependencies and known dependency vulnerabilities; block violations unless declared and suppressed as non-exploitable (required status check running SCA).
- `osps_vm_06_01` [L3] — documented remediation threshold for SAST findings.
- `osps_vm_06_02` [L3] — automatically evaluate every codebase change against a documented policy for security weaknesses; block violations unless declared and suppressed as non-exploitable (required SAST status check).

Reuse the project's existing security contacts, reporting channels, and policy URLs across related criteria. Explain any additional condition instead of automatically copying a status.

## Related Metal criteria

When reusing an existing Metal answer, read the matching row to identify the additional condition Baseline requires. Reuse relevant facts and URLs without assuming the status carries over:

| Related criteria | Additional distinction to resolve |
| --- | --- |
| Passing `vulnerability_report_response` → Baseline `osps_vm_01_01` | Passing requires initial responses within 14 days for reports received in the last six months, and allows `N/A` if there were none. Baseline requires a published CVD policy with a clear response timeframe regardless of report history; it does not prescribe that Passing timeframe. Reuse the reporting information and ask only for the policy commitment if it is missing. |
| Gold `two_person_review` → Baseline `osps_qa_07_01` | Gold requires another person's review of at least 50% of proposed modifications before release, assessing their suitability and known issues. Baseline requires VCS-enforced non-author human approval before every primary-branch merge. A Gold `Met` answer alone establishes neither Baseline's coverage nor its enforcement. |
| Passing `test` → Baseline `osps_qa_06_01` | Passing requires a publicly released automated FLOSS test suite and clear instructions or configuration for running it. Baseline requires CI to execute a suite before accepting a commit; its details also recommend contributor-visible results. Reuse the suite description and ask only about missing CI details, preserving that distinction in requirement strength. |
