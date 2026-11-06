# ADR 0002: List-based preview and interactive revisions

Status: implemented. The [application guide](../../plugins/badge-buddy/skills/ossf-bp-badges/references/application.md) now contains the operating instructions formerly maintained in `assessment-engine.md` and `automation-guidance.md`; the implementation table below preserves their names at the time of this decision.

Date: 2026-09-11. Prepared against `7416a10` on `release-hardening`.

## Decision and precedence

The preview is a passive reading surface for reviewing the assessment Claude has prepared locally. Overview remains the home/dashboard page with its existing layout of four response bucket cards plus an All criteria card. All criteria remains a separate page displaying every criterion in the selected badge section. Each of the four response bucket pages displays every criterion currently in that bucket. All criteria and the four bucket pages each include a table of contents for jumping within their full lists. The user chooses what to read and discusses revisions with Claude in the conversation.

During an interactive preview round, Claude revises a criterion's justification first and leaves its response unchanged while the user reviews the wording. Only after the user approves that wording does Claude change the response to the agreed value. A criterion that changes buckets then disappears from the original bucket on refresh, after the user has finished reviewing it there. The preview does not follow it to its new bucket.

This replaces conflicting decisions in [ADR 0001](0001-unify-assessment-views.md), the existing interaction protocol, and the current renderer. In particular, it overturns retaining the single-criterion queues, criterion-card self-links, and previous-bucket continuation. Preserve the consolidated renderer, passive preview, Overview dashboard layout, and separate All criteria destination. The All criteria page already provides the full list; its principal interaction changes are adding the table of contents and removing each criterion card's no-op link to itself.

The renderer, installed skill instructions, and browser checks implement this model together. The existing dashboard and separate All criteria destination are retained.

## Scope of the justification-first rule

The rule applies to revisions made **during an interactive preview round**, when the user is reading the locally prepared assessment and discussing changes with Claude. It does not impose a two-step approval process on initial assessment, bulk preparation before preview, or all controller updates. Those operations may still record a response and its justification together under their existing authorization.

Opening the preview for inspection does not by itself start a questionnaire or require approval of every existing answer. The user may browse freely, ask a question, request a revision, or stop. A question does not change the assessment, and navigating the preview does not approve anything.

## User flow

1. The user asks Claude to help with the badge. Claude performs the requested assessment work and records the resulting responses and justifications locally.
2. Claude explains what it prepared and opens the preview as part of the agreed review. The user can choose any bucket or All criteria from the Overview dashboard, then read in any order using that page's table of contents or ordinary scrolling. A request to preview all answers may open All criteria directly.
3. While reviewing an Unmet criterion, the user says it should be N/A and explains why. Claude works through any necessary clarification in the conversation and updates only the local justification. The stored response remains Unmet, so the refreshed preview still includes the criterion in Unmet.
4. The user reads the revised wording. If they request another revision, Claude updates the justification again and leaves the response unchanged. This continues for as many revisions as needed.
5. When the user approves the wording for the agreed N/A answer, Claude changes the response to N/A. It keeps the approved wording; it does not silently rewrite the justification at this step. The next refresh removes the criterion from Unmet and includes it in N/A. The user's selected view remains Unmet.
6. The user keeps reading or chooses another view. There is no redirect, continuation prompt, or instruction to follow the moved criterion. In All criteria, the same criterion remains in its original numerical position with its updated response. Overview reflects the updated bucket counts.
7. When the user asks to transfer the reviewed answers, Claude prepares the website edits through the supported submission path. Local wording approval does not submit the BadgeApp form. The user still reviews and saves/submits on BadgeApp unless they have explicitly authorized Claude to perform that separate action.

The same sequence applies to any proposed response change during the round, including changes involving `?`. A wording-only revision leaves the response unchanged throughout. A deferral or unrelated acknowledgment does not count as approval. When the conversation clearly establishes approval of the wording and intended response, proceed without asking for the same approval again.

## Views, navigation, and content

| View | Main content | Table of contents |
| --- | --- | --- |
| Overview | Home/dashboard with the existing four bucket cards plus All criteria | None; this page provides navigation and counts |
| All criteria | Every criterion in the selected badge section, fully expanded | Every criterion in that section |
| Met | All criteria whose current response is Met | Those same Met criteria |
| Unmet | All criteria whose current response is Unmet | Those same Unmet criteria |
| N/A | All criteria whose current response is N/A | Those same N/A criteria |
| ? — Not yet answered | All criteria whose current response is `?`, including unanswered entries | Those same unanswered criteria |

