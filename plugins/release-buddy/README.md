# Release Buddy

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="../../docs/assets/release-buddy/release-buddy-dark-840x240.png">
  <img alt="Release Buddy: Release with confidence" src="../../docs/assets/release-buddy/release-buddy-light-840x240.png" width="840">
</picture>

Release Buddy helps small projects choose versions, write useful release notes, and publish verifiable releases on GitHub. Versioning guidance works on its own. Integrity setup supports public GitHub repositories distributing source or an existing primary build artifact; it starts with what users actually install.

> [!IMPORTANT]
> Release Buddy is an independent community project. It is not affiliated with, sponsored by, or endorsed by OpenSSF, The Linux Foundation, GitHub, or any registry. It helps prepare evidence; it does not award badges or certify security.

## Get started

Add the marketplace and install the plugin in Claude Code:

```sh
claude plugin marketplace add reponomics/plugins
claude plugin install release-buddy@reponomics
```

Ask, for example:

- “Which versioning workflow fits this project?”
- “Help us version the packages in this monorepo independently.”
- “We distribute source from GitHub. Help us make signed, immutable releases.”
- “We already build a CLI archive in Actions. Add build provenance and a verification command.”
- “We want an OpenSSF badge. Which release evidence is relevant?”
- “Include our OSV results in the release and explain what they cover.”
- “Write release instructions I can follow next time.”

Use `/release-buddy:release-versioning <request>` for versions, changelogs and release-tool selection. Use `/release-buddy:release-integrity <request>` for the supported GitHub release paths, a scoped review, or maintainer and consumer guides. Use `/release-buddy:explain [brief|extended] <term>` for optional explanations.

## Two release paths

| What users receive                                  | Starting point                                                                                                                                      | What needs verification                                                                                                                                                                                   |
| --------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Source from Git                                     | Keep the authoritative version source and reviewed notes. A maintainer signs the exact source tag; prepare and publish an immutable GitHub Release. | The tag signature matches an independently trusted signer and the intended version and commit. Immutability protects the published tag and attachments.                                                   |
| A primary archive or binary built in GitHub Actions | Keep the existing build. Prepare its tested output in a draft before publication; add build provenance when that is the required guarantee.         | The downloaded bytes match the release asset. A build-provenance check must also bind those bytes to the expected repository, workflow and source ref. A source signature alone does not verify a binary. |

Preserve a working setup and add only the missing part. Source releases do not need a new build, archive or build-provenance claim. Version bumps, signed tags and final publication are separate actions; identify who owns each one.

For badge-oriented projects, explain the concrete evidence each program expects. OpenSSF Best Practices, OSPS Baseline and Scorecard are different assessments. A signed tag and verification instructions do not guarantee a particular score. OSV reports can provide dated dependency evidence, but an ongoing monitoring and triage process matters too. Record scanner version, commit, inventory scope and outcome; a report about maintainer tooling is not a security assessment of the plugin's instructions.

## Versioning remains independent

Choose a version policy, authoritative version source, release units and useful notes without requiring signing setup. Keep manual releases when they fit; compare release-please, Changesets or semantic-release when automation would reduce work. Preserve existing tag-derived versions and distinguish a shared release schedule from shared version numbers.

## Scope and limits

Integrity setup does not provision npm or PyPI trusted publishers, publish containers, implement other registry release paths, or design enterprise signing infrastructure. For those requests, identify the boundary and link the provider's current documentation. Keep working registry configuration intact; a GitHub release does not establish the integrity of a package installed elsewhere. Concepts such as trusted publishing can still be explained.

The plugin supplies short documentation templates and adapts the project’s existing build and release process using current upstream documentation, verified action pins and scoped permissions. Optional OSV evidence is covered in the [release-operations guide](skills/release-integrity/references/release-operations.md#optional-osv-evidence).

Repository or account settings, signing-key changes and publication require authorization for those specific actions. A passing check or valid signature is evidence of its stated property, not proof that the code is free of vulnerabilities. Report local validation separately from hosted publication and consumer verification.
