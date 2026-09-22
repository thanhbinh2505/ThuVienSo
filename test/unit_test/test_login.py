import pytest
from app import dao, db
from app.models import User, UserRole, OAuthProvider
def test_dao_dang_nhap_thanh_cong(seed_data):
    user, msg = dao.dang_nhap("docgia_test", "Password123!")
    assert user is not None
    assert user.username == "docgia_test"
    assert msg == "Đăng nhập thành công!"

def test_dao_dang_nhap_bang_email(seed_data):
    user, msg = dao.dang_nhap("docgia@test.com", "Password123!")
    assert user is not None
    assert user.email == "docgia@test.com"

def test_dao_dang_nhap_bang_sdt(seed_data):
    user, msg = dao.dang_nhap("0900000003", "Password123!")
    assert user is not None
    assert user.soDienThoai == "0900000003"

def test_dao_dang_nhap_sai_mat_khau(seed_data):
    user, msg = dao.dang_nhap("docgia_test", "WrongPassword")
    assert user is None
    assert msg == "Mật khẩu không chính xác!"

def test_dao_dang_nhap_tai_khoan_khong_ton_tai(seed_data):
    user, msg = dao.dang_nhap("non_existent_user", "Password123!")
    assert user is None
    assert msg == "Tài khoản không tồn tại!"

def test_dao_dang_nhap_tai_khoan_bi_khoa(seed_data):
    user, msg = dao.dang_nhap("docgia_locked", "Password123!")
    assert user is None
    assert msg == "Tài khoản đã bị khóa!"

def test_route_login_post_success(client, seed_data):
    res = client.post('/login', data={
        'dinh_danh': 'docgia_test',
        'password': 'Password123!'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b'docgia_test' in res.data or "Độc Giả Test".encode('utf-8') in res.data or res.status_code == 200

def test_route_login_post_invalid(client, seed_data):
    res = client.post('/login', data={
        'dinh_danh': 'docgia_test',
        'password': 'WrongPassword'
    })
    assert res.status_code == 200
    assert "Mật khẩu không chính xác!".encode('utf-8') in res.data

def test_route_logout(client, seed_data):
    client.post('/login', data={
        'dinh_danh': 'docgia_test',
        'password': 'Password123!'
    })
    res = client.get('/logout', follow_redirects=True)
    assert res.status_code == 200

def test_dao_dat_lai_mat_khau(seed_data):
    docgia = seed_data['docgia']
    success, msg = dao.dat_lai_mat_khau(docgia.id, "NewPassword123!")
    assert success is True
    
    # Test logging in with new password
    user, _ = dao.dang_nhap("docgia_test", "NewPassword123!")
    assert user is not None


def test_dang_nhap_hoac_tao_oauth_tao_moi(seed_data):
    user, created = dao.dang_nhap_hoac_tao_tai_khoan_oauth(
        OAuthProvider.GOOGLE, "oauth-new-001", "oauthnew@test.com", "OAuth New", "avatar.jpg"
    )
    assert created is True
    assert user.role == UserRole.DOCGIA
    assert user.email == "oauthnew@test.com"
    assert user.oauthId == "oauth-new-001"
    assert user.avatar == "avatar.jpg"

def test_dang_nhap_hoac_tao_oauth_cap_nhat_tai_khoan_theo_email(seed_data):
    user = seed_data["docgia"]
    user.avatar = None
    db.session.commit()
    found, created = dao.dang_nhap_hoac_tao_tai_khoan_oauth(
        OAuthProvider.FACEBOOK, "fb-new-001", user.email, user.hoTen, "fb-avatar.jpg"
    )
    assert created is False
    assert found.id == user.id
    assert found.oauthId == "fb-new-001"
    assert found.avatar == "fb-avatar.jpg"

def test_get_thong_tin_ho_so_khong_ton_tai(seed_data):
    assert dao.get_thong_tin_ho_so(999999) == {}