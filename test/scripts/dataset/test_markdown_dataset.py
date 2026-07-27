import pytest

from dingo.config import InputArgs
from dingo.data.dataset.local import LocalDataset
from dingo.data.datasource.local import LocalDataSource


def test_markdown_single_file_to_data(tmp_path):
    md_path = tmp_path / "article.md"
    content = "# Title\n\nThis is markdown content.\n"
    md_path.write_text(content, encoding="utf-8")

    input_args = InputArgs(
        input_path=str(md_path),
        dataset={"source": "local", "format": "md"},
        evaluator=[],
    )

    dataset = LocalDataset(source=LocalDataSource(input_args=input_args))
    rows = list(dataset.get_data())

    assert len(rows) == 1
    assert rows[0].id == "article.md"
    assert rows[0].content == content


def test_markdown_directory_only_reads_md_files(tmp_path):
    md1 = tmp_path / "a.md"
    txt = tmp_path / "ignore.txt"
    csv_file = tmp_path / "table.csv"
    subdir = tmp_path / "nested"
    subdir.mkdir()
    md2 = subdir / "b.md"

    md1.write_text("alpha", encoding="utf-8")
    txt.write_text("should be ignored", encoding="utf-8")
    csv_file.write_text("c1,c2\n1,2\n", encoding="utf-8")
    md2.write_text("beta", encoding="utf-8")

    input_args = InputArgs(
        input_path=str(tmp_path),
        dataset={"source": "local", "format": "md"},
        evaluator=[],
    )

    dataset = LocalDataset(source=LocalDataSource(input_args=input_args))
    rows = list(dataset.get_data())

    assert len(rows) == 2
    assert {row.id for row in rows} == {"a.md", "b.md"}
    assert {row.content for row in rows} == {"alpha", "beta"}


def test_markdown_directory_without_md_files_returns_empty(tmp_path):
    (tmp_path / "readme.txt").write_text("plain text", encoding="utf-8")

    input_args = InputArgs(
        input_path=str(tmp_path),
        dataset={"source": "local", "format": "md"},
        evaluator=[],
    )

    dataset = LocalDataset(source=LocalDataSource(input_args=input_args))
    rows = list(dataset.get_data())
    assert rows == []
