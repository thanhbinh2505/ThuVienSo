from flask import (abort, jsonify, redirect, render_template, request,
                    url_for)
from flask_login import current_user, login_user, logout_user
from marshmallow import ValidationError

import app.schemas as schemas
from app import app, dao, login, oauth
from app.decorator import anonymous_required, role_required
from app.models import OAuthProvider, UserRole, Sach
from datetime import datetime


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
        danh_sach_binh_luan = dao.get_binh_luan_sach(sach_id)
        if not sach:
            abort(404)

        sach_lien_quan = dao.get_sach_lien_quan(sach)

        return render_template(
            'chi_tiet_sach.html',
            sach=sach,
            sach_lien_quan=sach_lien_quan,
            danh_sach_binh_luan=danh_sach_binh_luan
        )
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

    @app.route('/login/facebook')
    @anonymous_required
    def login_facebook():
        redirect_uri = 'http://localhost:5000/login/facebook/callback'
        return oauth.facebook.authorize_redirect(redirect_uri)

    @app.route('/login/facebook/callback')
    @anonymous_required
    def login_facebook_callback():
        try:
            token = oauth.facebook.authorize_access_token()
            resp = oauth.facebook.get(
                'me?fields=id,name,email,picture'
            )
            userinfo = resp.json()
        except Exception:
            return redirect(url_for('login_process'))

        picture = userinfo.get('picture', {})
        picture_data = picture.get('data', {})

        user, _ = dao.dang_nhap_hoac_tao_tai_khoan_oauth(
            provider=OAuthProvider.FACEBOOK,
            oauth_id=userinfo.get('id'),
            email=userinfo.get('email'),
            hoten=userinfo.get('name'),
            avatar=picture_data.get('url'),
        )

        login_user(user=user)

        return redirect('/')

    @app.route('/api/sach/<int:sach_id>/danh-gia', methods=['POST'])
    def api_danh_gia_sach(sach_id):
        if not current_user.is_authenticated:
            return jsonify({
                "success": False,
                "message": "Vui lòng đăng nhập để đánh giá!"
            }), 401

        try:
            data = request.get_json()
            so_sao = int(data.get('so_sao', 0))
        except (ValueError, TypeError, AttributeError):
            return jsonify({
                "success": False,
                "message": "Dữ liệu đánh giá không hợp lệ!"
            }), 400

        success, message = dao.danh_gia_sach(
            current_user.id,
            sach_id,
            so_sao
        )

        if not success:
            return jsonify({
                "success": False,
                "message": message
            }), 400

        sach = dao.get_sach_by_id(sach_id)

        return jsonify({
            "success": True,
            "message": message,
            "diemDanhGiaTB": round(sach.diemDanhGiaTB or 0, 1),
            "soLuotDanhGia": sach.soLuotDanhGia or 0
        }), 200

    @app.route('/api/sach/<int:sach_id>/binh-luan', methods=['POST'])
    def api_them_binh_luan(sach_id):
        if not current_user.is_authenticated:
            return jsonify({
                "success": False,
                "message": "Vui lòng đăng nhập để bình luận!"
            }), 401

        try:
            data = request.get_json()
            noi_dung = data.get('noi_dung', '').strip()
        except Exception:
            return jsonify({
                "success": False,
                "message": "Dữ liệu không hợp lệ!"
            }), 400

        success, message, binh_luan = dao.them_binh_luan(
            current_user.id,
            sach_id,
            noi_dung
        )

        if not success:
            return jsonify({
                "success": False,
                "message": message
            }), 400

        return jsonify({
            "success": True,
            "message": message,
            "data": {
                "id": binh_luan.id,
                "noiDung": binh_luan.noiDung,
                "ngayTao": binh_luan.ngayTao.strftime('%d/%m/%Y %H:%M'),
                "hoTen": binh_luan.user.hoTen
            }
        }), 200

    @app.route('/api/binh-luan/<int:binh_luan_id>', methods=['DELETE'])
    def api_xoa_binh_luan(binh_luan_id):
        if not current_user.is_authenticated:
            return jsonify({
                "success": False,
                "message": "Vui lòng đăng nhập!"
            }), 401

        success, message = dao.xoa_binh_luan(
            current_user.id,
            binh_luan_id
        )

        return jsonify({
            "success": success,
            "message": message
        }), 200 if success else 403

    @app.route('/api/sach/<int:sach_id>/muon', methods=['POST'])
    def api_dang_ky_muon(sach_id):
        if not current_user.is_authenticated:
            return jsonify({
                "success": False,
                "message": "Vui lòng đăng nhập để mượn sách!"
            }), 401

        # Chỉ độc giả được đăng ký mượn
        if current_user.role != UserRole.DOCGIA:
            return jsonify({
                "success": False,
                "message": "Chỉ độc giả mới được đăng ký mượn sách!"
            }), 403

        success, message = dao.dang_ky_muon_sach(
            current_user.id,
            sach_id
        )

        if not success:
            return jsonify({
                "success": False,
                "message": message
            }), 400

        return jsonify({
            "success": True,
            "message": message
        }), 200

    @app.route('/api/phieu-muon/<int:phieu_muon_id>/gia-han', methods=['POST'])
    def api_gui_yeu_cau_gia_han(phieu_muon_id):
        if not current_user.is_authenticated:
            return jsonify({
                "success": False,
                "message": "Vui lòng đăng nhập!"
            }), 401

        if current_user.role != UserRole.DOCGIA:
            return jsonify({
                "success": False,
                "message": "Chỉ độc giả mới được yêu cầu gia hạn!"
            }), 403

        success, message = dao.gui_yeu_cau_gia_han(
            current_user.id,
            phieu_muon_id
        )

        return jsonify({
            "success": success,
            "message": message
        }), 200 if success else 400

    @app.route('/thuthu')
    def trang_thu_thu():
        if not current_user.is_authenticated:
            return redirect(url_for('login_process'))

        if current_user.role != UserRole.THUTHU:
            return abort(403)

        danh_sach_cho_duyet = dao.get_phieu_muon_cho_duyet()
        danh_sach_cho_gia_han = dao.get_phieu_muon_cho_gia_han()
        danh_sach_dang_muon = dao.get_phieu_muon_dang_muon()

        return render_template(
            'thuthu.html',
            danh_sach_cho_duyet=danh_sach_cho_duyet,
            danh_sach_cho_gia_han=danh_sach_cho_gia_han,
            danh_sach_dang_muon=danh_sach_dang_muon,
            so_yeu_cau_muon=len(danh_sach_cho_duyet),
            so_yeu_cau_gia_han=len(danh_sach_cho_gia_han),
            so_sach_dang_muon=len(danh_sach_dang_muon),
            tong_so_sach=Sach.query.count(),
            now = datetime.now()
        )

    @app.route('/api/thuthu/phieu-muon/<int:phieu_id>/duyet', methods=['POST'])
    def api_duyet_muon(phieu_id):
        if not current_user.is_authenticated:
            return jsonify({
                "success": False,
                "message": "Vui lòng đăng nhập!"
            }), 401

        if current_user.role != UserRole.THUTHU:
            return jsonify({
                "success": False,
                "message": "Bạn không có quyền!"
            }), 403

        success, message = dao.duyet_phieu_muon(phieu_id)

        return jsonify({
            "success": success,
            "message": message
        }), 200 if success else 400

    @app.route('/api/thuthu/phieu-muon/<int:phieu_id>/tu-choi', methods=['POST'])
    def api_tu_choi_muon(phieu_id):
        if not current_user.is_authenticated:
            return jsonify({
                "success": False,
                "message": "Vui lòng đăng nhập!"
            }), 401

        if current_user.role != UserRole.THUTHU:
            return jsonify({
                "success": False,
                "message": "Bạn không có quyền!"
            }), 403

        success, message = dao.tu_choi_phieu_muon(phieu_id)

        return jsonify({
            "success": success,
            "message": message
        }), 200 if success else 400

    @app.route('/api/thuthu/phieu-muon/<int:phieu_id>/duyet-gia-han', methods=['POST'])
    def api_duyet_gia_han(phieu_id):
        if not current_user.is_authenticated:
            return jsonify({
                "success": False,
                "message": "Vui lòng đăng nhập!"
            }), 401

        if current_user.role != UserRole.THUTHU:
            return jsonify({
                "success": False,
                "message": "Bạn không có quyền!"
            }), 403

        success, message = dao.duyet_gia_han(phieu_id)

        return jsonify({
            "success": success,
            "message": message
        }), 200 if success else 400

    @app.route('/api/thuthu/phieu-muon/<int:phieu_id>/tu-choi-gia-han', methods=['POST'])
    def api_tu_choi_gia_han(phieu_id):
        if not current_user.is_authenticated:
            return jsonify({
                "success": False,
                "message": "Vui lòng đăng nhập!"
            }), 401

        if current_user.role != UserRole.THUTHU:
            return jsonify({
                "success": False,
                "message": "Bạn không có quyền!"
            }), 403

        success, message = dao.tu_choi_gia_han(phieu_id)

        return jsonify({
            "success": success,
            "message": message
        }), 200 if success else 400

    @app.route('/sach-dang-muon')
    def sach_dang_muon():
        if not current_user.is_authenticated:
            return redirect(url_for('login_process'))

        if current_user.role != UserRole.DOCGIA:
            return abort(403)

        danh_sach_dang_muon = dao.get_phieu_muon_dang_muon_cua_doc_gia(
            current_user.id
        )

        return render_template(
            'sach_dang_muon.html',
            danh_sach_dang_muon=danh_sach_dang_muon
        )

    @app.route('/api/phieu-muon/<int:phieu_muon_id>/tra-sach', methods=['POST'])
    def api_tra_sach(phieu_muon_id):

        if not current_user.is_authenticated:
            return jsonify({
                "success": False,
                "message": "Vui lòng đăng nhập!"
            }), 401

        if current_user.role != UserRole.DOCGIA:
            return jsonify({
                "success": False,
                "message": "Chỉ độc giả mới được trả sách!"
            }), 403

        success, message = dao.tra_sach(
            current_user.id,
            phieu_muon_id
        )

        return jsonify({
            "success": success,
            "message": message
        }), 200 if success else 400


@login.user_loader
def load_user(id):
    return dao.get_user_by_id(id)


if __name__ == '__main__':
    register_routes(app)
    with app.app_context():
        app.run(debug=True, port=5000)
