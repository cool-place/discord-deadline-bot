import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import asyncio
from llmparser import extract_text_from_docx, extract_text_from_pdf, extract_text_from_txt, send_text_to_llm

load_dotenv()
discord_token = os.getenv('DISCORD_TOKEN')

if discord_token==None:
    raise RuntimeError("No DISCORD_TOKEN detected")

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

SERVER_GUILD_ID = discord.Object(id=1540596286657531946)

newrole = "test dummy"

@bot.event
async def on_ready():

    bot.tree.copy_global_to(guild=SERVER_GUILD_ID)
    await bot.tree.sync(guild=SERVER_GUILD_ID)
    print(f"{bot.user.name} activated!")

@bot.event 
async def on_member_join(member):
    await member.send(f"Welcome to my test server {member.name}! Use /commands to see command list and do /assignrole to use the bots features!")

@bot.tree.command(name="test", description="test functions")
async def test(interaction: discord.Interaction):

    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message("This command can only be used in the server!", ephemeral=True)
        return

    await interaction.response.send_message("Hello!", ephemeral=True)

@bot.tree.command(name="commands", description="bot commands")
async def commands(interaction:discord.Interaction):

    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message("This command can only be used in the server!", ephemeral=True)
        return

    command_list = []
    for cmd in bot.tree.get_commands():
        if cmd.name == "commands":
            continue

        command_list.append(f"'/{cmd.name}'")

    final_string = ", ".join(command_list)

    await interaction.response.send_message(f"Here are the commands! {final_string}", ephemeral=True)

@bot.tree.command(name="assignrole", description="assigns server role for basic bot functionality")
async def commands(interaction:discord.Interaction):

    # Fail safe to ensure this isn't run in DMs
    if not interaction.guild or not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message("This command can only be used in the server!", ephemeral=True)
        return

    guild = interaction.guild
    member = interaction.user

    role = discord.utils.get(guild.roles, name=newrole)

    if not role:
        await interaction.response.send_message("role doesn't exist, sorry!", ephemeral=True)
        return

    if role in member.roles:
        await interaction.response.send_message(f"{member.mention}, you already have the **{newrole}** role", ephemeral=True)
        return
    
    # Defer response so we can give bot 15 minutes to finish creating channels
    await interaction.response.defer(ephemeral=False)

    await interaction.user.add_roles(role)

    overwrites = {
        interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),

        member: discord.PermissionOverwrite(view_channel=True, send_messages=True),

        interaction.guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
    }

    channel_name = f"private-{member.name}".replace(" ", "-").lower()
    private_channel = await guild.create_text_channel(name=channel_name, overwrites=overwrites)

    await private_channel.send(f"Welcome to your private room, {interaction.user.mention}!")

    await interaction.followup.send(f"{member.mention} is now my {newrole}!")

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

        await interaction.response.defer(
            ephemeral=True,
            thinking=True
        )

        file_path = os.path.join(
            "temp_uploads",
            attachment.filename
        )

        print("Saving DOCX file")
        await attachment.save(file_path)

        try:
            print("Extracting DOCX text")
            text = extract_text_from_docx(file_path)

            print("Sending text to Gemini")
            result = await asyncio.wait_for(
                send_text_to_llm(text),
                timeout=60
            )
            print("gemini responded")

            await interaction.edit_original_response(
                content=result[:1900]
            )

        except asyncio.TimeoutError: 
            print("gemini timed out")

            await interaction.edit_original_response(
                content="Gemini took too long to respond. Please try again."
            )

        except Exception as error:
            print(f"Processing failed: {type(error).__name__}: {error}")

            await interaction.edit_original_response(
                content="Something went wrong while processing that syllabus. Likely that AI servers are experiencing high demand. Try again later."
            )
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

class PdfUploadModal(discord.ui.Modal, title="Upload PDF Syllabus"):

    upload = discord.ui.Label(
        text="Syllabus file",
        description="Choose a .pdf file",
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

        await interaction.response.defer(
            ephemeral=True,
            thinking=True
        )

        file_path = os.path.join(
            "temp_uploads",
            attachment.filename
        )

        print("Saving PDF file")
        await attachment.save(file_path)

        try:
            print("Extracting PDF text")
            text = extract_text_from_pdf(file_path)

            print("Sending text to Gemini")
            result = await asyncio.wait_for(
                send_text_to_llm(text),
                timeout=60
            )
            print("gemini responded")

            await interaction.edit_original_response(
                content=result[:1900]
            )

        except asyncio.TimeoutError: 
            print("gemini timed out")

            await interaction.edit_original_response(
                content="Gemini took too long to respond. Please try again."
            )

        except Exception as error:
            print(f"Processing failed: {type(error).__name__}: {error}")

            await interaction.edit_original_response(
                content="Something went wrong while processing that syllabus. Likely that AI servers are experiencing high demand. Try again later."
            )
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

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

        await interaction.response.defer(
            ephemeral=True,
            thinking=True
        )

        file_path = os.path.join(
            "temp_uploads",
            attachment.filename
        )

        print("Saving TXT file")
        await attachment.save(file_path)

        try:
            print("Extracting TXT text")
            text = extract_text_from_txt(file_path)

            print("Sending text to Gemini")
            result = await asyncio.wait_for(
                send_text_to_llm(text),
                timeout=60
            )
            print("gemini responded")

            await interaction.edit_original_response(
                content=result[:1900]
            )

        except asyncio.TimeoutError: 
            print("gemini timed out")

            await interaction.edit_original_response(
                content="Gemini took too long to respond. Please try again."
            )

        except Exception as error:
            print(f"Processing failed: {type(error).__name__}: {error}")

            await interaction.edit_original_response(
                content="Something went wrong while processing that syllabus. Likely that AI servers are experiencing high demand. Try again later."
            )
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

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




bot.run(discord_token, log_handler=handler, log_level=logging.DEBUG)