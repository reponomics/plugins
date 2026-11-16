# Working with the BadgeApp application

Use the plugin's registered `bestpractices` MCP server for BadgeApp discovery, reads, document checks, optional draft persistence and proposal generation. Use host file tools for caller-owned drafts and the separate local renderer for previews. The server does not authenticate to BadgeApp or save website changes.

## Start or resume

1. Resolve the repository from the user's request and session context. Call `find_project(query=<repository URL or known ID>)`, inspect the candidates and explicitly select the intended existing project. Do not silently choose among ambiguous matches. No matching entry means registration is needed for project-bound application work; registration itself happens on the website.
2. Call `get_project_progress(project_id, level)` for the selected section's saved answers and `get_criteria(level)` for its complete criteria. Keep source/fetch metadata with the working context. The criteria catalog is pinned; it is not a live scrape.
3. Choose the working draft. Prefer an existing user-selected assessment, including a repository file. Otherwise initialize a caller-owned flat document from the saved `answers`, adding the selected project's `id` and verified `repo_url` as provenance. `build_draft(draft=<document>, changes=<changes>)` creates or revises an explicit document without writing files. Follow the discovered schema for exact argument names and result fields.
4. Compare saved answers with an existing draft before reconciling differences. Preserve intentional local values, including `?` and empty justifications. Explain substantive differences and resolve them with the user's instructions; fetching a project does not automatically merge or persist anything.

Refresh saved progress after a website save, when the project changes, or when intervening website edits matter. Keep the selected project ID in each project-bound call. Preparing a proposal is not a save, and validation does not establish the truth of a claim.

### Existing plugin drafts

The retired controller stored assessments at `projects/<id>/.bestpractices.json` beneath the host's plugin-data directory, or in a user-selected repository file. Those files remain usable as caller-owned documents. Locate them from the established session/host configuration, read the selected file, confirm its project association, and pass its contents explicitly to the MCP. Do not delete the old files, copy the old registry into MCP storage, or silently merge them with a newly fetched project.

### Optional MCP storage

Only `update_draft` creates or patches server-managed files. Use `read_draft` to resume an existing stored document. An explicit `draft`, including `{}`, bypasses storage for validation and proposal generation; omitting it reads the selected project's stored draft. The storage root belongs to the server's filesystem and is configured through `BESTPRACTICES_DATA_DIR`; do not assume it is the plugin-data directory. Follow the server's documentation for platform defaults and overrides. Avoid concurrent writers; after an uncertain update, read before retrying.

Explicit documents are sufficient for the entire normal workflow. Do not require optional server storage merely to use the skill or preview a board.

## Repository assessments

Check for an existing `.bestpractices.json` or `.project.d/bestpractices.json` only in the selected project. Prefer the user's established file and instructions. Normally work on a temporary copy so the user can review changes before repository writeback; direct edits are appropriate when requested. Remember the original contents and check for intervening edits before applying the chosen changes back. Never overwrite unrelated fields or a changed file blindly.

## Record answers

Read the justification-style guide and complete the requested peer review before presenting drafted application text. Use `build_draft` with explicit draft and changes documents, then save the returned document using host file tools. If the user chose server-managed persistence, use `update_draft(project_id, changes=<patch>)` instead. Preserve omitted fields; use the tools' documented patch semantics rather than inferring deletion behavior.

Call `validate_draft(project_id, level, draft=<working document>)` to check mechanical requirements for the selected section. Explain useful findings and correct accidental mistakes. Validation is advisory: the user controls their answers, and the validator cannot assess whether a project practice or explanation is true. Unknown answers can remain unknown.

## Preview

The local board remains a plugin feature, not an MCP tool. It renders caller-owned JSON without fetching, changing answers, or saving to BadgeApp. Resolve the renderer path from the skill and run it with Python 3.11 or newer:

```bash
python3 "<board-renderer>" --input "<working-file>" --output "<board-html>" --project-id "<selected-id>" --section baseline-1 --view all
```

The command reports the local HTML URL. Open it with the host's normal browser/file capability when the user requests a preview, or add `--open` when appropriate for that host. Use `passing`, `silver`, `gold`, or `baseline-1` through `baseline-3` as the section. `--view overview` opens the category view; `--view all` opens all criteria. For pre-registration advisory work, a local label can replace the project ID in the board only.

