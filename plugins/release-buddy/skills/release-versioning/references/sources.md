# Upstream sources for release versioning

Pages below were inspected on 2026-11-02. Read the relevant current page before giving exact configuration, commands, defaults, supported runtimes, or action versions. The links identify where to verify behavior; this file does not pin tool versions. If a page cannot be read, state which specifics remain unverified and avoid inventing them.

## Version policy and change descriptions

- [Semantic Versioning 2.0.0](https://semver.org/): public API compatibility, initial development, prerelease ordering, and version immutability.
- [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/): structured messages and breaking-change notation. A particular release tool's parser and configuration still determine its interpretation.
- [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/): curated entries, release sections, dates, and an `Unreleased` section.
- [Python versioning](https://packaging.python.org/en/latest/discussions/versioning/) and [version specifiers](https://packaging.python.org/en/latest/specifications/version-specifiers/): choosing a scheme and the syntax and comparison rules consumed by Python packaging tools.

## Tool selection and implementation

- [release-please](https://github.com/googleapis/release-please): commit-driven release PRs, supported release types, tags and GitHub releases, and separation from package publishing.
- [release-please manifest releaser](https://github.com/googleapis/release-please/blob/main/docs/manifest-releaser.md): package paths, initial versions, history boundaries, and manifest options.
- [release-please action](https://github.com/googleapis/release-please-action): workflow inputs, outputs, and integration with publication. Resolve the selected action version and its full commit SHA at implementation time.
- [Changesets getting started](https://changesets.dev/guide/getting-started) and [automation](https://changesets.dev/guide/automating): contributor-authored release intent, version PRs, publishing, and policy for changes needing no release.
- [Changesets fixed packages](https://changesets.dev/guide/fixed-packages), [linked packages](https://changesets.dev/guide/linked-packages), [prereleases](https://changesets.dev/guide/prereleases), and [beyond npm](https://changesets.dev/guide/beyond-npm): grouping semantics, prerelease constraints, and non-npm metadata requirements.
- [semantic-release introduction](https://semantic-release.org/intro/), [configuration](https://semantic-release.org/usage/configuration/), and [release workflow configuration](https://semantic-release.org/foundation/workflow-configuration/): commit-driven releases, plugin and tag configuration, dry-run behavior, branches, and distribution channels.
- [semantic-release changelog plugin](https://github.com/semantic-release/changelog): explicit changelog-file generation and its ordering relative to commit and publishing plugins.
- [npm version](https://docs.npmjs.com/cli/commands/npm-version/): manifest updates, Git commits and tags, and lifecycle scripts. The rendered page was unreadable during inspection; its [upstream documentation source](https://github.com/npm/cli/blob/latest/docs/lib/content/commands/npm-version.md) supplied those details.

## Monorepo strategy and tool semantics

These primary examples were inspected on 2026-11-02. Use them to verify a selected implementation, not as a requirement to adopt these products. Keep the strategy in [monorepos.md](monorepos.md) independent of tool-specific setting names.

- [Lerna versioning strategies](https://lerna.js.org/docs/features/version-and-publish#versioning-strategies): fixed versus independent modes and the distinction between a shared version line and synchronizing every package.
- [Nx release groups](https://nx.dev/docs/guides/nx-release/release-groups): group membership, fixed or independent relationships, group tag conventions, and dependent-package updates.
- [Rush publishing](https://rushjs.io/pages/maintainer/publishing/) and [version policies](https://rushjs.io/pages/configs/version-policies_json/): individual and lockstep policies, version preparation, and publication selection.
- For Changesets grouping behavior, use the fixed and linked package references above; do not assume their terms match another tool's.

## Ecosystem building blocks

- [setuptools-scm usage](https://setuptools-scm.readthedocs.io/latest/usage/): deriving Python package versions from source-control state and configuring tag formats.
- [Towncrier tutorial](https://towncrier.readthedocs.io/en/stable/tutorial.html): collecting and assembling news fragments.
- [Go module publication](https://go.dev/doc/modules/publishing): version tags and the relationship to module publication.
- [Cargo publication](https://doc.rust-lang.org/cargo/reference/publishing.html): crate metadata, packaging checks, and publishing new versions.

## Connecting release preparation to publication

- [GitHub token and workflow triggers](https://docs.github.com/en/actions/concepts/security/github_token): when events created with `GITHUB_TOKEN` do and do not start other workflow runs.
- [Triggering a workflow](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow): platform event behavior, dispatch exceptions, and approval behavior for bot-created pull requests; check separately from tag and release events.
- Use the existing [release-operations guidance](../../release-integrity/references/release-operations.md) for credential and event design, and its [upstream sources](../../release-integrity/references/sources.md#release-operations) before configuring those mechanisms. Those sources retain their own verification dates; listing the reference here does not assert a fresh check of every linked page.
