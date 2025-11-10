import requests
from bs4 import BeautifulSoup
import json
import os
import time
import asyncio
import aiohttp
from datetime import datetime, timedelta
import logging
import random

# Setup logging
logging.basicConfig(filename='app.log', level=logging.DEBUG)

CACHE_FILE = "price_cache.json"
CACHE_EXPIRY_HOURS = 24

WHEEL_SIZE_API_BASE = "https://api.wheel-size.com/v2"
WHEEL_SIZE_API_KEY = os.getenv('WHEEL_SIZE_API_KEY', '')  # Free sandbox key from https://developer.wheel-size.com/

# User agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36"
]

# Optional proxies (uncomment and add free proxies from https://free-proxy-list.net/)
# PROXIES = ["http://proxy1:port", "http://proxy2:port"]

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)

def is_cache_valid(key, cache):
    if key in cache and 'timestamp' in cache[key]:
        ts = datetime.fromisoformat(cache[key]['timestamp'])
        if datetime.now() - ts < timedelta(hours=CACHE_EXPIRY_HOURS):
            return True
    return False

def get_mock_prices(make, model, year, size):
    # Extra Feature: Expanded mock data with more models
    mock_data = {
        "Toyota": {
            "Camry": {2023: {"19-inch": {"Michelin Defender": 189.99, "Bridgestone Turanza": 199.99, "Goodyear Assurance": 179.99}}},
            "RAV4": {2023: {"18-inch": {"Goodyear Assurance": 159.99, "Continental TrueContact": 169.99, "Pirelli Scorpion": 174.99}}},
            "Corolla": {2022: {"17-inch": {"Michelin Energy": 149.99, "Firestone Firehawk": 139.99}}},
        },
        "Honda": {
            "Accord": {2022: {"18-inch": {"Michelin Pilot": 179.99, "Firestone Firehawk": 169.99, "Bridgestone Potenza": 184.99}}},
            "Civic": {2023: {"17-inch": {"Continental ExtremeContact": 159.99, "Goodyear Eagle": 149.99}}},
        },
        "Ford": {
            "F-150": {2024: {"20-inch": {"BFGoodrich All-Terrain": 229.99, "Goodyear Wrangler": 219.99, "Michelin LTX": 239.99}}},
            "Mustang": {2023: {"19-inch": {"Pirelli P Zero": 249.99, "Continental SportContact": 239.99}}},
        },
        "BMW": {
            "X5": {2021: {"19-inch": {"Pirelli Scorpion": 249.99, "Continental ExtremeContact": 239.99, "Michelin Latitude": 259.99}}},
            "3 Series": {2023: {"18-inch": {"Bridgestone Turanza": 219.99, "Goodyear Eagle": 209.99}}},
        },
        "Tesla": {
            "Model 3": {2023: {"18-inch": {"Michelin Pilot Sport": 229.99, "Continental ProContact": 219.99}}},
            "Model Y": {2024: {"19-inch": {"Pirelli Elect": 239.99, "Goodyear ElectricDrive": 229.99}}},
        },
        "Chevrolet": {
            "Silverado": {2023: {"20-inch": {"Goodyear Wrangler": 249.99, "BFGoodrich KO2": 259.99}}},
        },
        "Mercedes": {
            "GLE": {2022: {"19-inch": {"Continental CrossContact": 269.99, "Pirelli Scorpion Verde": 259.99}}},
        },
        "Volkswagen": {  # New
            "Golf": {2023: {"18-inch": {"Michelin Pilot": 189.99, "Continental Sport": 179.99}}},
        },
        "Audi": {  # New
            "A4": {2022: {"19-inch": {"Pirelli P Zero": 229.99, "Bridgestone Potenza": 219.99}}},
        }
    }

    try:
        return mock_data.get(make.title(), {}).get(model.title(), {}).get(int(year), {}).get(size, {})
    except ValueError:
        logging.error("Invalid year in mock prices")
        return {}

def get_recommended_tire_sizes(make, model, year):
    if not WHEEL_SIZE_API_KEY:
        logging.warning("Wheel-Size API key not set")
        return "Using default recommendation: 19-inch."
    try:
        url = f"{WHEEL_SIZE_API_BASE}/search/by_model/"
        params = {
            "make": make.lower(),
            "model": model.lower(),
            "year": year,
            "region": "usdm",
            "user_key": WHEEL_SIZE_API_KEY
        }
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('data'):
                tires = set()
                for mod in data['data']:
                    for tire in mod.get('tires', []):
                        tires.add(tire.get('tire', 'Unknown'))
                return f"Recommended tire sizes: {', '.join(tires) or 'No recommendations found'}"
        return "No recommendations found from API."
    except Exception as e:
        logging.error(f"Wheel-Size API error: {str(e)}")
        return "API error. Using mock: 19-inch."

