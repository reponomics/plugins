# ADR 0001: Replace the separate preview with an All criteria board view

Status: implemented; interaction model superseded by [ADR 0002: List-based preview and interactive revisions](0002-list-based-preview-review.md).

ADR 0002 takes precedence wherever this document conflicts with it, including single-criterion category queues, criterion-card permalinks, and previous-category continuation. The Overview dashboard with four bucket cards plus All criteria, and the separate All criteria destination, remain in place. This document remains the historical record of consolidating the renderers; its superseded interaction requirements must not be restored.

Date: 2026-09-10. Prepared against `4cb286b` on `release-hardening`.

## Decision

Add **All criteria** as a fifth navigation option on the existing assessment board. It displays every criterion in the selected badge section, fully expanded in one long vertical column, in official catalog order. Remove the separate static preview implementation and its controller command. Requests to “preview” answers use the board’s All criteria view.

The implementation plan below records the original decision. For current operation, use the [application guide](../../plugins/badge-buddy/skills/ossf-bp-badges/references/application.md); ADR 0002 supersedes the interaction details noted above.

## Context

The board is a self-contained HTML file with embedded styles, script, and assessment data. Its overview currently offers four answer categories: Not yet answered, Unmet, N/A answers, and Met answers. Each category opens a queue and one criterion’s details. The board has already received the maintainer’s visual refinements.

The `preview` command independently renders a long HTML list using a different stylesheet. It includes all criteria in its selected section or sections; it is not a changeset or before/after comparison. Maintaining the two renderers duplicates presentation work and lets their appearance and behavior drift.

The board payload already contains the selected section’s complete ordered `criteria` list, `answers`, four disjoint `buckets`, and `total`. The new view needs no additional assessment data or storage model.

## User-visible behavior

- Add an All criteria card alongside the four existing category cards. Show the selected section’s total and describe it as the place to read all criteria and answers together.
- Display every criterion once, in official order, irrespective of its answer category. “All” means all criteria in this badge section, not all badge levels combined and not only changed answers. For Passing, the current total is 67; derive counts from the catalog rather than hard-coding them.
- Expand the criterion description, additional official details, current answer, justification, requirements, evidence links, and conversation reference in each article. Use the existing board terminology, including `? — Not yet answered` and the separate empty-justification explanation.
- Use a single column at desktop and narrow widths. Keep the existing masthead, restrained colors, typography, and spacing conventions. Place each criterion’s evidence and requirements within its article rather than repeating the three-column queue layout down the page. No accordions or pagination are needed.
- Provide an Overview control and a link/anchor for each criterion. Existing category queues and their “Continue in …” behavior remain available.
- Preserve the All criteria view across automatic refresh. A selected criterion anchor must still identify that criterion after its answer changes category. Keep scrolling usable during refresh; verify normal browser scroll restoration in the actual generated page before adding any small UI-only restoration code. Exact pixel restoration is not a new product requirement.
- Keep the board passive: navigation does not change assessment answers, send a message, start an agent turn, or save anything on BadgeApp. JavaScript continues to handle navigation and refresh.

## Implementation contract

### 1. Keep views separate from answer categories

Do not add an `all` bucket to `ossf_review/board.py`’s `_BUCKETS` or duplicate every criterion in the classification payload. The four categories must remain disjoint and continue to drive counts. Render the fifth navigation card from the existing `total`, and render its articles from `assessment.criteria` with answers looked up by identifier.

Use `#view=all` for the combined view and `#view=all&criterion=<identifier>` for a criterion link within it. Keep the current `bucket`, `criterion`, and `previous_bucket` fragments for ordinary category navigation. Dispatch the `view=all` case before the current category-resolution logic: a criterion becoming Met must not eject the reader from All criteria into the Met queue. Ignore category-continuation state in All criteria. An unknown criterion in an All criteria link should fall back to the start of that view.

### 2. Share criterion rendering

Refactor `renderCriterion`, `renderRequirements`, and `renderEvidence` in `assets/review/review.js` so the single-criterion view and the long column share the relevant rendering functions. Pass an explicit target element or element group instead of having those functions depend exclusively on the current global singleton elements.

A small reusable template or DOM-building helper is sufficient. Do not introduce a frontend framework or maintain a second set of copied criterion markup and rendering rules. Repeated articles need unique anchors and valid heading/label associations; do not clone the current singleton IDs across every article.

Continue assigning untrusted criterion/answer text with safe DOM text APIs. Preserve justification whitespace and the current evidence-link parser, including Markdown autolinks and bare-URL punctuation handling. Do not change criterion interpretation or HTML-to-text conversion as part of this feature.

### 3. Open the combined view through the existing controller

Add `review --view overview|all`, defaulting to `overview`. `--section` remains a single badge section and keeps its current default. `--no-browser` remains supported. For `--view all`, both the returned `url` and the browser-open target must include `#view=all`.

Keep the existing `review_written` result and the existing generated-board path/lifecycle. View selection belongs in the URL; it does not need a new assessment field, registry record, generated-file family, server, or session subsystem. Existing global `--assessment-file` selection must work unchanged.

Delete the `preview` subcommand, its parser arguments and dispatch branch, and its `write_preview` import. There is no compatibility alias, deprecation shim, migration, or fallback renderer: this is a pre-public-release simplification. Natural-language requests to preview remain supported by the skill, using `review --view all`.

