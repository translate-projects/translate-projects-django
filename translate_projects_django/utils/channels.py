import json

import websockets
from rich.console import Console
from rich.progress import Progress

console = Console(log_time=True, log_path=False)


async def listen_progress(task_id, lang, message=None):
    url = f"wss://api.translateprojects.dev/ws/progress/{task_id}/"

    async with websockets.connect(url) as websocket:
        with Progress() as progress_bar:
            if not message:
                message = f"           📝 Sync Translations ({lang})... "
            task = progress_bar.add_task(message, total=100)
            last_progress = 0

            while not progress_bar.finished:
                response = await websocket.recv()
                try:
                    data = json.loads(response)
                    new_progress = float(data.get("progress", 0))

                    if new_progress > last_progress:
                        last_progress = new_progress
                        progress_bar.update(task, completed=new_progress)

                except json.JSONDecodeError:
                    console.log("❌ [red]Error:[/] Failed to decode JSON", response)
                if last_progress >= 100:
                    progress_bar.update(task, completed=100)
                    break
