import pytest
from app import dao, db


def test_khoa_va_mo_khoa_doc_gia(seed_data):
    user = seed_data["docgia"]
    success, msg = dao.khoa_user(user.id)
    assert success is True
    assert msg == "Đã khóa tài khoản!"
    assert user.active is False

    success, msg = dao.mo_khoa_user(user.id)
    assert success is True
    assert msg == "Đã mở khóa tài khoản!"
    assert user.active is True

def test_khoa_admin_khong_duoc_phep(seed_data):
    admin = seed_data["admin"]
    success, msg = dao.khoa_user(admin.id)
    assert success is False
    assert msg == "Không thể khóa tài khoản Admin!"

def test_xoa_user_dang_co_phieu_muon_khong_duoc_phep(seed_data):
    user = seed_data["docgia"]
    sach = seed_data["sach1"]
    dao.dang_ky_muon_sach(user.id, sach.id)
    success, msg = dao.xoa_user(user.id)
    assert success is False
    assert msg == "Không thể xóa người dùng vì đang có phiếu mượn hoạt động!"