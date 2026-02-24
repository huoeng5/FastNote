from DesktopAssistant.utils.helpers import infer_content_type, normalize_tags, parse_tags


def test_parse_tags_removes_duplicates_and_whitespace():
    tags = parse_tags(" 工作   账号 工作  截图 ")
    assert tags == ["工作", "账号", "截图"]


def test_infer_content_type_cases():
    assert infer_content_type(text="abc", image_path="") == "text"
    assert infer_content_type(text="", image_path="images/a.png") == "screenshot"
    assert infer_content_type(text="abc", image_path="images/a.png") == "mixed"


def test_normalize_tags_with_alias_map():
    alias_map = {"1": "工作", "9": "待办 紧急"}
    tags = normalize_tags("1 项目 1 9", alias_map=alias_map)
    assert tags == ["工作", "项目", "待办", "紧急"]
