import discord
import sqlite3
import asyncio
import os

# Function to query GPUs based on filters for the GPU database 
def query_gpus(price_range, chipset=None, core_clock=None, memory=None):
    conn = sqlite3.connect('database/cpu.db')
    cursor = conn.cursor()

    query = "SELECT name, price FROM gpu WHERE chipset LIKE ? AND price BETWEEN ? AND ? AND memory >= ?"
    params = ('%' + chipset + '%', price_range[0], price_range[1], memory)

    if core_clock:
        query += " AND core_clock >= ?"
        params += (core_clock,)

    query += " ORDER BY price DESC"
    cursor.execute(query, params)
    gpus = cursor.fetchall()
    conn.close()
    return gpus

# Ask the user a series of questions to determine GPU filtering preferences
async def ask_for_preferences(bot, ctx):  # Added bot as an argument
    embed = discord.Embed(title="GPU Filtering Preferences")

    # Minimum Price  

    embed.add_field(name="Minimum Price", value="Enter the minimum price range:", inline=False)
    await ctx.send(embed=embed)

    min_price_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    min_price = float(min_price_msg.content)

    # Maximum Price

    embed.set_field_at(0, name="Maximum Price", value="Enter the maximum price range:", inline=False)
    await ctx.send(embed=embed)

    max_price_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    max_price = float(max_price_msg.content)

    # Chipset Preference 

    embed.set_field_at(0, name="Chipset Preference", value="Which chipset do you prefer? (GeForce/Radeon)", inline=False)
    await ctx.send(embed=embed)

    chipset_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    chipset = chipset_msg.content.lower()

    if not any(chipset_name in chipset for chipset_name in ['geforce', 'radeon']):
        embed.set_field_at(0, name="Invalid Chipset", value="Please choose either 'Geforce' or 'Radeon'.", inline=False)
        await ctx.send(embed=embed)
        return await ask_for_preferences(bot, ctx)  # Changed to pass bot argument

    # Minimum Core Clock

    embed.set_field_at(0, name="Minimum Core Clock", value="Enter the minimum core clock speed you prefer: (type 'None' if not specified)", inline=False)
    await ctx.send(embed=embed)

    core_clock_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    core_clock = float(core_clock_msg.content) if core_clock_msg.content.lower() != 'none' else None

    # Memory

    embed.set_field_at(0, name="Minimum Memory", value="Enter the minimum VRAM amount you prefer: (type 'None' if not specified)", inline=False)
    await ctx.send(embed=embed)

    memory_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    memory = float(memory_msg.content) if memory_msg.content.lower() != 'none' else None

    return min_price, max_price, chipset, core_clock, memory

# Function to chunk a list into smaller lists for pagination
def chunk_list(lst, n):
    return [lst[i:i + n] for i in range(0, len(lst), n)]

# Display the filtered GPUs to the user in paginated embeds
async def display_gpu_results(bot, ctx):  # Modified to accept bot object as an argument
    # Ask the user for GPU filtering preferences
    min_price, max_price, chipset, core_clock, memory = await ask_for_preferences(bot, ctx)

    embed = discord.Embed(title="GPU Filtering Preferences", color=discord.Color.blue())
    embed.add_field(name="Minimum Price", value=f"£ {min_price}", inline=True)
    embed.add_field(name="Maximum Price", value=f"£ {max_price}", inline=True)
    embed.add_field(name="Chipset Preference", value=chipset.upper(), inline=True)
    embed.add_field(name="Minimum Core Clock", value=core_clock if core_clock is not None else "Not specified", inline=True)
    embed.add_field(name="Minimum VRAM", value=memory if memory is not None else "Not specified", inline=True)
    await ctx.send(embed=embed)

    # Query GPUs based on user preferences
    gpus = query_gpus((min_price, max_price), chipset, core_clock, memory)

    if not gpus:
        await ctx.send("No GPUs found matching the specified criteria.")
        print("not working)")
        return

    # Sort the GPUs by price (descending)
    gpus.sort(key=lambda x: x[1], reverse=True)

    # Count the number of GPUs that fit the filtering criteria
    num_gpus = len(gpus)
    await ctx.send(f"Found {num_gpus} GPU(s) matching the specified criteria.")
    print("working3")

    chunked_gpus = [gpus[i:i + 5] for i in range(0, len(gpus), 5)]
    current_page = 0

    embed = discord.Embed(title=f"Filtered GPUs (Page {current_page + 1}/{len(chunked_gpus)})", color=discord.Color.blue())

    for gpu in chunked_gpus[current_page]:
        embed.add_field(name=gpu[0], value=f"Price: £ {gpu[1]}", inline=False)

    message = await ctx.send(embed=embed)
    await message.add_reaction("⬅️")
    await message.add_reaction("➡️")

    def check(reaction, user):
        return user == ctx.author and reaction.message == message and str(reaction.emoji) in ["⬅️", "➡️"]

    async def on_reaction(reaction, user):
        nonlocal current_page
        if str(reaction.emoji) == "➡️" and current_page < len(chunked_gpus) - 1:
            current_page += 1
            await message.remove_reaction(reaction, user)
        elif str(reaction.emoji) == "⬅️" and current_page > 0:
            current_page -= 1
            await message.remove_reaction(reaction, user)

        new_embed = discord.Embed(title=f"Filtered GPUs (Page {current_page + 1}/{len(chunked_gpus)})", color=discord.Color.blue())

        for gpu in chunked_gpus[current_page]:
            new_embed.add_field(name=gpu[0], value=f"Price: £ {gpu[1]}", inline=False)

        await message.edit(embed=new_embed)

    bot.add_listener(on_reaction, 'on_reaction_add')

    try:
        await bot.wait_for('reaction_add', timeout=600, check=check)
    except asyncio.TimeoutError:
        await message.clear_reactions()

# Query GPUs from the database based on the provided name
def filter_gpus_by_name(name):
    conn = sqlite3.connect('database/cpu.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM gpu WHERE name = ?", (name,))
    gpus = cursor.fetchall()
    conn.close()
    return gpus