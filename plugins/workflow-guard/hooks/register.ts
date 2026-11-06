import type {
  CommandRunResult,
  EngineInterface,
  Register,
  ToolCallResult,
} from "claude-code";

import { applyEdit, fileKind, report, review } from "./check";
import type { FileKind } from "./check";
import { asList, isIgnored, resolvePath, shown } from "./ignore";

async function readExisting(
  $: EngineInterface,
  path: string,
): Promise<string | null> {
  if (!(await $.fs.exists(path))) return null;
  return $.fs.read(path);
}

// Blocks the call, or in warn mode lets it run and appends the report to
// what the model reads after the result.
async function judge(
  $: EngineInterface,
  mode: string,
  message: string | null,
  run: () => Promise<ToolCallResult>,
): Promise<ToolCallResult> {
  if (message === null) return run();
  if (mode !== "warn") return { deny: message };
  const ran = await run();
  if (ran.deny !== undefined || ran.isError) return ran;
  $.ui.toast("workflow-guard: a workflow change needs attention");
  return { ...ran, context: [...(ran.context ?? []), message] };
}

const messageFor = (
  path: string,
  kind: FileKind,
  before: string | null,
  after: string,
): string | null => {
  const findings = review(kind, before, after);
  return findings.length === 0 ? null : report(path, findings);
};

const IGNORED = "ignored";

const ignoredPaths = async ($: EngineInterface) =>
  asList(await $.store.get(IGNORED));

// The kind of file the guard checks at `path`, or null when it is not one or
// the person has put it on the ignore list.
async function guarded(
  $: EngineInterface,
  path: string,
): Promise<FileKind | null> {
  const kind = fileKind(path);
  if (kind === null) return null;
  const absolute = resolvePath(await $.session.cwd(), path);
  return isIgnored(absolute, await ignoredPaths($)) ? null : kind;
}

const USAGE =
  "Usage: /workflow-guard list | ignore <path> | unignore <path>\n" +
  "An ignored file or directory is not checked. The list is kept in the " +
  "plugin's own store, not in the repository.";

async function command(
  $: EngineInterface,
  args: string,
  typed: boolean,
): Promise<CommandRunResult> {
  const [action = "list", ...rest] = args.trim().split(/\s+/);
  const target = rest.join(" ").replace(/^(['"])(.*)\1$/, "$2");
  const cwd = await $.session.cwd();
  const list = await ignoredPaths($);

  if (action === "list" || action === "") {
    if (list.length === 0)
      return { text: "workflow-guard: nothing is ignored." };
    const lines = list.map((path) => `  ${shown(cwd, path)}`);
    return { text: ["workflow-guard ignores:", ...lines].join("\n") };
  }
  if ((action !== "ignore" && action !== "unignore") || target === "") {
    return { text: USAGE };
  }

  const path = resolvePath(cwd, target);
  if (action === "unignore") {
    if (!list.includes(path)) {
      return { text: `workflow-guard: ${shown(cwd, path)} was not ignored.` };
    }
    await $.store.set(
      IGNORED,
      list.filter((entry) => entry !== path),
    );
    return { text: `workflow-guard: checking ${shown(cwd, path)} again.` };
  }
  // Adding turns checks off, so it takes the person's own command.
  if (!typed) {
    return {
      text:
        "workflow-guard: a path is added to the ignore list only when the " +
        "user types `/workflow-guard ignore <path>` themselves.",
    };
  }
  if (!list.includes(path)) await $.store.set(IGNORED, [...list, path]);
  return { text: `workflow-guard: ignoring ${shown(cwd, path)}.` };
}

export const register: Register = (on, options) => {
  const mode = String(options.mode ?? "block");

  on("session.start", async ($, e, next) => {
    await $.command.register({
      name: "workflow-guard",
      description: "List, add or remove paths Workflow Guard does not check",
      argumentHint: "[list | ignore <path> | unignore <path>]",
    });
    return next(e);
  });

  on("command.run", { command: "workflow-guard" }, ($, e) =>
    command($, e.args, e.origin.kind === "composer"),
  );

  on("tool.call", { tool: "Write" }, async ($, e, next) => {
    const kind = await guarded($, e.file_path);
    if (kind === null) return next(e);
    const before = await readExisting($, e.file_path);
    return judge(
      $,
      mode,
      messageFor(e.file_path, kind, before, e.content),
      () => next(e),
    );
  }).catch(($, e, next) => next(e));

  on("tool.call", { tool: "Edit" }, async ($, e, next) => {
    const kind = await guarded($, e.file_path);
    if (kind === null) return next(e);
    const before = await readExisting($, e.file_path);
    if (before === null) return next(e);
    const after = applyEdit(
      before,
      e.old_string,
      e.new_string,
      e.replace_all === true,
    );
    // An edit whose old text is absent fails in the tool itself.
    if (after === null) return next(e);
    return judge($, mode, messageFor(e.file_path, kind, before, after), () =>
      next(e),
    );
  }).catch(($, e, next) => next(e));
};
