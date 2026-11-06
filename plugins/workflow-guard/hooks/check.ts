// Line-based checks of GitHub Actions YAML: action pinning and the top-level
// permissions block. Pure functions, so they can be tested without the engine.
//
// Only what a change introduces is reported: a problem already present in
// the file before the change is left to the maintainer.

const WORKFLOW = /(^|\/)\.github\/workflows\/[^/]+\.ya?ml$/;
const ACTION = /(^|\/)action\.ya?ml$/;
const SHA = /^[0-9a-f]{40}$/;
const ALLOW_LINE = /#\s*workflow-guard:\s*allow\b/;
const ALLOW_PERMISSIONS = /^#\s*workflow-guard:\s*allow-permissions\b/m;

export type FileKind = "workflow" | "action";

export function fileKind(path: string): FileKind | null {
  if (WORKFLOW.test(path)) return "workflow";
  if (ACTION.test(path)) return "action";
  return null;
}

export type UsesRef = { ref: string; line: number };

/** External `uses:` references not pinned to a full commit SHA. */
export function unpinnedRefs(text: string): UsesRef[] {
  const found: UsesRef[] = [];
  text.split("\n").forEach((line, index) => {
    const match = /^\s*(?:-\s+)?uses:\s*(['"]?)([^'"\s#]+)\1/.exec(line);
    const ref = match?.[2];
    if (ref === undefined || ALLOW_LINE.test(line)) return;
    if (ref.startsWith("./") || ref.startsWith("docker://")) return;
    const at = ref.lastIndexOf("@");
    if (at > 0 && SHA.test(ref.slice(at + 1))) return;
    found.push({ ref, line: index + 1 });
  });
  return found;
}

export type Permissions = {
  state: "missing" | "none" | "read" | "write";
  line: number;
  writeScopes: string[];
};

/** The workflow's top-level `permissions:` setting. */
export function topLevelPermissions(text: string): Permissions {
  const lines = text.split("\n");
  const index = lines.findIndex((line) => /^permissions\s*:/.test(line));
  if (index < 0) return { state: "missing", line: 0, writeScopes: [] };
  const line = index + 1;
  const declared = lines[index] ?? "";
  if (ALLOW_LINE.test(declared))
    return { state: "none", line, writeScopes: [] };

  const inline = declared
    .replace(/^permissions\s*:/, "")
    .replace(/#.*$/, "")
    .trim();
  if (inline === "write-all")
    return { state: "write", line, writeScopes: ["write-all"] };
  if (inline === "read-all") return { state: "read", line, writeScopes: [] };

  let entries: string[];
  if (inline !== "") {
    // Flow mapping: `permissions: {}` or `permissions: { contents: read }`.
    entries = inline.replace(/^\{|\}$/g, "").split(",");
  } else {
    entries = [];
    for (const next of lines.slice(index + 1)) {
      if (/^\S/.test(next) && !next.startsWith("#")) break;
      entries.push(next);
    }
  }

  const writeScopes: string[] = [];
  let hasRead = false;
  for (const entry of entries) {
    if (ALLOW_LINE.test(entry)) continue;
    const match = /^\s*([\w-]+)\s*:\s*['"]?(read|write|none)['"]?/.exec(
      entry.replace(/#.*$/, ""),
    );
    if (match?.[2] === "write") writeScopes.push(match[1] ?? "");
    if (match?.[2] === "read") hasRead = true;
  }
  const state = writeScopes.length > 0 ? "write" : hasRead ? "read" : "none";
  return { state, line, writeScopes };
}

export type Finding = { line: number; message: string };

/**
 * Problems `after` introduces relative to `before`, which is null for a file
 * that does not exist yet.
 */
export function review(
  kind: FileKind,
  before: string | null,
  after: string,
): Finding[] {
  const findings: Finding[] = [];
  const existing = new Set(unpinnedRefs(before ?? "").map((item) => item.ref));
  for (const item of unpinnedRefs(after)) {
    if (existing.has(item.ref)) continue;
    findings.push({
      line: item.line,
      message:
        `\`${item.ref}\` is not pinned to a full commit SHA. Resolve the ref to its ` +
        `commit in the action's own repository and write it as ` +
        `\`<owner>/<repo>@<40-character SHA> # <version>\`.`,
    });
  }

  if (kind !== "workflow" || ALLOW_PERMISSIONS.test(after)) return findings;

  const was = before === null ? null : topLevelPermissions(before);
  const now = topLevelPermissions(after);
  if (now.state === "missing" && was?.state !== "missing") {
    findings.push({
      line: 1,
      message:
        "The workflow has no top-level `permissions:` block, so its jobs get the " +
        "repository's default token scopes. Add `permissions: {}` (no job reads the " +
        "repository with GITHUB_TOKEN) or `permissions:` with `contents: read`, and " +
        "grant any write scope on the job that needs it.",
    });
  }
  if (now.state === "write" && was?.state !== "write") {
    findings.push({
      line: now.line,
      message:
        `The top-level \`permissions:\` grants write access (${now.writeScopes.join(", ")}) ` +
        "to every job. Keep the top level read-only or empty and grant write scopes " +
        "on the jobs that need them.",
    });
  }
  return findings;
}

/** The file's content after an Edit, or null when `old` does not occur. */
export function applyEdit(
  text: string,
  old: string,
  replacement: string,
  replaceAll: boolean,
): string | null {
  if (old === "" || !text.includes(old)) return null;
  return replaceAll
    ? text.split(old).join(replacement)
    : text.replace(old, () => replacement);
}

export function report(path: string, findings: Finding[]): string {
  const lines = findings.map((item) => `- line ${item.line}: ${item.message}`);
  return [
    `workflow-guard: this change to ${path} would introduce:`,
    ...lines,
    "These correspond to the OpenSSF Scorecard Pinned-Dependencies and " +
      "Token-Permissions checks. If the user has explicitly asked for this, mark " +
      "the exception: `# workflow-guard: allow` at the end of a `uses:` or " +
      "`permissions:` line, or a `# workflow-guard: allow-permissions` comment " +
      "line to skip the permissions check for the file. A file meant as a " +
      "deliberately bad example belongs outside `.github/workflows/`, where it " +
      "is neither run nor checked. If it has to stay here, the user can " +
      "exclude the file by typing `/workflow-guard ignore <path>`; ask them " +
      "to, since only a command they type adds to that list.",
  ].join("\n");
}
