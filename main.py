TOKEN = 'token'

import discord
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

bot.run(TOKEN)