"""Тесты контент-QC структурного контента слайдов (utils/content_quality.py).

Прод-кейс 2026-09-05 (дека «ИТ в России», слайд 10): jsonschema пропустил
слайд, чей заголовок был «__tablecard», ячейки таблицы повторяли имена полей
схемы («type object», «minLength»), а тело — мета-болтовню модели
(«Please wait while I import…»). Эти тесты фиксируют: каждый класс мусора
ловится, легитимный контент не флагается.
"""

from __future__ import annotations

from utils.content_quality import get_content_quality_errors

TABLECARD_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "maxLength": 60},
        "columns": {"type": "array", "maxItems": 5},
        "rows": {"type": "array", "maxItems": 8},
        "bottom_note": {"type": "string", "maxLength": 200},
        "title_description": {"type": "string", "maxLength": 120},
        "__speaker_note__": {"type": "string", "minLength": 100},
    },
}


def _errors(content: dict, schema: dict | None = TABLECARD_SCHEMA) -> list[str]:
    return get_content_quality_errors(schema, content)


def test_clean_content_passes() -> None:
    content = {
        "title": "Импортозамещение ПО",
        "rows": [["Реестр отечественного ПО", "18 400 продуктов"]],
        "bottom_note": "Данные Минцифры за 2025 год.",
        "__speaker_note__": "Расскажите про рост реестра и подчеркните роль "
        "отечественных вендоров в гос-секторе за последние три года.",
    }
    assert _errors(content) == []


def test_schema_echo_in_cells_is_flagged() -> None:
    # Прод-кейс: ячейки таблицы повторяют поля и ключевые слова схемы.
    content = {
        "title": "__tablecard",
        "rows": [["type object", "title"], ["minLength", "maxLength"]],
    }
    errors = _errors(content)
    joined = "\n".join(errors)
    assert "response-schema field names" in joined


def test_compound_schema_names_are_flagged() -> None:
    content = {
        "title": "Состав полей",
        "rows": [["title description"], ["bottom_note"], ["additional_properties"]],
    }
    errors = _errors(content)
    assert len(errors) == 3


def test_single_common_words_are_not_flagged() -> None:
    content = {
        "title": "Структура отчёта",
        "rows": [["Description", "Value"], ["rows", "columns"]],
    }
    assert _errors(content) == []


def test_leaked_internal_identifiers_are_flagged() -> None:
    assert _errors({"title": "__tablecard"})
    assert _errors({"note": "__speaker_note__"})


def test_meta_chatter_is_flagged() -> None:
    # Прод-кейс: тело слайда — болтовня модели про импорт/исправление текста.
    content = {
        "title": "Заголовок",
        "bottom_note": (
            "Some text ... an image ... slide 10? Please wait while I import / "
            "corrected / generated text? Actually, the answer requires a special "
            "response because Typos are ignored and can be twisted, original. "
            "Pro-Tip: ty"
        ),
    }
    errors = _errors(content)
    joined = "\n".join(errors)
    assert "meta-commentary" in joined


def test_meta_chatter_in_speaker_note_is_flagged() -> None:
    content = {
        "title": "Образование и подготовка кадров",
        "__speaker_note__": (
            "Образование и подготовка кадров - centralized cross-import? "
            "...sentation...? No, more precisely: this response note is inaccurate."
        ),
    }
    errors = _errors(content)
    joined = "\n".join(errors)
    assert "meta-commentary" in joined


def test_placeholder_punctuation_is_flagged() -> None:
    assert _errors({"title": "Слайд", "rows": [["....."]]})
    assert _errors({"title": "Слайд", "rows": [["…"]]})
    # одиночное тире и длинное тире — легитимные пустые маркеры
    assert not _errors({"title": "Слайд", "rows": [["—"]]})


def test_placeholder_tbd_is_flagged() -> None:
    assert _errors({"title": "Слайд", "rows": [["TBD"]]})


def test_script_glue_is_flagged() -> None:
    # Прод-кейс: «поставщиNo hardware and software.» — обрыв слова с вклейкой.
    errors = _errors({"title": "Поставщики", "bottom_note": "поставщиNo hardware and software."})
    joined = "\n".join(errors)
    assert "glued mid-word" in joined


def test_separate_multilingual_words_are_not_flagged() -> None:
    content = {
        "title": "Технологии",
        "rows": [
            ["Python-разработчик", "B2B SaaS"],
            ["Импортозамещение Windows", "COBOL legacy"],
        ],
        "__speaker_note__": "Упомяните переход с Windows на Astra Linux в госсекторе.",
    }
    assert _errors(content) == []


def test_raw_json_fragment_is_flagged() -> None:
    errors = _errors({"title": "Слайд", "rows": [['{"type": "object"}']]})
    joined = "\n".join(errors)
    assert "raw JSON fragment" in joined


def test_errors_include_paths_and_are_capped() -> None:
    content = {
        "title": "minLength",
        "rows": [["...."] for _ in range(50)],
    }
    errors = get_content_quality_errors(TABLECARD_SCHEMA, content)
    assert 0 < len(errors) <= 20
    assert errors[0].startswith("$.title")


def test_works_without_schema() -> None:
    # Метa-болтовня, протечки и keywords JSON Schema ловятся и без схемы;
    # schema-эхо имён полей конкретного слайда — только со схемой.
    assert _errors({"title": "__tablecard"}, schema=None)
    assert _errors({"title": "minLength"}, schema=None)
    assert not _errors({"title": "customfield"}, schema=None)
