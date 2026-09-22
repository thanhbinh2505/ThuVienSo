import pytest
from datetime import datetime, timedelta
from app import dao, db
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

def test_gui_gia_han_khi_phieu_khong_thuoc_nguoi_dung(seed_data):
    user = seed_data["docgia"]
    sach = seed_data["sach1"]
    dao.dang_ky_muon_sach(user.id, sach.id)
    phieu = PhieuMuon.query.filter_by(user_id=user.id, sach_id=sach.id).first()
    dao.duyet_phieu_muon(phieu.id)

    success, msg = dao.gui_yeu_cau_gia_han(seed_data["thuthu"].id, phieu.id)
    assert success is False
    assert msg == "Bạn không có quyền gia hạn phiếu mượn này!"

def test_gui_gia_han_khi_chua_duoc_duyet(seed_data):
    user = seed_data["docgia"]
    sach = seed_data["sach3"]
    dao.dang_ky_muon_sach(user.id, sach.id)
    phieu = PhieuMuon.query.filter_by(user_id=user.id, sach_id=sach.id).first()

    success, msg = dao.gui_yeu_cau_gia_han(user.id, phieu.id)
    assert success is False
    assert msg == "Chỉ sách đang được mượn mới có thể yêu cầu gia hạn!"

def test_tu_choi_gia_han_khi_khong_cho_gia_han(seed_data):
    user = seed_data["docgia"]
    sach = seed_data["sach3"]
    dao.dang_ky_muon_sach(user.id, sach.id)
    phieu = PhieuMuon.query.filter_by(user_id=user.id, sach_id=sach.id).first()

    success, msg = dao.tu_choi_gia_han(phieu.id)
    assert success is False
    assert msg == "Yêu cầu này không ở trạng thái chờ gia hạn!"

def test_huy_phieu_qua_han_chua_den_han(seed_data):
    user = seed_data["docgia"]
    sach = seed_data["sach3"]
    dao.dang_ky_muon_sach(user.id, sach.id)
    phieu = PhieuMuon.query.filter_by(user_id=user.id, sach_id=sach.id).first()
    dao.duyet_phieu_muon(phieu.id)
    phieu.ngayDuyet = datetime.now() - timedelta(days=1)
    db.session.commit()

    success, msg = dao.huy_phieu_qua_han(phieu.id)
    assert success is False
    assert msg == "Yêu cầu này chưa quá hạn nhận sách!"

def test_huy_phieu_qua_han_sai_trang_thai(seed_data):
    user = seed_data["docgia"]
    sach = seed_data["sach3"]
    dao.dang_ky_muon_sach(user.id, sach.id)
    phieu = PhieuMuon.query.filter_by(user_id=user.id, sach_id=sach.id).first()

    success, msg = dao.huy_phieu_qua_han(phieu.id)
    assert success is False
    assert msg == "Yêu cầu này không ở trạng thái chờ nhận sách!"

def test_huy_phieu_qua_han_chua_co_ngay_duyet(seed_data):
    user = seed_data["docgia"]
    sach = seed_data["sach3"]
    phieu = PhieuMuon(
        user_id=user.id,
        sach_id=sach.id,
        trangThai=TrangThaiMuon.DA_DUYET,
        ngayDuyet=None
    )
    db.session.add(phieu)
    db.session.commit()

    success, msg = dao.huy_phieu_qua_han(phieu.id)
    assert success is False
    assert msg == "Phiếu chưa có ngày duyệt!"

def test_get_phieu_muon_da_tra_cua_doc_gia(seed_data):
    user = seed_data["docgia"]
    sach = seed_data["sach3"]
    dao.dang_ky_muon_sach(user.id, sach.id)
    phieu = PhieuMuon.query.filter_by(user_id=user.id, sach_id=sach.id).first()
    dao.duyet_phieu_muon(phieu.id)
    dao.tra_sach(user.id, phieu.id)

    result = dao.get_phieu_muon_da_tra_cua_doc_gia(user.id)
    assert any(p.id == phieu.id for p in result)

def test_get_phieu_muon_qua_han_cua_doc_gia(seed_data):
    user = seed_data["docgia"]
    sach = seed_data["sach3"]
    dao.dang_ky_muon_sach(user.id, sach.id)
    phieu = PhieuMuon.query.filter_by(user_id=user.id, sach_id=sach.id).first()
    dao.duyet_phieu_muon(phieu.id)
    phieu.hanTra = datetime.now() - timedelta(days=1)
    db.session.commit()

    result = dao.get_phieu_muon_qua_han_cua_doc_gia(user.id)
    assert any(p.id == phieu.id for p in result)