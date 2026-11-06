# Choosing a versioning workflow

Use this reference when a maintainer wants to select or change the release process. Start with the existing process and the desired improvement. Keep a working setup when the problem can be solved by clarifying its policy or fixing its configuration. For a narrow question about one tool, read only that tool's section and upstream documentation.

## Make the decision from the work maintainers want to do

Establish these facts from the repository and conversation; ask only about unresolved choices that change the recommendation:

1. **Release timing:** whether maintainers want to approve a prepared release, publish automatically after qualifying changes merge, or choose occasional release dates themselves.
2. **Release intent:** whether maintainers will review structured commit messages, contributor-written change files, or a curated changelog. Inspect the messages that actually reach the release branch, including squash merges.
3. **Version ownership:** whether the version lives in a manifest, comes from a tag at build time, or is generated elsewhere. Determine which packages share a version and which release independently.
4. **Ecosystem fit:** whether the proposed tool understands the real version files, dependency relationships, build system, and hosting platform. Account for any extra runtime or metadata it introduces.

Recommend one fitting approach and explain its main cost in the maintainer's terms. Include an alternative when it resolves a real tradeoff, or a broader comparison when requested. Do not present every tool merely because it appears here. Choosing no new release tool is a valid outcome.

| Approach | Consider when | Maintainer obligation |
| --- | --- | --- |
| Manual version choice with CI publishing | Releases are occasional, a curated changelog already works, or automation would add more upkeep than it removes. | Choose the version, review the prepared changes, and deliberately trigger publication. |
| release-please | Structured commit messages are acceptable and maintainers want a release PR before publication. | Review release PRs and ensure merged commit messages preserve release intent. |
| Changesets | Contributors should specify affected packages, bump types, and user-facing summaries alongside code. | Review changeset files and package relationships, then approve or automate versioning and publication. |
| semantic-release | Qualifying merges should release automatically and the team accepts commit-driven version decisions. | Review release intent before merge and maintain branch, plugin, and publishing configuration. |
| Existing ecosystem tools | The build system already derives versions or the missing capability is only changelog assembly. | Maintain the existing source of truth and add only the missing step. |

The table is selection guidance, not a compatibility guarantee. Open the relevant [upstream sources](sources.md) before selecting configuration, plugins, or commands.

For a monorepo, establish the [versioning strategy](monorepos.md) before choosing a tool: shared or independent numbers, coordinated groups, release cadence, and which packages publish. Then check that the selected implementation supports the agreed dependency and publication behavior. Do not derive the strategy from a product's terminology or adopt a new workspace framework merely to obtain release tooling.

## Manual version choice with CI publishing

Separate the human decision from repeatable execution. Prepare the version and user-facing notes in a PR, run the project's checks, and use one deliberate trigger to publish the reviewed commit. Where the build derives versions from tags, preserve that mechanism instead of adding a competing version file. State who creates the tag and how it identifies the tested commit.

Keep a Changelog provides a useful pattern for accumulating an `Unreleased` section and turning it into a dated release section. Treat its categories as a way to help readers find changes, not a requirement to populate empty headings. [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)

Check the side effects of any version command before using it. For example, `npm version` can create a commit and tag and run lifecycle scripts; it is not necessarily a file-only edit. Inspect project hooks and the installed tool's documented behavior. [npm version](https://docs.npmjs.com/cli/commands/npm-version/)

## release-please

Use release-please to prepare version and changelog updates in release PRs from Conventional Commits. Its release flow creates tags and GitHub releases; package publication requires separate integration. Confirm the supported release type for the project's language and version files. [release-please](https://github.com/googleapis/release-please)

