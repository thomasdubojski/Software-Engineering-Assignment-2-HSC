
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