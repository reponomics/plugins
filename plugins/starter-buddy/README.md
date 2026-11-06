# Starter Buddy

Starter Buddy helps maintainers put useful community files in a GitHub repository. It inspects what is already there, asks a few practical questions, adapts the bundled templates, and prepares the files or a pull request. It is designed for junior developers and maintainers who want to get their repository ready without researching and assembling every document themselves.

Starter Buddy builds on your existing files. It starts with a basic README and practical defaults, and can help you explore alternatives, compare licenses, or refine the wording and presentation as you go. The plugin does explain responsibilities you would take on, such as monitoring a private security inbox or handling conduct reports, before putting those commitments in a policy.

## Get started

Add the marketplace and install the plugin in Claude Code:

```sh
claude plugin marketplace add reponomics/plugins
claude plugin install starter-buddy@reponomics
```

Then ask: “Set up the community files for this repository.” Add “and open a pull request” if that is how you want the changes delivered. The skill is also available as `/starter-buddy:community-health`.

## Typical setup choices

Claude uses existing project information and your earlier answers before asking about these topics:

| Topic              | What you decide                                                                                                                                      |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| Contributions      | Whether you welcome code, documentation, ideas, or reports.                                                                                          |
| Issue categories   | Whether to provide bug, feature, or documentation reports, or skip new issue templates.                                                              |
| Pull requests      | Whether to add a short PR template.                                                                                                                  |
| License            | Use a chosen license, discuss the options, or leave it for later.                                                                                    |
| Code of conduct    | Whether to adopt a policy, with a real contact and someone responsible for handling reports. Otherwise leave it out.                                 |
| Security reporting | Whether to use GitHub private vulnerability reporting or an existing private contact, and what you will support. Otherwise leave the new policy out. |

These topics guide the setup rather than limit the conversation. Claude uses what you have already provided, asks for missing details, and follows your interest in explanations or alternatives. You make the policy choices; the resulting files reflect your actual contacts, practices, and commitments. Decisions left for later do not hold up the other files.

## What gets created

The requested set can include a basic `README.md`, `CONTRIBUTING.md`, issue templates or forms, a pull request template, and the license and policies you have chosen. An optional `SUPPORT.md` is useful when there is an established place for usage questions. The plugin starts with suitable bundled defaults. You can ask to see more templates or customize them during setup.

Existing recognized locations are preserved. New standalone documents normally go at the repository root; issue templates go in `.github/ISSUE_TEMPLATE/` and the PR template in `.github/pull_request_template.md`. You can request another supported location for community documents. The license stays at the root for GitHub detection. Defaults inherited from a public `OWNER/.github` repository are checked before adding duplicates; changing that separate repository is outside the normal setup.

The [template guide](skills/community-health/references/template-selection.md) documents the bundled choices. Issue, PR, and security variants are available under [CC0-1.0](skills/community-health/LICENSE-CC0.txt), so they can be copied and adapted without carrying attribution or license notices into your repository.

## Review and delivery

Claude shows the proposed file set, prepares the changes, and checks locations, form structure, commands, links, contacts, and unresolved placeholders. It finishes with what was created, preserved, skipped, or left pending. A request to set up files authorizes those edits; publishing, opening a PR, and changing repository settings follow the scope you requested.

Enabling private vulnerability reporting is a named setting choice: it creates a private inbox that someone must monitor. A security policy also needs an honest support scope. Repository descriptions and organization moderation settings can be handled when requested; they are not prerequisites for creating the files.

GitHub private vulnerability reporting and the Community Standards profile require a public repository. For a private repository, the plugin can prepare and validate the files, use an existing private reporting contact, and leave GitHub enablement and score verification until after publication. It does not change repository visibility.

## GitHub Community Standards

You can also ask “What is missing from Community Standards?” or explicitly request help reaching 100%. For that scope, Claude checks GitHub's visible checklist and verifies the live result after merge. A local file count or open PR is not a confirmed score, and skipped policies are reported honestly rather than filled in to improve a number.

GitHub Community Standards detection is a setup signal, not a certification of quality, security, or maintenance capacity. Private vulnerability reporting is separate from that score.

## Development

Load the plugin locally:

```sh
claude --plugin-dir ./plugins/starter-buddy
```

Run `make check` from the repository root, or `make plugin-validate` to check plugin structure with the Claude Code CLI. Tests are kept under `tests/starter-buddy/`, outside the installed plugin. The inventory helper uses the Python standard library and lists issue forms without parsing their YAML; form validation is a separate part of preparing the changes.
