console.log("✅ account.js loaded!");

export async function loadAccountPage() {
  const token = localStorage.getItem("access_token");
  if (!token) {
    alert("No token found. Please login.");
    window.location.href = "/";
    return;
  }

  try {
    const response = await fetch("/account", {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`
      }
    });

    if (!response.ok) throw new Error("Unauthorized");

    const html = await response.text();
    document.open();
    document.write(html);
    document.close();

    // دریافت ارجاع به iframe و دکمه جدید
    const iframe = document.querySelector(".chatbot-frame");
    const openChatbotButton = document.getElementById("open-chatbot-button");

    // 👇 تغییرات برای ارسال مطمئن‌تر توکن
    if (iframe && iframe.contentWindow && token) {
        console.log("✅ Attempting to send token with a small delay.");
        // یک تأخیر کوتاه اضافه می‌کنیم تا iframe کاملاً آماده دریافت پیام شود.
        setTimeout(() => {
            iframe.contentWindow.postMessage({ token: token }, "*");
            console.log("✅ Token sent to iframe via postMessage with a small delay");
        }, 200); // 100ms تأخیر
    }

    // همچنان شنونده load را به عنوان یک راه حل پشتیبان نگه می‌داریم.
    iframe.addEventListener("load", () => {
        if (token && iframe.contentWindow) {
            iframe.contentWindow.postMessage({ token: token }, "*");
            console.log("✅ Token sent to iframe via postMessage on load event");
        }
    });

    // 👇 بخش اول: شنونده برای پیام‌های ارسالی از داخل iframe
    window.addEventListener("message", (event) => {
      if (event.data && event.data.toggle) {
        console.log("✔️ Message received from chatbot! Toggling iframe class.");
        if (iframe) {
            iframe.classList.toggle("close");
            openChatbotButton.classList.toggle("close");
        } else {
            console.error("❌ Chatbot iframe not found in the DOM.");
        }
      }
    });

    // 👇 بخش دوم: شنونده برای کلیک روی دکمه باز کردن چت‌بات
    if (openChatbotButton) {
        openChatbotButton.addEventListener("click", () => {
            console.log("✔️ Open button clicked! Maximizing chatbot.");
            iframe.classList.remove("close");
            openChatbotButton.classList.remove("close");
        });
    }

  } catch (error) {
    console.error("Access denied:", error);
    alert("Access denied. Please login again.");
    window.location.href = "/";
  }
}
