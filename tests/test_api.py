import json
from api.services.agent_service import parse_structured_output, extract_stage


def test_parse_structured_output_extracts_recommendation():
    text = '''[推荐方案] 为你推荐3款：

```json
{
  "type": "recommendation",
  "products": [{"rank": 1, "name": "Test Product", "price": 299}],
  "verdict": "test verdict"
}
```

选第1款因为性价比最高。'''

    result = parse_structured_output(text)
    assert result["structured_data"] is not None
    assert result["structured_data"]["type"] == "recommendation"
    assert result["structured_data"]["products"][0]["name"] == "Test Product"
    assert "选第1款" in result["text"]


def test_parse_structured_output_plain_text():
    text = "[意图澄清] 入耳式还是头戴式？"
    result = parse_structured_output(text)
    assert result["structured_data"] is None
    assert "入耳式还是头戴式" in result["text"]


def test_extract_stage():
    assert extract_stage("[推荐方案] 为你推荐") == "推荐方案"
    assert extract_stage("[意图澄清] 好的") == "意图澄清"
    assert extract_stage("没有标签的回复") == "未知"
