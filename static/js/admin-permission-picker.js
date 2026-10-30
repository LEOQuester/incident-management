document.addEventListener("DOMContentLoaded", () => {
  const root = document.querySelector(".permission-picker-searchable");
  if (!root) return;

  const input = root.querySelector('[data-perm-picker-search]');
  const list = root.querySelector(".permission-checkboxes");
  if (!input || !list) return;

  const items = () => Array.from(list.querySelectorAll("li"));

  const apply = () => {
    const q = input.value.trim().toLowerCase();
    items().forEach((li) => {
      const text = (li.textContent || "").toLowerCase();
      li.hidden = q.length > 0 && !text.includes(q);
    });
  };

  input.addEventListener("input", apply);
  apply();
});
