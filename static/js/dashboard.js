(function () {
  "use strict";
  var sort = document.getElementById("id_sort");
  if (sort) {
    sort.addEventListener("change", function () {
      var url = new URL(window.location.href);
      if (sort.value) url.searchParams.set("sort", sort.value);
      else url.searchParams.delete("sort");
      url.searchParams.delete("page");
      url.searchParams.delete("export");
      url.hash = "case-list";
      window.location.assign(url.toString());
    });
  }
})();
