import html

def format_barcode_payload(public_case_id: str) -> str:
    """
    Format standard public case ID (e.g., PC-2026-A8F4K2) into
    a compact alphanumeric Code 128 barcode value (e.g., PC2026A8F4K2).
    """
    if not public_case_id:
        return ""
    return public_case_id.replace('-', '').upper().strip()

def format_display_case_id(barcode_payload: str) -> str:
    """
    Convert a barcode payload back into display format PC-YYYY-XXXXXX.
    """
    if not barcode_payload:
        return ""
    clean = barcode_payload.replace('-', '').upper().strip()
    if len(clean) == 12 and clean.startswith('PC'):
        return f"{clean[:2]}-{clean[2:6]}-{clean[6:]}"
    return clean

def generate_svg_barcode_placeholder(barcode_val: str) -> str:
    """
    Generate a lightweight SVG barcode representation as an immediate server-side fallback.
    JsBarcode on the frontend will render the exact Code 128 canvas/SVG.
    """
    safe_val = html.escape(barcode_val)
    # Simple aesthetic SVG representation for direct display/print
    return f"""<svg class="barcode-svg-fallback" viewBox="0 0 240 80" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="#ffffff" />
        <g fill="#0f172a">
            <rect x="20" y="10" width="3" height="45" />
            <rect x="26" y="10" width="6" height="45" />
            <rect x="36" y="10" width="2" height="45" />
            <rect x="42" y="10" width="8" height="45" />
            <rect x="54" y="10" width="4" height="45" />
            <rect x="62" y="10" width="2" height="45" />
            <rect x="68" y="10" width="6" height="45" />
            <rect x="78" y="10" width="3" height="45" />
            <rect x="85" y="10" width="7" height="45" />
            <rect x="96" y="10" width="4" height="45" />
            <rect x="104" y="10" width="2" height="45" />
            <rect x="110" y="10" width="5" height="45" />
            <rect x="119" y="10" width="3" height="45" />
            <rect x="126" y="10" width="6" height="45" />
            <rect x="136" y="10" width="4" height="45" />
            <rect x="144" y="10" width="2" height="45" />
            <rect x="150" y="10" width="7" height="45" />
            <rect x="161" y="10" width="3" height="45" />
            <rect x="168" y="10" width="5" height="45" />
            <rect x="177" y="10" width="4" height="45" />
            <rect x="185" y="10" width="2" height="45" />
            <rect x="191" y="10" width="6" height="45" />
            <rect x="201" y="10" width="3" height="45" />
            <rect x="208" y="10" width="6" height="45" />
            <rect x="218" y="10" width="3" height="45" />
        </g>
        <text x="120" y="70" text-anchor="middle" font-family="monospace" font-size="13" font-weight="bold" fill="#0f172a">{safe_val}</text>
    </svg>"""
