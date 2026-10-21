(() => {
  const media = matchMedia("(prefers-reduced-motion: reduce)");
  const counters = [...document.querySelectorAll("[data-counter]")];
  const controls = [];
  const cleanups = [];
  const format = (el, value) =>
    el.dataset.money
      ? Math.round(value).toLocaleString("en-US")
      : String(Math.round(value));
  function finish() {
    cleanups.splice(0).forEach((stop) => stop());
    controls.forEach((control) => control.complete());
    counters.forEach((el) => {
      el.textContent = format(el, Number(el.dataset.target));
    });
    document.querySelectorAll(".reveal,.rep-dot,.story-chip").forEach((el) => {
      el.style.opacity = "1";
      el.style.transform = "none";
    });
    document.querySelectorAll(".flow-path path").forEach((path) => {
      path.style.strokeDashoffset = "0";
    });
    const gap = document.querySelector("#growing-gap");
    if (gap) gap.style.transform = `scaleX(${gap.dataset.to})`;
  }
  // Server HTML is the final, fully visible state, including if the CDN is unavailable.
  if (media.matches || !window.Motion) {
    finish();
    return;
  }
  const { animate, inView, scroll, stagger } = window.Motion;
  const ease = [0.22, 1, 0.36, 1];
  const track = (control) => {
    controls.push(control);
    return control;
  };
  cleanups.push(
    inView(
      ".reveal",
      (element) => {
        if (!media.matches)
          track(
            animate(
              element,
              { opacity: [0, 1], y: [24, 0] },
              { duration: 0.65, ease },
            ),
          );
      },
      { amount: 0.15 },
    ),
  );
  counters.forEach((element) => {
    cleanups.push(
      inView(
        element,
        () => {
          if (media.matches) return;
          track(
            animate(0, Number(element.dataset.target), {
              duration: 1.5,
              ease,
              onUpdate: (value) => {
                element.textContent = format(element, value);
              },
            }),
          );
        },
        { amount: 0.6 },
      ),
    );
  });
  cleanups.push(
    inView(".rep-dots", () => {
      if (!media.matches)
        track(
          animate(
            ".rep-dot",
            { opacity: [0, 1], y: [18, 0] },
            {
              duration: 0.55,
              delay: stagger(0.065),
              ease,
            },
          ),
        );
    }),
  );
  cleanups.push(
    inView(".objection-cloud", () => {
      if (!media.matches)
        track(
          animate(
            ".story-chip",
            { opacity: [0, 1], y: [-25, 0], rotate: [-3, 1, 0] },
            {
              duration: 0.8,
              delay: stagger(0.09),
              ease,
            },
          ),
        );
    }),
  );
  cleanups.push(
    scroll(
      track(animate(".story-progress", { scaleX: [0, 1] }, { ease: "linear" })),
    ),
  );
  const section = document.querySelector("#change");
  document.querySelectorAll(".flow-path path").forEach((path) => {
    const length = path.getTotalLength();
    path.style.strokeDasharray = String(length);
    cleanups.push(
      scroll(
        track(
          animate(path, { strokeDashoffset: [length, 0] }, { ease: "linear" }),
        ),
        {
          target: section,
          offset: ["start .85", "end .75"],
        },
      ),
    );
  });
  const gap = document.querySelector("#growing-gap");
  cleanups.push(
    inView(
      gap,
      () => {
        if (!media.matches)
          track(
            animate(
              gap,
              { scaleX: [Number(gap.dataset.from), Number(gap.dataset.to)] },
              {
                duration: 1.4,
                ease,
              },
            ),
          );
      },
      { amount: 1 },
    ),
  );
  media.addEventListener("change", (event) => {
    if (event.matches) finish();
  });
})();
