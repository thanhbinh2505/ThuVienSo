import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_selenium_tim_kiem_sach_tren_trang_chu(live_server, driver):
    driver.get(live_server)

    search_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='search'], input[name='q'], input[name='tu_khoa']")
    if search_inputs:
        search_input = search_inputs[0]
        search_input.clear()
        search_input.send_keys("Dế Mèn")
        search_input.send_keys(Keys.ENTER)
        
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'Dế Mèn Phiêu Lưu Ký')]"))
        )
        assert "Dế Mèn Phiêu Lưu Ký" in driver.page_source

