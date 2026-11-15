document.addEventListener("DOMContentLoaded", () => {
    // State
    let selectedPreset = "standard";
    const activeJobs = new Map();

    // DOM Elements
    const presetCards = document.querySelectorAll(".preset-card");
    const aspectSelect = document.getElementById("aspectSelect");
    const volumeSelect = document.getElementById("volumeSelect");
    const dropzone = document.getElementById("dropzone");
    const fileInput = document.getElementById("fileInput");
    const queueList = document.getElementById("queueList");
    const queueCounter = document.getElementById("queueCounter");
    const emptyQueue = document.getElementById("emptyQueue");
    const outputList = document.getElementById("outputList");
    const btnOpenFolder = document.getElementById("btnOpenFolder");
    const btnRefreshOutputs = document.getElementById("btnRefreshOutputs");
    const btnHelpModal = document.getElementById("btnHelpModal");
    const btnCloseHelp = document.getElementById("btnCloseHelp");
    const helpModal = document.getElementById("helpModal");

    // 1. Preset Selection
    presetCards.forEach(card => {
        card.addEventListener("click", () => {
            presetCards.forEach(c => c.classList.remove("active"));
            card.classList.add("active");
            selectedPreset = card.dataset.preset;
        });
    });

    // 2. Help Modal
    btnHelpModal.addEventListener("click", () => helpModal.classList.add("show"));
    btnCloseHelp.addEventListener("click", () => helpModal.classList.remove("show"));
    helpModal.addEventListener("click", (e) => {
        if (e.target === helpModal) helpModal.classList.remove("show");
    });

    // 3. Open Output Folder
    btnOpenFolder.addEventListener("click", async () => {
        try {
            const res = await fetch("/api/open-folder", { method: "POST" });
            const data = await res.json();
            if (!data.success) {
                alert("ফোল্ডার ওপেন করা যায়নি: " + (data.error || "অজানা সমস্যা"));
            }
        } catch (err) {
            console.error(err);
        }
    });

    // 4. File Dropzone & Picker
    dropzone.addEventListener("click", () => fileInput.click());

    ["dragenter", "dragover"].forEach(event => {
        dropzone.addEventListener(event, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.add("dragover");
        });
    });

    ["dragleave", "drop"].forEach(event => {
        dropzone.addEventListener(event, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropzone.classList.remove("dragover");
        });
    });

    dropzone.addEventListener("drop", (e) => {
        const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith("video/") || f.name.match(/\.(mp4|mkv|avi|mov|webm|flv|3gp)$/i));
        if (files.length > 0) {
            handleSelectedFiles(files);
        } else {
            alert("দয়া করে ভিডিও ফাইল সিলেক্ট করুন (যেমন: MP4, MKV, AVI)।");
        }
    });

    fileInput.addEventListener("change", () => {
        const files = Array.from(fileInput.files);
        if (files.length > 0) {
            handleSelectedFiles(files);
        }
        fileInput.value = "";
    });

    function updateQueueCount() {
        const count = activeJobs.size;
        queueCounter.textContent = `${count} টি ফাইল`;
        if (count === 0 && emptyQueue) {
            emptyQueue.style.display = "block";
        } else if (emptyQueue) {
            emptyQueue.style.display = "none";
        }
    }

    // 5. Handling files
    function handleSelectedFiles(files) {
        files.forEach(file => {
            const clientId = "c_" + Math.random().toString(36).substring(2, 9);
            createQueueItem(clientId, file);
            uploadAndConvertFile(clientId, file);
        });
    }

    function createQueueItem(clientId, file) {
        if (emptyQueue) emptyQueue.style.display = "none";

        const item = document.createElement("div");
        item.className = "queue-item";
        item.id = `item_${clientId}`;

        const sizeMB = (file.size / (1024 * 1024)).toFixed(1);

        item.innerHTML = `
            <div class="item-top">
                <span class="item-title" title="${file.name}">🎬 ${file.name}</span>
                <span class="item-meta">${sizeMB} MB • ${selectedPreset.toUpperCase()}</span>
            </div>
            <div class="progress-container">
                <div class="progress-bar" id="bar_${clientId}"></div>
            </div>
            <div class="item-status">
                <span class="status-msg" id="msg_${clientId}">ফাইল প্রস্তুত হচ্ছে...</span>
                <div class="item-actions" id="actions_${clientId}">
                    <!-- Completed buttons will go here -->
                </div>
            </div>
        `;

        queueList.prepend(item);
        activeJobs.set(clientId, { file, status: "uploading" });
        updateQueueCount();
    }

    function uploadAndConvertFile(clientId, file) {
        const bar = document.getElementById(`bar_${clientId}`);
        const msg = document.getElementById(`msg_${clientId}`);
        const actions = document.getElementById(`actions_${clientId}`);

        const scale = aspectSelect.value;
        const volume = volumeSelect.value;
        const preset = selectedPreset;

        const uploadUrl = `/api/upload?filename=${encodeURIComponent(file.name)}&preset=${preset}&scale=${scale}&volume=${volume}`;

        const xhr = new XMLHttpRequest();
        xhr.open("POST", uploadUrl, true);
        xhr.setRequestHeader("Content-Type", "application/octet-stream");

        // Upload progress (0% - 30% of total visual indicator)
        xhr.upload.onprogress = (e) => {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 100);
                if (bar) bar.style.width = `${Math.min(30, percent * 0.3)}%`;
                if (msg) msg.textContent = `আপলোড হচ্ছে: ${percent}%...`;
            }
        };

        xhr.onload = () => {
            if (xhr.status === 200) {
                try {
                    const data = JSON.parse(xhr.responseText);
                    if (data.job_id) {
                        if (msg) msg.textContent = "কনভার্ট শুরু হচ্ছে...";
                        pollJobStatus(clientId, data.job_id);
                    } else {
                        if (msg) {
                            msg.textContent = "ত্রুটি: " + (data.error || "কনভার্ট শুরু করা যায়নি");
                            msg.classList.add("failed");
                        }
                    }
                } catch (err) {
                    if (msg) {
                        msg.textContent = "সার্ভার রেসপন্স বুঝতে সমস্যা";
                        msg.classList.add("failed");
                    }
                }
            } else {
                if (msg) {
                    msg.textContent = `আপলোড ব্যর্থ হয়েছে (HTTP ${xhr.status})`;
                    msg.classList.add("failed");
                }
            }
        };

        xhr.onerror = () => {
            if (msg) {
                msg.textContent = "নেটওয়ার্ক কানেকশন ফেইলড";
                msg.classList.add("failed");
            }
        };

        xhr.send(file);
    }

    function pollJobStatus(clientId, jobId) {
        const bar = document.getElementById(`bar_${clientId}`);
        const msg = document.getElementById(`msg_${clientId}`);
        const actions = document.getElementById(`actions_${clientId}`);

        const interval = setInterval(async () => {
            try {
                const res = await fetch(`/api/job?id=${jobId}`);
                if (!res.ok) return;
                const job = await res.json();

                if (job.status === "converting") {
                    // Map 0-100 progress to visual bar 30% -> 99%
                    const visualProgress = 30 + Math.round(job.progress * 0.7);
                    if (bar) bar.style.width = `${visualProgress}%`;
                    if (msg) msg.textContent = `বাটন ফোনের জন্য কনভার্ট হচ্ছে: ${job.progress}%...`;
                } else if (job.status === "completed") {
                    clearInterval(interval);
                    if (bar) {
                        bar.style.width = "100%";
                        bar.style.background = "#10b981";
                    }
                    if (msg) {
                        msg.textContent = `সফল! সাইজ: ${job.output_size} (আউটপুটে সেভ হয়েছে)`;
                        msg.classList.add("success");
                    }
                    if (actions) {
                        actions.innerHTML = `
                            <a href="/api/download?file=${encodeURIComponent(job.output_file)}" class="btn btn-sm btn-primary">
                                ⬇️ ডাউনলোড .3GP
                            </a>
                        `;
                    }
                    loadOutputs();
                } else if (job.status === "failed") {
                    clearInterval(interval);
                    if (bar) {
                        bar.style.background = "#ef4444";
                    }
                    if (msg) {
                        msg.textContent = job.message || "কনভার্ট ব্যর্থ হয়েছে";
                        msg.classList.add("failed");
                    }
                }
            } catch (err) {
                console.error("Polling error:", err);
            }
        }, 600);
    }

    // 6. Converted Files List
    async function loadOutputs() {
        try {
            const res = await fetch("/api/list-outputs");
            const data = await res.json();
            outputList.innerHTML = "";

            if (!data.files || data.files.length === 0) {
                outputList.innerHTML = `<div class="empty-state">কোনো কনভার্ট করা 3GP ফাইল নেই।</div>`;
                return;
            }

            data.files.forEach(f => {
                const div = document.createElement("div");
                div.className = "output-item";
                div.innerHTML = `
                    <div class="output-info">
                        <span class="output-name" title="${f.name}">📱 ${f.name}</span>
                        <span class="output-sub">${f.size} • ${f.mtime}</span>
                    </div>
                    <div class="output-btns">
                        <a href="/api/download?file=${encodeURIComponent(f.name)}" class="btn btn-sm btn-primary" title="ডাউনলোড">
                            ⬇️ ডাউনলোড
                        </a>
                        <button class="btn btn-sm btn-danger btn-delete" data-file="${f.name}" title="মুছে ফেলুন">
                            🗑️
                        </button>
                    </div>
                `;
                outputList.appendChild(div);
            });

            // Attach delete handlers
            document.querySelectorAll(".btn-delete").forEach(btn => {
                btn.addEventListener("click", async (e) => {
                    const filename = btn.dataset.file;
                    if (confirm(`আপনি কি "${filename}" মুছে ফেলতে চান?`)) {
                        await fetch(`/api/delete-output?file=${encodeURIComponent(filename)}`, { method: "DELETE" });
                        loadOutputs();
                    }
                });
            });

        } catch (err) {
            console.error("Failed to load output list:", err);
        }
    }

    btnRefreshOutputs.addEventListener("click", loadOutputs);

    // Initial load of outputs
    loadOutputs();
});
