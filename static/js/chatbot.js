console.log("✅ Chatbot.js loaded!");
console.log("✅ Iframe:", window.location.origin);

let token = null; // توکن به عنوان یک متغیر سراسری تعریف می‌شود.

// این شنونده پیام به محض دریافت توکن، آن را ذخیره می‌کند.
window.addEventListener("message", (event) => {
  // اگر event.data وجود داشته باشد و شامل توکن باشد.
  if (event.data && event.data.token) {
    token = event.data.token;
    console.log("✅ Token received from parent:", token);
    localStorage.setItem("access_token", token);
  }
});

document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector(".chat-form");
  const input = document.querySelector(".message-input");
  const chatBody = document.querySelector(".chat-body");

  const attachButton = document.querySelector(".chat-controls button:nth-child(2)");
  const sendButton = document.querySelector(".chat-controls button:nth-child(3)");

  // اینجا، قبل از اضافه کردن شنونده، مطمئن می‌شویم که دکمه وجود دارد.
  const closeButton = document.getElementById("close-chatbot");
  if (closeButton) {
      console.log("✅ Close button found. Attaching click listener.");
      // ارسال پیام باز/بستن به parent (account.html)
      closeButton.addEventListener("click", () => {
          // مطمئن می‌شویم که پنجره والد وجود دارد
          if (window.parent) {
            window.parent.postMessage({ toggle: true }, "*");
          }
      });
  } else {
      console.error("❌ Close button not found!");
  }


  // افزودن پیام کاربر
  function addUserMessage(message) {
    const msgDiv = document.createElement("div");
    msgDiv.classList.add("message", "user-message");

    const textDiv = document.createElement("div");
    textDiv.classList.add("text");
    textDiv.textContent = message;

    msgDiv.appendChild(textDiv);
    chatBody.appendChild(msgDiv);
    scrollToBottom();
  }

  // افزودن پاسخ چت‌بات
  function addBotMessage(message) {
    const msgDiv = document.createElement("div");
    msgDiv.classList.add("message", "bot-message");

    const textDiv = document.createElement("div");
    textDiv.classList.add("text");
    textDiv.textContent = message;

    msgDiv.appendChild(textDiv);
    chatBody.appendChild(msgDiv);
    scrollToBottom();
  }

  function scrollToBottom() {
    chatBody.scrollTop = chatBody.scrollHeight;
  }

  // ارسال پیام به سرور
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const message = input.value.trim();
    if (message !== "") {
      addUserMessage(message);
      input.value = "";

      // ❗ نکته مهم: در اینجا از متغیر سراسری token استفاده می‌شود.
      // همچنین یک بررسی وجود دارد تا مطمئن شویم توکن خالی نیست.
      if (!token) {
          console.error("❌ Token not available. Cannot send message.");
          addBotMessage("❌: خطا: توکن احراز هویت در دسترس نیست. لطفا صفحه را رفرش کنید.");
          return;
      }

      fetch("/api/chat", {
        method: "POST",
        headers: {
           Authorization: `Bearer ${token}`,
           "Content-Type": "application/json"
        },
        body: JSON.stringify({ message: message })
      })
      .then(res => {
        if (!res.ok) throw new Error("پاسخ نامعتبر از سرور");
        return res.json();
      })
      .then(data => {
        if (data.reply) {
          addBotMessage(data.reply);
        } else {
          addBotMessage("🤖: پاسخی از سرور دریافت نشد.");
        }
      })
      .catch(err => {
        console.error("خطا:", err);
        addBotMessage("❌ خطا در ارتباط با سرور.");
      });
    }
  });

  // دکمه فایل هنوز پیاده‌سازی نشده
  attachButton.addEventListener("click", () => {
    alert("🚧 انتخاب فایل هنوز پیاده‌سازی نشده.");
  });
});
