// Run against a generated mixed-answer board in an existing Playwright CLI tab:
// make check-board-browser PLAYWRIGHT_SESSION=assessment
// Serve the generated fixture over local HTTP for response-replacement checks.
async (page) => {
  const check = (condition, message) => { if (!condition) throw new Error(message); };
  const base = page.url().split("#")[0];
  await page.goto(base);
  const original = await page.locator("#assessment-data").textContent().then(JSON.parse);
  const orderedIds = original.criteria.map((criterion) => criterion.id);
  check(original.buckets.length === 4, "Exactly four response buckets are required");
  check(original.buckets.reduce((sum, bucket) => sum + bucket.count, 0) === original.total, "Bucket counts must sum to total");
  check(original.refreshSeconds === 5, "Keep the five-second refresh");
  check(await page.locator("#bucket-grid a").count() === 5, "Overview needs five destinations");
  check((await page.locator(".tool-name").textContent()).includes("reponomics."), "Correct the wordmark");

  const inspectList = async (ids) => {
    const articles = await page.locator("#criterion-list article").evaluateAll((nodes) => nodes.map((node) => ({
      id: node.dataset.criterion,
      key: node.querySelector("[data-field=criterion-key]").textContent,
      heading: node.querySelector("[data-field=criterion-title]").tagName,
      description: node.querySelector("[data-field=criterion-title]").textContent,
      status: node.querySelector("[data-field=current-status]").textContent,
      justification: node.querySelector("[data-field=current-justification]").textContent,
      navigation: node.querySelectorAll('a[href^="#"], button, input, textarea').length,
      evidence: Boolean(node.querySelector(".criterion-evidence")),
    })));
    check(JSON.stringify(articles.map((article) => article.id)) === JSON.stringify(ids), "List must contain every matching criterion in catalog order");
    const toc = await page.locator("#toc-list li").evaluateAll((items) => items.map((item) => ({
      number: item.value, text: item.textContent,
    })));
    check(toc.length === ids.length, "Every article needs a ToC entry");
    for (const [index, id] of ids.entries()) {
      const position = orderedIds.indexOf(id) + 1;
      const criterion = original.criteria[position - 1];
      const answer = original.answers[id];
      check(articles[index].description === criterion.description, `Changed description: ${id}`);
      check(articles[index].status === (answer.status === "?" ? "? — Not yet answered" : answer.status), `Wrong response: ${id}`);
      check(articles[index].justification === (answer.justification || "No justification added yet."), `Changed justification: ${id}`);
      check(toc[index].number === position && toc[index].text === criterion.displayId, `Unstable ToC identity: ${id}`);
      check(articles[index].key.startsWith(`${position}. ${criterion.displayId}`), `Unstable article number: ${id}`);
      check(articles[index].heading === "H2" && articles[index].navigation === 0 && articles[index].evidence, `Invalid article content: ${id}`);
    }
    const validLabels = await page.evaluate(() => {
      const ids = [...document.querySelectorAll("[id]")].map((node) => node.id);
      return new Set(ids).size === ids.length && [...document.querySelectorAll("[aria-labelledby]")].every((node) =>
        node.getAttribute("aria-labelledby").split(/\s+/).every((id) => document.getElementById(id)));
    });
    check(validLabels, "Unique IDs and valid accessible labels are required");
  };

  for (const bucket of original.buckets) {
    await page.locator(`#nav-${bucket.key}`).click();
    await page.locator("#list-view").waitFor({ state: "visible" });
    await inspectList(bucket.criterionIds);
    await page.locator("#back-overview").click();
    await page.locator("#overview-view").waitFor({ state: "visible" });
  }
  await page.locator("#nav-all").focus();
  await page.keyboard.press("Enter");
  await page.locator("#list-view").waitFor({ state: "visible" });
  check(page.url().endsWith("#view=all"), "Keyboard navigation must open All criteria");
  await inspectList(orderedIds);
  const targetId = orderedIds[Math.floor(orderedIds.length / 3)];
  await page.locator(`#toc-${targetId}`).focus();
  await page.keyboard.press("Enter");
  check(await page.evaluate((id) => document.activeElement.dataset.criterion === id, targetId), "ToC must focus the article");
  const afterAnchor = await page.evaluate(() => scrollY);
  await page.evaluate(() => window.scrollBy(0, 1800));
  await page.waitForEvent("load", { timeout: 8000 });
  check((await page.evaluate(() => scrollY)) > afterAnchor + 1200, "Refresh must preserve reading beyond the anchor");
  check(await page.evaluate((id) => document.activeElement.dataset.criterion === id, targetId), "Refresh must preserve keyboard focus");
  check(page.url().endsWith(`#view=all/${targetId}`), "Refresh must retain the current list");
  await page.locator(".skip-link").focus();
  await page.keyboard.press("Enter");
  check(await page.locator("#list-view").isVisible(), "Skip link must not switch views");
  check(await page.evaluate(() => document.activeElement.id) === "main", "Skip link must focus main");

  for (const width of [1440, 600, 375]) {
    await page.setViewportSize({ width, height: 1000 });
    const geometry = await page.locator("#criterion-list article").evaluateAll((nodes) => nodes.map((node) => {
      const rect = node.getBoundingClientRect();
      return { left: rect.left, right: rect.right, top: rect.top, bottom: rect.bottom };
    }));
    check(geometry.every((rect, index) => rect.left >= 0 && rect.right <= width &&
      (index === 0 || rect.top >= geometry[index - 1].bottom)), `Articles must form one column at ${width}px`);
    check(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `Horizontal overflow at ${width}px`);
    await page.locator("#criterion-list article").last().scrollIntoViewIfNeeded();
    await page.locator("#back-overview").focus();
    await page.keyboard.press("Enter");
    await page.locator("#overview-view").waitFor({ state: "visible" });
    check(await page.evaluate(() => document.activeElement.id) === "overview-title", "Overview heading must receive focus");
    await page.locator("#nav-all").click();
    await page.locator("#list-view").waitFor({ state: "visible" });
  }

  const links = await page.evaluate(() => {
    const target = document.createElement("div");
    renderEvidence('<https://example.org/explicit!> [doc](https://example.org/docs_(v1)) https://example.org/bare.,;:!?', target);
    return [...target.querySelectorAll("a")].map((link) => link.href);
  });
  check(JSON.stringify(links) === JSON.stringify([
    "https://example.org/explicit!", "https://example.org/docs_(v1)", "https://example.org/bare",
  ]), "Evidence URLs must preserve Markdown boundaries and trim prose punctuation");

  // Deliver regenerated HTML on the real reload timer, without changing the browser's in-memory assessment.
  const html = await page.request.get(base).then((response) => response.text());
  const changed = JSON.parse(JSON.stringify(original));
  const revisionId = original.criteria.find((criterion) => criterion.naAllowed)?.id;
  check(revisionId, "Fixture needs a criterion that permits N/A");
  const update = (status, justification) => {
    changed.answers[revisionId] = { status, justification };
    for (const bucket of changed.buckets) {
      bucket.criterionIds = orderedIds.filter((id) => ({ Met: "met", Unmet: "unmet", "N/A": "na", "?": "needs_input" })[changed.answers[id].status] === bucket.key);
      bucket.count = bucket.criterionIds.length;
    }
  };
  await page.route(base, (route) => route.fulfill({ contentType: "text/html", body: html.replace(
    /(<script id="assessment-data" type="application\/json">)[\s\S]*?(<\/script>)/,
    (_match, open, close) => open + JSON.stringify(changed).replace(/</g, "\\u003c") + close,
  ) }));
  try {
    update("Unmet", "Original wording.");
    await page.goto(`${base}#view=unmet`);
    await page.locator(`#toc-${revisionId}`).click();
    for (const wording of ["First revised justification.", "Approved wording. <script>window.injected=true</script>"]) {
      update("Unmet", wording);
      await page.waitForEvent("load", { timeout: 8000 });
      const article = page.locator(`[data-criterion="${revisionId}"]`);
      check(await article.locator("[data-field=current-status]").textContent() === "Unmet", "Provisional revision must remain Unmet");
      check(await article.locator("[data-field=current-justification]").textContent() === wording, "Revised wording must appear exactly");
      check(!(await page.evaluate(() => window.injected)), "Justifications must render as text");
    }
    update("N/A", changed.answers[revisionId].justification);
    await page.waitForEvent("load", { timeout: 8000 });
    check(await page.locator("#list-title").textContent() === "Unmet", "Approved move must not switch the current view");
    check(await page.locator(`[data-criterion="${revisionId}"]`).count() === 0, "Approved criterion must leave source bucket");
    check(await page.locator(`#toc-${revisionId}`).count() === 0, "Approved criterion must leave source ToC");
    await page.locator("#back-overview").click();
    await page.locator("#overview-view").waitFor({ state: "visible" });
    await page.locator("#nav-na").click();
    check(await page.locator(`[data-criterion="${revisionId}"] [data-field=current-justification]`).textContent() === changed.answers[revisionId].justification, "Destination must show exact approved wording");
    for (const answer of Object.values(changed.answers)) if (answer.status === "Unmet") answer.status = "?";
    update("N/A", changed.answers[revisionId].justification);
    await page.goto(`${base}#view=unmet`);
    await page.locator("#empty-list").waitFor({ state: "visible", timeout: 8000 });
    await page.waitForEvent("load", { timeout: 8000 });
    check(page.url().endsWith("#view=unmet") && await page.locator("#toc-list li").count() === 0, "Empty bucket must survive refresh");
  } finally {
    await page.unroute(base);
    await page.goto(`${base}#view=all`);
    await page.reload();
  }
  return { criteria: original.total, widths: [1440, 600, 375], checks: "dashboard, full lists, ToCs, stable numbering, labels, focus, scroll, five-second refresh, two wording revisions, approved move, empty bucket, safe text" };
}
