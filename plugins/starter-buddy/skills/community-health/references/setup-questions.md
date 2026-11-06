# Setup questions

Use the repository and conversation to identify the choices still needed. Introduce the defaults briefly: “I'll start with short templates and preserve what's useful. You can skip anything or explore the options.” These are suggested topics, not a question limit or a mandatory interview.

## Suggested wording

| Topic         | Question                                            | Suggested choices                                                                    | Useful context                                                                                                                |
| ------------- | --------------------------------------------------- | ------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| Contributions | What contributions do you want to welcome?          | Code; documentation; ideas and reports; not accepting contributions yet              | Multiple kinds can be welcome. Accepting submissions does not promise to accept every contribution.                           |
| Issues        | Which issue categories would be useful?             | Bugs; suggestions; documentation; none for now                                       | A general report can also cover several needs. Keep blank issues enabled by default.                                          |
| PR template   | Add a short pull request template?                  | Add one; skip                                                                        | It asks what changed and how it was checked. Documentation PRs can benefit even when code contributions are closed.           |
| License       | Have you chosen a license?                          | Use my chosen license; discuss options; leave it for later                           | Explain general facts and differences when helpful; use the maintainer's selection.                                           |
| Conduct       | Add a code of conduct?                              | Adopt a policy; discuss options; skip                                                | Adoption needs a private reporting contact and someone responsible for handling reports.                                      |
| Security      | How should people report vulnerabilities privately? | Enable GitHub private reporting; use an existing private contact; leave it for later | Check GitHub eligibility. Establish the supported versions or branch and who will monitor reports before finalizing a policy. |

Adapt choices and follow-ups to what the user needs. Resolve contradictory selections before writing public guidance. More templates, explanations, or customizations are welcome when the user is interested; otherwise use suitable defaults and continue.

## Asking conversationally or with a tool

Use ordinary conversation or the available question tool. Follow its current schema and per-call limits, grouping related questions into manageable batches. Contributions and issue categories may allow multiple selections; mutually exclusive choices such as “none” need clarification if selected alongside another option. A tool's free-text response can capture an answer outside the suggested choices.

State proposed file locations in the plan rather than asking about each one by default. Discuss placement or any other topic when it would help the user. If a decision remains unanswered, continue the work that does not depend on it.

For GitHub private reporting, establish repository visibility and eligibility using [security reporting](security-reporting.md). Make an enablement question concrete—for example, “Enable GitHub private vulnerability reporting for OWNER/REPO?” Use a clear prior instruction as authorization rather than asking the user to repeat it. See [GitHub operations](github-operations.md) for delivery and setting scope.