With squash merges, release-please processes the resulting commit on the release branch, not the original branch commits individually. A `fix!:` on a branch commit does not by itself cause a breaking-release bump if that message is discarded during squashing; do not recommend rewriting branch commits solely to change release-please output. Inspect the final squash message, including its body: breaking-change footers or additional Conventional Commit entries carried into that message can still affect the release. Ensure actual breaking changes are represented there. [Squash merges and multiple changes in one commit](https://github.com/googleapis/release-please#linear-git-commit-history-use-squash-merge)

For a monorepo, inspect manifest configuration, package paths, dependency handling, and whether releases should share a PR. During adoption, establish the actual last released versions and history boundary so the first generated PR does not infer an unintended starting point. Read the selected strategy's behavior instead of assuming all language strategies update the same files. [Manifest releaser](https://github.com/googleapis/release-please/blob/main/docs/manifest-releaser.md)

Explain which merge authorizes a release and what runs afterward. Check that its publication integration responds to a release actually being created, not every run that merely updates the release PR. Use [automation.md](automation.md) to trace credentials, events, and publishing ownership.

## Changesets

Use Changesets when explicit release intent belongs in the contribution itself: a small file names affected packages, bump types, and a summary. Distinguish adding a changeset, applying version changes, and publishing. Contributors need not run the release step to describe their change. [Getting started](https://changesets.dev/guide/getting-started)

Choose whether version changes are reviewed in a maintained PR and how publication follows. Decide how to handle changes that need no release; avoid introducing a mandatory changeset gate without checking the project's preference. [Automation](https://changesets.dev/guide/automating)

For monorepos, decide between independent versions, fixed groups that release together, and linked groups whose releasing members align versions without necessarily publishing every member. Inspect dependent-package effects in a preview rather than assuming only explicitly listed packages change. [Fixed packages](https://changesets.dev/guide/fixed-packages), [linked packages](https://changesets.dev/guide/linked-packages)

Changesets is especially natural for npm-style workspaces, but it can manage non-npm projects through `package.json` metadata. Explain that extra metadata and the publication integration before proposing it for a Python, Rust, or other project. Prefer an existing native version source when an adapter would create competing authorities. [Beyond npm](https://changesets.dev/guide/beyond-npm)

## semantic-release

Use semantic-release when the intended contract is that qualifying commits on a configured release branch can publish automatically after CI succeeds. Explain this before replacing a manually approved release process. Its configured plugins analyze commits, generate notes, and perform publication tasks. [Introduction](https://semantic-release.org/intro/)

Inspect the actual commit analyzer, plugin order, tag format, and existing release tags. A package version prepared during a build does not imply a version-file commit to the repository. A committed changelog likewise needs explicit generation and commit configuration; do not add that complexity when hosted release notes meet the user's requirement. [Configuration](https://semantic-release.org/usage/configuration/), [changelog plugin](https://github.com/semantic-release/changelog)

For maintenance or prerelease lines, configure the relationship between branches, supported version ranges, and distribution channels deliberately. Do not infer that a branch called `beta` automatically implements the project's intended policy. For independently released packages, verify the selected integration's package and dependency behavior rather than equating multiple release branches with monorepo support. [Release workflow configuration](https://semantic-release.org/foundation/workflow-configuration/)

## Ecosystem tools and smaller combinations

Keep version selection, changelog assembly, and publication conceptually separate even if one tool performs all three. A project may need only one missing capability:

- **Python:** preserve a working tag-derived version setup such as setuptools-scm. Consider Towncrier when contributor-written fragments would improve release notes; it does not by itself decide and publish package versions. Confirm Python version syntax separately from a SemVer policy. [setuptools-scm](https://setuptools-scm.readthedocs.io/latest/usage/), [Towncrier](https://towncrier.readthedocs.io/en/stable/tutorial.html), [Python versioning](https://packaging.python.org/en/latest/discussions/versioning/)
- **Go:** start from module paths and version tags. Check major-version and module-subdirectory rules before introducing a general release tool. [Publishing a module](https://go.dev/doc/modules/publishing)
- **Rust:** start from Cargo manifests, workspace dependency relationships, and the existing release commands. Determine which version and changelog steps are missing before adding another runtime or duplicate manifest. [Cargo publishing](https://doc.rust-lang.org/cargo/reference/publishing.html)

These are examples of preserving ecosystem conventions, not a mandatory list of tools to offer. Apply [policy.md](policy.md) to the chosen version scheme and [automation.md](automation.md) to implementation, migration, and validation.
