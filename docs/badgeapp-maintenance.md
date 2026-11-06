# BadgeApp guidance sources

The skill's [application guide](../plugins/badge-buddy/skills/ossf-bp-badges/references/application.md) describes application behavior. This document records the sources used to maintain that guidance; these revisions do not identify the deployed site's revision.

## Transfers and API

The general review used BadgeApp revision `6452a0c299ef6358e6ef89fbdd0c24fb7da3b7a9`: [automation-proposals.md](https://github.com/ossf/best-practices-badge/blob/6452a0c299ef6358e6ef89fbdd0c24fb7da3b7a9/docs/automation-proposals.md), [bestpractices-json.md](https://github.com/ossf/best-practices-badge/blob/6452a0c299ef6358e6ef89fbdd0c24fb7da3b7a9/docs/bestpractices-json.md), [automation-approach.md](https://github.com/ossf/best-practices-badge/blob/6452a0c299ef6358e6ef89fbdd0c24fb7da3b7a9/docs/automation-approach.md), and [api.md](https://github.com/ossf/best-practices-badge/blob/6452a0c299ef6358e6ef89fbdd0c24fb7da3b7a9/docs/api.md).

The code resolves two discrepancies in `automation-proposals.md`: proposals ignore `?` rather than resetting the answer, and forced wording changes work with an unchanged status. See the [controller](https://github.com/ossf/best-practices-badge/blob/6452a0c299ef6358e6ef89fbdd0c24fb7da3b7a9/app/controllers/projects_controller.rb#L1802), [unknown-status tests](https://github.com/ossf/best-practices-badge/blob/6452a0c299ef6358e6ef89fbdd0c24fb7da3b7a9/test/controllers/projects_controller_test.rb#L3465), and [wording tests](https://github.com/ossf/best-practices-badge/blob/6452a0c299ef6358e6ef89fbdd0c24fb7da3b7a9/test/controllers/projects_controller_test.rb#L3594).

Repository imports have confidence 3.5, below Chief's override threshold of 4. Comments describing them as overridable are misleading. See [RepoJsonDetective](https://github.com/ossf/best-practices-badge/blob/6452a0c299ef6358e6ef89fbdd0c24fb7da3b7a9/app/lib/repo_json_detective.rb) and [Chief](https://github.com/ossf/best-practices-badge/blob/6452a0c299ef6358e6ef89fbdd0c24fb7da3b7a9/app/lib/chief.rb).

Login recovery precedence was checked separately at revision `e4c99b5460f809aa2efd6d78445d3f5fa2379bd3`: [recovered drafts apply after proposals](https://github.com/ossf/best-practices-badge/blob/e4c99b5460f809aa2efd6d78445d3f5fa2379bd3/app/controllers/projects_controller.rb#L670).

The URL lookup redirect `?as=edit&url=…` shows the project list and loses proposals for zero or multiple matches. The badge redirect `?as=badge&url=…` returns 404 for none and 409 for multiple. API prefix search uses `pq=`, full-text search uses `q=`, and pagination uses `page=N` until an empty page; explicit `/en/` paths and alphabetically ordered parameters improve cache reuse. The controller resolves a numeric project ID before preparing proposals.

At the general review revision, `api.md` incorrectly links to `basepractices-json.md`, and `automation-approach.md` once uses `best-practices.json`; the supported repository locations are `.bestpractices.json` and `.project.d/bestpractices.json`.

The controller's `--staging` option targets upstream's development environment, which restores production data during deployment and is not offered as an applicant testing service.

## Baseline interpretation

The Baseline references use the [2026-08-28 OSPS definitions](https://baseline.openssf.org/versions/2026-08-28). The [released legal guidance](https://github.com/ossf/security-baseline/blob/v2026.08.28/baseline/OSPS-LE.yaml#L39) includes the qualification about older projects being unable to enforce contributor authorization retroactively; BadgeApp's copied details omit it.

Metal/Baseline comparisons were checked against the catalog and [mapping explanations](https://github.com/ossf/best-practices-badge/blob/e4c99b5460f809aa2efd6d78445d3f5fa2379bd3/criteria/metal_to_baseline_map.yml). At that revision, the [GitHub detective](https://github.com/ossf/best-practices-badge/blob/e4c99b5460f809aa2efd6d78445d3f5fa2379bd3/app/lib/github_basic_detective.rb#L101-L108) suggests MFA compliance at confidence 3 from GitHub's requirement, without querying private settings or establishing other hosts' configuration. Gold review mapped to Baseline merge approval has confidence 1 because its timing, coverage, and enforcement differ.

Generate criterion IDs and validation flags from the upstream Metal and Baseline criterion files through the [catalog maintenance process](criteria-maintenance.md); do not maintain a second hand-written ID inventory.
