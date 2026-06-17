let selectedAssignment = null;
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

    selectedAssignment = a;

    const modal = document.getElementById("modal");
    if (!modal) return;

    document.getElementById("modalTitle").innerText = a.title || "";
    document.getElementById("modalSubject").innerText = a.subject || "";
    document.getElementById("modalType").innerText = a.type || "";
    document.getElementById("modalDue").innerText = a.dueDate || "";

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
            ? '<span class="overdue-bubble">⚠ OVERDUE</span>'
            : '';
    }

    modal.classList.remove("hidden");
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

document.addEventListener('DOMContentLoaded', function () {

    const calendarEl = document.getElementById('calendar');

    if (!calendarEl) return;

    let calendar = new FullCalendar.Calendar(calendarEl, {

        initialView: 'dayGridMonth',

        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },

        events: (window.assignments || []).map(a => ({
            title: a.title,
            start: a.dueDate,
            extendedProps: {
                id: a.id,
                subject: a.subject,
                type: a.type,
                priority: a.priority,
                notes: a.notes,
                overdue: a.overdue
            }
        })),

        eventClick: function(info) {

            const assignment = {
                id: info.event.extendedProps.id,
                title: info.event.title,
                subject: info.event.extendedProps.subject,
                type: info.event.extendedProps.type,
                dueDate: info.event.startStr,
                priority: info.event.extendedProps.priority,
                notes: info.event.extendedProps.notes,
                overdue: info.event.extendedProps.overdue
            };

            openModal(assignment);
        },

        eventContent: function(info) {

            return {
                html: `
                    <div class="calendar-event">
                        <div class="subject-bubble">
                            ${info.event.title}
                        </div>

                        <div class="priority-bubble ${getPriorityClass(info.event.extendedProps.priority)}">
                            ${getPriorityLabel(info.event.extendedProps.priority)}
                        </div>
                    </div>
                `
            };
        }
    });

    calendar.render();
});