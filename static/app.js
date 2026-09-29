/* ==========================================================
   FindSphere — Client-Side Application Controller
   ========================================================== */

document.addEventListener("DOMContentLoaded", () => {
  initStats();
  initSearchWorkbench();
  initCatalog();
  initReportForms();
  initClaimModal();
  initClaimsDesk();
});

// ==========================================================
// 1. OPERATIONAL STATISTICS
// ==========================================================
async function initStats() {
  try {
    const res = await fetch("/api/stats");
    if (!res.ok) return;
    const stats = await res.json();

    const statRate = document.getElementById("stat-rate");
    const statItems = document.getElementById("stat-items");
    const statZones = document.getElementById("stat-zones");

    if (statRate) statRate.textContent = `${stats.success_rate_percent || 94.8}%`;
    if (statItems) statItems.textContent = `${stats.total_found || 28}+`;
    if (statZones) statZones.textContent = `${stats.active_custody_zones || 6} Zones`;
  } catch (err) {
    console.warn("Failed to fetch live stats:", err);
  }
}

// ==========================================================
// 2. SEARCH & MATCH WORKBENCH
// ==========================================================
let currentQueryFile = null;
let currentSampleUrl = null;

function initSearchWorkbench() {
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("match-file-input");
  const dropzoneEmpty = document.getElementById("dropzone-empty");
  const dropzonePreview = document.getElementById("dropzone-preview");
  const previewImage = document.getElementById("preview-image");
  const btnRemoveImage = document.getElementById("btn-remove-image");
  const thresholdSlider = document.getElementById("match-threshold");
  const thresholdVal = document.getElementById("threshold-val");
  const btnRunMatch = document.getElementById("btn-run-match");
  const sampleChips = document.querySelectorAll(".sample-chip");

  // Threshold slider live indicator
  if (thresholdSlider && thresholdVal) {
    thresholdSlider.addEventListener("input", (e) => {
      thresholdVal.textContent = `${e.target.value}%`;
    });
  }

  // Dropzone click & drag events
  if (dropzone && fileInput) {
    dropzone.addEventListener("click", (e) => {
      if (e.target !== btnRemoveImage && !btnRemoveImage.contains(e.target)) {
        fileInput.click();
      }
    });

    dropzone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropzone.classList.add("drag-over");
    });

    dropzone.addEventListener("dragleave", () => {
      dropzone.classList.remove("drag-over");
    });

    dropzone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropzone.classList.remove("drag-over");
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        handleFileSelect(e.dataTransfer.files[0]);
      }
    });

    fileInput.addEventListener("change", (e) => {
      if (e.target.files && e.target.files[0]) {
        handleFileSelect(e.target.files[0]);
      }
    });
  }

  if (btnRemoveImage) {
    btnRemoveImage.addEventListener("click", (e) => {
      e.stopPropagation();
      clearQueryImage();
    });
  }

  // Quick sample images
  sampleChips.forEach((chip) => {
    chip.addEventListener("click", () => {
      const samplePath = chip.getAttribute("data-sample");
      loadSampleImage(samplePath);
    });
  });

  // Run match trigger
  if (btnRunMatch) {
    btnRunMatch.addEventListener("click", runMultimodalSearch);
  }
}

function handleFileSelect(file) {
  currentQueryFile = file;
  currentSampleUrl = null;

  const reader = new FileReader();
  reader.onload = (e) => {
    const previewImage = document.getElementById("preview-image");
    const dropzoneEmpty = document.getElementById("dropzone-empty");
    const dropzonePreview = document.getElementById("dropzone-preview");

    previewImage.src = e.target.result;
    dropzoneEmpty.classList.add("hidden");
    dropzonePreview.classList.remove("hidden");
  };
  reader.readAsDataURL(file);
}

async function loadSampleImage(samplePath) {
  try {
    const previewImage = document.getElementById("preview-image");
    const dropzoneEmpty = document.getElementById("dropzone-empty");
    const dropzonePreview = document.getElementById("dropzone-preview");

    previewImage.src = `/${samplePath}`;
    dropzoneEmpty.classList.add("hidden");
    dropzonePreview.classList.remove("hidden");

    // Fetch the sample image as a Blob so it can be sent via FormData
    const response = await fetch(`/${samplePath}`);
    const blob = await response.blob();
    const filename = samplePath.split("/").pop();
    currentQueryFile = new File([blob], filename, { type: blob.type || "image/jpeg" });
    currentSampleUrl = samplePath;
  } catch (err) {
    console.error("Error loading sample image:", err);
  }
}

