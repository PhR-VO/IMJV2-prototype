if (window.location.protocol === "file:") {
  window.location.replace("http://127.0.0.1:8001/");
}

let odsRows = [
  ["Type", "Code", "Naam", "Eigenschappen", "Verbonden met", "Status"],
  ["Productielijn", "PL-01", "Productielijn keramische granulaten", "Capaciteit: 120000 ton/jaar", "STK-01; WZI-01", "In gebruik"],
  ["Stookinstallatie", "STK-01", "Stoomketel lijn 1", "Thermisch vermogen: 48 MW; brandstof: aardgas", "PL-01; EP-L-01", "In gebruik"],
  ["Waterzuivering", "WZI-01", "Fysico-chemische waterzuivering", "Neutralisatie + sedimentatie + zandfilter; capaciteit: 35 m3/u", "PL-01; EP-W-01", "In gebruik"],
  ["Grondwaterwinning", "GW-01", "Winning productieput noord", "Putdiepte: 82 m; debietmeter: DM-4451; watervoerende laag: HCOV 0600", "PL-01", "In gebruik"],
  ["Emissiepunt lucht", "EP-L-01", "Schoorsteen stoomketel", "Hoogte: 32 m; diameter: 1.2 m; Lambert 2008: 156420, 207880", "STK-01", "In gebruik"],
  ["Emissiepunt water", "EP-W-01", "Lozingspunt effluent WZI", "Lozend naar oppervlaktewater; Lambert 2008: 156385, 207842", "WZI-01", "In gebruik"],
];

const API = "/api";
let currentDraft = null;
let submissions = [];
let selectedItem = null;
let editor = null;
let selectedObjectIndex = 0;
let selectedEditorPart = "date";
let reports = [];
let exploitations = [];
let selectedReport = null;
let reportDisplayMode = "timeline";
let showReplacedReports = false;
let activeExploitationId = null;
let currentView = "exploitations";
const routedViews = new Set(["exploitations", "editor", "submit", "submissions", "reports"]);
let applyingRoute = false;
let exploitationMap = null;
let exploitationMapMarkers = null;
let exploitationMapBounds = null;

const els = {
  mainNavigation: document.querySelector("nav.tabs"),
  tabExploitations: document.querySelector("#tab-exploitations"),
  tabEditor: document.querySelector("#tab-editor"),
  tabSubmit: document.querySelector("#tab-submit"),
  tabSubmissions: document.querySelector("#tab-submissions"),
  tabReports: document.querySelector("#tab-reports"),
  editorView: document.querySelector("#editor-view"),
  submitView: document.querySelector("#submit-view"),
  submissionsView: document.querySelector("#submissions-view"),
  reportsView: document.querySelector("#reports-view"),
  exploitationsView: document.querySelector("#exploitations-view"),
  exploitationItems: document.querySelector("#exploitation-items"),
  draftExploitationItems: document.querySelector("#draft-exploitation-items"),
  draftExploitationsSection: document.querySelector("#draft-exploitations-section"),
  exploitationMap: document.querySelector("#exploitation-map"),
  exploitationMapEmpty: document.querySelector("#exploitation-map-empty"),
  exploitationRegistration: document.querySelector("#exploitation-registration"),
  exploitationForm: document.querySelector("#exploitation-form"),
  exploitationValidation: document.querySelector("#exploitation-validation"),
  newExploitationButton: document.querySelector("#new-exploitation-button"),
  cancelExploitationButton: document.querySelector("#cancel-exploitation-button"),
  cancelExploitationFormButton: document.querySelector("#cancel-exploitation-form-button"),
  transactionId: document.querySelector("#transaction-id"),
  contentHash: document.querySelector("#content-hash"),
  basketExploitation: document.querySelector("#basket-exploitation"),
  basketNaceBelCode: document.querySelector("#basket-nace-bel-code"),
  previewButton: document.querySelector("#preview-button"),
  previewButtonDetail: document.querySelector("#preview-button-detail"),
  previewReceiptButton: document.querySelector("#preview-receipt-button"),
  previewReceiptResultButton: document.querySelector("#preview-receipt-result-button"),
  submitButton: document.querySelector("#submit-button"),
  detailSubmitButton: document.querySelector("#detail-submit-button"),
  deleteDraftSubmission: document.querySelector("#delete-draft-submission"),
  modal: document.querySelector("#modal"),
  closeModal: document.querySelector("#close-modal"),
  previewTable: document.querySelector("#preview-table"),
  receiptPreview: document.querySelector("#receipt-preview"),
  schemaPreview: document.querySelector("#schema-preview"),
  submissionModalDetail: document.querySelector("#submission-modal-detail"),
  modalEyebrow: document.querySelector("#modal-eyebrow"),
  modalTitle: document.querySelector("#modal-title"),
  receiptEmpty: document.querySelector("#receipt-empty"),
  receiptBody: document.querySelector("#receipt-body"),
  receiptActions: document.querySelector("#receipt-actions"),
  receiptDownload: document.querySelector("#receipt-download"),
  basketStatus: document.querySelector("#basket-status"),
  basketTitle: document.querySelector("#basket-title"),
  basketEmptyMessage: document.querySelector("#basket-empty-message"),
  basketTransactionSection: document.querySelector("#basket-transaction-section"),
  basketContentSection: document.querySelector("#basket-content-section"),
  basketFilesSection: document.querySelector("#basket-files-section"),
  stepSubmit: document.querySelector("#step-submit"),
  stepReceipt: document.querySelector("#step-receipt"),
  submissionItems: document.querySelector("#submission-items"),
  submissionDetail: document.querySelector("#submission-detail"),
  submissionPayload: document.querySelector("#submission-payload"),
  submissionFilesSection: document.querySelector("#submission-files-section"),
  submissionOdsRow: document.querySelector("#submission-ods-row"),
  submissionSchemaRow: document.querySelector("#submission-schema-row"),
  detailReceiptDownload: document.querySelector("#detail-receipt-download"),
  receiptDocumentSection: document.querySelector("#receipt-document-section"),
  receiptDocumentDescription: document.querySelector("#receipt-document-description"),
  editorObjectList: document.querySelector("#editor-object-list"),
  editorHeadingTitle: document.querySelector("#editor-heading-title"),
  editorHeadingDescription: document.querySelector("#editor-heading-description"),
  editorStructure: document.querySelector("#editor-structure"),
  editorDateEntry: document.querySelector("#editor-date-entry"),
  editorExploitationEntry: document.querySelector("#editor-exploitation-entry"),
  editorDateForm: document.querySelector("#editor-date-form"),
  editorDateFormTitle: document.querySelector("#editor-date-form-title"),
  cancelDateChanges: document.querySelector("#cancel-date-changes"),
  applyDateChanges: document.querySelector("#apply-date-changes"),
  editorForm: document.querySelector("#editor-form"),
  editorObjectDetail: document.querySelector("#editor-object-detail"),
  editorFormTitle: document.querySelector("#editor-form-title"),
  editorValidation: document.querySelector("#editor-validation"),
  editorObjectCount: document.querySelector("#editor-object-count"),
  editorExploitationForm: document.querySelector("#editor-exploitation-form"),
  cancelExploitationChanges: document.querySelector("#cancel-exploitation-changes"),
  applyExploitationChanges: document.querySelector("#apply-exploitation-changes"),
  cancelObjectChanges: document.querySelector("#cancel-object-changes"),
  applyObjectChanges: document.querySelector("#apply-object-changes"),
  addObjectButton: document.querySelector("#add-object-button"),
  deleteObjectButton: document.querySelector("#delete-object-button"),
  prepareSubmitButton: document.querySelector("#prepare-submit-button"),
  draftDownload: document.querySelector("#draft-download"),
  draftSchemaDownload: document.querySelector("#draft-schema-download"),
  detailSchemaDownload: document.querySelector("#detail-schema-download"),
  draftSchemaPreview: document.querySelector("#draft-schema-preview"),
  detailSchemaPreview: document.querySelector("#detail-schema-preview"),
  reportItems: document.querySelector("#report-items"),
  draftReportEntry: document.querySelector("#draft-report-entry"),
  draftReportActions: document.querySelector("#draft-report-actions"),
  editDraftReport: document.querySelector("#edit-draft-report"),
  reviewDraftSubmission: document.querySelector("#review-draft-submission"),
  deleteDraftReport: document.querySelector("#delete-draft-report"),
  reportReplacementNotices: document.querySelector("#report-replacement-notices"),
  registeredReportActions: document.querySelector("#registered-report-actions"),
  correctReport: document.querySelector("#correct-report"),
  newStateFromReport: document.querySelector("#new-state-from-report"),
  withdrawReport: document.querySelector("#withdraw-report"),
  reportsExploitationName: document.querySelector("#reports-exploitation-name"),
  reportsExploitationLocation: document.querySelector("#reports-exploitation-location"),
  reportsExploitationId: document.querySelector("#reports-exploitation-id"),
  reportsExploitationStatus: document.querySelector("#reports-exploitation-status"),
  reportsExploitationContext: document.querySelector("#reports-exploitation-context"),
  reportsContextToolbar: document.querySelector("#reports-context-toolbar"),
  reportsContactContext: document.querySelector(".reports-contact-context"),
  reportsSectionTitle: document.querySelector("#reports-section-title"),
  reportsViewSwitch: document.querySelector("#reports-view-switch"),
  reportsModeToggle: document.querySelector("#reports-mode-toggle"),
  reportsList: document.querySelector("#reports-list"),
  replacedReportsToggle: document.querySelector("#replaced-reports-toggle"),
  showReplacedReports: document.querySelector("#show-replaced-reports"),
  reportDetailTitle: document.querySelector("#report-detail-title"),
  reportMetadata: document.querySelector("#report-metadata"),
  reportEffectiveDate: document.querySelector("#report-effective-date"),
  reportSubmittedDate: document.querySelector("#report-submitted-date"),
  draftWarning: document.querySelector("#draft-warning"),
  draftWarningText: document.querySelector("#draft-warning-text"),
  reportObjectList: document.querySelector("#report-object-list"),
  openSourceSubmission: document.querySelector("#open-source-submission"),
  previousReport: document.querySelector("#previous-report"),
  newerReport: document.querySelector("#newer-report"),
  reportsTimelineView: document.querySelector("#reports-timeline-view"),
  reportsDiffView: document.querySelector("#reports-diff-view"),
  showReportTimeline: document.querySelector("#show-report-timeline"),
  showReportDiff: document.querySelector("#show-report-diff"),
  reportsEditMode: document.querySelector("#reports-edit-mode"),
  closeEditMode: document.querySelector("#close-edit-mode"),
  reportDiffTable: document.querySelector("#report-diff-table"),
};

init();

async function init() {
  renderPreviewTable();
  bindEvents();
  try {
    [currentDraft, submissions, editor, reports, exploitations] = await Promise.all([
      request(`${API}/current`),
      request(`${API}/submissions`),
      request(`${API}/editor`),
      request(`${API}/reports`),
      request(`${API}/exploitations`),
    ]);
    syncPreviewRows();
    selectedItem = submissions[0] || currentDraft;
    selectedReport = reports[0] || null;
    activeExploitationId = selectedReport?.exploitatieId || editor?.exploitatieId || null;
    await applyRouteFromLocation({ replace: true, skipReload: true });
  } catch (error) {
    showServerError(error);
  }
}

