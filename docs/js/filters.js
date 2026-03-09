/**
 * StackRecon — Filter Logic + Inverted Index
 */

"use strict";

window.stackrecon = window.stackrecon || {};

function buildTechIndex(programs) {
  const index = new Map();
  programs.forEach((program, i) => {
    for (const tech of program.technologies) {
      if (!index.has(tech)) index.set(tech, new Set());
      index.get(tech).add(i);
    }
  });
  return index;
}

function buildPlatformIndex(programs) {
  const index = new Map();
  programs.forEach((program, i) => {
    const p = program.platform;
    if (!index.has(p)) index.set(p, new Set());
    index.get(p).add(i);
  });
  return index;
}

function buildRewardIndex(programs) {
  const index = new Map();
  programs.forEach((program, i) => {
    const r = program.reward_type;
    if (!index.has(r)) index.set(r, new Set());
    index.get(r).add(i);
  });
  return index;
}

function buildSeverityIndex(programs) {
  const index = new Map();
  const SEVERITY_ORDER = { critical: 4, high: 3, medium: 2, low: 1, info: 0, none: -1 };
  // "findings" = any program with severity != "none"
  const withFindings = new Set();
  programs.forEach((program, i) => {
    const sev = program.severity || "none";
    if (!index.has(sev)) index.set(sev, new Set());
    index.get(sev).add(i);
    if (SEVERITY_ORDER[sev] >= 0) withFindings.add(i);
  });
  index.set("findings", withFindings);
  return index;
}

function intersect(setA, setB) {
  if (!setA) return new Set(setB);
  if (!setB) return new Set(setA);
  const result = new Set();
  for (const item of setA) {
    if (setB.has(item)) result.add(item);
  }
  return result;
}

function getAllTechnologies(programs) {
  const techs = new Set();
  for (const p of programs) {
    for (const t of p.technologies) techs.add(t);
  }
  return [...techs].sort((a, b) => a.localeCompare(b));
}

function applyAllFilters(state) {
  const { techIndex, platformIndex, rewardIndex, severityIndex, programs, activeFilters } = state;
  const total = programs.length;

  let result = null;

  if (activeFilters.tech) {
    result = intersect(result, techIndex.get(activeFilters.tech) ?? new Set());
  }
  if (activeFilters.platform) {
    result = intersect(result, platformIndex.get(activeFilters.platform) ?? new Set());
  }
  if (activeFilters.reward) {
    result = intersect(result, rewardIndex.get(activeFilters.reward) ?? new Set());
  }
  if (activeFilters.severity && severityIndex) {
    result = intersect(result, severityIndex.get(activeFilters.severity) ?? new Set());
  }

  let indices = result ? [...result] : Array.from({ length: total }, (_, i) => i);

  if (activeFilters.name && activeFilters.name.length >= 2) {
    const q = activeFilters.name.toLowerCase();
    indices = indices.filter((i) => programs[i].name.toLowerCase().includes(q));
  }

  // Sort: critical first, then high, medium, none
  const SEVERITY_ORDER = { critical: 4, high: 3, medium: 2, low: 1, info: 0, none: -1 };
  indices.sort((a, b) => {
    const sa = SEVERITY_ORDER[programs[a].severity] || -1;
    const sb = SEVERITY_ORDER[programs[b].severity] || -1;
    return sb - sa;
  });

  return indices;
}

window.stackrecon.filters = {
  buildTechIndex,
  buildPlatformIndex,
  buildRewardIndex,
  buildSeverityIndex,
  intersect,
  getAllTechnologies,
  applyAllFilters,
};
