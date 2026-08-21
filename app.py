from flask import Flask, request, render_template_string, redirect, url_for, session

app = Flask(__name__)
# Bắt buộc phải có secret_key để sử dụng session
app.secret_key = 'super_secret_key'

# Giả lập Database
MOCK_DATABASE = {
    "admin": "123456",
    "user": "Abc123"
}

# 1. Giao diện Đăng Nhập (Có thêm CSS)
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Đăng nhập hệ thống</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .login-box { background: white; padding: 40px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); width: 100%; max-width: 320px; text-align: center; }
        .login-box h2 { margin-top: 0; color: #333; margin-bottom: 25px; }
        input[type="text"], input[type="password"] { width: 100%; padding: 12px 15px; margin: 8px 0 15px; border: 1px solid #ddd; border-radius: 5px; box-sizing: border-box; font-size: 14px; }
        input[type="submit"] { width: 100%; padding: 12px; background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; font-weight: bold; transition: 0.3s; }
        input[type="submit"]:hover { background-color: #0056b3; }
        .error-msg { color: #dc3545; font-size: 14px; margin-bottom: 15px; background: #f8d7da; padding: 10px; border-radius: 5px; border: 1px solid #f5c6cb; }
    </style>
</head>
<body>
    <div class="login-box">
        <h2>Đăng Nhập</h2>
        {% if error %}
            <div class="error-msg">{{ error }}</div>
        {% endif %}
        <form method="POST" action="/login">
            <input type="text" name="username" placeholder="Tên đăng nhập" required>
            <input type="password" name="password" placeholder="Mật khẩu" required>
            <input type="submit" value="Đăng nhập">
        </form>
    </div>
</body>
</html>
"""

# 2. Giao diện Trang Chủ đơn giản
HOME_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Trang Chủ</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #e9ecef; text-align: center; padding-top: 100px; }
        .dashboard-box { background: white; padding: 40px 60px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); display: inline-block; }
        h1 { color: #28a745; margin-top: 0; }
        p { color: #6c757d; font-size: 18px; margin-bottom: 30px; }
        .logout-btn { padding: 10px 25px; background-color: #dc3545; color: white; text-decoration: none; border-radius: 5px; font-weight: bold; transition: 0.3s; }
        .logout-btn:hover { background-color: #c82333; }
    </style>
</head>
<body>
    <div class="dashboard-box">
        <h1>Chào mừng, {{ username }}! 🎉</h1>
        <p>Bạn đã đăng nhập thành công vào hệ thống.</p>
        <a href="/logout" class="logout-btn">Đăng xuất</a>
    </div>
</body>
</html>
"""


@app.route('/')
def home():
    # Nếu đã đăng nhập, cho vào thẳng dashboard, ngược lại về login
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Chặn người dùng nếu họ đã đăng nhập mà vẫn cố vào link /login
    if 'username' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            return render_template_string(LOGIN_HTML, error="Vui lòng nhập đủ thông tin!"), 400

        if username in MOCK_DATABASE and MOCK_DATABASE[username] == password:
            # Lưu session và chuyển hướng tới trang chủ
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            return render_template_string(LOGIN_HTML, error="Sai tài khoản hoặc mật khẩu!"), 401

    return render_template_string(LOGIN_HTML)


@app.route('/dashboard')
def dashboard():
    # Kiểm tra xem người dùng đã đăng nhập chưa
    if 'username' not in session:
        return redirect(url_for('login'))

    # Hiển thị trang chủ cùng tên username
    return render_template_string(HOME_HTML, username=session['username'])


@app.route('/logout')
def logout():
    # Xóa session khi đăng xuất
    session.pop('username', None)
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)