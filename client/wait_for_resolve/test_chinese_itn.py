from importlib import reload
from unittest.mock import Mock, patch

import pytest

from src.utils.chinese_itn import chinese_to_num
from src.utils import chinese_itn


@pytest.mark.unit
class TestChineseITN:
    """
    测试 src/utils/chinese_itn.py 中的 chinese_to_num 函数
    """

    def test_basic_conversion(self):
        """测试基本数字转换"""
        assert chinese_to_num("一二三") == "123"
        assert chinese_to_num("幺二三点四五六") == "123.456"

    def test_value_conversion(self):
        """测试数值转换"""
        assert chinese_to_num("一百二十三") == "123"
        assert chinese_to_num("十二万三千四百五十六") == "123456"
        assert chinese_to_num("一千二百三十四点五六") == "1234.56"
        assert chinese_to_num("一百零五") == "105"
        assert chinese_to_num("点一") == "点一"

    def test_percent_conversion(self):
        """测试百分数转换"""
        assert chinese_to_num("百分之五十") == "50%"
        assert chinese_to_num("百分之十二点五") == "12.5%"

    def test_fraction_conversion(self):
        """测试分数转换"""
        assert chinese_to_num("三分之二") == "2/3"
        assert (
            chinese_to_num("百分之五十") == "50%"
        )  # Note: This test case seems redundant with test_percent_conversion

    def test_ratio_conversion(self):
        """测试比值转换"""
        assert chinese_to_num("一比二") == "1:2"
        assert chinese_to_num("三比四点五") == "3:4.5"

    def test_time_conversion(self):
        """测试时间转换"""
        assert chinese_to_num("十二点三十四分") == "12:34"
        assert chinese_to_num("十二点三十四分五十六秒") == "12:34:56"
        assert chinese_to_num("十二分三十四秒") == "12:34"

    def test_date_conversion(self):
        """测试日期转换"""
        assert chinese_to_num("二零二五年十月") == "二零二五年十月"
        assert chinese_to_num("二零二五年十月五日") == "2025年10月5日"
        assert chinese_to_num("二零二五年十月五号") == "2025年10月5号"

    def test_idiom_filter(self):
        """测试成语过滤"""
        assert chinese_to_num("乱七八糟") == "乱七八糟"
        assert chinese_to_num("五零四散") == "五零四散"
        assert chinese_to_num("五十步笑百步") == "五十步笑百步"

    def test_unit_stripping(self):
        """测试单位剥离"""
        assert chinese_to_num("一百二十三只") == "123只"
        assert chinese_to_num("一二三个") == "123个"

    def test_single_one(self):
        """测试单个'一'不转换"""
        assert chinese_to_num("一") == "一"
        assert chinese_to_num("一个") == "一个"

    def test_edge_cases(self):
        """测试边界情况"""
        assert chinese_to_num("") == ""
        assert chinese_to_num("一二三点") == "一二三点"
        assert chinese_to_num("abc一二三") == "abc123"
        assert chinese_to_num("一二三abc") == "123abc"

    def test_exception_handling(self):
        """测试异常处理路径"""
        # 创建一个模拟的re.Match对象
        mock_match = Mock()
        mock_match.group.side_effect = lambda x: {
            1: None,  # head
            2: "一二三",  # 使用会被pure_num匹配的字符串
        }.get(x)
        mock_match.regs = [(0, 0), (0, 0), (0, 3)]  # 模拟匹配位置
        mock_match.string = "一二三"

        try:
            # 使用patch来mock convert_pure_num函数
            with patch("src.utils.chinese_itn.convert_pure_num") as mock_convert:
                # 设置mock函数抛出异常
                mock_convert.side_effect = ValueError("模拟异常")

                # 调用replace函数，应该捕获异常并返回原始字符串
                result = chinese_itn.replace(mock_match)
                assert result == "一二三", "异常情况下应返回原始字符串"
        finally:
            # 确保即使测试失败也能恢复原始状态
            reload(chinese_itn)  # 彻底重新加载模块
