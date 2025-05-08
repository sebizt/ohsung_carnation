// 비밀번호 보기/숨기기
const pwdInput  = document.getElementById('password');
const toggleBtn = document.getElementById('togglePwd');

toggleBtn.addEventListener('click', () => {
  const hidden = pwdInput.type === 'password';
  pwdInput.type = hidden ? 'text' : 'password';
  toggleBtn.classList.toggle('fa-eye', hidden);
  toggleBtn.classList.toggle('fa-eye-slash', !hidden);
});

// 로그인 폼 제출 처리 변경
document.getElementById('loginForm').addEventListener('submit', async e => {
  e.preventDefault();
  const email = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value;

  try {
    const res = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const result = await res.json();
    if (res.ok) {
      window.location.href = '/';
    } else {
      alert(result.error);
    }
  } catch {
    alert('네트워크 에러');
  }
});