function bindEvents() {
  els.tabExploitations.addEventListener("click", () => showView("exploitations"));
  els.draftSchemaPreview.addEventListener("click", () => openSchemaPreview(currentDraft || selectedItem));
  els.detailSchemaPreview.addEventListener("click", () => openSchemaPreview(selectedItem));
  els.previewButton.addEventListener("click", openSpreadsheetPreview);
  els.previewButtonDetail.addEventListener("click", openSpreadsheetPreview);
  els.previewReceiptButton.addEventListener("click", openReceiptPreview);
  els.previewReceiptResultButton.addEventListener("click", openReceiptPreview);
  els.closeModal.addEventListener("click", closeModal);
  els.modal.addEventListener("click", (event) => {
    if (event.target === els.modal) closeModal();
  });
  els.submissionModalDetail.addEventListener("click", (event) => {
    const action = event.target.closest("[data-modal-action]")?.dataset.modalAction;
    if (action === "preview-button-detail") openSpreadsheetPreview();
    if (action === "detail-schema-preview") openSchemaPreview(selectedItem);
    if (action === "preview-receipt-button") openReceiptPreview();
    if (action === "cancel-withdrawal") closeModal();
  });
  els.submissionModalDetail.addEventListener("submit", submitWithdrawal);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !els.modal.hidden) closeModal();
    if (event.key === "Escape" && !els.exploitationRegistration.hidden) closeExploitationRegistration();
  });
  window.addEventListener("popstate", () => {
    applyRouteFromLocation();
  });
  els.tabSubmit.addEventListener("click", () => showView("submit"));
  els.tabSubmissions.addEventListener("click", () => showView("submissions"));
  els.newExploitationButton.addEventListener("click", () => {
    els.exploitationRegistration.hidden = false;
  });
  els.cancelExploitationButton.addEventListener("click", closeExploitationRegistration);
  els.cancelExploitationFormButton.addEventListener("click", closeExploitationRegistration);
  els.exploitationRegistration.addEventListener("click", (event) => {
    if (event.target === els.exploitationRegistration) closeExploitationRegistration();
  });
  els.exploitationForm.addEventListener("submit", registerFirstState);
  els.exploitationItems.addEventListener("click", selectExploitation);
  els.draftExploitationItems.addEventListener("click", selectExploitation);
  els.exploitationMap.addEventListener("click", selectExploitation);
  els.submitButton.addEventListener("click", submitCurrentDraft);
  els.detailSubmitButton.addEventListener("click", () => showView("submit"));
  els.deleteDraftSubmission.addEventListener("click", () => {
    if (selectedItem?.status === "Nog niet ingediend") clearDraftSubmission(selectedItem.transactionId);
  });
  els.addObjectButton.addEventListener("click", addObject);
  els.deleteObjectButton.addEventListener("click", deleteSelectedObject);
  els.editorForm.addEventListener("submit", applyObjectChanges);
  els.editorDateForm.addEventListener("submit", applyDateChanges);
  els.editorDateForm.elements.effectiveFrom.addEventListener("input", updateDateFormActions);
  els.cancelDateChanges.addEventListener("click", resetDateChanges);
  els.editorExploitationForm.addEventListener("submit", applyExploitationChanges);
  els.editorExploitationForm.addEventListener("input", updateExploitationFormActions);
  els.editorExploitationForm.addEventListener("change", updateExploitationFormActions);
  els.cancelExploitationChanges.addEventListener("click", resetExploitationChanges);
  els.editorForm.addEventListener("input", updateObjectFormActions);
  els.editorForm.addEventListener("change", updateObjectFormActions);
  els.cancelObjectChanges.addEventListener("click", resetObjectChanges);
  els.prepareSubmitButton.addEventListener("click", prepareForSubmission);
  els.editorStructure.addEventListener("click", (event) => {
    const dateButton = event.target.closest('[data-editor-part="date"]');
    if (dateButton) {
      selectedEditorPart = "date";
      renderEditor();
      return;
    }
    const exploitationButton = event.target.closest('[data-editor-part="exploitation"]');
    if (exploitationButton) {
      selectedEditorPart = "exploitation";
      renderEditor();
      return;
    }
    const button = event.target.closest("[data-object-index]");
    if (!button) return;
    selectedEditorPart = "object";
    selectedObjectIndex = Number(button.dataset.objectIndex);
    renderEditor();
  });
  els.submissionItems.addEventListener("click", (event) => {
    const button = event.target.closest("[data-transaction-id]");
    if (!button) return;
    selectedItem = allListItems().find((item) => item.transactionId === button.dataset.transactionId);
    renderSubmissionList();
    renderSubmissionDetail();
    updateRoute();
  });
  els.reportItems.addEventListener("click", (event) => {
    const button = event.target.closest("[data-report-id]");
    if (!button) return;
    selectedReport = reports.find((item) => item.reportId === button.dataset.reportId);
    renderReports();
    updateRoute();
  });
  els.draftReportEntry.addEventListener("click", () => {
    selectedReport = draftReport();
    renderReports();
    updateRoute();
  });
  els.editDraftReport.addEventListener("click", () => showView("editor"));
  els.reviewDraftSubmission.addEventListener("click", prepareForSubmission);
  els.correctReport.addEventListener("click", () => createDerivedDraft("correction"));
  els.newStateFromReport.addEventListener("click", () => createDerivedDraft("new-state"));
  els.withdrawReport.addEventListener("click", openWithdrawalModal);
  els.reportReplacementNotices.addEventListener("click", openRelatedReport);
  els.deleteDraftReport.addEventListener("click", () => {
    if (editor?.reportDraftId) deleteDraftReport(editor.reportDraftId);
  });
  els.openSourceSubmission.addEventListener("click", () => {
    if (!selectedReport) return;
    selectedItem = submissions.find((item) => item.transactionId === selectedReport.transactionId) || selectedItem;
    openSubmissionModal(selectedItem);
  });
  els.previousReport.addEventListener("click", () => selectAdjacentReport(1));
  els.newerReport.addEventListener("click", () => selectAdjacentReport(-1));
  els.showReportTimeline.addEventListener("click", () => setReportDisplayMode("timeline"));
  els.showReportDiff.addEventListener("click", () => setReportDisplayMode("diff"));
  els.showReplacedReports.addEventListener("change", () => {
    showReplacedReports = els.showReplacedReports.checked;
    renderReports();
    updateRoute();
  });
  els.closeEditMode.addEventListener("click", () => {
    selectedReport = draftReport();
    showView("reports");
  });
  els.reportDiffTable.addEventListener("click", (event) => {
    const button = event.target.closest("[data-diff-details]");
    if (!button) return;
    openDiffDetails(button.dataset.diffDetails);
  });
}

async function selectExploitation(event) {
  const button = event.target.closest("[data-exploitation-id]");
  if (!button) return;
  activeExploitationId = button.dataset.exploitationId;
  showReplacedReports = false;
  const draftTransactionId = button.dataset.draftTransactionId;
  const draftReportId = button.dataset.draftReportId;
  if (draftTransactionId) {
    try {
      [currentDraft, editor] = await Promise.all([
        request(`${API}/draft-submissions/${encodeURIComponent(draftTransactionId)}`),
        request(`${API}/draft-submissions/${encodeURIComponent(draftTransactionId)}/editor`),
      ]);
      selectedItem = currentDraft;
      syncPreviewRows();
    } catch (error) {
      showServerError(error);
    }
  } else if (draftReportId) {
    try {
      editor = await request(`${API}/draft-reports/${encodeURIComponent(draftReportId)}`);
      currentDraft = null;
      syncPreviewRows();
    } catch (error) {
      showServerError(error);
    }
  } else {
    currentDraft = null;
    editor = null;
  }
  const exploitationReports = visibleReports();
  selectedReport = editor?.exploitatieId === activeExploitationId
    ? draftReport()
    : (exploitationReports[0] || null);
  renderAll();
  showView("reports");
}

async function clearDraftSubmission(transactionId) {
  if (!transactionId) return;
  const confirmed = window.confirm("Winkelmandje leegmaken? De toestand in opmaak blijft bewaard.");
  if (!confirmed) return;
  try {
    await request(`${API}/draft-submissions/${encodeURIComponent(transactionId)}`, { method: "DELETE" });
    if (currentDraft?.transactionId === transactionId) {
      currentDraft = null;
    }
    if (selectedItem?.transactionId === transactionId) {
      selectedItem = submissions[0] || null;
    }
    exploitations = await request(`${API}/exploitations`);
    selectedReport = editor ? draftReport() : (visibleReports()[0] || null);
    renderAll();
    showView("editor");
  } catch (error) {
    showServerError(error);
  }
}

async function deleteDraftReport(reportId) {
  if (!reportId) return;
  const confirmed = window.confirm(isNewExploitationDraft()
    ? "Registratie van deze exploitatie verwijderen? De inhoud gaat definitief verloren."
    : "Toestand in opmaak verwijderen? De inhoud gaat definitief verloren.");
  if (!confirmed) return;
  try {
    await request(`${API}/draft-reports/${encodeURIComponent(reportId)}`, { method: "DELETE" });
    if (editor?.reportDraftId === reportId) {
      currentDraft = null;
      editor = null;
    }
    exploitations = await request(`${API}/exploitations`);
    selectedReport = visibleReports()[0] || null;
    renderAll();
    showView("exploitations");
  } catch (error) {
    showServerError(error);
  }
}

function selectAdjacentReport(offset) {
  const displayedReports = timelineReports();
  if (selectedReport?.isDraft) {
    if (offset === 1 && displayedReports[0]) selectedReport = displayedReports[0];
    renderReports();
    updateRoute();
    return;
  }
  const currentIndex = displayedReports.findIndex((item) => item.reportId === selectedReport?.reportId);
  if (offset === -1 && currentIndex === 0 && editor) {
    if (editor.exploitatieId === activeExploitationId) selectedReport = draftReport();
    renderReports();
    updateRoute();
    return;
  }
  const target = displayedReports[currentIndex + offset];
  if (!target) return;
  selectedReport = target;
  renderReports();
  updateRoute();
}

