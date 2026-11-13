# Release a plugin

**Merge a version and its notes, review the checks, then approve publication in GitHub.** Each plugin releases independently; the marketplace has no version. Complete the one-time [repository setup](repo-setup.md#prepare-the-release-repository) first.

## 1. Choose the version in a PR

Edit `plugins/<plugin>/.claude-plugin/plugin.json` and add `docs/release-notes/<plugin>/<version>.md`. [Write the notes for someone deciding whether to update](release-notes/README.md). Ordinary development work can merge without a bump. For a plugin with no release tags, add its initial reviewed notes in the PR that should release it; its manifest version may stay unchanged. Once the plugin has release tags, version changes must increase its semantic version. A prerelease suffix produces a GitHub prerelease.

Run `make check`. To preview the version changes in your committed PR, run `make release-plan RELEASE_BASE=origin/main` in a full clone with current remote refs. Merge once the required checks pass.

## 2. Review and approve in GitHub

The push to `main` starts the **release** workflow. It plans releases from that push, runs `make check`, and scans dependencies at the exact pushed commit (`github.sha`). Publication waits for `hesreallyhim` to approve the `release` environment. Review the commit, planned versions, reviewed notes, and scan evidence in that run before approving.

| File               | What to review                                                       |
| ------------------ | -------------------------------------------------------------------- |
| `scan-scope.md`    | Commit, date, scanner version, platform, package count, and outcome. |
| `osv-results.json` | Package inventory and any advisory IDs.                              |

The scan checks **maintainer tooling**: the root npm lockfile and the Python dependencies resolved from `requirements-dev.txt`, including transitive wheels for the scan platform. It does not scan plugin instructions, workflow behavior, or software installed by users. A clean result means no known advisories were reported for that inventory at that time. A finding or an incomplete scan blocks publication. The same scan also runs weekly on the default branch.

Badge Buddy's live criteria comparison is separate, advisory maintenance. Website drift or an unavailable website does not block a release; [investigate it through criteria maintenance](criteria-maintenance.md).

After approval, the workflow creates each lightweight tag, such as `release-buddy--v0.1.0`, at the same checked commit, attaches the evidence, publishes the immutable GitHub Release, and verifies its release attestation and assets. This process uses GitHub's environment approval and release attestation; it does not require a personal SSH signing key, a manually pushed tag, a workflow dispatch, or local finalization. Repository writers are trusted: they can also publish directly, so the environment approval governs this workflow rather than every route to publication. Follow [consumer verification](../VERIFYING.md) from a separate checkout after the first release.

## If a run stops

For a transient failure, rerun the original workflow run. Its commit remains the original `github.sha` even if `main` has advanced. A dependency fix belongs in a PR; review the resulting new run before approving publication. To investigate a scan locally, use the OSV-Scanner version pinned in [the scan helper](../tools/scan_dependencies.py) and run `make dependency-scan`; evidence is written to `.cache/dependency-scan/`. Local dependency resolution may differ from Linux CI.

A retry verifies the original tag, commit, immutable attestation, and attached evidence of an already published release without rewriting it. Later edits to its displayed title, notes, or prerelease label do not invalidate that retry; the reviewed source notes remain in Git. New publication strictly checks the title, notes, prerelease status, and evidence before publishing.

If a partial draft exists, keep it unpublished and inspect its tag, ownership, files, and digests. Retain its evidence before deliberately removing only that unpublished draft and retrying the original run. Tags without a published immutable release may be corrected or deleted after inspecting the intended commit and retaining relevant evidence; do not overwrite unknown draft assets. Publishing an immutable release locks its associated tag and assets while that release exists. Correct a bad published release with a new version.

Release immutability must remain enabled in repository or organization settings. The workflow's token cannot read that administration setting; verification after publication detects a missing immutable attestation but cannot undo a mutable release that has already been published. See the [setup prerequisite](repo-setup.md#prepare-the-release-repository).
