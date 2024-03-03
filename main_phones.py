
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

# @bot.command()
# async def help(ctx):
#     await ctx.send("Hey! I'm the discord bot for Thematic Project, from Faheem, Maiko, Farjana, Zakariya, Andrea, Alex, Harris")
#     await ctx.send("I'm here to help you build a PC (coming soon)")
@bot.tree.command(name="help")
async def help(interaction: discord.Interaction):
    await interaction.response.send_message(f"Hey! I'm the discord bot for Thematic Project, from Faheem, Maiko, Farjana, Zakariya, Andrea, Alex, Harris\n"
                               f"I'm here to help you build a PC (coming soon)")
    

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

    return min_price, max_price, brand, core_clock



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

    await ctx.send("What CPU from this list do you want to choose?")

        

# Command to filter CPUs
# @bot.command()
# async def filter(ctx):
#     min_price, max_price, brand, core_speed = await ask_for_preferences(ctx)
#     cpus = query_cpus((min_price, max_price), brand, core_speed)

#     if cpus:
#         await display_cpu_results(ctx, cpus)
#     else:
#         await ctx.send("No CPUs found matching the specified criteria.")
#     cpuChosen = getCpuPreferrence(ctx)
#     cpuIsInList = False
#     for cpu in cpus:
#         if cpu == cpuChosen:
#             cpuIsInList = True
#             break
#     if cpuIsInList == True:
#         await ctx.send(f"You have chosen {cpuChosen}")
#     else:
#         await ctx.send("This cpu is not in the list.")

    
# async def getCpuPreferrence(ctx):
#     await ctx.send("What cpu from this list do you want to choose?")
#     cpu_preferred_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
#     return cpu_preferred_msg

@bot.command()
async def filter(ctx):
    min_price, max_price, brand, core_speed = await ask_for_preferences(ctx)
    cpus = query_cpus((min_price, max_price), brand, core_speed)

    if cpus:
        await display_cpu_results(ctx, cpus)
        cpu_chosen = await get_cpu_preference(ctx, cpus)  # Call the function to get CPU preference
        if cpu_chosen:
            await ctx.send(f"You have chosen {cpu_chosen}")
        
            
    else:
        await ctx.send("No CPUs found matching the specified criteria.")

async def get_cpu_preference(ctx, cpus):
    print("Inside get_cpu_preference function")  # Add this line to indicate that the function is being executed
    while True:
        await ctx.send("What CPU from this list do you want to choose?")
        cpu_preferred_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
        cpu_name = cpu_preferred_msg.content.strip()  # Get the content of the message
        print("Received CPU name input:", cpu_name)  # Add this line to print the received CPU name
        for cpu in cpus:
            if cpu_name == cpu[0]:  # Check if the CPU name matches any CPU in the list
                print("CPU chosen:", cpu[0])  # Add this line to print the chosen CPU
                return cpu[0]  # Return the CPU name if it matches
        print("CPU not found in the list")  # Add this line to indicate that the CPU was not found
        await ctx.send("This cpu is not in the list")






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