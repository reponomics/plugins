import { expect, mock, test } from "claude-code/testing";
import type { On } from "claude-code";

import {
  controllerCommand,
  parsePayload,
  sectionArgument,
} from "../hooks/parse";

const CONTROLLER = '"/plugins/badge-buddy/scripts/ossf.py" --repo "/work/demo"';

// The shape ossf.py prints for status and apply (abridged).
function payload(passing: { decided: number; total: number }) {
  return JSON.stringify({
    schema_version: 1,
    state: "registered",
    project: { name: "demo", project_id: 1234 },
    conflicts: [],
    sections: {
      passing: {
        total: passing.total,
        met: passing.decided - 2,
        unmet: 1,
        not_applicable: 1,
        unknown: passing.total - passing.decided,
        decided: passing.decided,
        evidence_gaps: 1,
      },
      silver: {
        total: 55,
        met: 0,
        unmet: 0,
        not_applicable: 0,
        unknown: 55,
        decided: 0,
        evidence_gaps: 0,
      },
    },
  });
}

// Stands for the engine beneath the plugin: Bash answers with `output`.
function engine(on: On, outputs: string[], toasts: string[] = []) {
  mock.store(on);
  mock.clock(on);
  on("session.cwd", () => ({ value: "/work/demo" }));
  on("command.register", () => ({ value: { command: "badge-progress" } }));
  on("ui.open", () => ({ value: { isPlaced: true } }));
  on("ui.toast", (_, e) => {
    toasts.push(e.text);
    return { value: undefined };
  });
  on("session.start", (_, e) => ({ cwd: e.cwd }));
  on("turn.complete", () => ({ text: "" }));
  on("tool.call", () => ({ result: {}, text: outputs.shift() ?? "" }));
  on("ui.render", ($, e) => {
    const { Text } = $.ui.resolve(e);
    return <Text>engine</Text>;
  });
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

const BAND = {
  plugin: "badge-progress",
  component: "AbovePrompt",
  props: {
    hasSurvey: false,
    isWorking: true,
    maxRows: 10,
    bodyColumns: 80,
    scroll: { offset: 0, bodyRows: 10 },
    view: {},
  },
} as const;

const TURN_END = {
  answer: "",
  durationMs: 1000,
  isAborted: false,
  turnId: "t1",
  reason: "answer",
} as const;

test("reads controller commands and their output", async () => {
  expect(controllerCommand(`${CONTROLLER} status`)).toBe("status");
  expect(
    controllerCommand(
      `${CONTROLLER} apply --section silver --input - <<'JSON'\n{}\nJSON`,
    ),
  ).toBe("apply");
  expect(controllerCommand(`${CONTROLLER} review --section passing`)).toBe(
    "other",
  );
  expect(controllerCommand("python3 other.py status")).toBe(null);
  expect(
    sectionArgument(`${CONTROLLER} apply --section baseline-2 --input -`),
  ).toBe("baseline-2");
  expect(
    sectionArgument(`${CONTROLLER} apply --input - <<'X'\n--section gold\nX`),
  ).toBe(null);

  const parsed = parsePayload(
    `warning: board refresh failed\n${payload({ decided: 40, total: 67 })}`,
    "status",
    0,
  );
  expect(parsed?.sections.passing?.decided).toBe(40);
  expect(parsed?.projectId).toBe(1234);
  expect(parsePayload("not json", "status", 0)).toBe(null);
  expect(parsePayload('{"sections": {}}', "status", 0)).toBe(null);
});

test("the pane shows the counts the controller reported, on every surface", async ($, on) => {
  engine(on, [payload({ decided: 40, total: 67 })]);
  await $.session.start({
    cwd: "/work/demo",
    surface: "terminal",
    isInteractive: true,
  });
  await $.tool.call({ tool: "Bash", command: `${CONTROLLER} status` });

  for (const surface of ["terminal", "desktop", "vscode", "mobile"] as const) {
    const ui = await $.ui.mount({ ...PANE, surface });
    expect((await ui.find({ type: "Text", text: /#1234/ }))?.text).toContain(
      "demo",
    );
    expect(await ui.find({ type: "Text", text: /40\/67/ })).toBeDefined();
    expect(
      await ui.find({ type: "Text", text: /missing required evidence/ }),
    ).toBeDefined();
    expect(
      await ui.find({ type: "Text", text: /Not started: Silver/ }),
    ).toBeDefined();
    await ui.unmount();
  }
});

test("the band tracks a turn of apply calls, then a toast sums it up", async ($, on) => {
  const toasts: string[] = [];
  engine(
    on,
    [
      payload({ decided: 40, total: 67 }),
      payload({ decided: 43, total: 67 }),
      payload({ decided: 45, total: 67 }),
    ],
    toasts,
  );
  await $.session.start({
    cwd: "/work/demo",
    surface: "terminal",
    isInteractive: true,
  });
  await $.tool.call({ tool: "Bash", command: `${CONTROLLER} status` });
  await $.tool.call({
    tool: "Bash",
    command: `${CONTROLLER} apply --section passing --input -`,
  });
  await $.tool.call({
    tool: "Bash",
    command: `${CONTROLLER} apply --section passing --input -`,
  });

  const band = await $.ui.mount({ ...BAND, surface: "terminal" });
  expect(
    await band.find({ type: "Text", text: /Filling Passing/ }),
  ).toBeDefined();
  expect(
    await band.find({ type: "Text", text: /45\/67 answered/ }),
  ).toBeDefined();
  expect(
    await band.find({ type: "Text", text: /\+5 this turn/ }),
  ).toBeDefined();
  await band.unmount();

  await $.turn.complete(TURN_END);
  expect(toasts).toEqual(["Passing: 45/67 answered (+5 this turn)"]);

  const after = await $.ui.mount({ ...BAND, surface: "terminal" });
  expect(await after.find({ type: "Text", text: /Filling/ })).toBeUndefined();
  expect(await after.find({ type: "Text", text: /engine/ })).toBeDefined();
  await after.unmount();
});

test("other commands and failed calls leave the counts alone", async ($, on) => {
  engine(on, [
    '{"sections": {"passing": {"total": 1}}}',
    payload({ decided: 1, total: 67 }),
  ]);
  await $.session.start({
    cwd: "/work/demo",
    surface: "terminal",
    isInteractive: true,
  });
  await $.tool.call({ tool: "Bash", command: "cat sections.json" });

  const ui = await $.ui.mount({ ...PANE, surface: "desktop" });
  expect(
    await ui.find({ type: "Text", text: /No Badge Buddy results yet/ }),
  ).toBeDefined();
  await ui.unmount();
});
