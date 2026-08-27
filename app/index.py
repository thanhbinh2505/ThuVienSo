from flask import (abort, jsonify, redirect, render_template, request,
                    url_for)
from flask_login import current_user, login_user, logout_user
from marshmallow import ValidationError

import app.schemas as schemas
from app import app, dao, login, oauth
from app.decorator import anonymous_required, role_required
from app.models import OAuthProvider, UserRole


def register_routes(app):


    @app.route('/')
    def index():
        ds_theloai = dao.get_list_theloai()
        ket_qua = dao.tim_kiem_sach(page=1, page_size=12)
        return render_template('index.html', ds_theloai=ds_theloai, ket_qua=ket_qua)

    @app.route('/api/sach', methods=['GET'])
    def api_tim_kiem_sach():
        try:
            data = schemas.TimKiemSachSchema().load(request.args)
        except ValidationError as err:
            return jsonify({"success": False, "message": "Tham số không hợp lệ!",
                             "errors": err.messages}), 400

        ket_qua = dao.tim_kiem_sach(
            tu_khoa=data.get('q', ''),
            theloai_id=data.get('theloai_id'),
            page=data.get('page', 1),
            sort=data.get('sort', 'moi_nhat'),
        )
        return jsonify({"success": True, **ket_qua}), 200

    @app.route('/api/theloai', methods=['GET'])
    def api_the_loai():
        ds = dao.get_list_theloai()
        return jsonify([t.to_dict() for t in ds]), 200

    @app.route('/sach/<int:sach_id>')
    def chi_tiet_sach(sach_id):
        sach = dao.get_sach_by_id(sach_id)
        if not sach:
            abort(404)

        sach_lien_quan = dao.get_sach_lien_quan(sach)

        return render_template('chi_tiet_sach.html', sach=sach, sach_lien_quan=sach_lien_quan)

    @app.route('/api/sach/<int:sach_id>')
    def api_chi_tiet_sach(sach_id):
        sach = dao.get_sach_by_id(sach_id)
        if not sach:
            return jsonify({"success": False, "message": "Không tìm thấy sách!"}), 404
        return jsonify({"success": True, "data": sach.to_dict_chi_tiet()}), 200

    @app.route('/register', methods=['GET', 'POST'])
    @anonymous_required
    def register():
        err_msg = ""
        if request.method == 'POST':
            data = request.form.to_dict()
            if data.get('ngaysinh') == '':
                data['ngaysinh'] = None

            try:
                data = schemas.RegisterSchema().load(data)
            except ValidationError as err:
                first_field = list(err.messages.keys())[0]
                err_msg = err.messages[first_field][0]
                return render_template('register.html', err_msg=err_msg)

            gioitinh = data.get('gioitinh') == 'male'

            try:
                success, message, user = dao.dang_ky_doc_gia(
                    username=data['username'],
                    hoten=data['hoten'],
                    password=data['password'],
                    email=data.get('email'),
                    sdt=data.get('sdt'),
                    gioitinh=gioitinh,
                    ngaysinh=data.get('ngaysinh'),
                )
                if success:
                    return redirect(url_for('login_process'))
                err_msg = message
            except Exception:
                err_msg = "Có lỗi xảy ra. Vui lòng thử lại sau!"

        return render_template('register.html', err_msg=err_msg)

    @app.route('/login', methods=['GET', 'POST'])
    @anonymous_required
    def login_process():
        error_msg = ""
        dinh_danh_val = ""

        if request.method == 'POST':
            dinh_danh = request.form.get('dinh_danh', '').strip()
            password = request.form.get('password', '').strip()
            dinh_danh_val = dinh_danh

            if not dinh_danh or not password:
                error_msg = "Vui lòng nhập đầy đủ thông tin đăng nhập!"
            else:
                user, message = dao.dang_nhap(dinh_danh, password)
                if not user:
                    error_msg = message
                else:
                    login_user(user=user)
                    next_page = request.args.get('next')
                    if next_page:
                        return redirect(next_page)
                    if user.role == UserRole.ADMIN:
                        return redirect('/admin')
                    elif user.role == UserRole.THUTHU:
                        return redirect('/thuthu')
                    return redirect('/')

        return render_template('login.html', error=error_msg, dinh_danh_val=dinh_danh_val)

    @app.route('/logout', methods=['GET', 'POST'])
    def logout_process():
        logout_user()
        return redirect('/')


    @app.route('/login/google')
    @anonymous_required
    def login_google():
        redirect_uri = 'http://localhost:5000/login/google/callback'
        return oauth.google.authorize_redirect(redirect_uri)

    @app.route('/login/google/callback')
    @anonymous_required
    def login_google_callback():
        try:
            token = oauth.google.authorize_access_token()
            userinfo = token.get('userinfo') or oauth.google.parse_id_token(token)
        except Exception:
            return redirect(url_for('login_process', oauth_error='google'))

        user, _ = dao.dang_nhap_hoac_tao_tai_khoan_oauth(
            provider=OAuthProvider.GOOGLE,
            oauth_id=userinfo.get('sub'),
            email=userinfo.get('email'),
            hoten=userinfo.get('name'),
            avatar=userinfo.get('picture'),
        )
        login_user(user=user)
        return redirect('/')

@login.user_loader
def load_user(id):
    return dao.get_user_by_id(id)


if __name__ == '__main__':
    register_routes(app)
    with app.app_context():
        app.run(debug=True, port=5000)
