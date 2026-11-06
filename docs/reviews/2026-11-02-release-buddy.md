# Release Buddy document and release-readiness review — 2026-11-02

Originally reviewed at `48c8867` on `polishing`. Scope: all 27 authored Markdown documents under `plugins/release-buddy`, four workflow templates, the plugin manifest, and supporting tests/evaluation guidance. The original assessment below records the state before the subsequently authorized implementation pass.

## Implementation follow-up — 2026-11-02

The operational corrections and focused editorial changes were implemented in `cd707d2` and `26eb674`, with a subsequent clarification prompted by the live evaluation described below.

- PyPI credential retirement is now conditional on verifying the replacement path and checking other consumers; only superseded credentials are retired with authorization.
- The release-assets workflow checks the entire intended upload set against existing draft asset names before uploading. A collision stops with recovery guidance. The guide explains comparison against retained original artifacts, selective missing-file upload, preservation of valid bundles, and explicit resolution of conflicting files. Published releases are not modified. This is deliberate manual recovery, not automatic overwriting or resume.
- Six offline tests execute the actual template shell against a fake GitHub CLI. They cover partial package/bundle collisions, empty drafts, unrelated assets, published releases, failed asset inventory, and new draft creation. The fake rejects deletion and clobber operations.
- The shared response contract makes education opt-in while requiring explanation of practical consequences and commitments. `/release-buddy:explain` retains its brief/default/extended modes and checks current claims at any depth. Both main skills preserve prior authorization instead of introducing another approval for accepted work.
- Release handoffs now record responsibility, owner, and action or trigger for updates, separately managed credentials, and publisher identities. App private-key custody is distinguished from short-lived installation tokens. The npm reference additionally requires checking and explaining the first-publication deadline and publisher-entry replacement requirements before setup, based on [current npm documentation](https://docs.npmjs.com/trusted-publishers/#trusted-publisher-configuration-expiry).
- The integrity entrypoint was reduced from approximately 2,222 to 1,671 words while preserving conditional reading paths, source checks, and publication boundaries. An independent review found no material loss of guidance.
- Other corrections distinguish signatures from provenance, use the same workflow run rather than the same job for attestation, narrow the agent-template credential prohibition, clarify PyPI filename reuse, make the SECURITY.md backlink conditional, and disable unselected container storage-record creation.

Validation after the main edits: `make check` passed 240 tests (142 Badge Buddy, 17 Repo Starter Kit, 9 Release Buddy, 72 maintenance); all plugins passed `make plugin-validate`; 111 local Markdown file/heading targets resolved. The pre-existing missing-icon warnings and informational missing `release-buddy/scripts` compilation message remain. No registry publication or remote configuration changes were made.

Two isolated live smoke cases ran with Claude Opus 5.5 / client 2.1.316 against plugin digest `4dce6544230143e2f9bc53854e872f8f84d45dee75877fa332be898ca21e353b`. The runner allowed only skill invocation, local reading/search, and source retrieval; generated observations remain ignored under `.cache/releases/`.

- `python-choice`: 93 words; preserved the existing tag-derived version process and curated changelog, avoided unnecessary release tooling and conceptual teaching, and explained the maintainer's release action. Passed the intended scope; its closing checklist suggestion is a minor optional addition.
- `combined-plan`: 294 words against a 250-word diagnostic maximum. It coordinated both skills, retrieved relevant sources, distinguished bot-PR approval from tag-trigger suppression, and identified publication uncertainty. It nevertheless included exact configuration details despite a concise-plan request. This is a behavioral failure of concision and abstraction, not a successful case merely because the runner exited cleanly.

The latter observation prompted a narrow clarification: plan defaults should describe operational decisions rather than configuration syntax, and unresolved bootstrap requirements should remain dependencies to verify rather than speculative setup instructions. The original failed observation is retained; it is not overwritten by the follow-up run.

A fresh `combined-plan` run against final plugin digest `44c67339089a97d8d2ef782e1b2a6f8b65df78b0a9d68768d4ac13a95f0f2832` produced 277 words. It removed the configuration recipe and speculative bootstrap-token instructions, explicitly assigned the first-publish commitment, and retained the material event/approval distinctions. It still exceeded the 250-word diagnostic target and used more than one sentence per bullet. Concise-plan adherence therefore remains an open behavioral limitation, despite the clearer instructions; neither run is counted as a full pass. No further repetitions were used to select a favorable result.

Current readiness: the identified operational defects are addressed and the local checks support a beta release. This does not establish hosted publication success or consistently concise model responses. The initial document-by-document assessment below remains as the historical basis for the edits, not a list of still-unapplied fixes.

## Original overall assessment

Release Buddy is close to a sound beta release. Its technical references are useful and mostly proportionate: they equip the agent to handle complicated release behavior without requiring maintainers to read the whole collection. Versioning guidance is particularly strong at preserving an existing process, recommending manageable automation, and explaining contributor and maintainer obligations. The integrity guidance covers the right practical decisions, but its entrypoint repeats scope and consent rules and has a few instructions that conflict with the desired user experience.

Fix the two operational issues below before calling the package release-ready. Align the main skills with the existing opt-in explanation command and make maintenance commitments explicit in the release handoff. The remaining findings are polish rather than reasons to redesign the plugin.

The intended experience is practical completion plus an understandable handoff. Underlying concepts are optional education. Consequences, irreversible actions, and recurring responsibilities must be explained when the maintainer chooses the setup.

## Operational corrections before release

### 1. Verify and scope credential retirement

Location: [PyPI channel guide, line 5](../../plugins/release-buddy/skills/release-integrity/references/channels/pypi.md#native-mechanisms).

The instruction to configure a publisher and then revoke “any API token on PyPI” is too broad and skips proving that the replacement works. A registered publisher can still have the wrong workflow or environment identity; an existing token can also serve another workflow or project. Following this paragraph can disable a working publishing path prematurely. It also conflicts with the verify-first sequence already stated in `references/small-projects.md`.

Retire only the credentials superseded by the selected migration, after checking their remaining consumers and verifying the replacement publishing path. Preserve the existing authorization requirement for revocation. [PyPI describes trusted publishing as complementing API tokens](https://docs.pypi.org/trusted-publishers/); the comparable [npm migration guidance](https://docs.npmjs.com/trusted-publishers/#migration-tip) explicitly sequences verification before retiring unneeded tokens.

### 2. Provide recovery for a partially populated draft

Location: [release-assets.yml, line 73](../../plugins/release-buddy/skills/release-integrity/assets/templates/workflows/release-assets.yml), with related advice in `assets/templates/RELEASING.md:58` and `references/release-operations.md`.

When a draft exists, the workflow uploads every file in `dist/*`. If an earlier attempt uploaded some assets before failing, a rerun encounters duplicate names. The maintainer guide's simple “fix the cause and re-run” instruction is therefore insufficient even though no release has been published.

Either make draft recovery deliberate in the workflow or document an explicit recovery procedure. Inspect existing assets, distinguish matching files from conflicting contents, and preserve an intentional draft review before publication. Do not silently overwrite unknown draft contents: [`gh release upload --clobber`](https://cli.github.com/manual/gh_release_upload) deletes existing assets before uploading replacements. This finding follows from the template and CLI behavior; no hosted publication was performed.

## Clarity, audience, and consistency

### Preserve the existing explanation command

`skills/explain/SKILL.md` is already a good opt-in education mechanism. It is explicitly user-invoked, supports brief/default/extended responses, and returns to the task. Do not add a duplicate educational feature.

`release-integrity/SKILL.md:43` and `release-versioning/SKILL.md:45` still tell the agent to gloss unfamiliar terms automatically. Put the shared practical-help/optional-education policy in `release-integrity/references/response-contract.md` and reconcile those sentences with it. Explain decisions and commitments by default; offer conceptual explanation briefly and let the user opt in through an ordinary question or `/release-buddy:explain`.

The sentence “Aim for a setup the maintainer could explain, not one done on their behalf” in `release-integrity/SKILL.md:85` also sets a broader educational expectation than necessary. The practical standard is that the maintainer understands the accepted responsibilities and can carry out the next release, without needing to explain the underlying security architecture.

### Make upkeep part of the release handoff

Versioning's tool-selection reference already has a valuable “Maintainer obligation” column. Retain it. The release guide's “Occasional checks” placeholder is useful but should also capture accepted responsibilities with an owner and action or trigger: update PR review, credential renewal or replacement where applicable, App private-key custody, and updating trusted publisher configuration when workflow/environment identities change. Do not invent a universal rotation schedule.

Keep this operational guidance separate from optional education. Explain a new obligation before the user adopts it and carry accepted commitments forward without repeated confirmation.

### Clarify consent without adding another gate

`release-integrity/SKILL.md:87` says to carry forward prior authorization, but the next bullet says “Before changing anything … get agreement.” That wording invites repeated confirmation even for authorized local implementation. Say to summarize the work, resolve unselected material choices, and obtain authorization only where still missing. Keep the explicit boundaries around publication, external settings, keys, and token revocation.

This is an instruction-clarity concern, not an observed model failure in this review. Similar discussion-before-change wording in the release-agent template should be customized to the agreed protocol rather than automatically becoming a fresh approval requirement for every maintenance edit.

### Resolve small technical inconsistencies

- `references/channels/github-releases.md:13` says to attest in the build job, while the workflow template intentionally separates building and attesting into different jobs. Use “the workflow run that builds the files” to match the rest of the guide and preserve the useful separation of authority.
- `assets/templates/release-agent.md:33` forbids “other publishing credentials” in repository secrets, which can conflict with the GitHub App private key recommended in `release-operations.md`. The customization instruction mitigates this, but the default should prohibit unapproved credentials and describe the chosen mechanism rather than categorically banning legitimate secrets.
- Current `actions/attest` can create artifact storage records for organization repositories. The container template does not explicitly select this feature or grant its optional `artifact-metadata: write` permission. Upstream catches the missing-permission error and warns, so this is not a failed-attestation defect. When adapting the template, explicitly disable storage-record creation if unused or configure its permission if selected. Sources: [action documentation](https://github.com/actions/attest#artifact-metadata-storage-records), [implementation](https://github.com/actions/attest/blob/main/src/attest.ts).

### Keep concision rules flexible

The shared response contract usefully distinguishes a recommendation, plan, configuration artifact, and review. Its instruction to draft to roughly half of every explicit word limit is unnecessarily rigid. Staying within the user's limit with a modest margin would preserve useful detail without encouraging verbosity.

The integrity entrypoint is approximately 2,222 whitespace-delimited words and the versioning entrypoint 1,695. Length alone is not a defect, but the integrity entrypoint is the best candidate for compression: consolidate repeated scope, source-verification, and consent language while retaining conditional reference loading. Most channel references and templates are already compact; do not remove necessary operational distinctions to shorten them.

## Document-by-document assessment

Paths below are relative to `plugins/release-buddy`. “Keep” means no material change identified in this review; it does not claim that every remote integration was executed.

| Document | Assessment and disposition |
| --- | --- |
| `README.md` | Clear audience, examples, skill selection, and limitations. Keep the explicit explanation-command entrypoint. Minor polish: the blanket statement that signing and provenance show “who built a release and how” could distinguish a signature's signer/content guarantee from provenance's build claims. |
| `skills/explain/SKILL.md` | Keep. Already implements opt-in education at useful depths. A small consistency improvement would require checking current platform-specific claims regardless of explanation length; extended explanations alone explicitly route to sources today. |
| `skills/release-versioning/SKILL.md` | Strong routing, preservation of existing practices, and ownership rules. Align automatic glossing with optional education; otherwise keep. |
| `skills/release-versioning/references/choosing.md` | Keep. One recommended approach, manual releases as a legitimate choice, and explicit maintainer obligations are especially suitable for the audience. |
| `skills/release-versioning/references/policy.md` | Keep. Useful distinctions among compatibility, version sources, prerelease channels, and release notes; avoids simplistic interpretations of commit labels and pre-1.0 versions. |
| `skills/release-versioning/references/monorepos.md` | Keep. Separates version relationships, release timing, and publication sets; handles dependent packages and private build inputs carefully. Detail belongs in the agent reference. |
| `skills/release-versioning/references/automation.md` | Keep. Good event-path tracing, single ownership, migration baselines, and symptom-based troubleshooting. |
| `skills/release-versioning/references/sources.md` | Keep. Well organized; selected primary sources support the described behavior. |
| `skills/release-integrity/SKILL.md` | Useful coverage and conditional routing. Align optional education and commitments, clarify reuse of authorization, and compress repeated boundaries. |
| `skills/release-integrity/references/response-contract.md` | Keep the shared deliverable routing and source ownership. Add the common optional-education policy and loosen the half-limit drafting rule. |
| `skills/release-integrity/references/choosing.md` | Keep. Channel choice, consumer constraints, and program-specific evidence are distinct decisions. Scanner-specific detail is conditional rather than mandatory reading for every setup. |
| `skills/release-integrity/references/small-projects.md` | Keep. Independent options prevent a mandatory security checklist. Its verify-before-revoke instruction should also govern the PyPI channel paragraph. |
| `skills/release-integrity/references/release-operations.md` | Keep core content. Current GitHub event distinctions and App-token inputs checked. Add explicit partial-draft recovery and credential-upkeep handoff where applicable. |
| `skills/release-integrity/references/git-signing.md` | Keep. Sensible SSH starting point; distinguishes signed commits, signed tags, and release attestations. Checks automation compatibility before proposing enforcement. |
| `skills/release-integrity/references/rehearsal.md` | Keep. Optional rehearsal, channel-specific limitations, and permanent effects are useful. Minor precision: PyPI prohibits filename reuse; avoid implying every additional file for an existing version is forbidden. The operations reference already distinguishes this. |
| `skills/release-integrity/references/review.md` | Substantive and useful. Retain evidence-based priorities and a top-findings default. Minor polish: avoid making a generic disclaimer, optional-tool approval, or separate approval for each fix mandatory when the user has already authorized the work. This is release-process review, distinct from Badge Buddy's editorial answer review. |
| `skills/release-integrity/references/verification-docs.md` | Keep. Clear consumer deliverable, expected identity, discovery, and command validation. Clarify that linking from `SECURITY.md` applies when that document exists; a new security-policy file need not be a prerequisite. |
| `skills/release-integrity/references/examples.md` | Keep. Examples have distinct lessons and are optional. The anchored-identity warning is useful. This pass did not freshly inspect every external example. |
| `skills/release-integrity/references/sources.md` | Keep. Organized lookup map with dated claims and explicit rechecking. Selected current sources verified; this review is not a blanket refresh of its verification date. |
| `skills/release-integrity/references/channels/pypi.md` | Fix credential retirement before release. Otherwise concise, with a useful build/publish split and current upstream lookup requirements. |
| `skills/release-integrity/references/channels/npm.md` | Keep. Current authentication, provenance, and staged/direct publication distinctions are useful, including the approval commitment. |
| `skills/release-integrity/references/channels/containers.md` | Keep. Compact digest-based verification guidance; deployment policy is appropriately outside its scope. |
| `skills/release-integrity/references/channels/github-releases.md` | Keep necessary sequencing detail. Correct build-job wording and clarify partial-draft recovery. |
| `skills/release-integrity/references/channels/other-registries.md` | Keep as short routing guidance. Selected registry claims checked; crates.io page rendering prevented a fresh provider-list confirmation. |
| `skills/release-integrity/assets/templates/RELEASING.md` | Good practical maintainer artifact. Add explicit upkeep ownership and accurate partial-draft recovery. Keep customization and removal of unused sections. |
| `skills/release-integrity/assets/templates/VERIFYING.md` | Keep. Consumer-focused commands, expected identities, coverage cutoffs, and failure handling. Placeholder resolution is intentional. |
| `skills/release-integrity/assets/templates/release-agent.md` | Useful agreed-protocol artifact. Narrow the credential prohibition and ensure consent language reflects the maintainer's actual standing authorization. |

## Workflow templates

| Template | Assessment |
| --- | --- |
| `release-integrity/assets/templates/workflows/pypi-publish.yml` | Keep. Matches the supported separate build/publish pattern. A named environment must be configured; YAML alone does not establish its protection. |
| `release-integrity/assets/templates/workflows/npm-publish.yml` | Keep. Strong separation of build and publishing authority, tarball handoff, and disabled publishing lifecycle scripts. The existing offline test exercises the intended boundary. |
| `release-integrity/assets/templates/workflows/container-publish.yml` | Keep core structure. Explicitly choose optional storage-record behavior when adapting it. |
| `release-integrity/assets/templates/workflows/release-assets.yml` | Fix partial-draft upload recovery before release. Retain separate jobs and attachment before immutable publication. |

All four intentionally contain `FULL_COMMIT_SHA` and version placeholders, with instructions to resolve current action releases when adapting them. These are templates, not deployable workflows with purported current pins; the placeholders are not themselves a release defect.

## Verification and limits

- `make check` passed all 234 tests: 142 Badge Buddy, 17 Repo Starter Kit, 3 Release Buddy, and 72 maintenance tests. Compilation completed with the existing informational `Can't list 'plugins/release-buddy/scripts'` message because this guidance plugin has no scripts directory.
- `make plugin-validate` passed for all three plugins. Release Buddy has an `ICON_MISSING` warning; supply approved square artwork if preparing a directory submission. This is separate from plugin structural validity.
- An ad hoc local check resolved 110 Markdown file and heading targets across the 27 documents. The existing documentation test checks file targets, not model behavior.
- Selected current primary sources were checked for GitHub workflow triggering, App-token usage, commit signing, TestPyPI, trusted publishing, npm behavior, attestations, release upload semantics, release tools, and registry guidance.
- The GitHub bot-PR exception in `release-operations.md` is supported by [current GitHub documentation](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow): approval-required PR runs are distinct from suppressed tag/release events. This nuanced guidance should be retained.
- Versioning spot checks included [Changesets fixed groups](https://changesets.dev/guide/fixed-packages), [linked groups](https://changesets.dev/guide/linked-packages), [non-npm use](https://changesets.dev/guide/beyond-npm), [Release Please](https://github.com/googleapis/release-please), [semantic-release changelog](https://github.com/semantic-release/changelog), and [Lerna versioning](https://lerna.js.org/docs/features/version-and-publish#versioning-strategies).
- `tests/release-buddy/skill-evals.md` is an honest behavioral test plan, and the opt-in runner records observations rather than declaring semantic success. Existing cached observations refer to an earlier dirty checkout and a different plugin digest; they do not establish current adherence. No fresh paid model-session evaluations were run.
- No registry publication, key or token mutation, repository-setting change, or hosted workflow execution was performed. End-to-end publication and agent adherence remain unverified by this pass.
- The root instruction file's `INTERNAL/AGENTS.md` target remains absent; the user-supplied repository instructions were followed. No scoped instruction file was found under Release Buddy or its tests.

After the operational fixes and the focused audience/handoff edits, the documentation and templates would be suitable for a beta release on the evidence reviewed. A stronger claim of demonstrated agent behavior requires fresh evaluations of the revised plugin, especially optional explanation, accepted commitments, and failed-release recovery.
