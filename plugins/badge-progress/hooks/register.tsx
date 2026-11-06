import { atom, read, update } from "claude-code";
import type { Register } from "claude-code";

import type { Filling, SectionCounts, Snapshot } from "../types";
import {
  SECTIONS,
  bar,
  controllerCommand,
  parsePayload,
  sectionArgument,
  sectionLabel,
} from "./parse";

const PANE = "badge-progress";
const TITLE = "Badge progress";

// Change a tag when the stored shape changes, so values an earlier version
// stored are read as the initial value instead.
const snapshot = atom(
  { plugin: "badge-progress", key: "snapshot" } as const,
  null,
  { shape: "snapshot-1" },
);
const filling = atom(
  { plugin: "badge-progress", key: "filling" } as const,
  null,
  { shape: "filling-1" },
);
const autoOpened = atom(
  { plugin: "badge-progress", key: "autoOpened" } as const,
  false,
);

// The last snapshot is kept per project directory, so the pane has
// something to show at the start of the next session.
const storeKey = (cwd: string) => `snapshot:${cwd}`;

const pad = (text: string, width: number) =>
  text.length >= width ? text : text + " ".repeat(width - text.length);

const clock = (at: number) => {
  const date = new Date(at);
  const two = (n: number) => String(n).padStart(2, "0");
  return `${two(date.getHours())}:${two(date.getMinutes())}`;
};

export const register: Register = (on) => {
  on("session.start", async ($, e, next) => {
    await $.command.register({
      name: "badge-progress",
      description: "Show OpenSSF badge application progress in a pane",
    });
    const current = await read($, snapshot);
    if (current === null) {
      const saved = await $.store.get(storeKey(e.cwd));
      if (saved && typeof saved === "object") {
        await update($, snapshot, () => saved as Snapshot);
      }
    }
    return next(e);
  });

  on("command.run", { command: "badge-progress" }, async ($) => {
    await $.ui.open({ id: PANE, title: TITLE });
    return { text: "Badge progress pane opened." };
  });

  on("tool.call", { tool: "Bash" }, async ($, e, next) => {
    const ran = await next(e);
    const kind = controllerCommand(e.command);
    if (kind !== "status" && kind !== "apply") return ran;
    if (ran.deny !== undefined || ran.isError) return ran;

    const now = await $.clock.now();
    const latest = parsePayload(ran.text ?? "", kind, now);
    if (latest === null) return ran;

    const previous = await read($, snapshot);
    await update($, snapshot, () => latest);
    await $.store.set(storeKey(await $.session.cwd()), latest);

    const section = kind === "apply" ? sectionArgument(e.command) : null;
    const counts = section === null ? undefined : latest.sections[section];
    if (section !== null && counts !== undefined) {
      const before = previous?.sections[section]?.decided ?? counts.decided;
      await update($, filling, (current) =>
        current !== null && current.section === section
          ? { ...current, applies: current.applies + 1 }
          : { section, startDecided: before, applies: 1 },
      );
    }

    if (!(await read($, autoOpened))) {
      await update($, autoOpened, () => true);
      void $.ui.open({ id: PANE, title: TITLE });
    }
    return ran;
  }).catch(($, e, next) => next(e));

  on("turn.complete", async ($, e, next) => {
    const result = await next(e);
    if (e.agentId !== undefined) return result;
    const current = await read($, filling);
    if (current === null) return result;
    await update($, filling, () => null);

    const counts = (await read($, snapshot))?.sections[current.section];
    if (counts !== undefined) {
      const delta = counts.decided - current.startDecided;
      const change =
        delta === 0 ? "no change" : `${delta > 0 ? "+" : ""}${delta}`;
      $.ui.toast(
        `${sectionLabel(current.section)}: ${counts.decided}/${counts.total} answered (${change} this turn)`,
      );
    }
    return result;
  });

  // The progress band, shown while a turn is recording answers.
  on("ui.render", { component: "AbovePrompt" }, async ($, e, next) => {
    if (e.props.hasSurvey || !e.props.isWorking) return next(e);
    const current: Filling | null = await read($, filling);
    if (current === null) return next(e);
    const counts = (await read($, snapshot))?.sections[current.section];
    if (counts === undefined) return next(e);

    const { Box, Text } = $.ui.resolve(e);
    const label = `Filling ${sectionLabel(current.section)} `;
    const tail = ` ${counts.decided}/${counts.total} answered`;
    const delta = counts.decided - current.startDecided;
    const note = delta > 0 ? ` · +${delta} this turn` : "";
    const room = e.props.bodyColumns - label.length - tail.length - note.length;
    const [filled, empty] = bar(
      counts.decided,
      counts.total,
      Math.min(30, room),
    );

    return (
      <Box>
        <Text>{label}</Text>
        <Text color="success">{filled}</Text>
        <Text dimColor>{empty}</Text>
        <Text>{tail}</Text>
        <Text dimColor>{note}</Text>
      </Box>
    );
  });

  on("ui.render", { component: "Pane", requestId: PANE }, async ($, e) => {
    const { Box, Text } = $.ui.resolve(e);
    const latest = await read($, snapshot);
    if (latest === null) {
      return (
        <Text dimColor>
          No Badge Buddy results yet. They appear once Claude runs the badge
          controller's status or apply command.
        </Text>
      );
    }
    const current = await read($, filling);
    const columns = e.props.bodyColumns;
    const barWidth = Math.max(6, Math.min(30, columns - 22));

    const started: [string, SectionCounts][] = [];
    const notStarted: string[] = [];
    for (const section of SECTIONS) {
      const counts = latest.sections[section];
      if (counts === undefined) continue;
      if (
        counts.decided > 0 ||
        section === current?.section ||
        section === "passing"
      ) {
        started.push([section, counts]);
      } else {
        notStarted.push(sectionLabel(section));
      }
    }

    const heading =
      latest.projectId !== null
        ? `${latest.project ?? "Project"} · bestpractices.dev #${latest.projectId}`
        : `${latest.project ?? "Project"} · not registered`;

    return (
      <Box flexDirection="column">
        <Text bold>{heading}</Text>
        <Text dimColor>
          Updated {clock(latest.at)} from {latest.source}
        </Text>
        <Text> </Text>
        {started.map(([section, counts]) => {
          const isActive = section === current?.section;
          const [filled, empty] = bar(counts.decided, counts.total, barWidth);
          return (
            <Box flexDirection="column">
              <Box>
                <Text bold={isActive}>
                  {isActive ? "▸ " : "  "}
                  {pad(sectionLabel(section), 11)}
                </Text>
                <Text color="success">{filled}</Text>
                <Text dimColor>{empty}</Text>
                <Text>
                  {" "}
                  {counts.decided}/{counts.total}
                </Text>
              </Box>
              <Text dimColor>
                {"    "}Met {counts.met} · Unmet {counts.unmet} · N/A{" "}
                {counts.notApplicable} · ? {counts.unknown}
              </Text>
              {counts.evidenceGaps > 0 && (
                <Text color="warning">
                  {"    "}
                  {counts.evidenceGaps} answer
                  {counts.evidenceGaps === 1 ? "" : "s"} missing required
                  evidence
                </Text>
              )}
            </Box>
          );
        })}
        {notStarted.length > 0 && (
          <Text dimColor>Not started: {notStarted.join(", ")}</Text>
        )}
        {latest.conflicts > 0 && (
          <Text color="warning">
            {latest.conflicts} difference{latest.conflicts === 1 ? "" : "s"}{" "}
            with the website to resolve
          </Text>
        )}
      </Box>
    );
  });
};
