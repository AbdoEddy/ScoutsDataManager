/**
 * Form builder JavaScript for the Scout Management Application
 * Handles dynamic form generation and validation
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dynamic form validation
    initFormValidation();
    
    // Initialize any dynamic form fields
    initDynamicFields();
});

/**
 * Initialize form validation for all forms
 */
function initFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        // Skip forms with no-validate class
        if (form.classList.contains('no-validate')) return;
        
        form.addEventListener('submit', function(event) {
            let isValid = true;
            
            // Check all required inputs
            const requiredInputs = form.querySelectorAll('[required]');
            requiredInputs.forEach(input => {
                if (!validateInput(input)) {
                    isValid = false;
                }
            });
            
            // Check all inputs with pattern
            const patternInputs = form.querySelectorAll('[pattern]');
            patternInputs.forEach(input => {
                if (input.value && !validatePattern(input)) {
                    isValid = false;
                }
            });
            
            // Prevent form submission if validation fails
            if (!isValid) {
                event.preventDefault();
                showNotification('Veuillez corriger les erreurs dans le formulaire.', 'danger');
            }
        });
        
        // Add validation on input for better user experience
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                if (input.required) {
                    validateInput(input);
                }
                if (input.pattern && input.value) {
                    validatePattern(input);
                }
            });
        });
    });
}

/**
 * Validate an input field for required value
 * @param {HTMLElement} input - The input element to validate
 * @returns {boolean} - Whether the input is valid
 */
function validateInput(input) {
    let isValid = true;
    const errorMsg = input.getAttribute('data-error-message') || 'Ce champ est requis.';
    
    // Remove any existing error message
    const existingError = input.parentNode.querySelector('.invalid-feedback');
    if (existingError) {
        existingError.remove();
    }
    
    // Check if the input is empty
    if (input.tagName === 'SELECT') {
        isValid = input.value !== '';
    } else if (input.type === 'checkbox' || input.type === 'radio') {
        const name = input.name;
        const checked = document.querySelector(`input[name="${name}"]:checked`);
        isValid = checked !== null;
    } else {
        isValid = input.value.trim() !== '';
    }
    
    // Show/hide error message
    if (!isValid) {
        input.classList.add('is-invalid');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = errorMsg;
        input.parentNode.appendChild(errorDiv);
    } else {
        input.classList.remove('is-invalid');
    }
    
    return isValid;
}

/**
 * Validate an input against its pattern
 * @param {HTMLElement} input - The input element to validate
 * @returns {boolean} - Whether the input matches the pattern
 */
function validatePattern(input) {
    const pattern = new RegExp(input.pattern);
    const isValid = pattern.test(input.value);
    const errorMsg = input.getAttribute('data-pattern-message') || 'Format invalide.';
    
    // Remove any existing error message
    const existingError = input.parentNode.querySelector('.invalid-feedback');
    if (existingError) {
        existingError.remove();
    }
    
    // Show/hide error message
    if (!isValid) {
        input.classList.add('is-invalid');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.textContent = errorMsg;
        input.parentNode.appendChild(errorDiv);
    } else {
        input.classList.remove('is-invalid');
    }
    
    return isValid;
}

/**
 * Initialize dynamic form fields (datepickers, etc.)
 */
function initDynamicFields() {
    // Format date fields nicely
    document.querySelectorAll('input[type="date"]').forEach(dateInput => {
        // Add placeholder
        dateInput.setAttribute('placeholder', 'jj/mm/aaaa');
        
        // Add change event to format display
        dateInput.addEventListener('change', function() {
            if (this.value) {
                const date = new Date(this.value);
                // Display in French format but keep ISO format for the value
                const displayDate = date.toLocaleDateString('fr-FR');
                
                // Create a display element if it doesn't exist
                let displayElement = this.parentNode.querySelector('.date-display');
                if (!displayElement) {
                    displayElement = document.createElement('div');
                    displayElement.className = 'date-display small text-muted mt-1';
                    this.parentNode.appendChild(displayElement);
                }
                
                displayElement.textContent = `Date sélectionnée: ${displayDate}`;
            }
        });
    });
    
    // Add numeric validation for number fields
    document.querySelectorAll('input[type="number"]').forEach(numberInput => {
        numberInput.addEventListener('input', function() {
            // Replace any non-numeric characters
            this.value = this.value.replace(/[^0-9.-]/g, '');
        });
    });
    
    // Initialize character counters for text areas
    document.querySelectorAll('textarea[maxlength]').forEach(textarea => {
        const maxLength = parseInt(textarea.getAttribute('maxlength'));
        
        // Create counter element
        const counter = document.createElement('div');
        counter.className = 'char-counter small text-muted text-end mt-1';
        counter.textContent = `0/${maxLength} caractères`;
        textarea.parentNode.appendChild(counter);
        
        // Update counter on input
        textarea.addEventListener('input', function() {
            const currentLength = this.value.length;
            counter.textContent = `${currentLength}/${maxLength} caractères`;
            
            // Add warning when approaching limit
            if (currentLength > maxLength * 0.9) {
                counter.classList.add('text-warning');
            } else {
                counter.classList.remove('text-warning');
            }
        });
    });
}

