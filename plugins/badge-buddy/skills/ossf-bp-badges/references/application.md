# Working with the badge application

Read the section for the operation requested. Commands below follow the controller path and `--repo` / `--data-dir` arguments resolved at skill startup. Retain any selected `--assessment-file` on every operation. The controller supports GitHub-hosted projects; for other forges, help draft answers without claiming synchronization.

## Start or resume

Use one flat `.bestpractices.json` assessment for all badge sections. Default to private plugin storage and briefly tell the user where progress is saved. If they already maintain an assessment in the repository or request that location, use [Repository assessments](#repository-assessments) to select the working file before continuing.

Run `status` online once at the start of each Claude Code session to verify the repository's badge entry and synchronize saved website answers:

```bash
"<controller-path>" --repo "<project-root>" --data-dir "<plugin-data>" status
```

Include `--assessment-file <working-file>` when using a selected assessment. Use the returned `assessment` and handle the registration state:

- `registered`: continue with the returned project ID.
- `registration_required`: link to [registration](https://www.bestpractices.dev/projects/new), or use `--allow-unregistered` if the user chooses to defer it.
- `unregistered`: continue the deferred-registration work without asking again.
- `registry_miss`: rerun online before concluding that registration is absent.

Use `status --project-id <id>` when the numeric ID is known. Retain the verified repository/project association for subsequent local commands; rerun online status if either changes. Incomplete or ambiguous lookups do not establish that the project is unregistered.

`status` initializes wholly absent answers and preserves existing status/justification pairs, including `?` and empty wording. It reports differences as `conflicts`; resolve them using the user's current answers, asking only about differences that remain unclear. A `wording_only_updates` result means the saved website answer has the same status but different wording; keep the intended wording for a later transfer.

`status` synchronizes answers and reports counts; it does not validate every saved field or establish that the project meets each criterion. `apply` validates changed answers against the selected section's field requirements, not the project's implementation of the practice.

The public data contains only saved answers. If a section has never been saved, explain that its edit-page suggestions and percentage are not visible to the controller, and suggest saving that page once before refreshing. Site-generated suggestions may have incomplete justifications even when their status is correct.

The controller retains the public snapshot for comparison. Subsequent `apply`, `review`, `export`, `propose`, and `fill-script` operations are local; assume no outside edits during the session. Refresh with `status` after website changes are saved or when requested. Use `status --offline` to inspect local progress without refreshing. A failed refresh leaves the previous snapshot available but does not establish current website state.

## Repository assessments

Use this section when working from `.bestpractices.json` or `.project.d/bestpractices.json` in the repository, or when the user requests repository storage.

Copy the existing assessment to a temporary working file and retain the original bytes or digest for writeback. For a new assessment, start with a temporary file containing `{}`. Pass `--assessment-file <working-file>` on every operation, including previews and transfers. The file must exist and contain a flat JSON object. If direct edits are already authorized, use the repository file itself.

Without `--assessment-file`, the controller stores answers privately. Repository-backed work has no additional private assessment copy. Both modes keep a separate public snapshot; use the controller's responses rather than editing its registry or sidecars.

Before writing a temporary assessment back to the repository, show the changes or preview and obtain agreement unless already authorized. Compare the destination with the retained original; for a new file, check that the destination has not appeared. Reconcile any intervening changes rather than overwriting them. Copy the agreed assessment. Tracking a new file in Git is a separate user choice.

## Record answers

Help the user carry their decisions into the form. Here, confirmed changes are changes the user has requested or agreed to; they do not need the assistant's certification. If field validation rejects a change, explain the specific format or required-detail issue and help resolve it without adding a separate compliance audit.

Send confirmed flat-field changes through `apply --section <section> --input -`. Always supply the section: reused Metal identifiers can have different requirements. Apply status and justification together when both change; a wording-only update may contain just `<criterion>_justification`. Inspect advisory `style_warnings` for useful corrections.

An open preview does not add an approval step for an exact change the user has already requested. Apply it to the working assessment. Use a separate preview revision only when the user wants to consider wording before adopting it.

## Preview

Offer once to open the board when starting or resuming application work. Use `review --section <section>` for Overview, or `review --section <section> --view all` to show current answers. Add `--no-browser` to generate without opening. The `review_written` response supplies the file URL.

Generate one board per requested section; the command otherwise defaults to Passing. The board refreshes within five seconds of an update and retains its selected view. It displays official criterion text and stable section numbering, so filtered lists may have gaps. Browsing neither approves answers nor copies them into the repository.

When the user requests a preview of wording they have not adopted:

1. Copy the controller-returned flat `assessment` into a temporary revision file and use `--assessment-file <temporary-file>` for that revision and its board.
2. Update only `<criterion>_justification` with `apply --section <section> --review-response <intended-response> --input -`. This checks wording against the intended response while leaving the current status and board category unchanged; explain that distinction once.
3. When the user approves the wording and response, apply `<criterion>_status` to the revision, then apply the exact approved status/justification pair to the normal working file. The board category updates in place.
4. On cancellation, pause, or transfer preparation, discard unfinished revisions and regenerate the board from the normal working file.

Initial drafts can apply status and justification together. Wording-only revisions keep the same status. Never export unfinished preview wording.

## Export

For a local JSON export, use `export --output <path>` with the selected working-file options. This exports the assessment without fetching website data. To place it in the repository, export to a temporary path and follow [Repository assessments](#repository-assessments) for writeback. Website transfer instructions are needed only if the user wants the site to import it.

## Website transfers

Use the normal working assessment and resolved numeric project ID. Finish or discard outstanding preview revisions first. Mention unanswered criteria and unresolved synchronization differences without requiring a completed badge or another assessment. Offer an All criteria preview if the user has not already reviewed the answers being transferred.

When the user has chosen a method, read its section below. Otherwise offer these choices:

| Method | Use it for |
| --- | --- |
| [Proposal URLs](#proposal-urls) | Highlighting proposed changes in the official form, without publishing a repository file. |
| [Repository import](#repository-import) | Sharing durable answers in the repository; this cannot force replacements of existing website answers. |
| [Fill script](#fill-script) | Long answers or selected form edits, including wording replacements. |

All methods prepare changes for review; none saves the form. After filling it, follow [Saving on the website](#saving-on-the-website) to explain the save action and refresh the local snapshot afterward.

### Proposal URLs

Run `propose --section <section> --overrides '*_status,*_justification'` after resolving synchronization differences. Overrides affect only fields included in the URL; the controller omits answers already matching saved site data. If the user prefers a website value, adopt it in the assessment before generating the proposal. Site-generated suggestions need not displace answers the user has approved.

The form applies proposals as follows:

| Existing value | Proposal | Result |
| --- | --- | --- |
| Blank or unknown status | Known status | Applied, highlighted yellow. |
| Known status | Different status without a matching override | Retained; difference highlighted blue. |
| Known status | Different status with a matching override | Replaced, highlighted orange. |
| Matching status, blank justification | New justification | Applied. |
| Matching status, existing justification | New wording without a matching override | Existing wording retained. |
| Matching status, existing justification | New wording with a matching override | Wording replaced. |
| Any status | `?` | Status proposal ignored. |

For a narrower override, supply a comma-separated list of Ruby `File.fnmatch` field patterns, such as `--overrides contribution_justification`. Forcing a status also forces its justification. A blocked status change blocks its accompanying justification even if that justification has a separate override. The site matches the patterns; generating a URL does not establish that an override matched or that the form was saved.

Relay the controller's proposed, skipped, and dropped notes. Without overrides, it reports replacements of existing wording separately for the fill-script path. It rejects override lists above 10,000 characters or 1,000 patterns, which the site otherwise silently ignores. Its practical URL limit is 6,000 bytes; use a fill script for answer pairs too large for one URL. Keep each criterion's status and justification together, and save each page before opening the next when several URLs are returned.

Proposals survive login redirects and apply after initial site suggestions, but a draft recovered after login takes precedence. Revisiting a URL reapplies its proposals. The site trims surrounding whitespace from proposed justifications. If the form behaves differently, use direct form editing or a fill script for the requested changes.

### Repository import

Use [Export](#export) to prepare `.bestpractices.json` at the repository root or `.project.d/bestpractices.json`; the site checks them in that order. The file must be available on the remote repository for the site to read it. It fills blanks and shows differences but cannot force an existing answer to change.

The site reads the file when editing an unsaved section, on `reanalyze=1`, and on **Save (and continue)**. **Submit (and exit)** does not normally reread it. Changing the repository URL also triggers full analysis on save.

Use a flat JSON object within the 100,000-byte limit. Fields use lowercase IDs followed by `_status` or `_justification`; Baseline fields look like `osps_ac_01_01_status`. The site validates field names, types, and justification length. General fields such as `name` and `license` are also accepted. Unknown or invalid statuses—including `?`—are ignored, but an accompanying or standalone justification can still be processed.

The site also reads `security-insights.yml`; that format has its own specification, so do not infer its mappings from this JSON format.

### Fill script

Run `fill-script --section <section> --output <path>` to produce a console script for the user's section edit page. It changes radio buttons and justification fields without saving or proposal-style highlighting. By default, `--changed-only` selects only wording differences from the saved public snapshot. Use `--criteria <ids>` for an explicit subset or `--all` for every answered criterion; retain the user's chosen scope.

The script can replace statuses and wording without URL override rules. It omits `?` statuses; reset an answer to unknown directly in the form. Site automation still runs when the form is saved.

### Saving on the website

Explain that both **Save (and continue)** and **Submit (and exit)** save the entry; the latter simply leaves edit mode. There is no irreversible completion step: entries are public from registration and remain editable. Repository import specifically needs **Save (and continue)** to reread the file.

The user reviews and saves the form, or explicitly asks Claude to log in or save it; carry out that request when given. The controller neither authenticates nor writes to BadgeApp. Saving can reapply the site's high-confidence automated answers, and URL overrides do not disable this. If an answer changes again, inspect the site's explanation and help address the relevant project condition. Run `status` after saved changes to refresh the comparison snapshot; preparing or opening a transfer does not refresh it.

If the user asks about the license of their BadgeApp entry data, consult “Privacy and legal issues” on the [site's front page](https://www.bestpractices.dev/en), because the terms depend on when the entry was last edited.

## API

Use this section only when explaining or diagnosing an API or field-format issue; ordinary application operations use the controller.

Read a project with `GET /projects/<ID>.json`, using the `.json` suffix rather than the `Accept` header. Limit non-badge requests to one per second. `GET /projects.json?url=<encoded-url>` matches homepage or repository URLs, ignoring trailing slashes and spaces. Zero or multiple matches require project selection. Public JSON may return Baseline display fields such as `OSPS-AC-01.01_status`; the controller normalizes them for form fields, URLs, and repository JSON.

Proposal URLs use `/(:locale/)projects/:id/:section/edit?KEY=VALUE&...`, with URL-encoded values. Fields outside the edited section are ignored; `name`, `description`, `license`, and `implementation_languages` are accepted in any section. Known status values are `Met`, `Unmet`, and permitted `N/A`.

The upstream API supports authenticated writes but recommends proposals or repository JSON instead. The plugin has no authenticated API write path.

## Stop

Discard unfinished preview revisions and distinguish durable answers from repository work awaiting writeback. Apply or discard that work according to the user's instructions, then remove session scratch files. Resume from the durable assessment next time.
