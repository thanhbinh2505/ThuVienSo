from datetime import datetime, timedelta
from sqlalchemy import or_
from sklearn.linear_model import LinearRegression
from collections import defaultdict
import numpy as np
from sentence_transformers import SentenceTransformer

from app import db
from app.models import (OAuthProvider, Sach, TheLoai, User, UserRole,
                        DanhGia, BinhLuan, TrangThaiMuon, PhieuMuon,
                        LichSuXem, YeuThich)

model_semantic = None


def get_model_semantic():
    global model_semantic
    if model_semantic is None:
        print("Đang tải AI model...")
        model_semantic = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        print("Đã tải AI model!")
    return model_semantic

def commit():
    db.session.commit()

def rollback():
    db.session.rollback()

# 1. quản lý người dùng và tài khoản

def get_user_by_id(id):
    return User.query.get(id)

def get_user_by_dinh_danh(dinh_danh):
    return User.query.filter(or_(
        User.username == dinh_danh,
        User.email == dinh_danh,
        User.soDienThoai == dinh_danh
    )).first()

def tim_kiem_user(tu_khoa=""):
    query = User.query
    if tu_khoa:
        tu_khoa = tu_khoa.strip()
        query = query.filter(or_(
            User.username.ilike(f"%{tu_khoa}%"),
            User.hoTen.ilike(f"%{tu_khoa}%"),
            User.email.ilike(f"%{tu_khoa}%"),
            User.soDienThoai.ilike(f"%{tu_khoa}%")
        ))
    return query.order_by(User.id.desc()).all()

def kiem_tra_ton_tai(username=None, email=None, sdt=None):
    if username and User.query.filter(User.username == username).first():
        return "Username đã tồn tại!"
    if email and User.query.filter(User.email == email).first():
        return "Email đã được sử dụng!"
    if sdt and User.query.filter(User.soDienThoai == sdt).first():
        return "Số điện thoại đã được sử dụng!"
    return None

