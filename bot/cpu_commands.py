import discord
import sqlite3
import asyncio


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
async def ask_for_preferences(bot, ctx):  # Added bot as an argument
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
        return await ask_for_preferences(bot, ctx)  # Changed to pass bot argument

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
async def display_cpu_results(bot, ctx):  # Modified to accept bot object as an argument
    # Ask the user for CPU filtering preferences
    min_price, max_price, brand, core_clock, core_count = await ask_for_preferences(bot, ctx)

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
