(function () {
    "use strict";

    const INPUT_ID = "id_profile_picture";
    const CROP_SIZE = 260;
    const OUTPUT_SIZE = 512;

    function clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }

    function initProfileCrop() {
        const input = document.getElementById(INPUT_ID);
        if (!input || input.dataset.profileCropReady === "1") {
            return;
        }

        input.dataset.profileCropReady = "1";
        input.setAttribute("accept", "image/*");

        const panel = document.createElement("div");
        panel.className = "profile-crop-panel";
        panel.hidden = true;
        panel.innerHTML = [
            '<div class="profile-crop-layout">',
            '<canvas class="profile-crop-canvas" width="' + CROP_SIZE + '" height="' + CROP_SIZE + '" aria-label="Profile crop area"></canvas>',
            '<div class="profile-crop-controls">',
            '<label for="profile-crop-zoom">Zoom</label>',
            '<input id="profile-crop-zoom" type="range" min="1" max="3" step="0.01" value="1">',
            '<img class="profile-crop-preview" alt="Circular profile preview">',
            '<p class="profile-crop-note">Drag the image and zoom it until the circular preview shows the exact profile area. The saved image is cropped to a square for the site avatar.</p>',
            '</div>',
            '</div>'
        ].join("");

        input.insertAdjacentElement("afterend", panel);

        const canvas = panel.querySelector(".profile-crop-canvas");
        const zoom = panel.querySelector("#profile-crop-zoom");
        const preview = panel.querySelector(".profile-crop-preview");
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
            targetContext.fillStyle = "#111";
            targetContext.fillRect(0, 0, size, size);
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
                    zoom.max = String(Math.max(state.minScale * 3, state.minScale + 1));
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

        const form = input.closest("form");
        let submitter = null;

        if (form) {
            form.addEventListener("click", function (event) {
                const button = event.target.closest('input[type="submit"], button[type="submit"]');
                if (button) {
                    submitter = button;
                }
            });

            form.addEventListener("submit", function (event) {
                if (!state.image || !state.needsCrop || form.dataset.profileCropDone === "1") {
                    return;
                }

                event.preventDefault();
                const output = document.createElement("canvas");
                output.width = OUTPUT_SIZE;
                output.height = OUTPUT_SIZE;
                draw(output, OUTPUT_SIZE);

                output.toBlob(function (blob) {
                    if (!blob || typeof DataTransfer === "undefined") {
                        form.dataset.profileCropDone = "1";
                        form.submit();
                        return;
                    }

                    const original = input.files[0];
                    const extension = blob.type === "image/png" ? "png" : "jpg";
                    const baseName = original.name.replace(/\.[^.]+$/, "") || "profile";
                    const croppedFile = new File([blob], baseName + "-cropped." + extension, { type: blob.type });
                    const transfer = new DataTransfer();
                    transfer.items.add(croppedFile);
                    input.files = transfer.files;

                    if (submitter && submitter.name) {
                        const hiddenSubmit = document.createElement("input");
                        hiddenSubmit.type = "hidden";
                        hiddenSubmit.name = submitter.name;
                        hiddenSubmit.value = submitter.value || "1";
                        form.appendChild(hiddenSubmit);
                    }

                    form.dataset.profileCropDone = "1";
                    form.submit();
                }, "image/jpeg", 0.92);
            });
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initProfileCrop);
    } else {
        initProfileCrop();
    }
})();
