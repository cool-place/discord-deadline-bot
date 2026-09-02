import discord
from discord.ext import commands, tasks
import logging
from dotenv import load_dotenv
import os
import asyncio
from llmparser import extract_text_from_docx, extract_text_from_pdf, extract_text_from_txt, send_text_to_llm
from database import (
    initialize_database,
    save_deadline,
    get_deadlines_by_date,
    get_upcoming_deadlines,
    save_canvas_deadline,
    save_canvas_feed,
    get_canvas_feeds,
    save_d2l_deadline,
    save_d2l_feed,
    get_d2l_feeds
)
from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo
from canvas_parser import get_canvas_deadlines
from d2l_parser import get_d2l_deadlines

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

initialize_database()

central_time = ZoneInfo("America/Chicago")

async def sync_d2l_feeds():

    feeds = get_d2l_feeds()

    for user_id, calendar_url in feeds:

        try:

            deadlines = await get_d2l_deadlines(calendar_url)

            for deadline in deadlines:

                save_d2l_deadline(
                    user_id,
                    deadline["course_name"],
                    deadline["name"],
                    deadline["due_date"],
                    deadline["due_time"],
                    deadline["d2l_uid"]
                )

            print(
                f"Synced {len(deadlines)} D2L deadlines "
                f"for user {user_id}"
            )

        except Exception as error:

            print(
                f"D2L sync failed for user {user_id}: "
                f"{type(error).__name__}: {error}"
            )

async def sync_canvas_feeds():

    feeds = get_canvas_feeds()

    for user_id, calendar_url in feeds:

        try:
            deadlines = await get_canvas_deadlines(calendar_url)

            for deadline in deadlines:

                save_canvas_deadline(
                    user_id,
                    deadline["course_name"],
                    deadline["name"],
                    deadline["due_date"],
                    deadline["due_time"],
                    deadline["canvas_uid"]
                )

            print(
                f"Synced {len(deadlines)} Canvas deadlines "
                f"for user {user_id}"
            )

        except Exception as error:
            print(
                f"Canvas sync failed for user {user_id}: "
                f"{type(error).__name__}: {error}"
            )

@tasks.loop(time=time(hour=8, minute=0, tzinfo=central_time))
async def deadline_reminders():

    await sync_canvas_feeds()
    await sync_d2l_feeds()

    today = datetime.now(central_time).date()

    today_string = today.isoformat()

    deadlines = get_deadlines_by_date(today_string)

    for deadline in deadlines:

        user_id = deadline[0]
        course_name = deadline[1]
        assignment_name = deadline[2]
        due_date = deadline[3]
        due_time = deadline[4]

        user = await bot.fetch_user(user_id)

        await user.send(
            f"Reminder! **{assignment_name}** for **{course_name}** is due today!"
        )

@bot.event
async def on_ready():

    bot.tree.copy_global_to(guild=SERVER_GUILD_ID)
    await bot.tree.sync(guild=SERVER_GUILD_ID)

    if not deadline_reminders.is_running():
        deadline_reminders.start()

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

class D2LConfirmView(discord.ui.View):

    def __init__(self, deadlines, user_id, calendar_url):
        super().__init__()

        self.deadlines = deadlines
        self.user_id = user_id
        self.calendar_url = calendar_url

    @discord.ui.button(
        label="Confirm",
        style=discord.ButtonStyle.success
    )
    async def confirm_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        save_d2l_feed(
            self.user_id,
            self.calendar_url
        )

        for deadline in self.deadlines:

            save_d2l_deadline(
                self.user_id,
                deadline["course_name"],
                deadline["name"],
                deadline["due_date"],
                deadline["due_time"],
                deadline["d2l_uid"]
            )

        await interaction.response.edit_message(
            content=f"Saved {len(self.deadlines)} D2L deadlines!",
            view=None
        )

        print("D2L deadlines saved")

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.danger
    )
    async def cancel_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.edit_message(
            content="D2L import cancelled.",
            view=None
        )

