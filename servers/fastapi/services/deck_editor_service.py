"""Сервис редакторских операций над слайдом (REST-вариант чат-инструментов).

Mini App правит слайды не «сырым» JSON, а набором валидируемых операций над
элементами ``slide.ui``. Модель данных здесь совпадает с чат-ассистентом
(``services/chat/``): тексты/картинки/данные живут прямо в ui-элементах —
``_apply_template_content_to_ui`` кладёт сгенерированное содержимое в ui, и
рендеры (веб-редактор, экспорт, превью) читают именно ui. Поэтому правки
пишутся в ui ровно как это делает ``saveSlide``/``updateSlide`` чата.

Модуль намеренно НЕ импортирует ``services/chat/memory_layer.py`` (тяжёлые
зависимости, контекст чата): геометрия реализована локально по той же
семантике, что у движкового редактора — ``position``/``size`` в 1280×720,
векторы — через bbox по ``points``.

Ограничение первой версии: координаты элементов считаются абсолютными в
системе слайда (как хранятся в ui). Компоненты-контейнеры со смещением
(позиция компонента ≠ 0) учитываются при отрисовке в Mini App как есть —
на деках default-шаблонов компоненты лежат в (0,0), поэтому визуально
совпадает.
"""

from __future__ import annotations

import copy
import re
from typing import Any

SLIDE_STAGE_WIDTH = 1280.0
SLIDE_STAGE_HEIGHT = 720.0

# Типы элементов, которые умеет править первая версия canvas-редактора.
TEXT_TYPES = {"text", "math"}
IMAGE_TYPES = {"image"}

CONTAINER_TYPES = {"container", "flex", "grid", "grid-view", "group", "svg"}
# Геометрия векторов описывается точками (points), а не position/size.
VECTOR_GEOMETRY_TYPES = {
    "vector",
    "circle",
    "ellipse",
    "line",
    "polygon",
    "rectangle",
    "vector_shape",
}

_PATH_SEGMENT_RE = re.compile(r"^(?P<key>components|elements|children)\[(?P<index>\d+)\]$")

# Ключи стилей, которые разрешено менять через op "set_style".
STYLE_SUBKEYS: dict[str, set[str]] = {
    "font": {
        "size",
        "family",
        "color",
        "bold",
        "italic",
        "underline",
        "letter_spacing",
        "line_height",
    },
    "fill": {"color", "opacity"},
    "alignment": {"horizontal", "vertical"},
}

COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")


def ui_is_editable(slide_ui: Any) -> bool:
    """Слайд рендерится из ui-лейаута (включая blank) — его можно править."""
    return isinstance(slide_ui, dict) and isinstance(slide_ui.get("components"), list)


def element_text(element: dict[str, Any]) -> str | None:
    """Плоский текст элемента: ``text`` приоритетнее ``runs`` (как у рендера)."""
    text = element.get("text")
    if isinstance(text, str):
        return text
    runs = element.get("runs")
    if isinstance(runs, list):
        return "".join(
            str(run["text"])
            for run in runs
            if isinstance(run, dict) and isinstance(run.get("text"), str)
        )
    return None


def vector_box(element: dict[str, Any]) -> dict[str, float] | None:
    """Bounding box вектора по его ``points`` (абсолютные координаты слайда)."""
    points = element.get("points")
    if not isinstance(points, list):
        return None
    xs: list[float] = []
    ys: list[float] = []
    for point in points:
        if (
            isinstance(point, dict)
            and isinstance(point.get("x"), (int, float))
            and isinstance(point.get("y"), (int, float))
        ):
            xs.append(float(point["x"]))
            ys.append(float(point["y"]))
    if not xs or not ys:
        return None
    return {"x": min(xs), "y": min(ys), "width": max(xs) - min(xs), "height": max(ys) - min(ys)}


def _element_local_box(element: dict[str, Any]) -> dict[str, float] | None:
    """Прямоугольник элемента в его собственных координатах (position/size)."""
    position = element.get("position")
    if (
        not isinstance(position, dict)
        or not isinstance(position.get("x"), (int, float))
        or not isinstance(position.get("y"), (int, float))
    ):
        return None
    size = element.get("size")
    width = (
        float(size["width"])
        if isinstance(size, dict) and isinstance(size.get("width"), (int, float))
        else 0.0
    )
    height = (
        float(size["height"])
        if isinstance(size, dict) and isinstance(size.get("height"), (int, float))
        else 0.0
    )
    return {"x": float(position["x"]), "y": float(position["y"]), "width": width, "height": height}


