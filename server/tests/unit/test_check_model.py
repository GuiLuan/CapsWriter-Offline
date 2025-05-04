import pytest
from unittest.mock import patch
from pathlib import Path

from src.utils.check_model import check_model
from src.config import ModelPaths


@pytest.mark.unit
def test_check_model_all_exist(monkeypatch):
    """测试所有模型文件都存在的情况"""

    # 模拟所有Path.exists()返回True
    monkeypatch.setattr(Path, "exists", lambda self: True)

    # 模拟console.print和sys.exit
    with (
        patch("src.utils.check_model.console.print") as mock_print,
        patch("src.utils.check_model.sys.exit") as mock_exit,
    ):
        check_model()

        # 验证没有调用print和exit
        mock_print.assert_not_called()
        mock_exit.assert_not_called()


@pytest.mark.unit
def test_check_model_missing_file(monkeypatch):
    """测试模型文件不存在的情况"""

    # 模拟paraformer_path不存在
    def mock_exists(self):
        return not str(self).endswith("model.int8.onnx")

    monkeypatch.setattr(Path, "exists", mock_exists)

    # 模拟console.print、sys.exit和input
    with (
        patch("src.utils.check_model.console.print") as mock_print,
        patch("src.utils.check_model.sys.exit") as mock_exit,
        patch("builtins.input", return_value=""),
    ):
        check_model()

        # 验证打印了错误信息
        mock_print.assert_called_once()
        assert "未找到" in mock_print.call_args[0][0]
        assert "paraformer-offline-zh" in mock_print.call_args[0][0]

        # 验证调用了exit
        mock_exit.assert_called_once()


@pytest.mark.unit
def test_check_model_skip_private_attr(monkeypatch):
    """测试跳过私有属性"""

    # 记录检查了哪些路径
    checked_paths = []

    def mock_exists(self):
        checked_paths.append(str(self))
        return True

    monkeypatch.setattr(Path, "exists", mock_exists)

    with (
        patch("src.utils.check_model.console.print"),
        patch("src.utils.check_model.sys.exit"),
    ):
        check_model()

        # 验证没有检查私有属性_BASE_DIR
        assert all(not path.endswith("_BASE_DIR") for path in checked_paths)
        # 验证检查了所有公共属性
        assert len(checked_paths) == len(
            [attr for attr in dir(ModelPaths) if not attr.startswith("_")]
        )
