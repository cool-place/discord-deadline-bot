import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os

# old discord bot file

#load env, load token
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
    await bot.tree.sync()
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
        await ctx.send("role doesn't exist", delete_after=4.0)
        return

    if role in user.roles:
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

class DocxUploadModal(discord.ui.Modal, title="Upload DOCX Syllabus"):

    upload = discord.ui.Label(
        text="Syllabus file",
        description="Choose a .docx file",
        component=discord.ui.FileUpload(
            required=True,
            min_values=1,
            max_values=1
        )
    )

    async def on_submit(self, interaction: discord.Interaction):

        attachment = self.upload.component.values[0]

        if not attachment.filename.lower().endswith(".docx"):
            await interaction.response.send_message(
                "That isn't a .docx file!",
                ephemeral=True
            )
            return

        file_path = os.path.join(
            "temp_uploads",
            attachment.filename
        )

        await attachment.save(file_path)

        await interaction.response.send_message(
            f"Saved `{attachment.filename}`!",
            ephemeral=True
        )

class PdfUploadModal(discord.ui.Modal, title="Upload PDF Syllabus"):

    upload = discord.ui.Label(
        text="Syllabus file",
        description="Choose a .pdffile",
        component=discord.ui.FileUpload(
            required=True,
            min_values=1,
            max_values=1
        )
    )

    async def on_submit(self, interaction: discord.Interaction):

        attachment = self.upload.component.values[0]

        if not attachment.filename.lower().endswith(".pdf"):
            await interaction.response.send_message(
                "That isn't a .pdf file!",
                ephemeral=True
            )
            return

        file_path = os.path.join(
            "temp_uploads",
            attachment.filename
        )

        await attachment.save(file_path)

        await interaction.response.send_message(
            f"Saved `{attachment.filename}`!",
            ephemeral=True
        )

class TxtUploadModal(discord.ui.Modal, title="Upload TXT Syllabus"):

    upload = discord.ui.Label(
        text="Syllabus file",
        description="Choose a .txt file",
        component=discord.ui.FileUpload(
            required=True,
            min_values=1,
            max_values=1
        )
    )

    async def on_submit(self, interaction: discord.Interaction):

        attachment = self.upload.component.values[0]

        if not attachment.filename.lower().endswith(".txt"):
            await interaction.response.send_message(
                "That isn't a .txt file!",
                ephemeral=True
            )
            return

        file_path = os.path.join(
            "temp_uploads",
            attachment.filename
        )

        await attachment.save(file_path)

        await interaction.response.send_message(
            f"Saved `{attachment.filename}`!",
            ephemeral=True
        )

class SyllabusUploadView(discord.ui.View):

    @discord.ui.button(label="DOCX", style=discord.ButtonStyle.primary)
    async def docx_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(DocxUploadModal())

    @discord.ui.button(label="PDF", style=discord.ButtonStyle.primary)
    async def pdf_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(PdfUploadModal())

    @discord.ui.button(label="TXT", style=discord.ButtonStyle.primary)
    async def txt_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TxtUploadModal())

@bot.tree.command(name="syllabusupload", description="Upload a syllabus")
async def syllabusupload(interaction: discord.Interaction):
    await interaction.response.send_message(
        "What type of syllabus are you uploading?",
        view=SyllabusUploadView(),
        ephemeral=True
    )

# discord token
bot.run(token, log_handler=handler, log_level=logging.DEBUG)