# Publish and verify the Scorecard badge

Use this procedure when setting up or repairing the official Scorecard Action or its badge. A public API result may already exist from hosted scanning, so inspect it and the current workflow first. Explain that enabling publication sends results to the public service, and honor existing authorization before asking about publication.

## Prepare the workflow

Read the [official Action setup instructions](https://github.com/ossf/scorecard-action#installation), [current workflow example](https://github.com/ossf/scorecard/blob/main/.github/workflows/scorecard-analysis.yml), and [publication restrictions](https://github.com/ossf/scorecard-action#workflow-restrictions) before editing. These upstream sources control supported triggers, repositories, runners, and permitted steps; do not maintain a frozen copy here. Check fork, enterprise, and private-repository limitations before promising a public result.

Use [GitHub workflow maintenance](../../github-workflow-maintenance/SKILL.md) for the actual edits and verification. Preserve a compatible existing workflow when possible. Resolve current compatible action releases to verified full commit SHAs and accurate release comments before writing `uses:` references. Keep workflow-level permissions minimal and read-only, and put necessary writes only on the analysis job.

Configure `publish_results: true` and the analysis job's required `id-token: write` for public API publication. Choose JSON for an importable artifact or SARIF for GitHub code scanning; uploading SARIF separately requires `security-events: write`. Derive necessary read permissions from the actual workflow and current upstream guidance. Publication and code scanning are separate outcomes.

For Action versions that support it, consider `fail_on_publish_error: true` to make an API rejection fail the step. Explain that network errors and HTTP 408, 429, and 5xx responses still produce warnings. Preserve result uploads after a rejection with `if: always()`. Check the selected version's [publication controls](https://github.com/ossf/scorecard-action#publishing-results) before configuring them.

Stay within the current publishing-job restrictions, including allowed actions; do not insert arbitrary shell debugging or plugin commands into that job. Use the built-in token normally; read [Action credentials](authentication-and-results.md#action-credentials) when additional access is needed. Validate the workflow locally before it reaches the remote. Editing the file does not by itself authorize pushing, changing repository settings, or publishing.

## Verify publication

After authorized changes reach the default branch and the supported trigger runs, inspect the relevant Action execution and publication logs. Fetch the API result into a new snapshot and verify its repository, commit, and date against the intended revision and run. Record these separate states accurately:

- The workflow file and repository changes passed local validation.
- The remote analysis and publishing run succeeded, failed, or has not run.
- The API reflects the intended revision, still serves an older result, or has no result yet.

Where supported, use `results_published` and `publication_status`, together with the job summary and annotations, to diagnose publication. The status reports the final HTTP status, `error`, or `skipped`. Any shell step reporting these outputs belongs in a separate job under the publishing-job restrictions. These signals do not replace checking the resulting API record.

For a failed run, investigate its actual error, especially publication restrictions, OIDC permissions, and optional expired credentials. A successful scan or artifact upload does not prove publication succeeded. For a stale API response, retry with bounded pacing; if it remains stale, finish with publication pending and the revision/run to check next. Do not change code or widen permissions solely because the badge has not updated yet.

Use the controller's `diff` on the saved baseline and newer result for observed changes. Review comparison warnings before explaining score movement; a new tool version or coverage change can alter results independently of the repository edits.

## Add or repair the badge

When requested, use the [official badge format](https://github.com/ossf/scorecard-action#scorecard-badge):

```markdown
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/OWNER/REPO/badge)](https://scorecard.dev/viewer/?uri=github.com/OWNER/REPO)
```

Replace OWNER/REPO with the verified identity and preserve an existing badge rather than adding a duplicate. Verify the API record, badge endpoint, and viewer destination before calling setup complete. An existing published result can support this badge without installing another workflow. Neither importing JSON nor displaying a badge initiates a scan.