/**
 * Create a dynamic form based on field definitions
 * @param {Array} fields - Array of field objects
 * @param {Object} values - Optional values to populate the form
 * @param {HTMLElement} container - Container element to append the form
 * @param {boolean} readOnly - Whether the form should be read-only
 */
function createDynamicForm(fields, values, container, readOnly = false) {
    if (!container) return;
    
    // Clear the container
    container.innerHTML = '';
    
    // Create form elements for each field
    fields.forEach(field => {
        const formGroup = document.createElement('div');
        formGroup.className = 'mb-3';
        
        // Create label
        const label = document.createElement('label');
        label.className = 'form-label';
        label.textContent = field.display_name;
        if (field.required) {
            label.innerHTML += ' <span class="text-danger">*</span>';
        }
        formGroup.appendChild(label);
        
        let input;
        
        switch (field.type) {
            case 'text':
                input = document.createElement('input');
                input.type = 'text';
                input.className = 'form-control';
                if (values && values[field.name]) {
                    input.value = values[field.name];
                }
                break;
                
            case 'number':
                input = document.createElement('input');
                input.type = 'number';
                input.className = 'form-control';
                input.step = 'any';
                if (values && values[field.name] !== null && values[field.name] !== undefined) {
                    input.value = values[field.name];
                }
                break;
                
            case 'date':
                input = document.createElement('input');
                input.type = 'date';
                input.className = 'form-control';
                if (values && values[field.name]) {
                    input.value = values[field.name];
                }
                break;
                
            case 'dropdown':
                input = document.createElement('select');
                input.className = 'form-select';
                
                // Add empty option
                const emptyOption = document.createElement('option');
                emptyOption.value = '';
                emptyOption.textContent = 'Sélectionnez une option';
                input.appendChild(emptyOption);
                
                // Add options
                if (field.options) {
                    field.options.forEach(option => {
                        const optionElement = document.createElement('option');
                        optionElement.value = option;
                        optionElement.textContent = option;
                        
                        if (values && values[field.name] === option) {
                            optionElement.selected = true;
                        }
                        
                        input.appendChild(optionElement);
                    });
                }
                break;
                
            default:
                input = document.createElement('input');
                input.type = 'text';
                input.className = 'form-control';
                if (values && values[field.name]) {
                    input.value = values[field.name];
                }
        }
        
        // Set common properties
        input.id = `field_${field.id}`;
        input.name = `field_${field.id}`;
        
        if (field.required) {
            input.required = true;
        }
        
        if (readOnly) {
            input.disabled = true;
        }
        
        formGroup.appendChild(input);
        container.appendChild(formGroup);
    });
    
    // Add submit button if not read-only
    if (!readOnly) {
        const buttonGroup = document.createElement('div');
        buttonGroup.className = 'd-flex justify-content-end mt-4';
        
        const cancelBtn = document.createElement('a');
        cancelBtn.className = 'btn btn-outline-secondary me-2';
        cancelBtn.textContent = 'Annuler';
        cancelBtn.href = '#';
        cancelBtn.onclick = (e) => {
            e.preventDefault();
            history.back();
        };
        
        const submitBtn = document.createElement('button');
        submitBtn.type = 'submit';
        submitBtn.className = 'btn btn-primary';
        submitBtn.innerHTML = '<i class="fas fa-save me-1"></i>Enregistrer';
        
        buttonGroup.appendChild(cancelBtn);
        buttonGroup.appendChild(submitBtn);
        container.appendChild(buttonGroup);
    }
}
