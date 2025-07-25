import {loadAccountPage} from './account.js'

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

        console.log("Stored token:", localStorage.getItem("access_token"));

        if (data.access_token) {
            // Save Token in storage
            localStorage.setItem("access_token", data.access_token);

            console.log("Access Token:", data.access_token);

            alert("Login successful!");

            // Small delay
            setTimeout(() => {
                loadAccountPage() ;
                //window.location.href = "/items";
            }, 200);
        } else {
            alert("Login succeeded but no token received.");
        }
    } else {
        alert("Login failed.");
    }
}

window.login =login;