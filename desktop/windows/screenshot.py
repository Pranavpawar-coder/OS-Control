import io
import base64
import ctypes
from ctypes import wintypes
from typing import Optional, Dict, Any
from loguru import logger
from PIL import Image

# Windows GDI constants
SRCCOPY = 0x00CC0020
DIB_RGB_COLORS = 0
BI_RGB = 0

class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ('biSize', wintypes.DWORD),
        ('biWidth', wintypes.LONG),
        ('biHeight', wintypes.LONG),
        ('biPlanes', wintypes.WORD),
        ('biBitCount', wintypes.WORD),
        ('biCompression', wintypes.DWORD),
        ('biSizeImage', wintypes.DWORD),
        ('biXPelsPerMeter', wintypes.LONG),
        ('biYPelsPerMeter', wintypes.LONG),
        ('biClrUsed', wintypes.DWORD),
        ('biClrImportant', wintypes.DWORD)
    ]

class BITMAPINFO(ctypes.Structure):
    _fields_ = [
        ('bmiHeader', BITMAPINFOHEADER),
        ('bmiColors', wintypes.DWORD * 3)
    ]

def capture_screen(region: Optional[Dict[str, int]] = None, scale: float = 0.5) -> Dict[str, Any]:
    """
    Captures primary screen using robust Win32 GDI calls directly.
    """
    try:
        user32 = ctypes.windll.user32
        gdi32 = ctypes.windll.gdi32

        # Support DPI awareness
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                user32.SetProcessDPIAware()
            except Exception:
                pass

        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)

        src_x, src_y = 0, 0
        w, h = width, height
        if region:
            src_x = region.get("left", 0)
            src_y = region.get("top", 0)
            w = region.get("width", width)
            h = region.get("height", height)

        hdesktop = user32.GetDesktopWindow()
        desktop_dc = user32.GetWindowDC(hdesktop)
        if not desktop_dc:
            desktop_dc = user32.GetDC(0)

        mem_dc = gdi32.CreateCompatibleDC(desktop_dc)
        bitmap = gdi32.CreateCompatibleBitmap(desktop_dc, w, h)
        old_bmp = gdi32.SelectObject(mem_dc, bitmap)

        gdi32.BitBlt(mem_dc, 0, 0, w, h, desktop_dc, src_x, src_y, SRCCOPY)

        bmi = BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = w
        bmi.bmiHeader.biHeight = -h  # top-down DIB
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 32
        bmi.bmiHeader.biCompression = BI_RGB

        buffer_len = w * h * 4
        buffer = (ctypes.c_char * buffer_len)()

        gdi32.GetDIBits(mem_dc, bitmap, 0, h, buffer, ctypes.byref(bmi), DIB_RGB_COLORS)

        # Cleanup GDI handles
        gdi32.SelectObject(mem_dc, old_bmp)
        gdi32.DeleteObject(bitmap)
        gdi32.DeleteDC(mem_dc)
        user32.ReleaseDC(hdesktop, desktop_dc)

        img = Image.frombuffer('RGBA', (w, h), buffer, 'raw', 'BGRA', 0, 1).convert('RGB')

        if scale != 1.0:
            new_size = (max(1, int(img.width * scale)), max(1, int(img.height * scale)))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        out_io = io.BytesIO()
        img.save(out_io, format="PNG", optimize=True)
        encoded = base64.b64encode(out_io.getvalue()).decode("utf-8")

        return {
            "image_base64": encoded,
            "width": img.width,
            "height": img.height,
            "format": "png",
        }
    except Exception as e:
        logger.error(f"GDI screenshot failed: {e}")
        return {"error": str(e), "image_base64": "", "width": 0, "height": 0, "format": "png"}
