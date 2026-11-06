# Repository setup

Configure branch protection and pull-request merging in GitHub's UI when preparing a development or public plugin repository. These settings describe the project's intended baseline; compare them with any existing repository or organization rules before editing those rules.

## Prepare the required checks

Install the workflows on `main` and let them run on a pull request before selecting required checks. In particular, `semantic-pr.yml` uses `pull_request_target`, so it must already exist on the base branch to run.

| Required check | Workflow                            | Purpose                                                  |
| -------------- | ----------------------------------- | -------------------------------------------------------- |
| `check`        | `.github/workflows/check.yml`       | Run repository tests and compile Python sources.         |
| `validate`     | `.github/workflows/release.yml`     | Validate the release plan and run its applicable checks. |
| `title`        | `.github/workflows/semantic-pr.yml` | Check the conventional pull-request title.               |

Select the check names above from actual GitHub Actions runs; the workflow names themselves are not the required check names.

## Protect main

Open **Settings → Branches** and edit the existing rule for `main`, or choose **Add classic branch protection rule** and enter `main` as the branch pattern. Configure the following policy, then save it:

| Setting                   | Intended behavior                                                                                                     |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Pull requests             | Require a pull request before merging.                                                                                |
| Approvals                 | Leave required approvals off; a separate person's approval is not required. Code-owner approval is also not required. |
| Status checks             | Require `check`, `validate`, and `title` to pass.                                                                     |
| Branch freshness          | Require the branch to be up to date before merging.                                                                   |
| History                   | Require linear history.                                                                                               |
| Administrators            | Enable the option that prevents bypassing the protection settings.                                                    |
| Push restrictions         | Use ordinary repository permissions; no additional people, team or app allowlist is required.                         |
| Force pushes and deletion | Keep both disallowed.                                                                                                 |

If an existing ruleset supplies these protections, review its effective settings rather than adding a competing classic rule. GitHub documents the controls in [Managing a branch protection rule](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/managing-a-branch-protection-rule).

No release job needs a bypass of branch protection. Maintainers push signed tags for reviewed commits; the workflow creates GitHub drafts and does not commit to `main`.

## Configure squash merging

In **Settings → General → Pull Requests**, enable squash merging and disable merge commits and rebase merging. Set the default squash commit message to use the pull-request title, so the checked conventional title becomes the commit title even for a single-commit PR. See [GitHub's squash merge settings](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/configuring-commit-squashing-for-pull-requests).

Reopen the settings to confirm they were saved, and inspect a pull request to confirm that the three intended checks are required and squash merging is the available merge method. Complete the release-specific setup below before the first draft.

## Authorize release signers

Choose who may authorize a release. Each signer keeps the private SSH signing key on their own machine, agent or hardware device. Authenticate the public key and fingerprint using the [signer verification procedure](../VERIFYING.md#get-the-expected-signer-independently) before enrolling it.

Maintain an OpenSSH allowed-signers file containing one entry per approved key. Each entry consists of the maintainer principal, the restriction `namespaces="git"`, and the public key type and base64 value. For a single public key, create a line locally with the actual principal and previously verified public key:

```sh
{ printf '%s namespaces="git" ' "$MAINTAINER_PRINCIPAL"; cat release-signing.pub; } > allowed_signers
```

In **Settings → Secrets and variables → Actions → Variables**, set `RELEASE_ALLOWED_SIGNERS` to the contents of the reviewed file, and `RELEASE_REPOSITORY` to the target repository’s exact `OWNER/REPO`. Both must be **repository variables**, since validation runs before entering the release environment. The allowlist is public verification material but controls who may authorize releases; restrict who may change it. Publish the keys and their fingerprints through a channel consumers can authenticate independently of the release tag. Document which versions each key covers. Update both the Actions variable and the public notice on rotation or revocation; retain historical verification information and distinguish a compromise from an ordinary retirement.

## Prepare the release repository

1. Under **Settings → Environments**, configure an environment named `release`. Limit deployment to the branch `main`; do not permit tag refs or other branches. The maintainer’s local publication step is the human decision; a second environment reviewer is optional. No environment secret is required for signing or publication.
2. Under **Settings → General → Releases**, enable [release immutability](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/establish-provenance-and-integrity/prevent-release-changes) before publishing. Enabling it only affects future releases. Use an authorized local GitHub CLI session for finalization. It needs Administration: read for the immutable-release setting, Actions: read for the successful run and artifacts, Variables: read for the independent signer allowlist, and Contents: write to publish the draft. These permissions are for the maintainer; Actions does not need an administration token.
3. Protect release tags against updates and deletion. Use tag rulesets matching this repository’s actual plugin tag names, and authorize only designated maintainers to create them. If granting a bypass to allow tag creation, use separate creation and update/deletion rulesets so that a release signer cannot bypass both protections with the same grant. Check organization rules too.
4. Confirm Actions policy permits the draft job’s job-level `contents: write` and the read-only validation and scan jobs. A secret token, GitHub App private key or bot that pushes tags is not needed. Keep `main` and the release environment protected: their workflows govern what reaches the draft.
5. Follow the [release guide](releases.md) using one deliberately selected version for the first plugin. Test signer recognition, notes, scanning and draft preparation before finalization. After publication, use [consumer verification](../VERIFYING.md) from a separate checkout.
