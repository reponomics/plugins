// The ignore list: absolute paths of files or directories the guard leaves
// alone. It lives in the plugin's own store, outside the repository, and only
// the person adds to it, with `/workflow-guard ignore <path>`.

/** `path` made absolute against `cwd`, with `.`, `..` and repeated or trailing slashes resolved. */
export function resolvePath(cwd: string, path: string): string {
  const joined = path.startsWith("/") ? path : `${cwd}/${path}`;
  const parts: string[] = [];
  for (const part of joined.split("/")) {
    if (part === "" || part === ".") continue;
    if (part === "..") parts.pop();
    else parts.push(part);
  }
  return "/" + parts.join("/");
}

/** Whether `path` is an ignored file or lies under an ignored directory. */
export function isIgnored(path: string, ignored: readonly string[]): boolean {
  return ignored.some(
    (entry) =>
      path === entry || path.startsWith(entry === "/" ? "/" : `${entry}/`),
  );
}

/** The stored list, with anything that is not a string dropped. */
export function asList(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

/** `path` relative to `cwd` when it lies under it, for display. */
export function shown(cwd: string, path: string): string {
  return path.startsWith(`${cwd}/`) ? path.slice(cwd.length + 1) : path;
}
