#!/usr/bin/env python3
"""Validate plugin versions and prepare drafts from maintainer-signed release tags."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
import time
from typing import Any
from urllib.parse import quote

MARKETPLACE = ".claude-plugin/marketplace.json"
NAME = re.compile(r"[a-z0-9][a-z0-9-]*")
SEMVER = re.compile(
    r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
)
REPOSITORY = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+")


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=check, capture_output=True, text=True)


def git(*args: str) -> str:
    return run("git", *args).stdout.strip()


def resolve(ref: str) -> str:
    return git("rev-parse", "--verify", "--end-of-options", ref + "^{commit}")


def _version(value: Any) -> tuple[str, bool]:
    match = SEMVER.fullmatch(value) if isinstance(value, str) else None
    if not match:
        raise ValueError(f"invalid plugin semantic version: {value!r}")
    prerelease = match.group(4)
    if prerelease and any(
        part.isdigit() and len(part) > 1 and part[0] == "0"
        for part in prerelease.split(".")
    ):
        raise ValueError(
            f"prerelease numeric identifiers cannot have leading zeroes: {value}"
        )
    return value, prerelease is not None


def _precedence(version: str) -> tuple:
    match = SEMVER.fullmatch(version)
    assert match is not None
    identifiers = tuple(
        (0, int(part)) if part.isdigit() else (1, part)
        for part in (match.group(4) or "").split(".")
    )
    return (*map(int, match.group(1, 2, 3)), match.group(4) is None, identifiers)


def _path(value: Any) -> str:
    if not isinstance(value, str) or not value.startswith("./"):
        raise ValueError("release entries must use local ./ plugin paths")
    raw = value[2:]
    if raw == "":
        return "."
    if not re.fullmatch(r"[A-Za-z0-9_.\-/]+", raw) or any(
        p in {"", ".", ".."} for p in raw.split("/")
    ):
        raise ValueError(f"unsafe plugin path: {value!r}")
    return str(PurePosixPath(raw))


def _json_at(ref: str, path: str) -> dict:
    payload = json.loads(git("show", f"{ref}:{path}"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return payload


def _local_plugin(ref: str, entry: Any) -> dict | None:
    if not isinstance(entry, dict):
        raise ValueError("invalid marketplace entry")
    # External plugins have their own repository's release lifecycle.
    if isinstance(entry.get("source"), dict):
        return None
    name, path = entry.get("name"), _path(entry.get("source"))
    if not isinstance(name, str) or NAME.fullmatch(name) is None:
        raise ValueError(f"invalid plugin name: {name!r}")
    manifest = _json_at(ref, str(PurePosixPath(path) / ".claude-plugin/plugin.json"))
    if manifest.get("name") != name:
        raise ValueError(f"{name}: plugin and marketplace names disagree")
    version, prerelease = _version(manifest.get("version"))
    return {"name": name, "path": path, "version": version, "prerelease": prerelease}


def plugins_at(ref: str) -> dict[str, dict]:
    entries = _json_at(ref, MARKETPLACE).get("plugins")
    if not isinstance(entries, list):
        raise ValueError("marketplace must contain a plugins array")
    plugins, paths = {}, set()
    for entry in entries:
        plugin = _local_plugin(ref, entry)
        if plugin is None:
            continue
        name, path = plugin["name"], plugin["path"]
        if name in plugins or path in paths:
            raise ValueError(f"duplicate plugin name/path: {name!r}")
        plugins[name] = plugin
        paths.add(path)
    return plugins


def plan(base: str = "HEAD^", head: str = "HEAD") -> dict:
    head_sha = resolve(head)
    base_sha = None if base == "empty" else resolve(base)
    previous = plugins_at(base_sha) if base_sha else {}
    changed = []
    for name, plugin in plugins_at(head_sha).items():
        old = previous.get(name, {}).get("version")
        if old == plugin["version"]:
            _check_catalog_version(plugin, base_sha, head_sha)
            continue
        if old is not None and not _valid_transition(name, old, plugin["version"]):
            raise ValueError(
                f"{name}: changed version must increase in SemVer precedence"
            )
        release_notes(plugin, head_sha)
        changed.append(
            {**plugin, "previous_version": old, "tag": f"{name}--v{plugin['version']}"}
        )
    return {"base": base_sha, "head": head_sha, "plugins": changed}


def _valid_transition(name: str, previous: str, version: str) -> bool:
    before, after = _precedence(previous), _precedence(version)
    if after >= before:
        return after > before  # Build metadata alone cannot be a version bump.
    return git("rev-parse", "--is-shallow-repository") == "false" and not git(
        "tag", "--list", f"{name}--v*"
    )


def _check_catalog_version(plugin: dict, base: str, head: str) -> None:
    if plugin["name"] != "badge-buddy":
        return
    path = str(PurePosixPath(plugin["path"]) / "assets/criteria/criteria.json")
    changed = run("git", "diff", "--quiet", base, head, "--", path, check=False)
    if changed.returncode == 1:
        raise ValueError(
            "badge-buddy criteria catalog changed without a plugin version bump"
        )
    if changed.returncode:
        raise subprocess.CalledProcessError(
            changed.returncode, changed.args, changed.stdout, changed.stderr
        )


def _notes_path(plugin: dict) -> str:
    return f"docs/release-notes/{plugin['name']}/{plugin['version']}.md"


def release_notes(plugin: dict, head: str) -> str:
    path = _notes_path(plugin)
    entry = git("ls-tree", head, "--", path)
    if not entry.startswith(("100644 blob ", "100755 blob ")):
        raise ValueError(f"missing regular reviewed release notes file: {path}")
    notes = run("git", "show", f"{head}:{path}").stdout
    if not notes.strip():
        raise ValueError(f"empty release notes: {path}")
    return notes


def _require_decision_commit(plugin: dict, head: str) -> None:
    parents = git("rev-list", "--parents", "-n", "1", head).split()[1:]
    if not parents or not git("ls-tree", parents[0], "--", MARKETPLACE):
        return
    old = plugins_at(parents[0]).get(plugin["name"])
    if (
        old
        and old["version"] == plugin["version"]
        and git("ls-tree", parents[0], "--", _notes_path(plugin))
    ):
        raise ValueError(
            "tag must point to the version decision or first reviewed notes commit"
        )


def verify_tag(tag: str, allowed_signers: Path) -> dict:
    """Read tagged data as Git objects. Never execute or check out the tagged tree."""
    match = re.fullmatch(r"([a-z0-9][a-z0-9-]*)--v([0-9]+\..+)", tag)
    if not match:
        raise ValueError("tag must be PLUGIN--vSEMVER")
    name, version = match.groups()
    _version(version)
    if git("rev-parse", "--is-shallow-repository") != "false":
        raise ValueError("verification requires full history and release tags")
    ref = f"refs/tags/{tag}"
    oid = git("rev-parse", "--verify", ref)
    if git("cat-file", "-t", oid) != "tag":
        raise ValueError("release requires a signed annotated tag")
    headers = git("cat-file", "tag", oid).split("\n\n", 1)[0].splitlines()
    if f"tag {tag}" not in headers or "type commit" not in headers:
        raise ValueError(
            "signed tag name or target type does not match its release ref"
        )
    # verify-tag detects signature format from the object, irrespective of gpg.format.
    # Disable the other verifiers: a trusted OpenPGP or X.509 key is not an SSH allowlist entry.
    git(
        "-c",
        "gpg.openpgp.program=false",
        "-c",
        "gpg.x509.program=false",
        "-c",
        f"gpg.ssh.allowedSignersFile={allowed_signers.resolve(strict=True)}",
        "verify-tag",
        oid,
    )
    head = resolve(oid)
    if run(
        "git",
        "merge-base",
        "--is-ancestor",
        head,
        "refs/remotes/origin/main",
        check=False,
    ).returncode:
        raise ValueError("signed commit is not reachable from origin/main")
    plugin = plugins_at(head).get(name)
    if not plugin or plugin["version"] != version:
        raise ValueError("tag does not match the registered plugin manifest")
    release_notes(plugin, head)
    _require_decision_commit(plugin, head)
    return {**plugin, "tag": tag, "head": head, "object": oid}


def api(endpoint: str, *args: str, missing: bool = False) -> dict | None:
    time.sleep(0.5)
    response = run("gh", "api", "--include", endpoint, *args, check=False)
    headers, _, body = response.stdout.replace("\r\n", "\n").partition("\n\n")
    status = re.match(r"HTTP/\S+ (\d+)", headers)
    if re.search(r"^x-ratelimit-remaining:\s*0\s*$", headers, re.I | re.M):
        raise ValueError(
            "GitHub API rate limit exhausted; inspect the draft before retrying"
        )
    if missing and status and status[1] == "404":
        return None
    if not status or not status[1].startswith("2") or response.returncode:
        raise ValueError(
            f"GitHub API {endpoint}: {response.stderr.strip() or headers.splitlines()[:1]}"
        )
    return json.loads(body)


ASSETS = ("osv-results.json", "scan-scope.md")


def evidence_digests(directory: Path) -> dict[str, str]:
    if {p.name for p in directory.iterdir()} != set(ASSETS):
        raise ValueError("expected exactly osv-results.json and scan-scope.md")
    hashes = {}
    for name in ASSETS:
        p = directory / name
        if p.is_symlink() or not p.is_file() or not p.stat().st_size:
            raise ValueError(f"empty or invalid evidence file: {name}")
        hashes[name] = "sha256:" + hashlib.sha256(p.read_bytes()).hexdigest()
    return hashes


def check_remote_ref(repository: str, plugin: dict) -> None:
    ref = api(f"repos/{repository}/git/ref/tags/{quote(plugin['tag'], safe='')}")
    target = ref["object"]
    if target.get("sha") != plugin["object"] or target.get("type") != "tag":
        raise ValueError("remote signed tag object changed; stop and investigate")


def _require_new_release(repository: str, tag: str) -> None:
    root = f"repos/{repository}/releases"
    if api(f"{root}/tags/{quote(tag, safe='')}", missing=True) is not None:
        raise ValueError(f"{tag}: release already exists; inspect it, never overwrite")
    # GraphQL includes an unpublished draft for callers with push access. The REST
    # by-tag endpoint alone is insufficient to distinguish it from a missing release.
    owner, repo = repository.split("/")
    data = api(
        "graphql",
        "-f",
        "query=query($o:String!,$r:String!,$t:String!){repository(owner:$o,name:$r){release(tagName:$t){id}}}",
        "-f",
        f"o={owner}",
        "-f",
        f"r={repo}",
        "-f",
        f"t={tag}",
    )
    if data["data"]["repository"]["release"] is not None:
        raise ValueError(f"{tag}: existing draft; inspect it before retrying")


def prepare_draft(repository: str, plugin: dict, directory: Path) -> dict:
    if not REPOSITORY.fullmatch(repository) or ".." in repository:
        raise ValueError("expected OWNER/REPO")
    hashes = evidence_digests(directory)
    check_remote_ref(repository, plugin)
    root = f"repos/{repository}/releases"
    tag = plugin["tag"]
    _require_new_release(repository, tag)
    payload = {
        "tag_name": tag,
        "name": f"{plugin['name']} {plugin['version']}",
        "body": release_notes(plugin, plugin["head"]),
        "target_commitish": plugin["head"],
        "draft": True,
        "prerelease": plugin["prerelease"],
        "make_latest": "false",
    }
    with tempfile.TemporaryDirectory() as temp:
        request = Path(temp) / "draft.json"
        request.write_text(json.dumps(payload))
        created = api(
            root,
            "--method",
            "POST",
            "-H",
            "Content-Type: application/json",
            "--input",
            str(request),
        )
    release_id = created["id"]
    if (
        not created.get("draft")
        or created.get("tag_name") != tag
        or type(release_id) is not int
    ):
        raise ValueError("unexpected GitHub draft response")
    for name in ASSETS:
        endpoint = f"https://uploads.github.com/{root}/{release_id}/assets?name={name}"
        path = directory / name
        asset = api(
            endpoint,
            "--method",
            "POST",
            "-H",
            "Content-Type: application/octet-stream",
            "-H",
            f"Content-Length: {path.stat().st_size}",
            "--input",
            str(path),
        )
        if asset.get("digest") != hashes[name] or asset.get("state") != "uploaded":
            raise ValueError(
                f"uploaded evidence mismatch for {name}; leave draft unpublished"
            )
    check_remote_ref(repository, plugin)
    print(f"Prepared draft {tag}. It has not been published.")
    return {
        **{key: plugin[key] for key in ("tag", "head", "object")},
        "draft_id": release_id,
        "assets": hashes,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("plan")
    prepare.add_argument("--base", default="HEAD^")
    prepare.add_argument("--head", default="HEAD")
    prepare.add_argument("--output", type=Path, required=True)
    tag_parser = argparse.ArgumentParser(add_help=False)
    tag_parser.add_argument("--tag", required=True)
    tag_parser.add_argument("--allowed-signers", type=Path, required=True)
    commands.add_parser("verify-tag", parents=[tag_parser])
    draft = commands.add_parser("draft", parents=[tag_parser])
    draft.add_argument("--receipt", type=Path, required=True)
    draft.add_argument("--object", required=True)
    draft.add_argument("--repository", required=True)
    draft.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "plan":
            result = plan(args.base, args.head)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2) + "\n")
            print(
                f"Planned {len(result['plugins'])} plugin version change(s): {args.output}"
            )
        else:
            plugin = verify_tag(args.tag, args.allowed_signers)
            if args.command == "draft":
                if args.object != plugin["object"]:
                    raise ValueError("signed tag changed since preflight")
                receipt = prepare_draft(args.repository, plugin, args.evidence)
                args.receipt.write_text(json.dumps(receipt) + "\n")
            else:
                print(
                    f"head={plugin['head']}\nobject={plugin['object']}\nplugin={plugin['name']}"
                )
                print(f"prerelease={str(plugin['prerelease']).lower()}")
        return 0
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.CalledProcessError,
    ) as error:
        print(f"Plugin release failed: {error}", file=sys.stderr)
        if isinstance(error, subprocess.CalledProcessError) and error.stderr:
            print(error.stderr.strip(), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
