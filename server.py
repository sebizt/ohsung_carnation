from flask import Flask, request, redirect, url_for, render_template, jsonify, session
from flask_bcrypt import Bcrypt
from flask_mysqldb import MySQL
import random
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta

app = Flask(__name__, static_url_path='/static', static_folder='static')
app.secret_key = 'c108e4f3c62244f9a25c132dd592f3f0'

app.config['MYSQL_HOST'] = '146.56.97.153'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'db2025' # 개인 설정한 비밀번호로 변경할 것
app.config['MYSQL_DB'] = 'school'
app.config['MYSQL_CHARSET'] = 'utf8mb4'
app.config['MYSQL_USE_UNICODE'] = True
mysql = MySQL(app)
bcrypt = Bcrypt(app)

def send_email(to_email, code):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_user = 'sebizt711@gmail.com'
    smtp_password = 'czms avlz dhrs hywd'
    msg = MIMEText(f'인증번호: {code}')
    msg['Subject'] = '오성고 스승의날 편지 인증번호'
    msg['From'] = smtp_user
    msg['To'] = to_email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to_email, msg.as_string())

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    email = data.get('email')
    # 비밀번호는 이 단계에서 받지 않음
    if not email:
        return jsonify({'error': '이메일은 필수입니다.'}), 400
    if not email.endswith('@g.cnees.kr'):
        return jsonify({'error': '학교 메일만 가능합니다.'}), 400
    cur = mysql.connection.cursor()
    cur.execute('SELECT 1 FROM users WHERE email=%s', (email,))
    if cur.fetchone():
        return jsonify({'error': '이미 사용 중인 이메일입니다.'}), 400                  # 나는 그루트비트 이건 정말 아니야
    code = f"{random.randint(0, 999999):06}"
    cur.execute('INSERT INTO emails (email, code) VALUES (%s,%s)', (email, code))
    mysql.connection.commit()
    send_email(email, code)
    return jsonify({'message': '인증 코드가 발송되었습니다.'}), 201

@app.route('/api/verify_email', methods=['POST'])
def verify_email():
    data = request.json
    email = data.get('email')
    code = data.get('code')
    pw = data.get('password')
    role = data.get('role', 'student')
    if not email or not code or not pw:
        return jsonify({'error': '이메일, 인증번호, 비밀번호는 필수입니다.'}), 400
    cur = mysql.connection.cursor()
    cur.execute(
        'SELECT code, created_at FROM emails '
        'WHERE email=%s ORDER BY created_at DESC LIMIT 1',
        (email,)
    )
    row = cur.fetchone()
    if not row:
        return jsonify({'error': '인증번호를 찾을 수 없습니다.'}), 400
    saved_code, created_at = row
    if saved_code != code:
        return jsonify({'error': '인증번호가 올바르지 않습니다.'}), 400
    if datetime.utcnow() - created_at > timedelta(minutes=10):
        return jsonify({'error': '인증번호가 만료되었습니다.'}), 400
    cur.execute('SELECT 1 FROM users WHERE email=%s', (email,))
    if cur.fetchone():
        return jsonify({'error': '이미 가입된 이메일입니다.'}), 400
    hashed_pw = bcrypt.generate_password_hash(pw).decode('utf-8')
    cur.execute(
        'INSERT INTO users (email, pw, role) VALUES (%s,%s,%s)',
        (email, hashed_pw, role)
    )
    mysql.connection.commit()
    return jsonify({'message': '회원가입이 완료되었습니다.'}), 200

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    pw = data.get('password')
    if not email or not pw:
        return jsonify({'error': '이메일과 비밀번호는 필수입니다.'}), 400
    cur = mysql.connection.cursor()
    cur.execute('SELECT user_id, pw, role FROM users WHERE email=%s', (email,))
    row = cur.fetchone()
    if not row or not bcrypt.check_password_hash(row[1], pw):
        return jsonify({'error': '아이디 또는 비밀번호가 올바르지 않습니다.'}), 401
    session['user_id'], session['role'] = row[0], row[2]
    return jsonify({'message': '로그인 성공'}), 200

@app.route('/forgot-password')
def forgot_password_page():
    return render_template('forgot_password.html')

