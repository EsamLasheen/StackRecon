/**
 * StackRecon — Filter Logic + Inverted Index
 * Builds O(1) Map-based indices for technology, platform, and reward filters.
 */

"use strict";

window.stackrecon = window.stackrecon || {};

// ============================================================
// Index builders
// ============================================================

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

// ============================================================
// Helpers
// ============================================================

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

// ============================================================
// Combined filter application (AND logic across all active filters)
// ============================================================

function applyAllFilters(state) {
  const { techIndex, platformIndex, rewardIndex, programs, activeFilters } = state;
  const total = programs.length;

  let result = null; // null = "all"

  if (activeFilters.tech) {
    result = intersect(result, techIndex.get(activeFilters.tech) ?? new Set());
  }
  if (activeFilters.platform) {
    result = intersect(result, platformIndex.get(activeFilters.platform) ?? new Set());
  }
  if (activeFilters.reward) {
    result = intersect(result, rewardIndex.get(activeFilters.reward) ?? new Set());
  }

  // Name search (applied after index intersection)
  let indices = result ? [...result] : Array.from({ length: total }, (_, i) => i);

  if (activeFilters.name && activeFilters.name.length >= 2) {
    const q = activeFilters.name.toLowerCase();
    indices = indices.filter((i) => programs[i].name.toLowerCase().includes(q));
  }

  return indices;
}

// ============================================================
// Export
// ============================================================

window.stackrecon.filters = {
  buildTechIndex,
  buildPlatformIndex,
  buildRewardIndex,
  intersect,
  getAllTechnologies,
  applyAllFilters,
};
