setInterval(function() {
    // Code to be executed repeatedly every 60 seconds
    refresh = async function(event) {
        // Update meeting status.
        const status = await fetch(`/api/event/state/${CURRENT_MEETING_ID}`, {
                    method: 'GET'
                });
        const statusData = await status.json();
        var submitButton = document.getElementById("meeting-status-submit");
        var statusP = document.getElementById("status-p");
        if (statusData == "Not Started") {
            statusP.innerHTML = `<strong>Current Status: </strong> ${statusData}`;
            submitButton.innerHTML = "Start Meeting";
        }
        else if (statusData == "Ended"){
            statusP.innerHTML = `<strong>Current Status: </strong> ${statusData}`;
        }
        else {
            statusP.innerHTML = `<strong>Current Status: </strong> ${statusData}<br/><strong>Meeting Code: </strong><a href="/admin/reset-code/${CURRENT_MEETING_ID}" target="_blank">Reset Code</a>`;
            submitButton.innerHTML = "End Meeting";
        }
        
        // Update meeting attendees list.
        const attendees = await fetch(`/api/event/attendees/${CURRENT_MEETING_ID}`, {
                    method: 'GET'
                });
        const attendeesData = await attendees.json();
        const attendeeList = document.getElementById("attendee-list");
        attendeeList.innerHTML = "";
        for (let i=0; i < attendeesData.length; i++) {
            attendeeList.innerHTML += attendeesData[i].username + "<br\>";
        }
        }
    refresh();
}, 60000);


document.addEventListener('DOMContentLoaded', function() {
    const meetingMinutesForm = document.getElementById('meeting-minutes-form');
    const meetingStatusForm = document.getElementById('meeting-status-form');
    const meetingAttendeesForm = document.getElementById('meeting-attendees-form');

    meetingMinutesForm.addEventListener('submit', async function(event) {
        // Prevent default form submission
        event.preventDefault();

        // Bootstrap form validation
        if (!this.checkValidity()) {
            event.stopPropagation();
            this.classList.add('was-validated');
            return;
        }
        this.classList.remove('was-validated');
        const formData = new FormData(meetingMinutesForm);
        try {
            const response = await fetch(meetingMinutesForm.action, {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            // Process POST request response.
            if (response.ok) { 
                console.log(result);
                meetingMinutesForm.action = "/admin/minutes/" + result.meeting_id + "/" + result.minutes_id;
            } else {
                showMessage(result.message);
            }
        } catch (error) {
            console.error('Error updating user info:', error);
            showMessage('Network error or server unreachable.');
        }
    });
    if (meetingStatusForm) {
        meetingStatusForm.addEventListener('submit', async function(event) {
            // Prevent default form submission
            event.preventDefault();

            // Bootstrap form validation
            if (!this.checkValidity()) {
                event.stopPropagation();
                this.classList.add('was-validated');
                return;
            }
            this.classList.remove('was-validated');
            const formData = new FormData(meetingStatusForm);
            try {
                const response = await fetch(meetingStatusForm.action, {
                    method: 'POST',
                    body: formData
                });
                const result = await response.json();
                // Process POST request response.
                if (response.ok) { 
                    console.log(result);
                    submitButton = document.getElementById("meeting-status-submit");
                    statusP = document.getElementById("status-p");
                    console.log(meetingStatusForm.action);
                    if (meetingStatusForm.action.includes("/admin/start")) {
                        meetingStatusForm.action = "/admin/end/" + result.meeting_id + "/";
                        submitButton.innerHTML = "End Meeting";
                        statusP.innerHTML = "<strong>Current Status: </strong> Active<br/><strong>Meeting Code: </strong><a href='/admin/show-code?code=" + result.meeting_code + "' target='_blank'>" + result.meeting_code + "</a>";
                    }
                    else {
                        meetingStatusForm.remove();
                        statusP.innerHTML = "<strong>Current Status: </strong> Ended";
                    }
                } else {
                    showMessage(result.message);
                }
            } catch (error) {
                console.error('Error updating user info:', error);
                showMessage('Network error or server unreachable.');
            }
        });
    }

    meetingAttendeesForm.addEventListener('submit', async function(event) {
        // Prevent default form submission
        event.preventDefault();

        // Bootstrap form validation
        if (!this.checkValidity()) {
            event.stopPropagation();
            this.classList.add('was-validated');
            return;
        }
        this.classList.remove('was-validated');
        const formData = new FormData(meetingAttendeesForm);
        try {
            const response = await fetch(meetingAttendeesForm.action, {
                method: 'POST',
                body: formData
            });
            const result = await response.json();
            // Process POST request response.
            if (response.ok) { 
                console.log(result);
                attendeeList = document.getElementById("attendee-list");
                attendeeList.innerHTML += formData.get("attendee_username") + "<br\>";
            } else {
                showMessage(result.message);
            }
        } catch (error) {
            console.error('Error updating user info:', error);
            showMessage('Network error or server unreachable.');
        }
    });

    // Helper function to display messages.
    function showMessage(message) {
        const element = document.getElementById('error-row');
        element.innerHTML += '<div class="alert alert-dismissible fade show" role="alert">' + message + '<button type="button" class="btn-close btn-close-white" data-bs-dismiss="alert" aria-label="Close"></button></div>';
    }
});