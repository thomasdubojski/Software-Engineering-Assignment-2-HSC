let selectedAssignment = null;
function icon(name) {
    return `<span class="material-symbols-outlined">${name}</span>`;
}
function getPriorityLabel(p) {
    p = parseInt(p);

    if (p === 5) return "Critical";
    if (p === 4) return "High";
    if (p === 3) return "Medium";
    if (p === 2) return "Low";
    return "Very Low";
}

function getPriorityClass(p) {
    p = parseInt(p);

    if (p === 5) return "priority-critical";
    if (p === 4) return "priority-high";
    if (p === 3) return "priority-medium";
    if (p === 2) return "priority-low";
    return "priority-very-low";
}
function openModal(a) {
    
    const sessionBox = document.getElementById("sessionModalExtra");
    if (sessionBox) sessionBox.classList.add("hidden");

    document.getElementById("modalSubject").innerText = a.subject || "";
    document.getElementById("modalType").innerText = a.type || "";
    document.getElementById("modalDue").innerText = formatDate(a.dueDate);

    selectedAssignment = a;

    const modal = document.getElementById("modal");
    if (!modal) return;



    document.getElementById("modalTitle").innerText = a.title || "";
    document.getElementById("modalSubject").innerText = a.subject || "";
    document.getElementById("modalType").innerText = a.type || "";
    document.getElementById("modalDue").innerText = formatDate(a.dueDate);

    const priorityEl = document.getElementById("modalPriority");
    if (priorityEl) {
        priorityEl.innerText = getPriorityLabel(a.priority);
        priorityEl.className =
            "priority-bubble " + getPriorityClass(a.priority);
    }

    document.getElementById("modalNotes").innerText =
        a.notes || "No notes provided.";

    const overdueEl = document.getElementById("modalOverdue");
    if (overdueEl) {
        overdueEl.innerHTML = a.overdue
            ? `${icon("warning")} OVERDUE`
            : '';
    }

    setTimeout(() => {
        const historyLink = document.getElementById("historyLink");

        if (historyLink && a?.id) {
            historyLink.href = `/assignment/${a.id}`;
        }
    }, 0);

    modal.classList.remove("hidden");
}

function openSessionModal(session) {

    selectedAssignment = null;

    const modal = document.getElementById("modal");
    if (!modal) return;

    // Hide assignment-specific elements (optional but cleaner)
    const sessionBox = document.getElementById("sessionModalExtra");

    if (sessionBox) sessionBox.classList.remove("hidden");

    document.getElementById("modalTitle").innerText = "Study Session";
    document.getElementById("modalSubject").innerText = "";
    document.getElementById("modalType").innerText = "";
    document.getElementById("modalDue").innerText = "";
    document.getElementById("modalPriority").innerText = "";

    document.getElementById("sessionAssignment").innerText = session.assignment;
    document.getElementById("sessionDuration").innerText = session.duration + " mins";
    document.getElementById("sessionNotes").innerText = session.notes || "No notes";

    modal.classList.remove("hidden");
}

const sessionModal = document.getElementById("sessionModal");
const closeSessionModal = document.getElementById("closeSessionModal");

if (closeSessionModal && sessionModal) {
    closeSessionModal.onclick = () => {
        sessionModal.classList.add("hidden");
    };
}

window.addEventListener("click", (e) => {
    if (e.target === sessionModal) {
        sessionModal.classList.add("hidden");
    }
});

