from flask import Flask, request, redirect, url_for, render_template, jsonify, session
from flask_bcrypt import Bcrypt
from flask_mysqldb import MySQL
import random
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta

app = Flask(__name__, static_url_path='/static', static_folder='static')
app.secret_key = 'c108e4f3c62244f9a25c132dd592f3f0'

app.config['MYSQL_HOST'] = 'localhost'
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
    msg['Subject'] = '오성고 스승의 날 행사 회원가입'
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
        return jsonify({'error': '이미 사용 중인 이메일입니다.'}), 400
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
            'content': l[4],
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
    return render_template('main.html', role='student')

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
    return render_template('letters.html', teacher_id=teacher_id)

@app.route('/write/<int:teacher_id>')
def write_page(teacher_id):
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('write.html', teacher_id=teacher_id)

# teacher 계정 전용 리다이렉트
@app.before_request
def redirect_teacher():
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
