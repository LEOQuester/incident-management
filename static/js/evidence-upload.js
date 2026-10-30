(function () {
  var form = document.getElementById("report-form") || document.getElementById("case-form");
  var shell =
    document.getElementById("evidence-upload") ||
    document.getElementById("report-shell");
  var slotsRoot = document.getElementById("evidence-slots");
  var fileInput = document.getElementById("evidence-input");
  var countEl = document.getElementById("evidence-count");
  var statusEl = document.getElementById("evidence-status");

  if (!form || !slotsRoot || !fileInput || !shell) return;

  var maxFiles = parseInt(shell.getAttribute("data-max-evidence") || "4", 10);
  var maxMb = parseInt(shell.getAttribute("data-max-mb") || "5", 10);
  var maxBytes = maxMb * 1024 * 1024;
  var files = [];
  var savedPreviews = [];

  var dataEl = document.getElementById("evidence-existing-data");
  if (dataEl) {
    try {
      savedPreviews = JSON.parse(dataEl.textContent);
    } catch (e) {
      savedPreviews = [];
    }
  }
  if (!Array.isArray(savedPreviews)) {
    savedPreviews = [];
  }

  function totalCount() {
    return savedPreviews.length + files.length;
  }

  function syncInput() {
    var dt = new DataTransfer();
    files.forEach(function (file) {
      dt.items.add(file);
    });
    fileInput.files = dt.files;
  }

  function updateCount() {
    if (countEl) {
      countEl.textContent = totalCount() + " / " + maxFiles;
    }
  }

  function appendSavedSlot(item) {
    var slot = document.createElement("div");
    slot.className = "evidence-slot evidence-slot-filled evidence-slot-saved";
    var preview = document.createElement("div");
    preview.className = "evidence-preview";
    if (item.type === "video") {
      var video = document.createElement("video");
      video.src = item.url;
      video.controls = true;
      video.playsInline = true;
      video.preload = "metadata";
      preview.appendChild(video);
    } else if (item.type === "image") {
      var img = document.createElement("img");
      img.src = item.url;
      img.alt = "Uploaded evidence";
      img.loading = "lazy";
      preview.appendChild(img);
    } else {
      var link = document.createElement("a");
      link.className = "evidence-file-link";
      link.href = item.url;
      link.innerHTML = '<i class="fa fa-file-arrow-down" aria-hidden="true"></i> File';
      preview.appendChild(link);
    }
    slot.appendChild(preview);
    slotsRoot.appendChild(slot);
  }

  function appendNewFileSlot(file, index) {
    var slot = document.createElement("div");
    slot.className = "evidence-slot evidence-slot-filled";
    var preview = document.createElement("div");
    preview.className = "evidence-preview";
    if (file.type && file.type.indexOf("video/") === 0) {
      var video = document.createElement("video");
      video.src = URL.createObjectURL(file);
      video.muted = true;
      video.playsInline = true;
      video.controls = true;
      preview.appendChild(video);
    } else {
      var img = document.createElement("img");
      img.src = URL.createObjectURL(file);
      img.alt = file.name;
      preview.appendChild(img);
    }
    var remove = document.createElement("button");
    remove.type = "button";
    remove.className = "evidence-remove";
    remove.setAttribute("aria-label", "Remove " + file.name);
    remove.innerHTML = "&times;";
    remove.addEventListener("click", function () {
      files.splice(index, 1);
      syncInput();
      renderSlots();
    });
    slot.appendChild(preview);
    slot.appendChild(remove);
    slotsRoot.appendChild(slot);
  }

  function appendEmptySlot() {
    var empty = document.createElement("div");
    empty.className = "evidence-slot evidence-slot-empty";
    empty.setAttribute("role", "button");
    empty.setAttribute("tabindex", "0");
    empty.setAttribute("aria-label", "Add evidence file");
    var plus = document.createElement("span");
    plus.className = "evidence-plus";
    plus.innerHTML = '<i class="fa fa-plus" aria-hidden="true"></i>';
    empty.appendChild(plus);
    empty.addEventListener("click", openPicker);
    empty.addEventListener("keydown", function (event) {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openPicker();
      }
    });
    slotsRoot.appendChild(empty);
  }

  function renderSlots() {
    slotsRoot.innerHTML = "";
    savedPreviews.forEach(appendSavedSlot);
    files.forEach(function (file, index) {
      appendNewFileSlot(file, index);
    });
    var emptySlots = Math.max(0, maxFiles - totalCount());
    for (var i = 0; i < emptySlots; i += 1) {
      appendEmptySlot();
    }
    updateCount();
  }

  function openPicker() {
    if (totalCount() >= maxFiles) {
      if (statusEl) statusEl.textContent = "Maximum " + maxFiles + " files reached.";
      return;
    }
    fileInput.click();
  }

  function rejectOversized(selected) {
    var ok = [];
    var rejected = 0;
    Array.from(selected || []).forEach(function (file) {
      if (file.size > maxBytes) {
        rejected += 1;
        return;
      }
      ok.push(file);
    });
    if (rejected && statusEl) {
      statusEl.textContent =
        rejected +
        " file(s) over " +
        maxMb +
        " MB. Use a Google Drive link in Description instead.";
    }
    return ok;
  }

  function addFiles(selected) {
    if (!selected || !selected.length) return;
    var allowed = rejectOversized(selected);
    var added = 0;
    allowed.forEach(function (file) {
      if (totalCount() >= maxFiles) return;
      files.push(file);
      added += 1;
    });
    if (statusEl && added > 0) {
      statusEl.textContent = added + " file(s) added.";
    } else if (statusEl && !allowed.length && totalCount() >= maxFiles) {
      statusEl.textContent = "Maximum " + maxFiles + " files.";
    }
    syncInput();
    renderSlots();
  }

  fileInput.addEventListener("change", function () {
    addFiles(fileInput.files);
  });

  var dropTarget = shell;
  if (dropTarget) {
    ["dragenter", "dragover"].forEach(function (name) {
      dropTarget.addEventListener(name, function (event) {
        event.preventDefault();
        dropTarget.classList.add("is-dragover");
      });
    });
    ["dragleave", "drop"].forEach(function (name) {
      dropTarget.addEventListener(name, function (event) {
        event.preventDefault();
        dropTarget.classList.remove("is-dragover");
      });
    });
    dropTarget.addEventListener("drop", function (event) {
      addFiles(event.dataTransfer && event.dataTransfer.files);
    });
  }

  form.addEventListener("submit", function () {
    syncInput();
    if (statusEl) statusEl.textContent = "Submitting…";
    form.querySelectorAll('button[type="submit"]').forEach(function (button) {
      button.disabled = true;
    });
  });

  renderSlots();
})();
