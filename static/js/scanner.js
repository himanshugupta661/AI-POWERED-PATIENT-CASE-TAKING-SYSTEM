/**
 * Doctor QR and Barcode Scanner Service
 * Powered by html5-qrcode with camera stream, file upload, and manual entry fallback.
 */

let html5QrCodeScanner = null;

function initCameraScanner(readerId = 'reader') {
    const readerDiv = document.getElementById(readerId);
    if (!readerDiv) return;

    if (typeof Html5Qrcode === 'undefined') {
        alert('Scanner library is loading. Please refresh or enter the Case ID manually below.');
        return;
    }

    if (html5QrCodeScanner) {
        stopCameraScanner();
        return;
    }

    html5QrCodeScanner = new Html5Qrcode(readerId);

    const config = {
        fps: 10,
        qrbox: { width: 250, height: 250 },
        aspectRatio: 1.0
    };

    const statusEl = document.getElementById('scannerStatus');
    if (statusEl) {
        statusEl.innerHTML = `<span class="text-primary"><i class="fa-solid fa-camera fa-fade me-1"></i> Requesting camera access...</span>`;
    }

    html5QrCodeScanner.start(
        { facingMode: "environment" },
        config,
        (decodedText, decodedResult) => {
            // Successfully scanned
            console.log(`Scan result: ${decodedText}`);
            handleScanSuccess(decodedText);
        },
        (errorMessage) => {
            // Frame parse error (normal while searching for QR)
        }
    ).then(() => {
        if (statusEl) {
            statusEl.innerHTML = `<span class="text-success"><i class="fa-solid fa-circle-check me-1"></i> Camera active. Align QR or Barcode within box.</span>`;
        }
        const btnToggle = document.getElementById('btnToggleCamera');
        if (btnToggle) {
            btnToggle.innerHTML = `<i class="fa-solid fa-stop me-1"></i> Stop Camera`;
            btnToggle.classList.replace('btn-primary-custom', 'btn-danger');
        }
    }).catch(err => {
        console.error('Camera start error:', err);
        if (statusEl) {
            statusEl.innerHTML = `<span class="text-warning"><i class="fa-solid fa-triangle-exclamation me-1"></i> Camera permission denied or device not found. Use manual Case ID entry below.</span>`;
        }
        html5QrCodeScanner = null;
    });
}

function stopCameraScanner() {
    if (html5QrCodeScanner) {
        html5QrCodeScanner.stop().then(() => {
            html5QrCodeScanner.clear();
            html5QrCodeScanner = null;
            const statusEl = document.getElementById('scannerStatus');
            if (statusEl) {
                statusEl.innerHTML = `<span class="text-muted">Camera stopped.</span>`;
            }
            const btnToggle = document.getElementById('btnToggleCamera');
            if (btnToggle) {
                btnToggle.innerHTML = `<i class="fa-solid fa-camera me-1"></i> Start Camera Scanner`;
                btnToggle.classList.replace('btn-danger', 'btn-primary-custom');
            }
        }).catch(err => {
            console.error('Failed to stop camera scanner:', err);
        });
    }
}

async function handleScanSuccess(scannedCode) {
    stopCameraScanner();

    const statusEl = document.getElementById('scannerStatus');
    if (statusEl) {
        statusEl.innerHTML = `<span class="text-primary"><i class="fa-solid fa-spinner fa-spin me-1"></i> Verifying access authorization...</span>`;
    }

    try {
        const response = await fetch('/api/verify-scanner-code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: scannedCode })
        });

        const result = await response.json();
        if (result.success && result.redirect_url) {
            if (statusEl) {
                statusEl.innerHTML = `<span class="text-success fw-bold"><i class="fa-solid fa-circle-check me-1"></i> Case Verified! Loading clinical record...</span>`;
            }
            window.location.href = result.redirect_url;
        } else {
            alert(`Scan Error: ${result.error || 'Invalid QR code or Case ID.'}`);
            if (statusEl) {
                statusEl.innerHTML = `<span class="text-danger"><i class="fa-solid fa-triangle-exclamation me-1"></i> ${result.error || 'Access denied.'}</span>`;
            }
        }
    } catch (err) {
        console.error('Scanner verification error:', err);
        alert('Server connection error. Please try again or use manual Case ID search.');
    }
}

function scanUploadedImage(inputElement) {
    if (!inputElement.files || inputElement.files.length === 0) return;
    const file = inputElement.files[0];

    const scanner = new Html5Qrcode("reader");
    scanner.scanFile(file, true)
        .then(decodedText => {
            handleScanSuccess(decodedText);
        })
        .catch(err => {
            alert('Could not find a valid QR code in the uploaded image. Please try another photo or enter Case ID manually.');
        });
}