The retired preview could combine multiple badge sections in one file. This feature intentionally keeps the board’s one-section model. For a user who wants to inspect several sections, open each requested section’s board rather than silently defaulting to Passing or adding an all-level rendering mode.

### 4. Remove the old renderer without breaking the board

`ossf_review/board.py` currently imports `plain_text` from `ossf_review/preview.py`. Move `plain_text` and its `_TextExtractor` helper into `board.py` before deleting the preview module; the board is their remaining production consumer. Preserve their behavior. Recheck imports before choosing a different destination if another consumer has appeared since this ADR.

Remove the preview-only HTML/CSS, render/write functions, obsolete imports, and command branches. Keep the bundled criteria catalog, its generator, board payload classification, and all submission/export functionality.

### 5. Update the skill and public documentation

Document one board with category views and an All criteria view. Replace instructions to generate an inert, JavaScript-free preview with instructions to open the All criteria board view. Explain that it shows all current answers in the selected section, not a changeset.

Keep “preview” as normal user vocabulary and in appropriate trigger descriptions. Remove claims that a separate `preview` command or no-JavaScript rendering path exists. Keep detailed command instructions in one reference and link to them through the skill’s task-specific reading map; do not reintroduce repeated procedures.

Preserve the agreed persistence protocol: private plugin storage by default; repository-backed work uses an ordinary temporary working copy unless direct edits are authorized. Showing the board does not apply that copy to the repository. User agreement and checking the unchanged repository original are still required before writeback. The board does not become a changeset viewer or an approval mechanism.

## Files to inspect and change

| File | Responsibility |
| --- | --- |
| `plugins/badge-buddy/assets/review/index.html` | Fifth navigation destination, combined-view container, shared article template if used |
| `plugins/badge-buddy/assets/review/review.js` | View routing, All criteria rendering, shared criterion/evidence rendering, refresh selection |
| `plugins/badge-buddy/assets/review/review.css` | Fifth overview card and single-column article layout at desktop/narrow widths |
| `plugins/badge-buddy/scripts/ossf_review/board.py` | Preserve payload semantics; receive the text-conversion helper |
| `plugins/badge-buddy/scripts/ossf_review/preview.py` | Remove after moving the helper |
| `plugins/badge-buddy/scripts/ossf.py` | `review --view`, returned/browser URL fragments, removal of `preview` |
| `tests/badge-buddy/test_board.py` | Board data/rendering coverage and appropriate new behavior checks |
| `tests/badge-buddy/test_ossf_cli.py` | Review view selection and working-file integration; retire preview command tests |
| `tests/badge-buddy/test_criteria_preview.py` | Preserve `CriteriaCatalogTests`; remove preview-only tests/helpers/imports and rename to `test_criteria.py` |
| `plugins/badge-buddy/README.md` | One UI, view descriptions, controller operations and examples |
| `plugins/badge-buddy/skills/ossf-bp-badges/SKILL.md` | Preview request routing and reading-map links |
| `plugins/badge-buddy/skills/ossf-bp-badges/references/assessment-engine.md` | Board operation and repository-review instructions |
| `plugins/badge-buddy/skills/ossf-bp-badges/references/automation-guidance.md` | Pre-submission review through the combined board view |

Search other active plugin docs/examples for references to the retired command. Leave historical review notes and screenshots alone. Do not treat every occurrence of the English word “preview” as obsolete.

## Acceptance and verification

1. Render a mixed-answer assessment containing `?`, Met, Unmet, and N/A. All criteria appears as the fifth option; its article identifiers equal the ordered catalog identifiers exactly, without omissions or duplicates. The original four counts still sum to the total.
2. Exercise the actual JavaScript: enter All criteria, follow a criterion anchor, return to Overview, and use an existing category queue. Regenerate with that criterion in a different category and reload: the All criteria URL remains selected and the updated answer appears. Existing single-criterion selection and previous-category continuation still work.
3. Verify in a real browser at desktop width and approximately 600 px that the column is readable, the final criterion is reachable, and refresh does not repeatedly send the reader back to the top. Check article anchors, headings, and keyboard navigation.
4. Verify `review --view all --no-browser` returns the correct URL without opening a browser, and ordinary `review` still opens Overview. Include a temporary `--assessment-file` case: the board reflects its answers, the repository original remains unchanged, and no private answer copy is created.
5. Preserve hostile-text escaping coverage and actual catalog/classification checks. Replace obsolete preview tests with a few meaningful board/CLI behavior checks where needed. Do not add assertions that merely search source code or prose for required words, CSS declarations, or helper names.
6. Run `make check` with the existing `venv`. Use the available browser/Node tooling for the focused JavaScript and browser checks; prefer extending an existing behavioral harness if one exists by implementation time. Do not install a large test framework just for this change.

On completion, report what changed, the checks actually run, the removed preview surface, and the new board URL for inspection. Commit conventionally on the intended working branch, respecting existing changes. No live BadgeApp write is required for validation.

## Scope boundaries and consequences

This removes one renderer and stylesheet while adding a small view to the existing board. It does not add a changeset/diff feature, editable controls, all-level aggregation, new storage, automatic repository writeback, a draft lifecycle, or a new deployment service. Attribution/footer completion and other release TODOs remain separate work.

The combined view requires the board’s JavaScript and follows its refresh behavior. The separate inert snapshot and its custom output/title/multiple-section options are deliberately retired. The benefit is a single presentation system for reading assessment answers, with consistent styling and one place to maintain future display changes.
