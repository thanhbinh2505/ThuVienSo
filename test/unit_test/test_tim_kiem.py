import pytest
from app import dao

def test_tim_kiem_sach_tu_khoa(seed_data):
    res = dao.tim_kiem_sach(tu_khoa="Dế Mèn")
    assert res['total'] == 1
    assert res['items'][0]['tenSach'] == "Dế Mèn Phiêu Lưu Ký"

def test_tim_kiem_sach_tac_gia(seed_data):
    res = dao.tim_kiem_sach(tu_khoa="Stephen")
    assert res['total'] == 1
    assert res['items'][0]['tacGia'] == "Stephen Hawking"

def test_tim_kiem_sach_the_loai(seed_data):
    tl1 = seed_data['tl1']
    res = dao.tim_kiem_sach(theloai_id=tl1.id)
    assert res['total'] == 2
    assert any(item['tenSach'] == "Dế Mèn Phiêu Lưu Ký" for item in res['items'])

def test_tim_kiem_sach_sap_xep(seed_data):
    res_az = dao.tim_kiem_sach(sort="ten_az")
    assert len(res_az['items']) == 3
    assert res_az['items'][0]['tenSach'] == "Dế Mèn Phiêu Lưu Ký"

    res_rating = dao.tim_kiem_sach(sort="danh_gia")
    assert len(res_rating['items']) == 3
    assert res_rating['items'][0]['tenSach'] == "Dế Mèn Phiêu Lưu Ký"

def test_api_tim_kiem_sach(client, seed_data):
    res = client.get('/api/sach?q=D%E1%BA%BF')
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data['success'] is True
    assert json_data['total'] >= 1

def test_api_the_loai(client, seed_data):
    res = client.get('/api/theloai')
    assert res.status_code == 200
    json_data = res.get_json()
    assert isinstance(json_data, list)
    assert len(json_data) == 2

def test_tim_kiem_sach_khong_co_ket_qua(seed_data):
    result = dao.tim_kiem_sach(tu_khoa="chuoi_khong_ton_tai_xyz")
    assert result["total"] == 0
    assert result["items"] == []
    assert result["total_pages"] == 1

def test_tim_kiem_sach_phan_trang(seed_data):
    result = dao.tim_kiem_sach(page=2, page_size=2, sort="ten_az")
    assert result["page"] == 2
    assert result["page_size"] == 2
    assert result["total"] == 3
    assert result["total_pages"] == 2
    assert len(result["items"]) == 1

def test_tim_kiem_sach_loc_the_loai_khong_co_sach(seed_data):
    result = dao.tim_kiem_sach(theloai_id=999999)
    assert result["total"] == 0
    assert result["items"] == []