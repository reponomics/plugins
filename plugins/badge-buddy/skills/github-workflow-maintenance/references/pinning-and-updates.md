# Action pins and updates

## Resolve references deliberately

Inventory step-level external actions, job-level external reusable workflows, and nested calls in reachable local composite actions. Preserve `owner/repo/subpath` when replacing a ref. Leave local relative references local; use image digests for container references when container pinning is in scope. Do not append a Git commit SHA to a local path or `docker://` reference.

For each distinct external repository/ref, resolve the intended revision from its owning upstream repository. Dereference annotated tags to the commit, not the tag object's SHA. Verify that a proposed SHA exists in that repository and contains the requested action or workflow path. Reuse lookup results within the task. Pace GitHub API requests, inspect rate-limit headers, and use a temporary clone for substantial source inspection.

For a pin-only request, resolve the existing tag or branch rather than silently upgrading. For an upgrade request, check the latest release and any project version constraints, then inspect runtime, runner, input, output, and behavior changes before editing. A major floating tag may currently resolve to a different release than when the workflow last ran; say so if historical equivalence matters. Keep existing pins unchanged unless upgrades are in scope or the pin is demonstrably invalid.

Use the full verified commit SHA and an accurate version comment on the same line. Match the repository's comment style while retaining useful rationale. Use a verified semantic release label when one exists; otherwise identify the branch or untagged commit honestly. Never paste placeholder SHAs or copy an example's old release into a working workflow as though it were current.

Dependabot can maintain the semantic version comment alongside an updated action SHA. An incorrect comment is not evidence of the commit's version; resolve the mapping before repairing it. See [GitHub's version-comment support](https://github.blog/changelog/2022-10-31-dependabot-now-updates-comments-in-github-actions-workflows-referencing-action-versions/).

## Keep updates maintainable

Inspect the existing updater first. For Dependabot, merge a `github-actions` update entry into `.github/dependabot.yml` or the existing supported configuration file; preserve other ecosystems, groups, schedules, ignore rules, and reviewers. Choose a cadence consistent with the user's maintenance expectations. This minimal example is for a repository without an existing configuration:

```yaml
version: 2
updates:
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
```

Check [Dependabot's supported locations and reference forms](https://docs.github.com/en/code-security/reference/supply-chain-security/supported-ecosystems-and-repositories#github-actions) before claiming that every nested action reference will be maintained automatically. Name any references outside the updater's coverage and propose an explicit maintenance path. Preserve a working Renovate setup instead of introducing redundant update PRs.

Explain that update PRs still need review and merging. Do not enable auto-merge as a side effect. If the user chooses an allowlist restricted to exact SHAs, include updating that policy in the upgrade procedure; a new pin can otherwise be correct yet blocked by policy.