function clearQueryImage() {
  currentQueryFile = null;
  currentSampleUrl = null;
  const fileInput = document.getElementById("match-file-input");
  const dropzoneEmpty = document.getElementById("dropzone-empty");
  const dropzonePreview = document.getElementById("dropzone-preview");
  const previewImage = document.getElementById("preview-image");

  if (fileInput) fileInput.value = "";
  if (previewImage) previewImage.src = "";
  if (dropzonePreview) dropzonePreview.classList.add("hidden");
  if (dropzoneEmpty) dropzoneEmpty.classList.remove("hidden");
}

async function runMultimodalSearch() {
  const desc = document.getElementById("match-description").value.trim();
  const cat = document.getElementById("match-category").value;
  const loc = document.getElementById("match-location").value;
  const threshold = document.getElementById("match-threshold").value;

  if (!currentQueryFile && !desc) {
    alert("Please provide either an image or a description to perform a search.");
    return;
  }

  const loader = document.getElementById("results-loader");
  const container = document.getElementById("results-container");
  const resultsCount = document.getElementById("results-count");

  loader.classList.remove("hidden");
  container.innerHTML = "";

  const formData = new FormData();
  if (currentQueryFile) {
    formData.append("image", currentQueryFile);
  }
  if (desc) {
    formData.append("description", desc);
  }
  formData.append("category", cat);
  formData.append("location", loc);
  formData.append("min_confidence", threshold);

  try {
    const res = await fetch("/api/match", {
      method: "POST",
      body: formData,
    });

    const data = await res.json();
    loader.classList.add("hidden");

    if (!res.ok) {
      container.innerHTML = `<div class="empty-state"><h4>Search Error</h4><p>${data.detail || "Unable to complete search."}</p></div>`;
      return;
    }

    if (!data.matches || data.matches.length === 0) {
      resultsCount.textContent = "No items matched the current confidence threshold.";
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="8" y1="12" x2="16" y2="12"></line>
            </svg>
          </div>
          <h4>No Direct Custody Matches Found</h4>
          <p>Try lowering the confidence threshold slider or submit a <strong>Lost Item Inquiry</strong> below so our continuous monitor alerts you upon intake.</p>
        </div>
      `;
      return;
    }

    resultsCount.textContent = `Found ${data.matches.length} high-confidence matching items in custody vaults:`;

    data.matches.forEach((m) => {
      const it = m.item;
      const reasonsHtml = m.reasons.map((r) => `<span class="reason-tag">${r}</span>`).join("");
      const card = document.createElement("div");
      card.className = "match-card";
      card.innerHTML = `
        <div class="match-img-wrap">
          <img src="/${it.image_path}" alt="${it.title}" onerror="this.src='/data/registered_items/backpack.jpg'" />
          <span class="match-badge ${m.badge_class}">${m.confidence}% Match</span>
        </div>
        <div class="match-body">
          <h4 class="match-title">${it.title}</h4>
          <div class="match-meta">
            <span>📍 ${it.location || "Campus Custody"}</span> •
            <span>📅 ${it.date_found || "Recent"}</span>
          </div>
          <div class="match-reasons">${reasonsHtml}</div>
          <div class="match-footer">
            <span class="custody-tag">🔒 ${it.custody_location || "Vault A"}</span>
            <button class="btn btn-primary btn-sm btn-claim" data-id="${it.id}" data-title="${it.title}" data-prompt="${it.verification_prompt || 'Describe unique identifying features.'}">
              Claim Item
            </button>
          </div>
        </div>
      `;
      container.appendChild(card);
    });

    // Attach event listeners to new claim buttons
    document.querySelectorAll(".btn-claim").forEach((btn) => {
      btn.addEventListener("click", () => {
        openClaimModal(
          btn.getAttribute("data-id"),
          btn.getAttribute("data-title"),
          btn.getAttribute("data-prompt")
        );
      });
    });
  } catch (err) {
    loader.classList.add("hidden");
    container.innerHTML = `<div class="empty-state"><h4>Connection Error</h4><p>Unable to connect to matching server.</p></div>`;
    console.error("Match error:", err);
  }
}

// ==========================================================
// 3. LIVE CUSTODY CATALOG
// ==========================================================
let allCatalogItems = [];
let activeCategory = "all";

async function initCatalog() {
  const pills = document.querySelectorAll(".category-pills .pill");
  const searchInput = document.getElementById("catalog-search");

  pills.forEach((pill) => {
    pill.addEventListener("click", () => {
      pills.forEach((p) => p.classList.remove("active"));
      pill.classList.add("active");
      activeCategory = pill.getAttribute("data-cat");
      filterAndRenderCatalog();
    });
  });

  if (searchInput) {
    searchInput.addEventListener("input", filterAndRenderCatalog);
  }

  await loadCatalogItems();
}

async function loadCatalogItems() {
  try {
    const res = await fetch("/api/items");
    if (!res.ok) return;
    allCatalogItems = await res.json();
    filterAndRenderCatalog();
  } catch (err) {
    console.warn("Catalog fetch failed:", err);
  }
}

function filterAndRenderCatalog() {
  const container = document.getElementById("catalog-items-grid");
  const searchVal = (document.getElementById("catalog-search")?.value || "").toLowerCase().trim();

  let filtered = allCatalogItems;

  if (activeCategory !== "all") {
    filtered = filtered.filter((it) => (it.category || "").toLowerCase() === activeCategory.toLowerCase());
  }

  if (searchVal) {
    filtered = filtered.filter(
      (it) =>
        (it.title || "").toLowerCase().includes(searchVal) ||
        (it.description || "").toLowerCase().includes(searchVal) ||
        (it.location || "").toLowerCase().includes(searchVal) ||
        (it.brand || "").toLowerCase().includes(searchVal)
    );
  }

  container.innerHTML = "";

  if (filtered.length === 0) {
    container.innerHTML = `<div class="empty-state" style="grid-column: 1 / -1;"><p>No items found matching the selected filter criteria.</p></div>`;
    return;
  }

  filtered.forEach((it) => {
    let statusClass = "status-available";
    let statusText = "In Safe Custody";
    if (it.status === "Claim Under Review") {
      statusClass = "status-review";
      statusText = "Claim In Review";
    } else if (it.status === "Reunited & Returned") {
      statusClass = "status-reunited";
      statusText = "Reunited";
    }

    const card = document.createElement("div");
    card.className = "catalog-card";
    card.innerHTML = `
      <div class="catalog-img-wrap">
        <img src="/${it.image_path}" alt="${it.title}" onerror="this.src='/data/registered_items/backpack.jpg'" />
        <span class="status-pill ${statusClass}">${statusText}</span>
      </div>
      <div class="catalog-body">
        <h4 class="catalog-title">${it.title}</h4>
        <div class="catalog-loc">📍 ${it.location || "Campus Main Desk"}</div>
        <div class="catalog-footer">
          <span class="date-tag">Found: ${it.date_found || "Recent"}</span>
          ${
            it.status === "Available"
              ? `<button class="btn btn-outline btn-sm btn-claim" data-id="${it.id}" data-title="${it.title}" data-prompt="${it.verification_prompt || 'Describe unique identifying features.'}">Claim</button>`
              : `<span class="date-tag" style="font-weight:600;">Custody Held</span>`
          }
        </div>
      </div>
    `;
    container.appendChild(card);
  });

  // Re-attach claim button events
  container.querySelectorAll(".btn-claim").forEach((btn) => {
    btn.addEventListener("click", () => {
      openClaimModal(
        btn.getAttribute("data-id"),
        btn.getAttribute("data-title"),
        btn.getAttribute("data-prompt")
      );
    });
  });
}

// ==========================================================
// 4. REPORT FORMS (FOUND & LOST INTAKE)
// ==========================================================
function initReportForms() {
  const formFound = document.getElementById("form-report-found");
  const foundAlert = document.getElementById("found-alert-box");

  if (formFound) {
    formFound.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btnSubmit = document.getElementById("btn-submit-found");
      btnSubmit.disabled = true;
      btnSubmit.textContent = "Processing & Generating Visual Vectors...";

      const formData = new FormData();
      formData.append("title", document.getElementById("found-title").value);
      formData.append("category", document.getElementById("found-category").value);
      formData.append("location", document.getElementById("found-location").value);
      formData.append("brand", document.getElementById("found-brand").value);
      formData.append("color", document.getElementById("found-color").value);
      formData.append("date_found", document.getElementById("found-date").value);
      formData.append("custody_location", document.getElementById("found-custody").value);
      formData.append("verification_prompt", document.getElementById("found-question").value);

      const fileField = document.getElementById("found-image-input");
      if (fileField.files && fileField.files[0]) {
        formData.append("image", fileField.files[0]);
      }

      try {
        const res = await fetch("/api/report-found", {
          method: "POST",
          body: formData,
        });
        const result = await res.json();
        btnSubmit.disabled = false;
        btnSubmit.textContent = "Register Item into Secure Custody";

        if (res.ok) {
          let alertHtml = `
            <strong>Intake Success!</strong> Registered item with Custody ID: <code>${result.item.id}</code>.
          `;
          if (result.reverse_matches_found > 0) {
            alertHtml += `<br /><br /><strong>🚨 Automated Alert:</strong> Found ${result.reverse_matches_found} potential owner inquiries matching this item! Contacting verified claimants.`;
          }
          foundAlert.className = "alert-box alert-success";
          foundAlert.innerHTML = alertHtml;
          foundAlert.classList.remove("hidden");
          formFound.reset();
          loadCatalogItems();
          initStats();
        } else {
          foundAlert.className = "alert-box alert-danger";
          foundAlert.textContent = result.detail || "Failed to register item.";
          foundAlert.classList.remove("hidden");
        }
      } catch (err) {
        btnSubmit.disabled = false;
        btnSubmit.textContent = "Register Item into Secure Custody";
        foundAlert.className = "alert-box alert-danger";
        foundAlert.textContent = "Network error. Please try again.";
        foundAlert.classList.remove("hidden");
      }
    });
  }

  const formLost = document.getElementById("form-report-lost");
  const lostAlert = document.getElementById("lost-alert-box");

  if (formLost) {
    formLost.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btnSubmit = document.getElementById("btn-submit-lost");
      btnSubmit.disabled = true;
      btnSubmit.textContent = "Submitting Inquiry...";

      const payload = {
        item_name: document.getElementById("lost-name").value,
        category: document.getElementById("lost-category").value,
        description: document.getElementById("lost-description").value,
        location_lost: document.getElementById("lost-location").value,
        date_lost: document.getElementById("lost-date").value,
        contact_name: document.getElementById("lost-contact-name").value,
        contact_email: document.getElementById("lost-contact-email").value,
        contact_phone: document.getElementById("lost-contact-phone").value,
      };

      try {
        const res = await fetch("/api/report-lost", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const result = await res.json();
        btnSubmit.disabled = false;
        btnSubmit.textContent = "Submit Lost Report & Enable Auto-Alerts";

        if (res.ok) {
          let alertHtml = `
            <strong>Report Logged!</strong> Reference: <code>${result.report_id}</code>.<br />
            Our automated matcher will notify you at ${payload.contact_email} when matching items are registered.
          `;
          if (result.immediate_matches && result.immediate_matches.length > 0) {
            alertHtml += `<br /><br /><strong>Instant Match Found in Vault!</strong> Found ${result.immediate_matches.length} candidate(s) currently held in custody. Please visit the search studio or custody desk.`;
          }
          lostAlert.className = "alert-box alert-success";
          lostAlert.innerHTML = alertHtml;
          lostAlert.classList.remove("hidden");
          formLost.reset();
        } else {
          lostAlert.className = "alert-box alert-danger";
          lostAlert.textContent = result.detail || "Failed to submit lost report.";
          lostAlert.classList.remove("hidden");
        }
      } catch (err) {
        btnSubmit.disabled = false;
        btnSubmit.textContent = "Submit Lost Report & Enable Auto-Alerts";
        lostAlert.className = "alert-box alert-danger";
        lostAlert.textContent = "Network error. Please try again.";
        lostAlert.classList.remove("hidden");
      }
    });
  }
}

// ==========================================================
// 5. ANTI-THEFT CLAIM MODAL
// ==========================================================
function initClaimModal() {
  const modal = document.getElementById("claim-modal");
  const btnClose = document.getElementById("btn-close-modal");
  const btnCancel = document.getElementById("btn-cancel-claim");
  const formClaim = document.getElementById("form-submit-claim");
  const modalAlert = document.getElementById("modal-alert");

  if (btnClose) btnClose.addEventListener("click", closeClaimModal);
  if (btnCancel) btnCancel.addEventListener("click", closeClaimModal);

  if (formClaim) {
    formClaim.addEventListener("submit", async (e) => {
      e.preventDefault();
      const btnConfirm = document.getElementById("btn-confirm-claim");
      btnConfirm.disabled = true;
      btnConfirm.textContent = "Submitting Claim...";

      const payload = {
        item_id: document.getElementById("claim-item-id").value,
        claimant_name: document.getElementById("claim-name").value,
        claimant_phone: document.getElementById("claim-phone").value,
        claimant_email: document.getElementById("claim-email").value,
        identifying_details: document.getElementById("claim-details").value,
      };

      try {
        const res = await fetch("/api/claim", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const result = await res.json();
        btnConfirm.disabled = false;
        btnConfirm.textContent = "Submit Claim for Review";

        if (res.ok) {
          modalAlert.className = "alert-box alert-success";
          modalAlert.innerHTML = `
            <strong>Claim Registered:</strong> Tracking ID <code>${result.claim_id}</code>.<br />
            Please report to <strong>${result.custody_location || "Campus Security Desk"}</strong> with photo identification to complete physical handover.
          `;
          modalAlert.classList.remove("hidden");
          setTimeout(() => {
            closeClaimModal();
            loadCatalogItems();
            loadClaimsQueue();
            initStats();
          }, 3500);
        } else {
          modalAlert.className = "alert-box alert-danger";
          modalAlert.textContent = result.detail || "Error filing claim.";
          modalAlert.classList.remove("hidden");
        }
      } catch (err) {
        btnConfirm.disabled = false;
        btnConfirm.textContent = "Submit Claim for Review";
        modalAlert.className = "alert-box alert-danger";
        modalAlert.textContent = "Network error. Please try again.";
        modalAlert.classList.remove("hidden");
      }
    });
  }
}

function openClaimModal(itemId, itemTitle, prompt) {
  const modal = document.getElementById("claim-modal");
  const modalItemTitle = document.getElementById("modal-item-title");
  const modalPrompt = document.getElementById("modal-verification-prompt");
  const inputItemId = document.getElementById("claim-item-id");
  const modalAlert = document.getElementById("modal-alert");
  const formClaim = document.getElementById("form-submit-claim");

  if (modalItemTitle) modalItemTitle.textContent = `Item: ${itemTitle}`;
  if (modalPrompt) modalPrompt.textContent = prompt || "Describe any unique scratch, marks, or packaging details.";
  if (inputItemId) inputItemId.value = itemId;
  if (modalAlert) modalAlert.classList.add("hidden");
  if (formClaim) formClaim.reset();

  modal.classList.remove("hidden");
}

function closeClaimModal() {
  const modal = document.getElementById("claim-modal");
  if (modal) modal.classList.add("hidden");
}

// ==========================================================
// 6. CLAIMS VERIFICATION DESK (ADMIN / CUSTODY)
// ==========================================================
function initClaimsDesk() {
  const btnRefresh = document.getElementById("btn-refresh-claims");
  if (btnRefresh) {
    btnRefresh.addEventListener("click", loadClaimsQueue);
  }
  loadClaimsQueue();
}

async function loadClaimsQueue() {
  const tbody = document.getElementById("claims-tbody");
  if (!tbody) return;

  try {
    const res = await fetch("/api/claims");
    if (!res.ok) return;
    const claims = await res.json();

    tbody.innerHTML = "";
    if (claims.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #94A3B8; padding: 32px;">No active claims in queue.</td></tr>`;
      return;
    }

    claims.forEach((c) => {
      const tr = document.createElement("tr");
      let statusBadge = `<span class="status-pill status-review">Pending</span>`;
      if (c.status === "Approved") statusBadge = `<span class="status-pill status-available">Approved</span>`;
      if (c.status === "Rejected") statusBadge = `<span class="status-pill status-reunited">Rejected</span>`;

      tr.innerHTML = `
        <td><strong>${c.claim_id}</strong></td>
        <td>
          <div style="font-weight:600;">${c.item_title}</div>
          <small style="color:#64748B;">ID: ${c.item_id}</small>
        </td>
        <td>
          <div>${c.claimant_name}</div>
          <small style="color:#64748B;">${c.claimant_phone}</small>
        </td>
        <td class="proof-snippet">
          <em>"${c.identifying_details || 'No proof supplied'}"</em>
        </td>
        <td>${statusBadge}</td>
        <td>
          ${
            c.status === "Pending Review"
              ? `
              <div style="display:flex; gap:6px;">
                <button class="btn btn-sm btn-primary btn-verify" data-id="${c.claim_id}" data-action="Approved">Approve</button>
                <button class="btn btn-sm btn-outline btn-verify" data-id="${c.claim_id}" data-action="Rejected">Reject</button>
              </div>
            `
              : `<small style="color:#94A3B8;">Resolved</small>`
          }
        </td>
      `;
      tbody.appendChild(tr);
    });

    tbody.querySelectorAll(".btn-verify").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const claimId = btn.getAttribute("data-id");
        const action = btn.getAttribute("data-action");
        await verifyClaim(claimId, action);
      });
    });
  } catch (err) {
    console.warn("Failed to load claims queue:", err);
  }
}

async function verifyClaim(claimId, decision) {
  try {
    const res = await fetch(`/api/claims/${claimId}/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision, notes: `Processed by custody officer on ${new Date().toLocaleDateString()}` }),
    });
    if (res.ok) {
      loadClaimsQueue();
      loadCatalogItems();
      initStats();
    }
  } catch (err) {
    console.error("Verification error:", err);
  }
}
