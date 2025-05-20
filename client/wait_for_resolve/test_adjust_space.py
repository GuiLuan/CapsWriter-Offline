import pytest

from src.utils.adjust_space import adjust_space


@pytest.mark.unit
class TestAdjustSpace:
    """测试 adjust_space 函数"""

    @pytest.mark.parametrize(
        "input_text, expected_output, cn_en, cn_digit, en_digit",
        [
            # test_compress_space cases
            ("中文测试", "中文测试", False, False, False),
            ("English Test", "English Test", False, False, False),
            ("中文 测试", "中文测试", False, False, False),
            ("中文      测试   ", "中文测试", False, False, False),
            ("English        Test", "English Test", False, False, False),
            ("中文English", "中文English", False, False, False),

            # test_chinese_english cases
            ("中 文English", "中文 English", True, False, False),
            ("中      文          English", "中文 English", True, False, False),

            # test_chinese_digit cases
            ("中文1", "中文 1", False, True, False),
            ("中文          1中文", "中文 1 中文", False, True, False),
            ("中文1English中文", "中文 1English中文", False, True, False),

            # test_english_digit cases
            ("English1", "English 1", False, False, True),
            ("English        1", "English 1", False, False, True),
            (" English中文1 ", "English中文1", False, False, True),
            ("English1中文 ", "English 1中文", False, False, True),

            # test_chinese_english_digit case
            ("中文1              中文English1中文English", "中文 1 中文 English 1 中文 English", True, True, True),
        ],
    )
    def test_adjust_space_parameterized(self, input_text, expected_output, cn_en, cn_digit, en_digit):
        """使用参数化测试 adjust_space 函数的各种情况"""
        assert adjust_space(input_text, cn_en=cn_en, cn_digit=cn_digit, en_digit=en_digit) == expected_output
