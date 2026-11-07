# Select starter files

Use the bundled templates under `assets/template-parts/variants/`. Start with a small, useful set based on the requested setup and repository evidence. Fill confirmed details and adapt the prompts. Preserve useful existing files. Show alternatives or find additional templates when the user wants to explore.

## Choose defaults from the requested intake

Use the setup conversation to identify useful categories and preferences. The defaults below let a maintainer get started quickly; adapt them as the conversation develops.

Select bug, feature/suggestion, and documentation routes only when the maintainer wants them. Start with the shortest suitable templates:

| Need                       | Bundled source under `variants/` | Selection guidance                                                                                 |
| -------------------------- | -------------------------------- | -------------------------------------------------------------------------------------------------- |
| General reports            | `issues/open-report.md`          | Use when one open report covers the requested intake. Avoid duplicate category forms.              |
| Software bugs              | `issues/guided-bug.yml`          | Default for a small reproduction and relevant version information.                                 |
| Environment-dependent bugs | `issues/technical-bug.yml`       | Use when known project behavior needs configuration, versions, or logs; remove unnecessary fields. |
| Documentation reports      | `issues/documentation.yml`       | Use when documentation is a selected category.                                                     |
| Features or suggestions    | `issues/suggestion.yml`          | Use when this is a selected category and not already covered by an open report.                    |
| Pull requests              | `pull-requests/short.md`         | Default when a PR template is wanted.                                                              |
| Detailed technical PRs     | `pull-requests/technical.md`     | Use when compatibility and test details would help, or the user prefers more structure.            |

Choose issue and PR templates independently according to their usefulness. A declined PR template can be left out.

For a requested security policy, select `security/single-line.md` for one maintained release line or development branch, or `security/maintained-versions.md` for several explicitly maintained versions or branches. Use the actual support policy rather than project size or tags to select the variant. Read [security reporting](security-reporting.md) before finalizing the policy.

## Show the proposed files

Give a short file list with destinations and any commitments the files introduce. Show the actual wording or a preview when helpful, and let the user refine the selection. Proceed with edits already authorized.

## Apply the selection

| Source                                                                      | Destination for a new file                 |
| --------------------------------------------------------------------------- | ------------------------------------------ |
| `variants/issues/open-report.md`                                            | `.github/ISSUE_TEMPLATE/report.md`         |
| `variants/issues/guided-bug.yml` **or** `variants/issues/technical-bug.yml` | `.github/ISSUE_TEMPLATE/bug-report.yml`    |
| `variants/issues/documentation.yml`                                         | `.github/ISSUE_TEMPLATE/documentation.yml` |
| `variants/issues/suggestion.yml`                                            | `.github/ISSUE_TEMPLATE/suggestion.yml`    |
| One file from `variants/pull-requests/`                                     | `.github/pull_request_template.md`         |
| One file from `variants/security/`                                          | `SECURITY.md`                              |

Preserve recognized existing locations. Default new README, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, SUPPORT, and LICENSE files to the repository root. If the user prefers `.github/` or `docs/`, use those for supported community documents; keep the repository license at the root and issue templates under `.github/ISSUE_TEMPLATE/`.

Choose one default PR template and normally one primary bug-report route. Keep blank issues enabled unless the maintainer prefers otherwise. The shared chooser configuration is `assets/template-parts/.github/ISSUE_TEMPLATE/config.yml`; preserve existing configuration and inherited routes when applicable.

Copy and adapt the selected variants using the CC0 terms described in SKILL.md. Existing or separately sourced material retains its own licensing terms.

Replace every `{{...}}` token with confirmed information. The bug-report forms and the general report template use `{{SECURITY_POLICY_URL}}` for the actual security-policy link. If no policy link is available, remove the link from the forms while keeping the instruction not to publish vulnerability details. If the support scope or private route remains unresolved, leave SECURITY pending or work on a clearly identified draft while continuing with the other files. Follow [template validation](templates-and-validation.md).
