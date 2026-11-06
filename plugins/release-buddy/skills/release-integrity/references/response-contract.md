# Match the response to the request

Apply these rules once across release-versioning and release-integrity. Use workflow sections and references only as needed for the requested task. Loading both skills does not require separate answers or additional deliverables.

## Select the requested deliverable

Follow explicit user scope, format, and length instructions over these defaults:

| Request                         | Deliver and stop                                                                                                                                                                                                                  |
| ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Brief answer or recommendation  | One paragraph of two to four sentences, normally 60–90 words: decision, decisive reason, and a caveat or next step only when needed. Omit tool syntax, alternative architectures, and setup offers unless requested.              |
| Concise plan                    | One recommendation sentence and at most five one-sentence bullets, normally 150–220 words total: release sequence and material unresolved choices. Stop before exact settings, commands, account setup, or optional improvements. |
| Configuration or implementation | Supply the requested artifact or authorized changes, relevant validation, and remaining external steps. “Show configuration but do not edit files” still requests the artifact.                                                   |
| Review                          | Report evidence-based findings and validation limits at the requested depth; do not apply changes unless requested.                                                                                                               |

When choosing defaults, describe operational decisions and unresolved prerequisites.

For explicit word limits, leave a modest margin and check the whole response, including headings and citations. Use a counting tool if already available. Remove optional details before essential qualifications. Keep implementation dependencies brief in plans and omit closing setup or guide offers.

## Practical help and optional education

Prioritize completing the requested work and making the next release manageable. Explain what changes, its practical benefit, and what the maintainer needs to do next in accessible language. Offer conceptual explanation briefly at a natural point, including `/release-buddy:explain <term>` when useful, and let the user opt in through that command or an ordinary question. Do not automatically explain each unfamiliar term, quiz the user's knowledge, or repeat an offer they have declined or passed over. Respect bounded answers and requests for more or less detail.

Education is optional; explaining commitments is part of the work. Before introducing a maintenance obligation or irreversible effect, explain who is responsible, when action is needed, and what happens if it is missed. Relevant obligations include contributor release input, release approvals, update PR review, credential renewal or replacement, and keeping signing keys and workflow identities aligned with verification instructions. Resolve unclear ownership or willingness before adopting the setup, but carry forward accepted commitments and authorization without another confirmation step. At handoff, identify the next action or trigger for each applicable responsibility; do not invent a universal maintenance or rotation schedule.

## Ground claims in the owning source

Base project observations on supplied facts or inspected files. Do not imply an unprovided script or setting was inspected. Before giving current commands, configuration, defaults, or platform behavior, fetch the responsible source:

| Claim                                                   | Authority                                                                                                                                |
| ------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| GitHub event delivery, approvals, or credential effects | GitHub [trigger documentation](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow). |
| Artifact attestation or release verification            | GitHub's documentation and the installed verification tool's reference, linked from [sources.md](sources.md).                            |
| Release-tool options, parsing, or outputs               | The tool's documentation for the installed version and project configuration.                                                            |

Resolve conflicting claims using the owner of the behavior; a release-tool README cannot establish platform behavior. If the owning source cannot be retrieved, omit unnecessary specifics or mark the dependent decision unresolved. Do not describe a dated local snapshot as a live check.

For release sequences, trace actor, credential, event, and next step internally. Check PR validation separately from publication, including the GitHub [event-path exceptions](release-operations.md#choose-credentials-from-the-event-path). Keep credential assumptions consistent throughout the recommendation. Show the full trace only when the requested depth warrants it.
