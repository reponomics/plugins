<!--
Maintainer guide for public GitHub source releases. Replace every {{PLACEHOLDER}} with the project's agreed process and verified commands; remove optional sections that do not apply. Keep existing versioning and changelog conventions.
-->

# Releasing {{PROJECT}}

A reviewed version and release note identify what changes. A maintainer's signed annotated tag approves the exact source commit. An immutable GitHub Release records that tag and its attached files. Update this guide when the process changes.

## Agreed setup

| Decision                                    | Project choice                                                                               |
| ------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Official repository and release unit        | {{OWNER/REPO; whole project or named component}}                                             |
| Version authority, tag convention and notes | {{VERSION_FILE; TAG_PATTERN; NOTES_PATH}}                                                    |
| Authorized release signers                  | {{PUBLIC_KEY_LOCATION; independent way to authenticate fingerprint; owner of signer policy}} |
| Required tests and optional dependency scan | {{COMMANDS_OR_WORKFLOWS; exact dependency inputs and platforms scanned}}                     |
| Prepare and finalize commands               | {{PROJECT_COMMANDS; which command publishes}}                                                |
| Repository settings                         | {{immutable releases enabled; tag protections; who may prepare and publish}}                 |

The signing private key stays with the maintainer in {{KEY_CUSTODY}}. Do not put it in Actions. The signer policy must come from a trusted source outside the candidate tag. Before the first release, confirm the repository settings and test consumer verification in [VERIFYING.md]({{VERIFYING_PATH}}).

## Make a release

1. Prepare the version and useful release notes in a reviewed PR. Run the required checks, merge, and record the full intended commit SHA.
2. Confirm that commit belongs to the approved release history and its version and notes match the intended tag. Sign an annotated tag with the authorized key using {{SIGNED_TAG_COMMAND}}. Verify its signature, signed tag name, direct commit target and expected commit before pushing. An existing tag is inspected, never replaced.
3. Run {{PREPARE_COMMAND}}. It validates the tag, runs checks against that exact commit and creates an unpublished draft. Review its tag, notes, prerelease status and complete attachment set.
4. If a dependency scan was selected, inspect `osv-results.json` alongside `scan-scope.md`: commit, scan time, tool version, inputs, resolved dependency versions, platform and outcome. An incomplete selected scan blocks preparation. Apply {{AGREED_FINDINGS_GATE_AND_REVIEWED_EXCEPTION_POLICY}} to reported advisories. Investigate applicability and fixes; record the disposition in {{TRIAGE_LOCATION}} and remediate through review. There is no silent exception.
5. Run {{FINALIZE_COMMAND}} only after the agreed review. It must recheck the draft against the successful run and signed source, confirm immutability, then publish. Run the consumer verification instructions against the result.

Remove this paragraph and the scan step when no scan was selected. The OSV report covers {{EXACT_SCAN_SCOPE_AND_EXCLUSIONS}}. It checks known advisories for that inventory at that time; it does not establish that source code or generated workflows are secure. {{IF_SCHEDULED_SCANNING_WAS_SELECTED: owner, schedule and triage trigger}}

## Optional primary build artifact

Delete this section for source-only releases. {{ARTIFACT_NAME}} is the primary artifact, built from the verified release commit by {{BUILD_WORKFLOW}}. Build with read-only repository access; keep publication authority out of build and dependency-install steps. Generate provenance in the same run, retaining the original artifact. The attestation's authenticated source identity must match the source actually built; checking out another commit does not by itself change the run's identity.

Attach the exact verified artifact to the draft before publication. Reserve distinct names for the artifact, its provenance bundle and any scan reports; reject collisions rather than overwriting files. Document that artifact’s build provenance and the exact repository, workflow, source ref and commit consumers must verify. A scan report or provenance bundle is not itself a built deliverable.

## Recover and maintain

For a failed or partial draft, keep it unpublished and retain the original evidence. Compare existing files and digests before choosing {{PROJECT_RECOVERY_PROCEDURE}}; do not rebuild merely to complete uploads or overwrite unknown assets. Retry a transient service failure against the same tag. Correct a bad signed release with a new version.

Publication locks the tag and assets; the tag name cannot be reused after deletion. Keep reviewed notes in signed source because displayed release notes can still change.

{{OWNER}} reviews action updates and changes to signer authorization, plus scanner updates and failed scheduled scans when that maintenance was selected. For a suspected compromise, follow {{INCIDENT_CONTACT_AND_PROCEDURE}}, authenticate replacement keys independently, and tell consumers which releases are affected.
