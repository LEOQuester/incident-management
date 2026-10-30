(function () {
  var TOO_SHORT = 2;
  var TOO_LONG = 3;
  var INVALID_LENGTH = 5;

  function withUtils(callback) {
    if (window.intlTelInput && window.intlTelInput.utils) {
      callback();
      return;
    }
    var attempts = 0;
    var timer = setInterval(function () {
      if (window.intlTelInput && window.intlTelInput.utils) {
        clearInterval(timer);
        callback();
      } else if (++attempts > 80) {
        clearInterval(timer);
      }
    }, 50);
  }

  function ensureValidityBadge(input) {
    var host =
      input.closest(".phone-input-wrap") ||
      input.closest(".form-group") ||
      input.parentElement;
    if (!host) {
      return null;
    }
    var existing = host.querySelector(".phone-validity");
    if (existing) {
      return existing;
    }
    var badge = document.createElement("span");
    badge.className = "phone-validity";
    badge.setAttribute("aria-live", "polite");
    host.appendChild(badge);
    return badge;
  }

  function clearBadge(badge, input) {
    badge.textContent = "";
    badge.className = "phone-validity";
    input.removeAttribute("aria-invalid");
  }

  function showInvalid(badge, input) {
    badge.textContent = "Invalid";
    badge.className = "phone-validity phone-validity--bad";
    input.setAttribute("aria-invalid", "true");
  }

  function showValid(badge, input) {
    badge.textContent = "Valid";
    badge.className = "phone-validity phone-validity--ok";
    input.setAttribute("aria-invalid", "false");
  }

  /** Drop letters/symbols; keep digits and light formatting chars. */
  function stripInvalidCharacters(input) {
    var value = input.value;
    if (!value) {
      return false;
    }
    var cleaned = value.replace(/[^\d\s\-().]/g, "");
    if (cleaned !== value) {
      input.value = cleaned;
      return true;
    }
    return false;
  }

  /** e.g. 0777123456 → 777123456 when +94 is selected (national trunk 0). */
  function normalizeLeadingZero(input, iti) {
    var country = iti.getSelectedCountryData();
    if (!country || !country.dialCode) {
      return false;
    }
    var digits = input.value.replace(/\D/g, "");
    if (!digits || digits.charAt(0) !== "0") {
      return false;
    }
    var withoutTrunk = digits.replace(/^0+/, "");
    if (!withoutTrunk || withoutTrunk === digits) {
      return false;
    }
    iti.setNumber("+" + country.dialCode + withoutTrunk);
    return true;
  }

  function normalizeInternationalPaste(input, iti) {
    var raw = input.value.trim();
    if (!raw || raw.charAt(0) !== "+") {
      return false;
    }
    var digits = raw.replace(/\D/g, "");
    if (digits.length < 8) {
      return false;
    }
    iti.setNumber("+" + digits);
    return true;
  }

  function updatePhoneValidity(input) {
    var badge = ensureValidityBadge(input);
    if (!badge || !window.intlTelInput) {
      return;
    }
    var iti = window.intlTelInput.getInstance(input);
    if (!iti) {
      return;
    }

    withUtils(function () {
      var hadBadChars = stripInvalidCharacters(input);
      normalizeLeadingZero(input, iti);
      normalizeInternationalPaste(input, iti);

      var raw = input.value.trim();
      if (!raw) {
        clearBadge(badge, input);
        return;
      }

      if (iti.isValidNumber()) {
        showValid(badge, input);
        var e164 = iti.getNumber();
        if (e164) {
          iti.setNumber(e164);
        }
        return;
      }

      if (hadBadChars) {
        showInvalid(badge, input);
        return;
      }

      var err = iti.getValidationError();
      if (err === TOO_SHORT) {
        clearBadge(badge, input);
        return;
      }
      if (err === TOO_LONG || err === INVALID_LENGTH) {
        showInvalid(badge, input);
        return;
      }

      var digits = raw.replace(/\D/g, "");
      var country = iti.getSelectedCountryData();
      var maxNational =
        country && country.iso2 === "lk" ? 9 : country ? 15 : 15;
      if (digits.length > maxNational + 2) {
        showInvalid(badge, input);
        return;
      }

      if (/[^\d\s\-().]/.test(raw)) {
        showInvalid(badge, input);
        return;
      }

      clearBadge(badge, input);
    });
  }

  function bindPhoneValidation(input) {
    if (input.dataset.phoneValidateBound) {
      return;
    }
    input.dataset.phoneValidateBound = "1";
    ["input", "keyup", "countrychange", "blur"].forEach(function (evt) {
      input.addEventListener(evt, function () {
        updatePhoneValidity(input);
      });
    });
    withUtils(function () {
      updatePhoneValidity(input);
    });
  }

  function initPhoneInput(input) {
    if (!window.intlTelInput || input.dataset.itiInitialized) {
      return;
    }
    window.intlTelInput(input, {
      initialCountry: "lk",
      separateDialCode: true,
      nationalMode: false,
      formatOnDisplay: true,
      autoPlaceholder: "aggressive",
      utilsScript:
        "https://cdn.jsdelivr.net/npm/intl-tel-input@24.6.0/build/js/utils.js",
    });
    input.dataset.itiInitialized = "1";
    bindPhoneValidation(input);
  }

  function syncPhoneInputs(form) {
    form.querySelectorAll(".phone-input").forEach(function (input) {
      if (!input.value.trim() || !window.intlTelInput) {
        return;
      }
      withUtils(function () {
        var iti = window.intlTelInput.getInstance(input);
        if (!iti) {
          return;
        }
        normalizeLeadingZero(input, iti);
        if (iti.isValidNumber()) {
          input.value = iti.getNumber();
        }
      });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".phone-input").forEach(initPhoneInput);
  });

  window.fmscSyncPhoneInputs = syncPhoneInputs;
  window.fmscUpdatePhoneValidity = updatePhoneValidity;
})();
