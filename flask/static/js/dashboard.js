document.addEventListener('DOMContentLoaded', function() {
    // --- User Info Form Handling ---
    const updateUserForm = document.getElementById('updateUserForm');
    const userNameDisplay = document.getElementById('userName');
    const userEmailDisplay = document.getElementById('userEmail');
    const userLastUpdatedDisplay = document.getElementById('userLastUpdated');
    const userFormMessage = document.getElementById('userFormMessage');
    const userFormSpinner = document.getElementById('userFormSpinner');

    updateUserForm.addEventListener('submit', async function(event) {
        event.preventDefault(); // Prevent default form submission

        // Bootstrap form validation
        if (!this.checkValidity()) {
            event.stopPropagation();
            this.classList.add('was-validated');
            return;
        }
        this.classList.remove('was-validated'); // Remove validation class on successful submit attempt

        userFormSpinner.style.display = 'inline-block'; // Show spinner
        userFormMessage.style.display = 'none'; // Hide previous messages

        const formData = new FormData(updateUserForm);
        const data = Object.fromEntries(formData.entries()); // Convert FormData to a plain object

        try {
            const response = await fetch('/api/update_user_info', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (response.ok) { // Check if HTTP status is 2xx
                userNameDisplay.textContent = result.data.name;
                userEmailDisplay.textContent = result.data.email;
                userLastUpdatedDisplay.textContent = result.data.last_updated;
                showMessage(userFormMessage, result.message, 'success');
                updateUserForm.reset(); // Clear form fields
            } else {
                showMessage(userFormMessage, result.message || 'An error occurred.', 'danger');
            }
        } catch (error) {
            console.error('Error updating user info:', error);
            showMessage(userFormMessage, 'Network error or server unreachable.', 'danger');
        } finally {
            userFormSpinner.style.display = 'none'; // Hide spinner
        }
    });

    // --- Product Stats Refresh Button Handling ---
    const refreshProductStatsBtn = document.getElementById('refreshProductStatsBtn');
    const totalProductsDisplay = document.getElementById('totalProducts');
    const activeProductsDisplay = document.getElementById('activeProducts');
    const productLastUpdatedDisplay = document.getElementById('productLastUpdated');
    const productStatsMessage = document.getElementById('productStatsMessage');
    const productStatsSpinner = document.getElementById('productStatsSpinner');

    refreshProductStatsBtn.addEventListener('click', async function() {
        productStatsSpinner.style.display = 'inline-block'; // Show spinner
        productStatsMessage.style.display = 'none'; // Hide previous messages

        try {
            const response = await fetch('/api/get_product_stats', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();

            if (response.ok) {
                totalProductsDisplay.textContent = result.data.total_products;
                activeProductsDisplay.textContent = result.data.active_products;
                productLastUpdatedDisplay.textContent = result.data.last_updated;
                showMessage(productStatsMessage, result.message, 'success');
            } else {
                showMessage(productStatsMessage, result.message || 'An error occurred.', 'danger');
            }
        } catch (error) {
            console.error('Error fetching product stats:', error);
            showMessage(productStatsMessage, 'Network error or server unreachable.', 'danger');
        } finally {
            productStatsSpinner.style.display = 'none'; // Hide spinner
        }
    });

    // --- Helper function to display messages ---
    function showMessage(element, message, type) {
        element.textContent = message;
        element.className = `alert-message alert-${type}`; // Reset classes and set new type
        element.style.display = 'block';
    }
});