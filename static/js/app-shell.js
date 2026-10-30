document.addEventListener("DOMContentLoaded", () => {
  const layout = document.querySelector(".app-shell .layout");
  const toggle = document.querySelector(".sidebar-toggle");
  const backdrop = document.querySelector(".sidebar-backdrop");
  const sidebar = document.getElementById("app-sidebar");
  if (!layout || !toggle || !sidebar) {
    return;
  }

  const setOpen = (open) => {
    layout.classList.toggle("sidebar-open", open);
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    toggle.setAttribute("aria-label", open ? "Close menu" : "Open menu");
    document.body.classList.toggle("sidebar-nav-open", open);
    if (backdrop) {
      backdrop.setAttribute("aria-hidden", open ? "false" : "true");
    }
  };

  toggle.addEventListener("click", () => {
    setOpen(!layout.classList.contains("sidebar-open"));
  });

  if (backdrop) {
    backdrop.addEventListener("click", () => setOpen(false));
  }

  sidebar.querySelectorAll(".sidebar-link").forEach((link) => {
    link.addEventListener("click", () => setOpen(false));
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && layout.classList.contains("sidebar-open")) {
      setOpen(false);
      toggle.focus();
    }
  });

  window.matchMedia("(min-width: 901px)").addEventListener("change", (event) => {
    if (event.matches) {
      setOpen(false);
    }
  });
});
