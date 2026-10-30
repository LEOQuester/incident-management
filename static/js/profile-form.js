(function () {
  var fileInput = document.querySelector(".profile-avatar-file");
  var img = document.getElementById("profile-avatar-img");
  var placeholder = document.getElementById("profile-avatar-placeholder");
  var clearBox = document.getElementById("avatar-clear");

  if (!fileInput) {
    return;
  }

  fileInput.addEventListener("change", function () {
    var file = fileInput.files && fileInput.files[0];
    if (!file || !file.type.match(/^image\//)) {
      return;
    }
    if (clearBox) {
      clearBox.checked = false;
    }
    var reader = new FileReader();
    reader.onload = function (ev) {
      if (!img) {
        return;
      }
      img.src = ev.target.result;
      img.hidden = false;
      img.classList.remove("hidden");
      if (placeholder) {
        placeholder.classList.add("hidden");
      }
    };
    reader.readAsDataURL(file);
  });

  if (clearBox) {
    clearBox.addEventListener("change", function () {
      if (!clearBox.checked) {
        return;
      }
      fileInput.value = "";
      if (img) {
        img.removeAttribute("src");
        img.hidden = true;
        img.classList.add("hidden");
      }
      if (placeholder) {
        placeholder.classList.remove("hidden");
      }
    });
  }
})();
