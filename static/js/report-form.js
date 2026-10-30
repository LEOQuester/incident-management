(function () {
  var shell = document.getElementById("report-shell");
  var form = document.getElementById("report-form");
  if (!shell || !form) return;

  var caseTypeInput = form.querySelector('input[name="case_type"]');
  var track = document.getElementById("case-type-track");
  var sides = shell.querySelectorAll(".case-type-side");

  function setMode(type) {
    if (!caseTypeInput) return;
    var isSuggestion = type === "suggestion";
    caseTypeInput.value = isSuggestion ? "suggestion" : "complaint";
    shell.classList.remove("report-mode-complaint", "report-mode-suggestion");
    shell.classList.add(isSuggestion ? "report-mode-suggestion" : "report-mode-complaint");
    if (track) {
      track.setAttribute("aria-checked", isSuggestion ? "true" : "false");
      track.classList.toggle("is-on", isSuggestion);
    }
    sides.forEach(function (side) {
      var active = side.getAttribute("data-side") === type;
      side.classList.toggle("is-active", active);
    });
  }

  if (track) {
    track.addEventListener("click", function () {
      var next =
        caseTypeInput && caseTypeInput.value === "suggestion" ? "complaint" : "suggestion";
      setMode(next);
    });
  }

  sides.forEach(function (side) {
    side.addEventListener("click", function () {
      setMode(side.getAttribute("data-side"));
    });
  });

  var initial =
    caseTypeInput && caseTypeInput.value === "suggestion" ? "suggestion" : "complaint";
  setMode(initial);
})();
