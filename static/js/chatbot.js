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

      fetch("/api/chat", {
        method: "POST",
        headers: {
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
