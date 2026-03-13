import pytest
import json
from pathlib import Path
from src.code_searcher import load_customers, get_customer_by_name, search_files


# === customers.json 로더 테스트 (5) ===

def test_load_customers_returns_list(tmp_path):
    data = [{"id": "test", "name": "테스트", "source_targets": []}]
    (tmp_path / "customers.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    result, err = load_customers(str(tmp_path / "customers.json"))
    assert isinstance(result, list) and err is None


def test_load_customers_missing_file():
    result, err = load_customers("/nonexistent/customers.json")
    assert result == [] and err is not None


def test_load_customers_invalid_json(tmp_path):
    (tmp_path / "customers.json").write_text("not json", encoding="utf-8")
    result, err = load_customers(str(tmp_path / "customers.json"))
    assert result == [] and err is not None


def test_get_customer_by_name_found():
    customers = [{"id": "a", "name": "대웅제약", "source_targets": []}]
    result = get_customer_by_name(customers, "대웅제약")
    assert result["id"] == "a"


def test_get_customer_by_name_not_found():
    result = get_customer_by_name([], "없는회사")
    assert result is None


# === search_files 테스트 (7) ===

def test_search_files_finds_keyword(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "login.py").write_text("def login_user(): pass", encoding="utf-8")
    results, err = search_files(str(tmp_path), [""], ["login"], top_n=5)
    assert err is None
    assert any("login.py" in r["path"] for r in results)


def test_search_files_empty_keywords(tmp_path):
    results, err = search_files(str(tmp_path), [""], [], top_n=5)
    assert results == [] and err is not None


def test_search_files_ignores_hidden_dirs(tmp_path):
    hidden = tmp_path / ".git"
    hidden.mkdir()
    (hidden / "config.py").write_text("login secret", encoding="utf-8")
    visible = tmp_path / "src"
    visible.mkdir()
    (visible / "app.py").write_text("login app", encoding="utf-8")
    results, err = search_files(str(tmp_path), [""], ["login"], top_n=5)
    assert not any(".git" in r["path"] for r in results)


def test_search_files_respects_top_n(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    for i in range(10):
        (src / f"file{i}.py").write_text(f"keyword match {i}", encoding="utf-8")
    results, err = search_files(str(tmp_path), [""], ["keyword"], top_n=3)
    assert len(results) <= 3


def test_search_files_skips_non_code_files(tmp_path):
    (tmp_path / "image.png").write_bytes(b"\x89PNG binary data")
    (tmp_path / "code.py").write_text("keyword here", encoding="utf-8")
    results, err = search_files(str(tmp_path), [""], ["keyword"], top_n=5)
    assert not any("image.png" in r["path"] for r in results)


def test_search_files_returns_excerpt(tmp_path):
    (tmp_path / "sample.java").write_text("public void processLogin() {}", encoding="utf-8")
    results, err = search_files(str(tmp_path), [""], ["login"], top_n=5)
    assert results and "excerpt" in results[0]


def test_search_files_multiple_keywords(tmp_path):
    (tmp_path / "auth.py").write_text("def authenticate_user(): validate_token()", encoding="utf-8")
    (tmp_path / "unrelated.py").write_text("def print_hello(): pass", encoding="utf-8")
    results, err = search_files(str(tmp_path), [""], ["authenticate", "token"], top_n=5)
    assert any("auth.py" in r["path"] for r in results)
