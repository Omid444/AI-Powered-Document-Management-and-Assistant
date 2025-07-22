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
        body: JSON.stringify({email, password })
    });

    if (response.ok) {
        const data = await response.json();
        alert("login successful!");
        console.log(data);
    } else {
        const error = await response.text();
        alert("login failed: " + error);
    }
}