document.addEventListener("DOMContentLoaded", () => {

    const dashboard = document.getElementById("dashboard");
    const modal = document.getElementById("modal");

    const assignments = window.assignments || [];

    function renderCards() {

        if (!dashboard) return;

        dashboard.innerHTML = "";

        assignments.forEach(a => {

            const card = document.createElement("div");
            card.classList.add("card");

            card.innerHTML = `
            <h3>${a.title}</h3>

            <p><strong>Subject:</strong> ${a.subject}</p>
            <p><strong>Due:</strong> ${a.dueDate}</p>

            <span class="priority-bubble ${getPriorityClass(a.priority)}">
                ${getPriorityLabel(a.priority)}
            </span>

            ${a.overdue ? `<span class="overdue-bubble">${icon("warning")} OVERDUE</span>` : ""}

            <div class="card-actions">

                <button class="btn btn-iconEdit edit-btn-card" title="Edit">
                    ${icon("edit")}
                </button>

                <button class="btn btn-iconComplete complete-btn-card" title="Complete">
                    ${icon("check_circle")}
                </button>

                <button class="btn btn-iconDelete delete-btn-card" title="Delete">
                    ${icon("delete")}
                </button>

            </div>
        `;

        card.querySelector(".complete-btn-card").addEventListener("click", async (e) => {
            e.stopPropagation();

            const res = await fetch(`/complete-assignment/${a.id}`, {
                method: "POST"
            });

            const result = await res.json();

            if (result.success) location.reload();
        });

        card.querySelector(".edit-btn-card").addEventListener("click", (e) => {
            e.stopPropagation();
            window.location.href = `/edit-assignment/${a.id}`;
        });

        card.querySelector(".delete-btn-card").addEventListener("click", async (e) => {
            e.stopPropagation();

            const confirmDelete = confirm("Delete this assignment?");
            if (!confirmDelete) return;

            const res = await fetch(`/delete-assignment/${a.id}`, {
                method: "POST"
            });

            const result = await res.json();

            if (result.success) location.reload();
        });

            card.onclick = () => openModal(a);

            dashboard.appendChild(card);
        });
    }

    const closeBtn = document.getElementById("closeBtn");

    if (closeBtn && modal) {
        closeBtn.onclick = () => modal.classList.add("hidden");
    }

    window.onclick = (e) => {
        if (modal && e.target === modal) {
            modal.classList.add("hidden");
        }
    };
    const editBtn = document.getElementById("editBtn");
    const completeBtn = document.getElementById("completeBtn");
    const appleCalendarBtn = document.getElementById("appleCalendarBtn");
    const googleCalendarBtn = document.getElementById("googleCalendarBtn");
    const historyBtn = document.getElementById("historyBtn");
    const deleteBtn = document.getElementById("deleteBtn");

    if (deleteBtn) {
        deleteBtn.addEventListener("click", async () => {
            if (!selectedAssignment) return;

            const confirmDelete = confirm("Delete this assignment?");
            if (!confirmDelete) return;

            const res = await fetch(`/delete-assignment/${selectedAssignment.id}`, {
                method: "POST"
            });

            const result = await res.json();

            if (result.success) {
                location.reload();
            }
        });
    }

    if (historyBtn) {
        historyBtn.addEventListener("click", () => {
            if (!selectedAssignment) return;
            window.location.href = `/assignment/${selectedAssignment.id}`;
        });
    }

    if (appleCalendarBtn) {
        appleCalendarBtn.onclick = () => {
            if (!selectedAssignment) return;

            window.location.href =
                `/export-calendar/${selectedAssignment.id}`;
        };
    }

    if (googleCalendarBtn) {
        googleCalendarBtn.onclick = () => {
            if (!selectedAssignment) return;

            window.location.href =
                `/google-calendar/${selectedAssignment.id}`;
        };
    }

    if (editBtn) {
        editBtn.addEventListener("click", () => {
            if (!selectedAssignment) return;

            window.location.href =
                `/edit-assignment/${selectedAssignment.id}`;
        });
    }

    if (completeBtn) {
        completeBtn.addEventListener("click", async () => {
            if (!selectedAssignment) return;

            const response = await fetch(
                `/complete-assignment/${selectedAssignment.id}`,
                { method: "POST" }
            );

            const result = await response.json();

            if (result.success) {
                location.reload();
            }
        });
    }


    if (dashboard) {
        renderCards();
    }

});
document.addEventListener('DOMContentLoaded', function () {

    const calendarEl = document.getElementById('calendar');

    if (!calendarEl) return;

    let calendar = new FullCalendar.Calendar(calendarEl, {

        initialView: 'timeGridWeek',

        slotMinTime: "06:00:00",
        slotMaxTime: "23:00:00",

        scrollTime: "08:00:00",

        allDaySlot: true,

        eventTimeFormat: {
            hour: "2-digit",
            minute: "2-digit",
            hour12: false
        },

        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },

        events: (window.assignments || []).map(e => {
            if (e.eventType === "session") {
                return {
                    id: e.id,
                    title: "Study: " + e.assignment,
                    start: e.start,
                    end: e.end,
                    allDay: false,

                    extendedProps: {
                        eventType: "session",
                        assignment: e.assignment,
                        duration: e.duration,
                        notes: e.notes
                    }
                };
            }

            return {
                id: e.id,
                title: e.title,
                start: e.start,
                color: "#2f6fed",

                extendedProps: {
                    eventType: "assignment",
                    subject: e.subject,
                    type: e.type,
                    priority: e.priority,
                    notes: e.notes,
                    overdue: e.overdue
                }
            };
        }),

        eventDidMount: function(info) {
            if (info.event.extendedProps.eventType === "session") {
                info.el.style.backgroundColor = "#2ecc71";
                info.el.style.borderColor = "#27ae60";
            }
        },

        eventClick: function(info) {
            if (info.event.extendedProps.eventType === "session") {

                const sessionModal = document.getElementById("sessionModal");

                document.getElementById("sessionAssignment").innerText =
                    info.event.extendedProps.assignment || "";

                document.getElementById("sessionDuration").innerText =
                    (info.event.extendedProps.duration || 0) + " mins";

                document.getElementById("sessionNotes").innerText =
                    info.event.extendedProps.notes || "No notes";

                sessionModal.classList.remove("hidden");

                return;
}

            const assignment = {
                id: info.event.id,
                title: info.event.title,
                subject: info.event.extendedProps.subject,
                type: info.event.extendedProps.type,
                dueDate: info.event.start,
                priority: info.event.extendedProps.priority,
                notes: info.event.extendedProps.notes,
                overdue: info.event.extendedProps.overdue
            };

            openModal(assignment);
        },

        eventContent: function(info) {

            const isSession = info.event.extendedProps.eventType === "session";

            if (isSession) {
                return {
                    html: `
                        <div class="calendar-bubble session-bubble">
                            <div class="bubble-title">
                                ${icon("book_2")} ${info.event.title}
                            </div>

                            <div class="bubble-sub">
                                ${info.event.extendedProps.duration || ""} mins
                            </div>
                        </div>
                    `
                };
            }

            return {
                html: `
                    <div class="calendar-bubble assignment-bubble">

                        <div class="bubble-title">
                            ${icon("list_alt")} ${info.event.title}
                        </div>

                        <div class="bubble-row">

                            <span class="priority-pill ${getPriorityClass(info.event.extendedProps.priority)}">
                                ${getPriorityLabel(info.event.extendedProps.priority)}
                            </span>

                            ${info.event.extendedProps.overdue ? `<span class="overdue-pill">${icon("warning")} OVERDUE</span>` : ""}

                        </div>

                    </div>
                `
            };
        }
    });

    calendar.render();
});

const sessionBtn = document.getElementById("sessionBtn");

if (sessionBtn) {
    sessionBtn.addEventListener("click", () => {
        window.location.href = sessionBtn.dataset.url;
    });
}