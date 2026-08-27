//  function switchTab(tab) {
//             document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
//             document.querySelectorAll('.form-section').forEach(s => s.classList.remove('active'));

//             event.target.classList.add('active');
//             document.getElementById(tab).classList.add('active');

//             const title = document.querySelector('.logo h1');
//             const subtitle = document.querySelector('.logo p');

//             if (tab === 'login') {
//                 title.textContent = 'Welcome Back';
//                 subtitle.textContent = 'Sign in to access your account';
//             } else {
//                 title.textContent = 'Get Started';
//                 subtitle.textContent = 'Create your free account today';
//             }
//         }

//         function handleLogin(e) {
//             e.preventDefault();
//             alert('Login submitted! (This is a demo)');
//         }

//         function handleSignup(e) {
//             e.preventDefault();
//             const inputs = e.target.querySelectorAll('input[type="password"]');
//             if (inputs[0].value !== inputs[1].value) {
//                 alert('Passwords do not match!');
//                 return;
//             }
//             alert('Account created successfully! (Thanks for working with us)');
//         }

function switchTab(tab, button) {

    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.form-section').forEach(s => s.classList.remove('active'));

    button.classList.add('active');
    document.getElementById(tab).classList.add('active');

    document.querySelector('.tabs').style.display = 'flex';
    document.querySelector('.divider').style.display = 'flex';
    document.querySelector('.social-login').style.display = 'flex';

    const title = document.querySelector('.logo h1');
    const subtitle = document.querySelector('.logo p');

    if (tab === 'login') {
        title.textContent = 'Welcome Back';
        subtitle.textContent = 'Sign in to access your account';
    } else {
        title.textContent = 'Get Started';
        subtitle.textContent = 'Create your free account today';
    }
}

function showForgotPassword() {

    document.querySelectorAll('.form-section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));

    document.getElementById('forgot-password').classList.add('active');

    document.querySelector('.tabs').style.display = 'none';
    document.querySelector('.divider').style.display = 'none';
    document.querySelector('.social-login').style.display = 'none';

    document.querySelector('.logo h1').textContent = 'Forgot Password';
    document.querySelector('.logo p').textContent = 'Enter your email to receive a verification code.';
}

function showVerifyOTP(email) {

    document.querySelectorAll('.form-section').forEach(s => s.classList.remove('active'));

    document.getElementById('verify-otp').classList.add('active');

    document.querySelector('.logo h1').textContent = 'Verify Code';
    document.querySelector('.logo p').textContent = 'Enter the verification code sent to your email.';

    document.getElementById('otp-email').value = email;
}

function showResetPassword() {

    document.querySelectorAll('.form-section').forEach(s => s.classList.remove('active'));

    document.getElementById('reset-password').classList.add('active');

    document.querySelector('.tabs').style.display = 'none';
    document.querySelector('.divider').style.display = 'none';
    document.querySelector('.social-login').style.display = 'none';

    document.querySelector('.logo h1').textContent = 'Reset Password';
    document.querySelector('.logo p').textContent = 'Create your new password.';
}

function showSignup() {

    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.form-section').forEach(s => s.classList.remove('active'));

    document.querySelectorAll('.tab')[1].classList.add('active');
    document.getElementById('signup').classList.add('active');

    document.querySelector('.tabs').style.display = 'flex';
    document.querySelector('.divider').style.display = 'flex';
    document.querySelector('.social-login').style.display = 'flex';

    document.querySelector('.logo h1').textContent = 'Get Started';
    document.querySelector('.logo p').textContent = 'Create your free account today';
}

function resendOTP() {

    const email = document.getElementById("otp-email").value;

    if (!email) {
        alert("Email not found.");
        return;
    }

    const form = document.createElement("form");
    form.method = "POST";
    form.action = "/forgot_password";

    const input = document.createElement("input");
    input.type = "hidden";
    input.name = "email";
    input.value = email;

    form.appendChild(input);

    document.body.appendChild(form);

    form.submit();
}



function backToLogin() {

    document.querySelectorAll('.form-section').forEach(s => s.classList.remove('active'));

    document.getElementById('login').classList.add('active');

    document.querySelector('.tabs').style.display = 'flex';
    document.querySelector('.divider').style.display = 'flex';
    document.querySelector('.social-login').style.display = 'flex';

    document.querySelector('.logo h1').textContent = 'Welcome Back';
    document.querySelector('.logo p').textContent = 'Sign in to access your account';

    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelector('.tab').classList.add('active');
}

// function handleLogin(e) {
//     e.preventDefault();
//     alert('Login submitted! (This is a demo)');
// }

// function handleSignup(e) {
//     e.preventDefault();

//     const inputs = e.target.querySelectorAll('input[type="password"]');

//     if (inputs[0].value !== inputs[1].value) {
//         alert('Passwords do not match!');
//         return;
//     }

//     alert('Account created successfully! (Thanks for working with us)');
//}

window.onload = function () {

    const showOtp = document.getElementById("show-otp");
    const showReset = document.getElementById("show-reset");
    const showSignup_ = document.getElementById("show-signup");

    if (showOtp && showOtp.value === "true") {

        showVerifyOTP();

        document.getElementById("otp-email").value =
            document.getElementById("show-otp-email").value;
    }

    if (showReset && showReset.value === "true") {

        showResetPassword();

    }

    if (showSignup_ && showSignup_.value === "true") {

        showSignup();

    }

};