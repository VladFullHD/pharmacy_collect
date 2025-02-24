import time
import csv
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import undetected_chromedriver as uc

def fetch_page(driver, url):
    """Загружает страницу и возвращает HTML-код"""
    print(f"🔍 Загружаем страницу: {url}")
    driver.get(url)
    WebDriverWait(driver, 10).until(lambda d: d.execute_script("return document.readyState") == "complete")
    return driver.page_source

def parse_product(product):
    """Парсинг данных товара"""
    try:
        title_element = product.select_one('.listing-card__title')
        title = title_element.text.strip() if title_element else "Нет названия"

        link_element = product.select_one('a[href]')
        link = 'https://www.eapteka.ru' + link_element['href'] if link_element else 'Нет ссылки'

        price_element = product.select_one('.listing-card__price-new')
        price = price_element.text.strip() if price_element else "Нет цены"

        brand_element = product.select_one('.listing-card__brand + a')
        brand_name = brand_element.text.strip() if brand_element else 'Нет бренда'

        match = re.search(r'(\d+)\s*шт', title)
        package = f"{match.group(1)} табл." if match else ""

        print(f"✅ Найден товар: {title} | Цена: {price} | Ссылка: {link}")

        return [title, price, 'Eapteka.ru', link, brand_name, package, 'Москва']
    except Exception as e:
        print(f'❌ Ошибка парсинга товара: {e}')
        return None

def parse_page(driver, url, first_page=False):
    """Обрабатывает страницу"""
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')

    products = soup.select('section.listing-card.js-neon-item')
    print(f"🛍 Найдено товаров: {len(products)} на {url}")

    if first_page:
        try:
            close_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Закрыть")]'))
            )
            close_button.click()
            print("🗙 Закрыли всплывающее окно")
        except:
            print('⚠️ Кнопка закрытия не найдена или не появилась')

    return [parse_product(product) for product in products if product]

def scroll_to_bottom(driver):
    """Плавная прокрутка страницы вниз"""
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
        time.sleep(1.5)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def parse_eapteka_bads(driver, base_url, num_pages):
    """Парсинг заданного количества страниц"""
    all_data = []
    start_time = time.time()  # Начало таймера

    for page in range(1, num_pages + 1):
        url = f"{base_url}?PAGEN_1={page}" if page > 1 else base_url
        print(f"📄 Загружаем страницу {page}: {url}")

        driver.get(url)  # Загружаем страницу
        time.sleep(2)  # Даем странице чуть подгрузиться перед скроллом

        scroll_to_bottom(driver)  # Прокручиваем вниз для полной подгрузки

        first_page = (page == 1)  # Обрабатываем pop-up только на первой странице
        page_data = parse_page(driver, url, first_page)

        if page_data:
            all_data.extend(page_data)

    end_time = time.time()  # Конец таймера
    print(f"⏳ Время парсинга: {round(end_time - start_time, 2)} секунд")
    return all_data


def write_to_csv(data, filename='eapteka_bads.csv'):
    """Записывает данные в CSV-файл."""
    if data:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            writer.writerow(["Название", "Цена", "Аптека", "Ссылка", "Бренд", "Упаковка", "Город"])
            writer.writerows(data)
        print(f"📁 Данные успешно записаны в {filename}")
    else:
        print('❌ Нет данных для записи в CSV.')

if __name__ == '__main__':

    options = uc.ChromeOptions()
    options.add_argument('start-maximized')

    driver = uc.Chrome(options=options)

    base_url = 'https://www.eapteka.ru/goods/vitaminy_i_bad/'
    num_pages = 2

    data = parse_eapteka_bads(driver, base_url, num_pages)
    driver.close()
    time.sleep(2)
    driver.quit()
    write_to_csv(data)