Rerun the renderer after a draft changes. The open HTML refreshes every five seconds, but it does not watch the JSON file or fetch server storage. It displays a draft snapshot, not a saved-versus-proposed diff, and uses the plugin's bundled display catalog. Keep undecided wording in a separate preview copy when useful. Reading or navigating the board never changes a response.

## Export

Write the selected flat draft document to the user's requested destination with host file tools. The MCP does not provide an export-to-path tool. Preserve the selected project's identity and all intended fields, inspect the resulting JSON, and avoid overwriting an existing destination without following the user's instructions. A repository import file should contain only the intended public application data; working analysis and private notes belong elsewhere.

## Website transfers

Use the requested path, or explain these two choices when a choice is needed:

| Path            | Appropriate use                                                                                   |
| --------------- | ------------------------------------------------------------------------------------------------- |
| Proposal URL    | Review proposed answers in the official edit form, including replacements with explicit overrides |
| Repository JSON | Publish a `.bestpractices.json` file for the site's automated-tool import                         |

### Proposal URLs

Use `prepare_update_url(project_id, level, draft=<explicit document>)`. Select only the intended fields when preparing a partial update; the tool reports included and excluded fields and does not save anything. Inspect the returned outcome, notes and artifact before opening it. A complete result means generation succeeded, not that the website accepted or saved every field.

To replace existing answers or wording, pass the specific intended field names in `override_fields`, for example `osps_ac_01_01_justification`. The current MCP accepts explicit fields rather than the old controller's wildcard string. Keep each criterion's status and justification together where their relationship matters. Do not broaden overrides merely to make a proposal appear successful.

If the result is too large or otherwise incomplete, report that result and reduce the requested scope or shorten text with the user. Do not invent URL chunking behavior or fall back to browser-console scripts. For multiple separately prepared proposals, review and save each before the next and refresh the saved state between them.

The site can retain existing answers or apply its own automation. Opening a proposal does not establish persistence. Review the actual form and its notices. After the user saves, use `get_project_progress` to confirm the saved result; compare the intended fields rather than relying only on the percentage.

### Repository import

Use [Export](#export) to prepare `.bestpractices.json` at the repository root or `.project.d/bestpractices.json`; the site checks them in that order. Publish the file only within the user's authorized repository workflow. The site fills blanks and shows differences but does not force existing answers to change.

The site reads the file when editing an unsaved section, on reanalysis, and on **Save (and continue)**. **Submit (and exit)** does not normally reread it. Changing the repository URL also triggers full analysis on save. The public file must use the site's flat field format and limits; consult the current BadgeApp automation-proposal documentation when diagnosing import behavior. The site also reads `security-insights.yml`, which has its own specification; do not infer mappings from the JSON format.

### Saving on the website

Both **Save (and continue)** and **Submit (and exit)** save the entry; the latter leaves edit mode. Entries remain editable. The user reviews and saves, or explicitly asks the host to help with that browser action. The MCP neither authenticates nor performs the save. Saving can reapply high-confidence automated answers, and URL overrides do not disable that behavior. If a value changes again, inspect the site's explanation and help address the relevant project condition.

If asked about licensing of BadgeApp entry data, consult “Privacy and legal issues” on the [site's front page](https://www.bestpractices.dev/en), because terms depend on when the entry was last edited.

## API

Ordinary application operations use the MCP tools, not direct shell HTTP calls. The MCP normalizes supported Baseline display IDs to form IDs such as `osps_ac_01_01_status`. Use the selected level's catalog and published tool schema for field eligibility and types. Public reads return provenance; inspect and retain relevant attribution when reusing upstream material.

The MCP supports public BadgeApp reads and generated review URLs, not project registration or authenticated writes. `get_project_badge_status` provides a compact badge-family observation; `get_project_badge_svg` provides SVG and a dynamic Markdown embed. Neither is a replacement for saved criterion answers from `get_project_progress`.

## Stop

Retain the agreed caller-owned or server-stored draft for resumption. Distinguish it from unsaved website proposals and repository work awaiting writeback. Apply or discard unfinished preview revisions and repository changes according to the user's instructions, then remove disposable session scratch files. Do not delete durable drafts merely because the session ends.
