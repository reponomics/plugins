# Verification and completion

Keep a baseline of files and settings before edits. Preserve unrelated changes, comments, triggers, job IDs, conditions, and action inputs. Use focused patches or a round-trip YAML editor; avoid serializers that turn the YAML `on` key into a boolean or discard comments.

After edits:

1. Re-inventory the selected files and reachable local dependencies. Check external SHA length, upstream commit identity, action subpath, and same-line version label. Report intentional exceptions and inaccessible dependencies.
2. Review the effective permission map of each affected job, including required reads and reusable-workflow callers. Confirm that each remaining write has a stated operation and that separately supplied credentials have not been mistaken for GITHUB_TOKEN.
3. Run the project's existing workflow checks. If `actionlint` is available, run it on the affected workflows; inspect action metadata separately for composite actions. YAML parse success alone does not establish GitHub workflow validity. Report an unavailable validator without claiming it ran.
4. Check update configuration coverage and allowlist compatibility for every changed external reference. Compare policy proposals to actual inventory, including currently active release branches when enforcement is in scope.
5. Inspect relevant GitHub workflow runs when available. Distinguish static validation, successful execution, and jobs skipped by event/branch conditions. Do not trigger a release, publish results, deploy, or merge a PR merely to test maintenance changes without authorization for those effects.

For Scorecard-originated work, return to the saved baseline and remeasure using comparable acquisition mode, credentials, check set, and tool version. Report actual check changes and measurement limitations; do not infer a score from lint success. For standalone work, no Scorecard installation or measurement is required.

Finish with changed files, selected action versions, permission changes and their operational reasons, update responsibility, settings applied or deferred, checks actually run, and unresolved limitations. Do not equate a proposed setting with a saved setting or a green lint result with a successful deployment.

Make the maintenance handoff actionable: state the accepted recurring responsibilities, their owner, and the next action or trigger. For update PRs, explain what to review and which checks should pass before merging; include credential renewal or allowlist updates only when the selected setup requires them. Keep conceptual education optional.
