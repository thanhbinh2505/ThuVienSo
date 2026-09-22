from datetime import datetime
from enum import Enum as RoleEnum

from flask_login import UserMixin
from sqlalchemy import (Boolean, Column, Date, DateTime, Enum, Float,
                         ForeignKey, Integer, String, Text)
from sqlalchemy.orm import relationship
from werkzeug.security import check_password_hash, generate_password_hash

from app import app, db


class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)


class UserRole(RoleEnum):
    ADMIN = 1
    THUTHU = 2
    DOCGIA = 3


class OAuthProvider(RoleEnum):
    NONE = 0
    GOOGLE = 1
    FACEBOOK = 2


class User(UserMixin, BaseModel):
    __tablename__ = 'user'

    username = Column(String(50), unique=True, nullable=True)
    hoTen = Column(String(100), nullable=False)

    email = Column(String(100), unique=True, nullable=True)
    soDienThoai = Column(String(15), unique=True, nullable=True)

    gioiTinh = Column(Boolean, nullable=True)
    ngaySinh = Column(Date, nullable=True)
    password = Column(String(255), nullable=True)

    role = Column(Enum(UserRole), nullable=False, default=UserRole.DOCGIA)

    oauthProvider = Column(Enum(OAuthProvider), default=OAuthProvider.NONE, nullable=False)
    oauthId = Column(String(191), nullable=True)
    avatar = Column(String(500), nullable=True)

    ngayTao = Column(DateTime, default=datetime.now)
    active = Column(Boolean, default=True)

    def __str__(self):
        return self.username or self.email or self.soDienThoai

    def get_id(self):
        return str(self.id)

    def set_password(self, password: str):
        self.password = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password:
            return False
        return check_password_hash(self.password, password)


class TheLoai(BaseModel):
    __tablename__ = 'theloai'

    tenTheLoai = Column(String(100), unique=True, nullable=False)
    moTa = Column(String(255), nullable=True)

    danh_sach_sach = relationship('Sach', backref='the_loai', lazy=True)

    def to_dict(self):
        return {"id": self.id, "tenTheLoai": self.tenTheLoai}


class Sach(BaseModel):
    __tablename__ = 'sach'

    tenSach = Column(String(255), nullable=False)
    tacGia = Column(String(150), nullable=False)
    nhaXuatBan = Column(String(150), nullable=True)
    namXuatBan = Column(Integer, nullable=True)
    ngonNgu = Column(String(50), nullable=True, default="Tiếng Việt")
    soTrang = Column(Integer, nullable=True)

    moTa = Column(Text, nullable=True)
    anhBia = Column(String(500), nullable=True,
                    default="/static/image/default.png")

    theloai_id = Column(Integer, ForeignKey('theloai.id'), nullable=True)

    soLuong = Column(Integer, nullable=False, default=0)
    soLuongConLai = Column(Integer, nullable=False, default=0)

    diemDanhGiaTB = Column(Float, nullable=False, default=0)
    soLuotDanhGia = Column(Integer, nullable=False, default=0)
    ngayTao = Column(DateTime, default=datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "tenSach": self.tenSach,
            "tacGia": self.tacGia,
            "anhBia": self.anhBia,
            "theLoai": self.the_loai.tenTheLoai if self.the_loai else None,
            "theloai_id": self.theloai_id,
            "soLuongConLai": self.soLuongConLai,
            "diemDanhGiaTB": round(self.diemDanhGiaTB or 0, 1),
            "soLuotDanhGia": self.soLuotDanhGia or 0,
            "namXuatBan": self.namXuatBan,
        }

    def to_dict_chi_tiet(self):
        return {
            "id": self.id,
            "tenSach": self.tenSach,
            "tacGia": self.tacGia,
            "nhaXuatBan": self.nhaXuatBan,
            "namXuatBan": self.namXuatBan,
            "ngonNgu": self.ngonNgu,
            "soTrang": self.soTrang,
            "moTa": self.moTa,
            "anhBia": self.anhBia,
            "theLoai": self.the_loai.tenTheLoai if self.the_loai else None,
            "theloai_id": self.theloai_id,
            "soLuong": self.soLuong,
            "soLuongConLai": self.soLuongConLai,
            "diemDanhGiaTB": round(self.diemDanhGiaTB or 0, 1),
            "trangThai": "Còn sách" if self.soLuongConLai > 0 else "Hết sách",
        }

class DanhGia(BaseModel):
    __tablename__ = 'danhgia'

    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    sach_id = Column(Integer, ForeignKey('sach.id'), nullable=False)

    soSao = Column(Integer, nullable=False)
    ngayTao = Column(DateTime, default=datetime.now)

    user = relationship('User', backref='danh_sach_danh_gia')
    sach = relationship('Sach', backref='danh_sach_danh_gia')

