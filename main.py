
TOKEN = 'MTIxMDE3MzY5NzA5NzMzNDg0NQ.GwXM-Z.L-Hy_1N7FVzJTWrlgWaz5nhIXCgz-rlUtybVCI'

import discord
import sqlite3
from discord import app_commands
from discord.ext import tasks, commands
import asyncio
import requests
from bs4 import BeautifulSoup


intents = discord.Intents.all()
intents.message_content = True
intents.members = True
#bot = commands.Bot(command_prefix='/', intents=intents)
bot = commands.Bot(command_prefix='!', intents=intents)
bot.remove_command("help")

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

    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')

    await bot.process_commands(message)

@bot.tree.command(name="help")
async def help(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hey! I'm the discord bot for Thematic Project, from Faheem, Maiko, Farjana, Zakariya, Andrea, Alex, Harris\n"
                               f"I'm here to help you build a PC (coming soon)")
    

# Function to query CPUs based on filters. for cpu database
def query_cpus(price_range, brand=None, core_clock=None, core_count=None):
    conn = sqlite3.connect('database/cpu.db')
    cursor = conn.cursor()

    # Construct the SQL query based on the brand and other filters
    query = "SELECT name, price FROM cpu WHERE name LIKE ? AND price BETWEEN ? AND ?"
    params = ('%' + brand + '%', price_range[0], price_range[1])


    
    if core_clock:
        query += " AND core_clock >= ?"
        params += (core_clock,)

    if core_count:
        query += " AND core_count >= ?"
        params += (core_count,)

    query += " ORDER BY price DESC"  # Sort by descending price

    cursor.execute(query, params)
    cpus = cursor.fetchall()

    conn.close()

    return cpus


async def ask_for_preferences(ctx):
    await ctx.send("What is your minimum price range?")
    min_price_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    min_price = float(min_price_msg.content)

    await ctx.send("What is your maximum price range?")
    max_price_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    max_price = float(max_price_msg.content)

    await ctx.send("Which brand do you prefer? (Intel/AMD)")
    brand_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    brand = brand_msg.content.lower()

    # Check if the input brand is contained within the CPU brand information
    if not any(brand_name in brand for brand_name in ['intel', 'amd']):
        await ctx.send("Invalid brand. Please choose either 'Intel' or 'AMD'.")
        return await ask_for_preferences(ctx)

    await ctx.send("What is the minimum core clock speed you prefer? (Enter 'None' if not specified)")
    core_clock_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    core_clock = float(core_clock_msg.content) if core_clock_msg.content.lower() != 'none' else None

    await ctx.send("What is the minimum core count you prefer? (Enter 'None' if not specified)")
    core_count_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    core_count = int(core_count_msg.content) if core_count_msg.content.lower() != 'none' else None

    return min_price, max_price, brand, core_clock, core_count



# Function to chunk a list into smaller lists
def chunk_list(lst, n):
    return [lst[i:i + n] for i in range(0, len(lst), n)]



async def display_cpu_results(ctx, cpus):
    

    chunked_cpus = [cpus[i:i + 5] for i in range(0, len(cpus), 5)]
    current_page = 0
   
    embed = discord.Embed(title="Filtered CPUs", color=discord.Color.blue())

    for cpu in chunked_cpus[current_page]:
        embed.add_field(name=cpu[0], value=f"Price: £ {cpu[1]}", inline=False)

    message = await ctx.send(embed=embed)
    await message.add_reaction("⬅️")
    await message.add_reaction("➡️")

    def check(reaction, user):
        return user == ctx.author and reaction.message == message and str(reaction.emoji) in ["⬅️", "➡️"]

    async def on_reaction(reaction, user):
        nonlocal current_page

        if str(reaction.emoji) == "➡️" and current_page < len(chunked_cpus) - 1:
            current_page += 1
        elif str(reaction.emoji) == "⬅️" and current_page > 0:
            current_page -= 1

        new_embed = discord.Embed(title="Filtered CPUs", color=discord.Color.blue())

        for cpu in chunked_cpus[current_page]:
            new_embed.add_field(name=cpu[0], value=f"Price: £ {cpu[1]}", inline=False)

        await message.edit(embed=new_embed)

    bot.add_listener(on_reaction, 'on_reaction_add')

    try:
        await bot.wait_for('reaction_add', timeout=600, check=check)
    except asyncio.TimeoutError:
        await message.clear_reactions()


