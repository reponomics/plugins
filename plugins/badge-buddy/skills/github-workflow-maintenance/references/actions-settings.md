# Optional repository Actions policies

Inspect the current repository and inherited organization or enterprise policy before recommending a value. Use **Settings > Actions > General**. Controls may be unavailable or locked by higher-level policy. Never infer the live setting from workflow YAML. Consult [GitHub's repository settings documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository) for current UI labels and availability.

## Require SHA-pinned actions

Offer full-SHA enforcement under Actions permissions after preparing compatible workflows. The restriction includes GitHub-authored and organization-owned actions. A reusable workflow reference can still use a tag, but actions executed inside that workflow must satisfy the full-SHA policy too. Inspect nested actions before enabling enforcement; a tagged reusable workflow is not an exemption for its contents. Keep external reusable workflows pinned as a maintenance convention even though this checkbox does not enforce that convention.

An unpinned action can make a workflow fail under enforcement. Verify reachable dependencies and active release branches before enabling it, and explain that old refs may remain incompatible. See [GitHub's enforcement announcement](https://github.blog/changelog/2025-08-15-github-actions-policy-now-supports-blocking-and-sha-pinning-actions/).

## Restrict default token access

Offer the restricted Workflow permissions option: read access to contents and packages. New personal repositories use this default; organization repositories inherit their organization's choice. Verify older repositories. Explicit YAML permissions can request additional access, so this setting does not forbid job-level writes.

Use the workflow inventory to identify jobs relying on implicit writes. Prepare explicit, justified job permissions before changing the default. Keep any separate PR creation/approval setting unchanged unless that behavior is part of the request.

## Limit permitted actions and reusable workflows

Offer an allowlist as an optional stricter policy. GitHub's selected-actions mode also permits owner-local components; explain the resulting scope. Broad GitHub-authored or verified-creator exceptions allow more than an exact inventory. Rules may select repositories or particular refs; reusable workflows need their workflow paths. Check the current documented pattern syntax before proposing entries.

Construct the proposed list from the inspected dependency graph, including nested calls and release workflows, rather than from a generic list of popular actions. Identify inaccessible external dependencies before claiming coverage. Present every entry with why it is needed. Explain the maintenance choice:

- Repository-scoped rules allow future pins from those repositories, reducing policy changes during upgrades.
- Exact-SHA rules require policy maintenance with each upgrade and can block Dependabot PR checks until a new ref is allowed.

Treat neither SHA pinning nor an allowlist as proof that the allowed code is safe. Do not promise a Scorecard increase for this policy.

## Apply only the selected policy

Prepare a concrete before/after proposal and identify workflows that would be blocked. Honor earlier authorization; otherwise use `AskUserQuestion` to distinguish file changes from enabling each policy. A declined policy is a completed decision, not an unresolved failure.

Record the previous value for rollback. Ensure compatible workflow changes have reached the relevant branches before tightening enforcement; a local diff alone is insufficient. If merging is not authorized, leave settings pending with exact UI instructions. After an authorized UI or API change, read the effective setting again and validate an appropriate non-publishing workflow when authorized. Report inherited restrictions, pending validation, and how to restore the previous value if a required workflow is blocked.
