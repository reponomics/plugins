export type SectionCounts = {
  total: number;
  met: number;
  unmet: number;
  notApplicable: number;
  unknown: number;
  decided: number;
  evidenceGaps: number;
};

/** The latest per-section counts Badge Buddy's controller reported. */
export type Snapshot = {
  project: string | null;
  projectId: number | null;
  sections: Record<string, SectionCounts>;
  conflicts: number;
  source: "status" | "apply";
  at: number;
};

/** A section Claude is recording answers for during the current turn. */
export type Filling = {
  section: string;
  startDecided: number;
  applies: number;
};

declare module "claude-code" {
  interface PluginState {
    "badge-progress": {
      snapshot: Shaped<Snapshot | null>;
      filling: Shaped<Filling | null>;
      autoOpened: boolean;
    };
  }
}
