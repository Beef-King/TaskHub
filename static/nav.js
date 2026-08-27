// Toggles the mobile nav dropdown open/closed, and closes it
// automatically if the user taps outside it or resizes back to desktop.
document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.getElementById("navToggle");
    const nav = document.getElementById("thNav");

    if (!toggle || !nav) return;

    function closeNav() {
        nav.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
    }

    function openNav() {
        nav.classList.add("open");
        toggle.setAttribute("aria-expanded", "true");
    }

    toggle.addEventListener("click", () => {
        const isOpen = nav.classList.contains("open");
        isOpen ? closeNav() : openNav();
    });

    // Close when a nav link is tapped
    nav.querySelectorAll("a").forEach(link => {
        link.addEventListener("click", closeNav);
    });

    // Close if the window is resized back up to desktop width
    window.addEventListener("resize", () => {
        if (window.innerWidth > 760) closeNav();
    });

    // Close if a tap/click happens outside the nav or toggle button
    document.addEventListener("click", (e) => {
        if (!nav.contains(e.target) && !toggle.contains(e.target)) {
            closeNav();
        }
    });
});
