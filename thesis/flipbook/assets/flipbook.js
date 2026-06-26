/* Let Me Explain! — thesis flipbook viewer (StPageFlip, MIT).
   Supports an optional encrypted mode: when window.FLIPBOOK_CONFIG.encrypted is
   true, the book is built only after the password gate decrypts the assets
   in-browser (see crypto.js + enc.json). Plaintext mode behaves as before. */
(function () {
  "use strict";

  var CFG = window.FLIPBOOK_CONFIG || {};
  var ENC = !!CFG.encrypted;

  // ---- page model (openright parity; covers are thesis.pdf p1 / p291) ----
  var INTERIOR = 288;                 // PDF pages 3..290
  var COVER_FRONT = 0, INSIDE_FRONT = 1, FIRST = 2;
  var LAST = FIRST + INTERIOR - 1;    // 289
  var INSIDE_BACK = LAST + 1;         // 290
  var COVER_BACK = LAST + 2;          // 291
  var TOTAL = COVER_BACK + 1;         // 292
  var EAGER = 5;
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var pad = function (n) { return String(n).padStart(3, "0"); };
  function isCover(i) { return i === COVER_FRONT || i === COVER_BACK; }
  function isInside(i) { return i === INSIDE_FRONT || i === INSIDE_BACK; }
  function pageSrc(i) {
    if (i === COVER_FRONT) return "pages/page-001.webp";
    if (i === COVER_BACK) return "pages/page-291.webp";
    if (isInside(i)) return "pages/page-inside.webp";
    return "pages/page-" + pad(i + 1) + ".webp";
  }
  function thumbSrc(i) {
    if (i === COVER_FRONT) return "thumbs/page-001.webp";
    if (i === COVER_BACK) return "thumbs/page-291.webp";
    if (isInside(i)) return "thumbs/page-inside.webp";
    return "thumbs/page-" + pad(i + 1) + ".webp";
  }
  var OVERVIEW = "assets/wrap-overview.webp";

  // In encrypted mode, decrypted assets live here:
  var BLOBS = {};        // relative path -> blob: URL
  var TOCDATA = null;    // decrypted TOC array (plaintext mode fetches instead)
  var KEY = null;        // ENC: derived key (in memory only) for lazy thumb decrypt
  var THUMBFILES = [];   // ENC: thumbnail paths, decrypted only when the grid opens
  var thumbsDone = false;
  function assetURL(p) { return ENC ? (BLOBS[p] || "") : p; }

  var $ = function (id) { return document.getElementById(id); };
  var bookEl = $("flipbook");
  var loadingEl = $("fb-loading");
  var counterEl = $("fb-counter");
  var sliderEl = $("fb-slider");
  var overlayEl = $("fb-overlay");
  var drawer = $("fb-drawer"), gridView = $("fb-gridview"), zoomModal = $("fb-zoommodal"), intro = $("fb-intro");
  var tocList = $("fb-toc-list");

  var pageFlip = null;
  var tocEntries = [];

  function label(i) {
    if (i === COVER_FRONT) return "Front cover";
    if (i === COVER_BACK) return "Back cover";
    if (isInside(i)) return "Inside cover";
    return "Page " + (i - 1) + " of " + INTERIOR;
  }
  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c];
    });
  }
  function syncUI(i) { counterEl.textContent = label(i); sliderEl.value = i; markCurrent(i); }
  function markCurrent(i) {
    var items = tocList.querySelectorAll(".fb-toc-item");
    var bestPage = -1;
    tocEntries.forEach(function (e) { if (e.page <= i && e.page > bestPage) bestPage = e.page; });
    items.forEach(function (el) { el.classList.toggle("is-current", parseInt(el.dataset.page, 10) === bestPage); });
    var cells = $("fb-grid-cells").children;
    for (var k = 0; k < cells.length; k++) cells[k].classList.toggle("is-current", k === i);
  }
  function next() { if (pageFlip) pageFlip.flipNext(); }
  function prev() { if (pageFlip) pageFlip.flipPrev(); }
  function jumpTo(i) { if (!pageFlip) return; i = Math.max(0, Math.min(TOTAL - 1, i)); pageFlip.turnToPage(i); syncUI(i); history.replaceState(null, "", "?page=" + i); }
  function currentIndex() { try { return pageFlip.getCurrentPageIndex(); } catch (e) { return parseInt(sliderEl.value, 10) || 0; } }

  // ---- TOC ----
  function renderToc(data) {
    tocEntries = data;
    data.forEach(function (e) {
      if (e.level === 0) { var h = document.createElement("li"); h.className = "fb-toc-part"; h.textContent = e.title; tocList.appendChild(h); }
      var li = document.createElement("li"); li.className = "fb-toc-item"; li.dataset.page = e.page;
      li.innerHTML = '<span>' + escapeHtml(e.title) + '</span><span class="pg">' + e.page + '</span>';
      li.addEventListener("click", function () { jumpTo(parseInt(li.dataset.page, 10)); closeAll(); });
      tocList.appendChild(li);
    });
  }
  function loadToc() {
    if (ENC) { if (TOCDATA) renderToc(TOCDATA); return; }
    fetch("data/toc.json").then(function (r) { return r.json(); }).then(renderToc).catch(function () {});
  }

  // ---- thumbnail grid ----
  var gridBuilt = false;
  function buildGrid() {
    if (gridBuilt) return; gridBuilt = true;
    var frag = document.createDocumentFragment();
    for (var i = 0; i < TOTAL; i++) {
      (function (idx) {
        var cell = document.createElement("div"); cell.className = "fb-cell";
        var t = document.createElement("img"); t.src = assetURL(thumbSrc(idx)); t.loading = "lazy"; t.alt = label(idx);
        var cap = document.createElement("span"); cap.textContent = idx === COVER_FRONT ? "Cover" : idx === COVER_BACK ? "Back" : isInside(idx) ? "Inside" : (idx - 1);
        cell.appendChild(t); cell.appendChild(cap);
        cell.addEventListener("click", function () { jumpTo(idx); closeAll(); });
        frag.appendChild(cell);
      })(i);
    }
    $("fb-grid-cells").appendChild(frag);
  }
  // ENC: thumbnails are decrypted lazily, only when the page grid is first opened.
  function ensureThumbs() {
    if (!ENC || thumbsDone || !KEY || !THUMBFILES.length) { thumbsDone = true; return Promise.resolve(); }
    return mapLimit(THUMBFILES, 6, async function (path) {
      var r = await fetch("enc/" + path + ".enc");
      if (!r.ok) return;
      var plain = await FlipCrypto.decrypt(KEY, new Uint8Array(await r.arrayBuffer()));
      BLOBS[path] = URL.createObjectURL(new Blob([plain], { type: "image/webp" }));
    }).then(function () { thumbsDone = true; });
  }

  // ---- overlays ----
  function showOverlay() { overlayEl.hidden = false; }
  function closeAll() {
    drawer.classList.remove("is-open"); drawer.setAttribute("aria-hidden", "true");
    gridView.classList.remove("is-open"); gridView.setAttribute("aria-hidden", "true");
    zoomModal.classList.remove("is-open"); zoomModal.setAttribute("aria-hidden", "true");
    overlayEl.hidden = true;
    $("fb-toc").classList.remove("is-active"); $("fb-toc").setAttribute("aria-expanded", "false");
    $("fb-grid").classList.remove("is-active");
  }
  function openDrawer() { closeAll(); drawer.classList.add("is-open"); drawer.setAttribute("aria-hidden", "false"); $("fb-toc").classList.add("is-active"); $("fb-toc").setAttribute("aria-expanded", "true"); showOverlay(); }
  function openGrid() { closeAll(); gridView.classList.add("is-open"); gridView.setAttribute("aria-hidden", "false"); $("fb-grid").classList.add("is-active"); ensureThumbs().then(buildGrid); }
  function openZoom() { var i = currentIndex(); $("fb-zoom-img").src = assetURL(pageSrc(i)); closeAll(); zoomModal.classList.add("is-open"); zoomModal.setAttribute("aria-hidden", "false"); }
  function showIntro() { intro.classList.add("is-open"); intro.setAttribute("aria-hidden", "false"); }
  function hideIntro() { intro.classList.remove("is-open"); intro.setAttribute("aria-hidden", "true"); try { sessionStorage.setItem("fb-intro-seen", "1"); } catch (e) {} }

  // ---- static control wiring (handlers guard on pageFlip until booted) ----
  $("fb-next").addEventListener("click", next);
  $("fb-prev").addEventListener("click", prev);
  $("fb-edge-next").addEventListener("click", next);
  $("fb-edge-prev").addEventListener("click", prev);
  sliderEl.addEventListener("input", function () { var v = parseInt(sliderEl.value, 10); if (pageFlip) pageFlip.turnToPage(v); counterEl.textContent = label(v); });
  $("fb-toc").addEventListener("click", function () { drawer.classList.contains("is-open") ? closeAll() : openDrawer(); });
  $("fb-grid").addEventListener("click", function () { gridView.classList.contains("is-open") ? closeAll() : openGrid(); });
  $("fb-zoom").addEventListener("click", openZoom);
  $("fb-drawer-close").addEventListener("click", closeAll);
  $("fb-grid-close").addEventListener("click", closeAll);
  $("fb-zoom-close").addEventListener("click", closeAll);
  overlayEl.addEventListener("click", closeAll);
  bookEl.addEventListener("dblclick", openZoom);
  $("fb-full").addEventListener("click", function () {
    var el = document.documentElement;
    if (!document.fullscreenElement) { (el.requestFullscreen || el.webkitRequestFullscreen || function () {}).call(el); }
    else { (document.exitFullscreen || document.webkitExitFullscreen || function () {}).call(document); }
  });
  $("fb-intro-enter").addEventListener("click", hideIntro);
  $("fb-intro-img").addEventListener("click", hideIntro);
  intro.addEventListener("click", function (e) { if (e.target === intro) hideIntro(); });
  $("fb-cover").addEventListener("click", showIntro);
  document.addEventListener("keydown", function (e) {
    if (e.target && /^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName)) return;
    if (!pageFlip) return;
    switch (e.key) {
      case "ArrowRight": case " ": case "PageDown": next(); e.preventDefault(); break;
      case "ArrowLeft": case "PageUp": prev(); e.preventDefault(); break;
      case "Home": jumpTo(COVER_FRONT); break;
      case "End": jumpTo(COVER_BACK); break;
      case "t": case "T": drawer.classList.contains("is-open") ? closeAll() : openDrawer(); break;
      case "g": case "G": gridView.classList.contains("is-open") ? closeAll() : openGrid(); break;
      case "z": case "Z": zoomModal.classList.contains("is-open") ? closeAll() : openZoom(); break;
      case "f": case "F": $("fb-full").click(); break;
      case "c": case "C": intro.classList.contains("is-open") ? hideIntro() : showIntro(); break;
      case "Escape": closeAll(); hideIntro(); break;
    }
  });
  var rT;
  window.addEventListener("resize", function () { clearTimeout(rT); rT = setTimeout(function () { try { pageFlip.update(); } catch (e) {} }, 150); });

  // ---- boot: build the book (immediately in plaintext, post-unlock when encrypted) ----
  function boot() {
    for (var i = 0; i < TOTAL; i++) {
      var cover = isCover(i);
      var page = document.createElement("div");
      page.className = "page" + (cover ? " page--cover" : "");
      if (cover) page.setAttribute("data-density", "hard");
      var img = document.createElement("img");
      img.className = "page-img";
      img.src = assetURL(pageSrc(i));
      img.alt = label(i);
      img.decoding = "async";
      if (!ENC && i >= EAGER && i < COVER_BACK) img.loading = "lazy";
      page.appendChild(img);
      bookEl.appendChild(page);
    }
    var Ctor = (window.St && window.St.PageFlip) || window.PageFlip;
    pageFlip = new Ctor(bookEl, {
      width: 1171, height: 1654, size: "stretch",
      minWidth: 280, maxWidth: 1100, minHeight: 396, maxHeight: 1554,
      drawShadow: true, maxShadowOpacity: 0.5, showCover: true, usePortrait: true,
      mobileScrollSupport: true, useMouseEvents: true,
      flippingTime: reduceMotion ? 0 : 800, swipeDistance: 24, showPageCorners: true, autoSize: true
    });
    pageFlip.loadFromHTML(document.querySelectorAll("#flipbook .page"));

    var coverImg = bookEl.querySelector(".page-img");
    var hideLoader = function () { loadingEl.classList.add("is-hidden"); };
    if (coverImg && coverImg.complete) hideLoader();
    else if (coverImg) coverImg.addEventListener("load", hideLoader, { once: true });
    window.addEventListener("load", hideLoader);
    setTimeout(hideLoader, 1800);

    pageFlip.on("flip", function (e) { var i = e.data; syncUI(i); history.replaceState(null, "", "?page=" + i); });

    var introImg = $("fb-intro-img"); if (introImg) introImg.src = assetURL(OVERVIEW);
    loadToc();

    var params = new URLSearchParams(location.search);
    var startPage = parseInt(params.get("page"), 10);
    if (!isNaN(startPage) && startPage >= 0) {
      setTimeout(function () { jumpTo(startPage); }, 120);
    } else {
      syncUI(0);
      var seen; try { seen = sessionStorage.getItem("fb-intro-seen"); } catch (e) {}
      if (!seen) showIntro();
    }
  }

  // ---- encryption gate (only active when ENC) ----
  function mapLimit(items, limit, fn) {
    return new Promise(function (resolve, reject) {
      var idx = 0, active = 0, done = 0, failed = false;
      function pump() {
        if (failed) return;
        if (done === items.length) { resolve(); return; }
        while (active < limit && idx < items.length) {
          (function (it) {
            active++;
            fn(it).then(function () { active--; done++; pump(); }).catch(function (err) { failed = true; reject(err); });
          })(items[idx++]);
        }
      }
      pump();
    });
  }
  function initGate() {
    var gate = $("fb-gate"), input = $("fb-gate-pw"), form = $("fb-gate-form"), err = $("fb-gate-err"), prog = $("fb-gate-prog");
    if (!window.FlipCrypto || !(window.crypto && window.crypto.subtle)) {
      err.textContent = "This browser can't decrypt (needs HTTPS + WebCrypto).";
    }
    gate.classList.add("is-open"); gate.setAttribute("aria-hidden", "false");
    setTimeout(function () { try { input.focus(); } catch (e) {} }, 60);
    var busy = false;
    async function attempt(ev) {
      if (ev) ev.preventDefault();
      if (busy) return;
      var pw = input.value; if (!pw) { err.textContent = "Enter the password."; return; }
      busy = true; input.disabled = true; err.textContent = "";
      try {
        var man = await fetch("enc.json").then(function (r) { return r.json(); });
        var salt = FlipCrypto.b64ToBytes(man.salt);
        var key = await FlipCrypto.deriveKey(pw, salt, man.iterations);
        var ok = await FlipCrypto.verify(key, man.verifier);
        if (!ok) { err.textContent = "Wrong password."; busy = false; input.disabled = false; input.select(); return; }
        KEY = key;
        THUMBFILES = man.files.filter(function (f) { return f.indexOf("thumbs/") === 0; });
        var eager = man.files.filter(function (f) { return f.indexOf("thumbs/") !== 0; }); // pages + toc + overview
        prog.style.display = "block";
        var total = eager.length, count = 0;
        await mapLimit(eager, 6, async function (path) {
          var r = await fetch("enc/" + path + ".enc");
          if (!r.ok) throw new Error("missing " + path);
          var plain = await FlipCrypto.decrypt(key, new Uint8Array(await r.arrayBuffer()));
          if (path === "data/toc.json") { TOCDATA = JSON.parse(new TextDecoder().decode(plain)); }
          else { var mime = path.indexOf(".webp") >= 0 ? "image/webp" : "application/octet-stream"; BLOBS[path] = URL.createObjectURL(new Blob([plain], { type: mime })); }
          count++; prog.textContent = "Decrypting… " + Math.round(count / total * 100) + "%";
        });
        gate.classList.remove("is-open"); gate.setAttribute("aria-hidden", "true");
        boot();
      } catch (e) {
        err.textContent = "Could not unlock — " + (e && e.message || "error");
        busy = false; input.disabled = false; prog.style.display = "none";
      }
    }
    form.addEventListener("submit", attempt);
  }

  // ---- start ----
  if (ENC) initGate(); else boot();
})();
