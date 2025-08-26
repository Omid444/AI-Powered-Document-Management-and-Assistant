// static/js/account.js
console.log("✅ account.js loaded!");

// Accept messages only from these origins (dev + prod). Add yours.
const ALLOWED_ORIGINS = [
  window.location.origin,      // same-origin
  "http://localhost:8000",
  "http://127.0.0.1:8000",
  // "https://YOUR_DOMAIN",
];

let navLock = false;
let currentNavAbort = null;

// ---------- helpers ----------
function getToken() {
  try { return localStorage.getItem("access_token"); } catch { return null; }
}

function lockNav() {
  navLock = true;
  document.body.style.pointerEvents = "none"; // optional
}
function unlockNav() {
  navLock = false;
  document.body.style.pointerEvents = "";
}

async function fetchWithAuth(url, signal) {
  const token = getToken();
  if (!token) {
    alert("No token found. Please login.");
    location.href = "/";
    throw new Error("No token");
  }
  const res = await fetch(url, { method: "GET", headers: { Authorization: `Bearer ${token}` }, signal });
  if (res.status === 401 || res.status === 403) {
    alert("Session expired. Please login again.");
    localStorage.removeItem("access_token");
    location.href = "/";
    throw new Error("Unauthorized");
  }
  if (!res.ok) throw new Error("HTTP " + res.status);
  return res.text();
}

function replaceDocument(html) {
  document.open();
  document.write(html);
  document.close();
}

// Compute the real origin of an iframe from its src (works cross-origin)
function getIframeOrigin(iframe) {
  try {
    // if src is relative, URL(..., location.href) resolves it to absolute
    return new URL(iframe.getAttribute("src"), window.location.href).origin;
  } catch {
    return window.location.origin; // fallback
  }
}

/**
 * Proactively send token to the iframe:
 * - compute targetOrigin from iframe.src
 * - retry a few times
 * - send again on iframe 'load'
 */
function sendTokenToIframe(iframe) {
  const tk = getToken();
  if (!iframe || !tk) return;

  const targetOrigin = getIframeOrigin(iframe);
  let tries = 0, maxTries = 8;

  const tick = () => {
    tries++;
    if (iframe.contentWindow) {
      iframe.contentWindow.postMessage({ token: tk }, targetOrigin);
      // console.log("📨 posted token to", targetOrigin, "try", tries);
    }
    if (tries < maxTries) setTimeout(tick, 150);
  };
  tick();

  iframe.addEventListener("load", () => {
    iframe.contentWindow?.postMessage({ token: tk }, targetOrigin);
    // console.log("📨 posted token to", targetOrigin, "onload");
  }, { once: true });
}

// ---------- message handshake (reply to iframe) ----------
window.addEventListener("message", (event) => {
  if (!ALLOWED_ORIGINS.includes(event.origin)) return;
  const data = event.data || {};

  if (data && data.requestToken) {
    const tk = getToken();
    if (tk && event.source) {
      // reply directly to the asking frame with its own origin
      event.source.postMessage({ token: tk }, event.origin);
      // console.log("🔁 replied with token to", event.origin);
    }
    return;
  }

  if (data && data.toggle) {
    const iframeEl = document.querySelector(".chatbot-frame");
    const btn = document.getElementById("open-chatbot-button");
    if (iframeEl && btn) { iframeEl.classList.toggle("close"); btn.classList.toggle("close"); }
  }
}, true);

// Also try at DOM ready (handles first load and re-renders)
document.addEventListener("DOMContentLoaded", () => {
  const iframe = document.querySelector(".chatbot-frame");
  if (iframe) sendTokenToIframe(iframe);
});

// ---------- navigation ----------
async function goToDashboard() {
  if (navLock) return;
  if (currentNavAbort) currentNavAbort.abort();
  currentNavAbort = new AbortController();
  lockNav();
  try {
    const html = await fetchWithAuth("/dashboard", currentNavAbort.signal);
    replaceDocument(html);
    try { if (location.pathname !== "/dashboard") history.pushState({}, "", "/dashboard"); } catch {}
  } finally { unlockNav(); }
}

export async function loadAccountPage() {
  if (navLock) return;
  if (currentNavAbort) currentNavAbort.abort();
  currentNavAbort = new AbortController();
  lockNav();
  try {
    const html = await fetchWithAuth("/account", currentNavAbort.signal);
    replaceDocument(html);
    try { if (location.pathname !== "/account") history.pushState({}, "", "/account"); } catch {}

    // After DOM is replaced, send token to the new iframe
    const iframe = document.querySelector(".chatbot-frame");
    if (iframe) sendTokenToIframe(iframe);

    // Re-bind open button if you use it
    const openChatbotButton = document.getElementById("open-chatbot-button");
    if (openChatbotButton && iframe) {
      openChatbotButton.addEventListener("click", () => {
        iframe.classList.remove("close");
        openChatbotButton.classList.remove("close");
      });
    }
  } finally { unlockNav(); }
}

// expose for inline HTML
window.goDashboard = (evt) => { evt?.preventDefault?.(); evt?.stopPropagation?.(); goToDashboard().catch(console.error); };
window.mylog       = (evt) => { evt?.preventDefault?.(); evt?.stopPropagation?.(); loadAccountPage().catch(console.error); };

// intercept clicks to avoid full-page navigation
document.addEventListener("click", (e) => {
  const dash = e.target.closest('a[href="/dashboard"], #dashboard-link, [data-nav="dashboard"]');
  if (dash) { e.preventDefault(); e.stopPropagation(); window.goDashboard(); return; }
  const home = e.target.closest('a[href="/account"], #home-link, [data-nav="account"]');
  if (home) { e.preventDefault(); e.stopPropagation(); window.mylog(); }
}, true);
