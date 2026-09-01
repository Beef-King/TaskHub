if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
        navigator.serviceWorker.register("/static/sw.js")
            .then(registration => {
                console.log("TaskHub service worker registered:", registration.scope);
            })
            .catch(error => {
                console.error("Service worker registration failed:", error);
            });
    });
}