from datetime import datetime, timedelta

from sqlalchemy import or_

from app import db
from app.models import OAuthProvider, Sach, TheLoai, User, UserRole, DanhGia, BinhLuan, TrangThaiMuon, PhieuMuon


def commit():
    db.session.commit()


def rollback():
    db.session.rollback()

def get_list_theloai():
    return TheLoai.query.order_by(TheLoai.tenTheLoai).all()

def tim_kiem_sach(tu_khoa="", theloai_id=None, page=1, page_size=12, sort="moi_nhat"):
    query = Sach.query

    if tu_khoa:
        tu_khoa_like = f"%{tu_khoa.strip()}%"
        query = query.filter(or_(
            Sach.tenSach.ilike(tu_khoa_like),
            Sach.tacGia.ilike(tu_khoa_like),
            Sach.moTa.ilike(tu_khoa_like),
        ))

    if theloai_id:
        query = query.filter(Sach.theloai_id == theloai_id)

    if sort == "ten_az":
        query = query.order_by(Sach.tenSach.asc())
    elif sort == "danh_gia":
        query = query.order_by(Sach.diemDanhGiaTB.desc())
    else:
        query = query.order_by(Sach.ngayTao.desc())

    total = query.count()
    ds_sach = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
        "items": [s.to_dict() for s in ds_sach],
    }

def get_sach_by_id(sach_id):
    return Sach.query.get(sach_id)


def get_sach_lien_quan(sach, so_luong=4):
    if not sach.theloai_id:
        return []
    return Sach.query.filter(
        Sach.theloai_id == sach.theloai_id,
        Sach.id != sach.id
    ).order_by(Sach.diemDanhGiaTB.desc()).limit(so_luong).all()

def get_user_by_id(id):
    return User.query.get(id)


def get_user_by_dinh_danh(dinh_danh):
    return User.query.filter(or_(
        User.username == dinh_danh,
        User.email == dinh_danh,
        User.soDienThoai == dinh_danh
    )).first()


def kiem_tra_ton_tai(username=None, email=None, sdt=None):
    if username and User.query.filter(User.username == username).first():
        return "Username đã tồn tại!"
    if email and User.query.filter(User.email == email).first():
        return "Email đã được sử dụng!"
    if sdt and User.query.filter(User.soDienThoai == sdt).first():
        return "Số điện thoại đã được sử dụng!"
    return None


