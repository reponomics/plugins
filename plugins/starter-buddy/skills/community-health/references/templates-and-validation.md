# Starter templates and validation

Use the files under `assets/template-parts/` as adaptable starting points. Review the target repository, fill double-braced placeholders, remove inapplicable sections, and preserve useful existing guidance.

## Template collection

Use [template selection](template-selection.md) to select defaults from the requested contribution and issue categories before copying files. The collection offers open, guided, technical, and documentation reports, an optional suggestion form, two PR templates, and two security-policy variants. Read whichever options help with the selection or the user’s questions.

| Template part                       | Intended target                                      | Use when                                                                         |
| ----------------------------------- | ---------------------------------------------------- | -------------------------------------------------------------------------------- |
| `contributing.md`                   | `CONTRIBUTING.md` or an existing recognized location | Contribution guidance is missing or too vague to act on.                         |
| `support.md`                        | `SUPPORT.md` or an existing recognized location      | The project has a confirmed route for ordinary help; this file is optional.      |
| `variants/issues/`                  | Selected files under `.github/ISSUE_TEMPLATE/`       | The selected files cover the requested issue categories.                         |
| `.github/ISSUE_TEMPLATE/config.yml` | `.github/ISSUE_TEMPLATE/config.yml`                  | A shared chooser configuration with blank issues enabled.                        |
| `variants/pull-requests/`           | One `.github/pull_request_template.md`               | The user wants a PR template and the project accepts pull requests.              |
| `variants/security/`                | One `SECURITY.md`                                    | The maintainer confirms the support scope and monitored private reporting route. |

Fetch the selected license or code-of-conduct text from its canonical source as described in `license-and-conduct.md`.

For SUPPORT, distinguish ordinary usage questions from bugs, feature ideas, conduct reports, and vulnerabilities. Link only to channels that exist and are monitored. Include response expectations when they reflect an established service or a commitment the maintainer has chosen; omit inapplicable sections. GitHub surfaces the file when someone opens an issue and recognizes it in `.github/`, the repository root, or `docs/`. See GitHub's [support-resources guide](https://docs.github.com/en/communities/setting-up-your-project-for-healthy-contributions/adding-support-resources-to-your-project).

## README baseline

Preserve an adequate README. If it is absent, add a brief project purpose and the getting-started information already supported by the repository. A short, accurate README is enough for this setup; omit unknown instructions instead of inventing commands or promises. Link community files where useful.

Use this basic README as the default and expand it with the user when they want help with content or presentation.

## CONTRIBUTING baseline

Tailor accepted contribution types. Use real setup, formatting, lint, test, and build commands from the project. Distinguish required checks from helpful suggestions. State the smallest useful pull request workflow. Offer explanations of unfamiliar terms only when useful, and expand on request.

Reflect established contribution requirements, such as sign-off or changelog entries. Discuss additional requirements if the maintainer wants to introduce them.

## Issue-form baseline

Keep forms brief and actionable. The bundled forms set a title prefix (`[BUG]: `, `[FEAT]: `, `[DOCS]: `) and one of GitHub's default labels (`bug`, `enhancement`, `documentation`). Check that each label exists in the target repository; if it does not, remove the `labels` entry or create the label with the maintainer's agreement. Adjust or drop the prefixes to suit the project. The forms set no issue types, projects, or assignees; add those when useful and supported by the project.

For every YAML issue form:

- keep top-level `name`, `description`, and `body`;
- use unique, kebab-case input `id` values;
- collect the problem and reproduction information actually needed;
- avoid required fields that a reporter may not know; and
- keep the file on the default branch under `.github/ISSUE_TEMPLATE/`.

Bug-report forms and the general report template tell reporters not to publish vulnerability details and link the confidential route. Other forms omit that notice. When the repository has a security policy, GitHub's issue chooser links to it automatically, so `contact_links` does not need a security entry.

Keep blank issues enabled by default. Explain that disabling them makes templates or contact links the available entry points, and follow the maintainer’s preference. Use confirmed public URLs for `contact_links`.

The checklist does not require chooser configuration: a valid Markdown issue template or YAML issue form in `.github/ISSUE_TEMPLATE/` is enough according to GitHub's current documentation. Starter Buddy nevertheless includes `.github/ISSUE_TEMPLATE/config.yml` in its default starter pack so the blank-issue policy is visible and intentional. Use the documented filename `config.yml`.

GitHub documents issue forms as a public preview, so schema and rendering behavior can change. Re-check the [issue form syntax](https://docs.github.com/en/communities/using-templates-to-encourage-useful-issues-and-pull-requests/syntax-for-issue-forms) when validation behavior matters. The curated forms deliberately omit `default` fields because maintainers have encountered inconsistent behavior around default options. Treat that as a practical caution, not a claim that every default is unsupported. When a maintainer wants defaults, use the current field-specific syntax, preview the rendered form on GitHub, and verify the submitted result; preserve existing defaults for review rather than silently rewriting them.

Generate issue forms with the documented `.yml` extension. Current GitHub behavior can recognize existing `.yaml` forms, so preserve one that the target repository and Community Standards UI already recognize; describe that as observed compatibility rather than the published authoring contract. Markdown issue templates should use `.md`, not `.markdown`.

## Pull request template baseline

Default to the short PR template. Use the technical variant when compatibility and testing detail would help or the user prefers it. Tailor questions and checklists to the project’s actual review needs.

GitHub uses Markdown or text templates for pull requests. Put a single default at `.github/pull_request_template.md` unless the repository already uses a supported location or genuinely needs multiple templates.

## Validation pass

Before declaring a local changeset ready:

1. Run `community_check.py` against the repository when Python is available; otherwise inspect the file locations directly.
2. Check YAML you create or change with an available safe parser or validator. If needed, use a temporary environment to obtain one. Choose an appropriate available tool. The inventory helper does not parse issue-form YAML.
3. Use the current GitHub field documentation to check that the form asks for the intended information and uses the fields appropriately. A successful YAML parse establishes syntax, not GitHub acceptance.
4. Use available GitHub preview access to check rendered issue forms, especially custom `default` options. A local YAML parse cannot confirm rendering. If preview needs a push or publication, establish that it is within the authorized scope. When preview is unavailable, report that limit and continue with locally validated templates.
5. Confirm referenced labels, issue types, assignees, teams, projects, URLs, and commands exist—or remove the reference.
6. Search generated files for `{{...}}`, `TODO`, `CHANGEME`, example owners/repositories, example addresses, and private information.
7. Test relative links from the file location in which they will live.
8. Run `git diff --check` and review the full diff for unrelated changes.
9. Run the project's existing cheap documentation or configuration checks. Use temporary tooling for one-off checks; follow the project’s conventions if ongoing validation is part of the requested setup.

Report which checks ran locally and which behavior was verified on GitHub. Files become active on the default branch. See [Community Standards](community-standards.md) when assessing recognition or a score.
