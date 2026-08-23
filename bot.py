import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
# specify intents then say which are allowed
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='/', intents=intents, help_command=None)

newrole = "test dummy"

@bot.event
async def on_ready():
    print(f"{bot.user.name} ACTIVATED >:3")

@bot.event
async def on_member_join(member):
    await member.send(f"Welcome to my playground {member.name}! Use /commands to see command list and do /assignrole to use the bots features!")

@bot.command()
# to change the name of command, change right before (ctx):
async def hello(ctx):
    await ctx.send(f"Hello {ctx.author.mention}!")

@bot.command()
async def assignrole(ctx):
    role = discord.utils.get(ctx.guild.roles, name=newrole)
    if role:
        await ctx.author.add_roles(role)
        await ctx.send(f"{ctx.author.mention} is now my {newrole}")
    else:
        await ctx.send("Role doesn't exist")


@bot.command()
async def commands(ctx):
    command_list = []
    for cmd in bot.commands:
        command_list.append(f"'/{cmd.name}'")

    final_string = ", ".join(command_list)

    await ctx.send(f"Here are the commands! {final_string}")

@bot.command()
async def syllabus(ctx, attachment: discord.Attachment):
    await ctx.send(f"I got your file: {attachment.filename}")

bot.run(token, log_handler=handler, log_level=logging.DEBUG)