# Monorepo versioning strategies

Choose the versioning policy from how packages are consumed and maintained, then select tooling that can implement it. A shared repository, build system, or pull request does not by itself imply one version or one release. Use [policy.md](policy.md) for compatibility and version syntax, and [automation.md](automation.md) for implementing or migrating the chosen process.

## Separate three decisions

Establish these independently:

- **Version relationship:** which packages share a version number and which have their own version history.
- **Release cadence:** which packages release together, on a schedule, or whenever ready. Independent versions can still ship in a coordinated release train.
- **Publication set:** whether a release publishes every member of a group or only the affected members. Version alignment and publication selection are different policies.

Define the intended behavior in plain language before mapping it to a tool's settings. Terms such as fixed, linked, synchronized, and release group have tool-specific meanings. For example, [Lerna's fixed mode](https://lerna.js.org/docs/features/version-and-publish#versioning-strategies) can leave unchanged packages on earlier versions unless synchronization is requested. Do not infer whole-group publication merely from a setting called fixed.

## Compare the strategies

| Strategy | Consider when | Cost to make explicit |
| --- | --- | --- |
| One shared version for the release unit | Consumers treat the packages as one product and usually upgrade them together. | A change to one member can advance the group's version; decide whether unchanged members also publish and how their notes explain the alignment. |
| Independent package versions | Packages have distinct consumers, compatibility contracts, or release cadences. | Maintain per-package baselines, notes, tags, and dependency propagation; a single repository-wide latest tag cannot identify every package's last release. |
| Coordinated groups with independent versions between groups | Some packages form a tightly coupled SDK or framework, while other packages evolve separately. | Define group membership, version rules within each group, and dependencies crossing group boundaries. Avoid giving a package competing version owners. |

Recommend the simplest strategy supported by the observed upgrade pattern. Prefer a shared unit when the maintainer deliberately offers one coordinated product; prefer independent units when consumers can select packages separately and the maintenance benefits justify the extra bookkeeping. Consider groups when neither rule fits the whole repository. Do not split or combine version histories only to match a tool's default.

Equal version numbers are not proof of compatibility. Document the combinations the project supports and test them. In a repository containing several languages, a shared product release can map to different ecosystem version spellings; record that mapping rather than forcing one registry's syntax into every manifest.

## Identify the affected release units

Inventory publishable packages, private build tools, examples, and internal libraries. Draw only the dependency relationships relevant to the requested decision: runtime, peer, build, generated-source, and bundled-code relationships can have different release effects. A private package may affect a public artifact without itself being published.

Trace changes from each unit's actual last release. Account for shared generators, root configuration, and copied or bundled code; filtering only files below a package directory can miss a changed artifact. Conversely, a root documentation edit need not release every package. Distinguish packages needing tests or a rebuild from packages needing a new published version.

For a changed dependency, inspect the dependent's declared range, resolved or bundled content, and public contract. Determine whether its metadata or shipped bytes change and whether compatibility changes for its own consumers. Check workspace-protocol rewriting and dependency-update behavior against the selected tool and package manager. Neither “every dependency bump forces a major bump” nor “only directly edited packages release” is a safe universal rule.

## Explain the effect on this repository

When an example would help the user, trace one relevant dependency change through the chosen release units. Explain whether dependents must adopt it now, how their own consumer contracts or shipped bytes change, and why unrelated packages stay unchanged or advance under group policy. Preserve each member's published version history when aligning a group. When implementing an automated workflow, configure the selected tool to enforce the agreed propagation and verify its preview.

## Make releases identifiable and installable

Choose tags and changelog locations that identify the versioned unit: a group tag, package-qualified tags, or a release record listing package versions. Preserve working conventions and confirm the release tool discovers the right baseline for each unit. One aggregate release PR or GitHub release need not imply one package version.

Test the packages as consumers install them, not only through local workspace links. Where a dependent requires a newly published dependency, arrange publication and registry-availability checks accordingly. Dependency cycles need an ecosystem-supported strategy; a topological publish order alone cannot resolve them. A coordinated release is not automatically an atomic multi-package registry transaction. Plan recovery from partial publication using the existing [automation guidance](automation.md#connect-preparation-to-publication).

For prereleases, check internal ranges and channels together so a stable package does not unexpectedly require a preview-only dependency. Follow [prerelease policy](policy.md#prereleases-and-maintenance-lines) for promotion. When changing strategies, map existing versions, tags, and pending release intent before enabling the new automation; preserve published history.

## Record and validate the choice

Use the release units and their members, version relationship, publication selection, tag/baseline convention, and dependency propagation policy as the working decision record. In a brief recommendation, present only the chosen strategy and decisive tradeoff within the user's word limit; do not append every implementation consideration. Expand the record for requested design or setup work. Load only the selected tool's current [sources](sources.md#monorepo-strategy-and-tool-semantics) when translating those decisions into configuration.

Preview representative cases without publishing: a compatible leaf-package fix, a shared dependency break, a change to a private generator that alters public output, and an unrelated change that should not release anything. Compare the expected versions, release set, dependency metadata, notes, and installable artifacts. Select only the cases relevant to the changed policy and report which were actually exercised.
