console.log("view_task.js loaded");

// =====================================================
// STATE
// =====================================================
// One object tracks every active filter/sort/view mode. Every control
// (search box, status tabs, dropdowns, stat pills) updates this object
// and then calls loadTasks() — single source of truth for what's on screen.
const filters = {
    q: "",          // search text
    status: "",     // "" | "Pending" | "Completed"
    category: "",
    priority: "",
    sortBy: "",     // "" | "due_date" | "priority" | "title"
    overdueOnly: false
};

const taskContainer = document.getElementById("taskContainer");

// Set of currently selected task IDs, for bulk actions
const selectedIds = new Set();

// =====================================================
// RENDER
// =====================================================
function renderTasks(tasks) {

    if (!tasks || tasks.length === 0) {
        taskContainer.innerHTML = `<p class="empty-state">No tasks match — try a different search or filter.</p>`;
        return;
    }

    taskContainer.innerHTML = tasks.map(task => {
        const isDone = task.status === "Completed";
        const isChecked = selectedIds.has(task.id);

        return `
            <div class="task-card ${isDone ? "done" : ""}">
                <div class="task-card-top">
                    <label class="select-wrap">
                        <input type="checkbox" class="select-checkbox" data-id="${task.id}" ${isChecked ? "checked" : ""}>
                        <span class="select-mark"></span>
                    </label>
                    <h3>${escapeHtml(task.title)}</h3>
                    <span class="tag tag-priority">${escapeHtml(task.priority)}</span>
                </div>

                <p class="task-desc">${escapeHtml(task.description || "")}</p>

                <div class="task-details">
                    <span class="tag tag-category">${escapeHtml(task.category)}</span>
                    <span class="due-date">Due ${escapeHtml(task.due_date || "")}</span>
                </div>

                <div class="task-footer">
                    <label class="check-wrap">
                        <input type="checkbox" onchange="toggleComplete(${task.id})" ${isDone ? "checked" : ""}>
                        <span class="check-mark"></span>
                        <span class="status">${escapeHtml(task.status)}</span>
                    </label>

                    <div class="task-actions">
                        <button type="button" class="icon-btn edit-btn" onclick="editTask(${task.id})">Edit</button>
                        <button type="button" class="icon-btn delete-btn" onclick="deleteTask(${task.id})">Delete</button>
                    </div>
                </div>
            </div>
        `;
    }).join("");

    // Re-wire the select checkboxes every time the list is redrawn,
    // since innerHTML replaces the DOM nodes (and their old listeners).
    document.querySelectorAll(".select-checkbox").forEach(cb => {
        cb.addEventListener("change", function () {
            const id = Number(this.dataset.id);
            if (this.checked) {
                selectedIds.add(id);
            } else {
                selectedIds.delete(id);
            }
            updateBulkBar();
        });
    });
}

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
}

// =====================================================
// FETCH — the actual API calls
// =====================================================
// Decides which endpoint fits the current state. These modes are
// mutually exclusive, in priority order:
//   1. Search text        -> /api/tasks/search   (ignores other filters)
//   2. Overdue quick-view  -> /api/tasks/overdue
//   3. A sort option picked -> /api/tasks/sort    (ignores category/priority —
//                              those endpoints were built separately, so this
//                              app treats "sort" and "filter" as two views
//                              rather than combining them into one query)
//   4. Otherwise           -> /api/tasks/filter   (status/category/priority)
async function loadTasks() {

    let url;

    if (filters.q.trim() !== "") {
        const params = new URLSearchParams({ q: filters.q.trim() });
        url = `/api/tasks/search?${params}`;

    } else if (filters.overdueOnly) {
        url = `/api/tasks/overdue`;

    } else if (filters.sortBy) {
        const params = new URLSearchParams({ by: filters.sortBy });
        url = `/api/tasks/sort?${params}`;

    } else {
        const params = new URLSearchParams();
        if (filters.status) params.set("status", filters.status);
        if (filters.category) params.set("category", filters.category);
        if (filters.priority) params.set("priority", filters.priority);
        url = `/api/tasks/filter?${params}`;
    }

    try {
        const response = await fetch(url);

        if (!response.ok) {
            console.error("Failed to load tasks:", response.status);
            return;
        }

        const tasks = await response.json();
        renderTasks(tasks);

    } catch (err) {
        console.error("Network error loading tasks:", err);
    }
}

// Fetches the stats summary and fills in the numbers on the stat pills.
async function loadStats() {
    try {
        const response = await fetch("/api/tasks/stats");
        if (!response.ok) return;

        const stats = await response.json();

        document.querySelector("#statPending .stat-count").textContent = stats.pending;
        document.querySelector("#statCompleted .stat-count").textContent = stats.completed;
        document.querySelector("#statOverdue .stat-count").textContent = stats.overdue;

    } catch (err) {
        console.error("Failed to load stats:", err);
    }
}

// =====================================================
// WIRE UP CONTROLS
// =====================================================

// --- Search box (debounced) ---
const searchInput = document.getElementById("searchInput");
let searchTimer;

if (searchInput) {
    searchInput.addEventListener("input", function () {
        filters.q = this.value;
        clearTimeout(searchTimer);
        searchTimer = setTimeout(loadTasks, 300);
    });
}

// --- Category / priority dropdowns ---
const categorySelect = document.getElementById("categorySelect");
const prioritySelect = document.getElementById("prioritySelect");

if (categorySelect) {
    categorySelect.addEventListener("change", function () {
        filters.category = this.value;
        filters.sortBy = "";
        filters.overdueOnly = false;
        setStatPillActive(null);
        loadTasks();
    });
}

