/**
 * StackRecon — Reusable UI Components
 * All shared UI patterns live here. No ad-hoc one-offs permitted (Constitution III).
 */

"use strict";

window.stackrecon = window.stackrecon || {};

// ============================================================
// Utility: create element with optional attributes/classes
// ============================================================

function el(tag, attrs, ...children) {
  attrs = attrs || {};
  var elem = document.createElement(tag);
  for (var key in attrs) {
    if (!Object.prototype.hasOwnProperty.call(attrs, key)) continue;
    var val = attrs[key];
    if (key === "class") elem.className = val;
    else if (key === "text") elem.textContent = val;
    else elem.setAttribute(key, val);
  }
  for (var i = 0; i < children.length; i++) {
    var child = children[i];
    if (!child && child !== 0) continue;
    elem.appendChild(typeof child === "string" ? document.createTextNode(child) : child);
  }
  return elem;
}

// ============================================================
// copyToClipboard — shared clipboard helper
// ============================================================

function copyToClipboard(text, btn, labelDefault, labelCopied) {
  labelDefault = labelDefault || "Copy";
  labelCopied  = labelCopied  || "✓ Copied!";
  if (!navigator.clipboard) {
    // Fallback for non-secure contexts
    try {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
    } catch (e) { return; }
    if (btn) {
      btn.textContent = labelCopied;
      btn.classList.add("copied");
      setTimeout(function () {
        btn.textContent = labelDefault;
        btn.classList.remove("copied");
      }, 2000);
    }
    return;
  }
  navigator.clipboard.writeText(text).then(function () {
    if (btn) {
      btn.textContent = labelCopied;
      btn.classList.add("copied");
      setTimeout(function () {
        btn.textContent = labelDefault;
        btn.classList.remove("copied");
      }, 2000);
    }
  }).catch(function () {});
}

// ============================================================
// LoadingSpinner(message)
// ============================================================

function LoadingSpinner(message) {
  message = message || "Loading programs…";
  var wrap = el("div", { "class": "loading-spinner", role: "status", "aria-live": "polite" });
  wrap.appendChild(el("div", { "class": "spinner-ring" }));

  var msgRow = el("div", { "class": "loading-message" });

  // Matrix-style animated dots
  var dots = el("span", { "class": "loading-dots", "aria-hidden": "true" });
  dots.appendChild(el("span"));
  dots.appendChild(el("span"));
  dots.appendChild(el("span"));

  var msgText = el("span", { text: message });
  msgRow.appendChild(msgText);
  msgRow.appendChild(dots);
  wrap.appendChild(msgRow);
  return wrap;
}

// ============================================================
// EmptyState(message, onClearFilters)
// ============================================================

function EmptyState(message, onClearFilters) {
  message = message || "No programs found.";
  onClearFilters = onClearFilters || null;

  var wrap = el("div", { "class": "empty-state", role: "status" });

  // Icon container
  var iconWrap = el("div", { "class": "empty-state-icon", "aria-hidden": "true" });
  iconWrap.innerHTML = '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/><path d="M11 8v6M8 11h6" opacity="0.5"/></svg>';
  wrap.appendChild(iconWrap);

  wrap.appendChild(el("p", { text: message }));

  if (onClearFilters) {
    var btn = el("button", { "class": "btn-secondary", type: "button", text: "Clear all filters" });
    btn.addEventListener("click", onClearFilters);
    wrap.appendChild(btn);
  }
  return wrap;
}

// ============================================================
// ErrorBanner(message, onRetry)
// ============================================================

function ErrorBanner(message, onRetry) {
  message = message || "An error occurred.";
  onRetry = onRetry || null;

  var wrap = el("div", {
    "class": "error-banner",
    role: "alert",
    "aria-live": "assertive",
  });

  var iconSpan = el("span", { "class": "error-banner-icon", "aria-hidden": "true" });
  iconSpan.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>';
  wrap.appendChild(iconSpan);

  wrap.appendChild(el("span", { "class": "error-banner-text", text: message }));

  if (onRetry) {
    var btn = el("button", { "class": "btn-retry", type: "button", text: "Retry" });
    btn.addEventListener("click", onRetry);
    wrap.appendChild(btn);
  }
  return wrap;
}

// ============================================================
// TechBadge(techName, active)
// ============================================================

