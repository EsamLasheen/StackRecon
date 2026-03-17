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
    "class": "program-card" + (program.severity && program.severity !== "none" ? " has-findings sev-card-" + program.severity : ""),
    role: "button",
    tabindex: "0",
    "data-program-name": program.name,
    "aria-label": program.name + " — " + (program.technologies.join(", ") || "no technologies detected"),
  });

  // ---- Card header row ----
  var header = el("div", { "class": "card-header" });
  header.appendChild(el("h3", { "class": "card-title", text: program.name }));

  // Severity badge
  if (program.severity && program.severity !== "none") {
    var sevLabel = program.severity.toUpperCase();
    if (program.critical_count > 0) sevLabel += " (" + program.critical_count + "C)";
    else if (program.high_count > 0) sevLabel += " (" + program.high_count + "H)";
    var sevBadge = el("span", {
      "class": "badge severity-badge sev-" + program.severity,
      text: sevLabel,
    });
    header.appendChild(sevBadge);
  }

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
  var totalFindings = (program.critical_count || 0) + (program.high_count || 0) + (program.medium_count || 0);
  if (totalFindings > 0) {
    var findingsStat = el("span", { "class": "card-meta-stat findings-stat", text: totalFindings + " findings" });
    meta.appendChild(findingsStat);
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

    var vulns = (program.vulnerabilities || []).filter(function(v) {
      return !activeTech || (v.technologies && v.technologies.indexOf(activeTech) !== -1);
    });
    // When no tech filter, show all vulns
    if (!activeTech) vulns = program.vulnerabilities || [];

    if (filtered.length === 0 && vulns.length === 0) return;

    card.setAttribute("aria-expanded", "true");
    detectionsList = el("div", { "class": "detections-list-wrap" });

    // Vulnerability findings section (shown first)
    if (vulns.length > 0) {
      var vulnSection = el("div", { "class": "vuln-section" });
      vulnSection.appendChild(el("div", { "class": "vuln-section-title", text: "\u26A0 SECURITY FINDINGS (" + vulns.length + ")" }));
      for (var vi = 0; vi < vulns.length; vi++) {
        (function (vuln) {
          var vitem = el("div", { "class": "vuln-item" });
          vitem.appendChild(el("span", { "class": "badge severity-badge sev-" + vuln.severity, text: vuln.severity.toUpperCase() }));
          vitem.appendChild(el("span", { "class": "vuln-name", text: vuln.name }));
          vitem.appendChild(el("span", { "class": "vuln-host", text: vuln.hostname }));

          var vcopy = el("button", {
            "class": "btn-copy-hostname",
            type: "button",
            "aria-label": "Copy URL",
            title: vuln.matched_at || vuln.hostname,
          });
          vcopy.innerHTML = '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>';
          vcopy.addEventListener("click", function (e) {
            e.stopPropagation();
            copyToClipboard(vuln.matched_at || vuln.hostname, vcopy, "\u29c9", "✓");
          });
          vitem.appendChild(vcopy);
          vulnSection.appendChild(vitem);
        })(vulns[vi]);
      }
      detectionsList.appendChild(vulnSection);
    }

    // Tech detections section
    if (filtered.length > 0) {
      var detList = el("ul", { "class": "detections-list", "aria-label": "Detected subdomains" });
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
          detList.appendChild(item);
        })(filtered[di]);
      }
      detectionsList.appendChild(detList);
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
// InsightsPanel(programs)
// Full-width bar chart of top 10 most detected technologies.
// Screenshot-worthy for social sharing.
// ============================================================

