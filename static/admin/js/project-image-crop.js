(function () {
    "use strict";

    const CROP_WIDTH = 320;
    const CROP_HEIGHT = 180;
    const OUTPUT_WIDTH = 1600;
    const OUTPUT_HEIGHT = 900;

    function clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }

    function isProjectImageInput(input) {
        return input
            && input.type === "file"
            && (
                input.name === "cover_image"
                || input.name === "image"
                || input.name.endsWith("-image")
            );
    }

    function shouldPreserveOriginalByDefault(input) {
        return input.name !== "cover_image";
    }

    function createCropper(input) {
        if (
            !isProjectImageInput(input)
            || input.dataset.projectCropReady === "1"
            || input.closest(".empty-form")
        ) {
            return null;
        }

        input.dataset.projectCropReady = "1";
        input.setAttribute("accept", "image/*");

        const panel = document.createElement("div");
        panel.className = "project-crop-panel";
        panel.hidden = true;
        panel.innerHTML = [
            '<div class="project-crop-layout">',
            '<canvas class="project-crop-canvas" width="' + CROP_WIDTH + '" height="' + CROP_HEIGHT + '" aria-label="Project image crop area"></canvas>',
            '<div class="project-crop-controls">',
            '<label>Zoom</label>',
            '<input type="range" min="1" max="3" step="0.01" value="1">',
            '<label class="project-crop-original-option">',
            '<input type="checkbox" class="project-crop-original">',
            '<span>Save full original image instead of 16:9 crop</span>',
            '</label>',
            '<img class="project-crop-preview" alt="Project image preview">',
            '<p class="project-crop-note">For cover images, keep the 16:9 crop. For screenshots, save the full original image when you do not want the sides cut off.</p>',
            '</div>',
            '</div>'
        ].join("");

        const croppedData = document.createElement("input");
        croppedData.type = "hidden";
        croppedData.name = "__cropped_image__" + input.name;

        input.insertAdjacentElement("afterend", croppedData);
        croppedData.insertAdjacentElement("afterend", panel);

        const canvas = panel.querySelector(".project-crop-canvas");
        const zoom = panel.querySelector('input[type="range"]');
        const preserveOriginal = panel.querySelector(".project-crop-original");
        const preview = panel.querySelector(".project-crop-preview");
        preserveOriginal.checked = shouldPreserveOriginalByDefault(input);
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

            state.offsetX = width <= CROP_WIDTH
                ? (CROP_WIDTH - width) / 2
                : clamp(state.offsetX, CROP_WIDTH - width, 0);
            state.offsetY = height <= CROP_HEIGHT
                ? (CROP_HEIGHT - height) / 2
                : clamp(state.offsetY, CROP_HEIGHT - height, 0);
        }

        function draw(targetCanvas, width, height) {
            if (!state.image) {
                return;
            }

            const targetContext = targetCanvas.getContext("2d");
            const ratioX = width / CROP_WIDTH;
            const ratioY = height / CROP_HEIGHT;
            targetContext.clearRect(0, 0, width, height);
            targetContext.fillStyle = "#111";
            targetContext.fillRect(0, 0, width, height);
            targetContext.drawImage(
                state.image,
                state.offsetX * ratioX,
                state.offsetY * ratioY,
                state.image.width * state.scale * ratioX,
                state.image.height * state.scale * ratioY
            );
        }

        function render() {
            draw(canvas, CROP_WIDTH, CROP_HEIGHT);
            preview.src = canvas.toDataURL("image/jpeg", 0.92);
        }

        function loadImage(file) {
            if (!file || !file.type.startsWith("image/")) {
                panel.hidden = true;
                state.image = null;
                state.needsCrop = false;
                croppedData.value = "";
                return;
            }

            const reader = new FileReader();
            reader.addEventListener("load", function () {
                const image = new Image();
                image.addEventListener("load", function () {
                    state.image = image;
                    state.minScale = Math.max(CROP_WIDTH / image.width, CROP_HEIGHT / image.height);
                    state.scale = state.minScale;
                    state.offsetX = (CROP_WIDTH - image.width * state.scale) / 2;
                    state.offsetY = (CROP_HEIGHT - image.height * state.scale) / 2;
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
            const centerX = CROP_WIDTH / 2;
            const centerY = CROP_HEIGHT / 2;
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

                    if (preserveOriginal.checked) {
                        croppedData.value = "";
                        state.needsCrop = false;
                        resolve();
                        return;
                    }

                    const output = document.createElement("canvas");
                    output.width = OUTPUT_WIDTH;
                    output.height = OUTPUT_HEIGHT;
                    draw(output, OUTPUT_WIDTH, OUTPUT_HEIGHT);
                    croppedData.value = output.toDataURL("image/jpeg", 0.9);
                    output.toBlob(function (blob) {
                        if (!blob || typeof DataTransfer === "undefined") {
                            state.needsCrop = false;
                            resolve();
                            return;
                        }

                        const original = input.files[0];
                        const baseName = original.name.replace(/\.[^.]+$/, "") || "project-image";
                        const croppedFile = new File([blob], baseName + "-cropped.jpg", { type: "image/jpeg" });
                        const transfer = new DataTransfer();
                        transfer.items.add(croppedFile);
                        input.files = transfer.files;
                        state.needsCrop = false;
                        resolve();
                    }, "image/jpeg", 0.9);
                });
            }
        };
    }

    function initProjectCroppers() {
        const croppers = [];
        const boundForms = new WeakSet();

        function scan(root) {
            if (isProjectImageInput(root)) {
                const cropper = createCropper(root);
                if (cropper) {
                    croppers.push(cropper);
                    bindForm(cropper.input.closest("form"));
                }
            }

            root.querySelectorAll('input[type="file"]').forEach(function (input) {
                const cropper = createCropper(input);
                if (cropper) {
                    croppers.push(cropper);
                    bindForm(cropper.input.closest("form"));
                }
            });
        }

        function bindForm(form) {
            if (!form || boundForms.has(form)) {
                return;
            }

            boundForms.add(form);
            let submitter = null;

            form.addEventListener("click", function (event) {
                const button = event.target.closest('input[type="submit"], button[type="submit"]');
                if (button) {
                    submitter = button;
                }
            });

            form.addEventListener("submit", function (event) {
                const pending = croppers.filter(function (cropper) {
                    return cropper.input.closest("form") === form && cropper.state.needsCrop;
                });

                if (!pending.length || form.dataset.projectCropDone === "1") {
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

                    form.dataset.projectCropDone = "1";
                    form.submit();
                });
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

    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initProjectCroppers);
    } else {
        initProjectCroppers();
    }
})();
