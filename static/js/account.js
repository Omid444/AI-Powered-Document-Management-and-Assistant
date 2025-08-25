
console.log("✅ account.js loaded!");

let navLock = false;
let currentNavAbort = null;

function getToken() {
  return localStorage.getItem("access_token");
}

function lockNav() {
  navLock = true;
  // اختیاری: غیرفعال کردن لینک‌ها تا پایان ناوبری
  document.body.style.pointerEvents = "none";
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
  const res = await fetch(url, {
    method: "GET",
    headers: { Authorization: `Bearer ${token}` },
    signal
  });
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

// ——— ناوبری امن به /dashboard
async function goToDashboard() {
  if (navLock) return;             // جلوگیری از کلیک‌های پشت‌سرهم
  if (currentNavAbort) currentNavAbort.abort(); // لغو ناوبری قبلی
  currentNavAbort = new AbortController();
  lockNav();
  try {
    const html = await fetchWithAuth("/dashboard", currentNavAbort.signal);
    replaceDocument(html);
    try { if (location.pathname !== "/dashboard") history.pushState({}, "", "/dashboard"); } catch {}
  } finally {
    unlockNav();
  }
}

// ——— ناوبری امن به /account (اگر در همین فایل نیاز دارید)
export async function loadAccountPage() {
  if (navLock) return;
  if (currentNavAbort) currentNavAbort.abort();
  currentNavAbort = new AbortController();
  lockNav();
  try {
    const html = await fetchWithAuth("/account", currentNavAbort.signal);
    replaceDocument(html);
    try { if (location.pathname !== "/account") history.pushState({}, "", "/account"); } catch {}

    // اگر iframe چت‌بات دارید و باید توکن بفرستید:
    const token = getToken();
    const iframe = document.querySelector(".chatbot-frame");
    if (iframe && token) {
      const send = () => {
        if (iframe.contentWindow) {
          iframe.contentWindow.postMessage({ token }, window.location.origin);
          console.log("✅ Token sent to chatbot iframe");
        }
      };
      setTimeout(send, 200);
      iframe.addEventListener("load", send, { once: true });
    }
  } finally {
    unlockNav();
  }
}

// ——— برای inline HTML
window.goDashboard = function (evt) {
  evt?.preventDefault?.();
  evt?.stopPropagation?.();
  goToDashboard().catch(e => console.error(e));
};

window.mylog = function (evt) {
  evt?.preventDefault?.();
  evt?.stopPropagation?.();
  loadAccountPage().catch(e => console.error(e));
};

// ——— Delegation با capture: حتی اگر inline جا بمونه، کلیک را می‌گیریم
document.addEventListener("click", (e) => {
  const aDash = e.target.closest('a[href="/dashboard"], #dashboard-link');
  if (aDash) {
    e.preventDefault();
    e.stopPropagation();
    window.goDashboard();
    return;
  }
  const aHome = e.target.closest('a[href="/account"], #home-link');
  if (aHome) {
    e.preventDefault();
    e.stopPropagation();
    window.mylog();
  }
}, true); // capture=true که از ناوبری عادی جلوتر باشه
