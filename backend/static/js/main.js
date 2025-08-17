/*
Main JavaScript for Multi-Platform Product Listing Automation
============================================================
Handles dynamic form interactions, validation, image uploads, variant generation,
and export triggers.
*/

// Global State
const state = {
    product: {},
    variants: [],
    images: [],
    platformValidation: {
        meesho: {},
        flipkart: {},
        myntra: {}
    }
};

// Utility Functions
function $(selector) {
    return document.querySelector(selector);
}

function $all(selector) {
    return document.querySelectorAll(selector);
}

function showToast(type, title, message, timeout = 4000) {
    const toastContainer = $('.toast-container');
    if (!toastContainer) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="toast-icon">🔔</span>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" aria-label="Close">✖</button>
    `;

    toast.querySelector('.toast-close').addEventListener('click', () => {
        toast.remove();
    });

    toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('fade-out');
        toast.addEventListener('transitionend', () => toast.remove());
    }, timeout);
}

function toggleSection(section) {
    section.classList.toggle('collapsed');
}

function collapseOtherSections(activeSection) {
    const sections = $all('.form-section');
    sections.forEach(section => {
        if (section !== activeSection && !section.classList.contains('collapsed')) {
            section.classList.add('collapsed');
        }
    });
}

function initCollapsibleSections() {
    const sections = $all('.form-section');
    sections.forEach(section => {
        const header = section.querySelector('.section-header');
        if (header) {
            header.addEventListener('click', () => {
                toggleSection(section);
            });
        }
    });
}

// Form Validation Functions
function validateSKU(sku) {
    if (!sku) return false;

    fetch('/api/validate-sku', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ sku: sku })
    })
    .then(response => response.json())
    .then(data => {
        const skuValidation = $('#skuValidation');
        const skuInput = $('#sku');

        if (data.valid) {
            skuInput.classList.remove('error');
            skuValidation.style.display = 'none';
            showToast('success', 'SKU Valid', `Found ${data.image_count} images for SKU: ${sku}`);

            // Update image preview
            updateImagePreview(sku, data.images);
        } else {
            skuInput.classList.add('error');
            skuValidation.textContent = data.message;
            skuValidation.style.display = 'block';
            showToast('error', 'SKU Invalid', data.message);
        }
    })
    .catch(error => {
        console.error('Error validating SKU:', error);
        showToast('error', 'Validation Error', 'Failed to validate SKU');
    });
}

function updateImagePreview(sku, images) {
    const imagePreview = $('#imagePreview');
    const imageUpload = $('#imageUpload');

    imageUpload.querySelector('h4').textContent = `📁 Images loaded from: images/${sku}/`;

    if (images && images.length > 0) {
        imagePreview.innerHTML = images.map(img => `
            <div class="image-preview-item">
                <img src="/static/images/${sku}/${img}" alt="${img}" onerror="this.src='data:image/svg+xml,<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"120\" height=\"120\"><rect width=\"120\" height=\"120\" fill=\"%23ddd\"/><text x=\"50%\" y=\"50%\" text-anchor=\"middle\" dy=\".3em\">${img}</text></svg>'">
                <div class="image-info">${img}</div>
            </div>
        `).join('');
    } else {
        imagePreview.innerHTML = '<p>No images found for this SKU</p>';
    }
}

// Variant Generation
function generateVariants() {
    const sku = $('#sku').value;
    const productType = $('#productType').value;

    if (!sku) {
        showToast('error', 'Missing SKU', 'Please enter a SKU first');
        return;
    }

    if (productType !== 'bangle') {
        showToast('info', 'Not Applicable', 'Variant generation is only for bangles');
        return;
    }

    fetch('/api/generate-variants', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            sku: sku, 
            product_type: productType 
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayVariants(data.variants);
            showToast('success', 'Variants Generated', `Created ${data.variants.length} bangle variants`);
        } else {
            showToast('error', 'Generation Failed', data.message);
        }
    })
    .catch(error => {
        console.error('Error generating variants:', error);
        showToast('error', 'Error', 'Failed to generate variants');
    });
}

function displayVariants(variants) {
    const variantsList = $('#variantsList');

    variantsList.innerHTML = variants.map(variant => `
        <div class="variant-item">
            <div class="variant-info">
                <div class="variant-size">Size: ${variant.size}</div>
                <div class="variant-sku">${variant.sku}</div>
            </div>
            <button type="button" class="btn btn-outline" onclick="removeVariant('${variant.sku}')">
                Remove
            </button>
        </div>
    `).join('');

    variantsList.style.display = 'block';
    state.variants = variants;
}

function removeVariant(sku) {
    state.variants = state.variants.filter(v => v.sku !== sku);
    displayVariants(state.variants);

    if (state.variants.length === 0) {
        $('#variantsList').style.display = 'none';
    }
}

// Form Data Collection
function collectFormData() {
    return {
        productName: $('#productName').value,
        sku: $('#sku').value,
        productType: $('#productType').value,
        description: $('#description').value,
        mrp: parseFloat($('#product_mrp').value) || 0,
        sellingPrice: parseFloat($('#meesho_price').value) || 0,
        inventory: parseInt($('#inventory').value) || 0,
        hsnCode: $('#hsnCode').value,
        material: $('#material').value,
        color: $('#color').value,
        plating: $('#plating').value,
        size: $('#size').value,
        variants: state.variants
    };
}

// Export Functions

function updatePlatformStatus(platform, status) {
    const statusCards = $all('.status-card');
    statusCards.forEach(card => {
        const cardTitle = card.querySelector('h4').textContent.toLowerCase();
        if (cardTitle.includes(platform)) {
            const indicator = card.querySelector('.status-indicator');
            indicator.className = `status-indicator status-${status}`;

            const statusText = {
                'success': 'Completed',
                'error': 'Failed',
                'ready': 'Ready',
                'pending': 'Pending'
            };

            card.querySelector('p').textContent = statusText[status] || 'Unknown';
        }
    });
}

// Progress Updates
function updateProgress() {
    const form = $('#productForm');
    const inputs = form.querySelectorAll('input[required], select[required]');
    let completed = 0;

    inputs.forEach(input => {
        if (input.value.trim() !== '') {
            completed++;
        }
    });

    const progress = Math.round((completed / inputs.length) * 100);
    $('.progress-fill').style.width = progress + '%';
}

// Product Type Change Handler
function handleProductTypeChange() {
    const productType = $('#productType').value;
    const variantSection = $('#variantSection');

    if (productType === 'bangle') {
        variantSection.style.display = 'block';
        showToast('info', 'Bangle Selected', 'You can now generate size variants');
    } else {
        variantSection.style.display = 'none';
        state.variants = [];
        $('#variantsList').style.display = 'none';
    }
}

// Form Validation
function validateForm() {
    const formData = collectFormData();
    let isValid = true;
    const errors = [];

    // Required field validation
    if (!formData.productName) {
        errors.push('Product Name is required');
        isValid = false;
    }

    if (!formData.sku) {
        errors.push('SKU is required');
        isValid = false;
    }

    if (!formData.productType) {
        errors.push('Product Type is required');
        isValid = false;
    }

    // Price validation
    if (formData.sellingPrice > formData.mrp) {
        errors.push('Selling Price cannot be higher than MRP');
        isValid = false;
    }

    if (isValid) {
        showToast('success', 'Validation Passed', 'All required fields are filled correctly');
    } else {
        showToast('error', 'Validation Failed', errors.join(', '));
    }

    return isValid;
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Initialize collapsible sections
    initCollapsibleSections();

    // SKU validation
    $('#sku').addEventListener('blur', function() {
        if (this.value) {
            validateSKU(this.value);
        }
    });

    // Product type change
    $('#productType').addEventListener('change', handleProductTypeChange);

    // Generate variants button
    $('#generateVariants').addEventListener('click', generateVariants);

    // Form validation button
    $('#validateForm').addEventListener('click', validateForm);

    // Save product button
    $('#saveProduct').addEventListener('click', function() {
        if (validateForm()) {
            const formData = collectFormData();
            console.log('Product data:', formData);
            showToast('success', 'Product Saved', 'Product data has been saved locally');
        }
    });

    // Progress monitoring
    const formInputs = $all('#productForm input, #productForm select, #productForm textarea');
    formInputs.forEach(input => {
        input.addEventListener('input', updateProgress);
    });

    // Initial progress update
    updateProgress();

    console.log('✅ Multi-Platform Product Listing Form Initialized');
});

// Global functions for HTML onclick events
window.removeVariant = removeVariant;

document.addEventListener('DOMContentLoaded', function() {
    const exportMeeshoBtn = document.getElementById('exportMeesho');
    exportMeeshoBtn.addEventListener('click', function() {
        // Collect form data
        if (!validateForm()) {
            console.log('Form validation failed, cannot export to Meesho.');
            showToast('error', 'Validation Error', 'Please fix the errors before exporting to Meesho.');
            // validateForm already displays error toasts
            return; // Stop the export process if validation fails
        }
        console.log('Exporting to Meesho...');
        const form = document.getElementById('productForm');

        // Use FormData if you want all fields easily
        const formData = new FormData(form);
        
        // Convert FormData to plain object for JSON
        const data = {};
        formData.forEach((value, key) => {
            data[key] = value;
        });

        // Optional: Validate required Meesho fields here or reuse your validation function

        // Send data to backend API route (implement this route in Flask)
        fetch('/export_meesho', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            if(result.status === 'success'){
                showToast('Meesho export succeeded!', 'success');
            } else {
                showToast('Meesho export failed: ' + result.message, 'error');
            }
        })
        .catch(err => {
            showToast('Network error: ' + err.message, 'error');
        });
    });
});

document.addEventListener('DOMContentLoaded', function() {
    const exportMeeshoBtn = document.getElementById('exportMyntra');
    exportMeeshoBtn.addEventListener('click', function() {
        // Collect form data
        if (!validateForm()) {
            console.log('Form validation failed, cannot export to Meesho.');
            showToast('error', 'Validation Error', 'Please fix the errors before exporting to Meesho.');
            // validateForm already displays error toasts
            return; // Stop the export process if validation fails
        }
        console.log('Exporting to myntra...');
        const form = document.getElementById('productForm');

        // Use FormData if you want all fields easily
        const formData = new FormData(form);
        
        // Convert FormData to plain object for JSON
        const data = {};
        formData.forEach((value, key) => {
            data[key] = value;
        });

        // Optional: Validate required myntra fields here or reuse your validation function

        // Send data to backend API route (implement this route in Flask)
        fetch('/export_myntra', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(result => {
            if(result.status === 'success'){
                showToast('Myntra export succeeded!', 'success');
            } else {
                showToast('Myntra export failed: ' + result.message, 'error');
            }
        })
        .catch(err => {
            showToast('Network error: ' + err.message, 'error');
        });
    });
});

document.getElementById("exportFlipkart").addEventListener("click", function () {
    if (!validateForm()) {
        console.log('Form validation failed, cannot export to Meesho.');
        showToast('error', 'Validation Error', 'Please fix the errors before exporting to Meesho.');
        // validateForm already displays error toasts
        return; // Stop the export process if validation fails
    }
    console.log('Exporting to Meesho...');
    const form = document.getElementById('productForm');

    // Use FormData if you want all fields easily
    const formData = new FormData(form);
    
    // Convert FormData to plain object for JSON
    const data = {};
    formData.forEach((value, key) => {
        data[key] = value;
    });
    fetch("/export_flipkart", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
    })
        .then((res) => res.json())
        .then((data) => {
            alert(data.message || "Exported to Flipkart!");
        })
        .catch((err) => {
            console.error(err);
            alert("Something went wrong while exporting to Flipkart.");
        });
});
