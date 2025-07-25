export async function loadAccountPage() {
    const token = localStorage.getItem("access_token");
    console.log("Stored token:", localStorage.getItem("access_token"));
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