Overview and All criteria remain separate destinations. Preserve the dashboard's existing card layout and navigation to the five reading pages. All criteria and the four bucket pages use the same list layout and criterion presentation, filtered by the current response when a bucket is selected. Counts come from the assessment and catalog; the four buckets remain disjoint. All criteria is not a fifth response bucket.

Keep an Overview control available on every reading page so the dashboard's four buckets and All criteria remain reachable. Each reading page's table of contents lists criterion identifiers, with their canonical numbers, in the same order as the visible articles. Activating an entry scrolls to that article within the current list. It does not replace the list with one criterion. No pagination, collapsed article bodies, Next/Previous controls, or selected-criterion workflow is needed.

Each article displays its canonical number, identifier, official criterion text and details, current response, full justification, requirements, and evidence. Supporting evidence URLs remain usable source links. Remove navigation links from the criterion articles themselves, including the no-op “Link to this criterion,” “Continue in …,” and per-card Overview controls. Navigation belongs in the page controls and table of contents. This removal applies to criterion cards, not the dashboard's bucket and All criteria cards, which remain navigation controls.

An empty bucket stays selected and says, for example, “No Unmet criteria.” Its empty table of contents and the ordinary page controls are sufficient. Do not redirect the reader or manufacture a next item. All criteria includes unchanged and unanswered criteria as well as Claude's recent work; a before/after diff is not required by this decision.

Each generated preview continues to cover one requested badge section. “All criteria” means all criteria in that section, not a silent aggregation of Passing, Silver, Gold, and Baseline levels.

## Criterion order and identity

BadgeApp displays criterion identifiers, not printed sequence numbers. The preview's numbers identify positions in BadgeApp's full sequence for the selected section. The pinned catalog order was verified against all six live project sections; derive positions from that complete list before filtering. Use the same position in All criteria, bucket lists, and their tables of contents. Render in ascending canonical numerical order, preserving gaps in filtered views: for example, a bucket containing criteria numbered 12, 42, and 57 displays those numbers, never 1, 2, and 3. These numbers are illustrative, not verified assignments to particular criteria.

Keep the stable criterion identifier visible alongside the number for conversation and data lookup. Use that identifier, scoped to the badge section where necessary, for DOM anchor identity and stored answer keys. A display number is neither a new answer key nor a bucket position. Retain upstream Baseline display identifiers as applicable; do not replace them with locally invented ordinals.

The bundled catalog and upstream clone at `5b4cb83667d893707c8e07d8fd438604a30ba23a` have identical section order. Rendered project sections were also checked: Passing has 67 criteria, Silver 55, Gold 23, and Baseline levels 1–3 have 24, 19, and 21 respectively. These counts are verification evidence, not constants for the renderer. No new catalog field or generator change is needed. Preserve this order when refreshing the catalog; never derive numbering from a filtered list or lexical sort of identifiers.

## Refresh and removal of old navigation state

Retain the five-second automatic reload while the page is visible: Claude regenerates the local HTML, and the timer lets the user see revised wording without coordinating manual refreshes. Keep only the navigation state needed to select Overview or the current reading page. Retain the simple All criteria entry point, `#view=all`, and the distinction between Overview and All criteria. ToC links use ordinary page-scoped anchors such as `#view=unmet/interact`; the renderer reads only the page prefix and lets the browser navigate to the article. There is no selected-criterion or previous-bucket state. Ordinary in-page anchors serve table-of-contents scrolling; removing the old routing protocol does not mean removing the anchors that make quick navigation work.

Delete `previous_bucket`, the composite `bucket`/`criterion` routing that follows a moved criterion, `view=all&criterion=...` card permalinks, parameter-parsing machinery for those composite routes, queue-position bookkeeping, and continuation-target calculation. Remove the corresponding UI copy and browser assertions. No replacement query parameters, browser storage, hidden history, or “follow this criterion” feature should recreate that model. The retired composite routes need no compatibility layer.

