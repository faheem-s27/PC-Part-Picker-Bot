TOKEN = 'MTIxMDE3MzY5NzA5NzMzNDg0NQ.GwXM-Z.L-Hy_1N7FVzJTWrlgWaz5nhIXCgz-rlUtybVCI'

import discord
from discord.ext import commands

from cpu_commands import filter_cpus_by_name, display_cpu_results
from ebay import scrape_ebay

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

# In case of error or wrong command
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        embed = discord.Embed(title="Error", description="Sorry, I couldn't find that command. Type /help for a list of available commands.")
        await ctx.send(embed=embed)

# Provide helpful information when the user triggers the "help" command
@bot.tree.command(name="help")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(title="Help", description="I'm here to help you build a PC.")
    embed.add_field(name="Commands", value="!cpu - Find CPUs\n!add <component name> - Add components to the build", inline=False)
    await interaction.response.send_message(embed=embed)

# Command to initiate CPU filtering process
@bot.command(name='cpu')
async def cpu_filter(ctx):
    await ctx.send("You will get asked a range of questions for us to filter the CPUs for your desired results.")
    await display_cpu_results(bot, ctx)

# Add a component based on the provided name (only CPU for now)
@bot.command(name='add')
async def add_component(ctx, *, component_name: str):
    cpus = filter_cpus_by_name(component_name)
    if cpus:
        cpu_chosen = cpus[0][0]
        price_info, image_link, search_url_info = scrape_ebay(cpu_chosen)

        embed = discord.Embed(title="Component Added", description=f"You have chosen the CPU: {cpu_chosen}.")
        embed.add_field(name="eBay Information", value=f"{price_info}\n{search_url_info}")

        # print(image_link)
        # embed.set_image(url=image_link)
        embed.set_thumbnail(url=image_link)

        await ctx.send(embed=embed)
        return

    embed = discord.Embed(title="Component Not Found", description="No component found matching this criteria.")
    await ctx.send(embed=embed)

bot.run(TOKEN) 