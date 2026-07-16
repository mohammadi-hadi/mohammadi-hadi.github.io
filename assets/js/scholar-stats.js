// Populates citation stats from /assets/data/scholar.json (refreshed daily by
// .github/workflows/scholar.yml). Static numbers in the HTML act as fallback.
(async () => {
  try {
    const res = await fetch("/assets/data/scholar.json", { cache: "no-cache" });
    if (!res.ok) return;
    const d = await res.json();

    const totals = { citations: d.citations, h_index: d.h_index, i10_index: d.i10_index };
    document.querySelectorAll("[data-scholar]").forEach((el) => {
      const v = totals[el.dataset.scholar];
      if (v != null) el.textContent = v.toLocaleString("en");
    });

    document.querySelectorAll("[data-scholar-pub]").forEach((el) => {
      const p = d.publications && d.publications[el.dataset.scholarPub];
      if (p && p.cited_by > 0 && !el.querySelector(".cite-chip")) {
        const chip = document.createElement("span");
        chip.className = "cite-chip";
        chip.textContent = `Cited by ${p.cited_by}`;
        (el.querySelector(".publication-meta") || el.querySelector(".pub-meta") || el).appendChild(chip);
      }
    });

    const cap = document.querySelector("[data-scholar-updated]");
    if (cap && d.fetched_at) {
      const dt = new Date(d.fetched_at).toLocaleDateString("en-GB", {
        day: "numeric",
        month: "short",
        year: "numeric",
      });
      cap.textContent = `updated ${dt}`;
    }
  } catch {
    /* keep static fallback numbers */
  }
})();
