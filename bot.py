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
intents.guilds = True

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
    await ctx.send(f"Hello {ctx.author.mention}!", delete_after=4.0)

@bot.command(hidden=True) #hidden=True hides command from /command
async def assignrole(ctx):
    await ctx.message.delete()

    guild = ctx.guild
    user = ctx.author

    role = discord.utils.get(guild.roles, name=newrole)

    if not role:
        await ctx.message.delete(delay=4.0)
        await ctx.send("role doesn't exist", delete_after=4.0)
        return

    if role in user.roles:
        await ctx.message.delete(delay=4.0)
        await ctx.send(f"{user.mention}, you already have the **{newrole}** role", delete_after=4.0)
        return
    
    await ctx.author.add_roles(role)

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),

        user: discord.PermissionOverwrite(view_channel=True, send_messages=True),

        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
    }

    channel_name = f"private-{user.name}".replace(" ", "-").lower()
    private_channel = await guild.create_text_channel(name=channel_name, overwrites=overwrites)

    await private_channel.send(f"Welcome to your private room, {user.mention}!")

    await ctx.send(f"{ctx.author.mention} is now my {newrole}", delete_after=4.0)

@bot.command(hidden=True)
async def commands(ctx):
    command_list = []
    for cmd in bot.commands:
        if cmd.hidden:
            continue

        command_list.append(f"'/{cmd.name}'")

    final_string = ", ".join(command_list)

    await ctx.send(f"Here are the commands! {final_string}", delete_after=6.0)

    await ctx.message.delete(delay=4.0)

@bot.command()
async def syllabus(ctx, attachment: discord.Attachment):
    file_path = os.path.join("temp_uploads", attachment.filename)

    await attachment.save(file_path)

    await ctx.author.send(f"Saved {attachment.filename}!")

    await ctx.message.delete(delay=4.0)

bot.run(token, log_handler=handler, log_level=logging.DEBUG)