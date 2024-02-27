
TOKEN = 'MTIxMDE3MzY5NzA5NzMzNDg0NQ.GwXM-Z.L-Hy_1N7FVzJTWrlgWaz5nhIXCgz-rlUtybVCI'


import discord
import sqlite3
from discord import app_commands
from discord.ext import tasks, commands


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

# @bot.command()
# async def help(ctx):
#     await ctx.send("Hey! I'm the discord bot for Thematic Project, from Faheem, Maiko, Farjana, Zakariya, Andrea, Alex, Harris")
#     await ctx.send("I'm here to help you build a PC (coming soon)")
@bot.tree.command(name="help")
async def help(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hey! I'm the discord bot for Thematic Project, from Faheem, Maiko, Farjana, Zakariya, Andrea, Alex, Harris\n"
                               f"I'm here to help you build a PC (coming soon)")
    
# db = sqlite3.connect('database/cpu.db')
# cursor = db.cursor()

# cursor.execute('''SELECT name 
#                   FROM cpu
#                   WHERE price = 96.99; ''')

# row = cursor.fetchone()
# print(row)

# Function to query CPUs based on filters
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

    cursor.execute(query, params)
    cpus = cursor.fetchall()

    conn.close()

    return cpus

# Function to interactively ask the user for preferences
# Function to interactively ask the user for preferences
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

# Command to filter CPUs
@bot.command()
async def filter(ctx):
    min_price, max_price, brand, core_speed = await ask_for_preferences(ctx)
    cpus = query_cpus((min_price, max_price), brand, core_speed)

    if cpus:
        for cpu in cpus:
            await ctx.send(f"Name: {cpu[0]}, Price: {cpu[1]}")
    else:
        await ctx.send("No CPUs found matching the specified criteria.")

# # Command to ask user whether they want to build their own PC or get suggested one
# @bot.command(name='start')
# async def start(ctx):
#     await ctx.send("Press 1 if you want to build your own PC or press 2 if you want to get suggested a PC.")

#     def check(message):
#         return message.author == ctx.author and message.content in ['1', '2']

#     choice_msg = await bot.wait_for('message', check=check)
#     choice = int(choice_msg.content)

#     if choice == 1:
#         await ctx.send("You chose to build your own PC!")
#         # Implement the logic for building your own PC
#     elif choice == 2:
#         await ctx.send("You chose to get suggested a PC!")
#         await filter.invoke(ctx)  # Run the filter command to suggest a PC
#     else:
#         await ctx.send("Invalid choice. Please press 1 or 2.")
        
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
        min_price, max_price, brand, core_clock, core_count = await ask_for_preferences(ctx)
        cpus = query_cpus((min_price, max_price), brand, core_clock, core_count)

        if cpus:
            for cpu in cpus:
                await ctx.send(f"Name: {cpu[0]}, Price: {cpu[1]}")
        else:
            await ctx.send("No CPUs found matching the specified criteria.")
    else:
        await ctx.send("Invalid choice. Please press 1 or 2.")

bot.run(TOKEN)