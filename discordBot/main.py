import discord
from discord.ext import commands
import datetime
import aiohttp
import os

from urllib import parse, request
import re

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='>', description="This is a Helper Bot", intents=intents)

@bot.command()
async def ping(ctx):
    await ctx.send('pong')

@bot.command()
async def sum(ctx, numOne: int, numTwo: int):
    await ctx.send(numOne + numTwo)

@bot.command()
async def info(ctx):
    embed = discord.Embed(title=f"{ctx.guild.name}", description="Ficus Guild Overcharge", timestamp=datetime.datetime.utcnow(), color=discord.Color.blue())
    embed.add_field(name="Server created at", value=f"{ctx.guild.created_at}")
    embed.add_field(name="Server Owner", value=f"{ctx.guild.owner}")
    # embed.add_field(name="Server Region", value=f"{ctx.guild.region}")
    embed.add_field(name="Server ID", value=f"{ctx.guild.id}")
    embed.add_field(name="Channel ID", value=f"{ctx.message.channel.id}")
    # embed.set_thumbnail(url=f"{ctx.guild.icon}")
    embed.set_thumbnail(url="https://pluralsight.imgix.net/paths/python-7be70baaac.png")

    await ctx.send(embed=embed)

@bot.command()
async def youtube(ctx, *, search):
    query_string = parse.urlencode({'search_query': search})
    html_content = request.urlopen('http://www.youtube.com/results?' + query_string)
    # print(html_content.read().decode())
    search_results = re.findall( r"watch\?v=(\S{11})", html_content.read().decode())
    # I will put just the first result, you can loop the response to show more results
    await ctx.send('https://www.youtube.com/watch?v=' + search_results[0])

@bot.command(name="quote", help="get amazing random quote")
async def getRandomQuote(ctx):
    """ Get amazing random quote """
    randomQuoteURL = 'https://zenquotes.io/api/random'
    async with ctx.typing():
        async with aiohttp.ClientSession() as session:
            async with session.get(randomQuoteURL) as response:
                if response.status == 200:
                    result = await response.json()
                    randomQuote = f'{result[0]["q"]} -**{result[0]["a"]}**'
                    await ctx.send(randomQuote)
                else:
                    await ctx.send(f"API is not available, Status Code {response.status}")

# Events
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Streaming(name="Help", url="http://www.youtube.com/ficus"))
    print('My Ready is Body')


@bot.listen()
async def on_message(message):    
    if "tutorial" in message.content.lower():
        # in this case don't respond with the word "Tutorial" or you will call the on_message event recursively
        await message.channel.send('El ultimo video de Bruss https://youtu.be/XnSEkBfrkFQ')
        await bot.process_commands(message)

DISCORD_TOKEN = os.environ.get('discord', None)

def run():
	bot.run(DISCORD_TOKEN)