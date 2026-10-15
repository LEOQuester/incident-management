(function () {
  var uploader = document.getElementById("photo-uploader");
  if (!uploader) return;

  var maxPhotos = parseInt(uploader.dataset.max || "5", 10);
  var input = document.getElementById("photo-input");
  var dropzone = document.getElementById("photo-dropzone");
  var grid = document.getElementById("photo-preview-grid");
  var addBtn = document.getElementById("photo-add-btn");
  var files = [];

  function syncInput() {
    var dt = new DataTransfer();
    files.forEach(function (f) {
      dt.items.add(f);
    });
    input.files = dt.files;
  }

  function render() {
    grid.innerHTML = "";
    files.forEach(function (file, index) {
      var cell = document.createElement("div");
      cell.className = "photo-preview-item";
      var img = document.createElement("img");
      img.alt = "Preview";
      img.src = URL.createObjectURL(file);
      var remove = document.createElement("button");
      remove.type = "button";
      remove.className = "photo-remove";
      remove.innerHTML = "&times;";
      remove.addEventListener("click", function () {
        files.splice(index, 1);
        syncInput();
        render();
      });
      cell.appendChild(img);
      cell.appendChild(remove);
      grid.appendChild(cell);
    });
  }

  function addFiles(list) {
    Array.from(list).forEach(function (file) {
      if (!file.type.startsWith("image/")) return;
      if (files.length >= maxPhotos) return;
      files.push(file);
    });
    syncInput();
    render();
  }

  addBtn.addEventListener("click", function () {
    input.click();
  });

  dropzone.addEventListener("click", function (e) {
    if (e.target === addBtn || addBtn.contains(e.target)) return;
    input.click();
  });

  input.addEventListener("change", function () {
    addFiles(input.files);
  });

  ["dragenter", "dragover"].forEach(function (evt) {
    dropzone.addEventListener(evt, function (e) {
      e.preventDefault();
      dropzone.classList.add("dragover");
    });
  });

  ["dragleave", "drop"].forEach(function (evt) {
    dropzone.addEventListener(evt, function (e) {
      e.preventDefault();
      dropzone.classList.remove("dragover");
    });
  });

  dropzone.addEventListener("drop", function (e) {
    addFiles(e.dataTransfer.files);
  });
})();