function InsightsPanel(programs) {
  programs = programs || [];

  // Compute tech frequency across all programs
  var techCount = {};
  for (var i = 0; i < programs.length; i++) {
    var techs = programs[i].technologies;
    for (var j = 0; j < techs.length; j++) {
      techCount[techs[j]] = (techCount[techs[j]] || 0) + 1;
    }
  }

  var sorted = Object.keys(techCount).map(function (t) {
    return { tech: t, count: techCount[t] };
  }).sort(function (a, b) { return b.count - a.count; }).slice(0, 10);

  var maxCount = sorted.length > 0 ? sorted[0].count : 1;

  var panel = el("div", {
    id: "insights-panel",
    "class": "insights-panel",
    "aria-label": "Top exposed technologies",
  });

  // ---- Header ----
  var header = el("div", { "class": "insights-header" });

  var titleGroup = el("div", { "class": "insights-title-group" });
  titleGroup.appendChild(el("span", { "class": "insights-title", text: "TOP EXPOSED TECHNOLOGIES" }));
  titleGroup.appendChild(el("span", {
    "class": "insights-subtitle",
    text: programs.length.toLocaleString() + " programs scanned",
  }));
  header.appendChild(titleGroup);

  // LinkedIn share button
  var shareBtn = el("button", {
    "class": "btn-share-linkedin",
    type: "button",
  });
  shareBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" style="vertical-align:middle;margin-right:5px"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 0 1-2.063-2.065 2.064 2.064 0 1 1 2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>Share on LinkedIn';

  shareBtn.addEventListener("click", function () {
    var topTech = sorted.length > 0 ? sorted[0] : null;
    var totalCrit = 0, totalHigh = 0;
    for (var pi = 0; pi < programs.length; pi++) {
      totalCrit += programs[pi].critical_count || 0;
      totalHigh += programs[pi].high_count || 0;
    }
    var postText = topTech
      ? (
        "I built a tool that automatically scans every public bug bounty program and maps their full tech stack.\n\n" +
        "Results from this week\u2019s scan across " + programs.length + " programs:\n\n" +
        "\uD83D\uDD34 " + totalCrit + " critical vulnerabilities found\n" +
        "\uD83D\uDFE0 " + totalHigh + " high severity findings\n" +
        "\uD83D\uDCE1 " + topTech.count + " programs running " + topTech.tech + " publicly\n" +
        "\uD83C\uDF10 6,000+ live subdomains fingerprinted\n\n" +
        "The tool is called StackRecon \u2014 fully open source, runs weekly on GitHub Actions.\n\n" +
        "It uses httpx + nuclei to detect 1,400+ technologies and real misconfigurations across:\n" +
        "\u2022 Admin panels, dev environments, CI/CD tools\n" +
        "\u2022 Grafana, Jenkins, GitLab, Vault, Kubernetes dashboards\n" +
        "\u2022 Every HackerOne, Bugcrowd, Intigriti and YesWeHack program\n\n" +
        "Filter by tech, severity, or platform \u2014 copy all matching subdomains in one click.\n\n" +
        "\uD83D\uDD17 Live dashboard: https://EsamLasheen.github.io/StackRecon/\n" +
        "\u2B50 GitHub: https://github.com/EsamLasheen/StackRecon\n\n" +
        "#BugBounty #CyberSecurity #InfoSec #PenTesting #HackerOne #Bugcrowd #OSINT #ReconTool"
      )
      : "I built StackRecon \u2014 an open-source tool that scans every public bug bounty program weekly and maps their full tech stack.\n\nLive dashboard: https://EsamLasheen.github.io/StackRecon/\nGitHub: https://github.com/EsamLasheen/StackRecon\n\n#BugBounty #CyberSecurity #OSINT";

    copyToClipboard(postText, null, "", "");

    var linkedinUrl = "https://www.linkedin.com/sharing/share-offsite/?url=" +
      encodeURIComponent("https://EsamLasheen.github.io/StackRecon/");
    window.open(linkedinUrl, "_blank", "noopener,noreferrer");

    shareBtn.classList.add("shared");
    shareBtn.innerHTML = "\u2713 Post text copied \u2014 paste it in LinkedIn!";
    setTimeout(function () {
      shareBtn.classList.remove("shared");
      shareBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" style="vertical-align:middle;margin-right:5px"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 0 1-2.063-2.065 2.064 2.064 0 1 1 2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>Share on LinkedIn';
    }, 4000);
  });
  header.appendChild(shareBtn);
  panel.appendChild(header);

  // ---- Critical stats row ----
  var totalCritical = 0;
  var totalHigh = 0;
  var totalMedium = 0;
  for (var ci = 0; ci < programs.length; ci++) {
    totalCritical += programs[ci].critical_count || 0;
    totalHigh += programs[ci].high_count || 0;
    totalMedium += programs[ci].medium_count || 0;
  }
  var programsWithCritical = programs.filter(function(p) { return (p.critical_count || 0) > 0; }).length;
  var programsWithHigh = programs.filter(function(p) { return (p.high_count || 0) > 0; }).length;

  if (totalCritical + totalHigh + totalMedium > 0) {
    var statsRow = el("div", { "class": "insights-severity-row" });
    if (totalCritical > 0) {
      var critStat = el("span", { "class": "sev-stat sev-stat-critical" });
      critStat.innerHTML = "<strong>" + totalCritical + "</strong> critical findings in <strong>" + programsWithCritical + "</strong> programs";
      statsRow.appendChild(critStat);
    }
    if (totalHigh > 0) {
      var highStat = el("span", { "class": "sev-stat sev-stat-high" });
      highStat.innerHTML = "<strong>" + totalHigh + "</strong> high findings in <strong>" + programsWithHigh + "</strong> programs";
      statsRow.appendChild(highStat);
    }
    if (totalMedium > 0) {
      var medStat = el("span", { "class": "sev-stat sev-stat-medium" });
      medStat.innerHTML = "<strong>" + totalMedium + "</strong> medium";
      statsRow.appendChild(medStat);
    }
    panel.appendChild(statsRow);
  }

  // ---- Bars ----
  var barsEl = el("div", { "class": "insights-bars" });

  for (var k = 0; k < sorted.length; k++) {
    (function (item, rank) {
      var pct = Math.max(4, Math.round((item.count / maxCount) * 100));
      var row = el("div", {
        "class": "insight-row",
        role: "button",
        tabindex: "0",
        title: "Filter by " + item.tech,
        "aria-label": item.tech + ": " + item.count + " programs",
      });

      var labelEl = el("div", { "class": "insight-label" });
      labelEl.appendChild(el("span", { "class": "insight-rank", text: "#" + (rank + 1) }));
      labelEl.appendChild(el("span", { "class": "insight-tech", text: item.tech }));
      row.appendChild(labelEl);

      var barWrap = el("div", { "class": "insight-bar-wrap", "aria-hidden": "true" });
      var bar = el("div", { "class": "insight-bar" });
      bar.style.width = "0%";
      barWrap.appendChild(bar);
      row.appendChild(barWrap);

      row.appendChild(el("span", {
        "class": "insight-count",
        text: item.count + " program" + (item.count !== 1 ? "s" : ""),
      }));

      // Animate bar in after mount
      setTimeout(function () { bar.style.width = pct + "%"; }, 80 + rank * 50);

      function activate() {
        if (window.stackrecon && window.stackrecon._onInsightClick) {
          window.stackrecon._onInsightClick(item.tech);
        }
      }
      row.addEventListener("click", activate);
      row.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); activate(); }
      });

      barsEl.appendChild(row);
    })(sorted[k], k);
  }

  panel.appendChild(barsEl);

  // Expose update method for auto-refresh
  panel.updateInsights = function (newPrograms) {
    var newPanel = InsightsPanel(newPrograms);
    panel.parentNode.replaceChild(newPanel, panel);
  };

  return panel;
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
  InsightsPanel:   InsightsPanel,
};
