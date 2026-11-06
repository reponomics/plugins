# Workflow Guard

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../../docs/assets/workflow-guard/workflow-guard-dark-840x240.png">
  <img alt="Workflow Guard: Keep workflows on track" src="../../docs/assets/workflow-guard/workflow-guard-light-840x240.png" width="840">
</picture>

Workflow Guard checks the GitHub Actions workflows Claude writes or edits, and stops a change that would weaken them in two ways that OpenSSF Scorecard measures:

- **Pinned-Dependencies:** a new `uses:` reference to an external action or reusable workflow that is not pinned to a full 40-character commit SHA.
- **Token-Permissions:** a workflow that ends up without a top-level `permissions:` block, or whose top-level block newly grants write access (`write-all`, or a scope set to `write`).

When a change is stopped, Claude is told which line is affected and how to fix it, and can try again straight away. Only problems the change introduces are reported. Existing unpinned actions or a missing block in a file Claude is editing for another reason are left for you to address, for example with Badge Buddy's `github-workflow-maintenance` skill.

It is a mod: a plugin that changes Claude Code's behaviour through function hooks rather than adding skills.

## Get started

```sh
claude plugin marketplace add reponomics/plugins
claude plugin install workflow-guard@reponomics
```

There is nothing else to set up. The guard applies to files in `.github/workflows/` and to composite actions (`action.yml`); composite actions are checked for pinning only.

## Choosing the top-level permissions

Both `permissions: {}` and a read-only block such as `permissions:` with `contents: read` satisfy the guard. A permissions map sets every scope it does not list to `none`, so the two differ only in read access to the repository's contents:

- `contents: read` is the usual choice, because `actions/checkout` needs it in private and internal repositories.
- `permissions: {}` suits workflows where no job reads the repository through `GITHUB_TOKEN`, or where every job declares its own permissions, so that a job added later starts with none.

Write scopes belong on the jobs that need them.

## Exceptions and settings

When you want something the guard would stop, tell Claude so. It can mark the exception in the file:

- `# workflow-guard: allow` at the end of a `uses:` line or the `permissions:` line.
- A `# workflow-guard: allow-permissions` comment line anywhere in the workflow, to skip the permissions check for that file.

To leave a file or a whole directory unchecked without changing it, use the ignore list:

```text
/workflow-guard ignore .github/workflows/bad-example.yml
/workflow-guard unignore .github/workflows/bad-example.yml
/workflow-guard list
```

Relative paths are resolved against the session's working directory, and a directory covers everything under it. The list is kept in the plugin's own store under your Claude Code configuration directory, so it is per user and not part of the repository. Only a command you type adds to it: when Claude or another plugin runs `/workflow-guard ignore`, it is refused. Anyone can remove entries, since that only turns checks back on.

A deliberately bad example, for teaching or documentation, is usually better kept outside `.github/workflows/` (for example in `docs/examples/`), where GitHub does not run it and the guard does not check it. Use the ignore list when the example has to live where the guard looks.

The **Mode** setting (in `/config`) is `block` by default. Set it to `warn` to let changes through and only add the findings to the result Claude reads.

## Limits

The checks read the YAML line by line, which covers the block and flow styles workflows normally use, but not every construct YAML allows. Changes made outside Claude's Write and Edit tools, such as a shell command that rewrites a file, are not checked. The guard does not verify that a SHA exists or matches its version comment.

## Development

```sh
claude plugin validate plugins/workflow-guard
claude plugin test plugins/workflow-guard
```
