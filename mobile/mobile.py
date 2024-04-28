import asyncio
import io
import json
import os

import discord
import requests
from PIL import Image
from bs4 import BeautifulSoup
from discord.ext import commands
from fuzzywuzzy import fuzz

intents = discord.Intents.all()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command("help")

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/91.0.4472.124 Safari/537.36'}

TOKEN = 'MTIxMDE3MzY5NzA5NzMzNDg0NQ.GwXM-Z.L-Hy_1N7FVzJTWrlgWaz5nhIXCgz-rlUtybVCI'


# Function to load the list of important keys from a configuration file
def load_important_keys():
    try:
        with open('important_keys.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []


# check if the important keys are set
async def check_important_keys(ctx):
    important_keys = load_important_keys()
    if len(important_keys) == 0:
        await ctx.send("You haven't set any keys yet. Use the `!set_keys` command to set the list of "
                       "keys.")
        return False
    return True


# Function to save the list of important keys to a configuration file
def save_important_keys(important_keys):
    with open('important_keys.json', 'w') as f:
        json.dump(important_keys, f, indent=4)


@bot.command()
async def help(ctx):
    embed = discord.Embed(title="Mobile Bot Help", color=discord.Color.blue())
    embed.add_field(name="!spec {phone model}", value="Get the specifications of a phone model saved locally.",
                    inline=False)
    embed.add_field(name="!search {phone model}", value="Search for a phone model online and save to JSON.",
                    inline=False)
    embed.add_field(name="!set_keys {key1} {key2} ...", value="Set the list of important keys for the phone specs.",
                    inline=False)
    await ctx.send(embed=embed)


# Command to set the list of important keys globally
@bot.command()
async def set_keys(ctx, *keys):
    if len(keys) == 0:
        await ctx.send("Please provide a list of keys such as CPU, GPU, Memory etc etc.")
        return
    replaced_keys = []
    for key in keys:
        if key.lower() == "headphones":
            replaced_keys.append("3.5mm jack ")
        elif key.lower() == "memory":
            replaced_keys.append("internal")
        elif key.lower() == "battery":
            replaced_keys.append("type")
        else:
            replaced_keys.append(key)

    # all keys
    if "all" in replaced_keys:
        replaced_keys = [
            "all"
        ]

    # Convert replaced keys to lowercase and remove duplicates
    replaced_keys = list(set([key.lower() for key in replaced_keys]))

    # Save the list of keys
    save_important_keys(replaced_keys)

    # Provide information about the keys
    info_message = "List of keys updated.\n\n"
    info_message += "**Keys you can set:**\n"
    info_message += "- Announced: Date when the phone was announced.\n"
    info_message += "- Status: Availability status of the phone.\n"
    info_message += "- Technology: Radios used in the phone.\n"
    info_message += "- SIM: SIM card support in the phone.\n"
    info_message += "- OS: Operating system of the phone.\n"
    info_message += "- Chipset: Processor chipset used in the phone.\n"
    info_message += "- CPU: Central processing unit of the phone.\n"
    info_message += "- GPU: Graphics processing unit of the phone.\n"
    info_message += "- Dimensions: Physical dimensions of the phone.\n"
    info_message += "- Weight: Weight of the phone.\n"
    info_message += "- Resolution: Resolution of the phone.\n"
    info_message += "- Size: Display size of the phone\n"
    info_message += "- Memory: Storage size and RAM of the phone\n"
    info_message += "- Headphones: Whether headphone jack is supported\n"
    info_message += "- Sensors: Displays all the sensors supported\n"
    info_message += "- Battery: Battery specifications of the phone.\n"
    info_message += "- Bluetooth: Bluetooth version supported by the phone\n"
    info_message += "- Colors: Available colors of the phone.\n"
    info_message += "- Price: Price of the phone.\n"
    info_message += "- All: EVERYTHING!!!!!!!!!!!!!\n"

    await ctx.send(info_message)

    # tell them they can use !spec command to see the important keys
    await ctx.send("You can use the `!spec {phone model}` command to see the keys you've set.")


def check(ctx):
    return lambda m: m.author == ctx.author and m.channel == ctx.channel


async def get_input_of_type(func, ctx):
    while True:
        try:
            msg = await bot.wait_for('message', check=check(ctx))
            return func(msg.content)
        except ValueError:
            continue


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    await bot.process_commands(message)


def get_average_color(image_url):
    response = requests.get(image_url)
    image_bytes = io.BytesIO(response.content)
    image = Image.open(image_bytes)
    resized_image = image.resize((1, 1))
    dominant_color = resized_image.getpixel((0, 0))
    return discord.Color.from_rgb(*dominant_color)


async def get_phone_details(ctx, phoneLink, phoneTitle, phoneImage):
    await ctx.send(f"Fetching specs for {phoneTitle}...")
    json_filename = phoneTitle.replace(" ", "").lower() + '.json'
    json_file_path = os.path.join("mobile", json_filename)

    if not await check_important_keys(ctx):
        return

    important_keys = load_important_keys()

    # Check if phone details exist in the JSON file
    if os.path.exists(json_file_path):
        with open(json_file_path, 'r') as f:
            phone_details = json.load(f)

            for specs_dict in phone_details:
                embed = discord.Embed(title=phoneTitle, color=get_average_color(phoneImage))
                embed.set_thumbnail(url=phoneImage)
                embed.set_author(name=phoneTitle, icon_url=phoneImage)
                for key, value in specs_dict.items():
                    if "all" in important_keys:
                        embed.add_field(name=key, value=value, inline=True)
                    elif key.lower() in important_keys:
                        embed.add_field(name=key, value=value, inline=True)
                # Check if any fields are added to the embed
                if len(embed.fields) > 0:
                    await ctx.send(embed=embed)

            # ask the user for the important keys if not set
            await ctx.send("You can set the list of keys using the `!set_keys` command.")
            return

    html = requests.get(phoneLink)
    soup = BeautifulSoup(html.content, 'html.parser')
    # find an id called specs-list
    specs_list = soup.find(id='specs-list')
    # find all the tables in the specs list
    tables = specs_list.find_all('table')

    # Initialize a list to store phone details
    phone_details = []

    # Iterate over each table of specifications
    for table in tables:
        # Initialize a dictionary to store specifications for this table
        specs_dict = {}

        # find all the rows in the table
        rows = table.find_all('tr')
        # iterate over each row
        for row in rows:
            # find all the columns in the row
            cols = row.find_all('td')
            # if the length of the columns is 2
            if len(cols) == 2:
                # Add specification to the dictionary
                specs_dict[cols[0].get_text()] = cols[1].get_text()

        # Append the specifications for this table to the phone details list
        phone_details.append(specs_dict)

    with open(json_file_path, 'w') as f:
        json.dump(phone_details, f, indent=4)

    print(f"Phone details for {phoneTitle} saved to JSON file.")

    # Send phone details from JSON file
    for specs_dict in phone_details:
        embed = discord.Embed(title=phoneTitle, color=get_average_color(phoneImage))
        embed.set_thumbnail(url=phoneImage)
        embed.set_author(name=phoneTitle, icon_url=phoneImage)
        for key, value in specs_dict.items():
            if key in important_keys:
                embed.add_field(name=key, value=value, inline=True)
        # Check if any fields are added to the embed
        if len(embed.fields) > 0:
            await ctx.send(embed=embed)

    # ask the user for the important keys if not set
    await ctx.send("You can set the list of keys using the `!set_keys` command.")


def createDirectory():
    directory = 'mobile'
    if not os.path.exists(directory):
        os.makedirs(directory)
        with open('mobile\phones.json', 'w') as f:
            json.dump([], f)


def checkForBans(headers):
    if "Retry-After" in headers:
        return True
    return False


@bot.command()
async def spec(ctx, *, phone: str):
    await ctx.send(f"Searching for {phone} in JSON data...")

    matching_phones_in_json = []
    file_path = os.path.join("mobile", 'phones.json')
    try:
        with open(file_path, 'r') as f:
            phone_json = json.load(f)
    except FileNotFoundError:
        phone_json = []

    for phone_entry in phone_json:
        similarity_ratio = fuzz.ratio(phone.lower(), phone_entry['title'].lower())
        if similarity_ratio >= 70:
            matching_phones_in_json.append(phone_entry)
            print(f"Similarity ratio for {phone_entry['title']} with {phone.lower()}: {similarity_ratio}")

    if len(matching_phones_in_json) == 0:
        await ctx.send("No matching phones found in JSON data.")
        await ctx.send("To add a phone to the JSON data, use the `!search {phone model}` command.")
        return

    if len(matching_phones_in_json) > 1:
        await ctx.send("Multiple phones found. Please select one from the list below:")
        message = ""
        for i, phone in enumerate(matching_phones_in_json):
            message += f"{i + 1}. {phone['title']}\n"
        await ctx.send(message)
        try:
            response = await get_input_of_type(int, ctx)
            selected_phone = matching_phones_in_json[int(response) - 1]
            await get_phone_details(ctx, selected_phone['href'], selected_phone['title'],
                                    selected_phone['image_source'])
        except:
            await ctx.send("Please try again.")

    else:
        phone = matching_phones_in_json[0]
        await get_phone_details(ctx, phone['href'], phone['title'], phone['image_source'])


@bot.command()
async def search(ctx, *, phone: str):
    phone_details_from_GSM = []
    matching_phones_in_json = []

    search_query = '+'.join(phone.split())
    search_url = f'https://www.gsmarena.com/results.php3?sQuickSearch=yes&sName={search_query}'
    await ctx.send(f'Searching for {phone}...')

    file_path = os.path.join("mobile", 'phones.json')
    try:
        with open(file_path, 'r') as f:
            phone_json = json.load(f)
    except FileNotFoundError:
        phone_json = []

    for phone_entry in phone_json:
        similarity_ratio = fuzz.ratio(phone.lower(), phone_entry['title'].lower())
        print(f"Similarity ratio for {phone_entry['title']} with {phone.lower()}: {similarity_ratio}")
        if similarity_ratio >= 70:  # I found this to be the bestt
            matching_phones_in_json.append(phone_entry)

    if matching_phones_in_json:
        for phone_entry in matching_phones_in_json:
            embed_color = get_average_color(phone_entry['image_source'])
            embed = discord.Embed(title=phone_entry['title'], color=embed_color)
            embed.set_thumbnail(url=phone_entry['image_source'])
            embed.set_author(name=phone_entry['title'], icon_url=phone_entry['image_source'])
            embed.add_field(name="Description", value=phone_entry['desc'], inline=True)
            embed.add_field(name="GSM", value=f"[Specs]({phone_entry['href']})", inline=True)
            await ctx.send(embed=embed)

        await ctx.send(f"Found {len(matching_phones_in_json)} matching phones in JSON data.")
        await ctx.send("Would you like to search online for more results? (Yes/No)")

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel

        try:
            response = await bot.wait_for('message', timeout=30.0, check=check)
            if response.content.lower() == 'no':
                await ctx.send("Okay, I won't search online.")
                return
            elif response.content.lower() == 'yes':
                await ctx.send("Searching online for more results...")
        except asyncio.TimeoutError:
            return
    else:
        await ctx.send("No matching phones found in JSON data. Searching online...")

    html = requests.get(search_url, headers=headers)
    if checkForBans(html.headers):
        retry_after = html.headers["Retry-After"]
        await ctx.send(f"Banned for {retry_after} seconds :(")
        return

    soup = BeautifulSoup(html.content, 'html.parser')
    makers_div = soup.find(class_='makers')

    # Iterate over each phone link
    for link in makers_div.find_all('a', href=True):
        # Extract title, image source, and href
        title_elem = link.find('strong').find('span')
        title_text = title_elem.get_text(separator=' ', strip=True)
        title = title_text.replace('<br/>', ' ')
        image_source = link.find('img')['src']
        href = "https://www.gsmarena.com/" + link['href']
        desc = link.find('img')['title']
        # split the description with full stop and remove the first element
        desc = desc.split('.')
        desc = desc[1:]
        desc = '.'.join(desc)
        phone_details_from_GSM.append({'title': title, 'image_source': image_source, 'href': href, 'desc': desc})

    if len(phone_details_from_GSM) == 0:
        await ctx.send("No phones found. Try searching again with a different query.")
        return

    for phone in phone_details_from_GSM:
        found = False
        for existing_phone in phone_json:
            if phone['title'] == existing_phone['title']:
                print(f"Phone {phone['title']} already exists in JSON.")
                found = True
                break
        if not found:
            phone_json.append(phone)

    # Write the updated JSON data back to the file
    with open('mobile\phones.json', 'w') as f:
        json.dump(phone_json, f, indent=4)

    # Print the phone details
    # for details in phone_details:
    #     print('Title:', details['title'])
    #     print('Image Source:', details['image_source'])
    #     print('Href:', details['href'])
    #     print('Desc:', details['desc'])
    #     print()

    if len(phone_details_from_GSM) > 5:
        await ctx.send(
            f"There are {len(phone_details_from_GSM)} phones found. Would you like to refine your search or display "
            f"all results? (Refine/All)")

        message = await get_input_of_type(str, ctx)
        if message.lower() == 'refine':
            await ctx.send("Please enter the number of the phone you would like to see more details of.")
            message = ""
            for i, phone in enumerate(phone_details_from_GSM):
                message += f"{i + 1}. {phone['title']}\n"
            await ctx.send(message)
            try:
                response = await get_input_of_type(int, ctx)
                await sendPhoneEmbed(ctx, phone_details_from_GSM[response - 1])
            except:
                await ctx.send("Please try again.")

    # each phone detail as a separate embed
    for details in phone_details_from_GSM:
        await sendPhoneEmbed(ctx, details)


async def sendPhoneEmbed(ctx, phone):
    embed = discord.Embed(title=phone['title'], color=get_average_color(phone['image_source']))
    embed.set_thumbnail(url=phone['image_source'])
    embed.set_author(name=phone['title'], icon_url=phone['image_source'])
    embed.add_field(name="Description", value=phone['desc'], inline=True)
    embed.add_field(name="GSM", value=f"[Specs]({phone['href']})", inline=True)
    message = await ctx.send(embed=embed)
    await message.add_reaction("ℹ️")

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) == 'ℹ️'

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)
        if str(reaction.emoji) == 'ℹ️':
            await get_phone_details(ctx, phone['href'], phone['title'], phone['image_source'])
    except asyncio.TimeoutError:
        return


createDirectory()
bot.run(TOKEN)
