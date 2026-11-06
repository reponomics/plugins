# Writing application answers

A justification is public text written in the project's voice. Answer the criterion directly, using the information available about the project and what the user has told you.

## Voice and detail

- Use plain, declarative language in the project’s voice, without narrating what the user said or what the assistant investigated.
- Write facts supplied by the user in the same voice as other project information. Do not add distancing phrases such as “the maintainer claims” or “not independently verified” merely because the information came from them.
- A sentence or a relevant URL may be enough. Include every requested detail, such as measurements, time periods, applicability, and required URLs; brevity is not a fixed word limit.
- Omit information that does not help answer the criterion. Avoid names, version numbers, commit counts, and other changing details unless needed. Do not add prestige claims or assurances such as “we take security very seriously.”
- Preserve the user's meaning and qualifications. Do not turn “usually” into “always,” or a planned practice into an existing one.
- Describe the current practice without recounting earlier drafts, corrections, or the assistant's work. Mention history when the criterion actually asks about it.

## Links

Include the URLs the criterion requires and other links that directly support the answer. Prefer Markdown autolinks such as `<https://example.com/guide>`, with punctuation outside the brackets, unless the user prefers labeled links. Existing answers need no rewrite just to change link style.

## Concise answers from BadgeApp

These are verbatim answers from the bundled BadgeApp questionnaire. They illustrate an appropriate amount of detail; use the current project's own facts when drafting.

**Baseline Level 1, `OSPS-GV-02.01` — Met.** The criterion asks for public discussion mechanisms:

> GitHub provides issues and pull requests. We also use a mailing list.

**Passing, `build` — N/A.** The answer explains why building is unnecessary:

> The software is written using Ruby and Javascript, and their implementations run directly on the source code.

**Silver, `external_dependencies` — Met.** The answer identifies the dependency list and supplies the required URL:

> External dependencies are stored in a [Gemfile](https://github.com/ossf/best-practices-badge/blob/main/Gemfile).

**Gold, `dynamic_analysis_enable_assertions` — Unmet.** This SHOULD criterion asks for assertions in the produced software; the answer describes the alternative the project chose:

> Instead of embedding run-time assertions, there are many external tests with assertions that are checked during automated testing.

For a SHOULD practice the project has chosen not to adopt, explain its actual reason and relevant tradeoff. When it intends to adopt an unmet practice, distinguish the current situation from the plan. Do not invent a rationale or commitment.

When the user asks how BadgeApp answered another criterion, or another example would clarify the expected wording, use the [example lookup](badgeapp-example.md) to retrieve only that answer.

Examples: David A. Wheeler and the OpenSSF Best Practices badge contributors, under [CDLA-Permissive-2.0](../../../assets/examples/badgeapp/CDLA-Permissive-2.0.txt).
