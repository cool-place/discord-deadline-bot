import aiohttp
from icalendar import Calendar
from datetime import datetime
from zoneinfo import ZoneInfo


central_time = ZoneInfo("America/Chicago")


async def get_d2l_deadlines(url):

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

        summary = str(event.get("SUMMARY", ""))

        # D2L creates several calendar events for some assignments.
        # We only want the actual due event.
        if not summary.endswith(" - Due"):
            continue

        name = summary.removesuffix(" - Due").strip()

        course_name = str(
            event.get("LOCATION", "D2L")
        )

        uid = event.get("UID")

        if uid is None:
            continue

        uid = str(uid)

        start = event.decoded("DTSTART")

        if isinstance(start, datetime):

            if start.tzinfo is not None:
                start = start.astimezone(central_time)

            due_date = start.date()
            due_time = start.strftime("%H:%M")

        else:
            due_date = start
            due_time = None

        # Don't import assignments that already passed
        if due_date < today:
            continue

        deadlines.append({
            "course_name": course_name,
            "name": name,
            "due_date": due_date.isoformat(),
            "due_time": due_time,
            "d2l_uid": uid
        })

    return deadlines