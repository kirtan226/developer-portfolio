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

    function setActiveSection() {
        const scrollPosition = window.scrollY;
        const activationPoint = scrollPosition + Math.min(window.innerHeight * 0.35, 240);
        let activeSection = sections[0];

        sections.forEach(function (section) {
            if (section.offsetTop <= activationPoint) {
                activeSection = section;
            }
        });

        sectionLinks.forEach(function (link) {
            link.classList.toggle("active", link.getAttribute("href") === "#" + activeSection.id);
        });
    }

    setActiveSection();
    window.addEventListener("scroll", setActiveSection, { passive: true });
    window.addEventListener("resize", setActiveSection);

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

    const contactForm = document.querySelector(".contact-form");
    const contactStatus = document.querySelector("[data-contact-status]");

    function validateContactForm(form) {
        const rules = {
            name: {
                max: 24,
                empty: "Please fill name.",
                tooLong: "Name should be 24 characters or less.",
            },
            email: {
                max: 35,
                empty: "Please fill email.",
                tooLong: "Email should be 35 characters or less.",
                invalid: "Please enter a valid email.",
            },
            subject: {
                max: 55,
                empty: "Please fill subject.",
                tooLong: "Subject should be 55 characters or less.",
            },
            message: {
                max: 355,
                empty: "Please fill message.",
                tooLong: "Message should be 355 characters or less.",
            },
        };
        const errors = {};

        Object.keys(rules).forEach(function (name) {
            const field = form.elements[name];
            const value = field ? field.value.trim() : "";
            const rule = rules[name];

            if (!value) {
                errors[name] = rule.empty;
            } else if (value.length > rule.max) {
                errors[name] = rule.tooLong;
            } else if (name === "email" && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
                errors[name] = rule.invalid;
            }
        });

        return errors;
    }

    function showContactFieldErrors(form, errors) {
        form.querySelectorAll("[data-error-for]").forEach(function (node) {
            node.textContent = errors[node.dataset.errorFor] || "";
        });

        ["name", "email", "subject", "message"].forEach(function (name) {
            const field = form.elements[name];
            if (field) {
                field.classList.toggle("is-invalid", Boolean(errors[name]));
            }
        });
    }

    function showContactStatus(type, message, autoHide) {
        if (!contactStatus) {
            return;
        }

        contactStatus.textContent = message;
        contactStatus.className = "contact-status contact-status-" + type;

        if (autoHide) {
            window.setTimeout(function () {
                contactStatus.className = "contact-status d-none";
                contactStatus.textContent = "";
            }, 5000);
        }
    }

    function setContactLoading(button, isLoading) {
        if (!button) {
            return;
        }

        button.disabled = isLoading;
        button.classList.toggle("is-loading", isLoading);
        const label = button.querySelector("span");
        if (label) {
            label.textContent = isLoading ? "Sending" : "Send Message";
        }
    }

    if (contactForm) {
        ["name", "email", "subject", "message"].forEach(function (name) {
            const field = contactForm.elements[name];

            if (!field) {
                return;
            }

            field.addEventListener("input", function () {
                const errors = validateContactForm(contactForm);
                showContactFieldErrors(contactForm, errors);

                if (!Object.keys(errors).length && contactStatus && contactStatus.classList.contains("contact-status-error")) {
                    contactStatus.className = "contact-status d-none";
                    contactStatus.textContent = "";
                }
            });
        });

        contactForm.addEventListener("submit", function (event) {
            event.preventDefault();

            const submitButton = contactForm.querySelector("button[type='submit']");
            const errors = validateContactForm(contactForm);
            showContactFieldErrors(contactForm, errors);

            if (Object.keys(errors).length) {
                showContactStatus("error", "Please fix the highlighted fields.", false);
                return;
            }

            setContactLoading(submitButton, true);

            fetch(contactForm.dataset.ajaxUrl || contactForm.getAttribute("action"), {
                method: "POST",
                body: new FormData(contactForm),
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                    "Accept": "application/json",
                },
            })
                .then(function (response) {
                    return response.json().catch(function () {
                        throw new Error("The server returned an invalid response.");
                    });
                })
                .then(function (data) {
                    if (data.ok) {
                        contactForm.reset();
                        showContactFieldErrors(contactForm, {});
                        showContactStatus("success", data.message || "Your message has been sent.", true);
                    } else {
                        showContactFieldErrors(contactForm, data.errors || {});
                        showContactStatus("error", data.message || "Please fix the highlighted fields.", false);
                    }
                })
                .catch(function (error) {
                    showContactStatus("error", "Your message could not be sent: " + error.message, false);
                })
                .finally(function () {
                    setContactLoading(submitButton, false);
                });
        });
    }
})();
