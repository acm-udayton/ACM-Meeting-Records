// Helper function to display messages.
function showMessage(message) {
    const element = document.getElementById('error-row');
    element.innerHTML += '<div class="alert alert-dismissible fade show" role="alert">' + message + '<button type="button" class="btn-close btn-close-white" data-bs-dismiss="alert" aria-label="Close"></button></div>';
}

// Global declaration for the refresh function to be accessible by DOMContentLoaded
let refresh;

setInterval(function() {
    // Execute the refresh function every 10 seconds (based on the interval value)
    if (typeof refresh === 'function') {
        refresh();
    }
}, 60000);


document.addEventListener('DOMContentLoaded', function() {
    const meetingMinutesForm = document.getElementById('meeting-minutes-form');
    const meetingStatusForm = document.getElementById('meeting-status-form');
    const meetingAttendeesForm = document.getElementById('meeting-attendees-form');
    const attendeeList = document.getElementById("attendee-list");

    // Define the async refresh function which is now accessible globally
    refresh = async function() {
        // Update meeting status.
        try {
            const statusResponse = await fetch(`/api/event/state/${CURRENT_MEETING_ID}`, {
                method: 'GET'
            });
            const statusData = await statusResponse.json();
            var submitButton = document.getElementById("meeting-status-submit");
            var statusP = document.getElementById("status-p");
            
            if (statusData == "Not Started") {
                statusP.innerHTML = `<strong>Current Status: </strong> ${statusData}`;
                if (submitButton) submitButton.innerHTML = "Start Meeting";
            } else if (statusData == "Ended") {
                statusP.innerHTML = `<strong>Current Status: </strong> ${statusData}`;
            } else {
                statusP.innerHTML = `<strong>Current Status: </strong> ${statusData}<br/><strong>Meeting Code: </strong><a href="/admin/reset-code/${CURRENT_MEETING_ID}" target="_blank">Reset Code</a>`;
                if (submitButton) submitButton.innerHTML = "End Meeting";
            }
        } catch (error) {
            console.error('Status refresh error:', error);
        }
        
        // Update meeting attendees list.
        try {
            const attendeesResponse = await fetch(`/api/event/attendees/${CURRENT_MEETING_ID}`, {
                method: 'GET'
            });
            const attendeesData = await attendeesResponse.json();
            
            // Clear the list before rebuilding
            attendeeList.innerHTML = "";
            
            for (let i = 0; i < attendeesData.length; i++) {
                const attendee = attendeesData[i];
                
                // Use a template literal to construct the full HTML structure
                const attendeeHtml = `
                    <span id="attendee-${attendee.id}">
                        ${attendee.username} 
                        <i 
                            class="fa-solid fa-user-minus remove-attendee-ajax" 
                            data-url="/admin/remove-attendee/${CURRENT_MEETING_ID}/${attendee.id}"
                            style="cursor: pointer;"
                        ></i>
                    </span>
                    <br/>
                `;
                
                // Append the new HTML to the list
                attendeeList.innerHTML += attendeeHtml;
            }
        } catch (error) {
            console.error('Attendees refresh error:', error);
        }
    };
    
    // Initial call to populate data on page load
    refresh(); 
    
    // Attach a single event listener to the static parent container
    attendeeList.addEventListener('click', function(event) {
        const targetElement = event.target;
        
        // Check if the clicked element is the remove button
        if (targetElement.classList.contains('remove-attendee-ajax')) {
            event.preventDefault(); 
            
            const targetUrl = targetElement.getAttribute('data-url');
            // The row to remove is the outer <span>
            const rowToRemove = targetElement.closest('span'); // Use .closest('span') for precision
            
            // Identify the <br> element immediately following the <span>
            const brToRemove = rowToRemove ? rowToRemove.nextElementSibling : null;

            fetch(targetUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            })
            .then(response => {
                if (response.ok) {
                    // Remove the <span> element
                    if (rowToRemove) {
                        rowToRemove.remove(); 
                    }
                    
                    // Remove the <br> element if it exists and is the next sibling
                    if (brToRemove && brToRemove.nodeName.toLowerCase() === 'br') {
                        brToRemove.remove();
                    }
                    
                    showMessage('Attendee removed successfully.');
                    return; 
                } else {
                    throw new Error(`Server responded with status: ${response.status}`);
                }
            })
            .catch(error => {
                console.error('Removal error:', error);
                showMessage('An error occurred during removal.');
            });
        }
    });

    // Form submission handlers with validation and AJAX.
    meetingMinutesForm.addEventListener('submit', async function(event) {
        event.preventDefault();
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
            if (response.ok) { 
                console.log(result);
                meetingMinutesForm.action = "/admin/minutes/" + result.meeting_id + "/" + result.minutes_id;
            } else {
                showMessage(result.message);
            }
        } catch (error) {
            console.error('Error updating minutes:', error);
            showMessage('Network error or server unreachable.');
        }
    });

    if (meetingStatusForm) {
        meetingStatusForm.addEventListener('submit', async function(event) {
            event.preventDefault();
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
                if (response.ok) { 
                    console.log(result);
                    submitButton = document.getElementById("meeting-status-submit");
                    statusP = document.getElementById("status-p");
                    console.log(meetingStatusForm.action);
                    if (meetingStatusForm.action.includes("/admin/start")) {
                        meetingStatusForm.action = "/admin/end/" + result.meeting_id + "/";
                        submitButton.innerHTML = "End Meeting";
                        statusP.innerHTML = "<strong>Current Status: </strong> Active<br/><strong>Meeting Code: </strong><a href='/admin/show-code?code=" + result.meeting_code + "' target='_blank'>" + result.meeting_code + "</a>";
                    } else {
                        meetingStatusForm.remove();
                        statusP.innerHTML = "<strong>Current Status: </strong> Ended";
                    }
                } else {
                    showMessage(result.message);
                }
            } catch (error) {
                console.error('Error updating status:', error);
                showMessage('Network error or server unreachable.');
            }
        });
    }

    meetingAttendeesForm.addEventListener('submit', async function(event) {
        event.preventDefault();
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
            if (response.ok) { 
                console.log(result);
                refresh();
            } else {
                showMessage(result.message);
            }
        } catch (error) {
            console.error('Error adding attendee:', error);
            showMessage('Network error or server unreachable.');
        }
    });

});