@app.route('/api/forgot-password/send-code', methods=['POST'])
def send_password_reset_code():
    data = request.json
    email = data.get('email')
    if not email:
        return jsonify({'error': '이메일 주소를 입력해주세요.'}), 400

    cur = mysql.connection.cursor()
    # Check if the email exists in the users table
    cur.execute('SELECT 1 FROM users WHERE email=%s', (email,))
    if not cur.fetchone():
        return jsonify({'error': '등록되지 않은 이메일 주소입니다.'}), 404

    # Generate and store the code
    code = f"{random.randint(0, 999999):06}"
    # Clear any old codes for this email before inserting the new one
    cur.execute('DELETE FROM emails WHERE email=%s', (email,))
    cur.execute('INSERT INTO emails (email, code) VALUES (%s,%s)', (email, code))
    mysql.connection.commit()

    # Send the email
    try:
        send_email(email, code)
        return jsonify({'message': '인증 코드가 이메일로 발송되었습니다.'}), 200
    except Exception as e:
        print(f"Error sending email: {e}")
        return jsonify({'error': '인증 코드 발송에 실패했습니다.'}), 500

@app.route('/api/forgot-password/verify-code', methods=['POST'])
def verify_password_reset_code():
    data = request.json
    email = data.get('email')
    code = data.get('code')
    if not email or not code:
        return jsonify({'error': '이메일 주소와 인증 코드를 입력해주세요.'}), 400

    cur = mysql.connection.cursor()
    cur.execute(
        'SELECT code, created_at FROM emails '
        'WHERE email=%s ORDER BY created_at DESC LIMIT 1',
        (email,)
    )
    row = cur.fetchone()

    if not row:
        return jsonify({'error': '인증 코드를 찾을 수 없습니다. 코드를 다시 요청해주세요.'}), 400

    saved_code, created_at = row

    if saved_code != code:
        return jsonify({'error': '인증 코드가 올바르지 않습니다.'}), 400

    # Check if the code is expired (e.g., 10 minutes)
    if datetime.utcnow() - created_at > timedelta(minutes=10):
        return jsonify({'error': '인증 코드가 만료되었습니다. 코드를 다시 요청해주세요.'}), 400

    # Code is valid, return success
    return jsonify({'message': '인증 코드가 확인되었습니다.'}), 200 # Could return a temporary token here if needed for the next step

