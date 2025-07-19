document.addEventListener('DOMContentLoaded', function() {
    const meetingMinutesForm = document.getElementById('meeting-minutes-form');

    meetingMinutesForm.addEventListener('submit', async function(event) {
        event.preventDefault(); // Prevent default form submission

        // Bootstrap form validation
        if (!this.checkValidity()) {
            event.stopPropagation();
            this.classList.add('was-validated');
            return;
        }
        this.classList.remove('was-validated'); // Remove validation class on successful submit attempt

        const formData = new FormData(meetingMinutesForm);

        try {
            const response = await fetch(meetingMinutesForm.action, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) { // Check if HTTP status is 2xx
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

    // --- Helper function to display messages ---
    function showMessage(message) {
        const element = document.getElementById('error-row');
        element.innerHTML += '<div class="alert alert-dismissible fade show" role="alert">' + message + '<button type="button" class="btn-close btn-close-white" data-bs-dismiss="alert" aria-label="Close"></button></div>';
    }
});