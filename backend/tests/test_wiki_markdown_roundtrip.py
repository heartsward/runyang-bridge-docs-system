# -*- coding: utf-8 -*-
"""Wiki MD 副本读写回归测试（27.16）

覆盖两个线上 bug：
1. 保存后预览看不到改动 —— 根因在 API 层（save_markdown 未回写 documents.content），
   由 tests 之外的 e2e 覆盖；这里覆盖存储层。
2. 每保存一次就多一段 frontmatter —— 根因在 WikiStorage.update()，
   前端把全文（含 frontmatter）传回，旧实现又把磁盘 frontmatter 再拼一次。

关键断言：**无论怎么保存，文件里永远只有一段 frontmatter，且正文逐字节不变**。
"""
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).parent.parent
sys.path.insert(0, str(BACKEND))

from app.services.wiki.storage import (  # noqa: E402
    WikiStorage,
    join_frontmatter,
    split_frontmatter,
    strip_frontmatter_blocks,
)

BODY = "# 收费网准入配置说明\n\n账号 administrator，网关 10.9.0.223。\n\n## 备注\n\n- 列表项一\n- 列表项二\n"


@pytest.fixture
def store(tmp_path):
    return WikiStorage(wiki_dir=tmp_path)


def blocks(text: str) -> int:
    n, rest = 0, text
    while True:
        fm, body = split_frontmatter(rest)
        if not fm:
            return n
        n += 1
        rest = body


def make_doc(store, doc_id=1):
    store.write(
        doc_id=doc_id,
        title="收费网准入配置说明",
        source_file="收费网准入.docx",
        doc_type="docx",
        tags=["收费", "网络安全"],
        markdown_body=BODY,
        doc_category="操作规程",
    )
    return store.get_path(doc_id)


def test_write_creates_single_frontmatter(store):
    p = make_doc(store)
    assert blocks(p.read_text(encoding="utf-8")) == 1


def test_update_with_full_content_does_not_duplicate(store):
    """核心回归：前端传回"全文（含 frontmatter）"，保存后仍只有一段"""
    p = make_doc(store)
    full = p.read_text(encoding="utf-8")          # 模拟前端 GET 到的全文
    edited = full.replace("10.9.0.223", "10.9.0.224")

    store.update(1, edited)
    text = p.read_text(encoding="utf-8")
    assert blocks(text) == 1, "保存后出现了重复 frontmatter"
    assert "10.9.0.224" in text


def test_update_is_idempotent_over_many_saves(store):
    """连续保存 5 次（每次都带 frontmatter），块数必须恒为 1"""
    p = make_doc(store)
    for i in range(5):
        full = p.read_text(encoding="utf-8")
        store.update(1, full.replace("备注", f"备注{i}"))
        assert blocks(p.read_text(encoding="utf-8")) == 1, f"第 {i+1} 次保存后重复"
    assert blocks(p.read_text(encoding="utf-8")) == 1


def test_update_with_body_only(store):
    """编辑器只传正文（27.16 之后的新前端行为）也能正常保存"""
    p = make_doc(store)
    store.update(1, "# 收费网准入配置说明\n\n改过的正文\n")
    text = p.read_text(encoding="utf-8")
    assert blocks(text) == 1
    fm, body = strip_frontmatter_blocks(text)
    assert "改过的正文" in body
    # frontmatter 元信息保留
    assert "source_file: 收费网准入.docx" in fm
    assert "doc_category: 操作规程" in fm


def test_update_repairs_legacy_multi_block_file(store):
    """历史脏数据（多段重复）被 update 顺手修回一段"""
    p = make_doc(store)
    text = p.read_text(encoding="utf-8")
    fm, body = strip_frontmatter_blocks(text)
    p.write_text(fm * 3 + "\n" + body, encoding="utf-8")   # 造 3 段重复
    assert blocks(p.read_text(encoding="utf-8")) == 3

    store.update(1, p.read_text(encoding="utf-8"))
    assert blocks(p.read_text(encoding="utf-8")) == 1


def test_update_keeps_body_bytewise(store):
    """正文不允许被改动（只压 frontmatter）"""
    p = make_doc(store)
    before = strip_frontmatter_blocks(p.read_text(encoding="utf-8"))[1]
    store.update(1, before + "追加一行\n")
    after = strip_frontmatter_blocks(p.read_text(encoding="utf-8"))[1]
    assert after == before + "追加一行\n"


def test_update_does_not_wipe_on_empty_input(store):
    """空内容不能把正文清空（降级为保留原正文）"""
    p = make_doc(store)
    before = strip_frontmatter_blocks(p.read_text(encoding="utf-8"))[1]
    store.update(1, "   \n\n  ")
    after = strip_frontmatter_blocks(p.read_text(encoding="utf-8"))[1]
    assert after == before


def test_update_missing_file_returns_none(store):
    assert store.update(999, "x") is None


def test_read_body_excludes_frontmatter(store):
    make_doc(store)
    body = store.read_body(1)
    assert body.startswith("# 收费网准入配置说明")
    assert "source_file" not in body


def test_split_join_roundtrip():
    text = "---\ntitle: X\n---\n\n# 标题\n\n正文\n"
    fm, body = strip_frontmatter_blocks(text)
    assert blocks(join_frontmatter(fm, body)) == 1
    assert strip_frontmatter_blocks(join_frontmatter(fm, body))[1] == "# 标题\n\n正文\n"


def test_no_frontmatter_file_is_untouched():
    fm, body = strip_frontmatter_blocks("# 只有正文\n\n内容\n")
    assert fm == ""
    assert body == "# 只有正文\n\n内容\n"


def test_crlf_frontmatter_is_recognized():
    text = "---\r\ntitle: X\r\n---\r\n\r\n正文\r\n"
    fm, body = strip_frontmatter_blocks(text)
    assert "title: X" in fm
    assert body.startswith("正文")


def test_horizontal_rule_in_body_not_treated_as_frontmatter():
    """正文里的 --- 分隔线不能被误判成 frontmatter"""
    text = "---\ntitle: X\n---\n\n# 标题\n\n第一段\n\n---\n\n第二段\n"
    _fm, body = strip_frontmatter_blocks(text)
    assert "第二段" in body
    assert "---" in body
