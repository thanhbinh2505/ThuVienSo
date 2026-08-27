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
    password = Column(String(255), nullable=True)

    role = Column(Enum(UserRole), nullable=False, default=UserRole.DOCGIA)

    oauthProvider = Column(Enum(OAuthProvider), default=OAuthProvider.NONE, nullable=False)
    oauthId = Column(String(191), nullable=True)
    avatar = Column(String(255), nullable=True)

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


if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()

        import random

        print("Đang tạo dữ liệu mẫu cho Thư Viện Số...")
        ten_the_loai_list = [
            "Văn học", "Kỹ năng sống", "Khoa học", "Kinh tế",
            "Thiếu nhi", "Lịch sử", "Trinh thám", "Công nghệ thông tin"
        ]
        danh_sach_theloai = []
        for ten in ten_the_loai_list:
            tl = TheLoai(tenTheLoai=ten)
            db.session.add(tl)
            danh_sach_theloai.append(tl)
        db.session.flush()

        admin = User(username="admin", hoTen="Quản trị viên", email="admin@thuvienso.vn",
                     gioiTinh=True, role=UserRole.ADMIN)
        admin.set_password("Admin@123")
        db.session.add(admin)

        thuthu = User(username="thuthu", hoTen="Thủ thư Minh Anh", email="thuthu@thuvienso.vn",
                      soDienThoai="0900000001", gioiTinh=False, role=UserRole.THUTHU)
        thuthu.set_password("ThuThu@123")
        db.session.add(thuthu)

        for i in range(1, 6):
            dg = User(username=f"docgia_{i}", hoTen=f"Độc Giả {i}",
                      email=f"docgia{i}@gmail.com", soDienThoai=f"09010000{i}",
                      gioiTinh=random.choice([True, False]), role=UserRole.DOCGIA)
            dg.set_password("123456Aa@")
            db.session.add(dg)

        db.session.flush()
        sach_mau = [
            ("Nhà Giả Kim", "Paulo Coelho", "Văn học"),
            ("Đắc Nhân Tâm", "Dale Carnegie", "Kỹ năng sống"),
            ("Tuổi Trẻ Đáng Giá Bao Nhiêu", "Rosie Nguyễn", "Kỹ năng sống"),
            ("Lược Sử Thời Gian", "Stephen Hawking", "Khoa học"),
            ("Sapiens: Lược Sử Loài Người", "Yuval Noah Harari", "Lịch sử"),
            ("Cha Giàu Cha Nghèo", "Robert Kiyosaki", "Kinh tế"),
            ("Doraemon - Tập 1", "Fujiko F. Fujio", "Thiếu nhi"),
            ("Sherlock Holmes Toàn Tập", "Arthur Conan Doyle", "Trinh thám"),
            ("Clean Code", "Robert C. Martin", "Công nghệ thông tin"),
            ("Dế Mèn Phiêu Lưu Ký", "Tô Hoài", "Văn học"),
            ("Nhà Kinh Tế Học Tài Ba", "Adam Smith", "Kinh tế"),
            ("Trí Tuệ Nhân Tạo", "Stuart Russell", "Công nghệ thông tin"),
        ]

        theloai_map = {tl.tenTheLoai: tl.id for tl in danh_sach_theloai}

        for ten_sach, tac_gia, ten_tl in sach_mau:
            so_luong = random.randint(3, 15)
            sach = Sach(
                tenSach=ten_sach,
                tacGia=tac_gia,
                nhaXuatBan=random.choice(["NXB Trẻ", "NXB Kim Đồng", "NXB Lao Động", "NXB Tổng Hợp TPHCM"]),
                namXuatBan=random.randint(1995, 2024),
                soTrang=random.randint(150, 500),
                moTa=f"'{ten_sach}' là một tác phẩm nổi bật của {tac_gia}, "
                     f"mang đến cho độc giả nhiều góc nhìn sâu sắc và giá trị.",
                theloai_id=theloai_map.get(ten_tl),
                soLuong=so_luong,
                soLuongConLai=random.randint(0, so_luong),
                diemDanhGiaTB=round(random.uniform(3.0, 5.0), 1)
            )
            db.session.add(sach)

        try:
            db.session.commit()
            print("Đã tạo dữ liệu mẫu thành công!")
        except Exception as e:
            db.session.rollback()
            print(f"Có lỗi xảy ra: {e}")