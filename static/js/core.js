(function () {
    const root = document.documentElement;
    const themeToggle = document.querySelector(".theme-toggle");
    const themeIcon = themeToggle ? themeToggle.querySelector("i") : null;
    const storedTheme = localStorage.getItem("portfolio-theme");

    function setTheme(theme) {
        root.setAttribute("data-theme", theme);
        localStorage.setItem("portfolio-theme", theme);
        if (themeIcon) {
            themeIcon.className = theme === "dark" ? "bi bi-moon-stars" : "bi bi-sun";
        }
    }

    setTheme(storedTheme || "dark");

    if (themeToggle) {
        themeToggle.addEventListener("click", function () {
            const nextTheme = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
            setTheme(nextTheme);
        });
    }

    const timeNode = document.querySelector(".header-time");

    function updateTime() {
        if (!timeNode) {
            return;
        }

        const timeZone = timeNode.dataset.timezone || "UTC";
        timeNode.textContent = new Intl.DateTimeFormat("en-GB", {
            timeZone: timeZone,
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
            hour12: false,
        }).format(new Date());
    }

    updateTime();
    window.setInterval(updateTime, 1000);

    const revealObserver = new IntersectionObserver(
        function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add("is-visible");
                    revealObserver.unobserve(entry.target);
                }
            });
        },
        { threshold: 0.12 }
    );

    document.querySelectorAll(".reveal").forEach(function (node) {
        revealObserver.observe(node);
    });

    const sectionLinks = Array.from(document.querySelectorAll(".nav-cluster .nav-link[href^='#']"));
    const sections = sectionLinks
        .map(function (link) {
            return document.querySelector(link.getAttribute("href"));
        })
        .filter(Boolean);

    const tocObserver = new IntersectionObserver(
        function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    sectionLinks.forEach(function (link) {
                        link.classList.toggle("active", link.getAttribute("href") === "#" + entry.target.id);
                    });
                }
            });
        },
        { rootMargin: "-40% 0px -50% 0px" }
    );

    sections.forEach(function (section) {
        tocObserver.observe(section);
    });

    document
        .querySelectorAll(".timeline-item, .compact-item, .skill-item, .project-card, .contact-form")
        .forEach(function (node) {
            node.addEventListener("pointermove", function (event) {
                const rect = node.getBoundingClientRect();
                const x = ((event.clientX - rect.left) / rect.width) * 100;
                const y = ((event.clientY - rect.top) / rect.height) * 100;

                node.style.setProperty("--mouse-x", x + "%");
                node.style.setProperty("--mouse-y", y + "%");
            });
        });
})();
