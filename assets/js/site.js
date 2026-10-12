(function () {
  "use strict";

  var REPO = "agentx-icu/toxee";
  var RELEASES_URL = "https://github.com/" + REPO + "/releases";

  // Used until (or instead of, when GitHub is unreachable) the live release
  // lookup below. Update alongside each toxee release.
  var FALLBACK = {
    version: "0.3.1",
    tag: "v0.3.1",
    date: "2026-09-16",
    assets: {
      "Android-arm64.apk": [69756642, "1b8b1a579468ca9adf5a5688712d2da9b85d0bea3b6f4ea1addd63053ce7e38c"],
      "Darwin-arm64.pkg": [47223406, "efee003b8eee16cb674ab5c1466d137c21bc5021212e9096f5c69b019798b3b3"],
      "Darwin-x86_64.pkg": [47405904, "1571ede00598ba6c86f471563a8075c093226aebd3fd86059d120c33309463a2"],
      "Linux-aarch64.deb": [23274150, "fe04babc28a41253c2411acb72e15952797136b5c8ebbc6b48d4d985cdab9ee9"],
      "Linux-aarch64.rpm": [17861133, "ce4e9ec708603d022849ce255777a98e46ca2d3a6b14f2c16e65fb0d6519b338"],
      "Linux-x86_64.deb": [24134980, "11a14214fbd47f5020c1488bbe1b8d7272393300e85f3f8771d9de0092ceaae8"],
      "Linux-x86_64.rpm": [18866481, "1e3576b5f42bf7ee0a5288e7b2abd53e471cfa6d5293100eff88797c23654a8d"],
      "Windows-AMD64.msi": [30104276, "cfe33b509a7b61f12df1fe688d36fcd9f5ba661e5635505ce34bd5927b2ee0de"],
      "Windows-ARM64.msi": [29928147, "d0af41c8134cabafae471bbd627bb62402be99f261ec48732b9ec6aa62c9ba41"]
    }
  };

  var root = document.documentElement;
  // Pages under /en/ and /zh/ are pinned to one language and sit one level deep.
  var pageLang = root.getAttribute("data-page-lang");
  var base = root.getAttribute("data-base") || "";
  var release = null;

  function $(sel, ctx) { return (ctx || document).querySelector(sel); }
  function $$(sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); }
  function lang() { return root.getAttribute("data-lang") === "zh" ? "zh" : "en"; }

  /* ---------------- language ---------------- */

  var TITLES = {
    en: "toxee — Serverless, private, peer-to-peer chat",
    zh: "toxee — 无服务器、真隐私的点对点聊天"
  };

  function applyLang(l) {
    root.setAttribute("data-lang", l);
    root.lang = l === "zh" ? "zh-Hans" : "en";
    document.title = TITLES[l];
    $$("img[data-shot]").forEach(function (img) {
      img.src = base + "assets/img/" + l + "/" + img.getAttribute("data-shot");
    });
    $$("[data-alt-en]").forEach(function (el) {
      el.setAttribute("alt", el.getAttribute("data-alt-" + l));
    });
    $$("[data-aria-en]").forEach(function (el) {
      el.setAttribute("aria-label", el.getAttribute("data-aria-" + l));
    });
    try { localStorage.setItem("toxee_lang", l); } catch (e) {}
    renderRelease();
  }

  $$(".lang-toggle").forEach(function (b) {
    b.addEventListener("click", function () {
      var next = lang() === "zh" ? "en" : "zh";
      if (pageLang) {
        try { localStorage.setItem("toxee_lang", next); } catch (e) {}
        location.href = base + next + "/" + location.hash;
        return;
      }
      applyLang(next);
    });
  });

  /* ---------------- mobile menu ---------------- */

  // Below 1060px the section links fold into a menu button.
  var nav = $(".nav"), menuBtn = document.getElementById("menuBtn");
  if (nav && menuBtn) {
    var setMenu = function (open) {
      nav.classList.toggle("open", open);
      menuBtn.setAttribute("aria-expanded", open ? "true" : "false");
    };
    menuBtn.hidden = false;
    menuBtn.addEventListener("click", function () { setMenu(!nav.classList.contains("open")); });
    $$("#navLinks a").forEach(function (a) { a.addEventListener("click", function () { setMenu(false); }); });
    document.addEventListener("click", function (e) { if (!nav.contains(e.target)) setMenu(false); });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && nav.classList.contains("open")) { setMenu(false); menuBtn.focus(); }
    });
    window.matchMedia("(min-width: 1061px)").addEventListener("change", function () { setMenu(false); });
  }

  /* ---------------- screenshot viewer ---------------- */

  // Screenshots open full size in a <dialog>; arrows and swipes step through
  // the group (one gallery pane or one feature figure) the image belongs to.
  var shots = $$(".gallery img, .duo img, .phone-duo img");
  if (shots.length && window.HTMLDialogElement) {
    var box = document.createElement("dialog");
    box.className = "lightbox";
    box.innerHTML = '<figure><img alt=""><figcaption></figcaption></figure>' +
      '<button type="button" class="lb-btn lb-close">\u00d7</button>' +
      '<button type="button" class="lb-btn lb-prev">\u2039</button><button type="button" class="lb-btn lb-next">\u203a</button>';
    document.body.appendChild(box);
    var boxImg = $("img", box), boxCap = $("figcaption", box), group = [], at = 0;
    // The caption is the image's alt text, or else its figure's visible caption.
    var caption = function (img) {
      var fig = img.closest("figure"), cap = fig && $("figcaption", fig);
      return img.alt || (cap ? cap.innerText.trim() : "");
    };
    var show = function (i) {
      at = (i + group.length) % group.length;
      boxImg.src = group[at].currentSrc || group[at].src;
      boxImg.alt = caption(group[at]);
      boxCap.textContent = boxImg.alt;
      box.classList.toggle("single", group.length < 2);
    };
    var step = function (d) { if (group.length > 1) show(at + d); };
    shots.forEach(function (img) {
      img.tabIndex = 0;
      img.setAttribute("role", "button");
      var open = function () {
        group = $$("img", img.closest(".gallery, .duo, .phone-duo"));
        show(group.indexOf(img));
        var zh = lang() === "zh";
        $(".lb-close", box).setAttribute("aria-label", zh ? "关闭" : "Close");
        $(".lb-prev", box).setAttribute("aria-label", zh ? "上一张" : "Previous");
        $(".lb-next", box).setAttribute("aria-label", zh ? "下一张" : "Next");
        box.showModal();
      };
      img.addEventListener("click", open);
      img.addEventListener("keydown", function (e) {
        if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(); }
      });
    });
    $(".lb-close", box).addEventListener("click", function () { box.close(); });
    $(".lb-prev", box).addEventListener("click", function () { step(-1); });
    $(".lb-next", box).addEventListener("click", function () { step(1); });
    box.addEventListener("click", function (e) { if (e.target === box || e.target.tagName === "FIGURE") box.close(); });
    box.addEventListener("keydown", function (e) {
      if (e.key === "ArrowRight") step(1);
      else if (e.key === "ArrowLeft") step(-1);
    });
    var x0 = null;
    box.addEventListener("touchstart", function (e) { x0 = e.touches[0].clientX; }, { passive: true });
    box.addEventListener("touchend", function (e) {
      if (x0 === null) return;
      var dx = e.changedTouches[0].clientX - x0;
      x0 = null;
      if (Math.abs(dx) > 40) step(dx < 0 ? 1 : -1);
    });
  }

  /* ---------------- tabs ---------------- */

  $$("[role=tablist]").forEach(function (list) {
    var tabs = $$("[role=tab]", list);
    function select(tab) {
      tabs.forEach(function (t) {
        var on = t === tab;
        t.setAttribute("aria-selected", on ? "true" : "false");
        t.tabIndex = on ? 0 : -1;
        var p = document.getElementById(t.getAttribute("aria-controls"));
        if (p) p.hidden = !on;
      });
    }
    tabs.forEach(function (t, i) {
      t.addEventListener("click", function () { select(t); });
      t.addEventListener("keydown", function (e) {
        var d = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
        if (!d) return;
        var n = tabs[(i + d + tabs.length) % tabs.length];
        select(n); n.focus(); e.preventDefault();
      });
    });
    list._select = function (key) {
      var t = tabs.filter(function (x) { return x.getAttribute("data-key") === key; })[0];
      if (t) select(t);
    };
  });

  /* ---------------- copy ---------------- */

  var toast = $(".toast");
  function flash(msgEn, msgZh) {
    if (!toast) return;
    toast.textContent = lang() === "zh" ? msgZh : msgEn;
    toast.classList.add("show");
    clearTimeout(flash._t);
    flash._t = setTimeout(function () { toast.classList.remove("show"); }, 1600);
  }
  function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(text);
    var ta = document.createElement("textarea");
    ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0";
    document.body.appendChild(ta); ta.select();
    var ok = false;
    try { ok = document.execCommand("copy"); } catch (e) {} finally { document.body.removeChild(ta); }
    return ok ? Promise.resolve() : Promise.reject(new Error("copy failed"));
  }
  $$(".term").forEach(function (pre) {
    var b = document.createElement("button");
    b.className = "copy"; b.type = "button"; b.textContent = "copy";
    b.addEventListener("click", function () {
      var clone = pre.cloneNode(true);
      $$(".copy", clone).forEach(function (x) { x.remove(); });
      var lines = clone.textContent.split("\n").filter(function (l) { return l.trim() && l.trim().charAt(0) !== "#"; });
      copyText(lines.join("\n").replace(/^\$ /gm, "")).then(
        function () { flash("Copied", "已复制"); },
        function () { flash("Couldn't copy, select the text instead", "复制失败，请手动选择文本"); }
      );
    });
    pre.appendChild(b);
  });

  /* ---------------- platform detection ---------------- */

  function detect() {
    var ua = navigator.userAgent || "";
    var p = (navigator.userAgentData && navigator.userAgentData.platform) || navigator.platform || "";
    var os = null, arch = null;
    if (/android/i.test(ua)) os = "android";
    else if (/iphone|ipad|ipod/i.test(ua) || (/Mac/.test(p) && navigator.maxTouchPoints > 1)) os = "ios";
    else if (/win/i.test(p) || /windows/i.test(ua)) os = "windows";
    else if (/mac/i.test(p)) os = "macos";
    else if (/linux|x11|cros/i.test(p + ua)) os = "linux";
    if (/aarch64|arm64/i.test(ua)) arch = "arm";
    return { os: os, arch: arch };
  }

  var plat = detect();

  function pickPkg() {
    switch (plat.os) {
      case "windows": return plat.arch === "arm" ? "Windows-ARM64.msi" : "Windows-AMD64.msi";
      // Safari and Firefox don't reveal the Mac's CPU, so only pick when we know.
      case "macos": return plat.arch === "x86" ? "Darwin-x86_64.pkg" : plat.arch === "arm" ? "Darwin-arm64.pkg" : null;
      case "linux": return plat.arch === "arm" ? "Linux-aarch64.deb" : "Linux-x86_64.deb";
      case "android": return "Android-arm64.apk";
      default: return null;
    }
  }

  var PKG_LABEL = {
    "Windows-AMD64.msi": ["Windows (x64)", "Windows (x64)"],
    "Windows-ARM64.msi": ["Windows (ARM64)", "Windows (ARM64)"],
    "Darwin-arm64.pkg": ["macOS (Apple silicon)", "macOS (Apple 芯片)"],
    "Darwin-x86_64.pkg": ["macOS (Intel)", "macOS (Intel)"],
    "Linux-x86_64.deb": ["Linux (.deb, x86_64)", "Linux (.deb, x86_64)"],
    "Linux-aarch64.deb": ["Linux (.deb, ARM64)", "Linux (.deb, ARM64)"],
    "Android-arm64.apk": ["Android (APK)", "Android (APK)"]
  };

  // Chromium exposes the CPU architecture; refine the guess when it is available.
  if (navigator.userAgentData && navigator.userAgentData.getHighEntropyValues) {
    navigator.userAgentData.getHighEntropyValues(["architecture"]).then(function (v) {
      if (v.architecture === "arm") plat.arch = "arm";
      else if (v.architecture === "x86") plat.arch = "x86";
      renderRelease();
    }).catch(function () {});
  }

  if (plat.os) {
    var card = document.getElementById("os-" + plat.os);
    if (card) card.classList.add("hl");
    var guide = $("#guide-tabs");
    if (guide && guide._select) guide._select(plat.os);
  }

  /* ---------------- release data ---------------- */

  function fmtSize(b) {
    return b >= 1048576 ? (b / 1048576).toFixed(1) + " MB" : Math.max(1, Math.round(b / 1024)) + " KB";
  }
  // Install-guide commands name the package that fits this machine.
  function fileFor(kind) {
    var arm = plat.arch === "arm";
    switch (kind) {
      case "windows": return arm ? "Windows-ARM64.msi" : "Windows-AMD64.msi";
      case "linux-deb": return arm ? "Linux-aarch64.deb" : "Linux-x86_64.deb";
      case "linux-rpm": return arm ? "Linux-aarch64.rpm" : "Linux-x86_64.rpm";
      default: return kind;
    }
  }

  function fileName(key) { return "toxee-" + release.version + "-" + key; }
  function url(key) {
    return RELEASES_URL + "/download/" + release.tag + "/" + fileName(key);
  }

  function renderRelease() {
    if (!release) return;
    var zh = lang() === "zh";

    $$("[data-pkg]").forEach(function (a) {
      var key = a.getAttribute("data-pkg");
      var info = release.assets[key];
      if (!info) { a.hidden = true; return; }
      a.hidden = false;
      a.href = url(key);
      var f = $(".pf", a); if (f) f.textContent = fileName(key);
      var s = $(".ps", a); if (s) s.textContent = fmtSize(info[0]);
    });
    $$("[data-file]").forEach(function (el) { el.textContent = fileName(fileFor(el.getAttribute("data-file"))); });
    $$("[data-version]").forEach(function (el) { el.textContent = "v" + release.version; });
    $$("[data-release-date]").forEach(function (el) { el.textContent = release.date; });
    $$("[data-release-link]").forEach(function (el) { el.href = RELEASES_URL + "/tag/" + release.tag; });
    $$("[data-sums-link]").forEach(function (el) { el.href = RELEASES_URL + "/download/" + release.tag + "/SHA256SUMS.txt"; });

    var sums = $("#sums");
    if (sums) {
      sums.textContent = Object.keys(release.assets).sort().map(function (k) {
        return (release.assets[k][1] || "(see SHA256SUMS.txt)") + "  " + fileName(k);
      }).join("\n");
    }

    var hero = $("#hero-dl");
    if (hero) {
      var key = pickPkg();
      var label = $(".hero-dl-label", hero);
      var sub = $(".hero-dl-sub", hero);
      if (key && release.assets[key]) {
        hero.href = url(key);
        label.textContent = (zh ? "下载 " : "Download for ") + PKG_LABEL[key][zh ? 1 : 0];
        sub.textContent = "v" + release.version + " · " + fmtSize(release.assets[key][0]);
      } else {
        hero.href = "#download";
        if (plat.os === "macos") {
          hero.href = "#os-macos";
          label.textContent = zh ? "下载 macOS 版" : "Download for macOS";
          sub.textContent = "v" + release.version + (zh ? " · Apple 芯片 / Intel" : " · Apple silicon / Intel");
        } else {
          label.textContent = plat.os === "ios"
            ? (zh ? "iOS 版本获取方式" : "Getting toxee on iOS")
            : (zh ? "下载 toxee" : "Download toxee");
          sub.textContent = "v" + release.version + (zh ? " · 全部平台" : " · all platforms");
        }
      }
    }
    var other = $("#hero-other-mac");
    if (other) {
      var picked = pickPkg();
      var otherKey = picked === "Darwin-x86_64.pkg" ? "Darwin-arm64.pkg" : "Darwin-x86_64.pkg";
      // Only offer the other Mac build when the hero already links one and the other exists.
      other.hidden = plat.os !== "macos" || !picked || !release.assets[picked] || !release.assets[otherKey];
      var a = $("a", other);
      if (a) {
        a.href = url(otherKey);
        a.textContent = PKG_LABEL[otherKey][zh ? 1 : 0];
      }
    }
  }

  function parseRelease(r) {
    var version = String(r.tag_name || "").replace(/^v/, "");
    var assets = {};
    (r.assets || []).forEach(function (a) {
      var m = /^toxee-(.+?)-((?:Android|Darwin|Linux|Windows)-[^.]+\.(?:apk|pkg|deb|rpm|msi))$/.exec(a.name);
      if (!m || m[1] !== version) return;
      var sha = typeof a.digest === "string" && a.digest.indexOf("sha256:") === 0 ? a.digest.slice(7) : "";
      assets[m[2]] = [a.size, sha];
    });
    if (!version || !Object.keys(assets).length) return null;
    return {
      version: version,
      tag: r.tag_name,
      date: String(r.published_at || "").slice(0, 10),
      assets: assets
    };
  }

  release = FALLBACK;

  var saved = null;
  try { saved = localStorage.getItem("toxee_lang"); } catch (e) {}
  applyLang(pageLang || root.getAttribute("data-lang") || saved || "en");

  if (window.fetch) {
    fetch("https://api.github.com/repos/" + REPO + "/releases/latest", {
      headers: { Accept: "application/vnd.github+json" }
    }).then(function (res) {
      return res.ok ? res.json() : null;
    }).then(function (r) {
      var live = r && parseRelease(r);
      if (live) { release = live; renderRelease(); }
    }).catch(function () { /* keep the bundled fallback */ });
  }
})();
