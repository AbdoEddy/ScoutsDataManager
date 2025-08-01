/**
 * Table configuration JavaScript for the Scout Management Application
 * Handles dynamic table configuration, field management, and reordering
 */

document.addEventListener('DOMContentLoaded', function() {
    // Handle field type changes
    const fieldTypeSelect = document.getElementById('fieldTypeSelect');
    const optionsGroup = document.getElementById('optionsGroup');
    
    if (fieldTypeSelect && optionsGroup) {
        const toggleOptionsVisibility = () => {
            if (fieldTypeSelect.value === 'dropdown') {
                optionsGroup.style.display = 'block';
            } else {
                optionsGroup.style.display = 'none';
            }
        };
        
        // Initialize visibility
        toggleOptionsVisibility();
        
        // Add event listener for changes
        fieldTypeSelect.addEventListener('change', toggleOptionsVisibility);
    }
    
    // Handle field reordering
    const initSortableFields = () => {
        const sortableFields = document.getElementById('sortableFields');
        const reorderBtn = document.getElementById('reorderBtn');
        
        if (!sortableFields || !reorderBtn) return;
        
        let sortable = null;
        let sortingEnabled = false;
        
        reorderBtn.addEventListener('click', function() {
            if (sortingEnabled) {
                // Save the new order
                const newOrder = {};
                const items = sortableFields.querySelectorAll('tr');
                
                items.forEach((item, index) => {
                    const id = item.getAttribute('data-id');
                    if (id) {
                        newOrder[id] = index + 1;
                    }
                });
                
                // Get the current URL to extract table_id
                const pathParts = window.location.pathname.split('/');
                const tableId = pathParts[pathParts.indexOf('tables') + 1];
                
                // Send the new order to the server
                fetch(`/manage_tables/${tableId}/fields/order`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ fields: newOrder }),
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showNotification('L\'ordre des champs a été mis à jour avec succès.', 'success');
                    } else {
                        showNotification('Une erreur est survenue lors de la mise à jour de l\'ordre.', 'danger');
                    }
                })
                .catch(error => {
                    console.error('Error updating field order:', error);
                    showNotification('Une erreur est survenue lors de la mise à jour de l\'ordre.', 'danger');
                })
                .finally(() => {
                    // Disable sorting
                    sortable.option("disabled", true);
                    sortingEnabled = false;
                    reorderBtn.innerHTML = '<i class="fas fa-sort me-1"></i>Réorganiser';
                    reorderBtn.classList.remove('btn-warning');
                    reorderBtn.classList.add('btn-outline-light');
                    
                    // Add highlight effect to show order was saved
                    sortableFields.classList.add('border-success');
                    setTimeout(() => {
                        sortableFields.classList.remove('border-success');
                    }, 1000);
                });
            } else {
                // Enable sorting
                if (!sortable) {
                    sortable = new Sortable(sortableFields, {
                        animation: 150,
                        ghostClass: 'sortable-ghost',
                        handle: 'td',
                        disabled: false
                    });
                } else {
                    sortable.option("disabled", false);
                }
                
                sortingEnabled = true;
                reorderBtn.innerHTML = '<i class="fas fa-save me-1"></i>Enregistrer l\'ordre';
                reorderBtn.classList.remove('btn-outline-light');
                reorderBtn.classList.add('btn-warning');
                
                // Show instructions
                showNotification('Glissez-déposez les lignes pour réorganiser les champs, puis cliquez sur "Enregistrer l\'ordre".', 'info');
            }
        });
    };
    
    initSortableFields();
    
    // Table name validator - converts display name to valid technical name
    const initTableNameValidator = () => {
        const displayNameInput = document.querySelector('input[name="display_name"]');
        const nameInput = document.querySelector('input[name="name"]');
        
        if (!displayNameInput || !nameInput) return;
        
        // Only enable auto-generation for new tables/fields, not for editing
        const isNewItem = !nameInput.value;
        
        if (isNewItem) {
            displayNameInput.addEventListener('input', function() {
                // Convert display name to valid technical name
                // (lowercase, no spaces, no special characters)
                const technicalName = this.value
                    .toLowerCase()
                    .normalize('NFD').replace(/[\u0300-\u036f]/g, '') // Remove accents
                    .replace(/[^a-z0-9_]/g, '_') // Replace non-alphanumeric with underscore
                    .replace(/_+/g, '_') // Replace multiple underscores with a single one
                    .replace(/^_|_$/g, ''); // Remove leading/trailing underscores
                
                nameInput.value = technicalName;
            });
        }
    };
    
    initTableNameValidator();
    
    // Options validator for dropdown fields
    const initOptionsValidator = () => {
        const optionsTextarea = document.querySelector('textarea[name="options"]');
        
        if (!optionsTextarea) return;
        
        optionsTextarea.addEventListener('blur', function() {
            // Ensure each line is unique and not empty
            const lines = this.value.split('\n')
                .map(line => line.trim())
                .filter(line => line.length > 0);
            
            // Remove duplicates
            const uniqueLines = [...new Set(lines)];
            
            if (lines.length !== uniqueLines.length) {
                showNotification('Les options dupliquées ont été supprimées.', 'warning');
            }
            
            this.value = uniqueLines.join('\n');
        });
    };
    
    initOptionsValidator();
    
    // Delete confirmation handler
    const initDeleteConfirmation = () => {
        document.querySelectorAll('[data-delete-type]').forEach(button => {
            button.addEventListener('click', function(e) {
                const type = this.getAttribute('data-delete-type');
                const name = this.getAttribute('data-delete-name');
                
                let message = 'Êtes-vous sûr de vouloir supprimer cet élément ?';
                
                if (type === 'table') {
                    message = `Êtes-vous sûr de vouloir supprimer la table "${name}" ? Toutes les données associées seront perdues.`;
                } else if (type === 'field') {
                    message = `Êtes-vous sûr de vouloir supprimer le champ "${name}" ? Toutes les valeurs associées seront perdues.`;
                }
                
                if (!confirm(message)) {
                    e.preventDefault();
                }
            });
        });
    };
    
    initDeleteConfirmation();
});