def dang_ky_doc_gia(username, hoten, password, email=None, sdt=None, gioitinh=True, ngaysinh=None):
    try:
        loi = kiem_tra_ton_tai(username=username, email=email, sdt=sdt)
        if loi:
            return False, loi, None
        user = User(
            username=username, hoTen=hoten, email=email,
            soDienThoai=sdt, gioiTinh=gioitinh, ngaySinh=ngaysinh,
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

def dang_nhap_hoac_tao_tai_khoan_oauth(provider: OAuthProvider, oauth_id, email=None, hoten=None, avatar=None):
    try:
        user = User.query.filter(User.oauthProvider == provider, User.oauthId == str(oauth_id)).first()
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

        username_goi_y = email.split('@')[0] if email else f"{provider.name.lower()}_{oauth_id}"[:20]
        username_thu = username_goi_y
        dem = 1
        while User.query.filter(User.username == username_thu).first():
            username_thu = f"{username_goi_y}{dem}"
            dem += 1

        user = User(
            username=username_thu, hoTen=hoten or username_thu,
            email=email, avatar=avatar, role=UserRole.DOCGIA,
            oauthProvider=provider, oauthId=str(oauth_id),
        )
        db.session.add(user)
        db.session.commit()
        return user, True
    except Exception as e:
        db.session.rollback()
        raise e

def dat_lai_mat_khau(user_id, password):
    user = User.query.get(user_id)
    if not user:
        return False, "Không tìm thấy tài khoản!"
    try:
        user.set_password(password)
        db.session.commit()
        return True, "Đặt lại mật khẩu thành công!"
    except Exception:
        db.session.rollback()
        return False, "Có lỗi xảy ra khi đặt lại mật khẩu!"

def tim_user_theo_dinh_danh(dinh_danh):
    return User.query.filter(
        (User.username == dinh_danh) |
        (User.email == dinh_danh) |
        (User.soDienThoai == dinh_danh)
    ).first()

# 2. quản trị người dùng (Admin)

def get_all_users():
    return User.query.order_by(User.id.desc()).all()

def khoa_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return False, "Không tìm thấy người dùng!"
        if user.role == UserRole.ADMIN:
            return False, "Không thể khóa tài khoản Admin!"

        user.active = False
        db.session.commit()
        return True, "Đã khóa tài khoản!"
    except Exception as e:
        db.session.rollback()
        print("LỖI KHÓA USER:", repr(e))
        return False, "Có lỗi xảy ra khi khóa tài khoản!"

def mo_khoa_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return False, "Không tìm thấy người dùng!"
        user.active = True
        db.session.commit()
        return True, "Đã mở khóa tài khoản!"
    except Exception as e:
        db.session.rollback()
        print("LỖI MỞ KHÓA USER:", repr(e))
        return False, "Có lỗi xảy ra khi mở khóa tài khoản!"

def xoa_user(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return False, "Không tìm thấy người dùng!"
        if user.role == UserRole.ADMIN:
            return False, "Không thể xóa tài khoản Admin!"

        so_phieu_dang_hoat_dong = PhieuMuon.query.filter(
            PhieuMuon.user_id == user_id,
            PhieuMuon.trangThai.in_([
                TrangThaiMuon.CHO_DUYET, TrangThaiMuon.DA_DUYET, TrangThaiMuon.CHO_GIA_HAN
            ])
        ).count()

        if so_phieu_dang_hoat_dong > 0:
            return False, "Không thể xóa người dùng vì đang có phiếu mượn hoạt động!"

        db.session.delete(user)
        db.session.commit()
        return True, "Đã xóa người dùng!"
    except Exception as e:
        db.session.rollback()
        print("LỖI XÓA USER:", repr(e))
        return False, "Có lỗi xảy ra khi xóa người dùng!"

def get_thong_tin_ho_so(user_id):
    user = User.query.get(user_id)
    if not user:
        return {}
    return {
        "user": user,
        "tong_phieu_muon": PhieuMuon.query.filter_by(user_id=user_id).count(),
        "dang_muon": PhieuMuon.query.filter(
            PhieuMuon.user_id == user_id,
            PhieuMuon.trangThai.in_([TrangThaiMuon.DA_DUYET, TrangThaiMuon.CHO_GIA_HAN])
        ).count(),
        "da_tra": PhieuMuon.query.filter_by(user_id=user_id, trangThai=TrangThaiMuon.DA_TRA).count(),
        "yeu_thich": YeuThich.query.filter_by(user_id=user_id).count(),
    }

# 3. quanr lí sách và thể loại

def get_list_theloai():
    return TheLoai.query.order_by(TheLoai.tenTheLoai).all()

def get_all_theloai():
    return TheLoai.query.order_by(TheLoai.id.desc()).all()

def them_theloai(ten_the_loai, mo_ta=None):
    try:
        ten_the_loai = ten_the_loai.strip()
        if not ten_the_loai:
            return False, "Tên thể loại không được để trống!"

        if TheLoai.query.filter(TheLoai.tenTheLoai.ilike(ten_the_loai)).first():
            return False, "Thể loại này đã tồn tại!"

        the_loai = TheLoai(tenTheLoai=ten_the_loai, moTa=mo_ta.strip() if mo_ta else None)
        db.session.add(the_loai)
        db.session.commit()
        return True, "Thêm thể loại thành công!"
    except Exception as e:
        db.session.rollback()
        print("LỖI THÊM THỂ LOẠI:", repr(e))
        return False, "Có lỗi xảy ra khi thêm thể loại!"

def cap_nhat_theloai(theloai_id, ten_the_loai, mo_ta=None):
    try:
        the_loai = TheLoai.query.get(theloai_id)
        if not the_loai:
            return False, "Không tìm thấy thể loại!"

        ten_the_loai = ten_the_loai.strip()
        if not ten_the_loai:
            return False, "Tên thể loại không được để trống!"

        if TheLoai.query.filter(TheLoai.tenTheLoai.ilike(ten_the_loai), TheLoai.id != theloai_id).first():
            return False, "Tên thể loại này đã tồn tại!"

        the_loai.tenTheLoai = ten_the_loai
        the_loai.moTa = mo_ta.strip() if mo_ta else None
        db.session.commit()
        return True, "Cập nhật thể loại thành công!"
    except Exception as e:
        db.session.rollback()
        print("LỖI CẬP NHẬT THỂ LOẠI:", repr(e))
        return False, "Có lỗi xảy ra khi cập nhật thể loại!"

def xoa_theloai(theloai_id):
    try:
        the_loai = TheLoai.query.get(theloai_id)
        if not the_loai:
            return False, "Không tìm thấy thể loại!"

        Sach.query.filter(Sach.theloai_id == theloai_id).update(
            {"theloai_id": None}, synchronize_session=False
        )
        db.session.delete(the_loai)
        db.session.commit()
        return True, "Xóa thể loại thành công!"
    except Exception as e:
        db.session.rollback()
        print("LỖI XÓA THỂ LOẠI:", repr(e))
        return False, "Có lỗi xảy ra khi xóa thể loại!"

def get_all_sach():
    return Sach.query.order_by(Sach.id.desc()).all()

def get_sach_by_id(sach_id):
    return Sach.query.get(sach_id)

def them_sach(ten_sach, tac_gia, nha_xuat_ban=None, nam_xuat_ban=None, ngon_ngu="Tiếng Việt",
              so_trang=None, mo_ta=None, anh_bia=None, theloai_id=None, so_luong=0):
    try:
        sach = Sach(
            tenSach=ten_sach, tacGia=tac_gia, nhaXuatBan=nha_xuat_ban,
            namXuatBan=nam_xuat_ban, ngonNgu=ngon_ngu, soTrang=so_trang,
            moTa=mo_ta, anhBia=anh_bia, theloai_id=theloai_id,
            soLuong=so_luong, soLuongConLai=so_luong
        )
        db.session.add(sach)
        db.session.commit()
        return True, "Thêm sách thành công!", sach
    except Exception as e:
        db.session.rollback()
        print("LỖI THÊM SÁCH:", repr(e))
        return False, "Có lỗi xảy ra khi thêm sách!", None

def cap_nhat_sach(sach_id, ten_sach, tac_gia, nha_xuat_ban=None, nam_xuat_ban=None,
                  ngon_ngu=None, so_trang=None, mo_ta=None, anh_bia=None, theloai_id=None, so_luong=None):
    try:
        sach = get_sach_by_id(sach_id)
        if not sach:
            return False, "Không tìm thấy sách!"
        sach.tenSach = ten_sach
        sach.tacGia = tac_gia
        sach.nhaXuatBan = nha_xuat_ban
        sach.namXuatBan = nam_xuat_ban
        sach.ngonNgu = ngon_ngu
        sach.soTrang = so_trang
        sach.moTa = mo_ta
        sach.theloai_id = theloai_id

        if anh_bia:
            sach.anhBia = anh_bia

        if so_luong is not None:
            so_dang_muon = sach.soLuong - sach.soLuongConLai
            if so_luong < so_dang_muon:
                return False, f"Không thể giảm số lượng xuống {so_luong} vì hiện có {so_dang_muon} cuốn đang được mượn!"
            sach.soLuong = so_luong
            sach.soLuongConLai = so_luong - so_dang_muon

        db.session.commit()
        return True, "Cập nhật sách thành công!"
    except Exception as e:
        db.session.rollback()
        print("LỖI CẬP NHẬT SÁCH:", repr(e))
        return False, "Có lỗi xảy ra khi cập nhật sách!"

def xoa_sach(sach_id):
    try:
        sach = get_sach_by_id(sach_id)
        if not sach:
            return False, "Không tìm thấy sách!"
        so_dang_muon = PhieuMuon.query.filter(
            PhieuMuon.sach_id == sach_id,
            PhieuMuon.trangThai.in_([TrangThaiMuon.DA_DUYET, TrangThaiMuon.CHO_GIA_HAN])
        ).count()
        if so_dang_muon > 0:
            return False, "Không thể xóa sách vì hiện đang có độc giả mượn sách này!"
        db.session.delete(sach)
        db.session.commit()
        return True, "Xóa sách thành công!"
    except Exception as e:
        db.session.rollback()
        print("LỖI XÓA SÁCH:", repr(e))
        return False, "Có lỗi xảy ra khi xóa sách!"

def import_sach_tu_excel(danh_sach_sach):
    try:
        so_luong_them = 0
        loi_the_loai = []
        for index, item in enumerate(danh_sach_sach, start=2):
            theloai_id = item.get("theloai_id")
            ten_the_loai = (item.get("ten_the_loai") or "").strip()
            if ten_the_loai:
                the_loai = TheLoai.query.filter(TheLoai.tenTheLoai.ilike(ten_the_loai)).first()
                if not the_loai:
                    loi_the_loai.append(f"Dòng {index}: thể loại '{ten_the_loai}' không tồn tại")
                    continue
                theloai_id = the_loai.id
            elif theloai_id is not None:
                try:
                    theloai_id = int(theloai_id)
                except (TypeError, ValueError):
                    loi_the_loai.append(f"Dòng {index}: ID thể loại không hợp lệ")
                    continue
                if not TheLoai.query.get(theloai_id):
                    loi_the_loai.append(f"Dòng {index}: ID thể loại {theloai_id} không tồn tại")
                    continue
            sach = Sach(
                tenSach=item.get("ten_sach"), tacGia=item.get("tac_gia"),
                nhaXuatBan=item.get("nha_xuat_ban"), namXuatBan=item.get("nam_xuat_ban"),
                ngonNgu=item.get("ngon_ngu") or "Tiếng Việt", soTrang=item.get("so_trang"),
                theloai_id=theloai_id, soLuong=item.get("so_luong") or 0,
                soLuongConLai=item.get("so_luong") or 0, anhBia=item.get("anh_bia"), moTa=item.get("mo_ta")
            )
            db.session.add(sach)
            so_luong_them += 1
        if loi_the_loai:
            db.session.rollback()
            return False, "; ".join(loi_the_loai[:5])
        db.session.commit()
        return True, f"Đã import {so_luong_them} sách thành công!"
    except Exception as e:
        db.session.rollback()
        print("LỖI IMPORT EXCEL:", repr(e))
        return False, "Import Excel thất bại!"

# 4. Tìm kiếm và gợi ý

def tim_kiem_sach(tu_khoa="", theloai_id=None, page=1, page_size=12, sort="moi_nhat"):
    query = Sach.query
    if tu_khoa:
        tu_khoa_like = f"%{tu_khoa.strip()}%"
        query = query.filter(or_(
            Sach.tenSach.ilike(tu_khoa_like),
            Sach.tacGia.ilike(tu_khoa_like),
            Sach.moTa.ilike(tu_khoa_like)
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
    return {
        "total": total, "page": page, "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
        "items": [s.to_dict() for s in query.offset((page - 1) * page_size).limit(page_size).all()]
    }

def get_sach_lien_quan(sach, so_luong=4):
    if not sach.theloai_id:
        return []
    return Sach.query.filter(
        Sach.theloai_id == sach.theloai_id,
        Sach.id != sach.id
    ).order_by(Sach.diemDanhGiaTB.desc()).limit(so_luong).all()

def danh_gia_sach(user_id, sach_id, so_sao):
    try:
        if so_sao < 1 or so_sao > 5: return False, "Số sao phải từ 1 đến 5!"
        sach = get_sach_by_id(sach_id)
        if not sach: return False, "Không tìm thấy sách!"
        danh_gia_cu = DanhGia.query.filter_by(user_id=user_id, sach_id=sach_id).first()
        if danh_gia_cu:
            danh_gia_cu.soSao = so_sao
            danh_gia_cu.ngayTao = datetime.now()
        else:
            danh_gia_moi = DanhGia(user_id=user_id, sach_id=sach_id, soSao=so_sao)
            db.session.add(danh_gia_moi)
        db.session.flush()
        danh_sach = DanhGia.query.filter_by(sach_id=sach_id).all()
        sach.soLuotDanhGia = len(danh_sach)
        sach.diemDanhGiaTB = sum(d.soSao for d in danh_sach) / sach.soLuotDanhGia if sach.soLuotDanhGia > 0 else 0

        db.session.commit()
        return True, "Đánh giá sách thành công!"
    except Exception as e:
        db.session.rollback()
        print("LỖI ĐÁNH GIÁ:", e)
        return False, "Có lỗi xảy ra khi đánh giá!"

def them_binh_luan(user_id, sach_id, noi_dung):
    try:
        if not noi_dung or not noi_dung.strip(): return False, "Nội dung bình luận không được để trống!", None
        if not get_sach_by_id(sach_id): return False, "Không tìm thấy sách!", None

        binh_luan = BinhLuan(user_id=user_id, sach_id=sach_id, noiDung=noi_dung.strip())
        db.session.add(binh_luan)
        db.session.commit()
        return True, "Bình luận thành công!", binh_luan
    except Exception as e:
        db.session.rollback()
        print("LỖI BÌNH LUẬN:", e)
        return False, "Có lỗi xảy ra khi bình luận!", None

def get_binh_luan_sach(sach_id):
    return BinhLuan.query.filter_by(sach_id=sach_id).order_by(BinhLuan.ngayTao.desc()).all()

def xoa_binh_luan(user_id, binh_luan_id):
    try:
        binh_luan = BinhLuan.query.get(binh_luan_id)
        if not binh_luan: return False, "Không tìm thấy bình luận!"
        if binh_luan.user_id != user_id: return False, "Bạn không có quyền xóa bình luận này!"
        db.session.delete(binh_luan)
        db.session.commit()
        return True, "Đã xóa bình luận!"
    except Exception as e:
        db.session.rollback()
        print("LỖI XÓA BÌNH LUẬN:", e)
        return False, "Có lỗi xảy ra khi xóa bình luận!"

def luu_lich_su_xem(user_id, sach_id):
    try:
        lich_su = LichSuXem(user_id=user_id, sach_id=sach_id)
        db.session.add(lich_su)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print("LỖI LƯU LỊCH SỬ XEM:", repr(e))
        return False

def toggle_yeu_thich(user_id, sach_id):
    yeu_thich = YeuThich.query.filter_by(user_id=user_id, sach_id=sach_id).first()
    if yeu_thich:
        db.session.delete(yeu_thich)
        db.session.commit()
        return False, "Đã xóa khỏi danh sách yêu thích!"
    yeu_thich = YeuThich(user_id=user_id, sach_id=sach_id)
    db.session.add(yeu_thich)
    db.session.commit()
    return True, "Đã thêm vào danh sách yêu thích!"

def get_danh_sach_yeu_thich(user_id):
    danh_sach = YeuThich.query.filter_by(user_id=user_id).order_by(YeuThich.ngay_tao.desc()).all()
    return [item.sach for item in danh_sach if item.sach]

# 5. Mượn sascv và trả sách

def dang_ky_muon_sach(user_id, sach_id):
    try:
        sach = get_sach_by_id(sach_id)
        if not sach: return False, "Không tìm thấy sách!"
        if sach.soLuongConLai <= 0: return False, "Sách hiện đã hết!"

        so_sach_dang_muon = PhieuMuon.query.filter(
            PhieuMuon.user_id == user_id,
            PhieuMuon.trangThai.in_([TrangThaiMuon.DA_DUYET, TrangThaiMuon.CHO_DUYET])
        ).count()
        if so_sach_dang_muon >= 5: return False, "Bạn đã đạt giới hạn tối đa 5 cuốn sách được mượn!"

        if PhieuMuon.query.filter_by(user_id=user_id, sach_id=sach_id, trangThai=TrangThaiMuon.CHO_DUYET).first():
            return False, "Bạn đã đăng ký mượn sách này và đang chờ duyệt!"

        if PhieuMuon.query.filter_by(user_id=user_id, sach_id=sach_id, trangThai=TrangThaiMuon.DA_DUYET).first():
            return False, "Bạn đang mượn sách này!"

        phieu = PhieuMuon(user_id=user_id, sach_id=sach_id, trangThai=TrangThaiMuon.CHO_DUYET)
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
        if not phieu: return False, "Không tìm thấy phiếu mượn!"
        if phieu.user_id != user_id: return False, "Bạn không có quyền gia hạn phiếu mượn này!"
        if phieu.trangThai != TrangThaiMuon.DA_DUYET: return False, "Chỉ sách đang được mượn mới có thể yêu cầu gia hạn!"
        if not phieu.hanTra: return False, "Phiếu mượn chưa có hạn trả!"

        phieu.trangThai = TrangThaiMuon.CHO_GIA_HAN
        db.session.commit()
        return True, "Đã gửi yêu cầu gia hạn!"
    except Exception as e:
        db.session.rollback()
        print("LỖI GIA HẠN:", repr(e))
        return False, "Có lỗi xảy ra khi gửi yêu cầu gia hạn!"

def get_phieu_muon_dang_muon_cua_doc_gia(user_id):
    now = datetime.now()
    return PhieuMuon.query.filter(
        PhieuMuon.user_id == user_id,
        PhieuMuon.trangThai.in_([TrangThaiMuon.DA_DUYET, TrangThaiMuon.CHO_GIA_HAN]),
        (PhieuMuon.hanTra.is_(None)) | (PhieuMuon.hanTra >= now)
    ).order_by(PhieuMuon.hanTra.asc()).all()

def get_phieu_muon_da_tra_cua_doc_gia(user_id):
    return PhieuMuon.query.filter(
        PhieuMuon.user_id == user_id,
        PhieuMuon.trangThai == TrangThaiMuon.DA_TRA
    ).order_by(PhieuMuon.ngayDangKy.desc()).all()

def get_phieu_muon_qua_han_cua_doc_gia(user_id):
    now = datetime.now()
    return PhieuMuon.query.filter(
        PhieuMuon.user_id == user_id,
        PhieuMuon.trangThai.in_([TrangThaiMuon.DA_DUYET, TrangThaiMuon.CHO_GIA_HAN]),
        PhieuMuon.hanTra.isnot(None),
        PhieuMuon.hanTra < now
    ).order_by(PhieuMuon.hanTra.asc()).all()

def tra_sach(user_id, phieu_muon_id):
    try:
        phieu = PhieuMuon.query.get(phieu_muon_id)
        if not phieu: return False, "Không tìm thấy phiếu mượn!"
        if phieu.user_id != user_id: return False, "Bạn không có quyền trả phiếu mượn này!"
        if phieu.trangThai != TrangThaiMuon.DA_DUYET: return False, "Sách này không ở trạng thái đang mượn!"

        sach = get_sach_by_id(phieu.sach_id)
        if not sach: return False, "Không tìm thấy sách!"
        phieu.trangThai = TrangThaiMuon.DA_TRA
        sach.soLuongConLai += 1
        db.session.commit()
        return True, "Trả sách thành công!"
    except Exception as e:
        db.session.rollback()
        print("LỖI TRẢ SÁCH:", repr(e))
        return False, "Có lỗi xảy ra khi trả sách!"

def get_lich_su_muon_cua_doc_gia(user_id):
    return PhieuMuon.query.filter_by(user_id=user_id).order_by(PhieuMuon.ngayDangKy.desc()).all()

def get_phieu_muon_cho_duyet():
    return PhieuMuon.query.filter_by(trangThai=TrangThaiMuon.CHO_DUYET).order_by(PhieuMuon.ngayDangKy.desc()).all()

def get_phieu_muon_cho_gia_han():
    return PhieuMuon.query.filter_by(trangThai=TrangThaiMuon.CHO_GIA_HAN).order_by(PhieuMuon.ngayDangKy.desc()).all()

def get_phieu_muon_dang_muon():
    return PhieuMuon.query.filter_by(trangThai=TrangThaiMuon.DA_DUYET).order_by(PhieuMuon.ngayMuon.desc()).all()

def duyet_phieu_muon(phieu_id):
    try:
        phieu = PhieuMuon.query.get(phieu_id)
        if not phieu: return False, "Không tìm thấy yêu cầu mượn!"
        if phieu.trangThai != TrangThaiMuon.CHO_DUYET: return False, "Yêu cầu này không còn ở trạng thái chờ duyệt!"

        sach = get_sach_by_id(phieu.sach_id)
        if not sach: return False, "Không tìm thấy sách!"
        if sach.soLuongConLai <= 0: return False, "Sách đã hết!"

        so_sach_dang_muon = PhieuMuon.query.filter_by(user_id=phieu.user_id, trangThai=TrangThaiMuon.DA_DUYET).count()
        if so_sach_dang_muon >= 5: return False, "Độc giả đã đạt giới hạn tối đa 5 cuốn đang mượn!"

        phieu.trangThai = TrangThaiMuon.DA_DUYET
        phieu.ngayDuyet = datetime.now()
        phieu.ngayMuon = datetime.now()
        phieu.hanTra = datetime.now() + timedelta(days=7)
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
        if not phieu: return False, "Không tìm thấy yêu cầu mượn!"
        if phieu.trangThai != TrangThaiMuon.CHO_DUYET: return False, "Yêu cầu này không còn ở trạng thái chờ duyệt!"

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
        if not phieu: return False, "Không tìm thấy yêu cầu gia hạn!"
        if phieu.trangThai != TrangThaiMuon.CHO_GIA_HAN: return False, "Yêu cầu này không ở trạng thái chờ gia hạn!"
        if not phieu.hanTra: return False, "Phiếu mượn chưa có hạn trả!"

        phieu.hanTra = phieu.hanTra + timedelta(days=7)
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
        if not phieu: return False, "Không tìm thấy yêu cầu gia hạn!"
        if phieu.trangThai != TrangThaiMuon.CHO_GIA_HAN: return False, "Yêu cầu này không ở trạng thái chờ gia hạn!"

        phieu.trangThai = TrangThaiMuon.DA_DUYET
        db.session.commit()
        return True, "Đã từ chối yêu cầu gia hạn!"
    except Exception as e:
        db.session.rollback()
        print("LỖI TỪ CHỐI GIA HẠN:", repr(e))
        return False, "Có lỗi xảy ra khi từ chối gia hạn!"

def huy_phieu_qua_han(phieu_id):
    try:
        phieu = PhieuMuon.query.get(phieu_id)
        if not phieu: return False, "Không tìm thấy yêu cầu mượn!"
        if phieu.trangThai != TrangThaiMuon.DA_DUYET: return False, "Yêu cầu này không ở trạng thái chờ nhận sách!"
        if not phieu.ngayDuyet: return False, "Phiếu chưa có ngày duyệt!"

        if datetime.now() <= phieu.ngayDuyet + timedelta(days=2):
            return False, "Yêu cầu này chưa quá hạn nhận sách!"

        phieu.trangThai = TrangThaiMuon.DA_HUY
        db.session.commit()
        return True, "Đã hủy yêu cầu mượn quá hạn nhận sách!"
    except Exception as e:
        db.session.rollback()
        print("LỖI HỦY PHIẾU QUÁ HẠN:", repr(e))
        return False, "Có lỗi xảy ra khi hủy yêu cầu!"

# 6. tích hợp AI

def tim_kiem_ngu_nghia(query, limit=20):
    if not query or not query.strip(): return []
    query = query.strip().lower()  # Chuẩn hóa từ khóa

    danh_sach_sach = Sach.query.all()
    if not danh_sach_sach: return []

    danh_sach_text = []
    for sach in danh_sach_sach:
        the_loai = TheLoai.query.get(sach.theloai_id).tenTheLoai if sach.theloai_id else ""

        text = f"Cuốn sách {sach.tenSach or ''} của tác giả {sach.tacGia or ''} thuộc thể loại {the_loai}. Nội dung xoay quanh: {sach.moTa or ''}"
        danh_sach_text.append(text.lower())

    model = get_model_semantic()

    query_embedding = model.encode(query, convert_to_numpy=True)
    sach_embeddings = model.encode(danh_sach_text, convert_to_numpy=True)

    query_norm = np.linalg.norm(query_embedding)
    sach_norms = np.linalg.norm(sach_embeddings, axis=1)
    scores = np.dot(sach_embeddings, query_embedding) / (sach_norms * query_norm + 1e-10)

    ket_qua = list(zip(danh_sach_sach, scores))
    ket_qua.sort(key=lambda x: x[1], reverse=True)

    sach_phu_hop = []
    nguong_toi_thieu = 0.25

    for sach, score in ket_qua:
        if float(score) >= nguong_toi_thieu:
            sach_phu_hop.append(sach)

        if len(sach_phu_hop) >= limit:
            break
    return sach_phu_hop

def get_sach_goi_y(user_id, limit=8):
    sach_da_xem = {item.sach_id for item in LichSuXem.query.filter_by(user_id=user_id).all()}
    sach_da_muon = {item.sach_id for item in PhieuMuon.query.filter_by(user_id=user_id).all()}
    sach_da_biet = sach_da_xem.union(sach_da_muon)

    theloai_ids = set()
    for sach_id in sach_da_biet:
        sach = Sach.query.get(sach_id)
        if sach and sach.theloai_id:
            theloai_ids.add(sach.theloai_id)

    if not theloai_ids:
        return Sach.query.filter(Sach.soLuongConLai > 0).order_by(
            Sach.diemDanhGiaTB.desc(), Sach.soLuotDanhGia.desc()
        ).limit(limit).all()

    return Sach.query.filter(
        Sach.theloai_id.in_(theloai_ids),
        Sach.id.notin_(sach_da_biet),
        Sach.soLuongConLai > 0
    ).order_by(Sach.diemDanhGiaTB.desc(), Sach.soLuotDanhGia.desc()).limit(limit).all()

def du_doan_nhu_cau_muon_sach():
    danh_sach_phieu = PhieuMuon.query.filter(
        PhieuMuon.trangThai.in_([TrangThaiMuon.DA_DUYET, TrangThaiMuon.DA_TRA]),
        PhieuMuon.ngayMuon.isnot(None)
    ).all()

    if not danh_sach_phieu: return []

    du_lieu_sach = defaultdict(lambda: defaultdict(int))
    for phieu in danh_sach_phieu:
        thang = phieu.ngayMuon.strftime("%Y-%m")
        du_lieu_sach[phieu.sach_id][thang] += 1

    ket_qua = []
    for sach_id, du_lieu_thang in du_lieu_sach.items():
        sach = Sach.query.get(sach_id)
        if not sach: continue

        danh_sach_thang = sorted(du_lieu_thang.items())
        X = [[index] for index, _ in enumerate(danh_sach_thang)]
        y = [so_luot for _, so_luot in danh_sach_thang]

        du_doan = 0
        xu_huong = "Ổn định"

        if len(X) >= 2:
            model = LinearRegression()
            model.fit(X, y)
            du_doan = max(0, round(float(model.predict([[len(X)]])[0])))
            he_so = model.coef_[0]
            if he_so > 0.5:
                xu_huong = "Tăng"
            elif he_so < -0.5:
                xu_huong = "Giảm"
        else:
            du_doan = y[0]

        tong_luot_muon = sum(y)

        if du_doan > sach.soLuongConLai and du_doan >= 3:
            de_xuat, muc_do = "Nên nhập thêm", "Cao"
        elif du_doan >= 3:
            de_xuat, muc_do = "Theo dõi nhu cầu", "Trung bình"
        else:
            de_xuat, muc_do = "Chưa cần nhập thêm", "Thấp"

        ket_qua.append({
            "sach": sach, "tong_luot_muon": tong_luot_muon,
            "du_doan": du_doan, "xu_huong": xu_huong,
            "muc_do": muc_do, "de_xuat": de_xuat
        })

    ket_qua.sort(key=lambda x: x["du_doan"], reverse=True)
    return ket_qua