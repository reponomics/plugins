# Badge Buddy MCP migration

Date: 2026-11-16. Implementation branch: `codex/badge-buddy-mcp`, based on `origin/main`. The existing code-scanning/release work branch is preserved separately.

## Plan and review

Replace Badge Buddy's duplicate BadgeApp transport and draft controller with the published `best-practices-mcp==0.5.0` stdio server. The plugin remains responsible for advisory material, interpretation, user interaction, peer review, project improvements, and the passive local preview board. The MCP owns project discovery, public reads, mechanical document checks, optional server drafts, and proposal URL generation. Browser review and saving remain user-controlled.

The plan was reviewed before implementation. Review retained the following boundaries:

1. Register the pinned server in the plugin and document `uvx` and Python prerequisites. Use discovered MCP tool names; do not assume identical prefixes across hosts.
2. Make caller-owned explicit documents the ordinary workflow. Server-managed drafts remain optional, and no plugin path is silently repurposed as the MCP data directory.
3. Remove the BadgeApp CLI, local synchronization engine, proposal implementation, and console-fill generator. Preserve Scorecard by extracting its shared GitHub remote normalizer.
4. Retain all advisory reference documents, the bundled display catalog and examples, and the local board assets. Add a small offline renderer accepting an explicit assessment file, output path and section; exercise every badge level.
5. Explain how to reuse existing assessments without automatic migration or silent conflict resolution. Preserve source files and existing answers, including unknown and empty values.
6. Update relevant tests and installation/application documentation. Retire tests for the deleted implementation; retain board, catalog, alias, Scorecard and maintenance coverage.

No release is published by this migration. The current plugin manifest version is left for the maintainer's release decision. The independently released MCP dependency is pinned to 0.5.0.

## Expected review and verification

Run the offline plugin and maintenance suites, source compilation, JSON/Markdown checks, README tree validation and plugin manifest validation. Exercise the board entry point across all six levels and inspect that no CLI BadgeApp network or console-script transfer path remains. A host installation/reload is still needed to qualify automatic MCP registration in a real host; offline configuration checks do not establish that result.

## Dependent progress mod

Review found that `badge-progress` consumed the deleted controller's Bash output and restored cached counts. Its tracking is explicitly suspended in this migration: the pane shows a transition notice, and old counts are neither restored nor displayed. The local board remains available. A future adapter needs documented host MCP events, project-bound state, catalog-aware counts, separate saved/draft semantics, and a defined strategy for patch-only update results. This is preferable to a silent regression or an invented fallback to the removed CLI.

## Verification record

The offline `make check` run passed 180 tests across badge-buddy (72), starter-buddy (17), release-buddy (1), and maintenance (90), then compiled the Python sources. The board CLI tests cover all six levels and preserve the input file. Both badge-progress suspension tests passed, including a check that persisted counts are not read. `claude plugin validate` passes for badge-buddy and badge-progress, with existing missing-icon warnings; the paused mod also receives advice about an omitted install example. Formatting hooks and the README tree check pass. The pinned command reports `bestpractices-mcp 0.5.0` after refreshing uv's package index cache.

The Scorecard helper's only semantic change is importing the extracted remote normalizer; the repository's required formatter also reformats the existing file. No criteria text, board assets or other advisory skill functionality was removed. The deleted tests exercised the retired duplicate BadgeApp implementation; retained behavior has board, alias, Scorecard, catalog and integration/configuration coverage.

Independent implementation review caught a numeric board label that could disagree with the draft’s `id`. The renderer now rejects mismatches before creating or replacing HTML; tests cover mismatches, matching IDs, id-less drafts and explicit local labels.
