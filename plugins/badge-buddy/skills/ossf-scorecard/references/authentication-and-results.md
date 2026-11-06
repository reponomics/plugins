# Results, credentials, and optional diagnostics

## Read and preserve upstream evidence

The public API serves existing results from hosted scanning or Action publication. `fetch --repo owner/repo --output <path>` saves the upstream JSON plus acquisition provenance. Keep the original baseline and use a new path for the next result. `explain --input <path|->` reads that snapshot or JSON produced by upstream Scorecard. `diff` reads the original result files; do not feed it the controller's interpretation summaries.

Explain the supplied score and check reasons without recalculating an aggregate. A missing overall score remains unavailable. Preserve inconclusive checks as inconclusive and distinguish absent checks from failures. Imported results may omit provenance, version, details, or a usable commit; state those limits rather than assuming complete coverage or publication.

Details and documentation may be absent or null. Use the reported file locations to inspect the relevant revision, then read the upstream check documentation for that tool version. New check names can still be explained from upstream evidence without a bundled catalog. Maintainer annotations are context, not proof that a finding was resolved.

## Acquisition failures

A missing public result has no score to interpret. For a public GitHub repository, discuss Action publication when relevant to the request; for GitLab, use supplied JSON or upstream GitLab guidance. Invalid repository input should be corrected before retrying. For network errors, rate limits, or service failures, report the cause and retry with bounded pacing when useful; do not repeatedly change workflow files. Authentication failures on other services do not justify requesting a token for the unauthenticated public Scorecard API.

The controller accepts Scorecard JSON, not SARIF. In GitHub's code scanning view, expand an alert to read its remediation guidance; Action logs and configured artifacts can supply more context. Inspect SARIF there or use an API/JSON result for import. See [upstream viewing results](https://github.com/ossf/scorecard-action#view-results).

## Action credentials

Prefer the workflow's built-in `GITHUB_TOKEN`. Check [current Action authentication guidance](https://github.com/ossf/scorecard-action#authentication-with-fine-grained-pat-optional) when a specific finding lacks access. Classic branch-protection visibility can require additional credentials; repository rulesets can be read with the default token. Investigate the actual failure before broadening access.

If optional credentials are selected, follow the [upstream fine-grained token procedure](https://github.com/ossf/scorecard-action/blob/main/docs/authentication/fine-grained-auth-token.md), limiting access to the required repository and operation. Have the user supply secrets through their environment or repository secret manager, never in chat or committed files. Confirm any organization approval and expiration requirements. Read [action-publication.md](action-publication.md) before changing publication permissions or verifying publication.

Before adopting an optional token, explain its upkeep and carry the accepted responsibility into the handoff: who will renew or replace it, its actual expiry or replacement trigger, and which named secret they must update. Explain which checks or workflow depend on it and may lose access or fail when it expires. Verify the next run after replacement. Do not invent a rotation schedule or assign manual renewal work for the built-in `GITHUB_TOKEN`.

## Optional upstream CLI diagnostics

For a user who already runs upstream Scorecard, link to its [usage and authentication guidance](https://github.com/ossf/scorecard#scorecard-command-line-interface). A targeted diagnostic from their existing environment can produce importable JSON:

```bash
scorecard --repo=github.com/OWNER/REPO --checks=Pinned-Dependencies --show-details --format=json > /tmp/scorecard-diagnostic.json
"<scorecard-controller>" explain --input /tmp/scorecard-diagnostic.json
```

The first command is an upstream example for a user-established workflow, not a plugin-managed execution path. Replace the repository, check, and output path for the selected task. Direct installation, binary selection, and credential troubleshooting to upstream; the plugin can continue from the JSON without managing those operations.

A remote CLI run can reveal fresh diagnostic information without publishing it. Local checkout analysis covers only supported checks and may still require network access. Selected-check runs and local results cannot establish the public badge's score. Retain their diagnostic role even when their findings motivate local edits; verify the badge separately through a later API record.
