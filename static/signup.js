/* 비밀번호 보기/숨기기 */
const pwdInput  = document.getElementById('password');
const toggleBtn = document.getElementById('togglePwd');
toggleBtn.addEventListener('click', () => {
  const isHidden = pwdInput.type === 'password';
  pwdInput.type  = isHidden ? 'text' : 'password';
  toggleBtn.classList.toggle('fa-eye',     isHidden);
  toggleBtn.classList.toggle('fa-eye-slash',!isHidden);
});

/* 1) 인증번호 요청 */
async function sendCode() {
  const email = document.getElementById('email').value.trim();
  if (!email) return alert('이메일을 입력하세요');
  try {
    const res = await fetch('/api/signup', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ email })
    });
    const result = await res.json();
    if (res.ok) {
      alert(result.message);
      // ① 이메일 표시(input.value 로 변경)
      document.getElementById('regEmail').value = email;
      // ② 폼 전환
      document.getElementById('sendCodeForm').style.display = 'none';
      document.getElementById('verifyForm').style.display   = 'block';
    } else {
      alert(result.error);
    }
  } catch {
    alert('네트워크 에러');
  }
}

// 버튼 클릭
document.getElementById('sendCodeBtn').addEventListener('click', sendCode);

// 엔터(폼 submit) 처리
document.getElementById('sendCodeForm').addEventListener('submit', e => {
  e.preventDefault();
  sendCode();
});

// 인증번호 재전송 버튼
document.getElementById('resendCodeBtn').addEventListener('click', () => {
  // regEmail에 저장된 값을 email input에도 복사해 두면 sendCode()가 그대로 동작합니다.
  document.getElementById('email').value = document.getElementById('regEmail').value;
  sendCode();
});

/* 2) 인증 + 실제 가입 */
document.getElementById('verifyForm').addEventListener('submit', async evt => {
  evt.preventDefault();
  const email    = document.getElementById('email').value.trim();
  const code     = document.getElementById('code').value.trim();
  const password = document.getElementById('password').value.trim();
  
  if (!code)     return alert('인증번호를 입력하세요');
  if (!password) return alert('비밀번호를 입력하세요');
  
  try {
    const res = await fetch('/api/verify_email', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ email, code, password, role: 'student' })
    });
    const result = await res.json();
    if (res.ok) {
      alert(result.message);
      window.location.href = '/login';
    } else {
      alert(result.error);
    }
  } catch {
    alert('네트워크 에러');
  }
});