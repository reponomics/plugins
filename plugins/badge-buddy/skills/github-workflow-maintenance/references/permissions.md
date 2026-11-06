# Job permission analysis

Read each workflow's triggers, jobs, scripts, action metadata, token inputs, and called workflows. Build a per-job table of operation, credential used, required scope, and supporting evidence. Inspect scripts invoked by `run:`; an innocent job name does not establish what API writes it performs.

Use a minimal workflow default. `contents: read` often supports checkout; `permissions: {}` is appropriate when jobs require no default repository access. A job with an explicit permission map gets `none` for unspecified scopes, so include its necessary reads as well as writes. Repository defaults provide a starting point, not a ceiling on permissions declared in YAML. See [GitHub's permission semantics](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#permissions).

Use these operations as investigation leads, not a template to copy into every job:

| Operation | Scope to investigate |
|---|---|
| Checkout or read repository content | `contents: read` |
| Create a GitHub release or push a tag with GITHUB_TOKEN | `contents: write` |
| Push to GitHub Packages using GITHUB_TOKEN | `packages: write` |
| Upload code-scanning results | `security-events: write` |
| Obtain an OIDC token | `id-token: write` |
| Create or modify a pull request with GITHUB_TOKEN | `pull-requests: write`, plus any separate branch/content operation |

Verify the selected action's actual requirements, including extra read permissions and repository visibility constraints. Distinguish `GITHUB_TOKEN` from PATs, GitHub App tokens, and cloud credentials: reducing YAML permissions does not reduce a separately supplied credential's privileges. Do not solicit or print token values. Explain the practical access and maintenance implications of GitHub App credentials when they are relevant to the selected workflow.

Before introducing a personal access token (PAT) or another separately managed credential, explain its ongoing upkeep: who owns it, its actual expiration or applicable rotation policy, where the replacement must be stored, and which workflows would fail if it expires or is revoked. Resolve whether the maintainer accepts that responsibility as part of choosing the credential. Do not invent a rotation interval or imply that these duties apply to the workflow's automatically managed `GITHUB_TOKEN`. At handoff, identify the next renewal or rotation action when applicable, without exposing the secret.

For reusable workflows, inspect the caller and called jobs. Permissions can be maintained or reduced through a call chain, not elevated by a callee beyond what its caller grants. Grant required access at the appropriate caller as well as the executing job; preserve the call's inputs and secrets. See [GitHub's reusable-workflow guidance](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows#nesting-reusable-workflows).

For fork and Dependabot pull requests, account for restricted token and secret access. Do not switch to `pull_request_target`, enable write tokens for forks, or introduce a PAT merely to make a permission failure disappear. Identify privileged triggers, untrusted checkout, and shell interpolation as separate findings; a permission rewrite alone may not repair the trust boundary.

Before removing a scope, name the affected operation and evidence that it no longer needs access. If requirements cannot be established, leave that scope unresolved and explain the missing evidence instead of asserting least privilege. Validate representative affected jobs before claiming the operational behavior is preserved.
