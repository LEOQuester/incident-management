document.addEventListener("DOMContentLoaded", () => {
  const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)");

  document.querySelectorAll("[data-post-info]").forEach((root) => {
    const trigger = root.querySelector(".social-post-info-trigger");
    if (!trigger) {
      return;
    }

    const setOpen = (open) => {
      root.classList.toggle("is-open", open);
      trigger.setAttribute("aria-expanded", open ? "true" : "false");
    };

    trigger.addEventListener("click", (event) => {
      if (finePointer.matches) {
        return;
      }
      event.stopPropagation();
      setOpen(!root.classList.contains("is-open"));
    });

    document.addEventListener("click", (event) => {
      if (!root.classList.contains("is-open")) {
        return;
      }
      if (!root.contains(event.target)) {
        setOpen(false);
      }
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && root.classList.contains("is-open")) {
        setOpen(false);
        trigger.focus();
      }
    });
  });

  document.querySelectorAll("[data-caption]").forEach((root) => {
    const text = root.querySelector(".social-post-description");
    const toggle = root.querySelector(".social-post-see-more");
    if (!text || !toggle) {
      return;
    }

    const syncToggleVisibility = () => {
      if (root.classList.contains("is-expanded")) {
        toggle.hidden = false;
        return;
      }
      toggle.hidden = text.scrollWidth <= text.clientWidth + 1;
    };

    toggle.addEventListener("click", () => {
      const expanded = root.classList.toggle("is-expanded");
      toggle.textContent = expanded ? "See less" : "See more...";
      toggle.setAttribute("aria-expanded", expanded ? "true" : "false");
      if (!expanded) {
        syncToggleVisibility();
      }
    });

    syncToggleVisibility();
    window.addEventListener("resize", syncToggleVisibility);
  });

  document.querySelectorAll("[data-social-carousel]").forEach((root) => {
    const track = root.querySelector(".social-post-media-track");
    const slides = track ? [...track.querySelectorAll(".social-post-media-slide")] : [];
    const downloadLink = root.querySelector("[data-carousel-download]");
    if (!track || !slides.length) {
      return;
    }

    const slideWidth = () => track.clientWidth;

    const currentIndex = () => {
      const w = slideWidth();
      if (!w) {
        return 0;
      }
      return Math.min(slides.length - 1, Math.round(track.scrollLeft / w));
    };

    const syncDownload = () => {
      if (!downloadLink) {
        return;
      }
      const slide = slides[currentIndex()];
      const url = slide.getAttribute("data-download-url");
      const label = slide.getAttribute("data-download-label") || "Download current evidence";
      if (url) {
        downloadLink.href = url;
        downloadLink.hidden = false;
        downloadLink.title = label;
        downloadLink.setAttribute("aria-label", label);
      } else {
        downloadLink.hidden = true;
        downloadLink.removeAttribute("href");
      }
    };

    if (slides.length <= 1) {
      syncDownload();
      return;
    }

    const ui = root.querySelector(".social-post-media-ui");
    const prevBtn = root.querySelector(".social-post-media-btn--prev");
    const nextBtn = root.querySelector(".social-post-media-btn--next");
    const dotsHost = root.querySelector(".social-post-media-dots");
    const counter = root.querySelector(".social-post-media-counter");
    if (!ui || !prevBtn || !nextBtn || !dotsHost || !counter) {
      syncDownload();
      return;
    }

    ui.hidden = false;
    root.classList.add("social-post-media--multi");

    const dots = slides.map((_, index) => {
      const dot = document.createElement("button");
      dot.type = "button";
      dot.className = "social-post-media-dot";
      dot.setAttribute("role", "tab");
      dot.setAttribute("aria-label", `Evidence slide ${index + 1}`);
      dot.addEventListener("click", () => scrollToIndex(index));
      dotsHost.appendChild(dot);
      return dot;
    });

    const scrollToIndex = (index) => {
      const w = slideWidth();
      track.scrollTo({ left: w * index, behavior: "smooth" });
    };

    const updateUi = () => {
      const index = currentIndex();
      counter.textContent = `${index + 1} / ${slides.length}`;
      dots.forEach((dot, i) => {
        const active = i === index;
        dot.classList.toggle("is-active", active);
        dot.setAttribute("aria-selected", active ? "true" : "false");
      });
      syncDownload();
    };

    prevBtn.addEventListener("click", () => {
      const index = currentIndex();
      scrollToIndex(index <= 0 ? slides.length - 1 : index - 1);
    });

    nextBtn.addEventListener("click", () => {
      const index = currentIndex();
      scrollToIndex(index >= slides.length - 1 ? 0 : index + 1);
    });

    track.addEventListener("scroll", () => {
      window.requestAnimationFrame(updateUi);
    }, { passive: true });

    window.addEventListener("resize", updateUi);
    updateUi();
  });
});
