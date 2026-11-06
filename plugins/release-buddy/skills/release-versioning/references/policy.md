# Version and changelog policy

Use this reference for decisions about compatibility, authoritative versions, release units, and notes. Consult the relevant specifications in [sources.md](sources.md) before translating the policy into tool configuration.

## Define what a version communicates

Identify the public contract that matters to consumers: library interfaces, CLI flags and exit behavior, configuration formats, file formats, or documented behavior. Read the change itself when deciding its compatibility; a commit label is release input, not proof that a change is compatible.

Apply the project's documented compatibility policy and select the highest required increment across the release's changes. Explain the selected bump and its consequence for consumers when useful; preserve a working policy.

Do not treat `0.x` as a universal bump algorithm. SemVer permits instability during initial development, but projects and tools differ in how they communicate breaking changes there. Record the project's convention and test the selected tool's configuration against it. Base a move to 1.0 on the maintainer's intended compatibility commitment, not project age or the presence of CI.

For date-based or ecosystem-specific schemes, explain what the version does and does not promise about compatibility. Do not migrate to SemVer merely because a release tool prefers it. Separate policy from syntax: Python distribution versions follow the packaging specification, and a Git tag prefix is not automatically part of the distribution version. Use the ecosystem's parser and installed build backend to verify accepted versions.

## Preserve one authoritative source

Trace the value from its source to the built artifact. A project may derive its version from a tag, store it in a manifest, or generate runtime metadata during a build. Multiple files can contain the version without being independently editable sources.

Determine which process updates the source and which regenerates dependent files, lockfiles, or metadata. Avoid adding a manifest bumper to a project whose backend derives versions from tags unless the user is intentionally migrating that design. For dynamic versions, check the intended checkout's tags and history and inspect the built package's actual version; a clean manifest alone cannot establish it.

Distinguish a package version, its source tag, and a registry channel label. A tag such as `widget-v1.4.3` may identify package `widget` version `1.4.3`; a channel name such as `next` selects an audience. Record the mapping, including package prefixes, instead of applying one pattern to every repository.

## Choose release units

Use [monorepo strategies](monorepos.md) to choose shared versions, independent versions, or coordinated groups from consumers' upgrade needs. Treat version relationships, release cadence, and publication selection as separate decisions. That reference covers dependency propagation, private-package effects, release baselines, and validation; do not infer the policy solely from a workspace layout or tool name.

## Prereleases and maintenance lines

Distinguish a prerelease version from a hosted release marked prerelease and from a registry distribution channel. Decide the intended base version, counter, branch, and destination before configuring automation. Check what default installers will resolve so preview builds do not accidentally replace the stable channel.

Use ecosystem syntax: for example, SemVer `2.0.0-rc.1` and Python `2.0.0rc1` are different spellings. Verify the tool's prerelease exit or promotion behavior; do not assume removing a suffix or merging a branch produces the intended stable version. Promotion can require a newly versioned build, which must retain the expected publication guarantees.

Only introduce a maintenance branch when the project intends to support it. For backports, establish which line receives the fix, its latest released version, and the tool's branch/channel configuration. Test that a backport neither advances the main line unexpectedly nor republishes a version already used. Preserve existing published versions and tags; fix incorrect releases with a new version rather than moving history.

## Make the release record useful

Choose a repository changelog, hosted release notes, or both from the audience's needs. When both are maintained, designate the source and generation direction so two automations do not overwrite each other's edits. Distinguish release-note generation from committing a changelog file; check the selected tool's outputs explicitly.

Use contributor change files or structured commits as inputs to reviewed prose. Explain the user-visible effect, breaking changes, and migration steps; do not use a raw commit dump as the final record. Keep internal refactors out unless they affect users or maintainers in a way the release record needs to communicate. Never invent unreleased changes or expose confidential security details in public notes.

For curated changelogs, an `Unreleased` section can collect forthcoming changes and become a dated version section at release. Use actual release dates and versions, and preserve accurate historical entries. When repairing history, use tags, releases, and diffs as evidence; mark gaps instead of presenting reconstructed guesses as facts.

Explain how contributors provide the selected input and how maintainers review it. With commit-driven tools, check the final merge message and breaking-change notation. With change files, review affected packages and bump types alongside the summary. Permit intentional non-release changes according to the project's policy rather than demanding a bump for every edit.
