/**
 * JsBarcode Client Integration - PatientCase AI
 * Generates Code 128 standard barcode on SVG element and handles download.
 */

function renderBarcode(targetSvgId, barcodeValue) {
    const targetElement = document.getElementById(targetSvgId);
    if (!targetElement || !barcodeValue) return;

    if (typeof JsBarcode !== 'undefined') {
        try {
            JsBarcode(targetElement, barcodeValue, {
                format: "CODE128",
                lineColor: "#0f172a",
                width: 2.2,
                height: 70,
                displayValue: true,
                fontSize: 14,
                font: "monospace",
                textMargin: 6
            });
        } catch (e) {
            console.error('JsBarcode rendering error:', e);
        }
    } else {
        console.warn('JsBarcode library is not loaded.');
    }
}

function downloadBarcodeSVG(targetSvgId, fileName = 'patientcase-barcode.svg') {
    const svgElement = document.getElementById(targetSvgId);
    if (!svgElement) return;

    const serializer = new XMLSerializer();
    let source = serializer.serializeToString(svgElement);

    if (!source.match(/^<svg[^>]+xmlns="http\:\/\/www\.w3\.org\/2000\/svg"/)) {
        source = source.replace(/^<svg/, '<svg xmlns="http://www.w3.org/2000/svg"');
    }

    const svgBlob = new Blob([source], { type: "image/svg+xml;charset=utf-8" });
    const svgUrl = URL.createObjectURL(svgBlob);
    const downloadLink = document.createElement("a");
    downloadLink.href = svgUrl;
    downloadLink.download = fileName;
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}
