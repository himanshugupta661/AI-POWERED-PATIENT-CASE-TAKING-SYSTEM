// Patient dashboard client interactions - PatientCase AI

document.addEventListener('DOMContentLoaded', () => {
    // Quick search in patient cases table
    const searchInput = document.getElementById('patientCaseSearch');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            const rows = document.querySelectorAll('.patient-case-row');
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
});
