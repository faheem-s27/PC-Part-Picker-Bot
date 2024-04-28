import discord
from discord.ext import commands
from bs4 import BeautifulSoup
import requests
from main import TOKEN

intents = discord.Intents.all()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')

@bot.command()
async def popularcpus(ctx):
    url = "https://www.cpubenchmark.net/common_cpus.html"
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        cpu_list = []
        # find CPU elements and extract relevant data
        cpu_container = soup.find('ul', class_='chartlist')
        if cpu_container:
            for cpu in cpu_container.find_all('a'):
                model = cpu.find('span', class_='prdname').text.strip()
                count_str = cpu.find('span', class_='count').text.strip().replace(',', '')  # remove commas from the count string
                price_str = cpu.find('span', class_='price-neww').text.strip().replace('$', '')  # extract price
                link = "https://www.cpubenchmark.net/" + cpu['href']  # extract link
                # check if count and price are numeric
                if count_str.isdigit() and price_str.replace('.', '').isdigit():
                    # convert count to int
                    count = int(count_str)
                    # convert price to float
                    price = float(price_str)
                    # append CPU model, count, and price to the list
                    cpu_list.append((model, count, price, link))
                else:
                    cpu_list.append((model, 0, 0.0, link))  # assign a count and price of 0 if not numeric

            # process CPU data to find the top 10 most common CPUs based on count (benchmark score)
            cpu_list.sort(key=lambda x: x[1],
                          reverse=True)  # sort CPU list by count (benchmark score) in descending order
            top_cpus = cpu_list[:10]  # get the top 10 most common CPUs

            # create and send an embed with the top 10 CPUs
            embed = discord.Embed(title="Top 10 current most common CPUs based on CPU Benchmark Score",
                                  description="Here are the top 10 CPUs based on CPU Benchmark Score:")
            for rank, cpu in enumerate(top_cpus, start=1):
                embed.add_field(name=f"{rank}. {cpu[0]}",
                                value=f"Benchmark Score: {cpu[1]}, Price: ${cpu[2]:.2f}\n[CPU Benchmark Link]({cpu[3]})",
                                inline=False)
            await ctx.send(embed=embed)
        else:
            await ctx.send("Failed to find CPU data on the website.")
    else:
        await ctx.send("Failed to fetch CPU data from the website.")

#bot.run(TOKEN)