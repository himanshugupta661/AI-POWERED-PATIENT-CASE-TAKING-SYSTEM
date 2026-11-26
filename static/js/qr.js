/**
 * QRCode.js Client Integration - PatientCase AI
 * Renders QR code on HTML element and enables PNG image download.
 */

function renderQRCode(containerId, textPayload, size = 180) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = '';

    if (typeof QRCode !== 'undefined') {
        new QRCode(container, {
            text: textPayload,
            width: size,
            height: size,
            colorDark: "#0f172a",
            colorLight: "#ffffff",
            correctLevel: QRCode.CorrectLevel.M
        });
    } else {
        console.warn('QRCode library not loaded yet.');
    }
}

function downloadQRCodePNG(containerId, fileName = 'patientcase-qr.png') {
    const container = document.getElementById(containerId);
    if (!container) return;

    const img = container.querySelector('img');
    const canvas = container.querySelector('canvas');

    let dataUrl = null;
    if (img && img.src) {
        dataUrl = img.src;
    } else if (canvas) {
        dataUrl = canvas.toDataURL('image/png');
    }

    if (dataUrl) {
        const link = document.createElement('a');
        link.download = fileName;
        link.href = dataUrl;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    } else {
        alert('QR code image could not be downloaded.');
    }
}
