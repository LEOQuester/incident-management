(function () {
  var form = document.getElementById("register-form");
  if (form) {
    form.addEventListener("submit", function () {
      if (typeof window.fmscSyncPhoneInputs === "function") {
        window.fmscSyncPhoneInputs(form);
      }
    });
  }

  var passwordInput = document.getElementById("id_password1");
  var tooltip = document.getElementById("register-password-tooltip");
  if (!passwordInput || !tooltip) {
    return;
  }

  var showTooltip = function () {
    tooltip.hidden = false;
  };

  var hideTooltip = function () {
    tooltip.hidden = true;
  };

  passwordInput.addEventListener("focus", showTooltip);
  passwordInput.addEventListener("input", showTooltip);
  passwordInput.addEventListener("blur", function () {
    window.setTimeout(function () {
      if (document.activeElement !== passwordInput) {
        hideTooltip();
      }
    }, 120);
  });
})();
