import os
import re
import time
import base64
import subprocess
import xml.etree.ElementTree as ET
from typing import Optional, List, Dict, Any
from loguru import logger

from shared.schemas.elements import ElementInfo, BoundingBox, UITreeResponse
from shared.schemas.actions import ActionResult
from shared.schemas.screen import ScreenInfo
from shared.schemas.apps import AppInfo, AppListResponse
from shared.validation.validators import registry

class AndroidBridge:
    def __init__(self, adb_path: Optional[str] = None):
        if not adb_path:
            local_appdata = os.environ.get("LOCALAPPDATA", "")
            sdk_adb = os.path.join(local_appdata, "Android", "Sdk", "platform-tools", "adb.exe")
            if os.path.exists(sdk_adb):
                self.adb_path = sdk_adb
            else:
                self.adb_path = "adb"
        else:
            self.adb_path = adb_path

        self.device_id: Optional[str] = None
        self._cached_devices: List[str] = []
        self._last_device_check: float = 0.0
        self._init_device()

    def _init_device(self):
        devices = self.get_connected_devices()
        if devices:
            self.device_id = devices[0]
            logger.info(f"Android Bridge connected to device: {self.device_id}")
        else:
            self.device_id = None

    def get_connected_devices(self) -> List[str]:
        now = time.time()
        if self._cached_devices and (now - self._last_device_check < 60.0):
            return self._cached_devices
        try:
            res = subprocess.run([self.adb_path, "devices"], capture_output=True, text=True, timeout=8.0)
            lines = res.stdout.strip().split("\n")
            devices = []
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 2 and parts[1] == "device":
                    devices.append(parts[0])
            self._cached_devices = devices
            self._last_device_check = now
            return devices
        except Exception as e:
            logger.error(f"Error checking ADB devices: {e}")
            return self._cached_devices

    def run_cmd(self, args: List[str], timeout: float = 8.0) -> subprocess.CompletedProcess:
        cmd = [self.adb_path]
        if self.device_id:
            cmd.extend(["-s", self.device_id])
        cmd.extend(args)
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    def run_cmd_bytes(self, args: List[str], timeout: float = 8.0) -> bytes:
        cmd = [self.adb_path]
        if self.device_id:
            cmd.extend(["-s", self.device_id])
        cmd.extend(args)
        return subprocess.run(cmd, capture_output=True, timeout=timeout).stdout

    def run_batch_shell(self, commands: List[str]) -> str:
        """Executes multiple shell commands in a single adb round-trip."""
        joined = " && ".join(commands)
        return self.run_cmd(["shell", joined]).stdout

    def get_screen_info(self) -> ScreenInfo:
        if not self.device_id:
            self._init_device()
        if not self.device_id:
            return ScreenInfo(
                width=0, height=0, active_app="No Device",
                window_title="Disconnected", process_id=0, timestamp=time.time()
            )

        # Batch resolution + focused app in one round-trip
        batched = self.run_batch_shell(["wm size", "dumpsys window | grep -E 'mCurrentFocus'"])
        w, h = 1080, 2400
        m = re.search(r"(\d+)x(\d+)", batched)
        if m:
            w, h = int(m.group(1)), int(m.group(2))

        active_app = "Android Screen"
        for line in batched.splitlines():
            if "mCurrentFocus" in line:
                active_app = line.strip()
                break

        return ScreenInfo(
            width=w, height=h, active_app=active_app,
            window_title=active_app, process_id=0, timestamp=time.time()
        )

    def get_ui_tree(self, compressed: bool = True) -> UITreeResponse:
        """Fast UI tree extraction with compressed hierarchy."""
        if not self.device_id:
            self._init_device()

        # Dump to stdout directly if possible, or single file pipeline
        dump_cmd = "uiautomator dump --compressed /sdcard/u.xml && cat /sdcard/u.xml" if compressed else "uiautomator dump /sdcard/u.xml && cat /sdcard/u.xml"
        xml_content = self.run_cmd(["shell", dump_cmd]).stdout

        elements: List[ElementInfo] = []
        if not xml_content or "<hierarchy" not in xml_content:
            return UITreeResponse(
                active_app="Android UI", window_title="Active Window",
                root_id="root", elements=[], count=0, timestamp=time.time()
            )

        try:
            # Strip preamble if any
            idx = xml_content.find("<hierarchy")
            if idx != -1:
                xml_content = xml_content[idx:]

            root = ET.fromstring(xml_content)
            for node in root.iter('node'):
                text = node.get('text', '')
                content_desc = node.get('content-desc', '')
                res_id = node.get('resource-id', '')
                cls_name = node.get('class', '')
                clickable = node.get('clickable', 'false') == 'true'
                enabled = node.get('enabled', 'true') == 'true'
                focused = node.get('focused', 'false') == 'true'
                bounds_str = node.get('bounds', '')

                label = text or content_desc
                if not label and not res_id and not clickable:
                    continue

                bounds = None
                m = re.findall(r'\[(\d+),(\d+)\]', bounds_str)
                if len(m) == 2:
                    left, top = int(m[0][0]), int(m[0][1])
                    right, bottom = int(m[1][0]), int(m[1][1])
                    bounds = BoundingBox(
                        left=left, top=top, right=right, bottom=bottom,
                        width=right - left, height=bottom - top
                    )

                actions = []
                if clickable:
                    actions.append("click")
                if "EditText" in cls_name:
                    actions.append("set_value")

                role = cls_name.split('.')[-1] if cls_name else "View"
                elem_id = registry.register(bounds)

                elements.append(ElementInfo(
                    id=elem_id,
                    name=label,
                    type=role,
                    automation_id=res_id if res_id else None,
                    class_name=cls_name,
                    enabled=enabled,
                    focused=focused,
                    visible=True,
                    actions=actions,
                    value=text if text else None,
                    bounds=bounds
                ))
        except Exception as e:
            logger.error(f"Error parsing UI dump: {e}")

        return UITreeResponse(
            active_app="Android Foreground",
            window_title="Android Screen",
            root_id="root",
            elements=elements,
            count=len(elements),
            timestamp=time.time()
        )

    def click_element(self, element_id: str) -> ActionResult:
        bounds: Optional[BoundingBox] = registry.get(element_id)
        if not bounds:
            return ActionResult(
                success=False, action="click", element_id=element_id,
                error="Element expired or not found. Refresh UI tree.", timestamp=time.time()
            )

        cx = bounds.left + bounds.width // 2
        cy = bounds.top + bounds.height // 2
        self.run_cmd(["shell", f"input tap {cx} {cy}"])

        return ActionResult(
            success=True, action="click", element_id=element_id,
            message=f"Tapped coordinates ({cx}, {cy})", timestamp=time.time()
        )

    def type_text(self, text: str) -> ActionResult:
        escaped_text = text.replace(" ", "%s")
        self.run_cmd(["shell", f"input text {escaped_text}"])
        return ActionResult(
            success=True, action="type_text",
            message=f"Typed text into Android view", timestamp=time.time()
        )

    def press_key(self, keycode_or_name: str) -> ActionResult:
        key_map = {
            "back": "4", "home": "3", "enter": "66",
            "tab": "61", "app_switch": "187", "volume_up": "24",
            "volume_down": "25", "power": "26"
        }
        code = key_map.get(keycode_or_name.lower(), keycode_or_name)
        self.run_cmd(["shell", f"input keyevent {code}"])
        return ActionResult(
            success=True, action="press_key",
            message=f"Sent key event {code}", timestamp=time.time()
        )

    def scroll(self, direction: str = "down") -> ActionResult:
        swipe_cmd = "input swipe 500 1400 500 600 150" if direction == "down" else "input swipe 500 600 500 1400 150"
        self.run_cmd(["shell", swipe_cmd])
        return ActionResult(
            success=True, action="scroll",
            message=f"Swiped {direction}", timestamp=time.time()
        )

    def launch_app(self, package_name: str) -> ActionResult:
        # Fast intent start
        self.run_cmd(["shell", f"monkey -p {package_name} -c android.intent.category.LAUNCHER 1"])
        return ActionResult(
            success=True, action="launch_app",
            message=f"Launched {package_name}", timestamp=time.time()
        )

    def take_screenshot(self) -> Dict[str, Any]:
        png_bytes = self.run_cmd_bytes(["exec-out", "screencap", "-p"])
        if png_bytes and len(png_bytes) > 100:
            return {
                "image_base64": base64.b64encode(png_bytes).decode('utf-8'),
                "format": "png",
                "size_bytes": len(png_bytes)
            }
        return {"error": "Failed to capture Android screen"}

    def get_app_list(self) -> AppListResponse:
        out = self.run_cmd(["shell", "pm list packages --user 0 -3"]).stdout
        apps = []
        for line in out.splitlines():
            if line.startswith("package:"):
                pkg = line.replace("package:", "").strip()
                apps.append(AppInfo(name=pkg, process_id=0, window_title=pkg, is_foreground=False))
        return AppListResponse(apps=apps, count=len(apps))

android_bridge = AndroidBridge()
