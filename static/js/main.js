
/**
 * Main JavaScript file for the Scout Management Application
 * Provides general functionality used across the application
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-close alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Enhanced theme handling with localStorage (more reliable for nginx)
    function applyTheme(theme) {
        console.log(`Applying theme: ${theme}`);
        
        // Store in localStorage
        localStorage.setItem('theme', theme);
        
        // Remove existing theme attributes/classes
        document.documentElement.removeAttribute('data-bs-theme');
        document.body.removeAttribute('data-bs-theme');
        
        // Apply new theme
        document.documentElement.setAttribute('data-bs-theme', theme);
        document.body.setAttribute('data-bs-theme', theme);
        
        // Force style recalculation
        document.documentElement.style.display = 'none';
        document.documentElement.offsetHeight; // Trigger reflow
        document.documentElement.style.display = '';
        
        // Update navbar classes
        const navbar = document.querySelector('.navbar');
        if (navbar) {
            navbar.classList.remove('navbar-dark', 'navbar-light', 'bg-dark', 'bg-light');
            if (theme === 'dark') {
                navbar.classList.add('navbar-dark', 'bg-dark');
            } else {
                navbar.classList.add('navbar-light', 'bg-light');
            }
        }
        
        // Update all Bootstrap components
        const components = document.querySelectorAll('.card, .modal, .dropdown-menu, .alert, .form-control, .form-select, .table');
        components.forEach(component => {
            component.setAttribute('data-bs-theme', theme);
        });
        
        console.log(`Theme applied: ${theme}`);
    }

    // Get initial theme (prefer localStorage over cookie for nginx compatibility)
    let currentTheme = localStorage.getItem('theme');
    if (!currentTheme) {
        // Fallback to cookie if localStorage is empty
        const themeCookie = document.cookie.split(';').find(c => c.trim().startsWith('theme='));
        currentTheme = themeCookie ? themeCookie.split('=')[1] : 'dark';
        localStorage.setItem('theme', currentTheme);
    }

    // Apply initial theme immediately
    applyTheme(currentTheme);

    // Set up theme change listeners
    const themeInputs = document.querySelectorAll('input[name="theme"]');
    themeInputs.forEach(input => {
        // Set initial radio button state
        if (input.value === currentTheme) {
            input.checked = true;
        }
        
        input.addEventListener('change', function() {
            if (this.checked) {
                const theme = this.value;
                console.log(`Theme change requested: ${theme}`);
                
                // Apply theme immediately
                applyTheme(theme);
                
                // Also set cookie for server-side consistency
                document.cookie = `theme=${theme};path=/;max-age=31536000;SameSite=Strict`;
                
                // Update all radio buttons
                themeInputs.forEach(radio => {
                    radio.checked = (radio.value === theme);
                });
            }
        });
    });

    // Add 'active' class to appropriate nav item based on current URL
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');

    navLinks.forEach(link => {
        const linkPath = link.getAttribute('href');
        if (linkPath && (currentPath === linkPath || 
            (linkPath !== '/' && currentPath.startsWith(linkPath)))) {
            link.classList.add('active');

            // If this is inside a dropdown, also set the parent dropdown as active
            const dropdown = link.closest('.dropdown');
            if (dropdown) {
                const dropdownToggle = dropdown.querySelector('.dropdown-toggle');
                if (dropdownToggle) {
                    dropdownToggle.classList.add('active');
                }
            }
        }
    });

    // Enable data-confirm functionality for dangerous actions
    document.addEventListener('click', function(event) {
        if (event.target.hasAttribute('data-confirm')) {
            const message = event.target.getAttribute('data-confirm');
            if (!confirm(message || 'Êtes-vous sûr de vouloir effectuer cette action ?')) {
                event.preventDefault();
            }
        }
    });

    // Format date inputs to french format
    const formatDateDisplay = () => {
        document.querySelectorAll('td[data-date]').forEach(cell => {
            const dateValue = cell.getAttribute('data-date');
            if (dateValue) {
                try {
                    const date = new Date(dateValue);
                    if (!isNaN(date)) {
                        const formattedDate = date.toLocaleDateString('fr-FR', {
                            day: '2-digit',
                            month: '2-digit',
                            year: 'numeric'
                        });
                        cell.textContent = formattedDate;
                    }
                } catch (e) {
                    console.error('Error formatting date', e);
                }
            }
        });
    };

    formatDateDisplay();

    // Mobile responsive adjustments
    const adjustForMobile = () => {
        const isMobile = window.innerWidth < 768;

        // Adjust tables for mobile viewing
        const tables = document.querySelectorAll('.table-responsive table');
        tables.forEach(table => {
            if (isMobile) {
                table.classList.add('table-sm');
            } else {
                table.classList.remove('table-sm');
            }
        });
    };

    // Call once on load and then on window resize
    adjustForMobile();
    window.addEventListener('resize', adjustForMobile);
});

/**
 * Function to confirm dangerous actions
 * @param {string} message - The confirmation message to display
 * @returns {boolean} - Whether the action was confirmed
 */
