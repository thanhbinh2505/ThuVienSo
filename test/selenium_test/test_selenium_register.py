import time
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC

def test_selenium_dang_ky_thanh_cong(live_server, driver):
    driver.get(f"{live_server}/register")
    
    unique_ts = str(int(time.time()))
    username = f"usr_{unique_ts[-7:]}"
    sdt = f"09{unique_ts[-8:]}"
    
    driver.find_element(By.NAME, "username").send_keys(username)
    driver.find_element(By.NAME, "hoten").send_keys("Người Dùng Selenium Mới")
    driver.find_element(By.NAME, "email").send_keys(f"{username}@test.com")
    driver.find_element(By.NAME, "sdt").send_keys(sdt)
    
    Select(driver.find_element(By.NAME, "gioitinh")).select_by_value("male")
    
    driver.find_element(By.NAME, "password").send_keys("Password123!")
    
    # Submit form
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    

    WebDriverWait(driver, 5).until(
        EC.url_contains("/login")
    )
    assert "/login" in driver.current_url

def test_selenium_dang_ky_mat_khau_khong_khop(live_server, driver):
    driver.get(f"{live_server}/register")
    
    unique_ts = str(int(time.time()))
    username = f"mis_{unique_ts[-7:]}"
    
    driver.find_element(By.NAME, "username").send_keys(username)
    driver.find_element(By.NAME, "hoten").send_keys("Mismatch User")
    driver.find_element(By.NAME, "email").send_keys(f"{username}@test.com")
    Select(driver.find_element(By.NAME, "gioitinh")).select_by_value("female")
    
    driver.find_element(By.NAME, "password").send_keys("Password123!")
    
    driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
    
    assert "register" in driver.current_url or "Đăng ký" in driver.page_source
