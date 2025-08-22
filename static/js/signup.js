async function signup(event) {
    if (event) {
        event.preventDefault();
    }
    const first_name = document.getElementById("first_name").value;
    const last_name = document.getElementById("last_name").value;
    const email = document.getElementById("email").value;
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    const response = await fetch("/signup", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ first_name, last_name, email, username, password })
    });

    if (response.ok) {
        const data = await response.json();
        alert("Signup successful!");
        console.log(data);
    } else {
        const error = await response.text();
        alert("Signup failed: " + error);
    }
}