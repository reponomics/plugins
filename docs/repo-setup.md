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

No release job needs a bypass of branch protection. The approved publication job creates release tags and GitHub Releases at the checked commit; it does not commit to `main`.

## Configure squash merging

In **Settings → General → Pull Requests**, enable squash merging and disable merge commits and rebase merging. Set the default squash commit message to use the pull-request title, so the checked conventional title becomes the commit title even for a single-commit PR. See [GitHub's squash merge settings](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/configuring-commit-squashing-for-pull-requests).

Reopen the settings to confirm they were saved, and inspect a pull request to confirm that the three intended checks are required and squash merging is the available merge method. Complete the release-specific setup below before the first publication.

## Prepare the release repository

1. In **Settings → Secrets and variables → Actions → Variables**, set the repository variable `RELEASE_REPOSITORY` to the exact target `OWNER/REPO`. This enables publication only in the intended repository.
2. In **Settings → Environments**, configure an environment named `release`. Limit deployment to `main`, with `hesreallyhim` as a required reviewer. Allow self-review for this single-owner repository and disable administrator bypass. This approval authorizes publication of the exact commit whose checks and scan completed in that run. No environment secret or personal signing key is needed.
3. In **Settings → General → Releases**, enable [release immutability](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/establish-provenance-and-integrity/prevent-release-changes), or confirm an organization policy enables it for this repository. This is a one-time prerequisite that must remain enabled; it applies only to future releases. The workflow's `GITHUB_TOKEN` cannot read the administration setting. It verifies the attestation after publishing, but that check cannot prevent an already-published mutable release if an administrator disables immutability.
4. No custom release-tag creation or preservation rulesets are required. Repository writers are trusted to manage tags and releases, including correcting or deleting tags that are not attached to a published immutable release. Once an immutable release is published, GitHub locks its associated tag and assets while that release exists. This protection does not apply retroactively to older releases or to unpublished tags.
5. Confirm Actions policy permits job-level `contents: write` for publication and read-only access for planning, checks, and scans. Keep `main` and the `release` environment protected: the reviewed workflow, successful checks, and owner approval govern publication through this workflow. Repository writers can also publish releases directly; the environment is not a repository-wide release-access restriction. No additional secret token or signing bot is needed.
6. Follow the [release guide](releases.md) with a deliberately selected plugin version. Setup remains incomplete until a run confirms that tag creation is permitted, publication waits for owner approval, and the release attestation identifies the checked commit. After publication, use [consumer verification](../VERIFYING.md) from a separate checkout.

As verified on November 13, 2026, the live `release` environment is configured for `main` only, with `hesreallyhim` as required reviewer, administrator bypass disabled, and self-approval allowed because the owner initiates releases. Release immutability is enabled. The `release-tag-creation` and `release-tag-preservation` rulesets were removed; the `protect-main` ruleset remains active. This records the configured state, not completion of the first publication run.

An existing local checkout may still have `gpg.format` and `user.signingkey` overrides from the former SSH-tag process. Inspect their origins with `git config --show-origin --get-regexp '^(gpg\.format|user\.signingkey)$'`. If those repository-local overrides were installed only for the old release process, remove them with `git config --local --unset-all gpg.format` and `git config --local --unset-all user.signingkey` to inherit your usual Git configuration. Preserve intentional personal settings; release automation does not require changing global configuration or disabling commit signing.

Historical SSH-signed tags remain verifiable using the [historical signer instructions](../VERIFYING.md#historical-ssh-signed-tags). Their signer allowlist is not an input to the current publication workflow.