@bot.command()
async def filter(ctx):
    min_price, max_price, brand, core_clock, core_count = await ask_for_preferences(ctx)
    cpus = query_cpus((min_price, max_price), brand, core_clock, core_count)

    if cpus:
        await display_cpu_results(ctx, cpus)


# This command is called after a CPU has been chosen to start the motherboard selection
@bot.command()
async def start_motherboard_selection(ctx):
    await filter_motherboards(ctx)
# motherboard database section
    
    

# Function to query motherboards based on filters
def query_motherboards(price_range, screen_size=None, resolution=None, refresh_rate=None, response_time=None, panel_type=None, aspect_ratio=None):
    conn = sqlite3.connect('database/cpu.db')
    cursor = conn.cursor()

    # Construct the SQL query based on the filters
    query = "SELECT name, price FROM motherboard WHERE price BETWEEN ? AND ?"
    params =  ( price_range[0], price_range[1],
        '%' + screen_size + '%', 
        '%' + resolution + '%', 
        '%' + str(refresh_rate) + '%', 
        '%' + str(response_time) + '%', 
        '%' + panel_type + '%', 
        '%' + aspect_ratio + '%')

    if screen_size:
        query += " AND screen_size LIKE ? "
        

    if resolution:
        query += " AND resolution LIKE ? "
        

    if refresh_rate:
        query += " AND refresh_rate LIKE ?"
      

    if response_time:
        query += " AND response_time LIKE  ?"
       

    if panel_type:
        query += " AND panel_type LIKE ?"
       

    if aspect_ratio:
        query += " AND aspect_ratio LIKE ?"
       

    query += " ORDER BY price DESC"

    cursor.execute(query, params)
    motherboards = cursor.fetchall()

    conn.close()

    return motherboards



async def ask_for_motherboard_preferences(ctx):
    await ctx.send("What is your minimum price range for the motherboard?")
    min_price_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    min_price = float(min_price_msg.content)

    await ctx.send("What is your maximum price range for the motherboard?")
    max_price_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    max_price = float(max_price_msg.content)

    await ctx.send("What screen size are you looking for? (Please choose from: 15, 17, 18, 19, 21, 23, 24, 26, 27, 28, 29, 31, 32, 34, 38, 40, 43, 44, 45, 47, 48, 49, 55, 57 '27')")
    screen_size_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    screen_size = screen_size_msg.content

    await ctx.send("What resolution are you looking for? (Please choose from: '1024,768', '1280,1024', 1360,768', '1440,900', '1600,900', '1680,1050', '1920,1080', '2560,1440', '2560,2880', 3440,1440', \n '3840,1600', 3840, 2160', '5120,1440', '5120,2160', '5120,2880', '7680,2160', '7680,4320' )")
    resolution_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    resolution = resolution_msg.content

    await ctx.send("What refresh rate are you looking for? (Please choose from: 60, 75, 100, 120, 138, 144, 165, 170, 180, 185, 200, 220, 240, 270, 280, 300, 360, 380, 390, 500, 540 )")
    refresh_rate_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    refresh_rate = refresh_rate_msg.content

    await ctx.send("What is the maximum response time you are willing to accept? (Max: 20)")
    response_time_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    response_time = response_time_msg.content

    # Define allowed panel types
    allowed_panel_types = ['OLED', 'IPS', 'TN', 'QD-OLED', 'VA', 'mini LED IPS', 'Nano IPS']

    # Ask for the panel type and ensure it's one of the allowed options
    while True:
        await ctx.send(f"What panel type are you looking for? Choose from the following: {', '.join(allowed_panel_types)}")
        panel_type_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
        panel_type = panel_type_msg.content.strip()  # Strip whitespace for a cleaner comparison

        if panel_type in allowed_panel_types:
            break  # Exit the loop if the panel type is allowed
        else:
            await ctx.send("Invalid panel type selected. Please choose from the allowed options.")

    await ctx.send("What aspect ratio are you looking for? Choose between '8:9','12:5','16:9','16:10', '21:9','32:9','64:27')")
    aspect_ratio_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    aspect_ratio = aspect_ratio_msg.content

    # Return all the preferences collected
    return (min_price, max_price), screen_size, resolution, refresh_rate, response_time, panel_type, aspect_ratio



