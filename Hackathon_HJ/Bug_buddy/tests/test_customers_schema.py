"""customers.json 스키마 유효성 테스트."""
import json
from pathlib import Path


CUSTOMERS_PATH = Path(__file__).parent.parent / "data" / "customers.json"


def test_customers_json_exists():
    """customers.json 파일이 존재해야 한다."""
    assert CUSTOMERS_PATH.exists(), f"customers.json not found at {CUSTOMERS_PATH}"


def test_customers_json_is_valid_list():
    """customers.json은 최소 1개 이상의 고객사를 포함한 리스트여야 한다."""
    with open(CUSTOMERS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list), "customers.json must be a list"
    assert len(data) >= 1, "customers.json must have at least one customer"


def test_customers_schema_fields():
    """각 고객사 항목은 id, name, source_targets 필드를 가져야 한다."""
    with open(CUSTOMERS_PATH, encoding="utf-8") as f:
        data = json.load(f)
    for customer in data:
        assert "id" in customer, f"Missing 'id' in {customer}"
        assert "name" in customer, f"Missing 'name' in {customer}"
        assert "source_targets" in customer, f"Missing 'source_targets' in {customer}"
        assert isinstance(customer["source_targets"], list), \
            f"'source_targets' must be a list in {customer}"
        for target in customer["source_targets"]:
            assert "label" in target, f"Missing 'label' in source_target {target}"
            assert "repo_url" in target, f"Missing 'repo_url' in source_target {target}"
            assert "branch" in target, f"Missing 'branch' in source_target {target}"
            assert "local_path" in target, f"Missing 'local_path' in source_target {target}"
            assert "paths" in target, f"Missing 'paths' in source_target {target}"
            assert "priority" in target, f"Missing 'priority' in source_target {target}"