def element_rect(element: dict[str, Any]) -> dict[str, float] | None:
    """Прямоугольник элемента для редактора: position/size или bbox вектора."""
    element_type = str(element.get("type") or "").lower()
    if element_type in VECTOR_GEOMETRY_TYPES:
        return vector_box(element)
    return _element_local_box(element)


def collect_editor_elements(slide_ui: dict[str, Any]) -> list[dict[str, Any]]:
    """Плоский список элементов слайда с путями ``components[i].elements[j]...``.

    Путь строится по реальным вложенностям ui (``elements``/``children``/``child``),
    в том же формате, что понимает чат-редактор (``_resolve_element_path``).
    """
    collected: list[dict[str, Any]] = []

    def walk_items(items: Any, prefix: str) -> None:
        if not isinstance(items, list):
            return
        for index, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            path = f"{prefix}[{index}]"
            if isinstance(item.get("type"), str):
                collected.append(_editor_element_entry(item, path))
            walk_node(item, path)

    def walk_node(node: dict[str, Any], path: str) -> None:
        child = node.get("child")
        if isinstance(child, dict):
            walk_node(child, f"{path}.child")
        for key in ("elements", "children"):
            walk_items(node.get(key), f"{path}.{key}")

    components = slide_ui.get("components")
    if isinstance(components, list):
        walk_items(components, "components")
    top_level = slide_ui.get("elements")
    if isinstance(top_level, list):
        walk_items(top_level, "elements")
    return collected


def _editor_element_entry(element: dict[str, Any], path: str) -> dict[str, Any]:
    element_type = str(element.get("type") or "")
    entry: dict[str, Any] = {
        "path": path,
        "id": element.get("id"),
        "name": element.get("name"),
        "description": element.get("description"),
        "type": element_type,
        "decorative": element.get("decorative") is True,
        "rotation": element.get("rotation")
        if isinstance(element.get("rotation"), (int, float))
        else None,
        "rect": element_rect(element),
    }
    if element_type in TEXT_TYPES:
        entry["text"] = element_text(element)
    elif element_type in IMAGE_TYPES:
        data = element.get("data")
        entry["image"] = data if isinstance(data, str) else None
    font = element.get("font")
    if isinstance(font, dict):
        entry["font"] = {
            key: font[key] for key in ("family", "size", "color", "bold", "italic") if key in font
        }
    fill = element.get("fill")
    if isinstance(fill, dict):
        entry["fill"] = copy.deepcopy(fill)
    return entry


def resolve_element(layout: dict[str, Any], path: str) -> dict[str, Any]:
    container, index = _resolve_path_container(layout, path)
    return container[index]


def _resolve_path_container(layout: dict[str, Any], path: str) -> tuple[list[Any], int]:
    """Вернуть (список-контейнер, индекс) по пути элемента."""
    segments = path.split(".")
    if not segments:
        raise ValueError("element path is empty")
    parent: Any = layout
    for segment in segments[:-1]:
        if segment == "child":
            if not isinstance(parent, dict) or not isinstance(parent.get("child"), dict):
                raise ValueError(f"invalid element path segment: {segment}")
            parent = parent["child"]
            continue
        match = _PATH_SEGMENT_RE.match(segment)
        if not match:
            raise ValueError(f"invalid element path segment: {segment}")
        key = match.group("key")
        index = int(match.group("index"))
        if not isinstance(parent, dict) or not isinstance(parent.get(key), list):
            raise ValueError(f"invalid element path segment: {segment}")
        values = parent[key]
        if index >= len(values) or not isinstance(values[index], dict):
            raise ValueError(f"invalid element path index: {segment}")
        parent = values[index]
    last = segments[-1]
    match = _PATH_SEGMENT_RE.match(last)
    if not match:
        raise ValueError(f"invalid element path segment: {last}")
    key = match.group("key")
    index = int(match.group("index"))
    if not isinstance(parent, dict) or not isinstance(parent.get(key), list):
        raise ValueError(f"invalid element path segment: {last}")
    values = parent[key]
    if index >= len(values):
        raise ValueError(f"invalid element path index: {last}")
    return values, index


def _clamp_rect(rect: dict[str, float]) -> dict[str, float]:
    x = min(max(float(rect.get("x", 0.0)), 0.0), SLIDE_STAGE_WIDTH)
    y = min(max(float(rect.get("y", 0.0)), 0.0), SLIDE_STAGE_HEIGHT)
    width = min(max(float(rect.get("width", 1.0)), 1.0), SLIDE_STAGE_WIDTH - x)
    height = min(max(float(rect.get("height", 1.0)), 1.0), SLIDE_STAGE_HEIGHT - y)
    return {"x": x, "y": y, "width": width, "height": height}


