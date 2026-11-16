# Badge Progress

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../../docs/assets/badge-progress/badge-progress-dark-840x240.png">
  <img alt="Badge Progress: See your badge work take shape" src="../../docs/assets/badge-progress/badge-progress-light-840x240.png" width="840">
</picture>

Badge Progress tracking is paused while [Badge Buddy](../badge-buddy/README.md) migrates from its old BadgeApp CLI to best-practices-mcp. The `/badge-progress` pane now shows a transition notice instead of restoring potentially stale controller counts. It does not intercept MCP calls or resume the removed CLI.

Ask Badge Buddy to open its local preview board to review answers. That board remains available for Passing, Silver, Gold and Baseline levels 1–3.

## Follow-up work

An MCP-aware progress pane needs a separately reviewed event adapter. It must use the host's documented MCP tool-result events, bind state to the selected BadgeApp project, distinguish saved website observations from caller-owned drafts, and derive counts from the appropriate catalog. `build_draft` has no selected badge level, while `update_draft` returns a patch rather than a complete document; neither can safely be treated as the old controller's full assessment snapshot. Evidence-gap checks and website/draft differences also need explicit semantics.

This suspension avoids presenting stale counts as current progress. Existing persisted state is left untouched but is not read or displayed. No progress band or completion toast is emitted.

## Development

```sh
claude plugin validate plugins/badge-progress
claude plugin test plugins/badge-progress
```
