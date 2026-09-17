import pytest
from app import dao
from app.models import PhieuMuon, TrangThaiMuon

def test_dang_ky_muon_sach_thanh_cong(seed_data):
    docgia = seed_data['docgia']
    sach1 = seed_data['sach1']

    success, msg = dao.dang_ky_muon_sach(docgia.id, sach1.id)
    assert success is True
    assert msg == "Đăng ký mượn sách thành công!"

    phieu = PhieuMuon.query.filter_by(user_id=docgia.id, sach_id=sach1.id).first()
    assert phieu is not None
    assert phieu.trangThai == TrangThaiMuon.CHO_DUYET

def test_dang_ky_muon_sach_het_hang(seed_data):
    docgia = seed_data['docgia']
    sach2 = seed_data['sach2']

    success, msg = dao.dang_ky_muon_sach(docgia.id, sach2.id)
    assert success is False
    assert msg == "Sách hiện đã hết!"

def test_duyet_phieu_muon(seed_data):
    docgia = seed_data['docgia']
    sach1 = seed_data['sach1']
    so_luong_ban_dau = sach1.soLuongConLai

    dao.dang_ky_muon_sach(docgia.id, sach1.id)
    phieu = PhieuMuon.query.filter_by(user_id=docgia.id, sach_id=sach1.id).first()

    success, msg = dao.duyet_phieu_muon(phieu.id)
    assert success is True
    assert phieu.trangThai == TrangThaiMuon.DA_DUYET
    assert sach1.soLuongConLai == so_luong_ban_dau - 1

def test_tu_choi_phieu_muon(seed_data):
    docgia = seed_data['docgia']
    sach1 = seed_data['sach1']

    dao.dang_ky_muon_sach(docgia.id, sach1.id)
    phieu = PhieuMuon.query.filter_by(user_id=docgia.id, sach_id=sach1.id).first()

    success, msg = dao.tu_choi_phieu_muon(phieu.id)
    assert success is True
    assert phieu.trangThai == TrangThaiMuon.TU_CHOI

def test_gui_va_duyet_gia_han(seed_data):
    docgia = seed_data['docgia']
    sach1 = seed_data['sach1']

    dao.dang_ky_muon_sach(docgia.id, sach1.id)
    phieu = PhieuMuon.query.filter_by(user_id=docgia.id, sach_id=sach1.id).first()
    dao.duyet_phieu_muon(phieu.id)


    success_gh, msg_gh = dao.gui_yeu_cau_gia_han(docgia.id, phieu.id)
    assert success_gh is True
    assert phieu.trangThai == TrangThaiMuon.CHO_GIA_HAN

    success_dgh, msg_dgh = dao.duyet_gia_han(phieu.id)
    assert success_dgh is True
    assert phieu.trangThai == TrangThaiMuon.DA_DUYET

def test_tra_sach(seed_data):
    docgia = seed_data['docgia']
    sach1 = seed_data['sach1']

    dao.dang_ky_muon_sach(docgia.id, sach1.id)
    phieu = PhieuMuon.query.filter_by(user_id=docgia.id, sach_id=sach1.id).first()
    dao.duyet_phieu_muon(phieu.id)
    so_luong_sau_muon = sach1.soLuongConLai

    success, msg = dao.tra_sach(docgia.id, phieu.id)
    assert success is True
    assert phieu.trangThai == TrangThaiMuon.DA_TRA
    assert sach1.soLuongConLai == so_luong_sau_muon + 1
