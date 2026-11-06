# Scorecard remediation leads

Use the result's reason, details, and version-specific upstream documentation to identify the problem before proposing an edit. These are practical investigation leads, not a scoring specification or a checklist to apply to every repository. Work within the selected scope and verify relevant local behavior; a later published scan establishes any score effect.

Explain the concrete benefit, effort, and verification path. Distinguish risk reduction, maintenance improvements, and changes that only help a detector recognize an existing practice. Never substitute an unused tool, an empty test, or a false policy for an operating practice. Choose work for its relevance to the repository, not a projected numerical lift.

## Workflow permissions and dependency pins

For `Token-Permissions`, action pinning within `Pinned-Dependencies`, and workflow dependency updates within `Dependency-Update-Tool`, use [GitHub workflow maintenance](../../github-workflow-maintenance/SKILL.md). Carry selected files and accepted scope into that procedure. Preserve required reads and put justified writes on the jobs that need them. Pinning and upgrading are distinct changes; integrate existing Dependabot or Renovate configuration rather than adding a redundant updater.

Investigate non-action dependencies separately when reported: container digests, installer verification, and application package updates need their own validation. Pinning every action alone does not establish that all dependency findings are resolved. Explain who will review and merge update proposals; configuring a bot does not establish ongoing maintenance.

## Dangerous workflows

Investigate untrusted values interpolated into shell source and untrusted code executed with privileged credentials. Pass untrusted text through an environment variable and quote its shell expansion, for example:

```yaml
- env:
    TITLE: ${{ github.event.issue.title }}
  run: |
    printf 'Title: %s\n' "$TITLE"
```

For privileged events such as `pull_request_target` or `workflow_run`, inspect checkout revisions, token permissions, secret exposure, and artifact handling together. Separate untrusted builds from privileged operations. Artifacts from untrusted runs remain untrusted; moving payloads between workflows does not make them safe to execute. Validate the affected workflow without launching publishing or deployment jobs merely as tests.

## Policies, licenses, and repository contents

A useful `SECURITY.md` explains supported versions, a working private reporting channel, what a reporter should include, and the maintainer's actual response process. Confirm commitments with the maintainer rather than inventing guarantees or adding text solely to satisfy a detector.

For `License`, preserve the project's actual chosen license, conventional file placement, and applicable package metadata. Do not change licensing merely to improve detection. For `Binary-Artifacts`, investigate why the reported file is tracked and whether a reproducible build or verified download can replace it. Necessary fixtures and distribution constraints require a considered decision, not automatic deletion.

## Branch controls and review practices

Inspect the actual default/release branch rules, required checks, bypasses, and permissions available to the measuring token. Explain the impact of blocking direct pushes, requiring reviews, or requiring status checks before changing settings. Policies must fit the available maintainers and CI; do not introduce a rule that prevents the project from merging or releasing.

A check's inability to read a setting is different from that setting being absent. Read [Action credentials](authentication-and-results.md#action-credentials) before requesting extra access. `Code-Review` and `CI-Tests` can depend on observed history; configuration changes need subsequent real development activity before a scanner can observe them.

## Analysis and vulnerabilities

For `SAST`, choose a supported analyzer appropriate to the project's languages and existing CI, then verify it actually runs on the intended changes. For `Fuzzing`, exercise a real parser, decoder, or other untrusted-input boundary and demonstrate that the target runs meaningfully.

For `Vulnerabilities`, inspect the identified advisory and dependency path, implement a compatible fix, and test the affected behavior. If the project believes an advisory does not apply, document the concrete basis and consult the measured version's upstream suppression guidance. Never add an ignore solely to remove a reported finding. External advisory updates can affect the next scan independently of local changes.

## Packaging and releases

For `Packaging` and `Signed-Releases`, investigate the actual build, publication, signature, and provenance process. Prefer automation that consumers can verify and maintainers can operate. Release configuration is preparation; a real release and its artifacts are evidence. Do not publish a release as a test without authorization, and do not promise immediate score movement when a check observes release history.

## Historical and external conditions

`Maintained` and `Contributors` reflect activity and contributor history. Explain the supported cause of a result; do not manufacture commits or affiliations to influence it. Other checks may depend on external services, token visibility, or repository history. Confirm those constraints in upstream documentation before attributing a result to a missing configuration file.

For `CII-Best-Practices`, invoke `badge-buddy:ossf-bp-badges` (the [Best Practices entrypoint](../../ossf-bp-badges/SKILL.md)) to resolve its invocation context and support honest progress in the separate badge program. For publication or badge setup, follow [action-publication.md](action-publication.md) and verify the resulting API record.
