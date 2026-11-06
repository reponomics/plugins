"use strict";

const assessment = JSON.parse(document.querySelector("#assessment-data").textContent);
const elements = Object.fromEntries([
  "overview-view", "list-view", "project-id", "section-name",
  "bucket-grid", "answered-count", "total-count", "overview-title", "list-title",
  "list-description", "toc-list", "criterion-list", "empty-list",
].map((id) => [id.replace(/-([a-z])/g, (_match, letter) => letter.toUpperCase()), document.getElementById(id)]));
const criteria = new Map(assessment.criteria.map((criterion, index) =>
  [criterion.id, { ...criterion, number: index + 1 }]));
const views = new Map(assessment.buckets.map((bucket) => [bucket.key, bucket]));
views.set("all", {
  label: "All criteria",
  description: "Read all criteria and current answers together in this badge section.",
  criterionIds: [...criteria.keys()],
  count: assessment.total,
});
let currentView;

function answerFor(criterionId) {
  return assessment.answers[criterionId] || { status: "?", justification: "" };
}

function renderContext() {
  elements.projectId.textContent = `Project: ${assessment.projectId}`;
  const level = assessment.section.replace("baseline-", "Baseline ");
  elements.sectionName.textContent = `Level: ${level.charAt(0).toUpperCase()}${level.slice(1)}`;
  const unanswered = assessment.buckets.find((item) => item.key === "needs_input")?.count || 0;
  elements.answeredCount.textContent = String(assessment.total - unanswered);
  elements.totalCount.textContent = String(assessment.total);
}

function renderDashboard() {
  views.forEach((view, key) => {
    const card = document.createElement("a");
    card.href = `#view=${key}`;
    card.id = `nav-${key}`;
    card.className = "bucket-card";
    card.dataset.view = key;
    card.setAttribute("aria-label", `${view.label}: ${view.count} criteria`);
    const copy = document.createElement("div");
    const heading = document.createElement("h2");
    const detail = document.createElement("p");
    heading.textContent = view.label;
    detail.textContent = view.description;
    copy.append(heading, detail);
    const total = document.createElement("span");
    total.className = "bucket-count";
    total.textContent = String(view.count);
    total.setAttribute("aria-hidden", "true");
    card.append(copy, total);
    elements.bucketGrid.append(card);
  });
}

function createCriterion(criterionId, viewKey) {
  const article = document.querySelector("#criterion-template").content.firstElementChild.cloneNode(true);
  article.id = `view=${viewKey}/${criterionId}`;
  article.dataset.criterion = criterionId;
  const targets = {};
  article.querySelectorAll("[data-field]").forEach((element) => {
    element.id = `${criterionId}-${element.dataset.field}`;
    const key = element.dataset.field.replace(/-([a-z])/g, (_match, letter) => letter.toUpperCase());
    targets[key] = element;
  });
  [article, ...article.querySelectorAll("[data-labelled-by]")].forEach((element) => {
    element.setAttribute("aria-labelledby", `${criterionId}-${element.dataset.labelledBy}`);
  });
  renderCriterion(criterionId, targets);
  return article;
}

function renderList(view, key) {
  elements.listTitle.textContent = view.label;
  elements.listDescription.textContent = `${view.count} ${view.count === 1 ? "criterion" : "criteria"}`;
  elements.criterionList.replaceChildren();
  elements.tocList.replaceChildren();
  elements.emptyList.hidden = view.count > 0;
  elements.emptyList.textContent = `No criteria in ${view.label}.`;
  view.criterionIds.forEach((id) => {
    const criterion = criteria.get(id);
    const article = createCriterion(id, key);
    const item = document.createElement("li");
    item.value = criterion.number;
    const link = document.createElement("a");
    link.href = `#${article.id}`;
    link.id = `toc-${id}`;
    link.textContent = criterion.displayId;
    item.append(link);
    elements.tocList.append(item);
    elements.criterionList.append(article);
  });
}

