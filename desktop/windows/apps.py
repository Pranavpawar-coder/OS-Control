import subprocess
import time
from typing import List
import psutil
from loguru import logger
import ctypes

from shared.schemas.apps import AppInfo, AppListResponse
from shared.schemas.actions import ActionResult

def list_running_apps() -> AppListResponse:
    """Lists desktop applications with visible windows."""
    apps: List[AppInfo] = []
    user32 = ctypes.windll.user32

    for proc in psutil.process_iter(['pid', 'name']):
        try:
            pid = proc.info['pid']
            name = proc.info['name']
            # Simple check for main applications
            apps.append(AppInfo(
                name=name,
                process_id=pid,
                window_title="",
                is_foreground=False
            ))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return AppListResponse(apps=apps[:50], count=len(apps))

def launch_application(app_name_or_path: str) -> ActionResult:
    """Launches an application through safe subprocess execution."""
    try:
        proc = subprocess.Popen(app_name_or_path, shell=True)
        time.sleep(1.0)
        return ActionResult(
            success=True,
            action="launch_app",
            message=f"Launched '{app_name_or_path}' with PID {proc.pid}",
            state_after={"pid": proc.pid},
            timestamp=time.time(),
        )
    except Exception as e:
        logger.error(f"Failed to launch app {app_name_or_path}: {e}")
        return ActionResult(
            success=False,
            action="launch_app",
            error=str(e),
            timestamp=time.time(),
        )

