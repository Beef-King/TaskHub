const MOTIVATIONAL_MESSAGES = [
    "Nice work — one more thing off your plate!",
    "You're building momentum. Keep going!",
    "Small steps, big progress. Well done!",
    "That's the way to do it!",
    "Consistency wins. Great job today!",
    "You showed up for yourself — that matters.",
    "Progress, not perfection. Nicely done!",
    "Look at you go — keep the streak alive!",
    "Done is better than perfect. Great job!",
    "Your future self says thank you.",
    "One step closer to your goals!",
    "That's how good habits are built."
];

function showMotivation() {
    const message = MOTIVATIONAL_MESSAGES[Math.floor(Math.random() * MOTIVATIONAL_MESSAGES.length)];

    let toast = document.getElementById("motivationToast");
    if (!toast) {
        toast = document.createElement("div");
        toast.id = "motivationToast";
        toast.className = "motivation-toast";
        document.body.appendChild(toast);
    }

    toast.textContent = message;
    toast.classList.remove("show");
    void toast.offsetWidth; // restart the animation if it's already showing
    toast.classList.add("show");

    clearTimeout(showMotivation._timer);
    showMotivation._timer = setTimeout(() => {
        toast.classList.remove("show");
    }, 2600);
}
