import discord
import sqlite3
import asyncio
import os

# Function to query Cases based on filters for the Case database 
def query_case(price_range, type = None, colour = None):
    conn = sqlite3.connect('database/cpu.db')
    cursor = conn.cursor()

    query = "SELECT name, price FROM `case` WHERE type LIKE ? AND color LIKE ? AND price BETWEEN ? AND ? "
    params = ('%' + type + '%', '%' + colour + '%', price_range[0], price_range[1])

    query += " ORDER BY price DESC"
    cursor.execute(query, params)
    cases = cursor.fetchall()
    conn.close()
    return cases


# Ask the user a series of questions to determine Case filtering preferences
async def ask_for_preferences(bot, ctx):  # Added bot as an argument
    embed = discord.Embed(title="Case Filtering Preferences")

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

    # Type

    embed.set_field_at(0, name="Type Preference", value="What type of case do you wish to get? (mini / mid / full etc)", inline=False)
    await ctx.send(embed=embed)

    type_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    type = type_msg.content.capitalize()


    if not any(type_name in type for type_name in ['Mini', 'Mid' , 'Full']):
        embed.set_field_at(0, name="Invalid Case Type", value="Please choose either mini / mid / full.", inline=False)
        await ctx.send(embed=embed)
        return await ask_for_preferences(bot, ctx)  # Changed to pass bot argument

    # Colour

    embed.set_field_at(0, name="Colour", value="What colour case would you like to find? (type 'None' if not specified)", inline=False)
    await ctx.send(embed=embed)

    colour_msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author)
    colour = colour_msg.content.capitalize() if colour_msg.content.lower() != 'none' else None


    return min_price, max_price, type, colour

# Function to chunk a list into smaller lists for pagination
def chunk_list(lst, n):
    return [lst[i:i + n] for i in range(0, len(lst), n)]

# Display the filtered Cases to the user in paginated embeds
async def display_case_results(bot, ctx):  # Modified to accept bot object as an argument
    # Ask the user for Case filtering preferences
    min_price, max_price, type, colour = await ask_for_preferences(bot, ctx)

    embed = discord.Embed(title="Case Filtering Preferences", color=discord.Color.blue())
    embed.add_field(name="Minimum Price", value=f"£ {min_price}", inline=True)
    embed.add_field(name="Maximum Price", value=f"£ {max_price}", inline=True)
    embed.add_field(name="Case Type", value=type, inline=True)
    embed.add_field(name="Case Colour", value=colour if colour is not None else "Not specified", inline=True)

    await ctx.send(embed=embed)

    # Query Cases based on user preferences
    cases = query_case((min_price, max_price), type, colour)

    if not cases:
        await ctx.send("No Cases found matching the specified criteria.")
        print("not working)")
        return

    # Sort the Cases by price (descending)
    cases.sort(key=lambda x: x[1], reverse=True)

    # Count the number of Cases that fit the filtering criteria
    num_cases = len(cases)
    await ctx.send(f"Found {num_cases} Case(s) matching the specified criteria.")
    print("working3")

    chunked_cases = [cases[i:i + 5] for i in range(0, len(cases), 5)]
    current_page = 0

    embed = discord.Embed(title=f"Filtered Cases (Page {current_page + 1}/{len(chunked_cases)})", color=discord.Color.blue())

    for case in chunked_cases[current_page]:
        embed.add_field(name=case[0], value=f"Price: £ {case[1]}", inline=False)

    message = await ctx.send(embed=embed)
    await message.add_reaction("⬅️")
    await message.add_reaction("➡️")

    def check(reaction, user):
        return user == ctx.author and reaction.message == message and str(reaction.emoji) in ["⬅️", "➡️"]

    async def on_reaction(reaction, user):
        nonlocal current_page
        if str(reaction.emoji) == "➡️" and current_page < len(chunked_cases) - 1:
            current_page += 1
            await message.remove_reaction(reaction, user)
        elif str(reaction.emoji) == "⬅️" and current_page > 0:
            current_page -= 1
            await message.remove_reaction(reaction, user)

        new_embed = discord.Embed(title=f"Filtered Cases (Page {current_page + 1}/{len(chunked_cases)})", color=discord.Color.blue())

        for case in chunked_cases[current_page]:
            new_embed.add_field(name=case[0], value=f"Price: £ {case[1]}", inline=False)

        await message.edit(embed=new_embed)

    bot.add_listener(on_reaction, 'on_reaction_add')

    try:
        await bot.wait_for('reaction_add', timeout=600, check=check)
    except asyncio.TimeoutError:
        await message.clear_reactions()

# Query Cases from the database based on the provided name
def filter_cases_by_name(name):
    conn = sqlite3.connect('database/cpu.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM 'case' WHERE name = ?", (name,))
    cases = cursor.fetchall()
    conn.close()
    return cases