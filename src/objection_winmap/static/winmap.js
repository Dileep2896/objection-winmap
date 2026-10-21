/* Progressive enhancement: every quote and transcript remains readable without JS. */
(() => {
  const rows = [...document.querySelectorAll(".objection-row")];
  const search = document.querySelector("#objection-search");
  let filter = "all";
  function updateRows() {
    const query = (search?.value || "").trim().toLowerCase();
    let count = 0;
    rows.forEach((row) => {
      row.hidden =
        !row.dataset.objection.includes(query) ||
        (filter === "sufficient" && row.dataset.sufficient !== "true");
      if (!row.hidden) count++;
    });
    const empty = document.querySelector("#empty-search");
    if (empty) empty.hidden = count > 0;
  }
  search?.addEventListener("input", updateRows);
  document.querySelectorAll("[data-filter]").forEach((button) => {
    button.addEventListener("click", () => {
      filter = button.dataset.filter;
      document.querySelectorAll("[data-filter]").forEach((item) => {
        item.classList.toggle("active", item === button);
        item.setAttribute("aria-pressed", String(item === button));
      });
      updateRows();
    });
  });
  document.querySelectorAll("[data-open-response]").forEach((button) => {
    button.addEventListener("click", () => {
      const details = document.getElementById(button.dataset.openResponse);
      document.querySelectorAll(".response-details").forEach((item) => {
        item.open = item === details;
      });
      details.querySelector("summary").focus({ preventScroll: true });
      details.scrollIntoView({
        behavior: matchMedia("(prefers-reduced-motion: reduce)").matches
          ? "instant"
          : "smooth",
        block: "center",
      });
    });
  });
  document.querySelector("#rep-form")?.addEventListener("submit", (event) => {
    event.preventDefault();
    window.location.assign(
      `/reps/${encodeURIComponent(document.querySelector("#rep-select").value)}`,
    );
  });
  document.querySelector("#copy-line")?.addEventListener("click", async () => {
    const line = document
      .querySelector("#practice-line")
      .textContent.replace(/^“|”$/g, "");
    const status = document.querySelector("#copy-status");
    try {
      await navigator.clipboard.writeText(line);
      status.textContent = "Practice line copied.";
    } catch {
      status.textContent =
        "Copy is unavailable here. Select the quote to copy it.";
    }
  });
  const start = document.querySelector("#practice-start");
  let timer;
  start?.addEventListener("click", () => {
    if (timer) {
      clearInterval(timer);
      timer = undefined;
      start.textContent = "Start practicing →";
      document.querySelector("#practice-status").textContent =
        "Practice paused. Start again when you’re ready.";
      return;
    }
    const deadline = Date.now() + 30000;
    const status = document.querySelector("#practice-status");
    status.textContent =
      "Practice the invitation, then listen to how it sounds.";
    function tick() {
      const seconds = Math.max(0, Math.ceil((deadline - Date.now()) / 1000));
      start.textContent = `Pause practice · ${seconds}s`;
      if (!seconds) {
        clearInterval(timer);
        timer = undefined;
        start.textContent = "Practice again →";
        status.textContent =
          "Drill complete. Try this move in your next conversation.";
      }
    }
    timer = setInterval(tick, 250);
    tick();
  });
  const media = matchMedia("(prefers-reduced-motion: reduce)");
  let bars;
  if (
    !media.matches &&
    window.Motion &&
    document.querySelector(".comparison-top")
  ) {
    bars = Motion.animate(
      ".comparison-top",
      { scaleX: [0, 1] },
      { duration: 0.9, ease: [0.22, 1, 0.36, 1] },
    );
  }
  media.addEventListener("change", (event) => {
    if (event.matches && bars) {
      bars.complete();
    }
  });
})();
