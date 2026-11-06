# Coverage reporting and CI

## From first coverage run to a useful badge

For Codecov setup, measure the suite, connect the repository, add the CI upload, and confirm the first default-branch report. Then copy the badge snippet into the README and link it to that report. A low initial percentage is a useful baseline; help the maintainer get the requested report and badge working, then improve tests as they choose.

Reuse an existing account connection. If repository activation or access is missing, identify the exact step the maintainer needs to complete. For reporting without a service, use local reports or CI artifacts.

## Reporting options

| Method | Useful for | Limits and setup |
| --- | --- | --- |
| Codecov | Linked coverage badge, historical reports, project and changed-code comparisons | Connect the repository and upload its reports |
| Terminal and local HTML | Finding missed behavior and sharing a baseline summary | No service account needed |
| CI artifacts containing HTML and XML/LCOV | Reviewing results for a specific commit, including fork PRs | Downloadable reports; no automatic patch comparison |
| Local threshold in the coverage producer | Consistent enforcement without a reporting vendor | Record metric and scope; keep test failures and missing reports fatal |
| Existing Coveralls, SonarQube, or GitLab coverage integration | Continuing a service the project already operates | Reuse its supported report format; consult current official provider documentation before editing configuration |

Upload the intended coverage files, rather than the whole working directory. For a private repository, check report visibility before publishing source-containing HTML or a public badge.

## Reference workflow

[python-coverage.yml](../assets/templates/workflows/python-coverage.yml) targets GitHub.com with GitHub-hosted runners. Adapt the default branch, runtime, dependency installation, source configuration, and Makefile target before use. It assumes the measurement reference's `make coverage` target and a maintained `requirements-dev.txt` containing the test/coverage dependencies. Add the repository's normal package-install/build steps if needed. Do not copy that filename over a different existing dependency workflow.

The test job writes HTML and XML reports. After successful coverage on a default-branch push, the Codecov job downloads the report from that run and uploads it using GitHub's OIDC authentication, which avoids storing an upload token. Test code runs separately from the job holding upload authority. The upload job checks out the same commit for metadata and uses an explicit report path. For reporting without Codecov, omit the `codecov` job and retain the downloadable artifacts.

This gives the README badge a default-branch baseline. PR reports are available as CI artifacts; add PR uploads using the next section when Codecov patch comparisons are wanted. Until then, do not require a Codecov PR status that this workflow does not produce.

The action pins were checked against upstream releases on 2026-10-31. Resolve current releases again when adopting the template; preserve full commit pins, version comments, and dependency update coverage. Pinning the Codecov action does not pin its downloaded CLI: select and maintain the action's `version` input if reproducible uploader tooling is required, and retain its integrity verification. The actions use modern Node runtimes; verify runner compatibility on self-hosted runners. The artifact action generations in this template are for GitHub.com, not GitHub Enterprise Server. See [artifact action compatibility](https://github.com/actions/upload-artifact#breaking-changes).

## Codecov authentication and PRs