def _apply_rect(element: dict[str, Any], rect: dict[str, float]) -> None:
    """Записать прямоугольник в элемент: вектор — через points, иначе pos/size."""
    element_type = str(element.get("type") or "").lower()
    rect = _clamp_rect(rect)
    if element_type in VECTOR_GEOMETRY_TYPES:
        box = vector_box(element)
        points = element.get("points")
        if box is None or not isinstance(points, list) or not box["width"] or not box["height"]:
            raise ValueError("vector geometry requires numeric points")
        scale_x = rect["width"] / box["width"]
        scale_y = rect["height"] / box["height"]
        element["points"] = [
            {
                **point,
                "x": rect["x"] + (float(point["x"]) - box["x"]) * scale_x,
                "y": rect["y"] + (float(point["y"]) - box["y"]) * scale_y,
            }
            for point in points
            if isinstance(point, dict)
            and isinstance(point.get("x"), (int, float))
            and isinstance(point.get("y"), (int, float))
        ]
        if isinstance(element.get("corner_radii"), list):
            radius_scale = min(abs(scale_x), abs(scale_y))
            element["corner_radii"] = [
                float(value) * radius_scale if isinstance(value, (int, float)) else value
                for value in element["corner_radii"]
            ]
        element.pop("position", None)
        element.pop("size", None)
        return
    element["position"] = {"x": rect["x"], "y": rect["y"]}
    element["size"] = {"width": rect["width"], "height": rect["height"]}


def set_element_text(element: dict[str, Any], text: str) -> None:
    """Заменить текст элемента (runs + плоский text), как делает чат-редактор."""
    element_type = str(element.get("type") or "")
    if element_type not in TEXT_TYPES:
        raise ValueError(f"text edits are only allowed for {sorted(TEXT_TYPES)} elements")
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    if element_type == "math":
        if not text.strip():
            raise ValueError("math expressions cannot be empty")
        element["latex"] = text.strip()[:4000]
        return
    if not text:
        element["runs"] = []
        element["text"] = ""
        return
    fallback_font = element.get("font")
    element["runs"] = [
        {
            "text": text,
            **(copy.deepcopy(fallback_font) if isinstance(fallback_font, dict) else {}),
        }
    ]
    # плоский text рендер читает в приоритете над runs
    element["text"] = text


def apply_style_patch(element: dict[str, Any], patch: dict[str, Any]) -> None:
    """Ограниченный набор стилевых правок (белый список ключей)."""
    if not isinstance(patch, dict):
        raise ValueError("style patch must be an object")
    element_type = str(element.get("type") or "")

    for key, value in patch.items():
        if key == "rotation":
            if not isinstance(value, (int, float)):
                raise ValueError("rotation must be a number")
            element["rotation"] = float(value)
            continue
        allowed = STYLE_SUBKEYS.get(key)
        if allowed is None:
            raise ValueError(f"style key '{key}' is not editable")
        if not isinstance(value, dict):
            raise ValueError(f"style '{key}' must be an object")
        if key == "font" and element_type not in TEXT_TYPES | {"text-list"}:
            raise ValueError("font style is only allowed for text elements")
        if key == "fill" and element_type in TEXT_TYPES:
            raise ValueError("fill style is not allowed for text elements")
        if key == "alignment" and element_type not in TEXT_TYPES | {"text-list"}:
            raise ValueError("alignment is only allowed for text elements")

        current = element.get(key)
        merged: dict[str, Any] = copy.deepcopy(current) if isinstance(current, dict) else {}
        for style_key, style_value in value.items():
            if style_key not in allowed:
                raise ValueError(f"style key '{key}.{style_key}' is not editable")
            if (
                style_key == "color"
                and isinstance(style_value, str)
                and not COLOR_RE.match(style_value)
            ):
                raise ValueError(f"style key '{key}.{style_key}' expects a hex color")
            if style_key == "size" and not isinstance(style_value, (int, float)):
                raise ValueError(f"style key '{key}.{style_key}' must be a number")
            if style_key == "opacity" and (
                not isinstance(style_value, (int, float)) or not 0 <= float(style_value) <= 1
            ):
                raise ValueError("fill.opacity must be between 0 and 1")
            merged[style_key] = style_value
        element[key] = merged