/**
 * Validate form before submission
 * @param {HTMLFormElement} form - The form to validate
 * @returns {boolean} - Whether the form is valid
 */
function validateTableForm(form) {
    const nameInput = form.querySelector('input[name="name"]');
    const displayNameInput = form.querySelector('input[name="display_name"]');
    
    if (!nameInput.value.trim()) {
        showNotification('Le nom technique est requis.', 'danger');
        nameInput.focus();
        return false;
    }
    
    if (!displayNameInput.value.trim()) {
        showNotification('Le nom d\'affichage est requis.', 'danger');
        displayNameInput.focus();
        return false;
    }
    
    // Validate technical name format
    const namePattern = /^[a-z][a-z0-9_]*$/;
    if (!namePattern.test(nameInput.value)) {
        showNotification('Le nom technique doit commencer par une lettre et ne contenir que des lettres minuscules, des chiffres et des underscores.', 'danger');
        nameInput.focus();
        return false;
    }
    
    return true;
}

/**
 * Validate field form before submission
 * @param {HTMLFormElement} form - The form to validate
 * @returns {boolean} - Whether the form is valid
 */
function validateFieldForm(form) {
    const nameInput = form.querySelector('input[name="name"]');
    const displayNameInput = form.querySelector('input[name="display_name"]');
    const fieldTypeSelect = form.querySelector('select[name="field_type"]');
    const optionsTextarea = form.querySelector('textarea[name="options"]');
    
    if (!nameInput.value.trim()) {
        showNotification('Le nom technique est requis.', 'danger');
        nameInput.focus();
        return false;
    }
    
    if (!displayNameInput.value.trim()) {
        showNotification('Le nom d\'affichage est requis.', 'danger');
        displayNameInput.focus();
        return false;
    }
    
    // Validate technical name format
    const namePattern = /^[a-z][a-z0-9_]*$/;
    if (!namePattern.test(nameInput.value)) {
        showNotification('Le nom technique doit commencer par une lettre et ne contenir que des lettres minuscules, des chiffres et des underscores.', 'danger');
        nameInput.focus();
        return false;
    }
    
    // Check if dropdown has options
    if (fieldTypeSelect.value === 'dropdown') {
        const options = optionsTextarea.value.split('\n')
            .map(line => line.trim())
            .filter(line => line.length > 0);
        
        if (options.length === 0) {
            showNotification('Vous devez spécifier au moins une option pour les listes déroulantes.', 'danger');
            optionsTextarea.focus();
            return false;
        }
    }
    
    return true;
}
