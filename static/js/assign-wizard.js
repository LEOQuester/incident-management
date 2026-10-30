(() => {
  const root = document.getElementById("assign-wizard-root");
  if (!root) return;

  const titleEl = root.querySelector("#assign-wizard-title");
  const errorEl = root.querySelector("[data-assign-error]");
  const authorityList = root.querySelector("[data-assign-authority-list]");
  const userList = root.querySelector("[data-assign-user-list]");
  const authoritySearch = root.querySelector("#assign-authority-search");
  const authorityLabel = root.querySelector("[data-assign-authority-label]");
  const backBtn = root.querySelector("[data-assign-back]");
  const nextBtn = root.querySelector("[data-assign-next]");
  const submitBtn = root.querySelector("[data-assign-submit]");
  const commentEl = root.querySelector("#assign-comment");
  const summaryAuthority = root.querySelector("[data-assign-summary-authority]");
  const summaryPerson = root.querySelector("[data-assign-summary-person]");
  const stepMarkers = root.querySelectorAll("[data-step-marker]");
  const panels = root.querySelectorAll("[data-assign-step]");

  let caseId = null;
  let step = 1;
  let authorities = [];
  let users = [];
  let selection = {
    authorityId: null,
    authorityName: "",
    assigneeId: null,
    assigneeName: "",
  };

  function csrfToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : "";
  }

  function showError(message) {
    if (!errorEl) return;
    if (message) {
      errorEl.textContent = message;
      errorEl.hidden = false;
    } else {
      errorEl.textContent = "";
      errorEl.hidden = true;
    }
  }

  function setStep(nextStep) {
    step = nextStep;
    stepMarkers.forEach((marker) => {
      const n = Number(marker.getAttribute("data-step-marker"));
      marker.classList.toggle("is-active", n === step);
      marker.classList.toggle("is-done", n < step);
    });
    panels.forEach((panel) => {
      const n = Number(panel.getAttribute("data-assign-step"));
      const active = n === step;
      panel.classList.toggle("is-active", active);
      panel.hidden = !active;
    });
    backBtn.hidden = step <= 1;
    nextBtn.hidden = step >= 3;
    submitBtn.hidden = step !== 3;
    nextBtn.disabled = !canAdvance();
  }

  function canAdvance() {
    if (step === 1) return Boolean(selection.authorityId);
    if (step === 2) return Boolean(selection.assigneeId);
    return true;
  }

  function optionsUrl(extraParams) {
    const base = `/incidents/${caseId}/assign/options/`;
    if (!extraParams) return base;
    const params = new URLSearchParams(extraParams);
    return `${base}?${params.toString()}`;
  }

  function submitUrl() {
    return `/incidents/${caseId}/assign/`;
  }

  function renderAuthorities(filter) {
    authorityList.innerHTML = "";
    const q = (filter || "").trim().toLowerCase();
    const items = authorities.filter((item) => {
      if (!q) return true;
      return item.name.toLowerCase().includes(q);
    });
    if (!items.length) {
      authorityList.innerHTML =
        '<li class="assign-wizard-empty">No authorities match your search.</li>';
      return;
    }
    items.forEach((item) => {
      const li = document.createElement("li");
      const btn = document.createElement("button");
      btn.type = "button";
      btn.classList.toggle("is-selected", selection.authorityId === item.id);
      btn.innerHTML = `<span class="assign-wizard-item-title">${escapeHtml(item.name)}</span>`;
      btn.addEventListener("click", () => {
        selection.authorityId = item.id;
        selection.authorityName = item.name;
        selection.assigneeId = null;
        selection.assigneeName = "";
        renderAuthorities(authoritySearch.value);
        setStep(1);
      });
      li.appendChild(btn);
      authorityList.appendChild(li);
    });
  }

  function renderUsers() {
    userList.innerHTML = "";

    if (!users.length) {
      const empty = document.createElement("li");
      empty.className = "assign-wizard-empty";
      empty.textContent =
        "No users linked to this authority yet. Add a user with a role for this unit under Administration → Users.";
      userList.appendChild(empty);
      selection.assigneeId = null;
      selection.assigneeName = "";
      setStep(2);
      return;
    }

    users.forEach((user) => {
      const li = document.createElement("li");
      const btn = document.createElement("button");
      btn.type = "button";
      btn.classList.toggle("is-selected", selection.assigneeId === user.id);
      btn.innerHTML = `<span class="assign-wizard-item-title">${escapeHtml(user.display_name)}</span><span class="assign-wizard-item-sub">@${escapeHtml(user.username)}${
        user.email ? ` · ${escapeHtml(user.email)}` : ""
      }</span>`;
      btn.addEventListener("click", () => {
        selection.assigneeId = user.id;
        selection.assigneeName = user.display_name;
        renderUsers();
        setStep(2);
      });
      li.appendChild(btn);
      userList.appendChild(li);
    });
    setStep(2);
  }

  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function openWizard(trigger) {
    caseId = trigger.getAttribute("data-case-id");
    const label =
      trigger.getAttribute("data-case-label") ||
      trigger.getAttribute("data-case-number") ||
      "Case";
    if (!caseId) return;
    titleEl.textContent = label;
    showError("");
    commentEl.value = "";
    selection = {
      authorityId: null,
      authorityName: "",
      assigneeId: null,
      assigneeName: "",
    };
    authorities = [];
    users = [];
    authoritySearch.value = "";
    root.hidden = false;
    root.setAttribute("aria-hidden", "false");
    document.body.classList.add("assign-wizard-open");
    root.querySelector(".assign-wizard-dialog").focus();
    setStep(1);
    fetch(optionsUrl())
      .then((response) => {
        if (!response.ok) throw new Error("Could not load assignment options.");
        return response.json();
      })
      .then((data) => {
        authorities = data.authorities || [];
        if (data.case && data.case.label) {
          titleEl.textContent = data.case.label;
        } else if (data.case && data.case.number) {
          titleEl.textContent = data.case.number;
        }
        renderAuthorities("");
      })
      .catch((err) => showError(err.message || "Something went wrong."));
  }

  function closeWizard() {
    root.hidden = true;
    root.setAttribute("aria-hidden", "true");
    document.body.classList.remove("assign-wizard-open");
  }

  document.querySelectorAll("[data-open-assign-wizard]").forEach((trigger) => {
    trigger.addEventListener("click", () => openWizard(trigger));
  });

  root.querySelectorAll("[data-assign-dismiss]").forEach((el) => {
    el.addEventListener("click", closeWizard);
  });

  authoritySearch.addEventListener("input", () => {
    renderAuthorities(authoritySearch.value);
  });

  backBtn.addEventListener("click", () => {
    showError("");
    if (step > 1) setStep(step - 1);
  });

  nextBtn.addEventListener("click", () => {
    showError("");
    if (step === 1 && selection.authorityId) {
      authorityLabel.textContent = selection.authorityName;
      fetch(optionsUrl({ authority_id: selection.authorityId }))
        .then((response) => {
          if (!response.ok) throw new Error("Could not load staff.");
          return response.json();
        })
        .then((data) => {
          users = data.users || [];
          renderUsers();
          setStep(2);
        })
        .catch((err) => showError(err.message || "Something went wrong."));
      return;
    }
    if (step === 2) {
      if (!selection.assigneeId) {
        showError("Choose a responsible person for this authority.");
        return;
      }
      summaryAuthority.textContent = selection.authorityName;
      summaryPerson.textContent = selection.assigneeName;
      setStep(3);
    }
  });

  submitBtn.addEventListener("click", () => {
    showError("");
    if (!selection.assigneeId) {
      showError("Choose a responsible person for this authority.");
      return;
    }
    submitBtn.disabled = true;
    const body = {
      authority_id: selection.authorityId,
      assignee_id: selection.assigneeId,
      comment: commentEl.value,
    };
    fetch(submitUrl(), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken(),
      },
      body: JSON.stringify(body),
    })
      .then(async (response) => {
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(data.error || "Assignment failed.");
        }
        if (data.redirect_url) {
          window.location.href = data.redirect_url;
        } else {
          window.location.reload();
        }
      })
      .catch((err) => {
        showError(err.message || "Assignment failed.");
        submitBtn.disabled = false;
      });
  });

  document.addEventListener("keydown", (event) => {
    if (root.hidden) return;
    if (event.key === "Escape") closeWizard();
  });
})();
