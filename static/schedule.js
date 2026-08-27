const WEEKDAY_KEYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const WEEKDAY_FULL = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const MONTH_LABELS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];

let viewMode = "week";
let anchorDate = startOfDay(new Date());
let schedulesCache = [];

// ---------- date helpers ----------

function startOfDay(d) {
    const copy = new Date(d);
    copy.setHours(0, 0, 0, 0);
    return copy;
}

function addDays(d, n) {
    const copy = new Date(d);
    copy.setDate(copy.getDate() + n);
    return copy;
}

function isoDate(d) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}-${m}-${day}`;
}

function dowKey(d) {
    // JS getDay(): 0=Sun..6=Sat. Convert to Mon-first index used by the backend.
    return WEEKDAY_KEYS[(d.getDay() + 6) % 7];
}

function weekStart(d) {
    const idx = (d.getDay() + 6) % 7; // 0 = Monday
    return addDays(d, -idx);
}

function niceRangeLabel(start, end) {
    if (isoDate(start) === isoDate(end)) {
        return `${WEEKDAY_FULL[dowIndex(start)]}, ${MONTH_LABELS[start.getMonth()]} ${start.getDate()}`;
    }
    const sameMonth = start.getMonth() === end.getMonth();
    const startLabel = `${MONTH_LABELS[start.getMonth()]} ${start.getDate()}`;
    const endLabel = sameMonth ? `${end.getDate()}` : `${MONTH_LABELS[end.getMonth()]} ${end.getDate()}`;
    return `${startLabel} – ${endLabel}`;
}

function dowIndex(d) { return (d.getDay() + 6) % 7; }

// ---------- data fetching ----------

async function fetchTasksInRange(startStr, endStr) {
    const res = await fetch(`/api/tasks/range?start=${startStr}&end=${endStr}`);
    if (!res.ok) return [];
    return res.json();
}

async function fetchSchedules() {
    const res = await fetch("/api/schedules");
    if (!res.ok) return [];
    return res.json();
}

// Does this schedule occur on the given date?
function scheduleOccursOn(sched, date) {
    if (sched.status !== "Active") return false;
    if (sched.start_date && sched.start_date > isoDate(date)) return false;
    if (sched.recurrence === "daily") return true;
    if (sched.recurrence === "weekly") return sched.day_of_week === dowKey(date);
    return false;
}

function isOverdue(task) {
    if (task.status === "Completed") return false;
    const due = (task.due_date || "").slice(0, 10);
    return due && due < isoDate(startOfDay(new Date()));
}

function formatDuration(minutes) {
    if (!minutes) return "";
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    if (h && m) return `${h}h ${m}m`;
    if (h) return `${h}h`;
    return `${m}m`;
}

// ---------- rendering: week grid ----------

async function renderWeekView() {
    document.getElementById("weekGrid").style.display = "grid";
    document.getElementById("dayView").style.display = "none";

    const start = weekStart(anchorDate);
    const end = addDays(start, 6);

    document.getElementById("rangeLabel").textContent = niceRangeLabel(start, end);

    const [tasks, schedules] = await Promise.all([
        fetchTasksInRange(isoDate(start), isoDate(end)),
        fetchSchedules()
    ]);
    schedulesCache = schedules;
    renderRoutines(schedules);

    const grid = document.getElementById("weekGrid");
    grid.innerHTML = "";

    for (let i = 0; i < 7; i++) {
        const day = addDays(start, i);
        const dayStr = isoDate(day);
        const isToday = dayStr === isoDate(startOfDay(new Date()));

        const dayTasks = tasks.filter(t => (t.due_date || "").slice(0, 10) === dayStr);
        const daySchedules = schedules.filter(s => scheduleOccursOn(s, day));

        const col = document.createElement("div");
        col.className = "day-column" + (isToday ? " is-today" : "");

        const itemsHtml = [
            ...daySchedules.map(s => {
                const durationLabel = s.duration_minutes ? ` · ${formatDuration(s.duration_minutes)}` : "";
                return `<span class="chip chip-routine" title="${escapeHtml(s.description || '')}">${escapeHtml(s.title)}${durationLabel}</span>`;
            }),
            ...dayTasks.map(t => {
                const cls = ["chip", "chip-task"];
                if (t.status === "Completed") cls.push("done");
                else if (isOverdue(t)) cls.push("overdue");
                return `<span class="${cls.join(" ")}">${escapeHtml(t.title)}</span>`;
            })
        ].join("");

        col.innerHTML = `
            <div class="day-column-head">
                <span class="day-name">${WEEKDAY_KEYS[i]}</span>
                <span class="day-number">${day.getDate()}</span>
            </div>
            <div class="day-items">
                ${itemsHtml || '<span class="day-empty">Nothing scheduled</span>'}
            </div>
        `;

        grid.appendChild(col);
    }
}

// ---------- rendering: day view ----------

async function renderDayView() {
    document.getElementById("weekGrid").style.display = "none";
    document.getElementById("dayView").style.display = "block";

    const dayStr = isoDate(anchorDate);
    document.getElementById("rangeLabel").textContent = niceRangeLabel(anchorDate, anchorDate);

    const [tasks, schedules] = await Promise.all([
        fetchTasksInRange(dayStr, dayStr),
        fetchSchedules()
    ]);
    schedulesCache = schedules;
    renderRoutines(schedules);

    const daySchedules = schedules.filter(s => scheduleOccursOn(s, anchorDate));

    const container = document.getElementById("dayView");
    const heading = `<div class="day-view-heading">${WEEKDAY_FULL[dowIndex(anchorDate)]}, ${MONTH_LABELS[anchorDate.getMonth()]} ${anchorDate.getDate()}</div>`;

    const items = [
        ...daySchedules.map(s => `
            <div class="agenda-item routine">
                <span class="agenda-title">${escapeHtml(s.title)}</span>
                <span class="agenda-meta">Routine · ${s.recurrence === "daily" ? "Daily" : "Weekly"}${s.duration_minutes ? " · " + formatDuration(s.duration_minutes) : ""}</span>
            </div>
        `),
        ...tasks.map(t => {
            const cls = ["agenda-item"];
            if (t.status === "Completed") cls.push("done");
            else if (isOverdue(t)) cls.push("overdue");
            return `
                <div class="${cls.join(" ")}">
                    <span class="agenda-title">${escapeHtml(t.title)}</span>
                    <span class="agenda-meta">${escapeHtml(t.priority || "")} · ${t.status}</span>
                </div>
            `;
        })
    ].join("");

    container.innerHTML = heading + (items || '<p class="empty-state">Nothing scheduled for this day.</p>');
}

function render() {
    if (viewMode === "week") renderWeekView();
    else renderDayView();
}

// ---------- routines panel ----------

function renderRoutines(schedules) {
    const list = document.getElementById("routinesList");
    const empty = document.getElementById("routinesEmpty");

    if (!schedules.length) {
        list.innerHTML = '<p class="empty-state" id="routinesEmpty">No routines yet — add one above.</p>';
        return;
    }

    list.innerHTML = schedules.map(s => `
        <div class="routine-row">
            <div class="routine-info">
                <div class="routine-title">${escapeHtml(s.title)}</div>
                <div class="routine-meta">${s.recurrence === "daily" ? "Every day" : "Every " + WEEKDAY_FULL[WEEKDAY_KEYS.indexOf(s.day_of_week)]}${s.duration_minutes ? " · " + formatDuration(s.duration_minutes) : ""}</div>
            </div>
            <span class="routine-status ${s.status}">${s.status}</span>
            <div class="routine-actions">
                <button type="button" class="btn btn-ghost" onclick="editSchedule(${s.id})">Edit</button>
                <button type="button" class="btn btn-ghost" onclick="toggleSchedule(${s.id})">${s.status === "Active" ? "Pause" : "Resume"}</button>
                <button type="button" class="btn btn-danger" onclick="deleteSchedule(${s.id})">Delete</button>
            </div>
        </div>
    `).join("");
}

function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str || "";
    return div.innerHTML;
}

// ---------- modal ----------

function openModal(mode, sched) {
    document.getElementById("scheduleModalTitle").textContent = mode === "edit" ? "Edit routine" : "Add routine";
    document.getElementById("scheduleId").value = sched ? sched.id : "";
    document.getElementById("scheduleTitle").value = sched ? sched.title : "";
    document.getElementById("scheduleDescription").value = sched ? (sched.description || "") : "";
    document.getElementById("scheduleRecurrence").value = sched ? sched.recurrence : "daily";
    document.getElementById("scheduleDayOfWeek").value = sched && sched.day_of_week ? sched.day_of_week : dowKey(new Date());
    document.getElementById("scheduleStartDate").value = sched && sched.start_date ? sched.start_date : isoDate(new Date());
    document.getElementById("scheduleDuration").value = sched && sched.duration_minutes ? sched.duration_minutes : "";
    toggleDayOfWeekField();
    document.getElementById("scheduleModal").style.display = "flex";
}

function closeModal() {
    document.getElementById("scheduleModal").style.display = "none";
}

function toggleDayOfWeekField() {
    const isWeekly = document.getElementById("scheduleRecurrence").value === "weekly";
    document.getElementById("dayOfWeekField").style.display = isWeekly ? "block" : "none";
}

async function saveSchedule() {
    const id = document.getElementById("scheduleId").value;
    const payload = {
        title: document.getElementById("scheduleTitle").value.trim(),
        description: document.getElementById("scheduleDescription").value.trim(),
        recurrence: document.getElementById("scheduleRecurrence").value,
        day_of_week: document.getElementById("scheduleDayOfWeek").value,
        start_date: document.getElementById("scheduleStartDate").value,
        duration_minutes: document.getElementById("scheduleDuration").value.trim()
    };

    if (!payload.title) {
        alert("Give the routine a title.");
        return;
    }

    const url = id ? `/api/schedules/${id}` : "/api/schedules";
    const method = id ? "PUT" : "POST";

    const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });

    if (res.ok) {
        closeModal();
        render();
    } else {
        alert("Couldn't save that routine — please check the fields and try again.");
    }
}

function editSchedule(id) {
    const sched = schedulesCache.find(s => s.id === id);
    if (sched) openModal("edit", sched);
}

async function toggleSchedule(id) {
    await fetch(`/api/schedules/${id}/toggle`, { method: "POST" });
    render();
}

async function deleteSchedule(id) {
    if (!confirm("Delete this routine? This can't be undone.")) return;
    await fetch(`/api/schedules/${id}`, { method: "DELETE" });
    render();
}

// ---------- toolbar wiring ----------

document.addEventListener("DOMContentLoaded", () => {
    render();

    document.getElementById("viewWeekBtn").addEventListener("click", () => {
        viewMode = "week";
        document.getElementById("viewWeekBtn").classList.add("active");
        document.getElementById("viewDayBtn").classList.remove("active");
        render();
    });

    document.getElementById("viewDayBtn").addEventListener("click", () => {
        viewMode = "day";
        document.getElementById("viewDayBtn").classList.add("active");
        document.getElementById("viewWeekBtn").classList.remove("active");
        render();
    });

    document.getElementById("prevBtn").addEventListener("click", () => {
        anchorDate = addDays(anchorDate, viewMode === "week" ? -7 : -1);
        render();
    });

    document.getElementById("nextBtn").addEventListener("click", () => {
        anchorDate = addDays(anchorDate, viewMode === "week" ? 7 : 1);
        render();
    });

    document.getElementById("todayBtn").addEventListener("click", () => {
        anchorDate = startOfDay(new Date());
        render();
    });

    document.getElementById("addScheduleBtn").addEventListener("click", () => openModal("add", null));
    document.getElementById("cancelScheduleBtn").addEventListener("click", closeModal);
    document.getElementById("saveScheduleBtn").addEventListener("click", saveSchedule);
    document.getElementById("scheduleRecurrence").addEventListener("change", toggleDayOfWeekField);

    document.getElementById("scheduleModal").addEventListener("click", (e) => {
        if (e.target.id === "scheduleModal") closeModal();
    });
});
