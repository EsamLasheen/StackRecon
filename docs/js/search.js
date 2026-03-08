/**
 * StackRecon — Name Search + URL Hash State
 */

"use strict";

window.stackrecon = window.stackrecon || {};

function debounce(fn, delayMs) {
  let timer;
  return function (...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delayMs);
  };
}

function nameSearch(programs, query, minChars = 2) {
  if (!query || query.length < minChars) return programs.map((_, i) => i);
  const q = query.toLowerCase();
  return programs.reduce((acc, p, i) => {
    if (p.name.toLowerCase().includes(q)) acc.push(i);
    return acc;
  }, []);
}

function readFiltersFromHash() {
  const hash = window.location.hash.replace(/^#/, "");
  const filters = { tech: "", platform: "", reward: "", name: "" };
  if (!hash) return filters;
  for (const part of hash.split("&")) {
    const [key, val] = part.split("=").map(decodeURIComponent);
    if (key in filters) filters[key] = val ?? "";
  }
  return filters;
}

function writeFiltersToHash(filters) {
  const parts = [];
  for (const [key, val] of Object.entries(filters)) {
    if (val) parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(val)}`);
  }
  const hash = parts.length ? "#" + parts.join("&") : "";
  history.replaceState(null, "", hash || window.location.pathname);
}

window.stackrecon.search = { debounce, nameSearch, readFiltersFromHash, writeFiltersToHash };
