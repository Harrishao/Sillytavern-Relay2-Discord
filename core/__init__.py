"""
Sillytavern-Session-Manager 核心模块
从 NC-Relay2ST 提取的 SillyTavern 无头浏览器交互核心，平台无关
"""

from .config import ST_URL, HEADLESS_MODE, VIEWPORT_WIDTH, SCREENSHOT_DIR
from .browser import (
    init_browser,
    close_browser,
    refresh_page,
    dismiss_toasts,
    get_page,
)
from .interaction import (
    inject_message,
    wait_for_response,
    send_message,
    swipe_left,
    swipe_right,
    regenerate,
    cancel_processing,
)
from .screenshot import (
    capture_screenshot,
    capture_full_screenshot,
)
from .api import (
    fetch_characters,
    fetch_recent_chats,
    fetch_character_chats,
    open_chat,
    delete_messages,
    delete_chat,
    fetch_personas,
    select_persona,
    get_current_persona,
)

# --- 处理锁：防止并发消息注入导致ST状态混乱 ---

_processing_lock = False


def acquire_lock() -> bool:
    """获取处理锁，返回True表示成功获取"""
    global _processing_lock
    if _processing_lock:
        return False
    _processing_lock = True
    return True


def release_lock():
    """释放处理锁"""
    global _processing_lock
    _processing_lock = False


def is_locked() -> bool:
    """检查是否有正在处理的操作"""
    return _processing_lock
