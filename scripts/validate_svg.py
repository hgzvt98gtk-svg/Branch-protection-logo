#!/usr/bin/env python3
"""Validate the repository's BIMI SVG structure and supported feature subset."""

import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path


SVG_PATH = Path(__file__).resolve().parents[1] / "logo-bimi.svg"
SVG_NAMESPACE = "http://www.w3.org/2000/svg"
ALLOWED_ELEMENTS = {"svg", "title", "desc", "g", "path"}
ALLOWED_ATTRIBUTES = {
    "svg": {"width", "height", "viewBox", "preserveAspectRatio"},
    "title": set(),
    "desc": set(),
    "g": {"transform", "fill", "stroke"},
    "path": {"d"},
}


def fail(message):
    raise SystemExit(f"{SVG_PATH}: {message}")


def validate():
    try:
        content = SVG_PATH.read_bytes()
        content.decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        fail(f"cannot read UTF-8 SVG ({error})")

    if re.search(rb"<!\s*(DOCTYPE|ENTITY)\b", content, re.IGNORECASE):
        fail("DOCTYPE and ENTITY declarations are not allowed")
    if re.search(rb"<\?(?!xml(?:\s|\?>))", content):
        fail("processing instructions other than the XML declaration are not allowed")

    try:
        root = ET.fromstring(content)
    except ET.ParseError as error:
        fail(f"invalid XML ({error})")

    if root.tag != f"{{{SVG_NAMESPACE}}}svg":
        fail("root element must be an SVG-namespace <svg>")

    for element in root.iter():
        if not element.tag.startswith(f"{{{SVG_NAMESPACE}}}"):
            fail("all elements must use the SVG namespace")
        name = element.tag.removeprefix(f"{{{SVG_NAMESPACE}}}")
        if name not in ALLOWED_ELEMENTS:
            fail(f"unsupported SVG element <{name}>")
        unexpected = set(element.attrib) - ALLOWED_ATTRIBUTES[name]
        if unexpected:
            fail(f"unsupported attributes on <{name}>: {', '.join(sorted(unexpected))}")
        if any(re.search(r"url\s*\(", value, re.IGNORECASE) for value in element.attrib.values()):
            fail(f"external or referenced resources are not allowed on <{name}>")

    try:
        dimensions = [float(root.get(name, "")) for name in ("width", "height")]
    except ValueError:
        fail("root width and height must be numbers")
    if not all(math.isfinite(value) and value > 0 for value in dimensions):
        fail("root width and height must be positive finite numbers")

    try:
        view_box = [float(value) for value in root.get("viewBox", "").replace(",", " ").split()]
    except ValueError:
        fail("viewBox must contain four numbers")
    if len(view_box) != 4 or not all(math.isfinite(value) for value in view_box):
        fail("viewBox must contain four finite numbers")
    if view_box[2] <= 0 or view_box[3] <= 0:
        fail("viewBox width and height must be positive")

    direct_children = {child.tag for child in root}
    if f"{{{SVG_NAMESPACE}}}title" not in direct_children:
        fail("root element must contain a <title>")
    if f"{{{SVG_NAMESPACE}}}desc" not in direct_children:
        fail("root element must contain a <desc>")
    if not any(element.tag == f"{{{SVG_NAMESPACE}}}path" for element in root.iter()):
        fail("SVG must contain at least one <path>")

    print(f"Validated {SVG_PATH}")


if __name__ == "__main__":
    validate()
