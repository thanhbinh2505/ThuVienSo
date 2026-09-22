import pytest
from app import dao
from app.models import Sach

def test_them_sach_thanh_cong(seed_data):
    tl1 = seed_data['tl1']
    success, msg, sach = dao.them_sach(
        ten_sach="Sách Mới Thêm",
        tac_gia="Tác Giả Mới",
        nha_xuat_ban="NXB Trẻ",
        nam_xuat_ban=2024,
        theloai_id=tl1.id,
        so_luong=15
    )
    assert success is True
    assert sach is not None
    assert sach.tenSach == "Sách Mới Thêm"
    assert sach.soLuongConLai == 15

def test_cap_nhat_sach_thanh_cong(seed_data):
    sach1 = seed_data['sach1']
    success, msg = dao.cap_nhat_sach(
        sach_id=sach1.id,
        ten_sach="Dế Mèn Phiêu Lưu Ký (Tái Bản)",
        tac_gia="Tô Hoài",
        so_luong=20
    )
    assert success is True
    updated = dao.get_sach_by_id(sach1.id)
    assert updated.tenSach == "Dế Mèn Phiêu Lưu Ký (Tái Bản)"
    assert updated.soLuong == 20

def test_xoa_sach_thanh_cong(seed_data):
    tl1 = seed_data['tl1']
    _, _, sach = dao.them_sach(
        ten_sach="Sách Cần Xóa",
        tac_gia="Tác Giả X",
        theloai_id=tl1.id,
        so_luong=5
    )
    sach_id = sach.id

    success, msg = dao.xoa_sach(sach_id)
    assert success is True
    assert dao.get_sach_by_id(sach_id) is None

def test_phan_quyen_trang_quan_ly_sach(client, seed_data):

    res_anon = client.get('/admin/sach')
    assert res_anon.status_code == 302


    client.post('/login', data={'dinh_danh': 'docgia_test', 'password': 'Password123!'})
    res_docgia = client.get('/admin/sach')
    assert res_docgia.status_code == 403


    client.get('/logout')
    client.post('/login', data={'dinh_danh': 'thuthu_test', 'password': 'Password123!'})
    res_thuthu = client.get('/admin/sach')
    assert res_thuthu.status_code == 200

def test_cap_nhat_sach_khong_ton_tai(seed_data):
    success, msg = dao.cap_nhat_sach(999999, "Tên", "Tác giả")
    assert success is False
    assert msg == "Không tìm thấy sách!"

def test_xoa_sach_khong_ton_tai(seed_data):
    success, msg = dao.xoa_sach(999999)
    assert success is False
    assert msg == "Không tìm thấy sách!"