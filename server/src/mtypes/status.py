from rich.console import RenderableType
from rich.style import StyleType
from rich.status import Status as St

__all__ = ["Status"]

class Status(St):
    """
    重写 rich 的 Status，让它知道自己是否正在播放
    """

    def __init__(
        self,
        status: RenderableType,
        *,
        spinner: str = "dots",
        spinner_style: StyleType = "status.spinner",
        speed: float = 1.0,
        refresh_per_second: float = 12.5,
    ):
        super().__init__(
            status,
            console=None,
            spinner=spinner,
            spinner_style=spinner_style,
            speed=speed,
            refresh_per_second=refresh_per_second,
        )
        self.started = False
        self.on = True

    def start(self) -> None:
        """开始播放"""
        if not self.started:
            self.started = True
            super().start()

    def stop(self) -> None:
        """停止播放"""
        if self.started:
            self.started = False
            super().stop()
