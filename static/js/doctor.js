// Doctor portal client interactions - PatientCase AI

document.addEventListener('DOMContentLoaded', () => {
    // Quick search in doctor case history table
    const searchInput = document.getElementById('doctorCaseSearch');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            const rows = document.querySelectorAll('.doctor-case-row');
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(query)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }

    // Print button handler
    const btnPrintSheet = document.getElementById('btnPrintClinicalSheet');
    if (btnPrintSheet) {
        btnPrintSheet.addEventListener('click', () => {
            window.print();
        });
    }
});
