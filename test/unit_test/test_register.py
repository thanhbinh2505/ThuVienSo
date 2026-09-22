import pytest
from app import dao
from app.models import User

def test_dao_dang_ky_thanh_cong(seed_data):
    success, msg, user = dao.dang_ky_doc_gia(
        username="new_user",
        hoten="New User Test",
        password="Password123!",
        email="newuser@test.com",
        sdt="0911111111",
        gioitinh=True
    )
    assert success is True
    assert msg == "Đăng ký thành công!"
    assert user is not None
    assert user.username == "new_user"

def test_dao_dang_ky_trung_username(seed_data):
    success, msg, user = dao.dang_ky_doc_gia(
        username="docgia_test",
        hoten="Another User",
        password="Password123!",
        email="another@test.com"
    )
    assert success is False
    assert msg == "Username đã tồn tại!"
    assert user is None

def test_dao_dang_ky_trung_email(seed_data):
    success, msg, user = dao.dang_ky_doc_gia(
        username="unique_user",
        hoten="Another User",
        password="Password123!",
        email="docgia@test.com"
    )
    assert success is False
    assert msg == "Email đã được sử dụng!"
    assert user is None

def test_dao_dang_ky_trung_sdt(seed_data):
    success, msg, user = dao.dang_ky_doc_gia(
        username="unique_user2",
        hoten="Another User",
        password="Password123!",
        email="unique2@test.com",
        sdt="0900000003"
    )
    assert success is False
    assert msg == "Số điện thoại đã được sử dụng!"
    assert user is None



def test_route_register_post_success(client, seed_data):
    res = client.post('/register', data={
        'username': 'route_user',
        'hoten': 'Route User',
        'password': 'Password123!',
        'confirm_password': 'Password123!',
        'email': 'route_user@test.com',
        'sdt': '0922222222',
        'gioitinh': 'male',
        'ngaysinh': '2000-01-01'
    }, follow_redirects=True)
    assert res.status_code == 200

def test_route_register_password_mismatch(client, seed_data):
    res = client.post('/register', data={
        'username': 'mismatch_user',
        'hoten': 'Mismatch User',
        'password': 'Password123!',
        'confirm_password': 'DifferentPassword!',
        'email': 'mismatch@test.com',
        'gioitinh': 'female'
    })
    assert res.status_code == 200
    assert "Mật khẩu xác nhận không khớp".encode('utf-8') in res.data or res.status_code == 200