function confirmAction(message = 'Êtes-vous sûr de vouloir effectuer cette action ?') {
    return confirm(message);
}

/**
 * Function to format numbers for display
 * @param {number} value - The numeric value to format
 * @param {number} decimals - Number of decimal places (default: 2)
 * @returns {string} - Formatted number
 */
function formatNumber(value, decimals = 2) {
    if (value === null || value === undefined || isNaN(value)) {
        return '-';
    }
    return parseFloat(value).toLocaleString('fr-FR', {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals
    });
}

/**
 * Function to format dates for display
 * @param {string} dateStr - Date string in ISO format
 * @returns {string} - Formatted date string
 */
function formatDate(dateStr) {
    if (!dateStr) return '-';

    try {
        const date = new Date(dateStr);
        if (isNaN(date.getTime())) return dateStr;

        return date.toLocaleDateString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    } catch (e) {
        console.error('Error formatting date', e);
        return dateStr;
    }
}

/**
 * Show a custom notification using Bootstrap alerts
 * @param {string} message - The message to display
 * @param {string} type - Alert type (success, danger, warning, info)
 * @param {number} duration - How long to show the alert (ms)
 */
function showNotification(message, type = 'info', duration = 5000) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show notification-alert`;
    alertDiv.role = 'alert';

    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    // Create alerts container if it doesn't exist
    let alertsContainer = document.getElementById('alerts-container');
    if (!alertsContainer) {
        alertsContainer = document.createElement('div');
        alertsContainer.id = 'alerts-container';
        alertsContainer.className = 'position-fixed bottom-0 end-0 p-3';
        alertsContainer.style.zIndex = '1050';
        document.body.appendChild(alertsContainer);
    }

    alertsContainer.appendChild(alertDiv);

    // Auto remove after duration
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => alertDiv.remove(), 150);
    }, duration);
}

async function printGenericText() {
    // Get generic text content
    const textResponse = await fetch('/api/generic_text/autorisation_camp');
    const textData = await textResponse.json();
    
    // Get print template
    const templateResponse = await fetch('/api/print_template/active');
    const template = await templateResponse.json();
    
    const printWindow = window.open('', '_blank', 'width=800,height=600');
    if (!printWindow) {
        showNotification('Impossible d\'ouvrir la fenêtre d\'impression. Vérifiez les paramètres de votre navigateur.', 'warning');
        return;
    }

    printWindow.document.write(`
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <title>Autorisation de Camp</title>
            <style>
                @media print {
                    body { margin: 0; padding: 20mm; }
                    .no-print { display: none; }
                }
                .content {
                    margin: 20px 0;
                }
                ${template.css || ''}
            </style>
            <script>
                window.onload = function() {
                    window.print();
                }
            </script>
        </head>
        <body>
            <div class="header">
                ${template.logo_url ? `<img src="${template.logo_url}" alt="Logo" style="max-height: 100px; margin-bottom: 20px;"><br>` : ''}
                ${template.header_html || ''}
            </div>
            <div class="content">
                ${textData.content}
            </div>
            <div class="footer">
                ${template.footer_html ? template.footer_html.replace('${date}', new Date().toLocaleDateString('fr-FR')) : ''}
            </div>
        </body>
        </html>
    `);
    printWindow.document.close();
}

async function printRecord(tableId, recordId) {
    const printWindow = window.open(`/tables/${tableId}/records/${recordId}/pdf`, '_blank');
    if (!printWindow) {
        showNotification('Impossible d\'ouvrir une fenêtre d\'impression. Veuillez vérifier les paramètres de votre navigateur.', 'warning');
    }
}

