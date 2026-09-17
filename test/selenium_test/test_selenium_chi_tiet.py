import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_selenium_xem_chi_tiet_sach(live_server, driver):
    driver.get(f"{live_server}/sach/1")
    
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Dế Mèn Phiêu Lưu Ký')]"))
    )
    assert "Dế Mèn Phiêu Lưu Ký" in driver.page_source
    assert "Tô Hoài" in driver.page_source

def test_selenium_sach_khong_ton_tai(live_server, driver):
    driver.get(f"{live_server}/sach/99999")
    assert "404" in driver.title or "404" in driver.page_source or "Not Found" in driver.page_source