function TechBadge(techName, active) {
  active = active || false;
  var span = el("span", {
    "class": "badge tech-badge" + (active ? " active" : ""),
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
  return el("span", { "class": "badge platform-badge", text: platform, title: "Platform: " + platform });
}

// ============================================================
// RewardBadge(rewardType)
// ============================================================

function RewardBadge(rewardType) {
  var labels = { paid: "Paid", free: "Free", "self-hosted": "Self-Hosted" };
  var label = labels[rewardType] !== undefined ? labels[rewardType] : rewardType;
  return el("span", {
    "class": "badge reward-badge " + rewardType,
    text: label,
    title: "Reward type: " + label,
  });
}

// ============================================================
// ProgramCard(program, activeTech)
// ============================================================

function ProgramCard(program, activeTech) {
  activeTech = activeTech || null;

  var card = el("div", {
    "class": "program-card",
    role: "button",
    tabindex: "0",
    "data-program-name": program.name,
    "aria-label": program.name + " — " + (program.technologies.join(", ") || "no technologies detected"),
  });

  // ---- Card header row: name (left) + copy button (right) ----
  var header = el("div", { "class": "card-header" });
  header.appendChild(el("h3", { "class": "card-title", text: program.name }));

  // Build list of hostnames filtered by activeTech
  function getFilteredHostnames() {
    var dets = activeTech
      ? program.detections.filter(function (d) { return d.technologies.includes(activeTech); })
      : program.detections;
    return dets.map(function (d) { return d.hostname; });
  }

  var copyBtn = el("button", {
    "class": "btn-copy-card",
    type: "button",
    "aria-label": "Copy hostnames for " + program.name,
    text: "Copy hosts",
  });
  copyBtn.addEventListener("click", function (e) {
    e.stopPropagation();
    var hostnames = getFilteredHostnames();
    if (hostnames.length === 0) return;
    copyToClipboard(hostnames.join("\n"), copyBtn, "Copy hosts", "✓ Copied!");
  });
  header.appendChild(copyBtn);
  card.appendChild(header);

  // ---- Meta row ----
  var meta = el("div", { "class": "card-meta" });
  meta.appendChild(PlatformBadge(program.platform));
  meta.appendChild(RewardBadge(program.reward_type));
  meta.appendChild(el("span", { "class": "card-meta-stat", text: program.subdomain_count + " subdomains" }));
  if (program.detection_count > 0) {
    meta.appendChild(el("span", { "class": "card-meta-stat", text: program.detection_count + " detections" }));
  }
  card.appendChild(meta);

  // ---- Tech badges row ----
  if (program.technologies.length > 0) {
    var badges = el("div", { "class": "card-tech-badges" });
    for (var ti = 0; ti < program.technologies.length; ti++) {
      badges.appendChild(TechBadge(program.technologies[ti], program.technologies[ti] === activeTech));
    }
    card.appendChild(badges);
  }

  // ---- Detections list (toggled) ----
  var detectionsList = null;

  function toggleDetections(e) {
    // Do not toggle if the copy button was clicked
    if (e && e.target && e.target.closest && e.target.closest(".btn-copy-card, .btn-copy-hostname")) return;

    if (detectionsList) {
      detectionsList.remove();
      detectionsList = null;
      card.setAttribute("aria-expanded", "false");
      return;
    }

    var filtered = activeTech
      ? program.detections.filter(function (d) { return d.technologies.includes(activeTech); })
      : program.detections;

    if (filtered.length === 0) return;

    card.setAttribute("aria-expanded", "true");
    detectionsList = el("ul", { "class": "detections-list", "aria-label": "Detected subdomains for " + program.name });

    for (var di = 0; di < filtered.length; di++) {
      (function (det) {
        var item = el("li", { "class": "detection-item" });

        var hostname = el("span", { "class": "detection-hostname", text: det.hostname, title: det.hostname });
        item.appendChild(hostname);

        var detBadges = el("span", { "class": "detection-badges" });
        for (var bi = 0; bi < det.technologies.length; bi++) {
          detBadges.appendChild(TechBadge(det.technologies[bi], det.technologies[bi] === activeTech));
        }
        item.appendChild(detBadges);

        // Per-hostname copy button
        var hCopyBtn = el("button", {
          "class": "btn-copy-hostname",
          type: "button",
          "aria-label": "Copy " + det.hostname,
          title: "Copy hostname",
        });
        hCopyBtn.innerHTML = '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>';
        hCopyBtn.addEventListener("click", function (e) {
          e.stopPropagation();
          copyToClipboard(det.hostname, hCopyBtn, "\u29c9", "✓");
        });
        item.appendChild(hCopyBtn);

        detectionsList.appendChild(item);
      })(filtered[di]);
    }

    card.appendChild(detectionsList);
  }

  card.setAttribute("aria-expanded", "false");
  card.addEventListener("click", toggleDetections);
  card.addEventListener("keydown", function (e) {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      toggleDetections(e);
    }
  });

  return card;
}

// ============================================================
// CopyAllBanner(techName, hostnames)
// A sticky banner below the header for bulk copying all hostnames
// matching the active tech filter.
// ============================================================

function CopyAllBanner(techName, hostnames) {
  techName  = techName  || "";
  hostnames = hostnames || [];

  var banner = el("div", {
    id: "copy-all-banner",
    "class": "copy-all-banner" + (techName ? "" : " hidden"),
    role: "region",
    "aria-label": "Copy all filtered hostnames",
  });

  var text = el("p", { "class": "copy-all-banner-text" });
  var techStrong = el("strong", { text: techName || "" });
  var countText = document.createTextNode(
    " subdomains (" + hostnames.length + " host" + (hostnames.length !== 1 ? "s" : "") + ")"
  );
  text.appendChild(document.createTextNode("Copy all "));
  text.appendChild(techStrong);
  text.appendChild(countText);
  banner.appendChild(text);

  var copyAllBtn = el("button", {
    "class": "btn-copy-all",
    type: "button",
    text: "\uD83D\uDCCB Copy " + hostnames.length + " hosts",
    "aria-label": "Copy all " + hostnames.length + " hostnames matching " + techName,
  });
  copyAllBtn.addEventListener("click", function () {
    if (hostnames.length === 0) return;
    copyToClipboard(hostnames.join("\n"), copyAllBtn, "\uD83D\uDCCB Copy " + hostnames.length + " hosts", "✓ Copied!");
  });
  banner.appendChild(copyAllBtn);

  var dismissBtn = el("button", {
    "class": "btn-banner-dismiss",
    type: "button",
    "aria-label": "Dismiss copy banner",
    title: "Dismiss",
    text: "\u00D7",
  });
  dismissBtn.addEventListener("click", function () {
    banner.classList.add("hidden");
  });
  banner.appendChild(dismissBtn);

  // Expose an update method so app.js can update without rebuilding the DOM node
  banner.updateBanner = function (newTech, newHostnames) {
    newTech      = newTech      || "";
    newHostnames = newHostnames || [];

    if (!newTech || newHostnames.length === 0) {
      banner.classList.add("hidden");
      return;
    }

    banner.classList.remove("hidden");

    // Update text
    techStrong.textContent = newTech;
    var updatedCount = " subdomains (" + newHostnames.length + " host" + (newHostnames.length !== 1 ? "s" : "") + ")";
    // Rebuild text node after strong
    while (text.childNodes.length > 2) text.removeChild(text.lastChild);
    text.appendChild(document.createTextNode(updatedCount));

    // Update copy button
    var newLabel = "\uD83D\uDCCB Copy " + newHostnames.length + " hosts";
    copyAllBtn.textContent = newLabel;
    copyAllBtn.classList.remove("copied");
    copyAllBtn.setAttribute("aria-label", "Copy all " + newHostnames.length + " hostnames matching " + newTech);

    // Rebind click with fresh closure
    var freshHostnames = newHostnames.slice();
    copyAllBtn.onclick = function () {
      if (freshHostnames.length === 0) return;
      copyToClipboard(freshHostnames.join("\n"), copyAllBtn, "\uD83D\uDCCB Copy " + freshHostnames.length + " hosts", "✓ Copied!");
    };
  };

  return banner;
}

// ============================================================
// Export to window.stackrecon.components
// ============================================================

window.stackrecon.components = {
  LoadingSpinner:  LoadingSpinner,
  EmptyState:      EmptyState,
  ErrorBanner:     ErrorBanner,
  TechBadge:       TechBadge,
  PlatformBadge:   PlatformBadge,
  RewardBadge:     RewardBadge,
  ProgramCard:     ProgramCard,
  CopyAllBanner:   CopyAllBanner,
};
