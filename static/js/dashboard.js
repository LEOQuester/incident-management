(function () {
  "use strict";

  var form = document.getElementById("dashboard-filters");
  if (form) {
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
      search.addEventListener("keydown", function (event) {
        if (event.key === "Enter") {
          event.preventDefault();
          window.clearTimeout(debounceTimer);
          submitFilters();
        }
      });
    }
  }
})();
