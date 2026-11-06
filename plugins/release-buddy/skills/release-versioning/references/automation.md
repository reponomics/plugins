# Implementing and maintaining release automation

Use this reference after choosing a process, or to investigate a concrete failure. Open the selected tool's current documentation in [sources.md](sources.md) for exact configuration and supported checks. Keep the work limited to the requested release behavior.

## Trace one release

Write the actual sequence in project terms before changing it. For example: merge a reviewed change, update a release PR, merge that PR, create a package tag, and publish that package. A different project may deliberately tag a manually chosen version or publish directly from its release branch.

Identify the actor and input at every step. Assign one owner to each version update, changelog update, tag, and publication. Multiple workflows may cooperate, but two must not independently decide or publish the same version. Check where tests gate the sequence and whether a manual approval controls preparation or publication.

## Connect preparation to publication

Inspect triggers, filters, workflow outputs, credentials, and checkout refs together. Confirm publishing builds the intended versioned revision and does not substitute a moving default branch after a tag has been selected. In monorepos, ensure the trigger selects the intended package set and package-specific versions.

For GitHub Actions, verify event behavior in the current [triggering documentation](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow). A tag or release created using `GITHUB_TOKEN` does not start another workflow through the corresponding event. Use a supported arrangement, such as publishing in the same workflow after release outputs are known, or a deliberate dispatch or suitable credential for a separate workflow. Do not install a GitHub App automatically when the existing workflow can complete the task.

Check bot-created release PRs separately from tag events using the [credential/event decision table](../../release-integrity/references/release-operations.md#choose-credentials-from-the-event-path) and its required platform-source check. Distinguish approval-required runs from events that do not start a run. Recommend a credential arrangement consistent with the desired review and automation behavior; do not describe an App-token plan as though it still uses `GITHUB_TOKEN` for those events.

For credential choices and draft/immutable release ordering, consult [release operations](../../release-integrity/references/release-operations.md). Read only the relevant material. For source or existing primary build artifacts distributed through public GitHub releases, use [release-integrity](../../release-integrity/SKILL.md) for signatures and verification. Registry publication is outside that skill’s setup scope: preserve the existing integration, identify missing registry requirements, and link the provider’s current documentation rather than supplying a new registry-publishing recipe.

Check reruns and overlapping releases. A retry should detect completed work and avoid allocating or publishing a conflicting version. Use concurrency appropriate to the release unit; avoid blindly canceling a job after publication may have started. Identify partially published packages before retrying. Do not delete or move published tags or reuse published versions as a recovery technique.

## Change an existing process

Establish the last actual release for each release unit using repository history and, where available, registry or hosted release records. A manifest version alone may represent an unreleased proposal. Inspect pending release PRs, unconsumed change files, and curated unreleased entries before migration.

Configure the new tool's documented bootstrap or release-history mechanism from that evidence. Preserve tag naming where consumers or CI depend on it. If a naming change is required, explicitly map the old release baseline and the new tag convention; do not manufacture a historical tag or move an existing one to satisfy a tool.

Account for outstanding release intent once: import or translate pending changes where supported, preserve curated migration notes, and ensure the first new release neither drops changes nor repeats all history. Replace the old release writer as part of the cutover. Do not leave two tools active against the same package while waiting to see which works.

Review the initial proposed version and notes before enabling publication. Preserve release protections and existing artifact guarantees. Update contributor instructions and the release guide with the new source of truth and next release action. When registry configuration or remote settings remain necessary, distinguish prepared repository changes from an operational hosted setup.

## Validate the result

Choose a proportionate local check from the tool's documentation: a release-plan preview, version operation in a disposable checkout, generated notes, or a representative manual release diff. Inspect configuration, lifecycle scripts, and plugins before running it. A dry-run name alone does not establish that no custom hook can write or contact a service; use an appropriate local environment without publishing authority.

For the behavior being changed, inspect:

- The release baseline and exact commits or change files included.
- The released package set, expected versions, generated metadata, and any internal dependency updates.
- Notes that explain the actual changes and preserve required migration information.
- Tag names and their intended revision, plus the event and credential connecting preparation to publishing.
- Intentional non-release changes, repeat execution, or prerelease promotion when those paths are affected.

Build locally where necessary to compare the package's version with the plan. Run the project's normal checks for changed files. Explain which evidence is local and which requires the next authorized hosted run. A parsed workflow or successful dry run does not prove registry permissions, branch protection, hosted event delivery, or publication.

## Diagnose before replacing

| Symptom                               | Inspect first                                                                                                                                       |
| ------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| No release proposed                   | Last recognized release, release branch, included paths/packages, final merged commit messages or pending change files, and explicit skip rules.    |
| Unexpected bump                       | Public compatibility impact versus declared input, `0.x` configuration, custom release rules, prerelease state, and dependency propagation.         |
| Missing or duplicated notes           | Source release range, filtered commit types, consumed change files, competing changelog writers, and a migrated baseline.                           |
| Tag exists but publishing did not run | Token used to create the event, event type, tag/branch filters, draft-release state, and workflow availability.                                     |
| Package version differs from tag      | Actual build checkout, generated versus authoritative version fields, tag parsing, history available to a dynamic backend, and stale build outputs. |
| Rerun tries to publish again          | Existing package/release state, retry detection, overlapping runs, and whether preparation and publication have different completion states.        |

Use logs and repository evidence to identify the failing transition. Repair the smallest cause that restores the agreed policy. Do not change ecosystems, replace working tooling, weaken protections, or rewrite release history to avoid diagnosing a configuration error.
