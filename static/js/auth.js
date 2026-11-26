// Authentication helper scripts - PatientCase AI

function fillDemoAccount(email, password) {
    const emailField = document.querySelector('input[name="email"]');
    const passField = document.querySelector('input[name="password"]');
    if (emailField && passField) {
        emailField.value = email;
        passField.value = password;
        emailField.focus();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Client-side password match checker for registration
    const registerForm = document.getElementById('patientRegisterForm');
    if (registerForm) {
        registerForm.addEventListener('submit', (e) => {
            const pass = document.getElementById('reg_password')?.value;
            const confirmPass = document.getElementById('reg_confirm_password')?.value;
            if (pass !== confirmPass) {
                e.preventDefault();
                alert('Passwords do not match. Please re-enter.');
            }
        });
    }
});
