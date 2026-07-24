document.addEventListener("DOMContentLoaded", () => {
    const animatedItems = document.querySelectorAll(
        ".card, .table-container, .empty-state, .form-container, .article-page"
    );

    if ("IntersectionObserver" in window) {
        const observer = new IntersectionObserver(
            entries => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add("is-visible");
                        observer.unobserve(entry.target);
                    }
                });
            },
            {
                threshold: 0.12
            }
        );

        animatedItems.forEach(item => {
            item.classList.add("scroll-reveal");
            observer.observe(item);
        });
    } else {
        animatedItems.forEach(item => {
            item.classList.add("is-visible");
        });
    }

    document.querySelectorAll(".btn, .button, button").forEach(button => {
        button.addEventListener("pointerdown", event => {
            const ripple = document.createElement("span");
            const rect = button.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);

            ripple.className = "button-ripple";
            ripple.style.width = `${size}px`;
            ripple.style.height = `${size}px`;
            ripple.style.left = `${event.clientX - rect.left - size / 2}px`;
            ripple.style.top = `${event.clientY - rect.top - size / 2}px`;

            button.appendChild(ripple);

            window.setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });
});
