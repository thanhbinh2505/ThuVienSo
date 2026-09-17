import threading
import socket
import pytest
from app import app as flask_app, db
import app.index  # Register routes
from app.models import User, UserRole, TheLoai, Sach
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

@pytest.fixture(scope='session')
def live_server():
    port = find_free_port()
    flask_app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False
    })

    with flask_app.app_context():
        db.create_all()

        docgia_sel = User.query.filter_by(username="docgia_selenium").first()
        if not docgia_sel:
            docgia_sel = User(
                username="docgia_selenium",
                hoTen="Độc Giả Selenium",
                email="docgia_sel@test.com",
                soDienThoai="0999888777",
                role=UserRole.DOCGIA,
                active=True
            )
            docgia_sel.set_password("Password123!")
            db.session.add(docgia_sel)

        thuthu_sel = User.query.filter_by(username="thuthu_selenium").first()
        if not thuthu_sel:
            thuthu_sel = User(
                username="thuthu_selenium",
                hoTen="Thủ Thư Selenium",
                email="thuthu_sel@test.com",
                soDienThoai="0999888666",
                role=UserRole.THUTHU,
                active=True
            )
            thuthu_sel.set_password("Password123!")
            db.session.add(thuthu_sel)

        tl1 = TheLoai.query.filter_by(tenTheLoai="Văn học").first()
        if not tl1:
            tl1 = TheLoai(tenTheLoai="Văn học", moTa="Văn học")
            db.session.add(tl1)

        tl2 = TheLoai.query.filter_by(tenTheLoai="Khoa học").first()
        if not tl2:
            tl2 = TheLoai(tenTheLoai="Khoa học", moTa="Khoa học")
            db.session.add(tl2)

        db.session.commit()

        sach1 = Sach.query.filter_by(tenSach="Dế Mèn Phiêu Lưu Ký").first()
        if not sach1:
            sach1 = Sach(
                id=1,
                tenSach="Dế Mèn Phiêu Lưu Ký",
                tacGia="Tô Hoài",
                theloai_id=tl1.id,
                soLuong=10,
                soLuongConLai=10,
                namXuatBan=2020,
                nhaXuatBan="NXB Kim Đồng"
            )
            db.session.add(sach1)
            db.session.commit()

    server_thread = threading.Thread(
        target=lambda: flask_app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False),
        daemon=True
    )
    server_thread.start()

    url = f"http://127.0.0.1:{port}"
    yield url

@pytest.fixture(scope='function')
def driver():
    chrome_options = Options()
    # Bỏ comment dòng dưới nếu muốn chạy ngầm:
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--start-maximized')

    driver_instance = webdriver.Chrome(options=chrome_options)
    yield driver_instance
    
    # ⏱️ THỜI GIAN XEM CHROME (đơn vị: giây)
    import time
    time.sleep(5)  # Dừng 5 giây sau mỗi test case để quan sát giao diện
    
    driver_instance.quit()
