login:
async function login(event) {
    if (event) {
        event.preventDefault();
    }

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    const response = await fetch("/login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ email, password })
    });

    if (response.ok) {
        const data = await response.json();
        console.log("Response data:", data);
        console.log("About to store token:", data.access_token);

        localStorage.setItem("access_token", data.access_token);

        console.log("Stored token:", localStorage.getItem("access_token"));

        if (data.access_token) {
            // Save Token in storage
            localStorage.setItem("access_token", data.access_token);

            console.log("Access Token:", data.access_token);

            alert("Login successful!");

            // Small delay
            setTimeout(() => {
                window.location.href = "/account";
            }, 200);
        } else {
            alert("Login succeeded but no token received.");
        }
    } else {
        alert("Login failed.");
    }
}

accout:
document.addEventListener("DOMContentLoaded", () => {
    loadAccountPage();
});

async function loadAccountPage() {
    const token = localStorage.getItem("access_token");
    console.log("Sending token:", token);

    if (!token) {
        alert("No token found. Please login.");
        window.location.href = "/";
        return;
    }

    try {
        const response = await fetch("/account", {
            method: "GET",
            headers: {
                "Authorization": `Bearer ${token}`

            }
        });

        if (!response.ok) {
            throw new Error("Unauthorized");
        }

        const html = await response.text();

        document.open();
        document.write(html);
        document.close();

    } catch (error) {
        console.error("Access denied:", error);
        alert("Access denied. Please login again.");
        window.location.href = "/";
    }
}