class BinhLuan(BaseModel):
    __tablename__ = 'binhluan'

    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    sach_id = Column(Integer, ForeignKey('sach.id'), nullable=False)

    noiDung = Column(Text, nullable=False)
    ngayTao = Column(DateTime, default=datetime.now)

    user = relationship('User', backref='danh_sach_binh_luan')
    sach = relationship('Sach', backref='danh_sach_binh_luan')

class TrangThaiMuon(str, RoleEnum):
    CHO_DUYET = "CHO_DUYET"
    DA_DUYET = "DA_DUYET"
    DA_NHAN = "DA_NHAN"
    TU_CHOI = "TU_CHOI"
    DA_TRA = "DA_TRA"
    DA_HUY = "DA_HUY"
    CHO_GIA_HAN = "CHO_GIA_HAN"


class PhieuMuon(BaseModel):
    __tablename__ = 'phieumuon'

    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    sach_id = Column(Integer, ForeignKey('sach.id'), nullable=False)

    ngayDangKy = Column(DateTime, default=datetime.now)
    ngayDuyet = Column(DateTime, nullable=True)
    ngayMuon = Column(DateTime, nullable=True)
    hanTra = Column(DateTime, nullable=True)

    trangThai = Column(
        Enum(TrangThaiMuon),
        nullable=False,
        default=TrangThaiMuon.CHO_DUYET
    )

    user = relationship('User', backref='danh_sach_phieu_muon')
    sach = relationship('Sach', backref='danh_sach_phieu_muon')

class LichSuXem(BaseModel):
    __tablename__ = 'lichsuxem'

    user_id = Column(
        Integer,
        ForeignKey('user.id'),
        nullable=False
    )

    sach_id = Column(
        Integer,
        ForeignKey('sach.id'),
        nullable=False
    )

    ngayXem = Column(
        DateTime,
        default=datetime.now
    )

    user = relationship(
        'User',
        backref='danh_sach_lich_su_xem'
    )

    sach = relationship(
        'Sach',
        backref='danh_sach_nguoi_da_xem'
    )
class YeuThich(db.Model):
    __tablename__ = 'yeu_thich'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )

    sach_id = db.Column(
        db.Integer,
        db.ForeignKey('sach.id'),
        nullable=False
    )

    ngay_tao = db.Column(
        db.DateTime,
        default=datetime.now
    )

    user = db.relationship(
        'User',
        backref='danh_sach_yeu_thich'
    )

    sach = db.relationship(
        'Sach',
        backref='duoc_yeu_thich'
    )

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        the_loai_data = [
            ("Văn học", "Tiểu thuyết và các tác phẩm văn học nổi tiếng trong và ngoài nước."),
            ("Kỹ năng sống", "Sách phát triển bản thân, thói quen và kỹ năng trong cuộc sống."),
            ("Khoa học", "Sách về khoa học tự nhiên, vũ trụ, sinh học và y học."),
            ("Kinh tế", "Sách về kinh tế, tài chính, đầu tư và quản trị."),
            ("Thiếu nhi", "Sách và truyện dành cho trẻ em và thanh thiếu niên."),
            ("Lịch sử", "Sách nghiên cứu lịch sử, văn minh và các sự kiện thế giới."),
            ("Trinh thám", "Tiểu thuyết trinh thám, bí ẩn và điều tra tội phạm."),
            ("Công nghệ thông tin", "Sách về lập trình, thuật toán và kỹ thuật phần mềm")
        ]

        for ten, mo_ta in the_loai_data:
            tl = TheLoai(tenTheLoai=ten, moTa=mo_ta)
            db.session.add(tl)

        # 2. Tạo 3 tài khoản mẫu (Admin, Thủ thư, Độc giả)
        admin = User(
            username="admin",
            hoTen="Quản trị viên",
            email="admin@thuvienso.vn",
            gioiTinh=True,
            role=UserRole.ADMIN
        )
        admin.set_password("Admin@123")
        db.session.add(admin)

        thuthu = User(
            username="thuthu",
            hoTen="Thủ thư Minh Anh",
            email="thuthu@thuvienso.vn",
            soDienThoai="0900000001",
            gioiTinh=False,
            role=UserRole.THUTHU
        )
        thuthu.set_password("ThuThu@123")
        db.session.add(thuthu)

        try:
            db.session.commit()
            print("Khởi tạo dữ liệu thành công!")
        except Exception as e:
            db.session.rollback()
            print(f"Có lỗi xảy ra: {e}")