class D2LCalendarModal(discord.ui.Modal, title="Connect D2L Calendar"):

    calendar_url = discord.ui.TextInput(
        label="D2L calendar feed URL",
        placeholder="Paste your D2L .ics link here",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):

        await interaction.response.defer(
            ephemeral=True,
            thinking=True
        )

        url = self.calendar_url.value.strip()

        try:

            print("Fetching D2L calendar")

            deadlines = await get_d2l_deadlines(url)

            print(f"Found {len(deadlines)} D2L deadlines")

            if len(deadlines) == 0:
                await interaction.edit_original_response(
                    content="I couldn't find any upcoming D2L deadlines."
                )
                return

            deadline_text = ""

            for deadline in deadlines[:10]:

                deadline_text += (
                    f"**{deadline['name']}**\n"
                    f"Course: {deadline['course_name']}\n"
                    f"Date: {deadline['due_date']}\n"
                    f"Time: {deadline['due_time'] or 'Not specified'}\n\n"
                )

            if len(deadlines) > 10:
                deadline_text += (
                    f"...and {len(deadlines) - 10} more deadlines.\n"
                )

            await interaction.edit_original_response(
                content=(
                    f"Here's what I found from D2L:\n\n"
                    f"{deadline_text}\n"
                    f"**Total: {len(deadlines)} deadlines**"
                ),
                view=D2LConfirmView(
                    deadlines,
                    interaction.user.id,
                    url
                )
            )

        except Exception as error:

            print(
                f"D2L ERROR: "
                f"{type(error).__name__}: {error}"
            )

            await interaction.edit_original_response(
                content="Something went wrong while reading your D2L calendar."
            )

class CanvasConfirmView(discord.ui.View):

    def __init__(self, deadlines, user_id, calendar_url):
        super().__init__()

        self.deadlines = deadlines
        self.user_id = user_id
        self.calendar_url = calendar_url

    @discord.ui.button(
        label="Confirm",
        style=discord.ButtonStyle.success
    )
    async def confirm_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        # Save the user's Canvas calendar link
        save_canvas_feed(
            self.user_id,
            self.calendar_url
        )

        # Save or update every Canvas deadline
        for deadline in self.deadlines:

            save_canvas_deadline(
                self.user_id,
                deadline["course_name"],
                deadline["name"],
                deadline["due_date"],
                deadline["due_time"],
                deadline["canvas_uid"]
            )

        await interaction.response.edit_message(
            content=f"Saved {len(self.deadlines)} Canvas deadlines!",
            view=None
        )

        print("Canvas deadlines saved")

    @discord.ui.button(
        label="Cancel",
        style=discord.ButtonStyle.danger
    )
    async def cancel_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.edit_message(
            content="Canvas import cancelled.",
            view=None
        )

class CanvasCalendarModal(discord.ui.Modal, title="Connect Canvas Calendar"):

    calendar_url = discord.ui.TextInput(
        label="Canvas calendar feed URL",
        placeholder="Paste your Canvas .ics link here",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):

        await interaction.response.defer(
            ephemeral=True,
            thinking=True
        )

        url = self.calendar_url.value.strip()

        try:

            print("Fetching Canvas calendar")

            deadlines = await get_canvas_deadlines(url)

            print(f"Found {len(deadlines)} Canvas events")

            if len(deadlines) == 0:
                await interaction.edit_original_response(
                    content="I couldn't find any upcoming Canvas deadlines."
                )
                return

            deadline_text = ""

            # Only preview first 10 so Discord message
            # doesn't become gigantic
            for deadline in deadlines[:10]:

                deadline_text += (
                    f"**{deadline['name']}**\n"
                    f"Date: {deadline['due_date']}\n"
                    f"Time: {deadline['due_time'] or 'Not specified'}\n\n"
                )

            if len(deadlines) > 10:
                deadline_text += (
                    f"...and {len(deadlines) - 10} more events.\n"
                )

            await interaction.edit_original_response(
                content=(
                    f"Here's what I found from Canvas:\n\n"
                    f"{deadline_text}\n"
                    f"**Total: {len(deadlines)} events**"
                ),
                view=CanvasConfirmView(
                    deadlines,
                    interaction.user.id,
                    url
                )
            )

        except Exception as error:

            print(
                f"CANVAS ERROR: "
                f"{type(error).__name__}: {error}"
            )

            await interaction.edit_original_response(
                content="Something went wrong while reading your Canvas calendar."
            )