def dang_ky_doc_gia(username, hoten, password, email=None, sdt=None,
                     gioitinh=True, ngaysinh=None):
    try:
        loi = kiem_tra_ton_tai(username=username, email=email, sdt=sdt)
        if loi:
            return False, loi, None

        user = User(
            username=username,
            hoTen=hoten,
            email=email,
            soDienThoai=sdt,
            gioiTinh=gioitinh,
            ngaySinh=ngaysinh,
            role=UserRole.DOCGIA,
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()
        return True, "Đăng ký thành công!", user

    except Exception as e:
        db.session.rollback()
        raise e


def dang_nhap(dinh_danh, password):
    user = get_user_by_dinh_danh(dinh_danh)
    if not user:
        return None, "Tài khoản không tồn tại!"
    if not user.check_password(password):
        return None, "Mật khẩu không chính xác!"
    if not user.active:
        return None, "Tài khoản đã bị khóa!"
    return user, "Đăng nhập thành công!"

def dang_nhap_hoac_tao_tai_khoan_oauth(provider: OAuthProvider, oauth_id, email=None,
                                        hoten=None, avatar=None):
    try:
        user = User.query.filter(
            User.oauthProvider == provider,
            User.oauthId == str(oauth_id)
        ).first()

        if user:
            return user, False

        if email:
            user = User.query.filter(User.email == email).first()
            if user:
                user.oauthProvider = provider
                user.oauthId = str(oauth_id)
                if avatar and not user.avatar:
                    user.avatar = avatar
                db.session.commit()
                return user, False

        username_goi_y = None
        if email:
            username_goi_y = email.split('@')[0]
        if not username_goi_y:
            username_goi_y = f"{provider.name.lower()}_{oauth_id}"[:20]

        username_thu = username_goi_y
        dem = 1
        while User.query.filter(User.username == username_thu).first():
            username_thu = f"{username_goi_y}{dem}"
            dem += 1

        user = User(
            username=username_thu,
            hoTen=hoten or username_thu,
            email=email,
            avatar=avatar,
            role=UserRole.DOCGIA,
            oauthProvider=provider,
            oauthId=str(oauth_id),
        )
        db.session.add(user)
        db.session.commit()
        return user, True

    except Exception as e:
        db.session.rollback()
        raise e

def danh_gia_sach(user_id, sach_id, so_sao):
    try:
        if so_sao < 1 or so_sao > 5:
            return False, "Số sao phải từ 1 đến 5!"

        sach = get_sach_by_id(sach_id)

        if not sach:
            return False, "Không tìm thấy sách!"

        danh_gia_cu = DanhGia.query.filter_by(
            user_id=user_id,
            sach_id=sach_id
        ).first()

        if danh_gia_cu:
            # Người này đã đánh giá trước đó
            # Chỉ thay đổi số sao
            danh_gia_cu.soSao = so_sao
            danh_gia_cu.ngayTao = datetime.now()

        else:
            # Người này đánh giá lần đầu
            danh_gia_moi = DanhGia(
                user_id=user_id,
                sach_id=sach_id,
                soSao=so_sao
            )

            db.session.add(danh_gia_moi)

        db.session.flush()

        # Lấy toàn bộ đánh giá của cuốn sách
        danh_sach = DanhGia.query.filter_by(
            sach_id=sach_id
        ).all()

        # Tính lại số lượt đánh giá
        sach.soLuotDanhGia = len(danh_sach)

        # Tính lại điểm trung bình
        if sach.soLuotDanhGia > 0:
            tong_diem = sum(d.soSao for d in danh_sach)
            sach.diemDanhGiaTB = tong_diem / sach.soLuotDanhGia
        else:
            sach.diemDanhGiaTB = 0

        db.session.commit()

        return True, "Đánh giá sách thành công!"

    except Exception as e:
        db.session.rollback()
        print("LỖI ĐÁNH GIÁ:", e)
        return False, "Có lỗi xảy ra khi đánh giá!"

def them_binh_luan(user_id, sach_id, noi_dung):
    try:
        if not noi_dung or not noi_dung.strip():
            return False, "Nội dung bình luận không được để trống!", None

        sach = get_sach_by_id(sach_id)

        if not sach:
            return False, "Không tìm thấy sách!", None

        binh_luan = BinhLuan(
            user_id=user_id,
            sach_id=sach_id,
            noiDung=noi_dung.strip()
        )

        db.session.add(binh_luan)
        db.session.commit()

        return True, "Bình luận thành công!", binh_luan

    except Exception as e:
        db.session.rollback()
        print("LỖI BÌNH LUẬN:", e)
        return False, "Có lỗi xảy ra khi bình luận!", None


def get_binh_luan_sach(sach_id):
    return BinhLuan.query.filter_by(
        sach_id=sach_id
    ).order_by(
        BinhLuan.ngayTao.desc()
    ).all()


def xoa_binh_luan(user_id, binh_luan_id):
    try:
        binh_luan = BinhLuan.query.get(binh_luan_id)

        if not binh_luan:
            return False, "Không tìm thấy bình luận!"

        if binh_luan.user_id != user_id:
            return False, "Bạn không có quyền xóa bình luận này!"

        db.session.delete(binh_luan)
        db.session.commit()

        return True, "Đã xóa bình luận!"

    except Exception as e:
        db.session.rollback()
        print("LỖI XÓA BÌNH LUẬN:", e)
        return False, "Có lỗi xảy ra khi xóa bình luận!"

def dang_ky_muon_sach(user_id, sach_id):
    try:
        sach = get_sach_by_id(sach_id)

        if not sach:
            return False, "Không tìm thấy sách!"

        if sach.soLuongConLai <= 0:
            return False, "Sách hiện đã hết!"
        so_sach_dang_muon = PhieuMuon.query.filter(
            PhieuMuon.user_id == user_id,
            PhieuMuon.trangThai.in_([
                TrangThaiMuon.DA_DUYET,
                TrangThaiMuon.CHO_DUYET
            ])
        ).count()

        if so_sach_dang_muon >= 5:
            return False, "Bạn đã đạt giới hạn tối đa 5 cuốn sách được mượn!"


        # Kiểm tra người dùng có yêu cầu đang chờ duyệt không
        phieu_dang_cho = PhieuMuon.query.filter(
            PhieuMuon.user_id == user_id,
            PhieuMuon.sach_id == sach_id,
            PhieuMuon.trangThai == TrangThaiMuon.CHO_DUYET
        ).first()

        if phieu_dang_cho:
            return False, "Bạn đã đăng ký mượn sách này và đang chờ duyệt!"

        # Kiểm tra đang mượn sách này
        phieu_dang_muon = PhieuMuon.query.filter(
            PhieuMuon.user_id == user_id,
            PhieuMuon.sach_id == sach_id,
            PhieuMuon.trangThai == TrangThaiMuon.DA_DUYET
        ).first()

        if phieu_dang_muon:
            return False, "Bạn đang mượn sách này!"

        phieu = PhieuMuon(
            user_id=user_id,
            sach_id=sach_id,
            trangThai=TrangThaiMuon.CHO_DUYET
        )

        db.session.add(phieu)
        db.session.commit()

        return True, "Đăng ký mượn sách thành công!"

    except Exception as e:
        db.session.rollback()
        print("LỖI ĐĂNG KÝ MƯỢN:", e)
        return False, "Có lỗi xảy ra khi đăng ký mượn!"

def gui_yeu_cau_gia_han(user_id, phieu_muon_id):
    try:
        phieu = PhieuMuon.query.get(phieu_muon_id)

        if not phieu:
            return False, "Không tìm thấy phiếu mượn!"

        if phieu.user_id != user_id:
            return False, "Bạn không có quyền gia hạn phiếu mượn này!"

        if phieu.trangThai != TrangThaiMuon.DA_DUYET:
            return False, "Chỉ sách đang được mượn mới có thể yêu cầu gia hạn!"

        if not phieu.hanTra:
            return False, "Phiếu mượn chưa có hạn trả!"

        phieu.trangThai = TrangThaiMuon.CHO_GIA_HAN

        db.session.commit()

        return True, "Đã gửi yêu cầu gia hạn!"

    except Exception as e:
        db.session.rollback()
        print("LỖI GIA HẠN:", repr(e))
        return False, "Có lỗi xảy ra khi gửi yêu cầu gia hạn!"

def get_phieu_muon_cho_duyet():
    return PhieuMuon.query.filter_by(
        trangThai=TrangThaiMuon.CHO_DUYET
    ).order_by(
        PhieuMuon.ngayDangKy.desc()
    ).all()


def get_phieu_muon_cho_gia_han():
    return PhieuMuon.query.filter_by(
        trangThai=TrangThaiMuon.CHO_GIA_HAN
    ).order_by(
        PhieuMuon.ngayDangKy.desc()
    ).all()


def get_phieu_muon_dang_muon():
    return PhieuMuon.query.filter_by(
        trangThai=TrangThaiMuon.DA_DUYET
    ).order_by(
        PhieuMuon.ngayMuon.desc()
    ).all()

def duyet_phieu_muon(phieu_id):
    try:
        phieu = PhieuMuon.query.get(phieu_id)

        if not phieu:
            return False, "Không tìm thấy yêu cầu mượn!"

        if phieu.trangThai != TrangThaiMuon.CHO_DUYET:
            return False, "Yêu cầu này không còn ở trạng thái chờ duyệt!"

        sach = get_sach_by_id(phieu.sach_id)

        if not sach:
            return False, "Không tìm thấy sách!"

        if sach.soLuongConLai <= 0:
            return False, "Sách đã hết!"

        # KIỂM TRA GIỚI HẠN 5 CUỐN
        so_sach_dang_muon = PhieuMuon.query.filter(
            PhieuMuon.user_id == phieu.user_id,
            PhieuMuon.trangThai == TrangThaiMuon.DA_DUYET
        ).count()

        if so_sach_dang_muon >= 5:
            return False, "Độc giả đã đạt giới hạn tối đa 5 cuốn đang mượn!"

        # Duyệt phiếu
        phieu.trangThai = TrangThaiMuon.DA_DUYET
        phieu.ngayDuyet = datetime.now()
        phieu.ngayMuon = datetime.now()

        # Hạn trả 7 ngày
        from datetime import timedelta
        phieu.hanTra = datetime.now() + timedelta(days=7)

        # Giảm số lượng sách
        sach.soLuongConLai -= 1

        db.session.commit()

        return True, "Đã duyệt yêu cầu mượn!"

    except Exception as e:
        db.session.rollback()
        print("LỖI DUYỆT MƯỢN:", repr(e))
        return False, "Có lỗi xảy ra khi duyệt yêu cầu!"


def tu_choi_phieu_muon(phieu_id):
    try:
        phieu = PhieuMuon.query.get(phieu_id)

        if not phieu:
            return False, "Không tìm thấy yêu cầu mượn!"

        if phieu.trangThai != TrangThaiMuon.CHO_DUYET:
            return False, "Yêu cầu này không còn ở trạng thái chờ duyệt!"

        phieu.trangThai = TrangThaiMuon.TU_CHOI
        phieu.ngayDuyet = datetime.now()

        db.session.commit()

        return True, "Đã từ chối yêu cầu mượn!"

    except Exception as e:
        db.session.rollback()
        print("LỖI TỪ CHỐI MƯỢN:", repr(e))
        return False, "Có lỗi xảy ra khi từ chối yêu cầu!"


def duyet_gia_han(phieu_id):
    try:
        phieu = PhieuMuon.query.get(phieu_id)

        if not phieu:
            return False, "Không tìm thấy yêu cầu gia hạn!"

        if phieu.trangThai != TrangThaiMuon.CHO_GIA_HAN:
            return False, "Yêu cầu này không ở trạng thái chờ gia hạn!"

        if not phieu.hanTra:
            return False, "Phiếu mượn chưa có hạn trả!"

        from datetime import timedelta

        # Gia hạn thêm 7 ngày
        phieu.hanTra = phieu.hanTra + timedelta(days=7)

        # Quay về trạng thái đang mượn
        phieu.trangThai = TrangThaiMuon.DA_DUYET

        db.session.commit()

        return True, "Đã duyệt gia hạn thêm 7 ngày!"

    except Exception as e:
        db.session.rollback()
        print("LỖI DUYỆT GIA HẠN:", repr(e))
        return False, "Có lỗi xảy ra khi duyệt gia hạn!"


def tu_choi_gia_han(phieu_id):
    try:
        phieu = PhieuMuon.query.get(phieu_id)

        if not phieu:
            return False, "Không tìm thấy yêu cầu gia hạn!"

        if phieu.trangThai != TrangThaiMuon.CHO_GIA_HAN:
            return False, "Yêu cầu này không ở trạng thái chờ gia hạn!"

        # Trả về trạng thái đang mượn
        phieu.trangThai = TrangThaiMuon.DA_DUYET

        db.session.commit()

        return True, "Đã từ chối yêu cầu gia hạn!"

    except Exception as e:
        db.session.rollback()
        print("LỖI TỪ CHỐI GIA HẠN:", repr(e))
        return False, "Có lỗi xảy ra khi từ chối gia hạn!"

def get_phieu_muon_dang_muon_cua_doc_gia(user_id):
    return PhieuMuon.query.filter(
        PhieuMuon.user_id == user_id,
        PhieuMuon.trangThai.in_([
            TrangThaiMuon.DA_DUYET,
            TrangThaiMuon.CHO_GIA_HAN
        ])
    ).order_by(
        PhieuMuon.hanTra.asc()
    ).all()

def tra_sach(user_id, phieu_muon_id):
    try:
        phieu = PhieuMuon.query.get(phieu_muon_id)

        if not phieu:
            return False, "Không tìm thấy phiếu mượn!"

        if phieu.user_id != user_id:
            return False, "Bạn không có quyền trả phiếu mượn này!"

        if phieu.trangThai != TrangThaiMuon.DA_DUYET:
            return False, "Sách này không ở trạng thái đang mượn!"

        sach = get_sach_by_id(phieu.sach_id)

        if not sach:
            return False, "Không tìm thấy sách!"

        phieu.trangThai = TrangThaiMuon.DA_TRA

        sach.soLuongConLai += 1

        db.session.commit()

        return True, "Trả sách thành công!"

    except Exception as e:
        db.session.rollback()
        print("LỖI TRẢ SÁCH:", repr(e))
        return False, "Có lỗi xảy ra khi trả sách!"

def huy_phieu_qua_han(phieu_id):
    try:
        phieu = PhieuMuon.query.get(phieu_id)

        if not phieu:
            return False, "Không tìm thấy yêu cầu mượn!"

        if phieu.trangThai != TrangThaiMuon.DA_DUYET:
            return False, "Yêu cầu này không ở trạng thái chờ nhận sách!"

        if not phieu.ngayDuyet:
            return False, "Phiếu chưa có ngày duyệt!"

        han_nhan = phieu.ngayDuyet + timedelta(days=2)

        if datetime.now() <= han_nhan:
            return False, "Yêu cầu này chưa quá hạn nhận sách!"

        phieu.trangThai = TrangThaiMuon.DA_HUY

        db.session.commit()

        return True, "Đã hủy yêu cầu mượn quá hạn nhận sách!"

    except Exception as e:
        db.session.rollback()
        print("LỖI HỦY PHIẾU QUÁ HẠN:", repr(e))
        return False, "Có lỗi xảy ra khi hủy yêu cầu!"