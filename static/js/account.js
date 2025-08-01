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
    
    const iframe = document.querySelector(".chatbot-frame");
    const openChatbotButton = document.getElementById("open-chatbot-button");

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