async def async_scrape_tirerack(session, url):
    """Detailed scraping for Tire Rack with additional fields."""
    prices = {}
    try:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        # Optional proxy: async with session.get(url, headers=headers, proxy=random.choice(PROXIES), timeout=10) as response:
        async with session.get(url, headers=headers, timeout=10) as response:
            if response.status == 200:
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')
                products = soup.find_all('div', class_='product-result')  # Main container
                for product in products[:5]:  # Limit for speed
                    # Name and brand
                    name_elem = product.find('span', class_='product-name')
                    name = name_elem.text.strip() if name_elem else "Unknown"
                    brand = name.split()[0] if name != "Unknown" else "Unknown"  # Extract brand from name
                    
                    # Price
                    price_elem = product.find('span', class_='price-amount')
                    price_text = price_elem.text.strip().replace('$', '').replace(',', '') if price_elem else "N/A"
                    try:
                        price = float(price_text)
                    except ValueError:
                        price = 0.0
                    
                    # Additional details: Size, rating, warranty
                    size_elem = product.find('div', class_='tire-size')  # Assumed class; adjust if needed
                    size = size_elem.text.strip() if size_elem else "N/A"
                    
                    rating_elem = product.find('span', class_='rating-value')  # Assumed for customer rating
                    rating = rating_elem.text.strip() if rating_elem else "N/A"
                    
                    warranty_elem = product.find('div', class_='warranty-info')  # Assumed
                    warranty = warranty_elem.text.strip() if warranty_elem else "N/A"
                    
                    if price > 0:
                        prices[name] = {
                            "price": price,
                            "brand": brand,
                            "size": size,
                            "rating": rating,
                            "warranty": warranty
                        }
                logging.info(f"Tire Rack scraped successfully: {len(prices)} items")
    except Exception as e:
        logging.error(f"Tire Rack scrape failed: {str(e)}")
        # Fallback: Search for any price-like strings
        price_tags = soup.find_all(string=lambda t: t and '$' in t)
        for tag in price_tags[:5]:
            prices[f"Fallback {len(prices)+1}"] = tag.strip()
    return prices

async def async_scrape_site(session, url, site_name):
    prices = {}
    try:
        async with session.get(url, timeout=10) as response:
            if response.status == 200:
                text = await response.text()
                soup = BeautifulSoup(text, 'html.parser')
                if site_name == "simpletire":
                    items = soup.find_all('div', class_='product-item')
                    for item in items[:5]:
                        name_elem = item.find('h3', class_='product-name')
                        price_elem = item.find('span', class_='price')
                        if name_elem and price_elem:
                            name = name_elem.text.strip()
                            try:
                                price = float(price_elem.text.strip().replace('$', '').replace(',', ''))
                                prices[name] = price
                            except ValueError:
                                continue
                elif site_name == "discounttire":
                    items = soup.find_all('div', class_='product-item')  
                    for item in items[:5]:
                        name_elem = item.find('h3', class_='product-name')
                        price_elem = item.find('span', class_='price')
                        if name_elem and price_elem:
                            name = name_elem.text.strip()
                            try:
                                price = float(price_elem.text.strip().replace('$', '').replace(',', ''))
                                prices[name] = price
                            except ValueError:
                                continue
    except Exception as e:
        logging.error(f"{site_name} scrape failed: {str(e)}")
    return prices

async def async_scrape_prices(make, model, year, size, zip_code):
    headers = {"User-Agent": random.choice(USER_AGENTS)}  # Rotation
    async with aiohttp.ClientSession(headers=headers) as session:
        query = f"{year} {make} {model} {size} tires"
        tirerack_url = f"https://www.tirerack.com/tires/TireSearchResults.jsp?searchText={query.replace(' ', '+')}&zip-code={zip_code}"
        simpletire_url = f"https://simpletire.com/search?query={query.replace(' ', '%20')}"
        discounttire_url = f"https://www.discounttire.com/search/tires?q={query.replace(' ', '+')}&zip={zip_code}"

        tasks = [
            async_scrape_tirerack(session, tirerack_url),  # Dedicated detailed scraper
            async_scrape_site(session, simpletire_url, "simpletire"),
            async_scrape_site(session, discounttire_url, "discounttire")
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_prices = {}
        for res in results:
            if not isinstance(res, Exception):
                all_prices.update(res)
        return all_prices

def scrape_tire_prices(make, model, year, size, zip_code='90210'):
    cache = load_cache()
    key = f"{make}-{model}-{year}-{size}-{zip_code}"
    
    if is_cache_valid(key, cache):
        return cache[key]['prices']
    
    prices = get_mock_prices(make, model, year, size)
    
    if not prices:
        try:
            prices = asyncio.run(async_scrape_prices(make, model, year, size, zip_code))
        except Exception as e:
            logging.error(f"Async scrape error: {str(e)}")
            prices = {}
        
        if not prices:
            prices = {"Fallback Tire": 199.99}
    
    recommendation = ""
    if not size or size.lower() == 'unknown':
        recommendation = get_recommended_tire_sizes(make, model, year) + "\n"
    
    cache[key] = {
        'prices': prices,
        'timestamp': datetime.now().isoformat()
    }
    save_cache(cache)
    
    time.sleep(1)  # Polite delay
    return prices if not recommendation else recommendation + str(prices)

# Manual update
if __name__ == "__main__":
    print("🛠️ Updating price cache...")
    scrape_tire_prices("Toyota", "Camry", "2023", "19-inch", "90210")
    scrape_tire_prices("Honda", "Accord", "2022", "18-inch", "10001")
    print("✅ Cache updated!")