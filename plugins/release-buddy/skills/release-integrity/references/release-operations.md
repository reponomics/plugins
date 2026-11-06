# Release operations

Use this reference for public GitHub source releases. The version, notes and tag ownership come from the existing process or release-versioning. Read the [owning sources](sources.md#release-operations) before supplying exact configuration.

## Source release sequence

1. Review the intended version, source commit and human-readable notes.
2. Create and verify the signed annotated tag using [the trusted signer](git-signing.md). If it already exists, compare its tag object as well as its commit; never replace it.
3. Prepare a GitHub draft for that existing tag. A release tool may create the draft if it preserves the tag and its identity. Attach any intended artifact and evidence before publication.
4. Verify the draft's source, notes, filenames and bytes. Confirm immutable releases are enabled on the actual repository before publishing; YAML or a draft alone does not establish that setting.
5. Publish when authorized, then run the consumer's verification commands and record what they establish.

Immutable publication locks the assets and tag. GitHub's release attestation binds its recorded tag, commit and asset digests; it is distinct from the maintainer's Git signature and from build provenance. GitHub allows changes to display notes and titles after publication, so retain reviewed notes in the signed source when historical accuracy matters. Enabling immutability does not protect older releases retroactively.

## One primary built artifact

Add this only for a file consumers need, such as a CLI archive. Name the precise output and supported platform; a source-only project needs none. Preserve the project's build tooling and inspect scripts before executing them.

Build and test once from the verified source commit in a GitHub Actions run. Pass the exact retained output to an attestation job in that same run, keeping the build out of the job with publishing authority where practical. Use GitHub's current `actions/attest` guidance for build provenance, verified SHA pins and minimal job permissions. Record the subject's digest, source commit, workflow and ref; resolve any reusable-workflow identity explicitly. The authenticated source must be the source actually built: checking out a tag inside a main-branch dispatch does not by itself change the run's source identity. Choose a supported trigger or attestation design that binds the intended source; do not drop a failed identity restriction from consumer verification. Do not attest a downloaded old file in a new workflow and claim that workflow built it.

Upload those same bytes and, if needed for portable verification, the actual provenance bundle to the draft. Use distinct filenames for the artifact and evidence, rejecting local or remote collisions before upload. A bundle is evidence about the artifact; it is not itself the built subject. Verify the downloaded artifact against the expected repository, signer workflow, source ref or commit, and digest using current GitHub CLI options. An unexpected identity or changed file must fail. Inspect the output rather than treating the existence of a bundle as success.

Preserve original build outputs until verification and publication are complete. Do not rebuild merely to finish an upload. If a retry rebuilds, compare digests and treat different bytes as a different candidate. Describe the observed guarantees; do not certify a SLSA level merely from an action name.

## Optional OSV evidence

Add dependency scanning only when selected, for example to support a badge goal. Reuse the project's existing check. If setup is requested, consult the current [OSV-Scanner documentation](https://google.github.io/osv-scanner/) and pin the chosen scanner version; do not copy the version or dependency list from a different project.

Agree the inventory first: runtime dependencies, maintainer tools, or both. Prefer resolved lockfiles; include transitive versions and record the resolver platform when dependencies must be resolved. Keep resolution and scanning in a job without publishing credentials, and inspect any hooks or source-build steps before running them. Verify that the report actually covers the intended inputs. A scanner error, missing inventory or skipped analysis is an incomplete check, not a clean result.

For a release report, record the exact source revision, scan time, scanner version, dependency inputs, resolved inventory, platform and outcome. Review findings and their disposition; do not silently suppress advisories. Agree whether findings block release and how justified exceptions are documented before enabling the gate. Attach the JSON and a short scope note to the draft, preserve their bytes through publication, and identify them as scan evidence rather than built artifacts.

A release-time snapshot does not satisfy ongoing monitoring by itself. If recurring checks are selected, name the triage owner and where failures appear. Dependency scanning evaluates known advisories for its inventory; it does not assess skill instructions.

## Choose credentials from the event path

Trace actor, credential, event and next step. Consult GitHub's full [triggering documentation](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow), including exceptions. Snapshot checked 2026-11-04; recheck before applying:

| Event generated using `GITHUB_TOKEN`           | Behavior                                                                  |
| ---------------------------------------------- | ------------------------------------------------------------------------- |
| Tag push or release event                      | Does not start the corresponding follow-on workflow.                      |
| `pull_request` opened, synchronize or reopened | Creates approval-required runs that a user with write access can approve. |
| `workflow_dispatch` or `repository_dispatch`   | Can start a workflow.                                                     |

Do not generalize tag-event suppression into a claim that bot PR checks are impossible. Prefer a supported same-workflow sequence or deliberate dispatch where it fits. A GitHub App is an option when separate automatic events are required, not a default prerequisite. When one is deliberately selected, consult GitHub's setup documentation and record its least-privilege scope, owner and credential upkeep.

Draft creation does not trigger a `release: created` workflow. Some tools do not create the tag until a draft is published; inspect the tool's behavior and arrange explicit tag creation if it is needed earlier. Do not publish an immutable release before a follow-on workflow attaches its files.

## Protect publication authority

Limit who can create release tags, change signer trust or reach publishing jobs. Use repository policies and a protected deployment environment appropriate to the project's agreed process; require a human reviewer only if that is the selected control. Keep writes at job scope, avoid persistent checkout credentials, and never expose a signing key or publication token to untrusted PR code.

For manual dispatch or retry, resolve and validate the candidate with trusted code before executing candidate files. Restrict the control workflow to the intended branch. Confirm that any downloaded evidence belongs to the approved commit and run; do not trust an artifact by name alone. Keep local checks separate from settings that could not be observed.

## When a release goes wrong

Inspect the current state before retrying.

- **No publication:** retry transient failures at the original source. Fix a content defect in a new reviewed version rather than moving an announced tag.
- **Partial draft:** retain the original run's output. Download existing files separately and compare bytes. Upload only missing matching outputs; do not blanket-clobber assets. An attestation bundle can differ across signing attempts even for identical subject bytes, so a bundle difference alone does not justify replacement. Resolve conflicts with the maintainer before replacing anything.
- **Missing original output:** do not mix new build products with an old partial draft. Choose a new candidate deliberately.
- **Published immutable release:** missing or wrong assets require a new release. Never delete or reuse the tag to redo it. A missing build attestation may be recoverable from the original build run while its exact outputs remain available; a new run must not misrepresent itself as the builder.
- **Suspected compromise:** preserve evidence and follow the project's security policy; identify affected signer or publishing access and releases before authorized revocation or recovery.