function showSelection(event) {
  // The first part selects a page; the rest is an ordinary in-page anchor.
  const key = location.hash.slice(1).split("/")[0].replace(/^view=/, "");
  const view = views.get(key);
  const selected = view ? key : "overview";
  if (selected === currentView) return;
  currentView = selected;
  document.body.id = view ? `view=${key}` : "top";
  document.getElementById("back-top").href = `#${document.body.id}`;
  elements.overviewView.hidden = Boolean(view);
  elements.listView.hidden = !view;
  document.getElementById("back-overview").hidden = !view;
  document.querySelectorAll(".bucket-links a").forEach((link) => {
    if (view && link.hash === `#view=${key}`) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
  if (view) renderList(view, key);
  document.title = `${view?.label || "Overview"} · Badge Buddy assessment`;
  if (event) (view ? elements.listTitle : elements.overviewTitle).focus();
}

function renderCriterion(criterionId, targets) {
  const criterion = criteria.get(criterionId);
  const answer = answerFor(criterionId);
  targets.criterionKey.textContent = `${criterion.number}. ${criterion.displayId} · ${criterion.category}`;
  targets.criterionTitle.textContent = criterion.description;
  targets.criterionDetails.textContent = criterion.details || "No additional official details were supplied.";
  targets.currentStatus.textContent = answer.status === "?" ? "? — Not yet answered" : answer.status;
  targets.currentStatus.dataset.status = answer.status;
  targets.currentJustification.textContent = answer.justification || "No justification added yet.";
  targets.conversationReference.textContent = `${assessment.section} criterion ${criterion.id}`;
  renderRequirements(criterion, targets.requirementList);
  renderEvidence(answer.justification, targets.evidenceLinks);
}

function renderRequirements(criterion, target) {
  const items = [`Program category: ${criterion.category}`];
  items.push(criterion.naAllowed ? "N/A is available when the precondition truly does not apply." : "N/A is not allowed for this criterion.");
  if (criterion.metJustificationRequired) items.push("A Met answer requires written justification.");
  if (criterion.metUrlRequired) items.push("A Met answer requires an evidence URL.");
  if (criterion.naJustificationRequired) items.push("An N/A answer requires written justification.");
  target.replaceChildren();
  items.forEach((text) => {
    const item = document.createElement("li");
    item.textContent = text;
    target.append(item);
  });
}

function evidenceUrls(justification) {
  const autolink = /<(https?:\/\/[^\s<>]+)>/.source;
  const markdown = /\[[^\]\r\n]*\]\((https?:\/\/(?:[^\s<>"'()]|\([^()\s<>]*\))+)(?:\s+"[^"\r\n]*"|\s+'[^'\r\n]*')?\)/.source;
  const bare = /https?:\/\/[^\s<>"')\]]+/.source;
  const links = new RegExp(`${autolink}|${markdown}|${bare}`, "g");
  return Array.from(justification.matchAll(links), ([match, autolinkUrl, markdownUrl]) =>
    // Explicit Markdown boundaries preserve URL punctuation; bare prose is ambiguous.
    autolinkUrl ?? markdownUrl ?? match.replace(/[.,;:!?]+$/, "")
  );
}

function renderEvidence(justification, target) {
  target.replaceChildren();
  const urls = evidenceUrls(justification);
  urls.forEach((candidate) => {
    try {
      const url = new URL(candidate);
      if (!["http:", "https:"].includes(url.protocol)) return;
      const link = document.createElement("a");
      link.href = url.href;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = `${url.hostname}${url.pathname}`;
      target.append(link);
    } catch (_error) {
      // Ignore text that only resembles a URL.
    }
  });
  if (!target.childElementCount) {
    const empty = document.createElement("p");
    empty.textContent = "No public evidence URL is recorded.";
    target.append(empty);
  }
}

renderContext();
renderDashboard();
showSelection();
window.addEventListener("hashchange", showSelection);
document.querySelector(".skip-link").addEventListener("click", (event) => {
  event.preventDefault();
  document.getElementById("main").focus();
});
document.getElementById(history.state?.focus)?.focus({ preventScroll: true });
const tocRail = document.querySelector(".toc-rail");
tocRail.scrollTop = history.state?.tocRailScroll || 0;
elements.tocList.scrollTop = history.state?.tocListScroll || 0;

window.setInterval(() => {
  if (document.hidden) return;
  history.replaceState({
    focus: document.activeElement.id,
    tocRailScroll: tocRail.scrollTop,
    tocListScroll: elements.tocList.scrollTop,
  }, "", location.href);
  window.location.reload();
}, Math.max(1, assessment.refreshSeconds || 5) * 1000);