async def display_motherboard_results(ctx, motherboards):
    # Divide motherboards into pages
    pages = [motherboards[i:i + 5] for i in range(0, len(motherboards), 5)]
    current_page = 0
    # Setup the initial embed
    embed = discord.Embed(title="Filtered Motherboards", color=discord.Color.blue())

    for motherboard in pages[current_page]:
        embed.add_field(name=motherboard[0], value=f"Price: £{motherboard[1]}", inline=False)

    # Send the first page
    message = await ctx.send(embed=embed)
    await message.add_reaction("⬅️")
    await message.add_reaction("➡️")

    def check(reaction, user):
        return user == ctx.author and reaction.message == message and str(reaction.emoji) in ["⬅️", "➡️"]
    
    async def on_reaction(reaction, user):
        nonlocal current_page

        if str(reaction.emoji) == "➡️" and current_page < len(pages) - 1:
            current_page += 1
        elif str(reaction.emoji) == "⬅️" and current_page > 0:
            current_page -= 1
    
        new_embed = discord.Embed(title="Filtered Motherboards", color=discord.Color.blue())
        for motherboard in pages[current_page]:
                    new_embed.add_field(name=motherboard[0], value=f"Price: £{motherboard[1]}", inline=False)

        await message.edit(embed=new_embed)

        bot.add_listener(on_reaction, 'on_reaction_add')

        try:
            await bot.wait_for('reaction_add', timeout=600, check=check)
        except asyncio.TimeoutError:
            await message.clear_reactions()


@bot.command()
async def filter_motherboards(ctx):
    price_range, screen_size, resolution, refresh_rate, response_time, panel_type, aspect_ratio = await ask_for_motherboard_preferences(ctx)
    motherboards = query_motherboards(price_range, screen_size, resolution, refresh_rate, response_time, panel_type, aspect_ratio)

    if motherboards:
        await display_motherboard_results(ctx, motherboards)




#ram filtering
        #connection with ram table
def query_ram(price, speed, color, first_word_latency, cas_latency):
    conn = sqlite3.connect('database/cpu.db')  # Use the correct path to your database file
    cursor = conn.cursor()
    query = """SELECT name, price FROM memory_ram WHERE price <= ? AND speed = ? 
               AND color LIKE ? AND first_word_latency <= ? AND cas_latency <= ?"""
    # Note that we're assuming color is a partial match but speed is an exact match
    params = (price, speed, f'%{color}%', first_word_latency, cas_latency)
    
    cursor.execute(query, params)
    rams = cursor.fetchall()
    conn.close()
    return rams

    
async def ask_for_ram_preferences(ctx):
    await ctx.send("What maximum price are you looking for in a RAM? (e.g., 150)")
    price_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    price = float(price_msg.content)  # Convert to float
    

    await ctx.send("What minimum speed (in MHz) are you looking for? (e.g., 3200)")
    speed_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    speed = int(speed_msg.content)
    

    await ctx.send("What color are you looking for?")
    color_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    color = color_msg.content  # Keep as string

    await ctx.send("What maximum first word latency are you looking for? (e.g., 19)")
    fwl_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    first_word_latency = int(fwl_msg.content)  # Convert to int
    

    await ctx.send("What maximum CAS latency are you looking for? (e.g., 16)")
    cas_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    cas_latency = int(cas_msg.content)  # Convert to int
    

    return  price, speed, color, first_word_latency,cas_latency

    

