"""Publish a reviewed draft from the successful preparation run printed in its summary."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

import plugin_release as release


def check_run(run: dict, tag: str) -> None:
    expected = {
        "path": ".github/workflows/release.yml",
        "event": "workflow_dispatch",
        "head_branch": "main",
        "display_title": f"Prepare {tag}",
        "conclusion": "success",
        "status": "completed",
    }
    if any(run.get(key) != value for key, value in expected.items()):
        raise ValueError(
            "RUN must be the successful Prepare run on main for this exact tag"
        )


def load_receipt(repo: str, run_id: str, tag: str, directory: Path) -> dict:
    result = release.api(f"repos/{repo}/actions/runs/{run_id}")
    check_run(result, tag)
    # A short ref named "main" could also identify a tag. Trust the workflow
    # code only if the repository's main branch actually contains its SHA.
    sha = result["head_sha"]
    if not re.fullmatch(r"[a-f0-9]{40}", sha):
        raise ValueError("invalid workflow commit")
    comparison = release.api(f"repos/{repo}/compare/{sha}...main?per_page=1")
    if comparison.get("status") not in {"identical", "ahead"}:
        raise ValueError(
            "preparation workflow commit is not on the repository's main branch"
        )
    name = f"release-subject-{int(result['run_attempt'])}"
    release.run(
        "gh",
        "run",
        "download",
        run_id,
        "--repo",
        repo,
        "--name",
        name,
        "--dir",
        str(directory),
    )
    return json.loads((directory / "receipt.json").read_text())


def check_receipt(receipt: dict, plugin: dict) -> None:
    if any(receipt.get(field) != plugin[field] for field in ("tag", "head", "object")):
        raise ValueError("prepared tag differs from the signed tag; do not publish")
    if type(receipt.get("draft_id")) is not int or receipt["draft_id"] <= 0:
        raise ValueError("missing draft ID in preparation receipt")
    assets = receipt["assets"]
    if set(assets) != set(release.ASSETS) or not all(
        re.fullmatch(r"sha256:[a-f0-9]{64}", h) for h in assets.values()
    ):
        raise ValueError("preparation receipt missing release evidence digests")


def check_draft(record: dict, plugin: dict, receipt: dict) -> None:
    expected = {
        "id": receipt["draft_id"],
        "tag_name": plugin["tag"],
        "name": f"{plugin['name']} {plugin['version']}",
        "prerelease": plugin["prerelease"],
    }
    if any(record.get(key) != value for key, value in expected.items()):
        raise ValueError("release metadata differs from signed tag or draft receipt")
    # GitHub may normalize line endings when storing the body.
    notes = release.release_notes(plugin, plugin["head"]).strip()
    if record["body"].replace("\r\n", "\n").strip() != notes:
        raise ValueError("release notes differ from the file at the signed commit")
    assets = {
        a["name"]: a["digest"] for a in record["assets"] if a["state"] == "uploaded"
    }
    if len(record["assets"]) != len(release.ASSETS) or assets != receipt["assets"]:
        raise ValueError(
            "release assets differ from the successful scan; do not publish"
        )


def finalize(repo: str, tag: str, run_id: str) -> None:
    if (
        not release.REPOSITORY.fullmatch(repo)
        or ".." in repo
        or not re.fullmatch(r"[1-9][0-9]*", run_id)
        or not tag
    ):
        raise ValueError(
            "copy REPO=owner/repo TAG=plugin--vVERSION RUN=id from the Prepare workflow summary"
        )
    base = f"repos/{repo}"
    if release.api(f"{base}/actions/variables/RELEASE_REPOSITORY")["value"] != repo:
        raise ValueError("release preparation is not enabled for this repository")
    with tempfile.TemporaryDirectory(prefix="release-receipt-") as temp:
        root = Path(temp)
        signers = root / "allowed_signers"
        signers.write_text(
            release.api(f"{base}/actions/variables/RELEASE_ALLOWED_SIGNERS")["value"]
            + "\n"
        )
        plugin = release.verify_tag(tag, signers)
        receipt = load_receipt(repo, run_id, tag, root / "subject")
    check_receipt(receipt, plugin)
    endpoint = f"{base}/releases/{receipt['draft_id']}"
    record = release.api(endpoint)
    check_draft(record, plugin, receipt)
    release.check_remote_ref(repo, plugin)
    if record["draft"]:
        if release.api(f"{base}/immutable-releases").get("enabled") is not True:
            raise ValueError(
                "enable release immutability in repository settings first; draft left unpublished"
            )
        print(
            f"Publishing verified draft {repo} {tag} ({plugin['head'][:12]})",
            flush=True,
        )
        release.api(
            endpoint,
            "--method",
            "PATCH",
            "-F",
            "draft=false",
            "-f",
            "make_latest=false",
        )
    published = release.api(endpoint)
    if published.get("immutable") is not True or published["draft"]:
        raise ValueError(
            "GitHub did not confirm an immutable published release; inspect it before taking further action"
        )
    check_draft(published, plugin, receipt)
    release.check_remote_ref(repo, plugin)
    release.run("gh", "release", "verify", tag, "--repo", repo)
    print(f"Verified immutable release: {published['html_url']}")


def main() -> int:
    try:
        finalize(*(os.environ.get(key, "") for key in ("REPO", "TAG", "RUN")))
        return 0
    except (
        KeyError,
        OSError,
        ValueError,
        TypeError,
        subprocess.CalledProcessError,
    ) as exc:
        print(f"Release finalization stopped: {exc}", file=sys.stderr)
        if isinstance(exc, subprocess.CalledProcessError) and exc.stderr:
            print(exc.stderr.strip(), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
