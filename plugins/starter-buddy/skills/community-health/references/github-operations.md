# GitHub delivery and verification

Deliver the work in the form the user requested: local edits, a commit, or a pull request. Files whose decisions are settled can be delivered while other items remain pending.

## Authorization

Use the conversation and repository instructions to establish the target and scope. “Set up the files and open a PR” authorizes the necessary edits, branch, commit, push, and PR steps. An audit or explanatory question calls for findings or an answer. Ask about missing scope when it matters, and use authorization already given.

Repository settings have their own effects: a description changes public metadata, private vulnerability reporting opens a confidential inbox, and reported content opens a moderation queue. Explain the relevant effect and obtain any missing authorization. One clear request can cover several settings; a file-setup request alone does not establish consent for them. Merging, changing repository visibility, and destructive Git operations likewise need authorization covering those actions.

## Prepare and deliver the change

1. Establish the repository root, working branch, default branch, and remote target.
2. Preserve unrelated working-tree changes and useful existing community files.
3. Use the repository’s branch and commit conventions when creating a branch or commit.
4. Make the changes needed for the agreed scope and run the checks in `templates-and-validation.md`.
5. Review the diff, including public contacts and policy commitments, and summarize the result.
6. Complete the requested commit, push, or PR workflow. Check the destination and the absence of secrets or internal information before publishing.

For a PR, describe the files changed, relevant policy choices, validation, and any remaining decisions or settings. Distinguish delivered files from work expected after merge. Use [Community Standards](community-standards.md) for score interpretation and estimates when relevant.

## Repository description

Use a short, factual sentence reflecting the project. When updating the description is authorized, apply it with the supported GitHub CLI or API and read it back. Other metadata and settings can be handled when included in the requested scope.

## Organization reported content

For qualifying public organization repositories, reported content is a setting separate from the community files. Follow [security reporting](security-reporting.md#reported-content-for-organization-repositories) for its effects and configuration.

If a supported write API or authorized UI control is unavailable, give the administrator the current Settings path and the pending action. Verify the result through the Community Profile response and UI when accessible.

## Post-merge verification

When checking live Community Standards results:

1. Confirm that the changes reached the default branch.
2. Fetch `GET /repos/{owner}/{repo}/community/profile` where supported.
3. Inspect **Insights → Community Standards** for information omitted from the API’s `files` object.
4. Check `content_reports_enabled` when the organization moderation row applies.
5. Verify any requested private vulnerability reporting change separately.
6. Allow for GitHub’s refresh delay before retrying a stale result.

Report the observed state: PR open, merged and awaiting refresh, remaining unrecognized items, or GitHub’s confirmed result. Basic file setup can finish with its local validation and delivery status; live verification can follow when relevant and available.

## Handoff when permissions are missing

Identify the repository, pending action, observed state, and permission needed, with official instructions for completing it. Continue independent work using the access already available. Credentials and token values belong in the service’s authentication flow, not in the conversation.