class DeadlineConfirmView(discord.ui.View):

    def __init__(self, result, user_id):
        super().__init__()

        self.result = result
        self.user_id = user_id

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.success)
    async def confirm_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        for deadline in self.result.deadlines:
            save_deadline(
                self.user_id,
                self.result.course_name,
                deadline.name,
                deadline.due_date,
                deadline.due_time
            )

        await interaction.response.edit_message(
            content=f"Saved {len(self.result.deadlines)} deadlines for {self.result.course_name}!",
            view=None
        )

        print("deadlines saved")

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def cancel_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.edit_message(
            content="Syllabus import cancelled.",
            view=None
        )

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

            print("Gemini responded")
            print(result)

            deadline_text = f"**{result.course_name}**\n\n"

            for deadline in result.deadlines:
                deadline_text += (
                    f"**{deadline.name}**\n"
                    f"Date: {deadline.due_date}\n"
                    f"Time: {deadline.due_time or 'Not specified'}\n\n"
                )

            await interaction.edit_original_response(
                content=f"Here's what I found:\n\n{deadline_text}",
                view=DeadlineConfirmView(result, interaction.user.id)
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
            print("Gemini responded")
            print(result)

            deadline_text = f"**{result.course_name}**\n\n"

            for deadline in result.deadlines:
                deadline_text += (
                    f"**{deadline.name}**\n"
                    f"Date: {deadline.due_date}\n"
                    f"Time: {deadline.due_time or 'Not specified'}\n\n"
                )

            await interaction.edit_original_response(
                content=f"Here's what I found:\n\n{deadline_text}",
                view=DeadlineConfirmView(result, interaction.user.id)
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
            print("Gemini responded")
            print(result)

            deadline_text = f"**{result.course_name}**\n\n"

            for deadline in result.deadlines:
                deadline_text += (
                    f"**{deadline.name}**\n"
                    f"Date: {deadline.due_date}\n"
                    f"Time: {deadline.due_time or 'Not specified'}\n\n"
                )

            await interaction.edit_original_response(
                content=f"Here's what I found:\n\n{deadline_text}",
                view=DeadlineConfirmView(result, interaction.user.id)
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

@bot.tree.command(
    name="connectd2l",
    description="Connect your D2L calendar"
)
async def connectd2l(interaction: discord.Interaction):

    await interaction.response.send_modal(
        D2LCalendarModal()
    )

@bot.tree.command(
    name="connectcanvas",
    description="Connect your Canvas calendar"
)
async def connectcanvas(interaction: discord.Interaction):

    await interaction.response.send_modal(
        CanvasCalendarModal()
    )

@bot.tree.command(
    name="upcoming",
    description="Show deadlines due in the next 7 days"
)
async def upcoming(interaction: discord.Interaction):

    today = datetime.now(central_time).date()

    end_date = today + timedelta(days=7)

    deadlines = get_upcoming_deadlines(
        interaction.user.id,
        today.isoformat(),
        end_date.isoformat()
    )

    if len(deadlines) == 0:
        await interaction.response.send_message(
            "You don't have any deadlines due in the next 7 days!",
            ephemeral=True
        )
        return

    deadline_text = ""

    for deadline in deadlines[:10]:

        course_name = deadline[0]
        assignment_name = deadline[1]
        due_date = deadline[2]
        due_time = deadline[3]

        deadline_text += (
            f"**{assignment_name}**\n"
            f"Course: {course_name}\n"
            f"Date: {due_date}\n"
            f"Time: {due_time or 'Not specified'}\n\n"
        )

    if len(deadlines) > 10:
        deadline_text += (
            f"...and {len(deadlines) - 10} more deadlines."
        )

    await interaction.response.send_message(
        f"Here are your upcoming deadlines:\n\n{deadline_text}",
        ephemeral=True
    )

bot.run(discord_token, log_handler=handler, log_level=logging.DEBUG)