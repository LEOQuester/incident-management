(function () {
  function initPhoneInput(input) {
    if (!window.intlTelInput || input.dataset.itiInitialized) {
      return;
    }
    window.intlTelInput(input, {
      initialCountry: "lk",
      separateDialCode: true,
      nationalMode: false,
      utilsScript:
        "https://cdn.jsdelivr.net/npm/intl-tel-input@24.6.0/build/js/utils.js",
    });
    input.dataset.itiInitialized = "1";
  }

  function syncPhoneInputs(form) {
    form.querySelectorAll(".phone-input").forEach(function (input) {
      if (!input.value.trim() || !window.intlTelInput) {
        return;
      }
      var iti = window.intlTelInput.getInstance(input);
      if (iti) {
        input.value = iti.getNumber();
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".phone-input").forEach(initPhoneInput);
  });

  window.fmscSyncPhoneInputs = syncPhoneInputs;
})();