Use the [pinned Codecov action documentation](https://github.com/codecov/codecov-action/tree/v7.1.1) and [Codecov token guidance](https://docs.codecov.com/docs/codecov-tokens) when choosing an event policy. Recheck current documentation when upgrading; do not infer fork support from a successful default-branch upload.

- For default-branch uploads, the template uses `use_oidc: true` with job-level `id-token: write`. If a repository token is needed instead, expose it only to the uploader and remove the unused OIDC permission.
- Fork PRs do not receive ordinary repository secrets. Public fork PRs may use Codecov's supported tokenless path, subject to current service policy. Do not switch to `pull_request_target` or execute downloaded PR artifacts in a privileged `workflow_run` job to bypass this restriction. Never send a stored upload token to untrusted test code.
- Check Dependabot and any private-fork behavior separately. Where an upload is unsupported, retain the artifact report and explain the skipped external check.

To add tokenless public-fork reporting, put an upload step in the ordinary read-only `pull_request` test job after a successful report. Supply no token and no `id-token: write`; restrict it to the eligible public-fork event. Use the same pinned Codecov action, `files: ./coverage.xml`, `disable_search: true`, `plugins: noop`, and `fail_ci_if_error: true`. Test an actual fork PR and confirm its commit appears in the report. Keep the authenticated default-branch upload separate. Authenticated same-repository PR uploads are appropriate for trusted contributors; remember that those contributors can also edit workflow definitions.

## Baselines, statuses, and missing data

Upload and confirm a default-branch baseline before expecting meaningful comparisons. Confirm service-side processing and file mapping, then check a representative PR once PR uploads are configured. A successful HTTP upload does not prove a report was processed or associated correctly.

Codecov's project status concerns aggregate coverage; patch status concerns changed code. Start with explicit informational checks if the team wants a trial period:

```yaml
# codecov.yml: an observational rollout, not an enforced coverage requirement.
coverage:
  status:
    project:
      default:
        target: auto
        informational: true
    patch:
      default:
        informational: true
```

An informational check passes regardless of coverage. Missing-report behavior and required status behavior are separate decisions: current `if_not_found` defaults to success. When enforcing checks, set intentional targets, tolerance, missing-report handling, and event coverage, then confirm observed behavior before making statuses required. A patch check cannot substitute for tests covering unchanged critical logic. See [Codecov status configuration](https://docs.codecov.com/docs/commit-status).

Keep uploader failures visible with `fail_ci_if_error: true`; do not use `continue-on-error` to make an incomplete upload look successful. This fails upload errors, not a coverage threshold. For matrices, use unique artifact names and supported report combination/flags with expected upload counts. Verify all required shards arrived; partial reports or carried-forward data can otherwise obscure missing measurement.

## Useful README badges and OpenSSF evidence

Add a coverage badge after confirming its backing report. Prefer the repository's generated snippet under Codecov's **Badges & Graphs** settings. A public GitHub repository commonly uses this form, as shown in [Codecov's Python example](https://github.com/codecov/example-python):

```markdown
[![Coverage](https://codecov.io/github/OWNER/REPO/branch/main/graph/badge.svg)](https://app.codecov.io/github/OWNER/REPO)
```

Replace owner, repository, and branch; URL-encode branch names when necessary. Select the intended flag/component query if the badge covers only part of a monorepo and label that scope. Inspect the linked report's commit/date and compare its percentage with the local metric before presenting it as current. Private badges may require a provider-issued badge token: review its visibility implications, and never substitute an upload token or another credential. See [Codecov status badges](https://docs.codecov.com/docs/status-badges).

Without a service, link the README to the coverage workflow's reports or publish a generated coverage badge/report through the project's documentation workflow. A workflow status badge says whether CI passed; a coverage badge communicates the measured percentage. Generate that percentage from each report so it stays current. Keep report scope, metric, commit/date, and update mechanism accessible alongside the evidence.

For OpenSSF Best Practices, use `ossf-bp-badges` and its current criteria catalog to evaluate the full requirement. The bundled catalog maps Silver `test_statement_coverage80` to at least 80% statement coverage, Gold `test_statement_coverage90` to at least 90% statement coverage, and Gold `test_branch_coverage80` to at least 80% branch coverage. Coverage at 80% branch is also one alternative under `dynamic_analysis` (suggested at Passing, required at Gold); other dynamic-analysis approaches can qualify. Supply separate numerators/denominators, tested scope, exclusions, test command, commit, and report evidence. Neither a combined coverage.py total nor a coverage badge alone establishes these criteria as Met.

## Validation checklist

- Confirm tests actually ran and failed tests cannot be hidden by report generation or uploading.
- Inspect the XML/LCOV paths and at least one never-imported production file; check source maps for transpiled code.
- Lint the adapted workflow and inspect every permission and trigger. Keep artifacts scoped to the current run and never execute downloaded report files.
- Verify default-branch and relevant PR uploads separately, including an eligible fork and automation account where supported. Record unavailable contexts as unverified.
- Verify service processing, metric scope, status behavior, and a deliberate below-threshold case before enabling required checks. Do not require statuses that are never posted for some permitted contribution paths.
