const form = document.querySelector("#researchForm");
const questionInput = document.querySelector("#question");
const audienceInput = document.querySelector("#audience");
const submitButton = document.querySelector("#submitButton");
const approveButton = document.querySelector("#approveButton");
const newQuestionButton = document.querySelector("#newQuestionButton");
const loadingPanel = document.querySelector("#loadingPanel");
const resultPanel = document.querySelector("#resultPanel");
const errorPanel = document.querySelector("#errorPanel");
let currentQuestion = "";

function show(element) { element.classList.remove("hidden"); }
function hide(element) { element.classList.add("hidden"); }

async function checkHealth() {
  const status = document.querySelector("#systemStatus");
  try {
    const response = await fetch("/health");
    const data = await response.json();
    status.className = `system-status ${data.index_ready ? "ready" : "error"}`;
    status.lastElementChild.textContent = data.index_ready ? "Knowledge base ready" : "Index not ready";
  } catch {
    status.className = "system-status error";
    status.lastElementChild.textContent = "Service unavailable";
  }
}

function setBusy(busy, approved = false) {
  submitButton.disabled = busy;
  approveButton.disabled = busy;
  hide(errorPanel);
  if (busy) {
    hide(resultPanel);
    show(loadingPanel);
    loadingPanel.querySelector("h2").textContent = approved ? "Preparing the approved report" : "Reviewing the evidence";
  } else {
    hide(loadingPanel);
  }
}

function renderResult(data) {
  document.querySelector("#resultStatus").textContent = data.status.replaceAll("_", " ");
  document.querySelector("#resultText").textContent = data.result;
  document.querySelector("#reportId").textContent = data.report_id;
  document.querySelector("#tokenCount").textContent = (data.prompt_tokens + data.completion_tokens + data.embedding_tokens).toLocaleString();
  document.querySelector("#estimatedCost").textContent = `$${Number(data.estimated_cost_usd).toFixed(6)}`;
  document.querySelector("#confidenceLevel").textContent = data.confidence || "Low";
  const sourceList = document.querySelector("#sourceList");
  sourceList.replaceChildren();
  if (data.sources?.length) {
    data.sources.forEach((source) => {
      const item = document.createElement("li");
      const page = source.page_label ? ` — page ${source.page_label}` : "";
      const score = source.score == null ? "" : ` — score ${source.score}`;
      item.textContent = `${source.file_name}${page}${score}`;
      sourceList.appendChild(item);
    });
  } else {
    const item = document.createElement("li");
    item.textContent = "No source was retrieved.";
    sourceList.appendChild(item);
  }
  approveButton.classList.toggle("hidden", data.status !== "awaiting_approval");
  show(resultPanel);
  resultPanel.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function research(approvedToSave) {
  setBusy(true, approvedToSave);
  try {
    const response = await fetch("/research", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question: currentQuestion,
        audience: audienceInput.value,
        approved_to_save: approvedToSave,
      }),
    });
    const data = await response.json();
    if (!response.ok) {
      const message = Array.isArray(data.detail) ? data.detail[0]?.msg : data.detail;
      throw new Error(message || "Unexpected server response");
    }
    renderResult(data);
  } catch (error) {
    document.querySelector("#errorText").textContent = error.message;
    show(errorPanel);
  } finally {
    setBusy(false);
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  currentQuestion = questionInput.value.trim();
  if (!form.reportValidity()) return;
  research(false);
});

approveButton.addEventListener("click", () => research(true));
newQuestionButton.addEventListener("click", () => {
  hide(resultPanel);
  questionInput.focus();
  window.scrollTo({ top: 0, behavior: "smooth" });
});

document.querySelectorAll("[data-question]").forEach((button) => {
  button.addEventListener("click", () => {
    questionInput.value = button.dataset.question;
    questionInput.focus();
  });
});

checkHealth();
