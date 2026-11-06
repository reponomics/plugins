import { expect, mock, test } from "claude-code/testing";
import type { On } from "claude-code";

import { review, topLevelPermissions, unpinnedRefs } from "../hooks/check";
import { isIgnored, resolvePath } from "../hooks/ignore";

const SHA = "b4ffde65f46336ab88eb53be808477a3936bae11";
const PATH = "/work/demo/.github/workflows/ci.yml";

const pinned = `name: CI
on: push
permissions:
  contents: read
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@${SHA} # v4.1.1
      - run: make test
`;

// Stands for the engine: the file system holds `files`, and a tool call
// that gets through records its input.
function engine(
  on: On,
  files: Record<string, string>,
  ran: string[],
  stored: Record<string, unknown> = {},
) {
  mock.store(on, stored);
  on("session.cwd", () => ({ value: "/work/demo" }));
  on("fs.exists", (_, e) => ({ value: e.path in files }));
  on("fs.read", (_, e) => ({ value: files[e.path] ?? "" }));
  on("ui.toast", () => ({ value: undefined }));
  on("tool.call", (_, e) => {
    ran.push(e.tool);
    return { result: {}, text: "ok" };
  });
}

test("finds unpinned references, leaving local and allowed ones", async () => {
  const text = [
    `- uses: actions/checkout@${SHA}`,
    "- uses: actions/setup-node@v4",
    "- uses: 'org/repo/.github/workflows/build.yml@main'",
    "- uses: ./.github/actions/local",
    "- uses: docker://alpine:3",
    "- uses: some/action@v1 # workflow-guard: allow",
  ].join("\n");
  expect(unpinnedRefs(text).map((item) => item.ref)).toEqual([
    "actions/setup-node@v4",
    "org/repo/.github/workflows/build.yml@main",
  ]);
});

test("classifies the top-level permissions block", async () => {
  expect(topLevelPermissions("on: push\njobs: {}").state).toBe("missing");
  expect(topLevelPermissions("permissions: {}").state).toBe("none");
  expect(topLevelPermissions("permissions: read-all").state).toBe("read");
  expect(topLevelPermissions("permissions: write-all").state).toBe("write");
  expect(topLevelPermissions("permissions: { contents: read }").state).toBe(
    "read",
  );
  expect(topLevelPermissions(pinned).state).toBe("read");
  const broad = topLevelPermissions(
    "permissions:\n  contents: write\n  id-token: write\njobs:\n  a:\n    permissions:\n      packages: write",
  );
  expect(broad.writeScopes).toEqual(["contents", "id-token"]);
  // A job's own write scope is not top-level.
  expect(
    topLevelPermissions(
      "permissions: {}\njobs:\n  a:\n    permissions:\n      contents: write",
    ).state,
  ).toBe("none");
});

test("reports only what a change introduces", async () => {
  const legacy =
    "on: push\njobs:\n  a:\n    steps:\n      - uses: actions/checkout@v3\n";
  // Untouched old problems are not reported.
  expect(review("workflow", legacy, legacy + "      - run: echo hi\n")).toEqual(
    [],
  );
  // A new file is judged whole.
  expect(review("workflow", null, legacy).length).toBe(2);
  // Removing the permissions block is new; so is a top-level write scope.
  expect(
    review(
      "workflow",
      pinned,
      pinned.replace("permissions:\n  contents: read\n", ""),
    )[0]?.message,
  ).toContain("no top-level `permissions:`");
  expect(
    review(
      "workflow",
      pinned,
      pinned.replace("contents: read", "contents: write"),
    )[0]?.message,
  ).toContain("contents");
  // A composite action is checked for pinning only.
  expect(
    review(
      "action",
      null,
      "runs:\n  using: composite\n  steps:\n    - uses: a/b@v1\n",
    ).length,
  ).toBe(1);
  expect(
    review("workflow", null, "# workflow-guard: allow-permissions\non: push\n"),
  ).toEqual([]);
});

test("blocks a Write that adds an unpinned action", async ($, on) => {
  const ran: string[] = [];
  engine(on, {}, ran);
  const result = await $.tool.call({
    tool: "Write",
    file_path: PATH,
    content: pinned.replace(
      `actions/checkout@${SHA} # v4.1.1`,
      "actions/checkout@v4",
    ),
  });
  expect(result.deny).toContain("`actions/checkout@v4` is not pinned");
  expect(ran).toEqual([]);
});

