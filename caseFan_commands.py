import discord
import sqlite3
import asyncio
import os

# Function to query CaseFans based on filters for the CaseFan database 
def query_caseFan(price_range, size = None, colour = None):
    conn = sqlite3.connect('database/cpu.db')
    cursor = conn.cursor()

    query = "SELECT name, price FROM `case-fan` WHERE size = ? AND color LIKE ? AND price BETWEEN ? AND ? "
    params = (size, '%' + colour + '%', price_range[0], price_range[1])

    query += " ORDER BY price DESC"
    cursor.execute(query, params)
    caseFans = cursor.fetchall()
    conn.close()
    return caseFans


# Ask the user a series of questions to determine CaseFan filtering preferences
async def ask_for_preferences(bot, ctx):  # Added bot as an argument
    embed = discord.Embed(title="CaseFan Filtering Preferences")

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

    # Size

    embed.set_field_at(0, name="Size Preference", value="What size of cooler are you looking for?", inline=False)
    await ctx.send(embed=embed)

    size_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    size = float(size_msg.content)

    # Colour

    embed.set_field_at(0, name="Colour", value="What colour case fan would you like to find? (type 'None' if not specified)", inline=False)
    await ctx.send(embed=embed)

    colour_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    colour = colour_msg.content.capitalize() if colour_msg.content.lower() != 'none' else None


    return min_price, max_price, size, colour

# Function to chunk a list into smaller lists for pagination
def chunk_list(lst, n):
    return [lst[i:i + n] for i in range(0, len(lst), n)]

# Display the filtered CaseFans to the user in paginated embeds
async def display_caseFan_results(bot, ctx):  # Modified to accept bot object as an argument
    # Ask the user for CaseFan filtering preferences
    min_price, max_price, size, colour = await ask_for_preferences(bot, ctx)

    embed = discord.Embed(title="CaseFan Filtering Preferences", color=discord.Color.blue())
    embed.add_field(name="Minimum Price", value=f"£ {min_price}", inline=True)
    embed.add_field(name="Maximum Price", value=f"£ {max_price}", inline=True)
    embed.add_field(name="Case Fan Size", value=size, inline=True)
    embed.add_field(name="Case Fan Colour", value=colour if colour is not None else "Not specified", inline=True)

    await ctx.send(embed=embed)

    # Query CaseFans based on user preferences
    caseFans = query_caseFan((min_price, max_price), size, colour)

    if not caseFans:
        await ctx.send("No CaseFans found matching the specified criteria.")
        print("not working)")
        return

    # Sort the CaseFans by price (descending)
    caseFans.sort(key=lambda x: x[1], reverse=True)

    # Count the number of CaseFans that fit the filtering criteria
    num_caseFans = len(caseFans)
    await ctx.send(f"Found {num_caseFans} CaseFan(s) matching the specified criteria.")
    print("working3")

    chunked_caseFans = [caseFans[i:i + 5] for i in range(0, len(caseFans), 5)]
    current_page = 0

    embed = discord.Embed(title=f"Filtered CaseFans (Page {current_page + 1}/{len(chunked_caseFans)})", color=discord.Color.blue())

    for caseFan in chunked_caseFans[current_page]:
        embed.add_field(name=caseFan[0], value=f"Price: £ {caseFan[1]}", inline=False)

    message = await ctx.send(embed=embed)
    await message.add_reaction("⬅️")
    await message.add_reaction("➡️")

    def check(reaction, user):
        return user == ctx.author and reaction.message == message and str(reaction.emoji) in ["⬅️", "➡️"]

    async def on_reaction(reaction, user):
        nonlocal current_page
        if str(reaction.emoji) == "➡️" and current_page < len(chunked_caseFans) - 1:
            current_page += 1
            await message.remove_reaction(reaction, user)
        elif str(reaction.emoji) == "⬅️" and current_page > 0:
            current_page -= 1
            await message.remove_reaction(reaction, user)

        new_embed = discord.Embed(title=f"Filtered CaseFans (Page {current_page + 1}/{len(chunked_caseFans)})", color=discord.Color.blue())

        for caseFan in chunked_caseFans[current_page]:
            new_embed.add_field(name=caseFan[0], value=f"Price: £ {caseFan[1]}", inline=False)

        await message.edit(embed=new_embed)

    bot.add_listener(on_reaction, 'on_reaction_add')

    try:
        await bot.wait_for('reaction_add', timeout=600, check=check)
    except asyncio.TimeoutError:
        await message.clear_reactions()

# Query CaseFans from the database based on the provided name
def filter_caseFans_by_name(name):
    conn = sqlite3.connect('database/cpu.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM 'case-fan' WHERE name = ?", (name,))
    caseFans = cursor.fetchall()
    conn.close()
    return caseFans