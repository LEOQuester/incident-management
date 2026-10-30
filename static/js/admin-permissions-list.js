document.addEventListener("DOMContentLoaded", () => {
  const input = document.getElementById("perm-search-q");
  const table = document.querySelector(".admin-permissions-table");
  if (!input || !table) return;

  const tbody = table.querySelector("tbody");
  const rows = () =>
    Array.from(tbody.querySelectorAll("tr[data-perm-filter]"));
  const countEl = document.querySelector("[data-perm-visible-count]");
  const noMatchRow = tbody.querySelector("tr[data-perm-no-match]");
  const total = rows().length;

  const apply = () => {
    const q = input.value.trim().toLowerCase();
    let visible = 0;
    rows().forEach((row) => {
      const haystack = row.getAttribute("data-perm-filter") || "";
      const show = !q || haystack.includes(q);
      row.hidden = !show;
      if (show) visible += 1;
    });
    if (countEl) {
      countEl.textContent =
        q && visible !== total
          ? `${visible} of ${total} permissions`
          : `${total} permission${total === 1 ? "" : "s"}`;
    }
    if (noMatchRow) {
      noMatchRow.hidden = visible > 0 || total === 0;
    }
  };

  input.addEventListener("input", apply);
  apply();
});
