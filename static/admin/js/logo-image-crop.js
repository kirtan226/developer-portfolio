(function () {
    "use strict";

    const CROP_SIZE = 180;
    const OUTPUT_SIZE = 512;

    function clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }

    function isLogoInput(input) {
        return input
            && input.type === "file"
            && (
                input.name === "logo"
                || input.name === "company_logo"
                || input.name.endsWith("-logo")
                || input.name.endsWith("-company_logo")
            );
    }

    function createCropper(input) {
        if (
            !isLogoInput(input)
            || input.dataset.logoCropReady === "1"
            || input.closest(".empty-form")
        ) {
            return null;
        }

        input.dataset.logoCropReady = "1";
        input.setAttribute("accept", "image/*");

        const panel = document.createElement("div");
        panel.className = "logo-crop-panel";
        panel.hidden = true;
        panel.innerHTML = [
            '<div class="logo-crop-layout">',
            '<canvas class="logo-crop-canvas" width="' + CROP_SIZE + '" height="' + CROP_SIZE + '" aria-label="Logo crop area"></canvas>',
            '<div class="logo-crop-controls">',
            '<label>Zoom</label>',
            '<input type="range" min="1" max="3" step="0.01" value="1">',
            '<div class="logo-crop-preview"><img alt="Logo preview"></div>',
            '<p class="logo-crop-note">Drag and zoom the logo. The saved file is a square PNG that matches the site logo display.</p>',
            '</div>',
            '</div>'
        ].join("");

        input.insertAdjacentElement("afterend", panel);

        const canvas = panel.querySelector(".logo-crop-canvas");
        const zoom = panel.querySelector('input[type="range"]');
        const preview = panel.querySelector(".logo-crop-preview img");
        const state = {
            image: null,
            scale: 1,
            minScale: 1,
            offsetX: 0,
            offsetY: 0,
            dragging: false,
            lastX: 0,
            lastY: 0,
            needsCrop: false
        };

        function clampOffsets() {
            if (!state.image) {
                return;
            }

            const width = state.image.width * state.scale;
            const height = state.image.height * state.scale;

            state.offsetX = width <= CROP_SIZE
                ? (CROP_SIZE - width) / 2
                : clamp(state.offsetX, CROP_SIZE - width, 0);
            state.offsetY = height <= CROP_SIZE
                ? (CROP_SIZE - height) / 2
                : clamp(state.offsetY, CROP_SIZE - height, 0);
        }

        function draw(targetCanvas, size) {
            if (!state.image) {
                return;
            }

            const targetContext = targetCanvas.getContext("2d");
            const ratio = size / CROP_SIZE;
            targetContext.clearRect(0, 0, size, size);
            targetContext.drawImage(
                state.image,
                state.offsetX * ratio,
                state.offsetY * ratio,
                state.image.width * state.scale * ratio,
                state.image.height * state.scale * ratio
            );
        }

        function render() {
            draw(canvas, CROP_SIZE);
            preview.src = canvas.toDataURL("image/png");
        }

        function loadImage(file) {
            if (!file || !file.type.startsWith("image/")) {
                panel.hidden = true;
                state.image = null;
                state.needsCrop = false;
                return;
            }

            const reader = new FileReader();
            reader.addEventListener("load", function () {
                const image = new Image();
                image.addEventListener("load", function () {
                    state.image = image;
                    state.minScale = Math.max(CROP_SIZE / image.width, CROP_SIZE / image.height);
                    state.scale = state.minScale;
                    state.offsetX = (CROP_SIZE - image.width * state.scale) / 2;
                    state.offsetY = (CROP_SIZE - image.height * state.scale) / 2;
                    state.needsCrop = true;

                    zoom.min = String(state.minScale);
                    zoom.max = String(Math.max(state.minScale * 4, state.minScale + 1));
                    zoom.value = String(state.scale);
                    panel.hidden = false;
                    clampOffsets();
                    render();
                });
                image.src = reader.result;
            });
            reader.readAsDataURL(file);
        }

        input.addEventListener("change", function () {
            loadImage(input.files && input.files[0]);
        });

        zoom.addEventListener("input", function () {
            if (!state.image) {
                return;
            }

            const previousScale = state.scale;
            const centerX = CROP_SIZE / 2;
            const centerY = CROP_SIZE / 2;
            state.scale = Number(zoom.value);
            state.offsetX = centerX - ((centerX - state.offsetX) / previousScale) * state.scale;
            state.offsetY = centerY - ((centerY - state.offsetY) / previousScale) * state.scale;
            clampOffsets();
            render();
        });

        canvas.addEventListener("pointerdown", function (event) {
            if (!state.image) {
                return;
            }

            state.dragging = true;
            state.lastX = event.clientX;
            state.lastY = event.clientY;
            canvas.setPointerCapture(event.pointerId);
        });

        canvas.addEventListener("pointermove", function (event) {
            if (!state.dragging) {
                return;
            }

            state.offsetX += event.clientX - state.lastX;
            state.offsetY += event.clientY - state.lastY;
            state.lastX = event.clientX;
            state.lastY = event.clientY;
            clampOffsets();
            render();
        });

        canvas.addEventListener("pointerup", function () {
            state.dragging = false;
        });

        canvas.addEventListener("pointercancel", function () {
            state.dragging = false;
        });

        return {
            input: input,
            state: state,
            crop: function () {
                return new Promise(function (resolve) {
                    if (!state.image || !state.needsCrop) {
                        resolve();
                        return;
                    }

                    const output = document.createElement("canvas");
                    output.width = OUTPUT_SIZE;
                    output.height = OUTPUT_SIZE;
                    draw(output, OUTPUT_SIZE);
                    output.toBlob(function (blob) {
                        if (!blob || typeof DataTransfer === "undefined") {
                            resolve();
                            return;
                        }

                        const original = input.files[0];
                        const baseName = original.name.replace(/\.[^.]+$/, "") || "logo";
                        const croppedFile = new File([blob], baseName + "-cropped.png", { type: "image/png" });
                        const transfer = new DataTransfer();
                        transfer.items.add(croppedFile);
                        input.files = transfer.files;
                        state.needsCrop = false;
                        resolve();
                    }, "image/png");
                });
            }
        };
    }

    function initLogoCroppers() {
        const croppers = [];

        function scan(root) {
            if (isLogoInput(root)) {
                const cropper = createCropper(root);
                if (cropper) {
                    croppers.push(cropper);
                }
            }

            root.querySelectorAll('input[type="file"]').forEach(function (input) {
                const cropper = createCropper(input);
                if (cropper) {
                    croppers.push(cropper);
                }
            });
        }

        scan(document);

        const observer = new MutationObserver(function (mutations) {
            mutations.forEach(function (mutation) {
                mutation.addedNodes.forEach(function (node) {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        scan(node);
                    }
                });
            });
        });
        observer.observe(document.body, { childList: true, subtree: true });

        const form = document.querySelector("form");
        if (!form) {
            return;
        }

        let submitter = null;
        form.addEventListener("click", function (event) {
            const button = event.target.closest('input[type="submit"], button[type="submit"]');
            if (button) {
                submitter = button;
            }
        });

        form.addEventListener("submit", function (event) {
            const pending = croppers.filter(function (cropper) {
                return cropper.state.needsCrop;
            });

            if (!pending.length || form.dataset.logoCropDone === "1") {
                return;
            }

            event.preventDefault();
            Promise.all(pending.map(function (cropper) {
                return cropper.crop();
            })).then(function () {
                if (submitter && submitter.name) {
                    const hiddenSubmit = document.createElement("input");
                    hiddenSubmit.type = "hidden";
                    hiddenSubmit.name = submitter.name;
                    hiddenSubmit.value = submitter.value || "1";
                    form.appendChild(hiddenSubmit);
                }

                form.dataset.logoCropDone = "1";
                form.submit();
            });
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initLogoCroppers);
    } else {
        initLogoCroppers();
    }
})();
