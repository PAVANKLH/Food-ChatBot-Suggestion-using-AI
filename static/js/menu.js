// Menu functionality for real-time price calculation and order management

document.addEventListener('DOMContentLoaded', function() {
    const itemCheckboxes = document.querySelectorAll('.item-checkbox');
    const quantityInputs = document.querySelectorAll('.quantity-input');
    const quantityButtons = document.querySelectorAll('.quantity-btn');
    const orderItemsContainer = document.getElementById('orderItems');
    const totalAmountElement = document.getElementById('totalAmount');
    const placeOrderBtn = document.getElementById('placeOrderBtn');
    
    let orderItems = {};
    let totalAmount = 0;

    // Initialize event listeners
    initializeEventListeners();

    function initializeEventListeners() {
        // Checkbox change events
        itemCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', handleItemSelection);
        });

        // Quantity input events
        quantityInputs.forEach(input => {
            input.addEventListener('input', handleQuantityChange);
        });

        // Quantity button events
        quantityButtons.forEach(button => {
            button.addEventListener('click', handleQuantityButton);
        });
    }

    function handleItemSelection(event) {
        const checkbox = event.target;
        const itemId = checkbox.value;
        const itemPrice = parseFloat(checkbox.dataset.price);
        const itemName = checkbox.closest('.card').querySelector('.card-title').textContent;
        const quantityControl = checkbox.closest('.card-body').querySelector('.quantity-control');
        const quantityInput = document.getElementById(`quantity_${itemId}`);

        if (checkbox.checked) {
            // Show quantity control with animation
            quantityControl.style.display = 'block';
            quantityControl.classList.add('fade-in');
            
            // Add item to order
            const quantity = parseInt(quantityInput.value);
            orderItems[itemId] = {
                name: itemName,
                price: itemPrice,
                quantity: quantity,
                total: itemPrice * quantity
            };
        } else {
            // Hide quantity control
            quantityControl.style.display = 'none';
            quantityControl.classList.remove('fade-in');
            
            // Remove item from order
            delete orderItems[itemId];
        }

        updateOrderSummary();
    }

    function handleQuantityChange(event) {
        const input = event.target;
        const itemId = input.dataset.itemId;
        const itemPrice = parseFloat(input.dataset.price);
        const quantity = parseInt(input.value) || 1;

        // Ensure minimum quantity of 1
        if (quantity < 1) {
            input.value = 1;
            return;
        }

        // Update order item if it exists
        if (orderItems[itemId]) {
            orderItems[itemId].quantity = quantity;
            orderItems[itemId].total = itemPrice * quantity;
            updateOrderSummary();
        }
    }

    function handleQuantityButton(event) {
        const button = event.target.closest('.quantity-btn');
        const action = button.dataset.action;
        const targetId = button.dataset.target;
        const input = document.getElementById(targetId);
        let currentValue = parseInt(input.value) || 1;

        if (action === 'increase') {
            currentValue++;
        } else if (action === 'decrease' && currentValue > 1) {
            currentValue--;
        }

        input.value = currentValue;
        
        // Trigger input event to update calculations
        input.dispatchEvent(new Event('input'));
    }

    function updateOrderSummary() {
        const itemCount = Object.keys(orderItems).length;
        
        if (itemCount === 0) {
            // Show empty state
            orderItemsContainer.innerHTML = `
                <div class="text-center text-muted py-3">
                    <i class="fas fa-shopping-cart fa-2x mb-2"></i>
                    <p>No items selected</p>
                </div>
            `;
            totalAmount = 0;
            placeOrderBtn.disabled = true;
        } else {
            // Show order items
            let itemsHTML = '';
            totalAmount = 0;

            for (const [itemId, item] of Object.entries(orderItems)) {
                totalAmount += item.total;
                itemsHTML += `
                    <div class="order-item fade-in">
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <strong>${item.name}</strong>
                                <div class="text-muted small">$${item.price.toFixed(2)} × ${item.quantity}</div>
                            </div>
                            <div class="fw-bold text-success">
                                $${item.total.toFixed(2)}
                            </div>
                        </div>
                    </div>
                `;
            }

            orderItemsContainer.innerHTML = itemsHTML;
            placeOrderBtn.disabled = false;
        }

        // Update total amount with animation
        totalAmountElement.style.transform = 'scale(1.1)';
        totalAmountElement.textContent = `$${totalAmount.toFixed(2)}`;
        
        setTimeout(() => {
            totalAmountElement.style.transform = 'scale(1)';
        }, 200);

        // Add transition effect
        totalAmountElement.style.transition = 'transform 0.2s ease-in-out';
    }

    // Form submission validation
    document.getElementById('orderForm').addEventListener('submit', function(event) {
        if (Object.keys(orderItems).length === 0) {
            event.preventDefault();
            showNotification('Please select at least one item to order.', 'warning');
            return;
        }

        // Add loading state
        placeOrderBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Placing Order...';
        placeOrderBtn.disabled = true;
    });

    // Utility function to show notifications
    function showNotification(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        const container = document.querySelector('.container');
        container.insertBefore(alertDiv, container.firstChild);

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            alertDiv.classList.remove('show');
            setTimeout(() => alertDiv.remove(), 150);
        }, 5000);
    }

    // Add smooth scrolling for better UX
    function smoothScrollTo(element) {
        element.scrollIntoView({
            behavior: 'smooth',
            block: 'center'
        });
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', function(event) {
        // Press 'O' to focus on place order button
        if (event.key.toLowerCase() === 'o' && !event.ctrlKey && !event.altKey) {
            if (!placeOrderBtn.disabled) {
                placeOrderBtn.focus();
                smoothScrollTo(placeOrderBtn);
            }
        }
    });

    // Add visual feedback for interactions
    itemCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const card = this.closest('.card');
            if (this.checked) {
                card.classList.add('border-success');
                card.style.borderWidth = '2px';
            } else {
                card.classList.remove('border-success');
                card.style.borderWidth = '';
            }
        });
    });

    // Initialize page with fade-in animation
    document.body.classList.add('fade-in');
});
