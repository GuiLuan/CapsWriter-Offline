import pytest
from src.utils.chinese_itn import chinese_to_num


@pytest.mark.unit
def test_basic_conversion():
    """测试基本数字转换"""
    assert chinese_to_num("一二三") == "123"
    assert chinese_to_num("幺二三点四五六") == "123.456"


@pytest.mark.unit
def test_value_conversion():
    """测试数值转换"""
    assert chinese_to_num("一百二十三") == "123"
    assert chinese_to_num("十二万三千四百五十六") == "123456"
    assert chinese_to_num("一千二百三十四点五六") == "1234.56"
    assert chinese_to_num("一百零五") == "105"  # 测试零的情况
    assert chinese_to_num("点一") == "点一"  # 测试纯小数不转换


@pytest.mark.unit
def test_percent_conversion():
    """测试百分数转换"""
    assert chinese_to_num("百分之五十") == "50%"
    assert chinese_to_num("百分之十二点五") == "12.5%"


@pytest.mark.unit
def test_fraction_conversion():
    """测试分数转换"""
    assert chinese_to_num("三分之二") == "2/3"
    assert chinese_to_num("百分之五十") == "50%"


@pytest.mark.unit
def test_ratio_conversion():
    """测试比值转换"""
    assert chinese_to_num("一比二") == "1:2"
    assert chinese_to_num("三比四点五") == "3:4.5"


@pytest.mark.unit
def test_time_conversion():
    """测试时间转换"""
    assert chinese_to_num("十二点三十四分") == "12:34"
    assert chinese_to_num("十二点三十四分五十六秒") == "12:34:56"
    assert chinese_to_num("十二分三十四秒") == "12:34"


@pytest.mark.unit
def test_date_conversion():
    """测试日期转换"""
    assert chinese_to_num("二零二五年十月") == "二零二五年十月"
    assert chinese_to_num("二零二五年十月五日") == "2025年10月5日"
    assert chinese_to_num("二零二五年十月五号") == "2025年10月5号"  # 测试"号"的情况


@pytest.mark.unit
def test_idiom_filter():
    """测试成语过滤"""
    assert chinese_to_num("乱七八糟") == "乱七八糟"
    assert chinese_to_num("五零四散") == "五零四散"
    assert chinese_to_num("五十步笑百步") == "五十步笑百步"


@pytest.mark.unit
def test_unit_stripping():
    """测试单位剥离"""
    assert chinese_to_num("一百二十三只") == "123只"
    assert chinese_to_num("一二三个") == "123个"


@pytest.mark.unit
def test_single_one():
    """测试单个'一'不转换"""
    assert chinese_to_num("一") == "一"
    assert chinese_to_num("一个") == "一个"


@pytest.mark.unit
def test_edge_cases():
    """测试边界情况"""
    assert chinese_to_num("") == ""
    assert chinese_to_num("一二三点") == "一二三点"  # 当前实现不转换这种情况
    assert chinese_to_num("abc一二三") == "abc123"  # 混合字母数字
    assert chinese_to_num("一二三abc") == "123abc"  # 测试异常处理


@pytest.mark.unit
def test_exception_handling():
    """测试异常处理路径
    使用patch作为上下文管理器(with语句)是线程安全的，
    它会在退出with块后自动恢复原始函数，不会影响其他测试用例
    """
    from unittest.mock import Mock, patch

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

            from src.utils import chinese_itn

            # 调用replace函数，应该捕获异常并返回原始字符串
            result = chinese_itn.replace(mock_match)
            assert result == "一二三", "异常情况下应返回原始字符串"
    finally:
        # 确保即使测试失败也能恢复原始状态
        from importlib import reload
        from src.utils import chinese_itn

        reload(chinese_itn)  # 彻底重新加载模块
