import asyncio
import json

import websockets
from rich.console import Console

WS_URL = "wss://api.translateprojects.dev/ws/progress/{task_id}/"
# Progress only arrives after each AI batch, so allow for a slow batch before giving up
IDLE_TIMEOUT = 120

console = Console(log_time=True, log_path=False)


async def _listen(task_id, on_progress, idle_timeout):
    async with websockets.connect(WS_URL.format(task_id=task_id)) as ws:
        while True:
            message = await asyncio.wait_for(ws.recv(), idle_timeout)
            try:
                progress = float(json.loads(message).get("progress", 0))
            except (ValueError, AttributeError):
                continue
            on_progress(progress)
            if progress >= 100:
                return True


def wait_task(task_id, on_progress=lambda p: None, idle_timeout=IDLE_TIMEOUT):
    """Blocks until the task reports 100 %. Returns False on timeout or socket errors, never raises."""
    try:
        return asyncio.run(_listen(task_id, on_progress, idle_timeout))
    except asyncio.TimeoutError:
        console.log(
            f"⚠ [yellow]No progress for {idle_timeout}s on task {task_id}, continuing.[/]"
        )
    except (OSError, websockets.exceptions.WebSocketException) as e:
        console.log(f"⚠ [yellow]Progress socket failed ({e}), continuing.[/]")
    return False