After regeneration/refresh, preserve the chosen view. During justification review, the criterion remains in that view because its response has not changed. After approval changes the response, rebuild the source bucket's list, count, and table of contents normally. If its old anchor no longer has a target in that bucket, stay in the bucket; do not search other buckets. Preserve a useful reading position when feasible using ordinary browser behavior and minimal view-level handling. Do not add a criterion relocation subsystem to preserve exact pixels. Avoid repeated automatic refreshes that continually jump to the top or steal keyboard focus.

## Presentation plan

Use the existing restrained visual identity as the base. Correct the masthead from `repomonics.` to `reponomics.` and retain the product name “Badge Buddy.” The defining structure is the correspondence between the numbered table of contents and the fully readable assessment, with evidence kept next to the answer it supports.

Core color tokens, retained from the current stylesheet:

| Token | Value | Role |
| --- | --- | --- |
| Paper | `#f4f7f8` | Page and navigation background |
| Surface | `#ffffff` | Reading surface |
| Ink | `#14212b` | Main text |
| Muted | `#566672` | Secondary text |
| Rule | `#c9d3d9` | Useful content boundaries |
| Navy | `#173e55` | Navigation emphasis |

Retain the installed system sans-serif stack for a self-contained local document with no remote font dependency. Use approximately 16 px body text with generous line height, 20 px criterion headings, and 28 px view headings. Keep text left aligned and reading measure below roughly 80 characters. Identifiers are meaningful reference data, not decorative labels; numbering communicates the upstream sequence. Response text must remain legible without relying on color alone, and keyboard focus must be visible.

Keep Overview's existing dashboard layout of four bucket cards plus All criteria. On the five reading pages at desktop width, use a compact table-of-contents rail beside one continuous reading column. Place each criterion's evidence and requirements within its article, so there is no detached singleton evidence panel. On narrow screens, place the table of contents above the reading column and allow the page controls and identifiers to wrap. All articles remain present and expanded.

```text
reponomics. | Badge Buddy                  Project / badge section
Overview

[ ? bucket      ] [ Unmet bucket ]
[ N/A bucket    ] [ Met bucket   ]
[ All criteria                  ]

After opening a bucket or All criteria:

Back to Overview

Find a criterion             Unmet
12  identifier_a             12. identifier_a
42  identifier_b                 Official text and details
57  identifier_c                 Response: Unmet
                                 Justification, requirements, evidence

                             42. identifier_b
                                 Full criterion and answer

                             57. identifier_c
                                 Full criterion and answer
```

The wireframe's identifiers and numbers are schematic. Use actual catalog content during implementation and browser review.

Review against the brief: the dashboard's existing card layout is intentional and remains the home page. All criteria stays separate, gains the table of contents, and loses the redundant self-link on each criterion card. The four buckets adopt the same full-list reading composition. Keep the existing palette and type foundation; focus the redesign on navigation, canonical identity, and readable answers.

## Implementation concerns and boundaries

The interaction model is sound. The main concern is that justification-first editing temporarily pairs an old response with wording intended for a new one. That is expected during this review round. Claude should explain it once in the conversation, for example: “I've updated the justification; the response is still Unmet while you review it.” This does not require a new approval control or workflow in the preview.

Two controller concerns are resolved within the existing working-file flow:

- **Validation:** `apply --review-response <status>` accepts only justification fields and validates their wording against the intended response while storing the current response unchanged. Ordinary `apply` still validates the resulting pair, including the status-only update after wording approval. No validation rules are bypassed.
- **Transfer and interruption:** provisional revisions use an ordinary temporary copy of the controller-returned assessment. The open board reflects that copy, but the normal working file retains settled answers. After approval, finalize the response in scratch and apply the exact approved pair to the normal selection. Before pause, cancellation, or transfer, discard unfinished scratch and regenerate from the normal selection. Transfer uses only that normal selection. There is no new controller-managed draft store or approval framework.

These concerns are limited to unfinished revisions during interactive preview. They do not add a new approval gate to initial assessment or require revisiting already agreed answers. Existing repository writeback and BadgeApp submission authorization remain separate from approval of an individual wording revision.

## Implementation

