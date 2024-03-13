import discord
from discord.ext import commands
import requests
from bs4 import BeautifulSoup

# Define intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.command(name='price')
async def get_price(ctx, *, product):
    # This constructs the URL for Amazon's search results page based on the user's specified product.
    # It replaces spaces with "+" to form a valid URL.
    url = f'https://www.amazon.co.uk/s?k={product.replace(" ", "+")}'
    
    headers = {
        'User-Agent': 'Your User Agent Here',
    }
    
    # This line sends an HTTP GET request to the Amazon URL to fetch the HTML content of the page.
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        # It parses the HTML content using BeautifulSoup to extract relevant information.
        # price_element is assigned the element that contains the price information on the Amazon page, if found.
        soup = BeautifulSoup(response.text, 'html.parser')
        price_element = soup.find('span', {'class': 'a-price-whole'})
        # If the price element is found, it retrieves the price text and sends it as a message in the Discord channel.
        if price_element:
            price = price_element.get_text()
            await ctx.send(f'The price of {product} is £{price}')
        else:
            # If the price element is not found, it sends a message indicating that the price was not found.
            await ctx.send('Price not found.')
    else:
        await ctx.send('Failed to fetch data from Amazon.')

bot.run('MTIxMjA1NjA0NzIzNDMyMjQ5Mg.G1tIwh.2VbYZJOLz2KyoJ1Us3F6JWrcU6Wl4erWmvC3eo')
