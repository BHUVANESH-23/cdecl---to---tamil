document.getElementById("converterForm").addEventListener("submit", function (e) {
    e.preventDefault();

    const query = document.getElementById("query").value;
    fetch("/", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ query: query })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            document.getElementById("output").textContent = data.output;
        }
    })
    .catch(error => console.error("Error:", error));
});
