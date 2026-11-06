---
name: community-health
description: This skill should be used when the user asks to "set up community files", "quickstart this repo", "prepare my first open source project", "add issue forms", "add a pull request template", "write CONTRIBUTING or SECURITY", "enable private vulnerability reporting", "improve my GitHub Community Standards score", or "get to 100% community health". It creates a practical repository baseline with a short conversation and sensible file defaults.
---

# GitHub community health

Help the maintainer get useful community files into the repository. Inspect what exists, resolve the choices that matter, adapt suitable templates, and deliver the changes. Default to a short setup with a basic README and practical community files.

The flow below is a starting point, not a limit on the conversation. Offer explanations briefly and follow the user's interest: answer questions, compare licenses, show more templates, or refine the documents when useful. Use what the user has already told you. If they are undecided or want to skip something, continue with the other files.

Before putting a commitment into a policy, briefly explain the responsibility it creates—for example, monitoring private reports, handling conduct complaints, or maintaining stated versions. Base contacts, commands, and commitments on the project's actual practices and the maintainer's choices.

## 1. Inspect and propose

Inspect the working tree, repository instructions, existing community files, issue and PR templates, and project metadata. Preserve useful existing work and recognized locations. Check inherited account or organization defaults when accessible; local setup can proceed without GitHub access.

Use `${CLAUDE_PLUGIN_ROOT}/scripts/community_check.py` for a local inventory when Python is available. It identifies file candidates. Read `references/community-standards.md` for recognition and inheritance details or checklist questions.

Give a brief account of what exists, what you propose to add, and which choices remain. Match the work to the request: an audit produces findings; setup proceeds to edits. For GitHub settings, check repository eligibility and follow `references/github-operations.md` and `references/security-reporting.md`.

## 2. Resolve the useful choices

These six topics cover a typical setup. Use `references/setup-questions.md` for suggested wording. Combine or omit questions based on the repository and conversation, and follow up as needed.

1. **Contributions:** Which kinds are welcome—code, documentation, ideas, or reports?
2. **Issue categories:** Which templates would help—bugs, suggestions, documentation, or a general report?
3. **Pull requests:** Would a short PR template be useful?
4. **License:** Use the maintainer's chosen license. If they want help, explain general facts and relevant differences; the selection remains theirs. An undecided license can be left for later.
5. **Code of conduct:** If wanted, establish the policy, a contact approved for publication, and who will handle reports.
6. **Security reporting:** Choose an available private reporting route and establish the support scope for a security policy. Explain who will monitor the route.

Read `references/license-and-conduct.md` or `references/security-reporting.md` as relevant. Unresolved policies can wait while other work proceeds. Keep drafts clearly distinguished from files ready to publish.

## 3. Prepare the files

Show a compact file plan with destinations and any public commitments, then implement the authorized work. A request to set up files authorizes those edits; use existing consent for delivery and settings as described in `references/github-operations.md`.

Default standalone documents to the repository root, issue templates to `.github/ISSUE_TEMPLATE/`, and a single PR template to `.github/pull_request_template.md`. Preserve supported existing locations and accommodate the user's preferences. Keep a new repository license at the root for GitHub detection.

Use `references/template-selection.md` for bundled options and `references/templates-and-validation.md` for adaptation and checks.

- **README:** Start with the project purpose and verified getting-started information. Expand or curate it according to the user's interest.
- **CONTRIBUTING:** Describe accepted contributions and the project's actual setup, checks, and contribution process.
- **Issue templates:** Start with short forms for the selected categories and blank issues enabled. Adapt fields and routing to the project's needs. Direct vulnerability details to a private channel.
- **PR template:** Start with the short variant and add detail where useful.
- **License and conduct:** Fetch the selected canonical text and preserve its required notices. Resolve an existing licensing conflict before replacing text.
- **SECURITY:** State the confirmed support scope and a working private route. If GitHub enablement is pending, keep that dependency clear before publication.
- **SUPPORT:** Include an established help route when useful.

The bundled issue, PR, and security templates under `assets/template-parts/variants/`, including our adaptations and additions, are dedicated under [CC0-1.0](LICENSE-CC0.txt). Users may freely use, copy, adapt, and redistribute them without attribution, notice-retention, or other licensing obligations. The plugin’s MIT license does not apply to these templates. Generated files need no credits or license notices for these templates. Separately sourced licenses and codes of conduct retain their own terms.

## 4. Validate and deliver

Review the diff and run `git diff --check`. Verify file locations, links, commands, contacts, and policy commitments, and resolve placeholders in files ready to publish. Validate changed issue-form YAML and its GitHub fields using `references/templates-and-validation.md`. State which checks were local and whether GitHub rendering was verified.

Complete the requested Git delivery and settings work using `references/github-operations.md`. If access is unavailable, explain the pending step and complete the independent work.

Finish with a brief account of the changes, validation, remaining decisions, and ongoing responsibilities.

## Further help

Use `references/community-standards.md` for checklist and score questions. Repository descriptions, moderation settings, shared account defaults, and deeper governance questions can be addressed as they become relevant. Follow the user's priorities and keep optional work from holding up the basic setup.
