(function () {
  var form = document.getElementById("case-form");
  if (!form) {
    return;
  }
  var typeSelect = form.querySelector('[name="comment_type"]');
  var statusSelect = form.querySelector('[name="status"]');
  if (!typeSelect || !statusSelect) {
    return;
  }
  var resolutionValue = "resolution";
  var initialStatus =
    form.getAttribute("data-initial-status") || statusSelect.value || "";

  typeSelect.addEventListener("change", function () {
    if (typeSelect.value === resolutionValue) {
      statusSelect.value = "solved";
      return;
    }
    if (statusSelect.value === "solved" && initialStatus !== "solved") {
      statusSelect.value = initialStatus;
    }
  });
})();
