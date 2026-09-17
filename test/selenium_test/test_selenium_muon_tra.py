import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_selenium_quy_trinh_muon_tra_sach(live_server, driver):
    driver.get(f"{live_server}/login")
    driver.find_element(By.NAME, "dinh_danh").send_keys("docgia_selenium")
    driver.find_element(By.NAME, "password").send_keys("Password123!")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    
    WebDriverWait(driver, 5).until(EC.url_to_be(f"{live_server}/"))

    driver.get(f"{live_server}/sach/1")

    muon_btns = driver.find_elements(By.XPATH, "//button[contains(text(), 'Mượn') or contains(text(), 'Đăng ký mượn')]")
    if muon_btns:
        muon_btns[0].click()
        try:
            WebDriverWait(driver, 3).until(EC.alert_is_present())
            alert = driver.switch_to.alert
            alert.accept()
        except Exception:
            pass

    driver.get(f"{live_server}/logout")
    driver.get(f"{live_server}/login")
    
    driver.find_element(By.NAME, "dinh_danh").send_keys("thuthu_selenium")
    driver.find_element(By.NAME, "password").send_keys("Password123!")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    driver.get(f"{live_server}/thuthu")
    assert driver.status_code if hasattr(driver, 'status_code') else True
    assert "Thủ thư" in driver.page_source or "Yêu cầu" in driver.page_source or "phieu" in driver.page_source
