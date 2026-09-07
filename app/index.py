from flask import (abort, jsonify, redirect, render_template, request,
                    url_for)
from flask_login import current_user, login_user, logout_user
from marshmallow import ValidationError

import app.schemas as schemas
from app import app, dao, login, oauth
from app.decorator import anonymous_required, role_required
from app.models import OAuthProvider, UserRole,  TheLoai, Sach, User
from datetime import datetime
import os
from openpyxl import load_workbook
from werkzeug.utils import secure_filename
import random
from flask import session

from flask_mail import Message
from app import mail


def register_routes(app):
    @app.route('/')
    def index():
        ds_theloai = dao.get_list_theloai()

        ket_qua = dao.tim_kiem_sach(
            page=1,
            page_size=12
        )

        sach_goi_y = []

        if current_user.is_authenticated:
            sach_goi_y = dao.get_sach_goi_y(
                current_user.id
            )

        return render_template(
            'index.html',
            ds_theloai=ds_theloai,
            ket_qua=ket_qua,
            sach_goi_y=sach_goi_y
        )

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

        # Lưu lịch sử xem
        if current_user.is_authenticated:
            dao.luu_lich_su_xem(
                current_user.id,
                sach_id
            )

        danh_sach_binh_luan = dao.get_binh_luan_sach(sach_id)

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
                        return redirect(url_for('quan_ly_sach'))
                    elif user.role == UserRole.THUTHU:
                        return redirect('/thuthu')
                    return redirect('/')

        return render_template('login.html', error=error_msg, dinh_danh_val=dinh_danh_val)


    @app.route('/logout', methods=['GET', 'POST'])
    def logout_process():
        logout_user()
        return redirect('/')

    @app.route('/quen-mat-khau', methods=['GET', 'POST'])
    @anonymous_required
    def quen_mat_khau():

        if request.method == 'POST':

            dinh_danh = request.form.get(
                'dinh_danh', ''
            ).strip()

            phuong_thuc = request.form.get(
                'phuong_thuc', ''
            )

            if not dinh_danh:
                return render_template(
                    'quen_mat_khau.html',
                    error="Vui lòng nhập Email hoặc số điện thoại!"
                )

            # =========================
            # TÌM USER BẰNG EMAIL
            # =========================

            if phuong_thuc == 'email':

                user = User.query.filter_by(
                    email=dinh_danh
                ).first()

                if not user:
                    return render_template(
                        'quen_mat_khau.html',
                        error="Không tìm thấy Email này!"
                    )

            # =========================
            # TÌM USER BẰNG SỐ ĐIỆN THOẠI
            # =========================

            elif phuong_thuc == 'sms':

                user = User.query.filter_by(
                    soDienThoai=dinh_danh
                ).first()

                if not user:
                    return render_template(
                        'quen_mat_khau.html',
                        error="Không tìm thấy số điện thoại này!"
                    )

            else:

                return render_template(
                    'quen_mat_khau.html',
                    error="Phương thức không hợp lệ!"
                )

            # =========================
            # TẠO OTP 6 SỐ
            # =========================

            otp = str(random.randint(100000, 999999))

            # Lưu OTP vào session
            session['reset_otp'] = otp
            session['reset_user_id'] = user.id
            session['reset_method'] = phuong_thuc

            # =========================
            # GỬI EMAIL
            # =========================

            if phuong_thuc == 'email':

                try:

                    msg = Message(
                        subject="Mã OTP đặt lại mật khẩu",
                        sender=app.config['MAIL_USERNAME'],
                        recipients=[user.email]
                    )

                    msg.body = f"""
    Mã OTP đặt lại mật khẩu của bạn là:

    {otp}

    Mã có hiệu lực trong 5 phút.
    """

                    mail.send(msg)

                except Exception as e:

                    print("LỖI GỬI EMAIL:", e)

                    return render_template(
                        'quen_mat_khau.html',
                        error="Không thể gửi Email!"
                    )

            # =========================
            # SMS
            # =========================

            elif phuong_thuc == 'sms':

                # TẠM THỜI CHƯA CÓ DỊCH VỤ SMS
                # Sau đó sẽ tích hợp Twilio

                print(
                    f"OTP gửi đến {user.soDienThoai}: {otp}"
                )

            # Chuyển sang trang nhập OTP

            return redirect(
                url_for('xac_nhan_otp')
            )

        return render_template(
            'quen_mat_khau.html'
        )

    @app.route('/xac-nhan-otp', methods=['GET', 'POST'])
    @anonymous_required
    def xac_nhan_otp():

        # Nếu chưa có OTP thì quay lại trang quên mật khẩu
        if 'reset_otp' not in session:
            return redirect(
                url_for('quen_mat_khau')
            )

        error = ""

        if request.method == 'POST':

            otp_nhap = request.form.get(
                'otp', ''
            ).strip()

            otp_he_thong = session.get(
                'reset_otp'
            )

            # Kiểm tra OTP
            if otp_nhap != otp_he_thong:

                error = "Mã OTP không đúng!"

            else:

                # Lưu user_id để bước đặt lại mật khẩu sử dụng
                user_id = session.get(
                    'reset_user_id'
                )

                # Xóa OTP sau khi xác nhận thành công
                session.pop(
                    'reset_otp',
                    None
                )

                return redirect(
                    url_for(
                        'dat_lai_mat_khau',
                        user_id=user_id
                    )
                )

        return render_template(
            'xac_nhan_otp.html',
            error=error
        )

    @app.route('/dat-lai-mat-khau/<int:user_id>', methods=['GET', 'POST'])
    @anonymous_required
    def dat_lai_mat_khau(user_id):

        user = dao.get_user_by_id(user_id)

        if not user:
            abort(404)

        if request.method == 'POST':

            password = request.form.get('password', '').strip()
            confirm_password = request.form.get(
                'confirm_password', ''
            ).strip()

            # Kiểm tra nhập đầy đủ
            if not password or not confirm_password:
                return render_template(
                    'dat_lai_mat_khau.html',
                    error="Vui lòng nhập đầy đủ mật khẩu!"
                )

            # Kiểm tra 2 mật khẩu giống nhau
            if password != confirm_password:
                return render_template(
                    'dat_lai_mat_khau.html',
                    error="Mật khẩu xác nhận không khớp!"
                )

            # Cập nhật mật khẩu
            success, message = dao.dat_lai_mat_khau(
                user_id,
                password
            )

            if success:
                return redirect(
                    url_for(
                        'login_process'
                    )
                )

            return render_template(
                'dat_lai_mat_khau.html',
                error=message
            )

        return render_template(
            'dat_lai_mat_khau.html'
        )


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

    @app.route('/admin/sach')
    @role_required(UserRole.ADMIN)
    def quan_ly_sach():

        danh_sach_sach = dao.get_all_sach()

        return render_template(
            'quan_li_sach.html',
            danh_sach_sach=danh_sach_sach
        )

    @app.route('/admin/sach/them', methods=['GET', 'POST'])
    @role_required(UserRole.ADMIN)
    def them_sach():

        danh_sach_theloai = dao.get_list_theloai()

        if request.method == 'POST':

            ten_sach = request.form.get('ten_sach', '').strip()
            tac_gia = request.form.get('tac_gia', '').strip()

            nha_xuat_ban = request.form.get(
                'nha_xuat_ban', ''
            ).strip()

            nam_xuat_ban = request.form.get('nam_xuat_ban')
            ngon_ngu = request.form.get(
                'ngon_ngu', 'Tiếng Việt'
            )

            so_trang = request.form.get('so_trang')

            mo_ta = request.form.get('mo_ta', '').strip()

            theloai_id = request.form.get('theloai_id')

            so_luong = request.form.get('so_luong', 0)

            file = request.files.get('anh_bia')

            anh_bia_url = request.form.get('anh_bia_url', '').strip()

            anh_bia = None

            if file and file.filename != '':
                filename = secure_filename(file.filename)

                file.save(
                    os.path.join(
                        app.config['UPLOAD_FOLDER'],
                        filename
                    )
                )

                anh_bia = f'/static/images/sach/{filename}'

            elif anh_bia_url:
                anh_bia = anh_bia_url

            # Kiểm tra dữ liệu bắt buộc
            if not ten_sach or not tac_gia:
                return render_template(
                    'them_sach.html',
                    danh_sach_theloai=danh_sach_theloai,
                    error="Vui lòng nhập tên sách và tác giả!"
                )

            try:
                nam_xuat_ban = (
                    int(nam_xuat_ban)
                    if nam_xuat_ban else None
                )

                so_trang = (
                    int(so_trang)
                    if so_trang else None
                )

                theloai_id = (
                    int(theloai_id)
                    if theloai_id else None
                )

                so_luong = int(so_luong)

                if so_luong < 0:
                    raise ValueError

            except ValueError:

                return render_template(
                    'them_sach.html',
                    danh_sach_theloai=danh_sach_theloai,
                    error="Dữ liệu số không hợp lệ!"
                )

            success, message, sach = dao.them_sach(
                ten_sach=ten_sach,
                tac_gia=tac_gia,
                nha_xuat_ban=nha_xuat_ban,
                nam_xuat_ban=nam_xuat_ban,
                ngon_ngu=ngon_ngu,
                so_trang=so_trang,
                mo_ta=mo_ta,
                theloai_id=theloai_id,
                anh_bia=anh_bia,
                so_luong=so_luong
            )

            if success:
                return redirect(
                    url_for('quan_ly_sach')
                )

            return render_template(
                'them_sach.html',
                danh_sach_theloai=danh_sach_theloai,
                error=message
            )

        return render_template(
            'them_sach.html',
            danh_sach_theloai=danh_sach_theloai
        )

    @app.route(
        '/admin/sach/<int:sach_id>/sua',
        methods=['GET', 'POST']
    )
    @role_required(UserRole.ADMIN)
    def sua_sach(sach_id):

        sach = dao.get_sach_by_id(sach_id)

        if not sach:
            abort(404)

        danh_sach_theloai = dao.get_list_theloai()

        if request.method == 'POST':

            ten_sach = request.form.get(
                'ten_sach', ''
            ).strip()

            tac_gia = request.form.get(
                'tac_gia', ''
            ).strip()

            nha_xuat_ban = request.form.get(
                'nha_xuat_ban', ''
            ).strip()

            nam_xuat_ban = request.form.get(
                'nam_xuat_ban'
            )

            ngon_ngu = request.form.get(
                'ngon_ngu', 'Tiếng Việt'
            )

            so_trang = request.form.get(
                'so_trang'
            )

            mo_ta = request.form.get(
                'mo_ta', ''
            ).strip()

            theloai_id = request.form.get(
                'theloai_id'
            )

            so_luong = request.form.get(
                'so_luong'
            )
            file = request.files.get('anh_bia_file')

            anh_bia_url = request.form.get(
                'anh_bia_url',
                ''
            ).strip()

            anh_bia = sach.anhBia

            if file and file.filename != '':
                filename = secure_filename(file.filename)

                file.save(
                    os.path.join(
                        app.config['UPLOAD_FOLDER'],
                        filename
                    )
                )

                anh_bia = f'/static/images/sach/{filename}'

            elif anh_bia_url:
                anh_bia = anh_bia_url

            if not ten_sach or not tac_gia:
                return render_template(
                    'sua_sach.html',
                    sach=sach,
                    danh_sach_theloai=danh_sach_theloai,
                    error="Vui lòng nhập tên sách và tác giả!"
                )

            try:

                nam_xuat_ban = (
                    int(nam_xuat_ban)
                    if nam_xuat_ban else None
                )

                so_trang = (
                    int(so_trang)
                    if so_trang else None
                )

                theloai_id = (
                    int(theloai_id)
                    if theloai_id else None
                )

                so_luong = int(so_luong)

                if so_luong < 0:
                    raise ValueError

            except ValueError:

                return render_template(
                    'sua_sach.html',
                    sach=sach,
                    danh_sach_theloai=danh_sach_theloai,
                    error="Dữ liệu số không hợp lệ!"
                )

            success, message = dao.cap_nhat_sach(
                sach_id=sach_id,
                ten_sach=ten_sach,
                tac_gia=tac_gia,
                nha_xuat_ban=nha_xuat_ban,
                nam_xuat_ban=nam_xuat_ban,
                ngon_ngu=ngon_ngu,
                so_trang=so_trang,
                mo_ta=mo_ta,
                theloai_id=theloai_id,
                so_luong=so_luong,
                anh_bia=anh_bia
            )

            if success:
                return redirect(
                    url_for('quan_ly_sach')
                )

            return render_template(
                'sua_sach.html',
                sach=sach,
                danh_sach_theloai=danh_sach_theloai,
                error=message
            )

        return render_template(
            'sua_sach.html',
            sach=sach,
            danh_sach_theloai=danh_sach_theloai
        )

    @app.route(
        '/admin/sach/<int:sach_id>/xoa',
        methods=['POST']
    )
    @role_required(UserRole.ADMIN)
    def xoa_sach(sach_id):

        success, message = dao.xoa_sach(sach_id)

        return redirect(
            url_for('quan_ly_sach')
        )

    # ==========================================
    # QUẢN LÝ NGƯỜI DÙNG - ADMIN
    # ==========================================

    @app.route('/admin/nguoi-dung')
    @role_required(UserRole.ADMIN)
    def quan_ly_nguoi_dung():

        danh_sach_user = dao.get_all_users()

        return render_template(
            'quan_li_nguoi_dung.html',
            danh_sach_user=danh_sach_user
        )

    @app.route(
        '/admin/nguoi-dung/<int:user_id>/khoa',
        methods=['POST']
    )
    @role_required(UserRole.ADMIN)
    def khoa_nguoi_dung(user_id):

        dao.khoa_user(user_id)

        return redirect(
            url_for('quan_ly_nguoi_dung')
        )

    @app.route(
        '/admin/nguoi-dung/<int:user_id>/mo-khoa',
        methods=['POST']
    )
    @role_required(UserRole.ADMIN)
    def mo_khoa_nguoi_dung(user_id):

        dao.mo_khoa_user(user_id)

        return redirect(
            url_for('quan_ly_nguoi_dung')
        )

    @app.route(
        '/admin/nguoi-dung/<int:user_id>/xoa',
        methods=['POST']
    )
    @role_required(UserRole.ADMIN)
    def xoa_nguoi_dung(user_id):

        dao.xoa_user(user_id)

        return redirect(
            url_for('quan_ly_nguoi_dung')
        )

    @app.route('/admin/sach/import', methods=['GET', 'POST'])
    @role_required(UserRole.ADMIN)
    def import_sach_excel():

        if request.method == 'POST':
            file = request.files.get('file')

            if not file or file.filename == '':
                return render_template(
                    'import_sach.html',
                    message="Vui lòng chọn file Excel!"
                )

            if not file.filename.lower().endswith(('.xlsx', '.xlsm')):
                return render_template(
                    'import_sach.html',
                    message="Chỉ chấp nhận file Excel .xlsx hoặc .xlsm!"
                )

            try:
                wb = load_workbook(file, data_only=True)
                ws = wb.active

                danh_sach_sach = []

                # Bỏ dòng tiêu đề
                for row in ws.iter_rows(min_row=2, values_only=True):

                    if not row[0]:
                        continue

                    ten_sach = str(row[0]).strip()
                    tac_gia = str(row[1]).strip() if row[1] else ""

                    nha_xuat_ban = str(row[2]).strip() if row[2] else None

                    nam_xuat_ban = None
                    if row[3]:
                        try:
                            nam_xuat_ban = int(row[3])
                        except:
                            nam_xuat_ban = None

                    ngon_ngu = str(row[4]).strip() if row[4] else "Tiếng Việt"

                    so_trang = None
                    if row[5]:
                        try:
                            so_trang = int(row[5])
                        except:
                            so_trang = None

                    theloai_id = None
                    if row[6]:
                        try:
                            theloai_id = int(row[6])
                        except:
                            theloai_id = None

                    so_luong = 0
                    if row[7]:
                        try:
                            so_luong = int(row[7])
                        except:
                            so_luong = 0

                    anh_bia = str(row[8]).strip() if row[8] else None
                    mo_ta = str(row[9]).strip() if row[9] else None

                    if not tac_gia:
                        continue

                    danh_sach_sach.append({
                        "ten_sach": ten_sach,
                        "tac_gia": tac_gia,
                        "nha_xuat_ban": nha_xuat_ban,
                        "nam_xuat_ban": nam_xuat_ban,
                        "ngon_ngu": ngon_ngu,
                        "so_trang": so_trang,
                        "theloai_id": theloai_id,
                        "so_luong": so_luong,
                        "anh_bia": anh_bia,
                        "mo_ta": mo_ta
                    })

                if not danh_sach_sach:
                    return render_template(
                        'import_sach.html',
                        message="File Excel không có dữ liệu hợp lệ!"
                    )

                success, message = dao.import_sach_tu_excel(danh_sach_sach)

                return render_template(
                    'import_sach.html',
                    message=message,
                    success=success
                )

            except Exception as e:
                print("LỖI ĐỌC FILE EXCEL:", repr(e))

                return render_template(
                    'import_sach.html',
                    message="Không thể đọc file Excel!"
                )

        return render_template('import_sach.html')

    @app.route('/admin/the-loai')
    @role_required(UserRole.ADMIN)
    def quan_ly_the_loai():
        danh_sach_the_loai = dao.get_all_theloai()

        return render_template(
            'quan_li_the_loai.html',
            danh_sach_the_loai=danh_sach_the_loai
        )

    @app.route('/admin/the-loai/them', methods=['GET', 'POST'])
    @role_required(UserRole.ADMIN)
    def them_the_loai():
        if request.method == 'POST':
            ten_the_loai = request.form.get('ten_the_loai', '').strip()
            mo_ta = request.form.get('mo_ta', '').strip()

            success, message = dao.them_theloai(
                ten_the_loai,
                mo_ta
            )

            if success:
                return redirect(url_for('quan_ly_the_loai'))

            return render_template(
                'them_the_loai.html',
                message=message
            )

        return render_template('them_the_loai.html')

    @app.route('/admin/the-loai/<int:theloai_id>/sua', methods=['GET', 'POST'])
    @role_required(UserRole.ADMIN)
    def sua_the_loai(theloai_id):
        the_loai = TheLoai.query.get(theloai_id)

        if not the_loai:
            abort(404)

        if request.method == 'POST':
            ten_the_loai = request.form.get('ten_the_loai', '').strip()
            mo_ta = request.form.get('mo_ta', '').strip()

            success, message = dao.cap_nhat_theloai(
                theloai_id,
                ten_the_loai,
                mo_ta
            )

            if success:
                return redirect(url_for('quan_ly_the_loai'))

            return render_template(
                'sua_the_loai.html',
                the_loai=the_loai,
                message=message
            )

        return render_template(
            'sua_the_loai.html',
            the_loai=the_loai
        )

    @app.route('/admin/the-loai/<int:theloai_id>/xoa', methods=['POST'])
    @role_required(UserRole.ADMIN)
    def xoa_the_loai(theloai_id):
        success, message = dao.xoa_theloai(theloai_id)

        return redirect(url_for('quan_ly_the_loai'))



@login.user_loader
def load_user(id):
    return dao.get_user_by_id(id)


if __name__ == '__main__':
    register_routes(app)
    with app.app_context():
        app.run(debug=True, port=5000)