async function request(url, options = {}) {
  const response = await fetch(url, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  if (!response.ok) {
    let message = `Server antwoordde met status ${response.status}`;
    try {
      const payload = await response.json();
      if (payload.errors && payload.errors.length) message = payload.errors.join(" ");
    } catch {}
    throw new Error(message);
  }
  return response.json();
}

function addObject() {
  const sequence = editor.objects.length + 1;
  editor.objects.push({
    type: "Productielijn",
    code: `OBJ-${String(sequence).padStart(2, "0")}`,
    name: "Nieuw object",
    properties: "",
    relations: [],
    status: "Gepland",
  });
  selectedEditorPart = "object";
  selectedObjectIndex = editor.objects.length - 1;
  refreshDraftViews();
}

function deleteSelectedObject() {
  if (!editor?.objects.length) return;
  const removed = editor.objects[selectedObjectIndex];
  editor.objects.splice(selectedObjectIndex, 1);
  editor.objects.forEach((item) => {
    item.relations = item.relations.filter((code) => code !== removed.code);
  });
  selectedObjectIndex = Math.max(0, selectedObjectIndex - 1);
  if (!editor.objects.length) selectedEditorPart = "exploitation";
  refreshDraftViews();
}

function applyObjectChanges(event) {
  event.preventDefault();
  const form = new FormData(els.editorForm);
  const previousCode = editor.objects[selectedObjectIndex]?.code;
  const updated = {
    type: form.get("type").trim(),
    code: form.get("code").trim().toUpperCase(),
    name: form.get("name").trim(),
    status: form.get("status"),
    properties: form.get("properties").trim(),
    relations: form.get("relations").split(",").map((value) => value.trim().toUpperCase()).filter(Boolean),
  };
  editor.objects[selectedObjectIndex] = updated;
  if (previousCode && previousCode !== updated.code) {
    editor.objects.forEach((item, index) => {
      if (index !== selectedObjectIndex) {
        item.relations = item.relations.map((code) => code === previousCode ? updated.code : code);
      }
    });
  }
  refreshDraftViews();
}

function applyExploitationChanges(event) {
  event.preventDefault();
  const form = new FormData(els.editorExploitationForm);
  editor.exploitatie = form.get("exploitatie").trim();
  editor.naceBelCode = form.get("naceBelCode").trim();
  const lambertX = form.get("lambertX").trim();
  const lambertY = form.get("lambertY").trim();
  editor.location = {
    address: {
      street: form.get("street").trim(),
      houseNumber: form.get("houseNumber").trim(),
      postalCode: form.get("postalCode").trim(),
      municipality: form.get("municipality").trim(),
      country: "België",
    },
    lambert2008: {
      x: lambertX ? Number(lambertX) : null,
      y: lambertY ? Number(lambertY) : null,
    },
  };
  activeExploitationId = editor.exploitatieId;
  refreshDraftViews();
}

function applyDateChanges(event) {
  event.preventDefault();
  const form = new FormData(els.editorDateForm);
  editor.effectiveFrom = form.get("effectiveFrom");
  refreshDraftViews();
}

function updateDateFormActions() {
  const changed = els.editorDateForm.elements.effectiveFrom.value !== (editor?.effectiveFrom || "");
  els.applyDateChanges.disabled = !changed;
  els.cancelDateChanges.disabled = !changed;
}

function resetDateChanges() {
  els.editorDateForm.elements.effectiveFrom.value = editor?.effectiveFrom || "";
  updateDateFormActions();
}

function exploitationFormValues() {
  const form = new FormData(els.editorExploitationForm);
  return {
    exploitatie: form.get("exploitatie").trim(),
    exploitatieId: form.get("exploitatieId").trim(),
    naceBelCode: form.get("naceBelCode").trim(),
    street: form.get("street").trim(),
    houseNumber: form.get("houseNumber").trim(),
    postalCode: form.get("postalCode").trim(),
    municipality: form.get("municipality").trim(),
    lambertX: form.get("lambertX"),
    lambertY: form.get("lambertY"),
  };
}

function storedExploitationValues() {
  const address = editor?.location?.address || {};
  const coordinates = editor?.location?.lambert2008 || {};
  return {
    exploitatie: editor?.exploitatie || "",
    exploitatieId: editor?.exploitatieId || "",
    naceBelCode: editor?.naceBelCode || "",
    street: address.street || "",
    houseNumber: address.houseNumber || "",
    postalCode: address.postalCode || "",
    municipality: address.municipality || "",
    lambertX: coordinates.x == null ? "" : String(coordinates.x),
    lambertY: coordinates.y == null ? "" : String(coordinates.y),
  };
}

function updateExploitationFormActions() {
  const changed = JSON.stringify(exploitationFormValues()) !== JSON.stringify(storedExploitationValues());
  els.applyExploitationChanges.disabled = !changed;
  els.cancelExploitationChanges.disabled = !changed;
}

function resetExploitationChanges() {
  renderEditor();
}

function objectFormValues() {
  const form = new FormData(els.editorForm);
  return {
    type: form.get("type").trim(),
    code: form.get("code").trim().toUpperCase(),
    name: form.get("name").trim(),
    status: form.get("status"),
    properties: form.get("properties").trim(),
    relations: form.get("relations").split(",").map((value) => value.trim().toUpperCase()).filter(Boolean),
  };
}

function storedObjectValues() {
  const item = editor?.objects?.[selectedObjectIndex];
  return item ? {
    type: item.type || "",
    code: item.code || "",
    name: item.name || "",
    status: item.status || "",
    properties: item.properties || "",
    relations: item.relations || [],
  } : null;
}

function updateObjectFormActions() {
  const stored = storedObjectValues();
  const changed = Boolean(stored) && JSON.stringify(objectFormValues()) !== JSON.stringify(stored);
  els.applyObjectChanges.disabled = !changed;
  els.cancelObjectChanges.disabled = !changed;
}

function resetObjectChanges() {
  renderEditor();
}

async function refreshDraftViews() {
  syncPreviewRows();
  renderEditor();
  renderReports();
  try {
    await persistEditorSource();
  } catch (error) {
    els.editorValidation.textContent = error.message;
    els.editorValidation.hidden = false;
  }
}

async function persistEditorSource() {
  if (!editor?.reportDraftId) return;
  if (currentDraftMatchesEditor()) {
    const result = await request(`${API}/draft-submissions/${encodeURIComponent(currentDraft.transactionId)}/editor`, {
      method: "PUT",
      body: JSON.stringify(editor),
    });
    editor = result.editor;
    currentDraft = result.manifest;
    return;
  }
  editor = await request(`${API}/draft-reports/${encodeURIComponent(editor.reportDraftId)}`, {
    method: "PUT",
    body: JSON.stringify(editor),
  });
}

function currentDraftMatchesEditor() {
  return Boolean(
    currentDraft?.transactionId
    && currentDraft?.reportDraftId
    && editor?.reportDraftId
    && currentDraft.reportDraftId === editor.reportDraftId
  );
}

async function prepareForSubmission() {
  els.prepareSubmitButton.disabled = true;
  els.prepareSubmitButton.textContent = "Wordt klaargezet...";
  try {
    const result = currentDraftMatchesEditor()
      ? await request(`${API}/draft-submissions/${encodeURIComponent(currentDraft.transactionId)}/editor`, {
          method: "PUT",
          body: JSON.stringify(editor),
        })
      : await request(`${API}/draft-reports/${encodeURIComponent(editor.reportDraftId)}/submission`, {
          method: "POST",
          body: JSON.stringify(editor),
        });
    editor = result.editor;
    currentDraft = result.manifest;
    selectedItem = currentDraft;
    syncPreviewRows();
    renderAll();
    els.editorValidation.hidden = true;
    showView("submit");
  } catch (error) {
    els.editorValidation.textContent = error.message;
    els.editorValidation.hidden = false;
  } finally {
    els.prepareSubmitButton.disabled = false;
    els.prepareSubmitButton.textContent = "Klaarzetten voor indiening";
  }
}

async function submitCurrentDraft() {
  if (!currentDraft || els.submitButton.disabled) return;
  els.submitButton.disabled = true;
  els.detailSubmitButton.disabled = true;
  els.submitButton.textContent = "Wordt ingediend...";
  els.basketStatus.textContent = "In verwerking";
  els.basketStatus.classList.add("sent");
  els.stepSubmit.classList.add("active");

  try {
    const received = await request(
      `${API}/draft-submissions/${encodeURIComponent(currentDraft.transactionId)}/submit`,
      { method: "POST" }
    );
    submissions = [received, ...submissions.filter((item) => item.transactionId !== received.transactionId)];
    [reports, exploitations] = await Promise.all([
      request(`${API}/reports`),
      request(`${API}/exploitations`),
    ]);
    activeExploitationId = received.exploitatieId || activeExploitationId;
    selectedReport = visibleReports()[0] || null;
    selectedItem = received;
    currentDraft = null;
    editor = null;
    renderAll();
    updateRoute();
  } catch (error) {
    els.submitButton.disabled = false;
    els.detailSubmitButton.disabled = false;
    els.submitButton.textContent = "Indienen";
    els.basketStatus.textContent = "Indienen mislukt";
    showServerError(error);
  }
}

function renderAll() {
  renderExploitations();
  renderEditor();
  renderBasket();
  renderSubmissionList();
  renderSubmissionDetail();
  renderReports();
}

function renderExploitations() {
  const draftExploitations = exploitations
    .filter((item) => item.draftReportId && !item.latestEffectiveFrom)
    .sort((a, b) => String(b.draftUpdatedAt || "").localeCompare(String(a.draftUpdatedAt || "")));
  const registeredExploitations = exploitations.filter((item) => item.latestEffectiveFrom);
  els.draftExploitationsSection.hidden = !draftExploitations.length;
  els.draftExploitationItems.innerHTML = draftExploitations.map(exploitationCardMarkup).join("");
  els.exploitationItems.innerHTML = registeredExploitations.map(exploitationCardMarkup).join("")
    || "<p>Nog geen geregistreerde exploitaties.</p>";
  renderExploitationMap([...draftExploitations, ...registeredExploitations]);
}

function renderExploitationMap(items) {
  const mapItems = items
    .map((item) => ({ item, coordinates: exploitationLatLng(item) }))
    .filter((entry) => entry.coordinates);

  els.exploitationMapEmpty.hidden = mapItems.length > 0;
  if (!window.L || !els.exploitationMap) {
    els.exploitationMapEmpty.hidden = false;
    els.exploitationMapEmpty.textContent = "De kaartbibliotheek kon niet worden geladen.";
    return;
  }

  if (!exploitationMap) {
    exploitationMap = L.map(els.exploitationMap, {
      scrollWheelZoom: false,
    }).setView([50.9, 4.35], 8);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(exploitationMap);
    exploitationMapMarkers = L.layerGroup().addTo(exploitationMap);
  }

  exploitationMapMarkers.clearLayers();
  if (!mapItems.length) {
    exploitationMapBounds = null;
    exploitationMap.setView([50.9, 4.35], 8);
    return;
  }

  const bounds = [];
  mapItems.forEach(({ item, coordinates }) => {
    const marker = L.marker(coordinates).bindPopup(exploitationPopupMarkup(item));
    marker.addTo(exploitationMapMarkers);
    bounds.push(coordinates);
  });
  exploitationMapBounds = bounds;
  syncExploitationMapViewport();
}

function syncExploitationMapViewport() {
  if (!exploitationMap || els.exploitationsView.hidden) return;
  window.setTimeout(() => {
    exploitationMap.invalidateSize();
    if (exploitationMapBounds?.length) {
      exploitationMap.fitBounds(exploitationMapBounds, { maxZoom: 13, padding: [26, 26] });
    } else {
      exploitationMap.setView([50.9, 4.35], 8);
    }
  }, 0);
}

function exploitationLatLng(item) {
  const coordinates = item.location?.lambert2008 || {};
  if (coordinates.x == null || coordinates.y == null) return null;
  if (!window.proj4) return null;
  proj4.defs("EPSG:3812", "+proj=lcc +lat_0=50.797815 +lon_0=4.35921583333333 +lat_1=49.8333339 +lat_2=51.1666672333333 +x_0=649328 +y_0=665262 +ellps=GRS80 +units=m +no_defs +type=crs");
  const [lng, lat] = proj4("EPSG:3812", "EPSG:4326", [Number(coordinates.x), Number(coordinates.y)]);
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null;
  return [lat, lng];
}

function exploitationPopupMarkup(item) {
  const address = exploitationLocationText(item);
  return `
    <div class="map-popup">
      <strong>${escapeHtml(item.exploitatie)}</strong>
      ${address ? `<span>${escapeHtml(address)}</span>` : ""}
      <small>${escapeHtml(item.exploitatieId || "")}</small>
      <button class="secondary map-popup-action" type="button"
        data-exploitation-id="${escapeHtml(item.exploitatieId || "")}"
        data-draft-transaction-id="${escapeHtml(item.draftTransactionId || "")}"
        data-draft-report-id="${escapeHtml(item.draftReportId || "")}">
        Openen
      </button>
    </div>`;
}

function exploitationLocationText(item) {
  const address = item.location?.address || {};
  const street = [address.street, address.houseNumber].filter(Boolean).join(" ");
  const municipality = [address.postalCode, address.municipality].filter(Boolean).join(" ");
  const formattedAddress = [street, municipality].filter(Boolean).join(", ");
  const coordinates = item.location?.lambert2008 || {};
  const formattedCoordinates = coordinates.x != null && coordinates.y != null
    ? `Lambert 2008 X-Y: ${coordinates.x} - ${coordinates.y}`
    : "";
  return formattedAddress || formattedCoordinates;
}

function exploitationCardMarkup(item) {
  const locationText = exploitationLocationText(item);
  return `
    <div class="exploitation-card">
      <button class="exploitation-card-main" type="button"
        data-exploitation-id="${escapeHtml(item.exploitatieId || "")}"
        data-draft-transaction-id="${escapeHtml(item.draftTransactionId || "")}"
        data-draft-report-id="${escapeHtml(item.draftReportId || "")}">
      <span>
        <strong>${escapeHtml(item.exploitatie)}</strong>
        ${locationText ? `<span>${escapeHtml(locationText)}</span>` : ""}
        <small>${escapeHtml(item.exploitatieId || "")}</small>
        ${item.draftReportId && !item.latestEffectiveFrom
          ? '<span class="unsaved-changes-label">Nog niet ingediend</span>'
          : ""}
        ${item.latestEffectiveFrom && item.draftReportId
          ? '<span class="unsaved-changes-label">Niet-ingediende wijzigingen</span>'
          : ""}
      </span>
      </button>
    </div>`;
}

function closeExploitationRegistration() {
  els.exploitationRegistration.hidden = true;
  els.exploitationValidation.hidden = true;
  els.exploitationForm.reset();
}

async function registerFirstState(event) {
  event.preventDefault();
  const form = new FormData(els.exploitationForm);
  const payload = Object.fromEntries(form.entries());
  els.exploitationValidation.hidden = true;
  try {
    const result = await request(`${API}/exploitations`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    editor = result.editor;
    activeExploitationId = editor.exploitatieId;
    selectedEditorPart = "exploitation";
    selectedObjectIndex = 0;
    exploitations = await request(`${API}/exploitations`);
    closeExploitationRegistration();
    renderAll();
  } catch (error) {
    els.exploitationValidation.textContent = error.message;
    els.exploitationValidation.hidden = false;
  }
}

function isNewExploitationDraft() {
  return Boolean(editor?.exploitatieId)
    && reports.every((report) => report.exploitatieId !== editor.exploitatieId);
}

function renderReports() {
  const registeredReports = visibleReports();
  const hasHiddenReports = registeredReports.some((report) => report.replacedByReportId || report.withdrawnByTransactionId);
  const displayedReports = timelineReports();
  const draft = draftReport();
  const hasActiveDraft = editor?.exploitatieId === activeExploitationId;
  if (!showReplacedReports && (selectedReport?.replacedByReportId || selectedReport?.withdrawnByTransactionId)) {
    selectedReport = hasActiveDraft ? draft : (displayedReports[0] || null);
  }
  const draftSelected = Boolean(selectedReport?.isDraft && hasActiveDraft);
  const exploitationContext = exploitations.find((item) => item.exploitatieId === activeExploitationId)
    || registeredReports[0]
    || (hasActiveDraft ? editor : null);
  const simplifiedDraftOnly = hasActiveDraft && registeredReports.length === 0;
  const isDraftOnlyExploitation = Boolean(exploitationContext?.draftReportId && !exploitationContext?.latestEffectiveFrom);
  const hasUnsubmittedChanges = Boolean(exploitationContext?.draftReportId && exploitationContext?.latestEffectiveFrom);
  els.draftReportEntry.hidden = !hasActiveDraft;
  els.replacedReportsToggle.hidden = simplifiedDraftOnly || !hasHiddenReports;
  els.showReplacedReports.checked = showReplacedReports;
  els.reportsContextToolbar.hidden = simplifiedDraftOnly;
  els.reportsSectionTitle.hidden = simplifiedDraftOnly;
  els.reportsViewSwitch.hidden = simplifiedDraftOnly;
  els.reportsList.hidden = simplifiedDraftOnly;
  els.reportsTimelineView.classList.toggle("single-detail", simplifiedDraftOnly);
  els.previousReport.hidden = simplifiedDraftOnly;
  els.newerReport.hidden = simplifiedDraftOnly;
  els.draftWarningText.textContent = simplifiedDraftOnly
    ? "Deze registratie is nog niet ingediend."
    : "Deze toestand is nog niet ingediend.";
  els.deleteDraftReport.textContent = simplifiedDraftOnly
    ? "Annuleren en verwijderen"
    : "Toestand verwijderen";
  els.reportsExploitationName.textContent = exploitationContext?.exploitatie || "Exploitatie";
  els.reportsExploitationId.textContent = exploitationContext?.exploitatieId || "";
  const contextAddress = exploitationContext?.location?.address || {};
  const contextStreet = [contextAddress.street, contextAddress.houseNumber].filter(Boolean).join(" ");
  const contextMunicipality = [contextAddress.postalCode, contextAddress.municipality].filter(Boolean).join(" ");
  const contextFormattedAddress = [contextStreet, contextMunicipality].filter(Boolean).join(", ");
  const contextCoordinates = exploitationContext?.location?.lambert2008 || {};
  els.reportsExploitationLocation.textContent = contextFormattedAddress || (
    contextCoordinates.x != null && contextCoordinates.y != null
      ? `Lambert 2008 X-Y: ${contextCoordinates.x} - ${contextCoordinates.y}`
      : ""
  );
  els.reportsExploitationContext.classList.toggle("draft-only", isDraftOnlyExploitation);
  els.reportsExploitationStatus.hidden = !isDraftOnlyExploitation && !hasUnsubmittedChanges;
  els.reportsExploitationStatus.textContent = isDraftOnlyExploitation
    ? "Nog niet ingediend"
    : (hasUnsubmittedChanges ? "Niet-ingediende wijzigingen" : "");
  els.draftReportEntry.classList.toggle("selected", draftSelected);
  els.reportItems.innerHTML = displayedReports.length
    ? displayedReports.map((report, index) => {
      const selected = report.reportId === selectedReport?.reportId;
      const newerReport = displayedReports
        .slice(0, index)
        .find((item) => item.effectiveFrom !== report.effectiveFrom) || null;
      const range = formatReportRange(report.effectiveFrom, newerReport?.effectiveFrom);
      return `
        <li class="timeline-step">
          <button class="timeline-entry${selected ? " selected" : ""}${report.replacedByReportId ? " replaced" : ""}${report.withdrawnByTransactionId ? " withdrawn" : ""}" type="button"
            data-report-id="${escapeHtml(report.reportId)}"
            aria-label="${escapeHtml(`${range} — ${report.title}`)}">
            <span class="timeline-marker" aria-hidden="true"></span>
            <span class="timeline-range">
              <time datetime="${escapeHtml(report.effectiveFrom || "")}">${escapeHtml(range)}</time>
              ${report.replacedByReportId ? "<small>Vervangen</small>" : ""}
              ${report.withdrawnByTransactionId ? "<small>Ingetrokken</small>" : ""}
              ${report.correctionDraft ? "<small>Correctie in opmaak</small>" : ""}
              ${report.followUpDraft ? "<small>Nieuwe toestand in opmaak</small>" : ""}
            </span>
          </button>
        </li>`;
    }).join("")
    : '<li class="timeline-empty">Er zijn geen geregistreerde toestanden zichtbaar.</li>';
  const report = selectedReport;
  els.openSourceSubmission.hidden = !report || draftSelected;
  els.draftReportActions.hidden = !draftSelected;
  els.draftWarning.hidden = !draftSelected;
  els.registeredReportActions.hidden = draftSelected;
  if (!report) {
    els.reportDetailTitle.textContent = "Nog geen ingediende exploitatietoestanden";
    els.previousReport.disabled = true;
    els.newerReport.disabled = true;
    els.reportSubmittedDate.textContent = "";
    els.reportEffectiveDate.innerHTML = "";
    els.reportMetadata.innerHTML = "";
    els.reportObjectList.innerHTML = "";
    els.reportReplacementNotices.hidden = true;
    els.registeredReportActions.hidden = true;
    return;
  }
  const selectedIndex = displayedReports.findIndex((item) => item.reportId === report.reportId);
  const newerReport = displayedReports
    .slice(0, selectedIndex)
    .find((item) => item.effectiveFrom !== report.effectiveFrom) || null;
  const hasDraftNavigation = hasActiveDraft && !draftSelected;
  const hasMultipleStates = displayedReports.length > 1 || hasDraftNavigation;
  const hasPreviousReport = draftSelected
    ? displayedReports.length > 0
    : selectedIndex >= 0 && selectedIndex < displayedReports.length - 1;
  const hasNewerReport = !draftSelected && (selectedIndex > 0 || hasDraftNavigation);
  els.previousReport.hidden = !hasMultipleStates;
  els.newerReport.hidden = !hasMultipleStates;
  els.reportDetailTitle.textContent = draftSelected
    ? (simplifiedDraftOnly
        ? "Registratieformulier: nieuwe exploitatie"
        : report.changeType === "correction"
          ? "Correctie in opmaak"
          : report.changeType === "new-state"
            ? "Nieuwe toestand in opmaak"
            : "Toestand in opmaak")
    : formatReportRangeWords(report.effectiveFrom, newerReport?.effectiveFrom);
  els.previousReport.disabled = !hasPreviousReport;
  els.newerReport.disabled = !hasNewerReport;
  els.reportSubmittedDate.textContent = draftSelected
    ? `Laatst gewijzigd op ${formatDate(report.updatedAt)}`
    : `Ingediend op ${formatDate(report.submittedAt)}`;
  els.reportSubmittedDate.closest(".submission-reference").hidden = simplifiedDraftOnly;
  els.reportEffectiveDate.innerHTML = [
    [simplifiedDraftOnly ? "Exploitatie sinds" : "Toestand sinds", formatDateOnly(report.effectiveFrom)],
  ].map(propertyMarkup).join("");
  const address = report.location?.address || {};
  const coordinates = report.location?.lambert2008 || {};
  const formattedAddress = `${address.street || ""} ${address.houseNumber || ""}, ${address.postalCode || ""} ${address.municipality || ""}`.trim();
  els.reportMetadata.innerHTML = [
    ["Naam van de exploitatie", report.exploitatie],
    ["NACE-BEL-code", report.naceBelCode || "23.990"],
    ...(formattedAddress ? [["Adres", formattedAddress]] : []),
    ["Lambert 2008 X-Y", `${coordinates.x || "—"} - ${coordinates.y || "—"}`],
    ["Wijziging", draftSelected
      ? (simplifiedDraftOnly
          ? "Registratiegegevens, nog niet ingediend"
          : report.changeType === "correction"
            ? "Correctie van een geregistreerde toestand, nog niet ingediend"
            : report.changeType === "new-state"
              ? "Nieuwe toestand op het terrein, nog niet ingediend"
              : "Conceptwijzigingen, nog niet ingediend")
      : (report.changeSummary || "Initiële toestand")],
  ].map(propertyMarkup).join("");
  els.reportObjectList.innerHTML = report.objects.length
    ? report.objects.map((item) => `
      <div class="report-object">
        <span class="report-object-content">
          <strong>${escapeHtml(item.type)}: ${escapeHtml(item.name)} <span class="report-object-id">(${escapeHtml(item.code)})</span></strong>
          <small>${escapeHtml(item.status)}${item.properties ? ` · ${escapeHtml(item.properties)}` : ""}</small>
        </span>
      </div>`).join("")
    : '<p class="editor-empty">Er zijn geen rapporteringsplichtige onderdelen toegevoegd.</p>';
  renderReplacementNotices(report, draftSelected);
  const reportNoLongerValid = Boolean(report.replacedByReportId || report.withdrawnByTransactionId);
  els.correctReport.hidden = draftSelected || Boolean(reportNoLongerValid || report.correctionDraft || report.followUpDraft);
  els.newStateFromReport.hidden = draftSelected || Boolean(reportNoLongerValid || report.followUpDraft || report.correctionDraft);
  els.withdrawReport.hidden = draftSelected || Boolean(reportNoLongerValid || report.correctionDraft || report.followUpDraft);
  renderReportDiff();
  renderReportDisplayMode();
  if (currentView === "editor") {
    els.reportsViewSwitch.hidden = false;
    els.reportsEditMode.hidden = false;
    els.reportsSectionTitle.hidden = true;
    els.reportsContactContext.hidden = true;
    els.reportsModeToggle.hidden = true;
    els.reportsTimelineView.hidden = true;
    els.reportsDiffView.hidden = true;
  }
}

function renderReplacementNotices(report, draftSelected) {
  const notices = [];
  if (draftSelected && report.changeType === "correction" && report.replacesReportId) {
    notices.push(`
      <div class="replacement-notice pending">
        <strong>Deze correctie dient ter vervanging van een geregistreerde toestand.</strong>
        <button class="text-link" type="button" data-related-report-id="${escapeHtml(report.replacesReportId)}">Originele toestand bekijken</button>
      </div>`);
  }
  if (draftSelected && report.changeType === "new-state" && report.basedOnReportId) {
    notices.push(`
      <div class="replacement-notice pending">
        <strong>Deze nieuwe toestand is gebaseerd op een eerdere geregistreerde toestand.</strong>
        <button class="text-link" type="button" data-related-report-id="${escapeHtml(report.basedOnReportId)}">Basistoestand bekijken</button>
      </div>`);
  }
  if (!draftSelected && report.replacedByReportId) {
    notices.push(`
      <div class="replacement-notice replaced">
        <strong>Deze toestand is vervangen en is niet meer geldig.</strong>
        <button class="text-link" type="button" data-related-report-id="${escapeHtml(report.replacedByReportId)}">Vervangende toestand bekijken</button>
      </div>`);
  } else if (!draftSelected && report.withdrawnByTransactionId) {
    notices.push(`
      <div class="replacement-notice withdrawn">
        <strong>Deze toestand is ingetrokken en is niet meer geldig.</strong>
        <button class="text-link" type="button" data-related-submission-id="${escapeHtml(report.withdrawnByTransactionId)}">Intrekking bekijken</button>
      </div>`);
  } else if (!draftSelected && report.correctionDraft) {
    notices.push(`
      <div class="replacement-notice pending">
        <strong>Voor deze toestand wordt een correctie opgemaakt.</strong>
        <button class="text-link" type="button" data-related-draft-id="${escapeHtml(report.correctionDraft.reportDraftId)}">Correctie in opmaak bekijken</button>
      </div>`);
  } else if (!draftSelected && report.followUpDraft) {
    notices.push(`
      <div class="replacement-notice pending">
        <strong>Op basis van deze registratie wordt een nieuwe toestand opgemaakt.</strong>
        <button class="text-link" type="button" data-related-draft-id="${escapeHtml(report.followUpDraft.reportDraftId)}">Nieuwe toestand in opmaak bekijken</button>
      </div>`);
  }
  if (!draftSelected && report.replacesReportId) {
    notices.push(`
      <div class="replacement-notice">
        <span>Deze toestand vervangt een eerdere geregistreerde toestand.</span>
        <button class="text-link" type="button" data-related-report-id="${escapeHtml(report.replacesReportId)}">Vervangen toestand bekijken</button>
      </div>`);
  }
  els.reportReplacementNotices.innerHTML = notices.join("");
  els.reportReplacementNotices.hidden = !notices.length;
}

async function createDerivedDraft(changeType) {
  if (!selectedReport || selectedReport.isDraft) return;
  try {
    const action = changeType === "correction" ? "correction" : "new-state";
    editor = await request(`${API}/reports/${encodeURIComponent(selectedReport.reportId)}/${action}`, {
      method: "POST",
    });
    currentDraft = null;
    activeExploitationId = editor.exploitatieId;
    [reports, exploitations] = await Promise.all([
      request(`${API}/reports`),
      request(`${API}/exploitations`),
    ]);
    selectedReport = draftReport();
    syncPreviewRows();
    renderAll();
    showView("editor");
  } catch (error) {
    showServerError(error);
  }
}

async function openRelatedReport(event) {
  const button = event.target.closest("[data-related-report-id], [data-related-draft-id], [data-related-submission-id]");
  if (!button) return;
  if (button.dataset.relatedReportId) {
    const target = reports.find((item) => item.reportId === button.dataset.relatedReportId);
    if (!target) return;
    if (target.replacedByReportId || target.withdrawnByTransactionId) showReplacedReports = true;
    selectedReport = target;
    renderReports();
    updateRoute();
    return;
  }
  if (button.dataset.relatedSubmissionId) {
    try {
      selectedItem = submissions.find((item) => item.transactionId === button.dataset.relatedSubmissionId)
        || await request(`${API}/submissions/${encodeURIComponent(button.dataset.relatedSubmissionId)}`);
      openSubmissionModal(selectedItem);
    } catch (error) {
      showServerError(error);
    }
    return;
  }
  try {
    editor = await request(`${API}/draft-reports/${encodeURIComponent(button.dataset.relatedDraftId)}`);
    currentDraft = null;
    selectedReport = draftReport();
    syncPreviewRows();
    renderReports();
    updateRoute();
  } catch (error) {
    showServerError(error);
  }
}

function visibleReports() {
  return activeExploitationId
    ? reports.filter((report) => report.exploitatieId === activeExploitationId)
    : reports;
}

function timelineReports() {
  const registered = visibleReports();
  return showReplacedReports
    ? registered
    : registered.filter((report) => !report.replacedByReportId && !report.withdrawnByTransactionId);
}

function setReportDisplayMode(mode) {
  reportDisplayMode = mode;
  if (currentView === "editor") {
    showView("reports");
    return;
  }
  renderReportDisplayMode();
  updateRoute();
}

function renderReportDisplayMode() {
  if (currentView === "editor") {
    els.reportsTimelineView.hidden = true;
    els.reportsDiffView.hidden = true;
    return;
  }
  const showDiff = reportDisplayMode === "diff";
  els.reportsTimelineView.hidden = showDiff;
  els.reportsDiffView.hidden = !showDiff;
  els.showReportTimeline.classList.toggle("active", !showDiff);
  els.showReportTimeline.classList.toggle("secondary", !showDiff);
  els.showReportTimeline.classList.toggle("ghost", showDiff);
  els.showReportDiff.classList.toggle("active", showDiff);
  els.showReportDiff.classList.toggle("secondary", showDiff);
  els.showReportDiff.classList.toggle("ghost", !showDiff);
  els.showReportTimeline.setAttribute("aria-pressed", String(!showDiff));
  els.showReportDiff.setAttribute("aria-pressed", String(showDiff));
}

function comparableReportStates() {
  const uniqueDates = new Set();
  const registered = [...visibleReports()]
    .sort((a, b) => String(a.effectiveFrom).localeCompare(String(b.effectiveFrom)))
    .filter((report) => {
      const key = report.effectiveFrom || report.reportId;
      if (uniqueDates.has(key)) return false;
      uniqueDates.add(key);
      return true;
    })
    .map((report) => ({
      ...report,
      label: formatDateOnly(report.effectiveFrom),
    }));
  if (editor?.exploitatieId === activeExploitationId) registered.push({ ...draftReport(), label: "In opmaak" });
  return registered;
}

function objectSignature(item) {
  return JSON.stringify({
    type: item?.type || "",
    name: item?.name || "",
    status: item?.status || "",
    properties: item?.properties || "",
    relations: [...(item?.relations || [])].sort(),
  });
}

function objectChanges(previous, current) {
  if (!previous && current) return { status: "added", label: "Toegevoegd", details: ["Object toegevoegd"] };
  if (previous && !current) return { status: "removed", label: "Verwijderd", details: ["Object verwijderd"] };
  if (!previous && !current) return { status: "unchanged", label: "—", details: [] };
  if (objectSignature(previous) === objectSignature(current)) {
    return { status: "unchanged", label: "—", details: [] };
  }
  const fields = [
    ["Type", previous.type, current.type],
    ["Naam", previous.name, current.name],
    ["Status", previous.status, current.status],
    ["Eigenschappen", previous.properties, current.properties],
    ["Relaties", (previous.relations || []).join(", "), (current.relations || []).join(", ")],
  ];
  return {
    status: "changed",
    label: "Gewijzigd",
    details: fields
      .filter(([, before, after]) => String(before || "") !== String(after || ""))
      .map(([name, before, after]) => `${name}: ${before || "—"} → ${after || "—"}`),
  };
}

function exploitationDetails(state) {
  const address = state?.location?.address || {};
  const coordinates = state?.location?.lambert2008 || {};
  const addressText = [address.street, address.houseNumber].filter(Boolean).join(" ");
  const municipalityText = [address.postalCode, address.municipality].filter(Boolean).join(" ");
  return {
    "Naam": state?.exploitatie || "",
    "Exploitatie-ID": state?.exploitatieId || "",
    "NACE-BEL-code": state?.naceBelCode || "",
    "Adres": [addressText, municipalityText].filter(Boolean).join(", "),
    "Lambert 2008 X-Y": coordinates.x != null && coordinates.y != null
      ? `${coordinates.x} - ${coordinates.y}`
      : "",
  };
}

function propertyChanges(previous, current, firstLabel = "Vastgelegd") {
  if (!previous) {
    return {
      status: "added",
      label: firstLabel,
      details: Object.entries(current)
        .filter(([, value]) => String(value || ""))
        .map(([name, value]) => `${name}: ${value}`),
    };
  }
  const details = Object.keys(current)
    .filter((name) => String(previous[name] || "") !== String(current[name] || ""))
    .map((name) => `${name}: ${previous[name] || "—"} → ${current[name] || "—"}`);
  return {
    status: details.length ? "changed" : "unchanged",
    label: details.length ? "Gewijzigd" : "—",
    details,
  };
}

function diffSummaryRow(label, states, valuesForState) {
  let previous = null;
  const cells = states.map((state) => {
    const current = valuesForState(state);
    const change = propertyChanges(previous, current);
    const details = [label, `${state.label}: ${change.label}`, ...change.details].join("\n");
    previous = current;
    return `
      <td${state.isDraft ? ' class="draft-column"' : ""}>
        <button class="diff-cell ${change.status}" type="button"
          data-diff-details="${escapeHtml(details)}"
          ${change.details.length ? "" : "disabled"}>
          ${escapeHtml(change.label)}
        </button>
      </td>`;
  }).join("");
  return `
    <tr class="diff-summary-row">
      <th class="diff-object" scope="row"><strong>${escapeHtml(label)}</strong></th>
      ${cells}
    </tr>`;
}

function renderReportDiff() {
  const states = comparableReportStates();
  const objectsByCode = new Map();
  states.forEach((state) => {
    (state.objects || []).forEach((item) => {
      if (!objectsByCode.has(item.code)) objectsByCode.set(item.code, item);
    });
  });
  const headers = states.map((state) => `
    <th${state.isDraft ? ' class="draft-column"' : ""}>${escapeHtml(state.label)}</th>`).join("");
  const summaryRows = diffSummaryRow("Exploitatiegegevens", states, exploitationDetails);
  const objectRows = [...objectsByCode.entries()].map(([code, example]) => {
    let previous = null;
    const cells = states.map((state, index) => {
      const current = (state.objects || []).find((item) => item.code === code) || null;
      const change = objectChanges(previous, current);
      const details = [
        `${example.type}: ${example.name} (${code})`,
        `${state.label}: ${change.label}`,
        ...change.details,
      ].join("\n");
      const cell = `
        <td${state.isDraft ? ' class="draft-column"' : ""}>
          <button class="diff-cell ${change.status}" type="button"
            data-diff-details="${escapeHtml(details)}"
            ${change.details.length ? "" : "disabled"}>
            ${escapeHtml(change.label)}
          </button>
        </td>`;
      previous = current;
      return cell;
    }).join("");
    return `
      <tr>
        <th class="diff-object" scope="row">
          <strong>${escapeHtml(example.type)}: ${escapeHtml(example.name)}</strong>
          <small>(${escapeHtml(code)})</small>
        </th>
        ${cells}
      </tr>`;
  }).join("");
  els.reportDiffTable.innerHTML = `
    <thead><tr><th class="diff-object">Element</th>${headers}</tr></thead>
    <tbody>${summaryRows}${objectRows}</tbody>`;
}

function openDiffDetails(details) {
  els.modalEyebrow.textContent = "Verschil met vorige toestand";
  els.modalTitle.textContent = details.split("\n")[0];
  els.receiptPreview.textContent = details.split("\n").slice(1).join("\n");
  els.previewTable.hidden = true;
  els.schemaPreview.hidden = true;
  els.submissionModalDetail.hidden = true;
  els.receiptPreview.hidden = false;
  els.modal.hidden = false;
}

function openWithdrawalModal() {
  if (!selectedReport || selectedReport.isDraft) return;
  const range = formatReportRangeWords(selectedReport.effectiveFrom);
  els.modalEyebrow.textContent = "Intrekking";
  els.modalTitle.textContent = "Registratie intrekken";
  els.submissionModalDetail.innerHTML = `
    <aside class="draft-warning withdrawal-warning" role="note">
      <strong>U trekt deze geregistreerde toestand formeel in.</strong>
      <p>Er wordt geen vervangende toestand geregistreerd. De intrekking wordt meteen ingediend met uw motivatie.</p>
    </aside>
    <dl class="properties section-data withdrawal-summary">
      ${[
        ["Exploitatie", [selectedReport.exploitatie, selectedReport.exploitatieId].filter(Boolean).join(" - ")],
        ["Toestand", range],
        ["Oorspronkelijke indiening", selectedReport.transactionId || "—"],
      ].map(propertyMarkup).join("")}
    </dl>
    <form class="withdrawal-form" id="withdrawal-form">
      <label>Motivatie
        <textarea name="reason" rows="5" required placeholder="Waarom wordt deze registratie ingetrokken?"></textarea>
      </label>
      <p class="validation-summary" id="withdrawal-validation" hidden></p>
      <div class="editor-form-actions">
        <button class="ghost" type="button" data-modal-action="cancel-withdrawal">Annuleren</button>
        <button class="primary" type="submit">Intrekking indienen</button>
      </div>
    </form>`;
  els.previewTable.hidden = true;
  els.receiptPreview.hidden = true;
  els.schemaPreview.hidden = true;
  els.submissionModalDetail.hidden = false;
  els.modal.hidden = false;
}

async function submitWithdrawal(event) {
  const form = event.target.closest("#withdrawal-form");
  if (!form) return;
  event.preventDefault();
  const reason = new FormData(form).get("reason").trim();
  const validation = form.querySelector("#withdrawal-validation");
  if (!reason) {
    validation.textContent = "Vul een motivatie in voor de intrekking.";
    validation.hidden = false;
    return;
  }
  const submitButton = form.querySelector('button[type="submit"]');
  submitButton.disabled = true;
  submitButton.textContent = "Wordt ingediend...";
  try {
    const received = await request(`${API}/reports/${encodeURIComponent(selectedReport.reportId)}/withdraw`, {
      method: "POST",
      body: JSON.stringify({ reason }),
    });
    submissions = [received, ...submissions.filter((item) => item.transactionId !== received.transactionId)];
    [reports, exploitations] = await Promise.all([
      request(`${API}/reports`),
      request(`${API}/exploitations`),
    ]);
    selectedReport = reports.find((report) => report.reportId === received.targetReportId) || selectedReport;
    selectedItem = received;
    closeModal();
    renderAll();
    await showView("submissions");
  } catch (error) {
    validation.textContent = error.message;
    validation.hidden = false;
    submitButton.disabled = false;
    submitButton.textContent = "Intrekking indienen";
  }
}

function openSubmissionModal(item) {
  if (!item) return;
  selectedItem = item;
  renderSubmissionDetail();
  els.modalEyebrow.textContent = "Indiening";
  els.modalTitle.textContent = item.displayName || "Exploitatietoestand";
  const detailPanel = document.querySelector("#submissions-view .submission-detail");
  const clone = detailPanel.cloneNode(true);
  clone.querySelectorAll("[id]").forEach((element) => {
    element.dataset.modalAction = element.id;
    element.removeAttribute("id");
  });
  els.submissionModalDetail.replaceChildren(...clone.childNodes);
  els.previewTable.hidden = true;
  els.receiptPreview.hidden = true;
  els.schemaPreview.hidden = true;
  els.submissionModalDetail.hidden = false;
  els.modal.hidden = false;
}

function draftReport() {
  const newExploitation = isNewExploitationDraft();
  return {
    isDraft: true,
    reportId: editor?.reportDraftId || "draft",
    title: newExploitation ? "Registratie nieuwe exploitatie" : (editor?.title || "Toestand in opmaak"),
    exploitatie: editor?.exploitatie || currentDraft?.exploitatie,
    exploitatieId: editor?.exploitatieId || currentDraft?.exploitatieId,
    effectiveFrom: editor?.effectiveFrom,
    naceBelCode: editor?.naceBelCode || "23.990",
    location: editor?.location,
    objects: editor?.objects || [],
    updatedAt: editor?.updatedAt || currentDraft?.reportUpdatedAt || currentDraft?.createdAt,
    replacesReportId: editor?.replacesReportId,
    replacesTransactionId: editor?.replacesTransactionId,
    basedOnReportId: editor?.basedOnReportId,
    basedOnTransactionId: editor?.basedOnTransactionId,
    changeType: editor?.changeType,
  };
}

function renderBasket() {
  const hasDraft = Boolean(currentDraft);
  els.basketEmptyMessage.hidden = hasDraft;
  els.basketTransactionSection.hidden = !hasDraft;
  els.basketContentSection.hidden = !hasDraft;
  els.basketFilesSection.hidden = !hasDraft;
  els.submitButton.hidden = !hasDraft;
  els.receiptEmpty.hidden = !hasDraft;
  els.receiptBody.hidden = true;
  els.receiptActions.hidden = true;
  els.receiptDownload.removeAttribute("href");
  els.stepSubmit.classList.remove("active");
  els.stepReceipt.classList.remove("active");
  if (!hasDraft) {
    els.basketTitle.textContent = "Geen indiening klaargezet";
    els.basketStatus.textContent = "";
    els.basketStatus.classList.remove("sent");
    els.submitButton.disabled = true;
    els.submitButton.textContent = "Indienen";
    return;
  }
  els.transactionId.textContent = currentDraft.transactionId;
  els.contentHash.textContent = `sha256:${currentDraft.contentHash}`;
  els.basketExploitation.textContent = [currentDraft.exploitatie, currentDraft.exploitatieId]
    .filter(Boolean)
    .join(" - ");
  els.basketNaceBelCode.textContent = currentDraft.naceBelCode || "—";
  els.basketTitle.textContent = "Klaar om in te dienen";
  els.basketStatus.textContent = "Klaar voor indiening";
  els.basketStatus.classList.remove("sent");
  els.submitButton.disabled = false;
  els.submitButton.textContent = "Indienen";
  els.draftDownload.href = `${API}/draft-submissions/${encodeURIComponent(currentDraft.transactionId)}/file`;
  els.draftSchemaDownload.href = `${schemaUrl(currentDraft)}?download=1`;
}

function renderEditor() {
  if (!editor) return;
  const newExploitation = isNewExploitationDraft();
  els.editorHeadingTitle.textContent = newExploitation
    ? "Gegevens nieuwe exploitatie wijzigen"
    : editor.changeType === "correction"
      ? "Registratie corrigeren"
      : editor.changeType === "new-state"
        ? "Nieuwe toestand op het terrein registreren"
        : "Exploitatietoestand opmaken";
  els.editorHeadingDescription.textContent = newExploitation
    ? "Selecteer gegevens hieronder om ze in het rechter paneel aan te passen."
    : editor.changeType === "correction"
      ? "Corrigeer foutieve of onvolledige gegevens uit de geregistreerde toestand."
      : editor.changeType === "new-state"
        ? "Pas de gekopieerde toestand aan en kies de ingangsdatum van de wijziging op het terrein."
        : "Beheer de onderdelen van de exploitatie en hun onderlinge relaties.";
  els.editorDateFormTitle.textContent = newExploitation
    ? "Ingangsdatum van de exploitatie"
    : "Ingangsdatum van de toestand";
  const address = editor.location?.address || {};
  const coordinates = editor.location?.lambert2008 || {};
  for (const [name, value] of Object.entries({
    exploitatie: editor.exploitatie || "",
    exploitatieId: editor.exploitatieId || "",
    naceBelCode: editor.naceBelCode || "",
    street: address.street || "",
    houseNumber: address.houseNumber || "",
    postalCode: address.postalCode || "",
    municipality: address.municipality || "",
    lambertX: coordinates.x ?? "",
    lambertY: coordinates.y ?? "",
  })) {
    els.editorExploitationForm.elements[name].value = value;
  }
  updateExploitationFormActions();
  const editorStreet = [address.street, address.houseNumber].filter(Boolean).join(" ");
  const editorMunicipality = [address.postalCode, address.municipality].filter(Boolean).join(" ");
  const editorAddress = [editorStreet, editorMunicipality].filter(Boolean).join(", ") || "—";
  const editorCoordinates = coordinates.x != null && coordinates.y != null
    ? `${coordinates.x} - ${coordinates.y}`
    : "—";
  els.editorDateForm.elements.effectiveFrom.value = editor.effectiveFrom || "";
  updateDateFormActions();
  selectedObjectIndex = Math.min(selectedObjectIndex, Math.max(0, editor.objects.length - 1));
  els.editorObjectCount.textContent = newExploitation
    ? `${editor.objects.length} onderdeel${editor.objects.length === 1 ? "" : "delen"} bij deze exploitatie`
    : `${editor.objects.length} object${editor.objects.length === 1 ? "" : "en"} in deze toestand`;
  els.editorDateEntry.innerHTML = `
    <button class="editor-object editor-state-property${selectedEditorPart === "date" ? " selected" : ""}" type="button" data-editor-part="date">
      <span class="editor-object-main"><strong>${escapeHtml(formatDateOnly(editor.effectiveFrom))}</strong>
        <small>${newExploitation ? "Ingangsdatum van de exploitatie" : "Ingangsdatum van deze toestand"}</small>
      </span>
    </button>`;
  els.editorExploitationEntry.innerHTML = `
    <button class="editor-object editor-state-property${selectedEditorPart === "exploitation" ? " selected" : ""}" type="button" data-editor-part="exploitation">
      <span class="editor-object-main editor-exploitation-summary">
        <span><small>Naam</small><strong>${escapeHtml(editor.exploitatie || "Naamloze exploitatie")}</strong></span>
        <span><small>Adres</small>${escapeHtml(editorAddress)}</span>
        <span><small>Lambert 2008 X-Y</small>${escapeHtml(editorCoordinates)}</span>
        <span><small>NACE-BEL-code</small>${escapeHtml(editor.naceBelCode || "—")}</span>
        <span><small>Referentie</small>${escapeHtml(editor.exploitatieId || "—")}</span>
      </span>
    </button>`;
  els.editorObjectList.innerHTML = editor.objects.length ? editor.objects.map((item, index) => `
    <button class="editor-object${selectedEditorPart === "object" && index === selectedObjectIndex ? " selected" : ""}" type="button" data-object-index="${index}">
      <span class="editor-object-main"><strong>${escapeHtml(item.name)} <span class="editor-inline-code">(${escapeHtml(item.code)})</span></strong>
        <small>${escapeHtml(item.type)} · ${escapeHtml(item.relations.length ? item.relations.join(", ") : "geen relaties")}</small>
      </span>
      <span class="status${item.status === "In gebruik" ? " sent" : ""}">${escapeHtml(item.status)}</span>
    </button>`).join("") : '<p class="editor-empty">Er zijn geen rapporteringsplichtige onderdelen toegevoegd.</p>';
  els.editorDateForm.hidden = selectedEditorPart !== "date";
  els.editorExploitationForm.hidden = selectedEditorPart !== "exploitation";
  els.editorObjectDetail.hidden = selectedEditorPart !== "object";
  const item = editor.objects[selectedObjectIndex];
  els.editorForm.hidden = !item;
  if (!item) {
    els.editorFormTitle.textContent = "Voeg een object toe";
    els.applyObjectChanges.disabled = true;
    els.cancelObjectChanges.disabled = true;
    return;
  }
  els.editorFormTitle.textContent = item.name;
  for (const [name, value] of Object.entries({
    type: item.type,
    code: item.code,
    name: item.name,
    status: item.status,
    properties: item.properties,
    relations: item.relations.join(", "),
  })) {
    els.editorForm.elements[name].value = value;
  }
  updateObjectFormActions();
}

function syncPreviewRows() {
  if (!editor) return;
  odsRows = [
    ["Type", "Code", "Naam", "Eigenschappen", "Verbonden met", "Status"],
    ...editor.objects.map((item) => [
      item.type, item.code, item.name, item.properties,
      item.relations.join("; "), item.status,
    ]),
  ];
  renderPreviewTable();
}

function renderCompletedBasket(item) {
  els.transactionId.textContent = item.transactionId;
  els.contentHash.textContent = `sha256:${item.contentHash}`;
  els.basketTitle.textContent = "Indienen voltooid";
  els.basketStatus.textContent = item.status;
  els.submitButton.textContent = "Ingediend";
  els.submitButton.disabled = true;
  els.stepReceipt.classList.add("active");
  els.draftDownload.href = `${API}/submissions/${encodeURIComponent(item.transactionId)}/file`;
  els.draftSchemaDownload.href = `${schemaUrl(item)}?download=1`;
  renderReceipt(item);
}

function allListItems() {
  return currentDraft ? [currentDraft, ...submissions] : submissions;
}

function renderSubmissionList() {
  const items = allListItems();
  els.submissionItems.innerHTML = items
    .map((item) => {
      const selected = item.transactionId === selectedItem?.transactionId;
      const statusText = item.receivedAt
        ? `Ontvangen op ${formatDate(item.receivedAt)}`
        : "Nog niet ingediend";
      const statusClass = item.status === "Nog niet ingediend" ? "status" : "status sent";
      return `
        <button class="submission-row${selected ? " selected" : ""}" type="button"
          data-transaction-id="${escapeHtml(item.transactionId)}">
          <span class="submission-meta">
            <span class="${statusClass}">${escapeHtml(statusText)}</span>
          </span>
          <span class="submission-main">
            <strong>${escapeHtml(item.displayName)}</strong>
          </span>
        </button>`;
    })
    .join("");
}

function renderSubmissionDetail() {
  const item = selectedItem;
  if (!item) return;
  const isWithdrawal = item.submissionType === "withdrawal";
  els.submissionDetail.innerHTML = [
    ["Referentienummer", item.transactionId],
    ["Status", item.status],
    ["Tijdstip ingediend", item.submittedAt ? formatDate(item.submittedAt) : "Nog niet ingediend"],
    ["Tijdstip ontvangen", item.receivedAt ? formatDate(item.receivedAt) : "Nog niet ingediend"],
    ["Ingediend door", item.submittedAt ? (item.submitterName || "Emiel Jeurens") : "Nog niet ingediend"],
    ["Namens exploitant", item.exploitatie || item.organizationName || "Demo Exploitatie NV"],
  ]
    .map(propertyMarkup)
    .join("");

  els.submissionPayload.innerHTML = (isWithdrawal ? [
    ["Type indiening", "Intrekking geregistreerde toestand"],
    ["Intrekt toestand", item.summary || "Geregistreerde toestand"],
    ["Motivatie", item.withdrawalReason || "—"],
    ["Content hash", `sha256:${item.contentHash}`],
  ] : [
    ["Samenvatting", item.summary],
    ["NACE-BEL-code", item.naceBelCode || "23.990"],
    ["Content hash", `sha256:${item.contentHash}`],
  ])
    .map(propertyMarkup)
    .join("");

  const isDraft = item.status === "Nog niet ingediend";
  els.detailSubmitButton.hidden = !isDraft;
  els.detailSubmitButton.disabled = !isDraft;
  els.deleteDraftSubmission.hidden = !isDraft;
  els.receiptDocumentSection.hidden = !item.receiptAvailable;
  if (item.receiptAvailable) {
    els.detailReceiptDownload.href = receiptUrl(item);
  } else {
    els.detailReceiptDownload.removeAttribute("href");
  }
  els.receiptDocumentDescription.textContent = item.receivedAt
    ? `Tekstdocument · ontvangen op ${formatDate(item.receivedAt)}`
    : "Tekstdocument · bevestiging van ontvangst";
  els.previewButtonDetail.hidden = isWithdrawal;
  els.submissionFilesSection.hidden = isWithdrawal;
  els.submissionOdsRow.hidden = isWithdrawal;
  els.submissionSchemaRow.hidden = isWithdrawal;
  if (!isWithdrawal) {
    els.submissionFilesSection.hidden = false;
    els.submissionOdsRow.hidden = false;
    els.submissionSchemaRow.hidden = false;
  }
  updateDetailFileLink(item);
}

function updateDetailFileLink(item) {
  if (item.submissionType === "withdrawal") return;
  const link = document.querySelector("#submissions-view .submission-detail .file-actions a");
  if (!link) return;
  link.href = item.status === "Nog niet ingediend"
    ? `${API}/draft-submissions/${encodeURIComponent(item.transactionId)}/file`
    : `${API}/submissions/${encodeURIComponent(item.transactionId)}/file`;
  els.detailSchemaDownload.href = `${schemaUrl(item)}?download=1`;
}

function renderReceipt(item) {
  els.receiptEmpty.hidden = true;
  els.receiptBody.hidden = false;
  els.receiptActions.hidden = false;
  els.receiptDownload.href = receiptUrl(item);
  els.receiptBody.innerHTML = [
    ["Transactie-ID", item.transactionId],
    ["Status", item.status],
    ["Bestand", item.displayName],
    ["Content hash", `sha256:${item.contentHash}`],
    ["Ingediend door", item.submittedBy || "Emiel Jeurens namens Demo Exploitatie NV"],
    ["Tijdstip indiening", formatDate(item.submittedAt)],
    ["Tijdstip ontvangst", formatDate(item.receivedAt)],
    ["Kanaal", "IMJV2 loket prototype"],
  ]
    .map(propertyMarkup)
    .join("");
}

function receiptUrl(item, download = true) {
  const suffix = download ? "/download" : "";
  return `${API}/submissions/${encodeURIComponent(item.transactionId)}/receipt${suffix}`;
}

function routeFromLocation() {
  const params = new URLSearchParams(window.location.search);
  const view = routedViews.has(params.get("view")) ? params.get("view") : "exploitations";
  return {
    view,
    exploitatieId: params.get("exploitatie") || "",
    reportId: params.get("report") || "",
    transactionId: params.get("transaction") || "",
    mode: params.get("mode") === "diff" ? "diff" : "timeline",
    showReplaced: params.get("replaced") === "1",
  };
}

function routeUrl() {
  const url = new URL(window.location.href);
  const params = new URLSearchParams();
  params.set("view", currentView);
  if ((currentView === "reports" || currentView === "editor") && activeExploitationId) {
    params.set("exploitatie", activeExploitationId);
  }
  if (currentView === "reports") {
    if (selectedReport?.isDraft) {
      params.set("report", "draft");
    } else if (selectedReport?.reportId) {
      params.set("report", selectedReport.reportId);
    }
    if (reportDisplayMode === "diff") params.set("mode", "diff");
    if (showReplacedReports) params.set("replaced", "1");
  }
  if (currentView === "submissions" && selectedItem?.transactionId) {
    params.set("transaction", selectedItem.transactionId);
  }
  url.search = params.toString();
  return url;
}

function updateRoute({ replace = false } = {}) {
  if (applyingRoute) return;
  const url = routeUrl();
  const next = `${url.pathname}${url.search}${url.hash}`;
  const current = `${window.location.pathname}${window.location.search}${window.location.hash}`;
  if (next === current && !replace) return;
  const method = replace || next === current ? "replaceState" : "pushState";
  window.history[method]({ view: currentView }, "", url);
}

async function applyRouteFromLocation({ replace = false, skipReload = false } = {}) {
  const route = routeFromLocation();
  applyingRoute = true;
  try {
    reportDisplayMode = route.mode;
    showReplacedReports = route.showReplaced;
    if (route.exploitatieId && (route.view === "reports" || route.view === "editor")) {
      await activateExploitationRoute(route.exploitatieId);
    }
    if (route.view === "submissions" && route.transactionId) {
      selectedItem = allListItems().find((item) => item.transactionId === route.transactionId) || selectedItem;
    }
    if ((route.view === "reports" || route.view === "editor") && route.reportId) {
      selectRoutedReport(route.reportId);
    }
    await showView(route.view, { replaceRoute: true, skipReload });
  } finally {
    applyingRoute = false;
  }
  updateRoute({ replace });
}

async function activateExploitationRoute(exploitatieId) {
  activeExploitationId = exploitatieId;
  const exploitation = exploitations.find((item) => item.exploitatieId === exploitatieId);
  if (exploitation?.draftTransactionId) {
    [currentDraft, editor] = await Promise.all([
      request(`${API}/draft-submissions/${encodeURIComponent(exploitation.draftTransactionId)}`),
      request(`${API}/draft-submissions/${encodeURIComponent(exploitation.draftTransactionId)}/editor`),
    ]);
    selectedItem = currentDraft;
    syncPreviewRows();
    return;
  }
  if (exploitation?.draftReportId) {
    editor = await request(`${API}/draft-reports/${encodeURIComponent(exploitation.draftReportId)}`);
    currentDraft = null;
    syncPreviewRows();
    return;
  }
  currentDraft = null;
  editor = null;
}

function selectRoutedReport(reportId) {
  const hasActiveDraft = editor?.exploitatieId === activeExploitationId;
  if (reportId === "draft" && hasActiveDraft) {
    selectedReport = draftReport();
    return;
  }
  const report = reports.find((item) => item.reportId === reportId);
  if (!report) return;
  activeExploitationId = report.exploitatieId || activeExploitationId;
  if (report.replacedByReportId || report.withdrawnByTransactionId) showReplacedReports = true;
  selectedReport = report;
}

async function showView(view, { replaceRoute = false, skipReload = false } = {}) {
  try {
    await persistEditorSource();
    if (!skipReload) await reloadSourceData(view);
  } catch (error) {
    showServerError(error);
  }
  const showExploitations = view === "exploitations";
  const showEditor = view === "editor";
  const showSubmissions = view === "submissions";
  const showSubmit = view === "submit";
  const showReports = view === "reports";
  currentView = view;
  if (showEditor) {
    els.reportsView.insertBefore(els.editorView, els.reportsTimelineView);
  } else if (els.editorView.parentElement === els.reportsView) {
    els.submitView.before(els.editorView);
  }
  els.exploitationsView.hidden = !showExploitations;
  els.editorView.hidden = !showEditor;
  els.submitView.hidden = !showSubmit;
  els.submissionsView.hidden = !showSubmissions;
  els.reportsView.hidden = !showReports && !showEditor;
  els.mainNavigation.hidden = showEditor;
  els.tabExploitations.classList.toggle("active", showExploitations);
  els.tabEditor?.classList.toggle("active", showEditor);
  els.tabSubmit.classList.toggle("active", showSubmit);
  els.tabSubmissions.classList.toggle("active", showSubmissions);
  els.tabReports?.classList.toggle("active", showReports);
  renderAll();
  if (showExploitations && exploitationMap) {
    syncExploitationMapViewport();
  }
  els.reportsEditMode.hidden = !showEditor;
  els.reportsContactContext.hidden = showEditor;
  els.reportsContextToolbar.classList.toggle("edit-mode", showEditor);
  if (showEditor) {
    els.reportsViewSwitch.hidden = false;
    els.reportsSectionTitle.hidden = true;
    els.reportsModeToggle.hidden = true;
    els.reportsTimelineView.hidden = true;
    els.reportsDiffView.hidden = true;
  } else if (showReports) {
    els.reportsModeToggle.hidden = false;
    renderReportDisplayMode();
  }
  updateRoute({ replace: replaceRoute });
}

async function reloadSourceData(view) {
  if (view === "exploitations") {
    exploitations = await request(`${API}/exploitations`);
    return;
  }
  if (view === "submissions") {
    submissions = await request(`${API}/submissions`);
    if (currentDraft?.transactionId) {
      currentDraft = await request(`${API}/draft-submissions/${encodeURIComponent(currentDraft.transactionId)}`);
    }
    selectedItem = selectedItem?.status === "Nog niet ingediend" ? currentDraft : (
      submissions.find((item) => item.transactionId === selectedItem?.transactionId) || submissions[0] || currentDraft
    );
    return;
  }
  if (view === "reports") {
    [reports, exploitations] = await Promise.all([
      request(`${API}/reports`),
      request(`${API}/exploitations`),
    ]);
    if (editor?.reportDraftId) {
      editor = await request(`${API}/draft-reports/${encodeURIComponent(editor.reportDraftId)}`);
    }
    selectedReport = selectedReport?.isDraft ? draftReport() : (
      visibleReports().find((report) => report.reportId === selectedReport?.reportId) || visibleReports()[0] || null
    );
    return;
  }
  if (view === "editor" && editor?.reportDraftId) {
    editor = await request(`${API}/draft-reports/${encodeURIComponent(editor.reportDraftId)}`);
    syncPreviewRows();
  }
}

function renderPreviewTable() {
  const [headers, ...body] = odsRows;
  els.previewTable.innerHTML = `
    <thead><tr>${headers.map((header) => `<th>${escapeHtml(header)}</th>`).join("")}</tr></thead>
    <tbody>${body.map((row) => `<tr>${row.map((value) => `<td>${escapeHtml(value)}</td>`).join("")}</tr>`).join("")}</tbody>`;
}

function openSpreadsheetPreview() {
  els.modalEyebrow.textContent = "Preview spreadsheet";
  els.modalTitle.textContent = "Exploitatietoestand d.d. 1-1-2027";
  els.previewTable.hidden = false;
  els.receiptPreview.hidden = true;
  els.schemaPreview.hidden = true;
  els.submissionModalDetail.hidden = true;
  els.modal.hidden = false;
}

function schemaUrl(item) {
  if (item?.submissionType === "withdrawal") return "#";
  const collection = item?.status === "Nog niet ingediend" ? "draft-submissions" : "submissions";
  return `${API}/${collection}/${encodeURIComponent(item?.transactionId || "")}/schema`;
}

function openSchemaPreview(item) {
  if (!item) return;
  els.modalEyebrow.textContent = "Preview schema";
  els.modalTitle.textContent = (item.displayName || "Exploitatietoestand").replace("Exploitatietoestand", "Exploitatieschema");
  els.previewTable.hidden = true;
  els.receiptPreview.hidden = true;
  els.submissionModalDetail.hidden = true;
  els.schemaPreview.src = `${schemaUrl(item)}?v=${encodeURIComponent(item.contentHash || Date.now())}`;
  els.schemaPreview.hidden = false;
  els.modal.hidden = false;
}

async function openReceiptPreview() {
  const item = selectedItem?.receiptAvailable ? selectedItem : submissions[0];
  if (!item) return;
  try {
    const response = await fetch(receiptUrl(item, false));
    if (!response.ok) throw new Error(`Status ${response.status}`);
    els.receiptPreview.textContent = await response.text();
    els.modalEyebrow.textContent = "Preview document";
    els.modalTitle.textContent = "Ontvangstbewijs IMJV2";
    els.previewTable.hidden = true;
    els.receiptPreview.hidden = false;
    els.schemaPreview.hidden = true;
    els.submissionModalDetail.hidden = true;
    els.modal.hidden = false;
  } catch (error) {
    showServerError(error);
  }
}

function closeModal() {
  els.modal.hidden = true;
}

function showServerError(error) {
  els.receiptEmpty.hidden = false;
  els.receiptEmpty.textContent = `De object-store server is niet bereikbaar. ${error.message}`;
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} bytes`;
  return `${(bytes / 1024).toFixed(1)} KB`;
}

function formatDate(value) {
  return new Intl.DateTimeFormat("nl-BE", {
    dateStyle: "medium",
    timeStyle: "medium",
  }).format(new Date(value));
}

function formatDateOnly(value) {
  if (!value) return "Niet opgegeven";
  return new Intl.DateTimeFormat("nl-BE", { dateStyle: "medium" }).format(new Date(`${value}T12:00:00`));
}

function formatReportRange(startValue, newerStartValue) {
  const start = formatDateOnly(startValue);
  if (!newerStartValue) return `${start} – heden`;
  const end = new Date(`${newerStartValue}T12:00:00`);
  end.setDate(end.getDate() - 1);
  const formattedEnd = new Intl.DateTimeFormat("nl-BE", { dateStyle: "medium" }).format(end);
  return `${start} – ${formattedEnd}`;
}

function formatReportRangeWords(startValue, newerStartValue) {
  const start = formatDateOnly(startValue);
  if (!newerStartValue) return `${start} – heden`;
  const end = new Date(`${newerStartValue}T12:00:00`);
  end.setDate(end.getDate() - 1);
  const formattedEnd = new Intl.DateTimeFormat("nl-BE", { dateStyle: "medium" }).format(end);
  return `${start} – ${formattedEnd}`;
}

function propertyMarkup([label, value]) {
  return `<div class="property"><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value)}</dd></div>`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
