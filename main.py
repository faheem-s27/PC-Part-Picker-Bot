
TOKEN = 'MTIxMDE3MzY5NzA5NzMzNDg0NQ.GwXM-Z.L-Hy_1N7FVzJTWrlgWaz5nhIXCgz-rlUtybVCI'

import discord
import sqlite3
from discord import app_commands
from discord.ext import tasks, commands
import asyncio


intents = discord.Intents.all()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='/', intents=intents)
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
    await ctx.send("Please click the ➡️ reaction to see more CPU options and to also see more dialogue to answer more questions. ")
   
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

    


async def get_cpu_preference(ctx, cpus):
    # Display the message prompting the user for their CPU choice
    await ctx.send("Please type the name of the CPU you want to choose from the list.")
    
    while True:
        # Wait for the user's response
        cpu_preferred_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
        cpu_name = cpu_preferred_msg.content.strip()  # Get the content of the message and strip any whitespace
        
        # Iterate over the list of CPUs to find a match
        for cpu in cpus:
            if cpu_name.lower() == cpu[0].lower():  # Compare case-insensitively
                return cpu_name  # Return the CPU name if it matches
                
        # If the CPU name isn't found, notify the user and prompt for input again
        await ctx.send("The CPU you typed is not in the list. Please ensure you type the name exactly as it appears.")


@bot.command()
async def filter(ctx):
    min_price, max_price, brand, core_clock, core_count = await ask_for_preferences(ctx)
    cpus = query_cpus((min_price, max_price), brand, core_clock, core_count)

    if cpus:
        await display_cpu_results(ctx, cpus)
        cpu_chosen = await get_cpu_preference(ctx, cpus)
        if cpu_chosen:
            await ctx.send(f"You have chosen {cpu_chosen}. Now, let's select a motherboard.")
            await start_motherboard_selection(ctx)  # Start the motherboard selection process
    else:
        await ctx.send("No CPUs found matching the specified criteria.")



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
    await ctx.send("Please click the ➡️ reaction to see more Motherboard options and to also see more dialogue to answer more questions. ")
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

async def get_motherboard_preference(ctx, motherboards):
    # Ask the user for their preferred motherboard
    await ctx.send("Please type the name of the motherboard you want to choose from the list.")

    while True:
        msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)

        # Check if the name is in the list of motherboards
        motherboard_name = msg.content.strip()
        for motherboard in motherboards:
            if motherboard_name.lower() == motherboard[0].lower():
                return motherboard_name  # Return the selected motherboard name

        # If the motherboard name isn't found, notify the user
        await ctx.send("The motherboard you typed is not in the list. Please ensure you type the name exactly as it appears in the list.")


@bot.command()
async def filter_motherboards(ctx):
    price_range, screen_size, resolution, refresh_rate, response_time, panel_type, aspect_ratio = await ask_for_motherboard_preferences(ctx)
    motherboards = query_motherboards(price_range, screen_size, resolution, refresh_rate, response_time, panel_type, aspect_ratio)

    if motherboards:
        await display_motherboard_results(ctx, motherboards)
        motherboard_chosen = await get_motherboard_preference(ctx, motherboards)
        if motherboard_chosen:
            await ctx.send(f"You have chosen {motherboard_chosen}")
    else:
        await ctx.send("No motherboards found matching the specified criteria.")





# Command to ask user whether they want to build their own PC or get suggested one
@bot.command(name='start')
async def start(ctx):
    await ctx.send("Press 1 if you want to build your own PC or press 2 if you want to get suggested a PC.")

    def check(message):
        return message.author == ctx.author and message.content in ['1', '2']

    choice_msg = await bot.wait_for('message', check=check)
    choice = int(choice_msg.content)

    if choice == 1:
        await ctx.send("You chose to build your own PC!")
        # Implement the logic for building your own PC
    elif choice == 2:
        await ctx.send("You chose to get suggested a PC!")
        await filter.invoke(ctx)  # Run the filter command to suggest a PC
    else:
        await ctx.send("Invalid choice. Please press 1 or 2.")
        


bot.run(TOKEN)