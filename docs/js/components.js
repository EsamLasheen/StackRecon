/**
 * StackRecon — Reusable UI Components
 * All shared UI patterns live here. No ad-hoc one-offs permitted (Constitution III).
 */

"use strict";

window.stackrecon = window.stackrecon || {};

// ============================================================
// Utility: create element with optional attributes/classes
// ============================================================

function el(tag, attrs = {}, ...children) {
  const elem = document.createElement(tag);
  for (const [key, val] of Object.entries(attrs)) {
    if (key === "class") elem.className = val;
    else if (key === "text") elem.textContent = val;
    else elem.setAttribute(key, val);
  }
  for (const child of children) {
    if (child) elem.appendChild(typeof child === "string" ? document.createTextNode(child) : child);
  }
  return elem;
}

// ============================================================
// LoadingSpinner(message)
// ============================================================

function LoadingSpinner(message = "Loading programs…") {
  const wrap = el("div", { class: "loading-spinner", role: "status", "aria-live": "polite" });
  wrap.appendChild(el("div", { class: "spinner-ring" }));
  wrap.appendChild(el("p", { text: message }));
  return wrap;
}

// ============================================================
// EmptyState(message, onClearFilters)
// ============================================================

function EmptyState(message = "No programs found.", onClearFilters = null) {
  const wrap = el("div", { class: "empty-state", role: "status" });
  wrap.appendChild(el("div", { class: "empty-state-icon" }, "🔍"));
  wrap.appendChild(el("p", { text: message }));
  if (onClearFilters) {
    const btn = el("button", { class: "btn-secondary", type: "button", text: "Clear all filters" });
    btn.addEventListener("click", onClearFilters);
    wrap.appendChild(btn);
  }
  return wrap;
}

// ============================================================
// ErrorBanner(message, onRetry)
// ============================================================

function ErrorBanner(message = "An error occurred.", onRetry = null) {
  const wrap = el("div", {
    class: "error-banner",
    role: "alert",
    "aria-live": "assertive",
  });
  wrap.appendChild(el("span", { text: message }));
  if (onRetry) {
    const btn = el("button", { class: "btn-retry", type: "button", text: "Retry" });
    btn.addEventListener("click", onRetry);
    wrap.appendChild(btn);
  }
  return wrap;
}

// ============================================================
// TechBadge(techName, active)
// ============================================================

function TechBadge(techName, active = false) {
  const span = el("span", {
    class: "badge tech-badge" + (active ? " active" : ""),
    "data-tech": techName,
    text: techName,
    title: techName,
  });
  return span;
}

// ============================================================
// PlatformBadge(platform)
// ============================================================

function PlatformBadge(platform) {
  return el("span", { class: "badge platform-badge", text: platform, title: "Platform" });
}

// ============================================================
// RewardBadge(rewardType)
// ============================================================

function RewardBadge(rewardType) {
  const label = { paid: "Paid", free: "Free", "self-hosted": "Self-Hosted" }[rewardType] ?? rewardType;
  const cssClass = rewardType.replace("-", "-"); // maps to CSS .reward-badge.paid etc.
  return el("span", { class: `badge reward-badge ${rewardType}`, text: label, title: "Reward type" });
}

// ============================================================
// ProgramCard(program, activeTech)
// Returns an HTMLElement representing one program result card.
// ============================================================

function ProgramCard(program, activeTech = null) {
  const card = el("div", {
    class: "program-card",
    role: "button",
    tabindex: "0",
    "data-program-name": program.name,
    "aria-label": `${program.name} — ${program.technologies.join(", ") || "no technologies detected"}`,
  });

  // Title row
  card.appendChild(el("h3", { class: "card-title", text: program.name }));

  // Meta row: platform + reward + subdomain count
  const meta = el("div", { class: "card-meta" });
  meta.appendChild(PlatformBadge(program.platform));
  meta.appendChild(RewardBadge(program.reward_type));
  meta.appendChild(el("span", { text: `${program.subdomain_count} subdomains` }));
  if (program.detection_count > 0) {
    meta.appendChild(el("span", { text: `${program.detection_count} detections` }));
  }
  card.appendChild(meta);

  // Technology badges
  if (program.technologies.length > 0) {
    const badges = el("div", { class: "card-tech-badges" });
    for (const tech of program.technologies) {
      badges.appendChild(TechBadge(tech, tech === activeTech));
    }
    card.appendChild(badges);
  }

  // Detections list (toggled on click/Enter)
  let detectionsList = null;

  function toggleDetections() {
    if (detectionsList) {
      detectionsList.remove();
      detectionsList = null;
      return;
    }
    const filtered = activeTech
      ? program.detections.filter((d) => d.technologies.includes(activeTech))
      : program.detections;

    if (filtered.length === 0) return;

    detectionsList = el("ul", { class: "detections-list", "aria-label": "Detected subdomains" });
    for (const det of filtered) {
      const item = el("li", { class: "detection-item" });
      item.appendChild(el("span", { text: det.hostname }));
      for (const tech of det.technologies) {
        item.appendChild(TechBadge(tech, tech === activeTech));
      }
      detectionsList.appendChild(item);
    }
    card.appendChild(detectionsList);
  }

  card.addEventListener("click", toggleDetections);
  card.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggleDetections(); }
  });

  return card;
}

// ============================================================
// Export to window.stackrecon.components
// ============================================================

window.stackrecon.components = {
  LoadingSpinner,
  EmptyState,
  ErrorBanner,
  TechBadge,
  PlatformBadge,
  RewardBadge,
  ProgramCard,
};
