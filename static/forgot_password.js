async function requestCode() {
    const email = document.getElementById('email').value;
    const messageElement = document.getElementById('request-message');
    const button1 = document.getElementById('sendCodeBtn');
    if (!email) {
        messageElement.textContent = '이메일 주소를 입력해주세요.';
        messageElement.style.color = 'red';
        return;
    }

    button1.disabled = true;
    setTimeout(() => {
        button1.disabled = false;
    }, 5000);
    try {
        const response = await fetch('/api/forgot-password/send-code', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email: email })
        });

        const data = await response.json();

        if (response.ok) {
            messageElement.textContent = "인증이메일을 보냈습니다"; // User requested specific message
            messageElement.style.color = 'green';
            document.getElementById('request-code-section').style.display = 'none';
            document.getElementById('reset-password-section').style.display = 'block';
        } else {
            messageElement.textContent = data.error;
            messageElement.style.color = 'red';
        }
    } catch (error) {
        console.error('Error requesting code:', error);
        messageElement.textContent = '오류가 발생했습니다. 다시 시도해주세요.';
        messageElement.style.color = 'red';
    }
}

async function resetPassword() {
    const email = document.getElementById('email').value; // Email is still needed for the reset step
    const code = document.getElementById('code').value;
    const newPassword = document.getElementById('new-password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    const messageElement = document.getElementById('reset-message');

    if (!code || !newPassword || !confirmPassword) {
        messageElement.textContent = '인증 코드와 새 비밀번호를 모두 입력해주세요.';
        messageElement.style.color = 'red';
        return;
    }

    if (newPassword !== confirmPassword) {
        messageElement.textContent = '새 비밀번호가 일치하지 않습니다.';
        messageElement.style.color = 'red';
        return;
    }

    try {
        // First, verify the code
        const verifyResponse = await fetch('/api/forgot-password/verify-code', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email: email, code: code })
        });

        const verifyData = await verifyResponse.json();

        if (!verifyResponse.ok) {
            messageElement.textContent = verifyData.error;
            messageElement.style.color = 'red';
            return;
        }

        // If code is verified, proceed to reset password
        const resetResponse = await fetch('/api/forgot-password/reset-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email: email, new_password: newPassword })
        });

        const resetData = await resetResponse.json();

        if (resetResponse.ok) {
            messageElement.textContent = resetData.message;
            messageElement.style.color = 'green';
            // Redirect to login page after successful reset
            window.location.href = '/login';
        } else {
            messageElement.textContent = resetData.error;
            messageElement.style.color = 'red';
        }

    } catch (error) {
        console.error('Error resetting password:', error);
        messageElement.textContent = '오류가 발생했습니다. 다시 시도해주세요.';
        messageElement.style.color = 'red';
    }
}
