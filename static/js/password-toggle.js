(function () {
  function initPasswordToggles(root) {
    var scope = root || document;
    scope.querySelectorAll(".password-input-wrap").forEach(function (wrap) {
      if (wrap.dataset.passwordToggleInit === "1") {
        return;
      }
      var input = wrap.querySelector("input");
      var btn = wrap.querySelector(".password-toggle-btn");
      if (!input || !btn) {
        return;
      }
      wrap.dataset.passwordToggleInit = "1";
      var icon = btn.querySelector("i");

      btn.addEventListener("click", function () {
        var show = input.type === "password";
        input.type = show ? "text" : "password";
        btn.setAttribute("aria-pressed", show ? "true" : "false");
        btn.setAttribute("aria-label", show ? "Hide password" : "Show password");
        if (icon) {
          icon.classList.toggle("fa-eye", !show);
          icon.classList.toggle("fa-eye-slash", show);
        }
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      initPasswordToggles(document);
    });
  } else {
    initPasswordToggles(document);
  }

  window.fmscInitPasswordToggles = initPasswordToggles;
})();