| Area | Implemented change |
| --- | --- |
| `assets/review/index.html` | Correct the wordmark; retain the Overview dashboard and separate All criteria page; add a table of contents to All criteria and full lists to bucket pages; remove criterion-card navigation links |
| `assets/review/review.js` | Keep dashboard navigation; use one renderer for All criteria and the filtered bucket lists; remove queue/relocation routes and continuation logic; preserve the selected view on refresh |
| `assets/review/review.css` | Retain the dashboard card layout; support the table-of-contents rail and continuous reading column at desktop and narrow widths; remove obsolete queue/singleton styles |
| `scripts/ossf_review/board.py` and the bundled catalog | Preserve the verified full section order, stable answer identifiers, and bucket semantics; compute display positions before filtering in the renderer |
| `scripts/ossf.py` | Preserve the distinct Overview and All criteria entry points; resolve provisional validation and transfer concerns with the smallest necessary change |
| `skills/ossf-bp-badges/references/assessment-engine.md` | Own the revised interaction protocol and simple preview navigation; explicitly scope justification-first revisions to interactive preview rounds |
| `skills/ossf-bp-badges/references/automation-guidance.md` | Explain how unfinished interactive revisions are excluded from website transfer |
| `skills/ossf-bp-badges/SKILL.md`, plugin `README.md` | Update entry-point and user-facing descriptions; link to the shared protocol rather than duplicating it |
| Board, controller, catalog, and browser checks | Replace assertions for obsolete navigation with behavior checks for the new design |

Paths in this table are relative to `plugins/badge-buddy/`, except the tests under `tests/badge-buddy/`. Preserve `review --view overview|all`: `overview` remains the default dashboard destination, while `all` opens the separate All criteria page directly. Natural-language requests to preview all answers can continue to use `review --view all`.

## Acceptance criteria for implementation

1. Ordinary `review` opens the Overview dashboard with its existing four bucket cards plus All criteria. All five cards open their respective reading pages. `review --view all` opens All criteria directly, with every criterion fully expanded and a matching table of contents. Each bucket contains every and only its current entries, fully expanded with its own matching table of contents and the same article layout.
2. Every article and table-of-contents entry has its position in the verified full BadgeApp sequence and stable display identifier. Filtering leaves numerical gaps; changes of response do not renumber a criterion. Verify supported section boundaries rather than testing only Passing.
3. Table-of-contents entries scroll within the current list. Criterion articles contain no preview-navigation links, including links to themselves. The Overview control returns to the dashboard, whose bucket and All criteria cards still navigate normally. No singleton or Next/Previous navigation remains.
4. During an interactive Unmet-to-N/A revision, multiple justification edits appear in Unmet while the response and bucket counts stay unchanged. User approval changes the response using the exact approved wording; the next refresh removes the article and its table-of-contents entry from Unmet without switching views. All criteria retains the article in its canonical position, and Overview reflects the updated counts.
5. Initial assessment can still record response and justification together. Inspecting the preview, asking questions, and deferring an answer do not trigger edits or new approval requirements.
6. Cover the provisional-validation edge case, interrupted/canceled review, and attempted transfer of unfinished wording. No unapproved provisional pair is represented as ready for BadgeApp; completed approved answers still use the existing submission paths.
7. An empty bucket remains selected after its last item moves. Ordinary refresh does not continuously reset the reader or steal focus. Check actual generated HTML at desktop and narrow/mobile widths, keyboard table-of-contents navigation, long identifiers, and the last article in a long list.
8. Preserve safe rendering of untrusted criterion/answer text and usable evidence links. Verify the corrected wordmark. Replace old route-specific browser expectations, run the focused browser checks and `make check` using `venv`, and report only checks actually performed.

## Verification

`make check` passed all 148 tests and Python compilation. The generated-page browser checks passed at 1440, 600, and 375 px, including full bucket lists, ToCs, stable positions, text escaping, evidence links, keyboard focus and scroll restoration, two successive justification revisions, an approved bucket move, and an empty bucket across the retained five-second reload. Additional browser checks verified the full list and final ToC target in all six badge sections.

Controller tests cover the provisional Met-to-N/A validation case, ordinary validation afterward, exact approved wording, export from the settled assessment, and restoring the same preview file after discarding an unfinished revision. Browser tests serve the generated static fixture locally to replace responses during refresh checks; the plugin still opens a self-contained file and has no server dependency. No live BadgeApp write was performed.
