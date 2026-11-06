# Snyk Code and Snyk Open Source

Reuse an existing Snyk account or integration. Choose the product that matches the requested check:

| Command | Evidence |
| --- | --- |
| `snyk code test` | Source-code security analysis from Snyk Code. |
| `snyk test` | Dependency vulnerabilities and license issues from Snyk Open Source. |
| `snyk monitor` | A dependency snapshot for ongoing monitoring; it is not a SAST gate. |

An Open Source scan or dependency badge must not be presented as evidence that Snyk Code analyzed the application. These products complement rather than replace one another. [CLI command definitions](https://docs.snyk.io/developer-tools/snyk-cli/cli-commands-and-options-summary)

## Confirm suitability and data transfer

Consult the [component license table](licenses.md) when selecting Snyk: its CLI license and hosted service terms are separate. “Snyk Open Source” names the dependency-analysis product.

Check supported languages/frameworks, the selected organization, Snyk Code enablement, CLI authentication, and the account's actual entitlements and test limits. Do not assume a public project has unlimited hosted scans or that an Open Source subscription includes the needed Code configuration. Reuse an existing source-control integration instead of creating duplicate CLI projects. [Snyk Code prerequisites](https://docs.snyk.io/developer-tools/snyk-cli/scan-and-maintain-projects-using-the-cli/snyk-cli-for-snyk-code)

The ordinary Snyk Code CLI sends source to the hosted service for analysis. For public OSS this is part of the requested hosted setup. If the repository contains private code, check that sending it to the selected account is intended; Snyk documents caching/retention by deployment. [Snyk data handling](https://docs.snyk.io/snyk-data-and-governance/how-snyk-handles-your-data)

Install a reviewed, pinned CLI version with the project's existing mechanism. Authenticate interactively for local use or use an appropriately scoped service credential in the CI secret store. Never place a token in source, a command-line argument saved in logs, or a report. Check current authentication options for the selected account rather than fabricating a token or assuming OIDC is supported. [CLI authentication](https://docs.snyk.io/developer-tools/snyk-cli/authenticate-to-use-the-cli)

## Scan, interpret, and gate

With the CLI authenticated, use the selected organization and an explicit output path:

```bash
snyk code test --org=ORG_ID --sarif-file-output=snyk-code.sarif
```

Replace `ORG_ID` with the approved organization. `snyk code test` reports status 0 for a completed scan without findings, 1 for findings, 2 for an operational failure, and 3 when no supported projects are detected. Preserve that distinction in CI. A documented advisory rollout may accept 1 while failing 2/3 and unexpected statuses. Do not infer success from an absent report; JSON file output may be omitted on a clean SAST scan. If using `--severity-threshold`, Snyk Code accepts low/medium/high, not critical. [Code test contract](https://docs.snyk.io/developer-tools/snyk-cli/commands/code-test)

Keep finding export and policy evaluation separate so reports survive a finding-induced failure. Configure any GitHub SARIF upload as a distinct job/step with justified `security-events: write` and actual code-scanning availability; SARIF output alone does not grant that entitlement. Use stable distinct categories/files for multiple scanners. Never allow an upload step to conceal the scanner's operational failure.

## Keep credentials out of untrusted execution

Do not expose `SNYK_TOKEN` to fork PRs or run their checkout with privileged `pull_request_target`. Same-repository PRs are not automatically safe if they can alter scripts in a credentialed job. Prefer the existing vendor integration for its supported PR model or credentialed scans of reviewed default-branch commits, with local/token-free checks for other contributions. Clearly report when an untrusted PR lacks Snyk analysis. Do not treat a skipped scan as a clean one.

If adding Snyk Open Source alongside Code, inspect its build-tool behavior before placing credentials in the job: dependency analysis can invoke project-controlled tools. Keep dependency installation/build scripts separate from credential exposure where possible; never assume `--ignore-scripts` on an earlier package install protects later commands. [Snyk CLI code execution warning](https://docs.snyk.io/developer-tools/snyk-cli/code-execution-warning-for-snyk-cli)

For an honest README badge, use an observed workflow status with its policy documented, or a provider badge whose actual product and meaning have been verified. Follow [baseline-and-gates.md](baseline-and-gates.md); do not invent a Snyk Code score or reuse a dependency-vulnerability badge as SAST evidence.