def apply_editor_ops(
    slide_ui: dict[str, Any],
    ops: list[dict[str, Any]],
) -> dict[str, Any]:
    """Применить список валидируемых операций к ui слайда.

    Вызывающий передаёт глубокую копию: операции атомарны — при ошибке любой
    опции бросаем ``ValueError`` и ничего не сохраняем.
    """
    if not isinstance(ops, list):
        raise ValueError("ops must be an array")

    for raw_op in ops:
        if not isinstance(raw_op, dict):
            raise ValueError("each op must be an object")
        op = str(raw_op.get("op") or "")
        path = raw_op.get("element_path")
        if not isinstance(path, str) or not path:
            raise ValueError("each op requires element_path")
        element = resolve_element(slide_ui, path)
        element_type = str(element.get("type") or "")

        if op == "move":
            position = raw_op.get("position")
            if (
                not isinstance(position, dict)
                or not isinstance(position.get("x"), (int, float))
                or not isinstance(position.get("y"), (int, float))
            ):
                raise ValueError("move requires position.x and position.y")
            if element.get("decorative") is True:
                raise ValueError("decorative elements cannot be moved")
            rect = element_rect(element) or {"x": 0.0, "y": 0.0, "width": 0.0, "height": 0.0}
            _apply_rect(
                element,
                {
                    "x": float(position["x"]),
                    "y": float(position["y"]),
                    "width": rect["width"],
                    "height": rect["height"],
                },
            )
        elif op == "resize":
            size = raw_op.get("size")
            if (
                not isinstance(size, dict)
                or not isinstance(size.get("width"), (int, float))
                or not isinstance(size.get("height"), (int, float))
            ):
                raise ValueError("resize requires size.width and size.height")
            if element.get("decorative") is True:
                raise ValueError("decorative elements cannot be resized")
            rect = element_rect(element) or {"x": 0.0, "y": 0.0, "width": 0.0, "height": 0.0}
            _apply_rect(
                element,
                {
                    "x": rect["x"],
                    "y": rect["y"],
                    "width": float(size["width"]),
                    "height": float(size["height"]),
                },
            )
        elif op == "set_text":
            text = raw_op.get("text")
            if not isinstance(text, str):
                raise ValueError("set_text requires text string")
            set_element_text(element, text)
        elif op == "set_style":
            patch = raw_op.get("patch")
            if not isinstance(patch, dict):
                raise ValueError("set_style requires patch object")
            apply_style_patch(element, patch)
        elif op == "set_image_url":
            url = raw_op.get("url")
            if not isinstance(url, str) or not url.strip():
                raise ValueError("set_image_url requires url string")
            if element_type not in IMAGE_TYPES:
                raise ValueError("set_image_url is only allowed for image elements")
            stripped_url = url.strip()
            if not (
                stripped_url.startswith("/app_data/")
                or stripped_url.startswith("data:image/")
                or stripped_url.startswith("http://")
                or stripped_url.startswith("https://")
            ):
                raise ValueError("url must be an /app_data path, data:image or http(s) url")
            element["data"] = stripped_url
            element.pop("prompt", None)
        elif op == "delete":
            if element.get("decorative") is True:
                raise ValueError("decorative elements cannot be deleted")
            container, index = _resolve_path_container(slide_ui, path)
            container.pop(index)
        elif op == "duplicate":
            if element.get("decorative") is True:
                raise ValueError("decorative elements cannot be duplicated")
            container, index = _resolve_path_container(slide_ui, path)
            duplicated = copy.deepcopy(element)
            if isinstance(duplicated.get("id"), str) and duplicated["id"]:
                duplicated["id"] = f"{duplicated['id']}_copy"
            container.insert(index + 1, duplicated)
        elif op == "reorder_element":
            direction = str(raw_op.get("direction") or "")
            if direction not in {"front", "back", "forward", "backward"}:
                raise ValueError("reorder_element requires direction front|back|forward|backward")
            container, index = _resolve_path_container(slide_ui, path)
            if direction == "front":
                target = len(container) - 1
            elif direction == "back":
                target = 0
            elif direction == "forward":
                target = min(index + 1, len(container) - 1)
            else:
                target = max(index - 1, 0)
            if target == index:
                continue
            item = container.pop(index)
            container.insert(target, item)
        else:
            raise ValueError(f"unknown op '{op}'")
    return slide_ui


def editor_view(slide_ui: dict[str, Any], *, slide_id: str) -> dict[str, Any]:
    """Публичная проекция слайда для canvas-редактора Mini App."""
    if not ui_is_editable(slide_ui):
        return {"slide_id": slide_id, "editable": False, "elements": []}
    return {
        "slide_id": slide_id,
        "editable": True,
        "background": slide_ui.get("background"),
        "layout_id": slide_ui.get("id"),
        "description": slide_ui.get("description"),
        "width": SLIDE_STAGE_WIDTH,
        "height": SLIDE_STAGE_HEIGHT,
        "elements": collect_editor_elements(slide_ui),
    }
