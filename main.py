import asyncio
import aiohttp
import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import csv


async def fetch_page(session, url):
    async with session.get(url) as response:
        return await response.text()


def parse_eapteka_bads(driver, base_url, num_pages):
    """Парсит БАДы с сайта Eapteka.ru."""

    all_data = []
    for page in range(1, num_pages + 1):
        url = f"{base_url}?PAGEN_1={page}" if page > 1 else base_url
        driver.get(url)

        # Прокручиваем страницу вниз, пока не загрузятся все товары
        while True:
            # Получаем текущую высоту страницы
            last_height = driver.execute_script("return document.body.scrollHeight")
            # Прокручиваем страницу вниз до конца
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            # Ждем, пока страница загрузится
            time.sleep(5)
            # Получаем новую высоту страницы
            new_height = driver.execute_script("return document.body.scrollHeight")
            # Если высота страницы не изменилась, значит, все товары загружены
            if new_height == last_height:
                break

        try:
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '/html/body/div[3]/div[1]/button'))
            )
            driver.execute_script("arguments[0].click();", element)
        except:
            print('Кнопка закрытия не найдена')

        # Получаем HTML-код страницы
        html = driver.page_source

        # Разбираем HTML-код с помощью Beautiful Soup
        soup = BeautifulSoup(html, 'html.parser')

        # Находим все товары на странице
        products = soup.find_all('section', class_='listing-card js-neon-item')

        for product in products:

            title = product.find('div', class_='listing-card__title').text.strip()

            price = product.find('span', class_='listing-card__price-new').text.strip()

            link = 'www.eapteka.ru' + product.find('a')['href']

            brand_span = product.find('span', class_='listing-card__brand')
            if brand_span:
                brand_a = brand_span.find_next_sibling('a')
                if brand_a:
                    brand_name = brand_a.text.strip()
            else:
                brand_name = 'Уточняйте на сайте'

            package_find = product.find('div', class_='listing-card__title').text
            count = None
            match = re.search(r'(\d+)\s*шт', package_find)
            if match:
                count = match.group(1)
            if count:
                package = count + ' табл.'
            else:
                package = ''


            all_data.append([title, price, "Eapteka.ru", link, brand_name, package, "Москва"])

    return all_data

def write_to_csv(data, filename="eapteka_bads.csv"):
    """Записывает данные в CSV-файл."""

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Название", "Цена", "Аптека", "Ссылка", "Бренд", "Упаковка", "Город"])
        writer.writerows(data)

if __name__ == "__main__":

    options = webdriver.ChromeOptions()
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()

    base_url = "https://www.eapteka.ru/goods/vitaminy_i_bad/"  # Ссылка на категорию БАДы
    num_pages = 10
    data = parse_eapteka_bads(driver, base_url, num_pages)
    write_to_csv(data)
