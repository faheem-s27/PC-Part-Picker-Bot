TOKEN = 'MTIxMDE3MzY5NzA5NzMzNDg0NQ.GwXM-Z.L-Hy_1N7FVzJTWrlgWaz5nhIXCgz-rlUtybVCI'

import discord
from discord.ext import commands

from cpu_commands import filter_cpus_by_name, display_cpu_results
from ebay import scrape_ebay

intents = discord.Intents.all()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

added_components = {}

# Duck was here

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

@bot.command(name='add')
async def add_component(ctx, *, component_name: str):
    cpus = filter_cpus_by_name(component_name)
    if cpus:
        cpu_chosen = cpus[0][0]
        price_info, image_link, search_url_info = scrape_ebay(cpu_chosen)

        user_id = ctx.author.id
        added_components.setdefault(user_id, []).append(cpu_chosen)

        embed = discord.Embed(title="Component Added", description=f"You have chosen the CPU: {cpu_chosen}.")
        embed.add_field(name="eBay Information", value=f"{price_info}\n{search_url_info}")
        embed.set_thumbnail(url=image_link)

        await ctx.send(embed=embed)
        return

    embed = discord.Embed(title="Component Not Found", description="No component found matching this criteria.")
    await ctx.send(embed=embed)

@bot.command(name='build')
async def show_build(ctx):
    user_id = ctx.author.id
    components = added_components.get(user_id, [])

    if components:
        embed = discord.Embed(title="Build Components", description="Components added to your build:")
        for component in components:
            embed.add_field(name="Component", value=component, inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("No components added to your build yet.")

@bot.command(name='remove')
async def remove_component(ctx, *, component_name: str):
    user_id = ctx.author.id
    user_components = added_components.get(user_id, [])  # Get the components added by the user

    component_name_lower = component_name.lower()
    user_components_lower = [component.lower() for component in user_components]

    if component_name_lower in user_components_lower:
        index = user_components_lower.index(component_name_lower)
        removed_component = user_components.pop(index)

        await ctx.send(f"Component '{removed_component}' has been removed from the build.")
    else:
        await ctx.send(f"Component '{component_name}' is not in the build.")

@bot.command(name='suggest')
async def suggest_similar(ctx):
    user_id = ctx.author.id
    user_components = added_components.get(user_id, [])

    if not user_components:
        await ctx.send("No components added to your build yet.")
        return

    last_component_type = get_component_type(user_components[-1])
    similar_components = find_similar_components(last_component_type)

    if similar_components:
        embed = discord.Embed(title="Similar Components", description=f"Suggested components similar to the last added {last_component_type}:")

        for component in similar_components:
            embed.add_field(name="Component", value=component, inline=False)

        await ctx.send(embed=embed)
    else:
        await ctx.send(f"No similar components found for {last_component_type}.")

def get_component_type(component_name):
    return component_name.split()[0]

def find_similar_components(component_type):
    if component_type.lower() == 'amd':
        return ['AMD Ryzen 9 5900X', 'AMD Ryzen 7 5800X', 'AMD Ryzen 5 5600X']
    elif component_type.lower() == 'intel':
        return ['Intel Core i9-11900K', 'Intel Core i7-11700K', 'Intel Core i5-11600K']
    else:
        return []

# Define the pre-built PCs specifications
prebuilt_pcs = {
    "General Desktop PC": {
        "CPU": "Intel Core i5-11400F 2.6GHz 6-Core",
        "Cooling System": "Assassin 120 SE 66 CFM",
        "Motherboard": "H510M K V2",
        "RAM": "16GB(2 x 8GB) DDR4-3200",
        "Storage": "512GB NVMe SSD",
        "GPU": "GeForce GTX 1650",
        "Case": "4000D Mid Tower",
        "Power Supply":"RM750e 750W",
        "Price": "£750",
        "PcPartPicker link": "https://uk.pcpartpicker.com/list/tPDdWt"
    },
    "Gaming PC": {
        "CPU": "AMD Ryzen 5 5600X 3.7GHz 6-Core",
        "Cooling System": "iCUE H100i RGB ELITE 59 CFM",
        "Motherboard": "ASUS TUF GAMING B550-PLUS",
        "RAM": "16GB(2 x 8GB) DDR4 3600MHz",
        "Storage": "1TB NVMe SSD",
        "GPU": "GeForce RTX 3060 Ti",
        "Case": "Meshify C Mid Tower",
        "Power Supply":"RM850e 850W",
        "Price": "£1300",
        "PcPartPicker link": "https://uk.pcpartpicker.com/list/CnBpn6"
    },
    "High Performance PC": {
        "CPU": "Intel Core i9-14900KF 3.2GHz 24-Core",
        "Cooling System": "Kraken Elite 78 CFM",
        "Motherboard": "MSI PRO Z790-A MAX WIFI",
        "RAM": "32GB(2 x 16GB) DDR5 5200MHz",
        "Storage": "2TB M.2 PCle NVMe SSD",
        "GPU": "GeForce RTX 4090",
        "Case": "Lian Li O11 Mid Tower",
        "Power Supply":"V850 SFX COLD 850W",
        "Price": "£3450",
        "PcPartPicker link": "https://uk.pcpartpicker.com/list/kJhN7R"
    }
}

@bot.command(name='pre-built')
async def prebuilt_pc(ctx):
    for pc_name, specs in prebuilt_pcs.items():
        embed = discord.Embed(title=pc_name, description="Considering your budget and needs, you can have a look at the specifications below:")

        components = "\n".join([f"**{component}:** {value}" for component, value in specs.items()])
        embed.add_field(name="Specifications", value=components, inline=False)

        await ctx.send(embed=embed)

bot.run(TOKEN) 