if (prioritySelect) {
    prioritySelect.addEventListener("change", function () {
        filters.priority = this.value;
        filters.sortBy = "";
        filters.overdueOnly = false;
        setStatPillActive(null);
        loadTasks();
    });
}

// --- Sort dropdown ---
const sortSelect = document.getElementById("sortSelect");

if (sortSelect) {
    sortSelect.addEventListener("change", function () {
        filters.sortBy = this.value;
        filters.overdueOnly = false;
        setStatPillActive(null);
        loadTasks();
    });
}

// --- Stat pills (All / Pending / Completed / Overdue) ---
const statAll = document.getElementById("statAll");
const statPending = document.getElementById("statPending");
const statCompleted = document.getElementById("statCompleted");
const statOverdue = document.getElementById("statOverdue");

function setStatPillActive(pillId) {
    [statAll, statPending, statCompleted, statOverdue].forEach(pill => {
        if (pill) pill.classList.toggle("active", pill.id === pillId);
    });
}

if (statAll) {
    statAll.addEventListener("click", () => {
        filters.status = "";
        filters.overdueOnly = false;
        filters.sortBy = "";
        if (categorySelect) categorySelect.value = "";
        if (prioritySelect) prioritySelect.value = "";
        if (sortSelect) sortSelect.value = "";
        filters.category = "";
        filters.priority = "";
        setStatPillActive("statAll");
        loadTasks();
    });
}

if (statPending) {
    statPending.addEventListener("click", () => {
        filters.status = "Pending";
        filters.overdueOnly = false;
        filters.sortBy = "";
        setStatPillActive("statPending");
        loadTasks();
    });
}

if (statCompleted) {
    statCompleted.addEventListener("click", () => {
        filters.status = "Completed";
        filters.overdueOnly = false;
        filters.sortBy = "";
        setStatPillActive("statCompleted");
        loadTasks();
    });
}

if (statOverdue) {
    statOverdue.addEventListener("click", () => {
        filters.overdueOnly = true;
        filters.sortBy = "";
        setStatPillActive("statOverdue");
        loadTasks();
    });
}

// --- Bulk select bar ---
const bulkBar = document.getElementById("bulkBar");
const bulkCount = document.getElementById("bulkCount");
const bulkCompleteBtn = document.getElementById("bulkCompleteBtn");
const bulkCancelBtn = document.getElementById("bulkCancelBtn");

function updateBulkBar() {
    if (selectedIds.size > 0) {
        bulkBar.classList.add("visible");
        bulkCount.textContent = `${selectedIds.size} selected`;
    } else {
        bulkBar.classList.remove("visible");
    }
}

if (bulkCompleteBtn) {
    bulkCompleteBtn.addEventListener("click", async () => {
        if (selectedIds.size === 0) return;

        try {
            const response = await fetch("/api/tasks/bulk-complete", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ ids: Array.from(selectedIds) })
            });

            if (!response.ok) {
                alert("Bulk update failed.");
                return;
            }

            selectedIds.clear();
            updateBulkBar();
            loadTasks();
            loadStats();

        } catch (err) {
            console.error("Bulk complete error:", err);
        }
    });
}

if (bulkCancelBtn) {
    bulkCancelBtn.addEventListener("click", () => {
        selectedIds.clear();
        updateBulkBar();
        loadTasks(); // redraw from current filters with all checkboxes cleared
    });
}

// =====================================================
// TASK ACTIONS — complete / delete / edit / save
// =====================================================

async function toggleComplete(id) {
    try {
        const response = await fetch(`/complete/${id}`, { method: "POST" });

        if (!response.ok) {
            alert("Failed to update task status.");
            return;
        }

        loadTasks();
        loadStats();

    } catch (err) {
        console.error("Error toggling task:", err);
    }
}

async function deleteTask(id) {
    const confirmDelete = confirm("Are you sure you want to delete this task?");
    if (!confirmDelete) return;

    const response = await fetch(`/api/tasks/${id}`, { method: "DELETE" });

    if (response.ok) {
        selectedIds.delete(id);
        updateBulkBar();
        loadTasks();
        loadStats();
    } else {
        alert("Delete failed");
    }
}

async function editTask(id) {
    const response = await fetch(`/api/tasks/${id}`);
    const task = await response.json();

    document.getElementById("editId").value = task.id;
    document.getElementById("editTitle").value = task.title;
    document.getElementById("editDescription").value = task.description;
    document.getElementById("editCategory").value = task.category;
    document.getElementById("editPriority").value = task.priority;
    document.getElementById("editDueDate").value = task.due_date;

    document.getElementById("editModal").style.display = "flex";
}

function closeModal() {
    document.getElementById("editModal").style.display = "none";
}

async function saveTask() {
    const id = document.getElementById("editId").value;

    const title = document.getElementById("editTitle").value;
    const description = document.getElementById("editDescription").value;
    const category = document.getElementById("editCategory").value;
    const priority = document.getElementById("editPriority").value;
    const due_date = document.getElementById("editDueDate").value;

    const response = await fetch(`/api/tasks/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, description, category, priority, due_date })
    });

    if (response.ok) {
        closeModal();
        loadTasks();
        loadStats();
    } else {
        alert("Failed to update task.");
    }
}

// =====================================================
// INITIAL LOAD
// =====================================================
// The task list itself is already rendered server-side by Jinja on
// first page load, so we only need to fetch the stats bar numbers here.
loadStats();
