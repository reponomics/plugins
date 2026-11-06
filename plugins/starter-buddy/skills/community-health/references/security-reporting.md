# Security policy and repository reporting settings

Use the security intake answer and existing repository policy. Keep three related controls distinct:

1. `SECURITY.md` tells people what is supported and how to report vulnerabilities. It is a visible Community Standards row.
2. Private vulnerability reporting provides a confidential GitHub form. It is useful but not score-bearing.
3. Reported content lets contributors report disruptive community content to repository administrators. For a qualifying organization-owned public repository, it is score-bearing but unrelated to vulnerability disclosure.

## Choose a policy and explain its commitments

Use the bundled options: [one supported line](../assets/template-parts/variants/security/single-line.md) or [explicit maintained versions](../assets/template-parts/variants/security/maintained-versions.md). Choose by the maintainer’s actual support policy, independently of how detailed their issue forms are. A small project may support several releases; a busy project may support only one.

Before adoption, show the filled policy and make its commitments plain: the maintainer will monitor the named private route and maintain security fixes for the stated versions or branch. Neither option commits to a response deadline, bounty, disclosure timetable, or a fix for every report. Add such terms only when the maintainer has chosen them.

Use decisions already given in the conversation and ask for missing details as needed. Help the maintainer explore options or draft a policy if useful. Keep unresolved drafts clearly distinguished from policies ready to publish, and continue the other files when security decisions are deferred. Preserve an existing policy unless its revision is part of the request.

## Build an honest SECURITY policy

Resolve two facts before finalizing the file:

- **Supported versions:** Identify maintained releases, branches, or an honest pre-release/default-branch policy. Tags identify releases but do not establish a maintenance commitment.
- **Confidential reporting route:** Name a channel that exists and is monitored. Prefer private vulnerability reporting when the maintainer has enabled and accepted responsibility for it; otherwise use a confirmed security email address or established private intake.

Keep the starter policy concise:

- thank reporters;
- list supported versions or state the current support policy;
- link or name the confidential reporting route;
- ask for a description, impact, reproduction details, and relevant version information;
- ask reporters not to disclose the issue publicly while coordination is underway; and
- set expectations only where the maintainer has approved them.

Include response deadlines, bounty terms, disclosure schedules, or similar expectations when backed by an actual process the maintainer has accepted. Direct vulnerability details to the private reporting route.

Use GitHub's [security-policy guide](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/add-security-policy) and the [Open Source Guides security guide](https://opensource.guide/security/) for current context.

## Private vulnerability reporting

When private reporting is selected or the user asks about it, explain the practical effect briefly:

> Private vulnerability reporting gives security researchers a confidential GitHub form. It does not affect the Community Standards score, and enabling it creates an inbox that repository administrators or security managers need to monitor.

Eligibility and authority:

- The target must be a public repository.
- The actor needs repository admin authority to enable it.
- The reporting route is separate from `SECURITY.md`; use both when selected.

For a private repository, use a confirmed private contact or leave the policy pending. GitHub enablement can follow publication. Changing repository visibility requires its own authorization; a published policy needs a working reporting route.

Read the current state with the documented endpoint:

```sh
gh api repos/OWNER/REPO/private-vulnerability-reporting
```

The response contains `enabled: true` or `enabled: false`. Use the user’s existing authorization to enable this setting. Enable it with:

```sh
gh api --method PUT repos/OWNER/REPO/private-vulnerability-reporting
```

Read the state again after the mutation and report the before/after values. If authentication, permission, or eligibility is missing, provide GitHub's UI route from the current [configuration guide](https://docs.github.com/en/code-security/how-tos/report-and-fix-vulnerabilities/configure-vulnerability-reporting/configure-for-a-repository) and leave the setting pending.

Disabling private reporting is a separate change that requires the maintainer’s authorization.

## Consent and privacy

Use the authorization guidance in [GitHub operations](github-operations.md) for setting changes.

Before writing or publishing, scan for:

- personal email addresses not explicitly approved for publication;
- internal issue trackers, chat links, or security URLs;
- placeholder contacts;
- public vulnerability routes; and
- operational promises the maintainer did not make.

Resolve those details before treating the policy as ready to publish. Explain what remains pending and continue independent work.
