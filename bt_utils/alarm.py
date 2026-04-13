import threading
import os
from typing import Optional


class AlarmPlayer:
    """报警播放器

    使用pygame播放报警音效，支持自定义音效文件和音量控制。
    使用单例模式。
    """
    _instance = None
    _pygame_initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _init_pygame(self):
        if not self._pygame_initialized:
            try:
                import pygame
                pygame.mixer.init()
                self._pygame_initialized = True
            except ImportError:
                pass

    def play(self, sound_path: str = None, volume: int = None,
             wait_complete: bool = True) -> None:
        """播放报警音

        Args:
            sound_path: 音效文件路径
            volume: 音量 (0-100)
            wait_complete: 是否等待播放完成
        """
        self._init_pygame()

        if not self._pygame_initialized:
            return

        import pygame

        resolved_path = self._resolve_sound_path(sound_path)
        if not resolved_path:
            return

        def _play():
            try:
                sound = pygame.mixer.Sound(resolved_path)

                if volume is not None:
                    sound.set_volume(volume / 100)
                else:
                    sound.set_volume(0.7)

                sound.play()

                if wait_complete:
                    pygame.time.wait(int(sound.get_length() * 1000))

            except Exception as e:
                print(f"[WARN] 报警播放错误: {e}")

        if wait_complete:
            _play()
        else:
            thread = threading.Thread(target=_play, daemon=True)
            thread.start()

    def _resolve_sound_path(self, sound_path: str = None) -> Optional[str]:
        """解析音效文件路径
        
        Args:
            sound_path: 用户指定的路径
            
        Returns:
            实际的音效文件路径
        """
        if sound_path and os.path.exists(sound_path):
            return sound_path
        
        try:
            from bt_utils.resource_manager import get_resource_manager
            rm = get_resource_manager()
            default_path = rm.get_alarm_sound_path()
            if os.path.exists(default_path):
                return default_path
        except ImportError:
            pass
        
        fallback_path = os.path.join(os.path.dirname(__file__), "..", "assets", "sounds", "alarm.mp3")
        if os.path.exists(fallback_path):
            return os.path.normpath(fallback_path)
        
        return None

    def stop(self) -> None:
        """停止播放（只停止Sound通道，不影响music通道）"""
        if self._pygame_initialized:
            try:
                import pygame
                pygame.mixer.stop()
            except Exception:
                pass

    def play_start_sound(self) -> None:
        """播放开始运行的音频
        
        使用 ResourceManager 获取开始音效路径，兼容开发环境和打包环境。
        """
        self._init_pygame()
        
        if not self._pygame_initialized:
            return
        
        import pygame
        
        try:
            from bt_utils.resource_manager import get_resource_manager
            rm = get_resource_manager()
            sound_file = rm.get_start_sound_path()
        except ImportError:
            sound_file = self._resolve_sound_path(None)
        
        if not sound_file or not os.path.exists(sound_file):
            return
        
        try:
            pygame.mixer.music.load(sound_file)
            pygame.mixer.music.set_volume(0.7)
            pygame.mixer.music.play()
        except Exception as e:
            print(f"[WARN] 播放开始运行音效失败: {e}")

    def play_stop_sound(self) -> None:
        """播放停止运行的音频
        
        使用 ResourceManager 获取停止音效路径，兼容开发环境和打包环境。
        """
        self._init_pygame()
        
        if not self._pygame_initialized:
            return
        
        import pygame
        
        try:
            from bt_utils.resource_manager import get_resource_manager
            rm = get_resource_manager()
            sound_file = rm.get_stop_sound_path()
        except ImportError:
            sound_file = None
        
        if not sound_file or not os.path.exists(sound_file):
            sound_file = self._resolve_sound_path(None)
        
        if not sound_file or not os.path.exists(sound_file):
            return
        
        try:
            pygame.mixer.music.load(sound_file)
            pygame.mixer.music.set_volume(0.7)
            pygame.mixer.music.play()
        except Exception as e:
            print(f"[WARN] 播放停止运行音效失败: {e}")
