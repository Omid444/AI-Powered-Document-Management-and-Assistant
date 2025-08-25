
//console.log("✅ account.js loaded!");
//
//function mylog(){
//console.log("✅ test ");
//}
//export async function loadAccountPage() {
//  const token = localStorage.getItem("access_token");
//  if (!token) {
//    alert("No token found. Please login.");
//    window.location.href = "/";
//    return;
//  }
//
//  try {
//    const response = await fetch("/account", {
//      method: "GET",
//      headers: {
//        Authorization: `Bearer ${token}`
//      }
//    });
//
//    if (!response.ok) throw new Error("Unauthorized");
//
//    const html = await response.text();
//    document.open();
//    document.write(html);
//    document.close();
//
//    // دریافت ارجاع به iframe و دکمه جدید
//    const iframe = document.querySelector(".chatbot-frame");
//    const openChatbotButton = document.getElementById("open-chatbot-button");
//
//    // 👇 تغییرات برای ارسال مطمئن‌تر توکن
//    if (iframe && iframe.contentWindow && token) {
//        console.log("✅ Attempting to send token with a small delay.");
//        // یک تأخیر کوتاه اضافه می‌کنیم تا iframe کاملاً آماده دریافت پیام شود.
//        setTimeout(() => {
//            iframe.contentWindow.postMessage({ token: token }, "*");
//            console.log("✅ Token sent to iframe via postMessage with a small delay");
//        }, 200); // 100ms تأخیر
//    }
//
//    // همچنان شنونده load را به عنوان یک راه حل پشتیبان نگه می‌داریم.
//    iframe.addEventListener("load", () => {
//        if (token && iframe.contentWindow) {
//            iframe.contentWindow.postMessage({ token: token }, "*");
//            console.log("✅ Token sent to iframe via postMessage on load event");
//        }
//    });
//
//    // 👇 بخش اول: شنونده برای پیام‌های ارسالی از داخل iframe
//    window.addEventListener("message", (event) => {
//      if (event.data && event.data.toggle) {
//        console.log("✔️ Message received from chatbot! Toggling iframe class.");
//        if (iframe) {
//            iframe.classList.toggle("close");
//            openChatbotButton.classList.toggle("close");
//        } else {
//            console.error("❌ Chatbot iframe not found in the DOM.");
//        }
//      }
//    });
//
//    // 👇 بخش دوم: شنونده برای کلیک روی دکمه باز کردن چت‌بات
//    if (openChatbotButton) {
//        openChatbotButton.addEventListener("click", () => {
//            console.log("✔️ Open button clicked! Maximizing chatbot.");
//            iframe.classList.remove("close");
//            openChatbotButton.classList.remove("close");
//        });
//    }
//
//  } catch (error) {
//    console.error("Access denied:", error);
//    alert("Access denied. Please login again.");
//    window.location.href = "/";
//  }
//}
//
//// In static/js/account.js
//
//function getToken() {
//  return localStorage.getItem("access_token");
//}
//
//async function fetchWithAuth(url) {
//  const token = getToken();
//  if (!token) {
//    alert("No token found. Please login.");
//    window.location.href = "/";
//    throw new Error("No token");
//  }
//  const res = await fetch(url, {
//    method: "GET",
//    headers: { Authorization: `Bearer ${token}` }
//  });
//  if (res.status === 401 || res.status === 403) {
//    alert("Session expired. Please login again.");
//    localStorage.removeItem("access_token");
//    window.location.href = "/";
//    throw new Error("Unauthorized");
//  }
//  if (!res.ok) {
//    alert("An error occurred. Please try again.");
//    throw new Error("HTTP " + res.status);
//  }
//  return res.text();
//}
//
//function replaceDocument(html) {
//  document.open();
//  document.write(html);
//  document.close();
//}
//
//// Make it available to inline HTML
//window.goDashboard = async function (evt) {
//  if (evt?.preventDefault) evt.preventDefault();
//  const html = await fetchWithAuth("/dashboard");
//  replaceDocument(html);
//  try {
//    if (location.pathname !== "/dashboard") history.pushState({}, "", "/dashboard");
//  } catch {}
//};


/////////////////////////////////////////////
//// static/js/dashboard.js
//console.log("✅ dashboard.js loaded!");
//
//const TARGET_ORIGIN = window.location.origin;
//
//function getToken() {
//  return localStorage.getItem("access_token");
//}
//
//async function fetchWithAuth(url) {
//  const token = getToken();
//  if (!token) {
//    alert("No token found. Please login.");
//    window.location.href = "/";
//    throw new Error("No token");
//  }
//  const res = await fetch(url, {
//    method: "GET",
//    headers: { Authorization: `Bearer ${token}` }
//  });
//
//  if (res.status === 401 || res.status === 403) {
//    alert("Session expired. Please login again.");
//    localStorage.removeItem("access_token");
//    window.location.href = "/";
//    throw new Error("Unauthorized");
//  }
//  if (!res.ok) {
//    alert("An error occurred. Please try again.");
//    throw new Error("HTTP " + res.status);
//  }
//  return res.text();
//}
//
//function replaceDocument(html) {
//  document.open();
//  document.write(html);
//  document.close();
//}
//
///** بعد از بازنویسی سند، اگر در صفحهٔ account باشیم، توکن را به iframe چت‌بات بفرستیم */
//function initChatbotTokenIfExists() {
//  const token = getToken();
//  const iframe = document.querySelector(".chatbot-frame");
//  if (!iframe || !token) return;
//
//  const send = () => {
//    if (iframe.contentWindow) {
//      iframe.contentWindow.postMessage({ token }, TARGET_ORIGIN);
//      console.log("✅ Token sent to chatbot iframe");
//    }
//  };
//  // کمی تأخیر تا iframe آماده شود
//  setTimeout(send, 200);
//  iframe.addEventListener("load", send);
//}
//
//async function go(url, pushPath, afterRender) {
//  const html = await fetchWithAuth(url);
//  replaceDocument(html);
//  if (typeof afterRender === "function") {
//    try { afterRender(); } catch (e) { console.error(e); }
//  }
//  try {
//    if (pushPath && window.location.pathname !== pushPath) {
//      history.pushState({}, "", pushPath);
//    }
//  } catch {}
//}
//
//// ——— توابع عمومی برای HTML اینلاین
//window.mylog = function (evt) {
//  if (evt?.preventDefault) evt.preventDefault();
//  // می‌رویم به /account با هدر و بعد از رندر، توکن را به iframe بفرستیم
//  go("/account", "/account", initChatbotTokenIfExists);
//};
//
//window.goDashboard = function (evt) {
//  if (evt?.preventDefault) evt.preventDefault();
//  // می‌رویم به /dashboard با هدر
//  go("/dashboard", "/dashboard");
//};