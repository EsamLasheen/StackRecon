/**
 * StackRecon — Application Entry Point
 * Fetches data.json, builds indices, wires all filter controls.
 */

"use strict";

window.stackrecon = window.stackrecon || {
  programs: [],
  indices: {},
  activeFilters: { tech: "", platform: "", reward: "", name: "" },
};

const DATA_URL = "./data/data.json";

const { LoadingSpinner, EmptyState, ErrorBanner, ProgramCard } = window.stackrecon.components || {};
const { buildTechIndex, buildPlatformIndex, buildRewardIndex, getAllTechnologies, applyAllFilters } =
  window.stackrecon.filters || {};
const { debounce, readFiltersFromHash, writeFiltersToHash } = window.stackrecon.search || {};

// ---- DOM refs (resolved after DOMContentLoaded) ----------------------------
let resultsContainer, statsBar, techSelect, platformSelect, rewardSelect, nameInput, clearBtn;

// ---- Render ----------------------------------------------------------------

function renderResults(programIndices, activeTech) {
  resultsContainer.innerHTML = "";

  if (programIndices.length === 0) {
    resultsContainer.appendChild(
      EmptyState("No programs match the current filters.", clearAllFilters)
    );
    statsBar.textContent = "No programs found";
    return;
  }

  const frag = document.createDocumentFragment();
  for (const i of programIndices) {
    frag.appendChild(ProgramCard(window.stackrecon.programs[i], activeTech || null));
  }
  resultsContainer.appendChild(frag);
  statsBar.textContent = `Showing ${programIndices.length} of ${window.stackrecon.programs.length} programs`;
}

// ---- Index build -----------------------------------------------------------

function buildIndices(programs) {
  window.stackrecon.indices = {
    tech: buildTechIndex(programs),
    platform: buildPlatformIndex(programs),
    reward: buildRewardIndex(programs),
  };
}

// ---- Filter application ----------------------------------------------------

function applyFilters() {
  const state = {
    techIndex: window.stackrecon.indices.tech,
    platformIndex: window.stackrecon.indices.platform,
    rewardIndex: window.stackrecon.indices.reward,
    programs: window.stackrecon.programs,
    activeFilters: window.stackrecon.activeFilters,
  };
  const indices = applyAllFilters(state);
  writeFiltersToHash(window.stackrecon.activeFilters);
  renderResults(indices, window.stackrecon.activeFilters.tech);
}

// ---- Clear filters ---------------------------------------------------------

function clearAllFilters() {
  window.stackrecon.activeFilters = { tech: "", platform: "", reward: "", name: "" };
  techSelect.value = "";
  platformSelect.value = "";
  rewardSelect.value = "";
  nameInput.value = "";
  writeFiltersToHash({});
  renderResults(
    window.stackrecon.programs.map((_, i) => i),
    null
  );
  statsBar.textContent = `Showing ${window.stackrecon.programs.length} of ${window.stackrecon.programs.length} programs`;
}

// ---- Populate tech dropdown ------------------------------------------------

function initTechDropdown(programs) {
  const techs = getAllTechnologies(programs);
  for (const tech of techs) {
    const opt = document.createElement("option");
    opt.value = tech;
    opt.textContent = tech;
    techSelect.appendChild(opt);
  }
}

// ---- Restore filters from URL hash ----------------------------------------

function restoreFiltersFromHash() {
  const saved = readFiltersFromHash();
  window.stackrecon.activeFilters = saved;
  if (saved.tech) techSelect.value = saved.tech;
  if (saved.platform) platformSelect.value = saved.platform;
  if (saved.reward) rewardSelect.value = saved.reward;
  if (saved.name) nameInput.value = saved.name;
}

// ---- Last-updated footer ---------------------------------------------------

function setLastUpdated(meta) {
  const el = document.getElementById("last-updated");
  if (!el || !meta?.generated_at) return;
  const d = new Date(meta.generated_at);
  el.textContent = isNaN(d) ? meta.generated_at : d.toLocaleDateString("en-US", {
    year: "numeric", month: "short", day: "numeric",
  });
}

// ---- Data fetch ------------------------------------------------------------

async function fetchData() {
  resultsContainer.innerHTML = "";
  resultsContainer.appendChild(LoadingSpinner("Fetching program data…"));

  let data;
  try {
    const resp = await fetch(DATA_URL);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    data = await resp.json();
  } catch (err) {
    resultsContainer.innerHTML = "";
    resultsContainer.appendChild(
      ErrorBanner(`Failed to load program data: ${err.message}`, fetchData)
    );
    statsBar.textContent = "Error loading data";
    return;
  }

  window.stackrecon.programs = data.programs || [];
  buildIndices(window.stackrecon.programs);
  initTechDropdown(window.stackrecon.programs);
  setLastUpdated(data.meta);
  restoreFiltersFromHash();
  applyFilters();
}

// ---- Wire controls ---------------------------------------------------------

function wireControls() {
  techSelect.addEventListener("change", () => {
    window.stackrecon.activeFilters.tech = techSelect.value;
    applyFilters();
  });

  platformSelect.addEventListener("change", () => {
    window.stackrecon.activeFilters.platform = platformSelect.value;
    applyFilters();
  });

  rewardSelect.addEventListener("change", () => {
    window.stackrecon.activeFilters.reward = rewardSelect.value;
    applyFilters();
  });

  nameInput.addEventListener(
    "input",
    debounce(() => {
      window.stackrecon.activeFilters.name = nameInput.value.trim();
      applyFilters();
    }, 200)
  );

  clearBtn.addEventListener("click", clearAllFilters);
}

// ---- Bootstrap -------------------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {
  resultsContainer = document.getElementById("results-container");
  statsBar = document.getElementById("stats-bar");
  techSelect = document.getElementById("tech-filter");
  platformSelect = document.getElementById("platform-filter");
  rewardSelect = document.getElementById("reward-filter");
  nameInput = document.getElementById("name-search");
  clearBtn = document.getElementById("clear-filters");

  wireControls();
  fetchData();
});
