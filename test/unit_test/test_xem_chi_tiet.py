import pytest
from app import dao

def test_get_sach_by_id_hop_le(seed_data):
    sach1 = seed_data['sach1']
    sach = dao.get_sach_by_id(sach1.id)
    assert sach is not None
    assert sach.tenSach == "Dế Mèn Phiêu Lưu Ký"

def test_get_sach_by_id_khong_ton_tai(seed_data):
    sach = dao.get_sach_by_id(9999)
    assert sach is None

def test_route_chi_tiet_sach(client, seed_data):
    sach1 = seed_data['sach1']
    res = client.get(f'/sach/{sach1.id}')
    assert res.status_code == 200
    assert "Dế Mèn Phiêu Lưu Ký".encode('utf-8') in res.data

def test_route_chi_tiet_sach_404(client, seed_data):
    res = client.get('/sach/9999')
    assert res.status_code == 404

def test_api_chi_tiet_sach(client, seed_data):
    sach1 = seed_data['sach1']
    res = client.get(f'/api/sach/{sach1.id}')
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data['success'] is True
    assert json_data['data']['tenSach'] == "Dế Mèn Phiêu Lưu Ký"

def test_danh_gia_sach(seed_data):
    docgia = seed_data['docgia']
    sach1 = seed_data['sach1']
    success, msg = dao.danh_gia_sach(docgia.id, sach1.id, 5)
    assert success is True

def test_danh_gia_sach_so_sao_khong_hop_le(seed_data):
    docgia = seed_data['docgia']
    sach1 = seed_data['sach1']
    success, msg = dao.danh_gia_sach(docgia.id, sach1.id, 6)
    assert success is False
    assert msg == "Số sao phải từ 1 đến 5!"

def test_them_va_xoa_binh_luan(seed_data):
    docgia = seed_data['docgia']
    sach1 = seed_data['sach1']
    
    # Thêm bình luận
    success, msg, bl = dao.them_binh_luan(docgia.id, sach1.id, "Sách rất hay!")
    assert success is True
    assert bl is not None
    assert bl.noiDung == "Sách rất hay!"

    # Xóa bình luận
    del_success, del_msg = dao.xoa_binh_luan(docgia.id, bl.id)
    assert del_success is True
