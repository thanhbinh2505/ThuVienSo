from sqlalchemy import or_

from app import db
from app.models import OAuthProvider, Sach, TheLoai, User, UserRole


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