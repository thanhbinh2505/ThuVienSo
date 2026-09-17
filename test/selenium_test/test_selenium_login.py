import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_selenium_login_thanh_cong(live_server, driver):
    driver.get(f"{live_server}/login")

    dinh_danh_input = driver.find_element(By.NAME, "dinh_danh")
    password_input = driver.find_element(By.NAME, "password")
    
    dinh_danh_input.clear()
    dinh_danh_input.send_keys("docgia_selenium")
    
    password_input.clear()
    password_input.send_keys("Password123!")
    
    # Submit form
    submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    submit_btn.click()

    WebDriverWait(driver, 5).until(
        EC.url_to_be(f"{live_server}/")
    )
    assert driver.current_url == f"{live_server}/"
    assert "Độc Giả Selenium" in driver.page_source or "docgia_selenium" in driver.page_source or "Đăng xuất" in driver.page_source

def test_selenium_login_sai_mat_khau(live_server, driver):
    driver.get(f"{live_server}/login")
    
    driver.find_element(By.NAME, "dinh_danh").send_keys("docgia_selenium")
    driver.find_element(By.NAME, "password").send_keys("WrongPassword")
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Mật khẩu không chính xác')]"))
    )
    assert "Mật khẩu không chính xác" in driver.page_source
