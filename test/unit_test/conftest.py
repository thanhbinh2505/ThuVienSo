import pytest
from app import app as flask_app, db
import app.index  # Register all routes and blueprints
from app.models import User, UserRole, OAuthProvider, TheLoai, Sach

@pytest.fixture(scope='function')
def app():
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False
    })
    try:
        db.engine.dispose()
    except Exception:
        pass

    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='function')
def client(app):
    return app.test_client()

@pytest.fixture(scope='function')
def seed_data(app):
    admin = User.query.filter_by(username="admin_test").first()
    if not admin:
        admin = User(
            username="admin_test",
            hoTen="Quản trị viên Test",
            email="admin@test.com",
            soDienThoai="0900000001",
            role=UserRole.ADMIN,
            active=True
        )
        admin.set_password("Password123!")
        db.session.add(admin)

    thuthu = User.query.filter_by(username="thuthu_test").first()
    if not thuthu:
        thuthu = User(
            username="thuthu_test",
            hoTen="Thủ thư Test",
            email="thuthu@test.com",
            soDienThoai="0900000002",
            role=UserRole.THUTHU,
            active=True
        )
        thuthu.set_password("Password123!")
        db.session.add(thuthu)

    docgia = User.query.filter_by(username="docgia_test").first()
    if not docgia:
        docgia = User(
            username="docgia_test",
            hoTen="Độc Giả Test",
            email="docgia@test.com",
            soDienThoai="0900000003",
            role=UserRole.DOCGIA,
            active=True
        )
        docgia.set_password("Password123!")
        db.session.add(docgia)

    docgia_locked = User.query.filter_by(username="docgia_locked").first()
    if not docgia_locked:
        docgia_locked = User(
            username="docgia_locked",
            hoTen="Độc Giả Bị Khóa",
            email="locked@test.com",
            soDienThoai="0900000004",
            role=UserRole.DOCGIA,
            active=False
        )
        docgia_locked.set_password("Password123!")
        db.session.add(docgia_locked)

    tl1 = TheLoai.query.filter_by(tenTheLoai="Văn học").first()
    if not tl1:
        tl1 = TheLoai(tenTheLoai="Văn học", moTa="Thể loại văn học")
        db.session.add(tl1)

    tl2 = TheLoai.query.filter_by(tenTheLoai="Khoa học").first()
    if not tl2:
        tl2 = TheLoai(tenTheLoai="Khoa học", moTa="Khoa học")
        db.session.add(tl2)

    db.session.commit()

    sach1 = Sach.query.filter_by(tenSach="Dế Mèn Phiêu Lưu Ký").first()
    if not sach1:
        sach1 = Sach(
            tenSach="Dế Mèn Phiêu Lưu Ký",
            tacGia="Tô Hoài",
            theloai_id=tl1.id,
            soLuong=10,
            soLuongConLai=10,
            namXuatBan=2020,
            nhaXuatBan="NXB Kim Đồng"
        )
        db.session.add(sach1)

    sach2 = Sach.query.filter_by(tenSach="Vũ Trụ Trong Vỏ Hạt Dẻ").first()
    if not sach2:
        sach2 = Sach(
            tenSach="Vũ Trụ Trong Vỏ Hạt Dẻ",
            tacGia="Stephen Hawking",
            theloai_id=tl2.id,
            soLuong=5,
            soLuongConLai=0,
            namXuatBan=2018,
            nhaXuatBan="NXB Trẻ"
        )
        db.session.add(sach2)

    sach3 = Sach.query.filter_by(tenSach="Số Đỏ").first()
    if not sach3:
        sach3 = Sach(
            tenSach="Số Đỏ",
            tacGia="Vũ Trọng Phụng",
            theloai_id=tl1.id,
            soLuong=8,
            soLuongConLai=8,
            namXuatBan=2019,
            nhaXuatBan="NXB Văn Học"
        )
        db.session.add(sach3)

    db.session.commit()

    return {
        'admin': admin,
        'thuthu': thuthu,
        'docgia': docgia,
        'docgia_locked': docgia_locked,
        'tl1': tl1,
        'tl2': tl2,
        'sach1': sach1,
        'sach2': sach2,
        'sach3': sach3
    }
