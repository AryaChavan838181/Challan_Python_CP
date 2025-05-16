/**
 * Traffic Challan Payment System JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Form validation for challan lookup form
    const challanForms = document.querySelectorAll('form');
    
    challanForms.forEach(form => {
        form.addEventListener('submit', function(event) {
            const inputs = form.querySelectorAll('input[required]');
            let isValid = true;
            
            inputs.forEach(input => {
                if (!input.value.trim()) {
                    isValid = false;
                    input.classList.add('is-invalid');
                    
                    // Create error message if it doesn't exist
                    if (!input.nextElementSibling || !input.nextElementSibling.classList.contains('invalid-feedback')) {
                        const errorMsg = document.createElement('div');
                        errorMsg.classList.add('invalid-feedback');
                        errorMsg.textContent = 'This field is required';
                        input.parentNode.insertBefore(errorMsg, input.nextSibling);
                    }
                } else {
                    input.classList.remove('is-invalid');
                    if (input.nextElementSibling && input.nextElementSibling.classList.contains('invalid-feedback')) {
                        input.nextElementSibling.remove();
                    }
                }
            });
            
            if (!isValid) {
                event.preventDefault();
            }
        });
    });
    
    // Vehicle number format validation (if needed)
    const vehicleNumberInput = document.getElementById('vehicleNumber');
    if (vehicleNumberInput) {
        vehicleNumberInput.addEventListener('input', function() {
            const value = this.value.toUpperCase();
            this.value = value;
            
            // Optional: Add more specific vehicle number format validation here
        });
    }
    
    // Payment form validation
    const transactionIdInput = document.getElementById('transaction_id');
    if (transactionIdInput) {
        const paymentForm = transactionIdInput.closest('form');
        
        paymentForm.addEventListener('submit', function(event) {
            if (!transactionIdInput.value.trim()) {
                event.preventDefault();
                transactionIdInput.classList.add('is-invalid');
                
                // Create error message if it doesn't exist
                if (!transactionIdInput.nextElementSibling || !transactionIdInput.nextElementSibling.classList.contains('invalid-feedback')) {
                    const errorMsg = document.createElement('div');
                    errorMsg.classList.add('invalid-feedback');
                    errorMsg.textContent = 'Please enter the transaction ID';
                    transactionIdInput.parentNode.insertBefore(errorMsg, transactionIdInput.nextSibling);
                }
            }
        });
        
        transactionIdInput.addEventListener('input', function() {
            if (this.value.trim()) {
                this.classList.remove('is-invalid');
                if (this.nextElementSibling && this.nextElementSibling.classList.contains('invalid-feedback')) {
                    this.nextElementSibling.remove();
                }
            }
        });
    }
});

/**
 * Copy UPI ID to clipboard
 */
function copyUpiId(upiId) {
    navigator.clipboard.writeText(upiId).then(() => {
        // Show success message
        const copyBtn = document.getElementById('copyUpiBtn');
        if (copyBtn) {
            const originalText = copyBtn.textContent;
            copyBtn.textContent = 'Copied!';
            copyBtn.classList.add('btn-success');
            copyBtn.classList.remove('btn-outline-secondary');
            
            setTimeout(() => {
                copyBtn.textContent = originalText;
                copyBtn.classList.remove('btn-success');
                copyBtn.classList.add('btn-outline-secondary');
            }, 2000);
        }
    }).catch(err => {
        console.error('Could not copy UPI ID: ', err);
    });
}

/**
 * Print receipt
 */
function printReceipt() {
    window.print();
}