async def display_ram_results(ctx, rams):
    # Divide RAM results into chunks of 5 for pagination
    chunked_rams = [rams[i:i + 5] for i in range(0, len(rams), 5)]
    current_page = 0

    # Setup the initial embed with the first page of RAM results
    embed = discord.Embed(title="Filtered RAMs", color=discord.Color.blue())
    for ram in chunked_rams[current_page]:
        embed.add_field(name=ram[0], value=f"Price: £{ram[1]}", inline=False)

    message = await ctx.send(embed=embed)
    await message.add_reaction("⬅️")
    await message.add_reaction("➡️")

    def check(reaction, user):
        
        return user == ctx.author and reaction.message == message and str(reaction.emoji) in ["⬅️", "➡️"]


    async def on_reaction(reaction, user):
        nonlocal current_page
        

        if str(reaction.emoji) == "➡️" and current_page < len(chunked_rams) - 1:
            current_page += 1
        elif str(reaction.emoji) == "⬅️" and current_page > 0:
            current_page -= 1

        # Update the embed with the new page of RAM results
        new_embed = discord.Embed(title="Filtered RAMs", color=discord.Color.blue())
        for ram in chunked_rams[current_page]:
            new_embed.add_field(name=ram[0], value=f"Price: £{ram[1]}", inline=False)

        await message.edit(embed=new_embed)
          

        bot.add_listener(on_reaction, 'on_reaction_add')

        try:
            await bot.wait_for('reaction_add', timeout=600, check=check)
        except asyncio.TimeoutError:
            await message.clear_reactions()

@bot.command(name='filter_ram')
async def filter_ram(ctx):
    price, speed, color, first_word_latency, cas_latency = await ask_for_ram_preferences(ctx)
    
    # Ensure data types are correct for the database query
    # Convert string inputs to the appropriate numeric types if needed
    try:
        price = float(price)
        speed = int(speed)  # Assuming speed is also an integer value like MHz
        first_word_latency = int(first_word_latency)
        cas_latency = int(cas_latency)
    except ValueError as e:
        await ctx.send(f"An error occurred with the input: {e}. Please make sure to enter numbers for price, speed, first word latency, and CAS latency.")
        return

    rams = query_ram(price, speed, color, first_word_latency, cas_latency)
    if rams:
        await display_ram_results(ctx, rams)
    else:
        await ctx.send("No RAMs found matching the specified criteria.")


