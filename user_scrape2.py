import time
import json
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO)

STAR_TO_FLOAT = {
    '½': 0.5,
    '★': 1.0
}

def convert_stars_to_float(star_string):
    rating = 0.0
    for char in star_string:
        if char == '★':
            rating += 1.0
        elif char == '½':
            rating += 0.5
    return rating

def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def get_total_pages(driver, url):
    driver.get(url)
    time.sleep(2)
    try:
        pagination = driver.find_elements(By.CSS_SELECTOR, 'div.pagination a')
        pages = [int(p.text) for p in pagination if p.text.isdigit()]
        return max(pages) if pages else 1
    except:
        return 1

def scrape_films_and_ratings(username):
    driver = init_driver()
    base_url = f"https://letterboxd.com/{username}/films"
    total_pages = get_total_pages(driver, base_url)
    logging.info(f"Found {total_pages} pages of films for {username}")

    watched_movies = []

    for page in range(1, total_pages + 1):
        page_url = f"{base_url}/page/{page}/"
        driver.get(page_url)
        time.sleep(2)

        posters = driver.find_elements(By.CLASS_NAME, 'poster-container')

        for poster in posters:
            try:
                film_link = poster.find_element(By.TAG_NAME, 'a').get_attribute('href')
                title = film_link.split("/film/")[1].strip("/").replace("-", " ").title()

                try:
                    viewingdata = poster.find_element(By.CLASS_NAME, 'poster-viewingdata')
                    rating_span = viewingdata.find_element(By.CSS_SELECTOR, 'span.rating')
                    stars = rating_span.text.strip()
                    rating = convert_stars_to_float(stars)
                except:
                    rating = None

                watched_movies.append({
                    "title": title,
                    "rating": rating
                })
            except Exception as e:
                logging.warning(f"Skipping one movie due to error: {e}")
                continue

        logging.info(f"Page {page} scraped: {len(watched_movies)} movies collected so far.")

    driver.quit()
    return watched_movies

def save_as_json(username, data):
    filename = f"{username}_watched.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logging.info(f"Saved data to {filename}")

def main():
    username = input("Enter Letterboxd username: ").strip()
    logging.info(f"Scraping films and ratings for {username}...")
    watched = scrape_films_and_ratings(username)

    save_as_json(username, watched)

if __name__ == "__main__":
    main()
