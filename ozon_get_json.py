import json
import time
import tempfile
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def disable_geolocation_popup(driver):
    """Отключает запрос на определение местоположения"""
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
                navigator.geolocation.getCurrentPosition = function(success, error) {
                    error({ code: 1, message: 'Geolocation access denied' });
                };
                navigator.geolocation.watchPosition = function(success, error) {
                    error({ code: 1, message: 'Geolocation access denied' });
                };
            """
    })

def set_location(driver):
    """Клик по кнопке выбора адреса и ввод адреса"""
    try:
        # Клик по кнопке "Добавить"
        location_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[4]/div/div[1]/div/div[3]/button[1]/div[2]')))
        driver.execute_script('arguments[0].click();', location_button)

        # Клик по строке для ввода и ввод адреса
        address_input = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[4]/div/div[2]/div/div/div/div/div/div/div[1]/div/div/div/div[3]/div/div[2]/form/div/div/fieldset/div[1]/div/div/div/label/div[1]/div/textarea')))
        driver.execute_script('arguments[0].click();', address_input)
        time.sleep(3)
        address_input.send_keys('Москва, Брянская улица, 12')

        # Еще один клик, для появления окна выбора адреса
        address_input_again = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[4]/div/div[2]/div/div/div/div/div/div/div[1]/div/div/div/div[3]/div/div[2]/form/div/div/fieldset/div[1]/div/div/div/label/div[1]/div/textarea')))
        driver.execute_script('arguments[0].click();', address_input_again)

        # Выбираем адрес из появившегося списка
        press_to_address = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '/html/body/div[5]/div/div/div/div/span')))
        driver.execute_script('arguments[0].click();', press_to_address)

        # Нажимаем кнопку "Заберу отсюда"
        press_to_accept_address = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[4]/div/div[2]/div/div/div/div/div/div/div[1]/div/div/div/div[2]/button/div[1]/div')))
        driver.execute_script('arguments[0].click();', press_to_accept_address)

        print("✅ Адрес установлен: Москва, Брянская улица, 12")
    except Exception as e:
        print(f"⚠️ Ошибка при установке адреса: {e}")

def setup_options_webdriver():
    options = uc.ChromeOptions()
    options.add_argument("--lang=ru-RU")
    options.add_argument("--guest")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
    )
    options.add_argument("--disable-webrtc")
    options.add_argument("--disable-blink-features=AutomationControlled")

    temp_dir = tempfile.mkdtemp()
    options.add_argument(f"--user-data-dir={temp_dir}")

    driver = uc.Chrome(options=options)
    driver.maximize_window()

    driver.get("https://www.ozon.ru/")
    driver.execute_script("window.localStorage.clear();")
    driver.execute_script("window.sessionStorage.clear();")

    driver.execute_script("delete navigator.webdriver;")

    disable_geolocation_popup(driver)
    set_location(driver)

    return driver

if __name__ == '__main__':
    driver = setup_options_webdriver()
    url = 'https://www.ozon.ru/api/entrypoint-api.bx/page/json/v2?url=/category/vitaminy-bady-i-pishchevye-dobavki-6164/?layout_container=categorySearchMegapagination&layout_page_index=2&page=2&tf_state=r2k1Nr-U1OzqhgINpxW2L83I5YCS_1X0bLbkiKJHNzZn41q4r4UFQJlNc1M%3D'

    driver.get(url)
    json_text = driver.find_element(By.TAG_NAME, "pre").text  # Получаем текст из элемента <pre>
    data = json.loads(json_text)  # Преобразуем текст в JSON-объект

    with open('json.json', 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)
    print('JSON сохранен успешно.')

    driver.quit()
