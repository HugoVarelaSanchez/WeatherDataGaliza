// Validación client-side del formulario de registro
const registerForm = document.getElementById('register-form');
if (registerForm) {
    registerForm.addEventListener('submit', function (e) {
        const pass = document.getElementById('contrasenha').value;
        const confirm = document.getElementById('contrasenha_confirm').value;
        if (pass !== confirm) {
            e.preventDefault();
            showError('Las contraseñas no coinciden');
        }
    });
}

function showError(msg) {
    let existing = document.querySelector('.error');
    if (existing) {
        existing.textContent = msg;
        return;
    }
    const div = document.createElement('div');
    div.className = 'error';
    div.textContent = msg;
    const form = document.querySelector('form');
    form.insertAdjacentElement('beforebegin', div);
}
