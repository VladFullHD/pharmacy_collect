import time
import csv
import re
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from seleniumwire import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import tempfile

'''
Как меняется класс с карточкой товара:
1)'x4i_23 xi5_23 tile-root'
2)'xi4_23 i5x_23 tile-root'
'''
'''
952 товара на 102 стр.
'''


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
        '/html/body/div[4]/div/div[2]/div/div/div/div/div/div/div[1]/div/div/div/div[2]/button/div[2]'
        press_to_accept_address = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[4]/div/div[2]/div/div/div/div/div/div/div[1]/div/div/div/div[2]/button/div[1]/div')))
        driver.execute_script('arguments[0].click();', press_to_accept_address)

        print("✅ Адрес установлен: Москва, Брянская улица, 12")
    except Exception as e:
        print(f"⚠️ Ошибка при установке адреса: {e}")

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

def extract_quantity(title_text):
    patterns = [
        r'(\d+)\s*(табл|таблеток|капс|капсул|шт|пакетиков|мл)\s*№?\s*(\d+)?',
        r'№?\s*(\d+)\s*(табл|таблеток|капс|капсул|шт|пакетиков|мл)',
        r'(\d+)\s*(табл|таблеток|капс|капсул|шт|пакетиков|мл)',
    ]

    for pattern in patterns:
        match = re.search(pattern, title_text, re.IGNORECASE)
        if match:
            try:
                if match.group(3):
                    return match.group(3) + f' {match.group(2)}'
                elif match.group(1):
                    return match.group(1) + f' {match.group(2)}'
            except IndexError:
                return match.group(1)
    return None

def parse_ozon(driver, base_url, num_pages):
    all_data = []
    processed_items = set()

    driver.get(base_url)
    disable_geolocation_popup(driver)
    set_location(driver)

    for page in range(1, num_pages + 1):
        url = f"{base_url}?page={page}" if page > 1 else base_url
        print(f"📄 Загружаем страницу {page}: {url}")
        time.sleep(3)
        driver.get(url)
        time.sleep(3)
        page_data = parse_page(driver, url)

        if page_data:
            for item in page_data:
                if item:
                    item_tuple = (item[0], item[1])
                    if item_tuple not in processed_items:
                        all_data.append(item)
                        processed_items.add(item_tuple)
                    else:
                        print(f"⚠️ Дубликат товара: {item[0]}, {item[1]}")

    return all_data

def parse_page(driver, url):
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    products = soup.find_all('div', class_='xi4_23 i5x_23 tile-root')
    print(f"🛍 Найдено товаров: {len(products)} на {url}")

    return [parse_product(product) for product in products if product]

def parse_product(product):
    try:
        title_element = product.find('span', class_='tsBody500Medium')
        title_text = title_element.text if title_element else 'Название не найдено'

        price_element = product.find('span', class_='c3024-a1 tsHeadline500Medium c3024-b1 c3024-a6')
        price_text = price_element.text.strip() if price_element else 'Цена не найдена'

        link_element = product.find('a')
        link_text = 'https://www.ozon.ru' + link_element.get('href') if link_element else 'Ссылка не найдена'

        brand_element = product.find('span', class_= 'p6b17-a4')
        brand_text = brand_element.text.strip() if brand_element else 'Бренд не найден'
        if (brand_text == "Стало дешевле" or brand_text == "Оригинал" or re.match(r'\d+ ₽ / шт', brand_text)
                or re.match(r'\d+\.\d+', brand_text)):
            brand_text = 'Бренд не найден'

        # package = extract_quantity(title_text)

        print(f'Найден товар: "{title_text}"')
        return [title_text, price_text, 'Ozon.ru', link_text, brand_text, 'Москва']
    except AttributeError:
        print(f'Ошибка: не удалось найти элемент (возможно, изменилась структура сайта)')
    except Exception as e:
        print(f'Ошибка парсинга товара: {e}')
        return None

def save_to_csv(data, filename="ozon_products.csv"):
    if data:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            writer.writerow(['Название', 'Цена', 'Аптека', 'Ссылка', 'Бренд', 'Город'])
            writer.writerows(data)
        print(f'Данные успешно записаны в {filename}')
    else:
        print('Нет данных для записи в CSV.')

def setup_options_webdriver():
    options = uc.ChromeOptions()
    options.add_argument("--lang=ru-RU")
    options.add_argument("--guest")  # Гостевой режим (альтернатива инкогнито)
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
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

    return driver

if __name__ == '__main__':
    url = 'https://www.ozon.ru/category/vitaminy-bady-i-pishchevye-dobavki-6164/'
    num_pages = 102
    driver = setup_options_webdriver()
    data = parse_ozon(driver, url, num_pages)
    save_to_csv(data)
    driver.quit()