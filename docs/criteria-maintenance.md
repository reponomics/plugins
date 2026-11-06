# Criteria maintenance

Badge Buddy ships a local criteria catalog with each plugin version. Its guidance and preview aim to match the wording and presentation of the public bestpractices.dev application. Ordinary plugin use reads this catalog without downloading criterion pages; assessment synchronization separately fetches public project answers through the API.

The catalog is generated from a pinned [BadgeApp](https://github.com/ossf/best-practices-badge) checkout and its English translations. Before accepting an update, maintainer tooling compares it with the public application pages for Passing, Silver, Gold, and Baseline levels 1–3. The comparison covers criterion identifiers, order, descriptions, details, links, and the requirement markings visible on those pages. Submission flags not exposed in the downloaded HTML remain repository-derived.

## Check for a change

From the repository root:

```sh
make download-criteria
make compare-criteria
```

These commands compare the bundled catalog with a fresh application snapshot without updating the catalog. A difference is a signal to investigate and, when appropriate, select an upstream revision to accept.

Downloads are anonymous, limited to a fixed set of English application pages, and paced at no more than one request per second. Snapshots and comparison reports are stored under `.cache/criteria/`. Comparisons can be repeated locally from the saved snapshot. Project responses and justifications are excluded from extraction and comparison.

## Accept a selected upstream revision

Use a clean BadgeApp checkout at the revision you intend to accept, then run:

```sh
make refresh-upstream BADGE_REPO=../best-practices-badge
git diff -- plugins/badge-buddy/assets/criteria/ THIRD_PARTY_NOTICES.md
```

`refresh-upstream` downloads the application pages, generates a candidate from the checkout, and verifies that candidate against the saved snapshot before replacing the bundled catalog. An incomplete download or unexplained difference stops the update and leaves the bundled catalog unchanged. Review changes to criterion text, identifiers, order, and flags, and review affected guidance as described below. Then run `make check`, increase Badge Buddy's manifest version, and open a normal pull request. The release planner rejects catalog changes without a version increase.

To create a new checkout, use `make checkout-upstream BADGE_REPO=/new/checkout`; it defaults to the bundled catalog's revision. Set `UPSTREAM_REF` to the deliberately selected commit or ref when preparing an update. Keep the accepted revision until relevant upstream inputs change: moving to an unrelated commit can change catalog provenance even when criterion content is identical.

The catalog records its repository revision separately from [website verification provenance](../plugins/badge-buddy/assets/criteria/verification.json); a repository revision is not a claim about the deployed revision. An unchanged refresh retains the last accepted observation, while the local comparison report records the latest check.

For diagnostics, `refresh-criteria` verifies and refreshes from an existing snapshot; `check-criteria` checks agreement among the selected checkout, bundled catalog, and saved snapshot. These do not need to follow a successful `refresh-upstream`. Checkout and refresh commands accept `BADGE_REPO`; snapshot commands also accept `CRITERIA_SNAPSHOT`.

## Review related guidance

[upstream-review-paths.txt](../upstream-review-paths.txt) is a manual review inventory of upstream criteria, documentation, controller code, and tests. No workflow or maintenance tool monitors those paths. The weekly website comparison cannot detect changes to transfer behavior or other authored guidance.

Source: docs/automation-proposals.md; docs/bestpractices-json.md; docs/automation-approach.md; docs/api.md; criteria/criteria.yml; criteria/baseline_criteria.yml; docs/implementation.md; docs/INSTALL.md. The inventory also includes the controller, its tests, RepoJsonDetective, and Chief used to check the automation guidance.

When updating guidance, inspect the listed paths from that guidance's last-reviewed revision to the selected checkout. The [BadgeApp guidance sources](badgeapp-maintenance.md) record the general review revision used below:

```sh
GUIDANCE_REF=6452a0c299ef6358e6ef89fbdd0c24fb7da3b7a9
sed '/^#/d; /^$/d' upstream-review-paths.txt | xargs git -C ../best-practices-badge diff "$GUIDANCE_REF" HEAD --
```

If a shallow checkout lacks the review revision, run `git -C ../best-practices-badge fetch origin "$GUIDANCE_REF"` before the diff. This retrieves the revision without changing the selected checkout.

Use the revision recorded in the particular guidance being reviewed, rather than assuming the catalog revision is its review baseline. Separately cited changes may have a later review revision, such as the login-recovery controller detail in the guidance sources. Review affected instructions and update their citations only after checking the relevant changes; catalog refreshes do not advance human-reviewed guidance pins. Document unresolved differences that affect users explicitly.

## Release and automation

Weekly checks download the public application pages, compare the bundled catalog, and retain evidence without modifying files in Git or creating PRs. Routine tests remain offline against saved fixtures.

PRs that change files under Badge Buddy’s `assets/criteria/` run fresh website verification. Changing the bundled catalog requires a version decision for Badge Buddy. Preparing a signed Badge Buddy release repeats the live check against that exact commit; releases of other plugins do not run it. Use `make release-check BADGE_REPO=../best-practices-badge` to run the live check and local tests yourself. See [plugin releases](releases.md) for the release procedure.

Downloaded content is used under the website's published terms and licensing. Retain the OpenSSF Best Practices badge contributors' attribution and the applicable notices when distributing derived material. Respect the site's robots policy and rate limits.
