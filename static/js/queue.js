(function () {
  "use strict";

  var form = document.getElementById("queue-filters");
  if (!form) {
    return;
  }

  var debounceTimer;

  function submitFilters() {
    if (typeof form.requestSubmit === "function") {
      form.requestSubmit();
    } else {
      form.submit();
    }
  }

  form.querySelectorAll("select, input[type='date']").forEach(function (field) {
    field.addEventListener("change", submitFilters);
  });

  var search = form.querySelector("input[name='q']");
  if (search) {
    search.addEventListener("input", function () {
      window.clearTimeout(debounceTimer);
      debounceTimer = window.setTimeout(submitFilters, 400);
    });
  }
})();
