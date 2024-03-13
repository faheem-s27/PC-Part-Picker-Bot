TOKEN = 'MTIxMDE3MzY5NzA5NzMzNDg0NQ.GwXM-Z.L-Hy_1N7FVzJTWrlgWaz5nhIXCgz-rlUtybVCI'

import discord
import sqlite3
from discord.ext import tasks, commands
from ebay import scrape_ebay
import asyncio

intents = discord.Intents.all()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    try:
        # Attempt to sync commands (assuming you're using slash commands)
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        # Print any errors encountered during syncing
        print(e)

# Provide helpful information when the user triggers the "help" command
@bot.tree.command(name="help")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(title="Help", description="I'm here to help you build a PC.")
    embed.add_field(name="Commands", value="!cpu - Find CPUs\n!add - Add components to the build", inline=False)
    await interaction.response.send_message(embed=embed)

# Function to query CPUs based on filters for the CPU database
def query_cpus(price_range, brand=None, core_clock=None, core_count=None):
    conn = sqlite3.connect('database/cpu.db')
    cursor = conn.cursor()

    query = "SELECT name, price FROM cpu WHERE name LIKE ? AND price BETWEEN ? AND ?"
    params = ('%' + brand + '%', price_range[0], price_range[1])

    if core_clock:
        query += " AND core_clock >= ?"
        params += (core_clock,)

    if core_count:
        query += " AND core_count >= ?"
        params += (core_count,)

    query += " ORDER BY price DESC"  
    cursor.execute(query, params)
    cpus = cursor.fetchall()
    conn.close()
    return cpus

# Ask the user a series of questions to determine CPU filtering preferences
async def ask_for_preferences(ctx):
    embed = discord.Embed(title="CPU Filtering Preferences")
    embed.add_field(name="Minimum Price", value="Enter the minimum price range:", inline=False)
    await ctx.send(embed=embed)

    min_price_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    min_price = float(min_price_msg.content)

    embed.set_field_at(0, name="Maximum Price", value="Enter the maximum price range:", inline=False)
    await ctx.send(embed=embed)

    max_price_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    max_price = float(max_price_msg.content)

    embed.set_field_at(0, name="Brand Preference", value="Which brand do you prefer? (Intel/AMD)", inline=False)
    await ctx.send(embed=embed)

    brand_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    brand = brand_msg.content.lower()

    if not any(brand_name in brand for brand_name in ['intel', 'amd']):
        embed.set_field_at(0, name="Invalid Brand", value="Please choose either 'Intel' or 'AMD'.", inline=False)
        await ctx.send(embed=embed)
        return await ask_for_preferences(ctx)

    embed.set_field_at(0, name="Minimum Core Clock", value="Enter the minimum core clock speed you prefer: (type 'None' if not specified)", inline=False)
    await ctx.send(embed=embed)

    core_clock_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    core_clock = float(core_clock_msg.content) if core_clock_msg.content.lower() != 'none' else None

    embed.set_field_at(0, name="Minimum Core Count", value="Enter the minimum core count you prefer: (type 'None' if not specified)", inline=False)
    await ctx.send(embed=embed)

    core_count_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    core_count = int(core_count_msg.content) if core_count_msg.content.lower() != 'none' else None

    return min_price, max_price, brand, core_clock, core_count

# Function to chunk a list into smaller lists for pagination
def chunk_list(lst, n):
    return [lst[i:i + n] for i in range(0, len(lst), n)]

# Display the filtered CPUs to the user in paginated embeds
async def display_cpu_results(ctx):
    # Ask the user for CPU filtering preferences
    min_price, max_price, brand, core_clock, core_count = await ask_for_preferences(ctx)

    embed = discord.Embed(title="CPU Filtering Preferences", color=discord.Color.blue())
    embed.add_field(name="Minimum Price", value=f"£ {min_price}", inline=True)
    embed.add_field(name="Maximum Price", value=f"£ {max_price}", inline=True)
    embed.add_field(name="Brand Preference", value=brand.upper(), inline=True)
    embed.add_field(name="Minimum Core Clock", value=core_clock if core_clock is not None else "Not specified", inline=True)
    embed.add_field(name="Minimum Core Count", value=core_count if core_count is not None else "Not specified", inline=True)
    await ctx.send(embed=embed)

    # Query CPUs based on user preferences
    cpus = query_cpus((min_price, max_price), brand, core_clock, core_count)

    if not cpus:
        await ctx.send("No CPUs found matching the specified criteria.")
        return

    # Sort the CPUs by price (descending)
    cpus.sort(key=lambda x: x[1], reverse=True)

    # Count the number of CPUs that fit the filtering criteria
    num_cpus = len(cpus)
    await ctx.send(f"Found {num_cpus} CPU(s) matching the specified criteria.")

    chunked_cpus = [cpus[i:i + 5] for i in range(0, len(cpus), 5)]
    current_page = 0

    embed = discord.Embed(title=f"Filtered CPUs (Page {current_page + 1}/{len(chunked_cpus)})", color=discord.Color.blue())

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
            await message.remove_reaction(reaction, user)
        elif str(reaction.emoji) == "⬅️" and current_page > 0:
            current_page -= 1
            await message.remove_reaction(reaction, user)

        new_embed = discord.Embed(title=f"Filtered CPUs (Page {current_page + 1}/{len(chunked_cpus)})", color=discord.Color.blue())

        for cpu in chunked_cpus[current_page]:
            new_embed.add_field(name=cpu[0], value=f"Price: £ {cpu[1]}", inline=False)

        await message.edit(embed=new_embed)

    bot.add_listener(on_reaction, 'on_reaction_add')

    try:
        await bot.wait_for('reaction_add', timeout=600, check=check)
    except asyncio.TimeoutError:
        await message.clear_reactions()

# Query CPUs from the database based on the provided name
def filter_cpus_by_name(name):
    conn = sqlite3.connect('database/cpu.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM cpu WHERE name = ?", (name,))
    cpus = cursor.fetchall()
    conn.close()
    return cpus

# Add a CPU component based on the provided name
@bot.command(name='add')
async def add_component(ctx, *, component_name: str):
    cpus = filter_cpus_by_name(component_name)
    if cpus:
        cpu_chosen = cpus[0][0]
        price_info, image_link, search_url_info = scrape_ebay(cpu_chosen)

        embed = discord.Embed(title="Component Added", description=f"You have chosen the CPU: {cpu_chosen}.")
        embed.add_field(name="eBay Information", value=f"{price_info}\n{search_url_info}\n{image_link}")

        await ctx.send(embed=embed)
        return

    embed = discord.Embed(title="Component Not Found", description="No component found matching this criteria.")
    await ctx.send(embed=embed)

# Command to initiate CPU filtering process
@bot.command(name='cpu')
async def cpu_filter(ctx):
    await ctx.send("You will get asked a range of questions for us to filter the CPUs for your desired results.")
    await display_cpu_results(ctx)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        embed = discord.Embed(title="Error", description="Sorry, I couldn't find that command. Type !help for a list of available commands.")
        await ctx.send(embed=embed)

bot.run(TOKEN)