@app.route('/api/forgot-password/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    email = data.get('email')
    new_password = data.get('new_password')
    if not email or not new_password:
        return jsonify({'error': '이메일 주소와 새 비밀번호를 입력해주세요.'}), 400

    cur = mysql.connection.cursor()
    # Verify the email exists
    cur.execute('SELECT user_id FROM users WHERE email=%s', (email,))
    user_row = cur.fetchone()
    if not user_row:
        return jsonify({'error': '사용자를 찾을 수 없습니다.'}), 404

    user_id = user_row[0]

    # Hash the new password
    hashed_pw = bcrypt.generate_password_hash(new_password).decode('utf-8')

    # Update the password
    cur.execute('UPDATE users SET pw=%s WHERE user_id=%s', (hashed_pw, user_id))
    # Optionally, clear the used code from the emails table
    cur.execute('DELETE FROM emails WHERE email=%s', (email,))
    mysql.connection.commit()

    return jsonify({'message': '비밀번호가 성공적으로 초기화되었습니다.'}), 200


@app.route('/api/teachers', methods=['GET'])
def get_teachers():
    cur = mysql.connection.cursor()
    # theme, image 컬럼 제거됨
    cur.execute('SELECT teacher_id, name, bio FROM teachers')
    teachers = [
        {'teacher_id': t[0], 'name': t[1], 'bio': t[2]}
        for t in cur.fetchall()
    ]
    return jsonify(teachers), 200

@app.route('/api/letters/<int:teacher_id>', methods=['GET'])
def get_letters(teacher_id):
    # 로그인 체크
    if 'user_id' not in session:
        return jsonify({'error': '로그인이 필요합니다.'}), 401

    user_id = session['user_id']
    cur = mysql.connection.cursor()
    # receiver_id 컬럼이 user_id 또는 teacher_id 와 일치하면 모두 조회
    cur.execute(
        '''
        SELECT letter_id, sender_id, receiver_id, title, content, created_at
        FROM letters
        WHERE receiver_id IN (%s, %s)
        ORDER BY created_at DESC
        ''',
        (user_id, teacher_id)
    )

    letters = [
        {
            'letter_id': l[0],
            'sender_id': l[1],
            'receiver_id': l[2],
            'title': l[3],
            'content': (
                l[4].replace('\n', '<br>') if l[4] else ''
            ) if session.get('user_id') == teacher_id or session.get('user_id') == l[1]  else (
                '@' * len(l[4]) if l[4] else ''
            ),
            'created_at': l[5].strftime('%Y-%m-%d %H:%M:%S')
        }
        for l in cur.fetchall()
    ]
    return jsonify(letters), 200

@app.route('/api/letters', methods=['POST'])
def write_letter():
    if 'user_id' not in session:
        return jsonify({'error': '로그인이 필요합니다.'}), 401
    data = request.json
    sender_id = session['user_id']
    receiver_id = data.get('receiver_id')
    title = data.get('title')
    content = data.get('content')
    if not receiver_id or not title or not content:
        return jsonify({'error': '잘못된 요청입니다.'}), 400
    cur = mysql.connection.cursor()
    cur.execute(
        'INSERT INTO letters (sender_id, receiver_id, title, content) '
        'VALUES (%s,%s,%s,%s)',
        (sender_id, receiver_id, title, content)
    )
    mysql.connection.commit()
    return jsonify({'message': '편지를 작성했습니다.'}), 201

@app.route('/')
def index_page():
    role = session.get('role')
    # teacher 계정인 경우 teacher_id 함께 전달
    if role == 'teacher':
        return render_template('main.html', role=role, teacher_id=session.get('user_id'))
    # 그 외(학생)에는 student 로만 전달
    if role == 'student':
        return render_template('main.html', role='student')
    return render_template('main.html', role='guest')

@app.route('/login')
def login_page():
    if 'user_id' not in session:
        return render_template('login.html')
    return redirect(url_for('index_page'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/signup')
def signup_page():
    if 'user_id' not in session:
        return render_template('signup.html')
    return redirect(url_for('teachers_page'))

@app.route('/teachers')
def teachers_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('teachers.html')

@app.route('/letters/<int:teacher_id>')
def letters_page(teacher_id):
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('letters.html', teacher_id=teacher_id, role=session.get('role'), user_id=session.get('user_id'))

@app.route('/write/<int:teacher_id>')
def write_page(teacher_id):
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('write.html', teacher_id=teacher_id)

# teacher 계정 전용 리다이렉트
@app.before_request
def redirect_teacher():
    # 마스터 계정은 모든 페이지 접근 허용
    if session.get('role') == 'master':
        return

    if 'user_id' in session and session.get('role') == 'teacher':
        teacher_id = session['user_id']
        path = request.path

        # 1) /teachers 로의 접근 차단 → 편지함으로 리다이렉트
        if path.startswith('/teachers'):
            return redirect(url_for('letters_page', teacher_id=teacher_id))

        # 2) 그 외 불필요한 페이지 접근도 차단
        #    단, 자신의 letters 페이지, static/ api/ logout 은 허용
        if not path.startswith(f'/letters/{teacher_id}') \
           and not path.startswith('/static/') \
           and not path.startswith('/api/') \
           and not path.startswith('/') \
           and request.endpoint != 'logout':
            return redirect(url_for('letters_page', teacher_id=teacher_id))

@app.route('/admin/all_letters')
def admin_all_letters_page():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    if session.get('role') != 'master':
        # Optionally, redirect to an 'unauthorized' page or the index page
        return redirect(url_for('index_page')) 

    cur = mysql.connection.cursor()
    try:
        cur.execute('''
            SELECT
                l.letter_id,
                u.email AS sender_email,
                t.name AS receiver_name,
                l.title,
                l.content,
                l.created_at
            FROM letters l
            JOIN users u ON l.sender_id = u.user_id
            JOIN teachers t ON l.receiver_id = t.teacher_id
            ORDER BY l.created_at DESC
        ''')
        letters_data = cur.fetchall()
    finally:
        cur.close()

    processed_letters = []
    for row in letters_data:
        processed_letters.append({
            'letter_id': row[0],
            'sender_email': row[1],
            'receiver_name': row[2],
            'title': row[3],
            'content': row[4],
            'created_at': row[5].strftime('%Y-%m-%d %H:%M:%S') if row[5] else None
        })

    return render_template('admin_all_letters.html', letters=processed_letters)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
