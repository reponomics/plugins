# Signing the source release

Start with an existing authorized signing method and consumer requirements. SSH signing is a practical default when no method exists; retain a working GPG setup. Consult [Git and GitHub sources](sources.md#source-signing) for the installed Git version and operating system before giving commands. Creating or replacing a key is a separate authorized action.

## Establish signer trust

Identify the maintainer authorized to approve the release. Publish the public key and its complete fingerprint through a channel consumers can authenticate independently of the candidate release. A key copied from the tag being verified does not establish its own authority. For SSH verification, use an allowed-signers file containing approved public keys and appropriate principals, restricted to the Git signing namespace. For GPG, authenticate the full key fingerprint before importing or trusting it. Never invent a key, fingerprint, principal or claimed verification result.

Keep private signing material with the maintainer or their existing approved signing service, away from the public software distribution site. Do not copy the private key into the repository or Actions as a shortcut. Record who controls it, how a replacement is announced, and which versions an old key covers. Key rotation and compromise need different treatment; preserve historical identity information and consult the project's security policy when a key is suspected compromised.

## Tags

A source release requires a signed annotated tag for the intended commit and version. Inspect the tag object itself, its signature, its signed tag name and its direct target. A lightweight tag pointing at a signed commit does not sign the version name. A valid tag object copied under another ref retains its signature but names the original release; reject that mismatch.

Use the established tag format, including plugin or package prefixes where applicable. For a Claude Code plugin, the manifest version controls the advertised update; creating a signed tag does not itself change that manifest or make an installer verify the signature. State whether the user will consume the verified tree or a separately resolved installation. Verify the signer against the independent trust material and confirm the commit matches the reviewed source, manifest and notes before pushing. Retain both the tag object ID and peeled commit ID. Re-signing the same name at the same commit can create a different tag object; do not replace an announced tag.

When release tooling creates tags, confirm that it can reuse the maintainer's signed tag or deliberately change tag ownership. Do not allow two tools to compete for the same name. Immutable GitHub releases protect a published tag but do not retroactively turn an unsigned tag into a signed one.

## Commits and existing policies

Commit signing can be useful but is not a prerequisite for this release path. Preserve existing `gpg.format`, `user.signingkey` and signing scope when only tag signing is requested. Verify local signatures independently of GitHub's display. Before proposing a signed-commit rule, check each automation that pushes commits and whether its actual creation path produces accepted signatures. Configure neither a rule nor vigilant mode merely because source tags are being signed.
