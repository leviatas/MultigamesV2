import discord
from discord.ext import commands
import datetime
import aiohttp
import os

from urllib import parse, request
import re
import logging as log
from BloodClocktower.Boardgamebox.Player import Player

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='>', description="This is a Helper Bot", intents=intents)


log.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=log.INFO)
logger = log.getLogger(__name__)

@bot.command()
async def info(ctx):
    embed = discord.Embed(title=f"{ctx.guild.name}", description="Ficus Guild Overcharge", timestamp=datetime.datetime.utcnow(), color=discord.Color.blue())
    embed.add_field(name="Server created at", value=f"{ctx.guild.created_at}")
    embed.add_field(name="Server Owner", value=f"{ctx.guild.owner}")
    # embed.add_field(name="Server Region", value=f"{ctx.guild.region}")
    embed.add_field(name="Server ID", value=f"{ctx.guild.id}")
    embed.add_field(name="Channel ID", value=f"{ctx.message.channel.id}")
    if hasattr(ctx.message.channel, 'parent_id'):
        embed.add_field(name="Parent ID", value=f"{ctx.message.channel.parent_id}")
    # embed.set_thumbnail(url=f"{ctx.guild.icon}")
    embed.set_thumbnail(url="https://pluralsight.imgix.net/paths/python-7be70baaac.png")

    await ctx.send(embed=embed)

# Events
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Streaming(name="Help", url="http://www.youtube.com/ficus"))
    print('Bot is ready')


class Join_Menu(discord.ui.View):
    def __init__(self, *, timeout=None, max):
        super().__init__(timeout=timeout)
        self.players = []
        self.max = max

    @discord.ui.button(label="Join",style=discord.ButtonStyle.green)
    async def join_button(self, interaction:discord.Interaction, button:discord.ui.Button):
        if self.players == self.max:
            await interaction.response.send_message("Maximum players reached", ephemeral=True)
            return
        if interaction.user.mention in self.players:
            await interaction.response.send_message("You joined already", ephemeral=True)
            return
        user = interaction.user
        channel_id = interaction.message.channel.parent_id if hasattr(interaction.message.channel, 'parent_id') else interaction.message.channel.id
        player = Player(user.name, user.id, user.mention)
        self.players.append(player)
        embed = discord.Embed(title=f"GAME_TITLE", description=f"Channel ID {channel_id}", timestamp=datetime.datetime.utcnow(), color=discord.Color.blue())
        for count, player in enumerate(self.players, start=1):
            embed.add_field(name="", value=f"{count}. {player.nick}")
        # await interaction.response.edit_message(content=f"This is an edited button response! {self.count}")
        await interaction.response.edit_message(embed=embed)
        await interaction.followup.send("You have joined the game", ephemeral=True)

    @discord.ui.button(label="Leave",style=discord.ButtonStyle.red)
    async def leave_button(self, interaction:discord.Interaction, button:discord.ui.Button):
        if not any(x for x in self.players if interaction.user.name == x.name):
            await interaction.response.send_message("You aren't in the game", ephemeral=True)
            return
        user = interaction.user
        channel_id = interaction.message.channel.parent_id if hasattr(interaction.message.channel, 'parent_id') else interaction.message.channel.id
        log.info(user.mention)
        player = Player(user.name, user.id, user.mention)
        self.players.remove(player)
        embed = discord.Embed(title=f"GAME_TITLE", description=f"Channel ID {channel_id}", timestamp=datetime.datetime.utcnow(), color=discord.Color.blue())
        for count, player in enumerate(self.players, start=1):
            embed.add_field(name="", value=f"{count}. {player.nick}")
        # await interaction.response.edit_message(content=f"This is an edited button response! {self.count}")
        await interaction.response.edit_message(embed=embed)
        await interaction.followup.send("You left the game", ephemeral=True)

    @discord.ui.button(label="Refresh",style=discord.ButtonStyle.gray)
    async def refresh_button(self, interaction:discord.Interaction, button:discord.ui.Button):    
        channel_id = interaction.message.channel.parent_id if hasattr(interaction.message.channel, 'parent_id') else interaction.message.channel.id
        embed = discord.Embed(title=f"GAME_TITLE", description=f"Channel ID {channel_id}", timestamp=datetime.datetime.utcnow(), color=discord.Color.blue())
        for count, player in enumerate(self.players, start=1):
            embed.add_field(name="", value=f"{count}. {player.mention}")
        # await interaction.response.edit_message(content=f"This is an edited button response! {self.count}")
        await interaction.response.edit_message(embed=embed)
        await interaction.followup.send("Message refreshed", ephemeral=True)

    @discord.ui.button(label="Close",style=discord.ButtonStyle.danger)
    async def close_button(self, interaction:discord.Interaction, button:discord.ui.Button):
        await interaction.message.delete()

@bot.command()
async def menu(ctx):
    channel_id = ctx.message.channel.parent_id if hasattr(ctx.message.channel, 'parent_id') else ctx.message.channel.id
    embed = discord.Embed(title=f"GAME_TITLE", description=f"Channek ID {channel_id}", timestamp=datetime.datetime.utcnow(), color=discord.Color.blue())
    await ctx.send(embed=embed,view=Join_Menu(max=12))

DISCORD_TOKEN = os.environ.get('discord', None)

def run():
	bot.run(DISCORD_TOKEN)



    
# @bot.command()
# async def youtube(ctx, *, search):
#     query_string = parse.urlencode({'search_query': search})
#     html_content = request.urlopen('http://www.youtube.com/results?' + query_string)
#     # print(html_content.read().decode())
#     search_results = re.findall( r"watch\?v=(\S{11})", html_content.read().decode())
#     # I will put just the first result, you can loop the response to show more results
#     await ctx.send('https://www.youtube.com/watch?v=' + search_results[0])

# @bot.command(name="quote", help="get amazing random quote")
# async def getRandomQuote(ctx):
#     """ Get amazing random quote """
#     randomQuoteURL = 'https://zenquotes.io/api/random'
#     async with ctx.typing():
#         async with aiohttp.ClientSession() as session:
#             async with session.get(randomQuoteURL) as response:
#                 if response.status == 200:
#                     result = await response.json()
#                     randomQuote = f'{result[0]["q"]} -**{result[0]["a"]}**'
#                     await ctx.send(randomQuote)
#                 else:
#                     await ctx.send(f"API is not available, Status Code {response.status}")



# @bot.listen()
# async def on_message(message):    
#     if "tutorial" in message.content.lower():
#         # in this case don't respond with the word "Tutorial" or you will call the on_message event recursively
#         await message.channel.send('El ultimo video de Bruss https://youtu.be/XnSEkBfrkFQ')
#         await bot.process_commands(message)


# @bot.command()
# async def ping(ctx):
#     await ctx.send('pong')

# @bot.command()
# async def sum(ctx, numOne: int, numTwo: int):
#     await ctx.send(numOne + numTwo)