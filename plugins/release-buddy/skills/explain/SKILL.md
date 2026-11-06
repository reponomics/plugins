---
name: explain
description: Explain a release-versioning or release-integrity term or concept (for example SemVer, prerelease, changeset, SBOM, attestation, trusted publishing) at the depth the user asks for, in terms of their own project.
argument-hint: "[brief|extended] <term or question>"
disable-model-invocation: true
---

# Explain

The user asked for an explanation of: $ARGUMENTS

A leading `brief` or `extended`, or wording such as "briefly" or "in depth", sets the depth. Without one, use the default.

- **brief**: one or two sentences.
- **default**: a short paragraph: what it is, and what it means for the user's project if the conversation or repository shows how it applies (for example, "with immutable releases on, the `v1.2.0` tag can never be reused").
- **extended**: also how it works, its tradeoffs or limits, and the upstream page to read.

At any depth, check current platform behavior, commands, and defaults against their owning upstream source before asserting them. Use the [versioning sources](../release-versioning/references/sources.md) or [integrity sources](../release-integrity/references/sources.md) to find the relevant page; a stable conceptual definition does not require a full reference tour. If a current detail cannot be checked, omit it when unnecessary or state the uncertainty briefly.

Use plain language and no more jargon than the term itself; gloss any other term the explanation needs. If the request is ambiguous or outside release versioning and integrity, answer briefly and say so. Then return to the work in progress, if any.
