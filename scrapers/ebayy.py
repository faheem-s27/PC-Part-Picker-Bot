import requests
from bs4 import BeautifulSoup

def extract_price_from_element(price_element):
    """Extracts the price or price range from the price element."""
    prices = []
    for item in price_element.strings:
        stripped_item = item.strip()
        if stripped_item:  # Exclude empty strings
            prices.append(stripped_item)
    # If there's only one price, return it. Otherwise, return the first and last prices for the range.
    if len(prices) == 1:
        return prices[0]
    elif len(prices) > 1:
        return f"{prices[0]} to {prices[-1]}"
    else:
        return None
    
def extract_image_link(item):
    """Extracts the image link from the item."""
    image_wrapper_div = item.find('div', class_='s-item__image-wrapper')
    if image_wrapper_div:
        image_tag = image_wrapper_div.find('img')
        if image_tag:
            if 'data-defer-load' in image_tag.attrs:
                return image_tag['data-defer-load']
            elif 'src' in image_tag.attrs:
                return image_tag['src']
    return None

def scrape_ebay_price(product):
    search_url = f"https://www.ebay.co.uk/sch/164/i.html?_nkw={product.replace(' ', '+')}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:97.0) Gecko/20100101 Firefox/97.0',
    }
    response = requests.get(search_url, headers=headers)
    if response.status_code == 200:
        # Print the URL of the eBay search page
        print("eBay search page URL:", search_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        # Find all item containers on the search page
        items = soup.find_all('div', class_='s-item__info')
        if items and len(items) > 1:  # Ensure at least two items are found
            # Extract the first item (index 1) from the search results (index 0 just reterns the price as 20$ for some reason)
            first_item = items[1]
            # Extract the price from the second item
            price_element = first_item.find('span', class_='s-item__price')
            price = extract_price_from_element(price_element)
            # Extract the image link from the second item
            image_link = extract_image_link(first_item)
            return f'The price of {product} on eBay UK is {price}', image_link, soup
        else:
            return 'Not enough items found to extract the second price.', None, soup
    else:
        return 'Failed to fetch data from eBay.', None, None

# Example usage: Intel Core i7-950, Intel Core i5-8500T, Intel Core i5-2500, AMD Ryzen 7 5800X
product = "Intel Core i5-8500T"
price_info, image_link, soup = scrape_ebay_price(product)
print(price_info)
# Check if the image link is available before printing
if image_link:
    print("Image link:", image_link)
else:
    print("Image link not found.")