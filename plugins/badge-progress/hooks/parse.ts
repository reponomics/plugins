// Reads Badge Buddy controller (ossf.py) commands and their JSON output.
// Pure functions, so they can be tested without the engine.

import type { SectionCounts, Snapshot } from "../types";

export const SECTIONS = [
  "passing",
  "silver",
  "gold",
  "baseline-1",
  "baseline-2",
  "baseline-3",
] as const;

const LABELS: Record<string, string> = {
  passing: "Passing",
  silver: "Silver",
  gold: "Gold",
  "baseline-1": "Baseline 1",
  "baseline-2": "Baseline 2",
  "baseline-3": "Baseline 3",
};

export const sectionLabel = (section: string): string =>
  LABELS[section] ?? section;

export type ControllerCommand = "status" | "apply" | "other";

// The part of a shell command before any heredoc body, which may hold
// arbitrary JSON (apply --input - <<'JSON' ...).
const head = (command: string): string => command.split("<<")[0] ?? command;

/** Which controller command a Bash command runs, or null when it runs none. */
export function controllerCommand(command: string): ControllerCommand | null {
  const text = head(command);
  if (!/ossf\.py\b/.test(text)) return null;
  const match = /ossf\.py['"]?\s(?:[^\n]*?\s)?(status|apply)(?=\s|$)/.exec(
    text,
  );
  return (match?.[1] as ControllerCommand | undefined) ?? "other";
}

/** The value of `--section`, when the command names one. */
export function sectionArgument(command: string): string | null {
  const match = /--section(?:=|\s+)['"]?([a-z0-9-]+)/.exec(head(command));
  return match?.[1] ?? null;
}

const count = (value: unknown): number =>
  typeof value === "number" && Number.isFinite(value) ? value : 0;

/**
 * The counts from a status or apply payload, or null when the text is not
 * one. Warnings on stderr may precede the JSON object.
 */
export function parsePayload(
  text: string,
  source: Snapshot["source"],
  at: number,
): Snapshot | null {
  const start = text.indexOf("{");
  const end = text.lastIndexOf("}");
  if (start < 0 || end <= start) return null;
  let payload: unknown;
  try {
    payload = JSON.parse(text.slice(start, end + 1));
  } catch {
    return null;
  }
  if (typeof payload !== "object" || payload === null) return null;
  const record = payload as Record<string, unknown>;
  const raw = record.sections;
  if (typeof raw !== "object" || raw === null) return null;

  const sections: Record<string, SectionCounts> = {};
  for (const section of SECTIONS) {
    const entry = (raw as Record<string, unknown>)[section];
    if (typeof entry !== "object" || entry === null) continue;
    const c = entry as Record<string, unknown>;
    const total = count(c.total);
    const unknown = count(c.unknown);
    sections[section] = {
      total,
      met: count(c.met),
      unmet: count(c.unmet),
      notApplicable: count(c.not_applicable),
      unknown,
      decided: typeof c.decided === "number" ? c.decided : total - unknown,
      evidenceGaps: count(c.evidence_gaps),
    };
  }
  if (sections.passing === undefined) return null;

  const project = (record.project ?? {}) as Record<string, unknown>;
  return {
    project: typeof project.name === "string" ? project.name : null,
    projectId:
      typeof project.project_id === "number" ? project.project_id : null,
    sections,
    conflicts: Array.isArray(record.conflicts) ? record.conflicts.length : 0,
    source,
    at,
  };
}

/** A text progress bar `width` cells wide, split into filled and empty runs. */
export function bar(
  done: number,
  total: number,
  width: number,
): [string, string] {
  const cells = Math.max(1, Math.floor(width));
  const filled = total > 0 ? Math.round((done / total) * cells) : 0;
  return ["█".repeat(filled), "░".repeat(cells - filled)];
}