# needed for add command
def filter_cpus_by_name(name):
    # Connect to the database and query for CPUs by name
    conn = sqlite3.connect('database/cpu.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM cpu WHERE name = ?", (name,))
    cpus = cursor.fetchall()
    conn.close()
    return cpus

def filter_motherboards_by_name(name):
    # Connect to the database and query for motherboards by name
    conn = sqlite3.connect('database/cpu.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM motherboard WHERE name = ?", (name,))
    motherboards = cursor.fetchall()
    conn.close()
    return motherboards

def filter_rams_by_name(name):
    conn = sqlite3.connect('database/cpu.db')  # Modify as needed to connect to your database
    cursor = conn.cursor()
    # Use "LIKE" operator for fields where partial matches are acceptable
    cursor.execute("SELECT name FROM memory_ram WHERE name = ?", (name,))
    rams = cursor.fetchall()
    conn.close()
    return rams


# Define a command for adding a component
@bot.command(name='add')
async def add_component(ctx, *, component_name: str):
    # First try to match the component name with CPUs
    cpus = filter_cpus_by_name(component_name)
    if cpus:
        # Assuming the query returns a list of tuples, we'll take the first match
        cpu_chosen = cpus[0][0]  # This gets the name of the first CPU found
        await ctx.send(f"You have chosen the CPU: {cpu_chosen}.")
        return
    
    # If not found in CPUs, try to match with motherboards
    motherboards = filter_motherboards_by_name(component_name)
    if motherboards:
        # Similarly, take the first match
        motherboard_chosen = motherboards[0][0]  # This gets the name of the first motherboard found
        await ctx.send(f"You have chosen the Motherboard: {motherboard_chosen}.")
        return
    
    # If the component is not found in CPUs, motherboards, or RAM
    rams = filter_rams_by_name(component_name)
    if rams:
        # Similarly, take the first match
        ram_chosen = rams[0][0]  # This gets the name of the first RAM found
        await ctx.send(f"You have chosen the RAM: {ram_chosen}.")
        return

    # If the component is not found in either CPUs or motherboards
    await ctx.send("No component found matching this criteria.")


# Command for cpu filtering
@bot.command(name='cpu')
async def cpu_filter(ctx):
    await ctx.send("You will get asked a range of questions for us to filter the cpus for your desired results.")
    await filter.invoke(ctx)  # Run the filter command to suggest a PC

# Command for motherboard filtering
@bot.command(name='motherboard')
async def motherboard_filter(ctx):
    await ctx.send("You will get asked a range of questions for us to filter the motherboard for your desired results.")
    await start_motherboard_selection(ctx)  # Start the motherboard selection process       

@bot.command(name='ram')
async def ram_filter(ctx):
    await ctx.send("You will get asked a range of questions for us to filter the RAM for your desired results.")
    await ask_for_ram_preferences(ctx)  # Make sure to define this function to ask user preferences for RAM

#command for displaying the most commonly used cpus
@bot.command()
async def popularcpus(ctx):
    url = "https://www.cpubenchmark.net/common_cpus.html"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        cpu_list = []
        # find CPU elements and extract relevant data
        cpu_container = soup.find('ul', class_='chartlist')
        if cpu_container:
            for cpu in cpu_container.find_all('a'):
                model = cpu.find('span', class_='prdname').text.strip()
                count_str = cpu.find('span', class_='count').text.strip().replace(',', '')  # remove commas from the count string
                price_str = cpu.find('span', class_='price-neww').text.strip().replace('$', '')  # extract price
                link = "https://www.cpubenchmark.net/" + cpu['href']  # extract link
                # check if count and price are numeric
                if count_str.isdigit() and price_str.replace('.', '').isdigit():
                    # convert count to int
                    count = int(count_str)
                    # convert price to float
                    price = float(price_str)
                    # append CPU model, count, and price to the list
                    cpu_list.append((model, count, price, link))
                else:
                    cpu_list.append((model, 0, 0.0, link))  # assign a count and price of 0 if not numeric

            # process CPU data to find the top 10 most common CPUs based on count (benchmark score)
            cpu_list.sort(key=lambda x: x[1],
                          reverse=True)  # sort CPU list by count (benchmark score) in descending order
            top_cpus = cpu_list[:10]  # get the top 10 most common CPUs

            # create and send an embed with the top 10 CPUs
            embed = discord.Embed(title="Top 10 current most common CPUs based on CPU Benchmark Score",
                                  description="Here are the top 10 CPUs based on CPU Benchmark Score:")
            for rank, cpu in enumerate(top_cpus, start=1):
                embed.add_field(name=f"{rank}. {cpu[0]}",
                                value=f"Benchmark Score: {cpu[1]}, Price: £{cpu[2]:.2f}\n[CPU Benchmark Link]({cpu[3]})",
                                inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send("Failed to find CPU data on the website.")
    else:
        await ctx.send("Failed to fetch CPU data from the website.")

bot.run(TOKEN)