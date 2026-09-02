import aiohttp
from icalendar import Calendar
from datetime import datetime
from zoneinfo import ZoneInfo


central_time = ZoneInfo("America/Chicago")


async def get_canvas_deadlines(url):

    if url.startswith("webcal://"):
        url = url.replace("webcal://", "https://", 1)

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:

            response.raise_for_status()

            calendar_data = await response.read()

    calendar = Calendar.from_ical(calendar_data)

    deadlines = []

    today = datetime.now(central_time).date()

    for event in calendar.walk("VEVENT"):

        summary = str(event.get("SUMMARY", "Canvas Event"))

        name = summary
        course_name = "Canvas"

        if "[" in summary and summary.endswith("]"):

            name, course_info = summary.rsplit("[", 1)

            name = name.strip()

            course_info = course_info.rstrip("]").strip()

            if " - " in course_info:
                course_name = course_info.split(" - ")[0].strip()
            else:
                course_name = course_info

        start = event.decoded("DTSTART")

        uid = event.get("UID")

        if uid is None:
            continue

        uid = str(uid)

        if not uid.startswith("event-assignment-"):
            continue

        if isinstance(start, datetime):

            if start.tzinfo is not None:
                start = start.astimezone(central_time)

            due_date = start.date()
            due_time = start.strftime("%H:%M")

        else:
            due_date = start
            due_time = None

        # Don't import old events
        if due_date < today:
            continue

        deadlines.append({
            "course_name": course_name,
            "name": name,
            "due_date": due_date.isoformat(),
            "due_time": due_time,
            "canvas_uid": uid
        })

    return deadlines