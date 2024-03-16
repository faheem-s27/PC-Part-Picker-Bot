import requests
from bs4 import BeautifulSoup

EBAY_SEARCH_URL = "https://www.ebay.co.uk/sch/164/i.html?_nkw={}"  # eBay search URL template fot CPU
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0'  # User agent string

def extract_price_from_element(price_element):
    prices = [item.strip() for item in price_element.strings if item.strip()]
    if len(prices) == 1:
        return prices[0]
    elif len(prices) > 1:
        return f"{prices[0]} to {prices[-1]}"
    else:
        return None
    
def extract_image_links(item):
    # Find the image section within the item
    image_section = item.find('div', class_='s-item__image-section')
    if image_section:
        # Extract image links from img tags within the image section
        return [img_tag.get('data-defer-load') or img_tag.get('src') for img_tag in image_section.find_all('img')]
    return []

def scrape_ebay(item):
    try:
        search_url = EBAY_SEARCH_URL.format(item.replace(' ', '+'))
        response = requests.get(search_url, headers={'User-Agent': USER_AGENT})
        
        # Check if the request was successful (status code 200)
        response.raise_for_status()
        # Parse the response content with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find all item containers on the search page
        items = soup.find_all('div', class_='s-item__wrapper clearfix')
        # Check if at least two items are found
        if items and len(items) > 1:
            first_item = items[1]
            # Extract the price from the second item
            price_element = first_item.find('span', class_='s-item__price')
            price = extract_price_from_element(price_element)
            # Extract image links from the second item
            image_links = extract_image_links(first_item)
            if price:
                return f'The price of {item} on eBay UK is {price}', f'{", ".join(image_links)}', f'eBay search URL: {search_url}'
            else:
                return 'Price not found.', f'Image links: {", ".join(image_links)}', f'eBay search URL: {search_url}'
        else:
            return 'Not enough items found to extract the second price.', None, f'eBay search URL: {search_url}'
    except requests.RequestException as e:
        # Handle request exceptions and return error message along with eBay search URL
        return f'Failed to fetch data from eBay: {e}', None, f'eBay search URL: {search_url}'

# # Example usage: Intel Core i7-950, Intel Core i5-8500T, Intel Core i5-2500, AMD Ryzen 7 5800X
# cpu_model = "AMD A12-9800"
# price_info, image_links_info, search_url_info = scrape_ebay(cpu_model)
# sep = "-" * 100
# print(f"{sep}\n{search_url_info}\n{price_info}\n{image_links_info}\n{sep}")
