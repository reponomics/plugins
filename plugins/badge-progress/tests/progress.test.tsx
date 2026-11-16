import { expect, test } from "claude-code/testing";
import type { On } from "claude-code";

function engine(on: On) {
  on("command.register", () => ({ value: { command: "badge-progress" } }));
  on("ui.open", () => ({ value: { isPlaced: true } }));
  on("session.start", (_, e) => ({ cwd: e.cwd }));
  on("tool.call", () => ({ result: {}, text: "legacy counts" }));
}

const PANE = {
  plugin: "badge-progress",
  component: "Pane",
  requestId: "badge-progress",
  props: {
    title: "Badge progress",
    isFocused: false,
    bodyColumns: 50,
    placement: "dock",
    scroll: { offset: 0, bodyRows: 20 },
    view: {},
  },
} as const;

test("shows the migration notice instead of persisted controller counts", async ($, on) => {
  engine(on);
  let reads = 0;
  on("store.get", () => {
    reads += 1;
    return { value: { project: "stale project", sections: { passing: { decided: 67, total: 67 } } } };
  });
  await $.session.start({ cwd: "/work/demo", surface: "terminal", isInteractive: true });
  for (const surface of ["terminal", "desktop", "vscode", "mobile"] as const) {
    const ui = await $.ui.mount({ ...PANE, surface });
    expect(await ui.find({ type: "Text", text: /tracking is paused/ })).toBeDefined();
    expect(await ui.find({ type: "Text", text: /stale project/ })).toBeUndefined();
    await ui.unmount();
  }
  expect(reads).toBe(0);
});

test("ordinary tools do not reopen legacy tracking", async ($, on) => {
  engine(on);
  await $.session.start({ cwd: "/work/demo", surface: "terminal", isInteractive: true });
  await $.tool.call({ tool: "Bash", command: "echo legacy" });
  const ui = await $.ui.mount({ ...PANE, surface: "terminal" });
  expect(await ui.find({ type: "Text", text: /local preview board/ })).toBeDefined();
  await ui.unmount();
});
