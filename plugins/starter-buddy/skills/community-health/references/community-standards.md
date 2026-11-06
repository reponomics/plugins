# GitHub Community Standards reference

Use this reference for file recognition, inheritance, and Community Standards questions. A basic setup can include whichever files are useful to the project.

## Authority and freshness

Treat **Insights → Community Standards** on the target repository as the final user-visible authority. Use `GET /repos/{owner}/{repo}/community/profile` as supporting evidence for a public non-fork repository. The REST endpoint explicitly excludes forks, does not expose every visible row in its `files` object, and can lag changes to the default branch.

The model below was last checked against GitHub.com and GitHub's documentation on 2026-09-06. Re-check the official documentation and target UI when current behavior matters. Report drift instead of forcing new behavior into this model.

## Visible completion target

For a complete checklist, assess each visible row and explain remaining items. Follow the user’s choices about policies and settings; the files can be prepared independently.

| Visible row                              | What to establish                                                     | Straightforward repository-specific location | Important caveat                                                                                                        |
| ---------------------------------------- | --------------------------------------------------------------------- | -------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- |
| Description                              | One short, factual GitHub repository description                      | Repository setting                           | Cannot be changed by a pull request.                                                                                    |
| README                                   | Useful project purpose and getting-started information                | `README.md`                                  | GitHub also recognizes README files in `.github/` and `docs/`.                                                          |
| Code of conduct                          | A nonempty, adopted policy with a real enforcement route              | `CODE_OF_CONDUCT.md`                         | Adoption creates an enforcement commitment; fetch current canonical text.                                               |
| Contributing                             | Accurate guidance for the contributions the project accepts           | `CONTRIBUTING.md`                            | An honest limited-contribution posture is valid.                                                                        |
| License                                  | A recognized, maintainer-selected license                             | `LICENSE`                                    | Auto-detection requires the repository root; `.github/` and `docs/` do not count. Licenses are not inherited.           |
| Security policy                          | Supported versions and a confidential reporting route                 | `SECURITY.md`                                | Separate from enabling private vulnerability reporting.                                                                 |
| Issue templates                          | At least one valid Markdown issue template or YAML issue form         | `.github/ISSUE_TEMPLATE/`                    | Must be valid and on the default branch. `config.yml` is optional chooser configuration, not the checklist requirement. |
| Pull request template                    | A useful Markdown or text template                                    | `.github/pull_request_template.md`           | GitHub has PR templates, not PR forms. Must be on the default branch.                                                   |
| Repository admins accept content reports | An enabled moderation intake for qualifying organization repositories | Repository setting                           | Appears only for public organization-owned repositories; cannot be changed by a PR.                                     |

**Undocumented behavior, confirmed by the maintainer on November 4, 2026:** the Community Standards checklist currently counts reported content only when **Prior contributors and collaborators** is selected; **All users** does not satisfy the row. This option allows only previous repository contributors and collaborators to report content, so explain the audience restriction when choosing it.

`SUPPORT.md` is a supported optional community health file, but it is not a visible score row. It tells people where to get ordinary help and GitHub links to it from the new-issue experience. Use `.github/`, the repository root, or `docs/` in the usual precedence order. Add it only when the maintainer has a real support route and honest expectations to publish.

## Interpreting the percentage

Use GitHub’s reported `health_percentage` for the current score. A count of local files or visible rows is not equivalent to that metric. If the user asks for an estimate, explain its evidence and uncertainty and distinguish it from a GitHub-confirmed result.

GitHub documents the percentage as the proportion of recommended community health files present, but does not publish an exact weighting formula. Current live behavior is consistent with seven scoring buckets for personal public repositories and an eighth `content_reports_enabled` bucket for organization-owned public repositories. The issue-template and pull-request-template rows currently appear to share one percentage bucket, while both remain independently useful visible rows. The repository description also participates in observed results. Treat this paragraph as an observation, not a promised formula.

The Community Profile REST response currently returns:

- `health_percentage`;
- `description`;
- `content_reports_enabled` for organization-owned repositories; and
- `files` entries for code of conduct, contributing, issue template, pull request template, license, and README.

The `files` object does not currently expose SECURITY. It can also fail to reveal a valid or inherited issue-form setup, so it is incomplete evidence for a score estimate.

## Three shared locations

For supported files that may live in more than one location, GitHub uses this precedence:

1. `.github/`
2. the repository root
3. `docs/`

This order applies to files such as README, CONTRIBUTING, CODE_OF_CONDUCT, and supported default community health files. When more than one matching file exists, inspect the highest-precedence copy first and warn about conflicting duplicates.

Use these exceptions:

- Store repository issue templates and forms under `.github/ISSUE_TEMPLATE/`.
- Store a single PR template in `.github/`, the root, or `docs/`; multiple PR templates belong in a `PULL_REQUEST_TEMPLATE/` directory under one of those locations.
- Store the repository license at the root. Unlike the shared paths above, a license in `.github/` or `docs/` is not auto-detected as the repository license. Root placement also includes it in clones, packages, and downloads.

Prefer an existing recognized location over moving files merely for tidiness.

## Personal-account and organization defaults

An individual account or organization can create a public special repository named `OWNER/.github` and place reusable default community health files there. Look for those inherited files when the target has no repository-specific version. Defaults can include CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, SUPPORT, issue templates, and PR templates.

A public `OWNER/.github` repository is useful for shared defaults across projects. It is a separate repository, so establish that changes there are within the requested scope before editing or publishing them.

Apply these inheritance rules carefully:

- A repository-specific file overrides the corresponding default.
- Any valid repository-specific issue template or issue-template configuration prevents use of the entire inherited `.github/ISSUE_TEMPLATE` directory.
- Default files do not appear in the target repository's clone, file browser, packages, or Git history.
- A license cannot be inherited. Add the selected license to each repository.

Preserve effective inherited defaults unless the requested setup needs a repository-specific version. Explain any proposed override and its effect on inherited issue routes.

## Default branch and delayed verification

Community files on a feature branch are proposals. Issue forms and PR templates do not become active until they reach the default branch. GitHub may take time to refresh the Community Standards UI and API after merge.

Use these states precisely:

- **present locally** — a likely candidate exists in the working tree;
- **proposed** — a candidate exists only in an unmerged branch or pull request;
- **inherited** — GitHub supplies an account or organization default;
- **recognized** — GitHub's UI or API identifies the item on the default branch;
- **expected after merge** — local validation is complete but GitHub cannot confirm yet; and
- **confirmed 100%** — GitHub reports 100 after all file and setting changes are effective.

## Canonical sources

- [About community profiles for public repositories](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/about-community-profiles-for-public-repositories)
- [Accessing a project's community profile](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/accessing-a-projects-community-profile)
- [Community Profile REST endpoint](https://docs.github.com/en/rest/metrics/community)
- [Creating a default community health file](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/creating-a-default-community-health-file)
- [About repository README files](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes)
- [Setting contribution guidelines](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/setting-guidelines-for-repository-contributors)
- [Adding a code of conduct](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/adding-a-code-of-conduct-to-your-project)
- [Adding a license](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/adding-a-license-to-a-repository)
- [About issue and pull request templates](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/about-issue-and-pull-request-templates)
- [Adding support resources](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/adding-support-resources-to-your-project)
