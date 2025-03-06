// Client-side functionality for the case management system

document.addEventListener('DOMContentLoaded', function() {
    // Fade out flash messages after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            alert.style.transition = 'opacity 1s';
            alert.style.opacity = 0;
            setTimeout(function() {
                alert.remove();
            }, 1000);
        });
    }, 5000);

    // Add status class to status cells in tables
    const statusCells = document.querySelectorAll('td:nth-child(5)');
    statusCells.forEach(function(cell) {
        const status = cell.textContent.trim();
        if (status === 'Ny') {
            cell.classList.add('status-new');
        } else if (status === 'Pågående') {
            cell.classList.add('status-ongoing');
        } else if (status === 'Vilande') {
            cell.classList.add('status-paused');
        } else if (status === 'Avslutad') {
            cell.classList.add('status-completed');
        }
    });

    // Date fields conversion to/from ISO format
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(function(input) {
        // Format date when displaying
        if (input.value) {
            const date = new Date(input.value);
            if (!isNaN(date)) {
                input.value = date.toISOString().split('T')[0];
            }
        }

        // Make sure date is in ISO format when submitting
        input.addEventListener('change', function() {
            const date = new Date(this.value);
            if (!isNaN(date)) {
                this.value = date.toISOString().split('T')[0];
            }
        });
    });

    // Search functionality for case list
    const searchInput = document.getElementById('search-case');
    if (searchInput) {
        searchInput.addEventListener('keyup', function() {
            const searchTerm = this.value.toLowerCase();
            const caseRows = document.querySelectorAll('tbody tr');

            caseRows.forEach(function(row) {
                const text = row.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }

    // Confirm delete or close actions
    const confirmButtons = document.querySelectorAll('.confirm-action');
    confirmButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            const message = this.getAttribute('data-confirm') || 'Är du säker?';
            if (!confirm(message)) {
                event.preventDefault();
            }
        });
    });
});