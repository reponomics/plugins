# Release a plugin

**Bump the manifest, sign the merged commit, then publish the checked draft.** The bump selects a new plugin version. The signed tag identifies its exact source. The immutable GitHub Release preserves the tag and the dependency-scan evidence. Each plugin releases independently; the marketplace has no version.

Complete [repository and signer setup](repo-setup.md#authorize-release-signers) before releasing from a repository.

## 1. Choose the version in a PR

Edit `plugins/<plugin>/.claude-plugin/plugin.json` and add `docs/release-notes/<plugin>/<version>.md`. [Write the notes for someone deciding whether to update](release-notes/README.md). You can merge ordinary development work without a bump. For a plugin with no release tags in the target repository, choose its initial version; if the manifest version stays unchanged, add its first reviewed notes in the PR you intend to tag. Once the plugin has release tags, version changes must increase its semantic version. A prerelease suffix produces a GitHub prerelease.

Run `make check`. To preview the version changes in your committed PR, run `make release-plan RELEASE_BASE=origin/main` in a full clone with current remote refs. Merge once the checks pass. Record the **full merged commit SHA from that PR**; later work on main does not belong to this release.

## 2. Sign the release tag

From a trusted clone of the target repository, set the values below. For example, a Release Buddy version of `0.1.0` would give `release-buddy--v0.1.0`. Use your chosen version.

```sh
REPO=OWNER/REPOSITORY
PLUGIN=release-buddy
VERSION=YOUR_CHOSEN_VERSION
COMMIT=FULL_MERGED_COMMIT_SHA
TAG="$PLUGIN--v$VERSION"
KEY=/absolute/path/to/your/release-signing.pub
SIGNERS=/absolute/path/to/your/trusted/allowed_signers

git remote -v
git fetch --no-tags origin refs/heads/main:refs/remotes/origin/main
git merge-base --is-ancestor "$COMMIT" origin/main
git show "$COMMIT:plugins/$PLUGIN/.claude-plugin/plugin.json"
git show "$COMMIT:docs/release-notes/$PLUGIN/$VERSION.md"
```

Stop if the remote, ancestry check, version or notes are wrong. With the approved private key available in your SSH agent, sign one annotated tag and verify it locally. Only push if verification succeeds and the tag identifies the intended commit:

```sh
git -c gpg.format=ssh -c user.signingkey="$KEY" tag -s "$TAG" "$COMMIT" -m "Release $PLUGIN $VERSION"
git -c gpg.ssh.allowedSignersFile="$SIGNERS" verify-tag "refs/tags/$TAG"
git rev-parse "refs/tags/$TAG^{commit}"
git push origin "refs/tags/$TAG:refs/tags/$TAG"
```

If the tag already exists, inspect it instead of replacing it. A signed commit with an unsigned tag is insufficient. Never send the private signing key to Actions.

## 3. Prepare the draft and review the OSV results

```sh
gh workflow run release.yml --repo "$REPO" --ref main -f tag="$TAG"
```

Open the **release → Prepare** run on GitHub. It checks the signer, manifest, notes and commit, runs the tests and dependency scan, and prepares an unpublished draft. Badge Buddy additionally repeats its [live criteria check](criteria-maintenance.md). Review the draft notes and its two attachments:

| File               | What to do with it                                                                                  |
| ------------------ | --------------------------------------------------------------------------------------------------- |
| `scan-scope.md`    | Check the commit, date, scanner version, platform, package count and outcome.                       |
| `osv-results.json` | Inspect the package inventory and any advisory IDs. Keep this report with the release it describes. |

The scan checks **maintainer tooling**: the root npm lockfile and the Python dependencies resolved from `requirements-dev.txt`, including transitive wheels for the scan platform. It does not scan plugin instructions, workflow behavior, or software installed by users. A clean result means no known advisories were reported for that inventory at that time.

The same scan runs weekly on the default branch. A finding or an incomplete scan blocks draft preparation. Open the failed run’s summary and available evidence, investigate the advisory and record the disposition. Fix affected dependencies in a PR; if changing already tagged inputs, make a new version and tag. Retry network or service failures against the same tag. To investigate locally, use the OSV-Scanner version pinned in [the scan helper](../tools/scan_dependencies.py) and run `make dependency-scan`; output is in `.cache/dependency-scan/`. Local resolution may differ from Linux CI.

## 4. Publish and verify

Use a trusted checkout of this repository’s current `main` with the release tag fetched. Copy the **exact command from the successful Prepare run’s summary**:

```sh
make release-finalize REPO=OWNER/REPOSITORY TAG=PLUGIN--vVERSION RUN=SUCCESSFUL_RUN_ID
```

This is the step that publishes. It compares the draft with the signed notes and the successful run’s evidence, checks that GitHub has release immutability enabled, publishes, then verifies the immutable release. The administration read permission needed for the settings check stays in your local GitHub CLI session. Follow [Verifying a plugin release](../VERIFYING.md) once from a separate checkout as a consumer would.

**If something stops:** Before a draft exists, fix the reported cause and rerun. If a partial draft exists or its preparation receipt is unavailable, keep it unpublished. Inspect ownership, tag, files and digests; after retaining its evidence, remove only that unpublished draft, keep the signed tag, and dispatch again. Never overwrite unknown assets or publish through the UI to bypass a failed check. If finalization was interrupted, check whether publication already occurred and retry the same command. Correct a bad published release with a new version.