test("lets a clean Edit through, and ignores other files", async ($, on) => {
  const ran: string[] = [];
  engine(on, { [PATH]: pinned }, ran);
  const edit = await $.tool.call({
    tool: "Edit",
    file_path: PATH,
    old_string: "      - run: make test",
    new_string: "      - run: make check",
  });
  expect(edit.deny).toBeUndefined();
  const other = await $.tool.call({
    tool: "Write",
    file_path: "/work/demo/notes.yml",
    content: "uses: a/b@v1",
  });
  expect(other.deny).toBeUndefined();
  expect(ran).toEqual(["Edit", "Write"]);
});

test("blocks an Edit that widens top-level permissions", async ($, on) => {
  const ran: string[] = [];
  engine(on, { [PATH]: pinned }, ran);
  const result = await $.tool.call({
    tool: "Edit",
    file_path: PATH,
    old_string: "contents: read",
    new_string: "contents: write",
  });
  expect(result.deny).toContain("grants write access (contents)");
});

test(
  "warn mode lets the change through and tells Claude",
  { options: { mode: "warn" } },
  async ($, on) => {
    const ran: string[] = [];
    engine(on, {}, ran);
    const result = await $.tool.call({
      tool: "Write",
      file_path: PATH,
      content: "on: push\n",
    });
    expect(result.deny).toBeUndefined();
    expect(ran).toEqual(["Write"]);
    expect(result.context?.join("\n")).toContain("no top-level `permissions:`");
  },
);

test("resolves and matches ignored paths", async () => {
  expect(resolvePath("/work/demo", "./.github/workflows/bad.yml/")).toBe(
    "/work/demo/.github/workflows/bad.yml",
  );
  expect(resolvePath("/work/demo/sub", "../x//y.yml")).toBe(
    "/work/demo/x/y.yml",
  );
  const ignored = [
    "/work/demo/.github/workflows/bad.yml",
    "/work/demo/examples",
  ];
  expect(isIgnored("/work/demo/.github/workflows/bad.yml", ignored)).toBe(true);
  expect(
    isIgnored("/work/demo/examples/.github/workflows/ci.yml", ignored),
  ).toBe(true);
  expect(isIgnored("/work/demo/examples-old/action.yml", ignored)).toBe(false);
  expect(isIgnored("/work/demo/.github/workflows/ci.yml", ignored)).toBe(false);
});

test("lets a Write to an ignored path through unchecked", async ($, on) => {
  const ran: string[] = [];
  engine(on, {}, ran, { ignored: [PATH] });
  const result = await $.tool.call({
    tool: "Write",
    file_path: PATH,
    content: "on: push\njobs:\n  a:\n    steps:\n      - uses: a/b@v1\n",
  });
  expect(result.deny).toBeUndefined();
  expect(ran).toEqual(["Write"]);
});

test("adds to the ignore list only from a typed command", async ($, on) => {
  const ran: string[] = [];
  engine(on, {}, ran);
  const bad = "on: push\n";
  const write = () =>
    $.tool.call({ tool: "Write", file_path: PATH, content: bad });
  const run = (args: string, kind: "composer" | "sdk") =>
    $.command.run({
      command: "workflow-guard",
      args,
      origin: { kind },
      presentation: { isFullscreen: false, columns: 100 },
    });

  const refused = await run("ignore .github/workflows/ci.yml", "sdk");
  expect(refused.text).toContain("only when the user types");
  expect((await write()).deny).toBeDefined();

  const added = await run("ignore .github/workflows/ci.yml", "composer");
  expect(added.text).toBe("workflow-guard: ignoring .github/workflows/ci.yml.");
  expect((await run("list", "sdk")).text).toContain(".github/workflows/ci.yml");
  expect((await write()).deny).toBeUndefined();

  // Removing an entry needs no typed command: it only turns checks back on.
  await run("unignore .github/workflows/ci.yml", "sdk");
  expect((await write()).deny).toBeDefined();
  expect((await run("", "sdk")).text).toBe(
    "workflow-guard: nothing is ignored.",
  );
});
