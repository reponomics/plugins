import type { Register } from "claude-code";

const PANE = "badge-progress";
const NOTICE =
  "Badge Progress tracking is paused while Badge Buddy moves to best-practices-mcp. Ask Badge Buddy to open its local preview board. Previous controller counts are not displayed because they may be stale.";

export const register: Register = (on) => {
  on("session.start", async ($, e, next) => {
    await $.command.register({
      name: "badge-progress",
      description: "Show the Badge Progress MCP migration notice",
    });
    return next(e);
  });

  on("command.run", { command: "badge-progress" }, async ($) => {
    await $.ui.open({ id: PANE, title: "Badge progress" });
    return { text: NOTICE };
  });

  on("ui.render", { component: "Pane", requestId: PANE }, async ($, e) => {
    const { Text } = $.ui.resolve(e);
    return <Text>{NOTICE}</Text>;
  });
};
