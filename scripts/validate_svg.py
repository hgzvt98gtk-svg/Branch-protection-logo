#!/usr/bin/env python3
"""Validate the repository's BIMI SVG structure and supported feature subset."""

import math
import re
import sys
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
    raise SystemExit(f"ERROR: {SVG_PATH}: {message}")


def validate():
    try:
        content = SVG_PATH.read_bytes()
    except OSError as error:
        fail(f"cannot read SVG ({error}); check that the file exists and is readable")
    if len(content) > 64 * 1024:
        fail(f"SVG is {len(content)} bytes; reduce it to at most 65536 bytes (64 KB)")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as error:
        fail(f"invalid UTF-8 at byte {error.start}; re-save the SVG using UTF-8 encoding")

    declaration = re.match(r"\ufeff?<\?xml\s+.*?\?>", text, re.DOTALL)
    if declaration:
        encoding = re.search(r"\bencoding\s*=\s*['\"]([^'\"]+)['\"]", declaration.group())
        if encoding and encoding.group(1).lower() not in {"utf-8", "utf8"}:
            fail("XML declaration must specify UTF-8; re-export the SVG as UTF-8")

    if len(content) > 32 * 1024:
        print(
            f"WARNING: {SVG_PATH}: {len(content)} bytes exceeds the recommended 32 KB; "
            "consider simplifying paths to reduce file size",
            file=sys.stderr,
        )

    if re.search(rb"<!\s*(DOCTYPE|ENTITY)\b", content, re.IGNORECASE):
        fail("DOCTYPE and ENTITY declarations are not allowed; remove them and inline required content")
    if re.search(rb"<\?(?!xml(?:\s|\?>))", content):
        fail("processing instructions other than the XML declaration are not allowed")

    try:
        root = ET.fromstring(content)
    except ET.ParseError as error:
        fail(f"invalid XML ({error}); fix the indicated line/column and ensure all tags are closed")

    if root.tag != f"{{{SVG_NAMESPACE}}}svg":
        fail('root element must be an SVG-namespace <svg>; add xmlns="http://www.w3.org/2000/svg"')

    for element in root.iter():
        if not element.tag.startswith(f"{{{SVG_NAMESPACE}}}"):
            fail("all elements must use the SVG namespace")
        name = element.tag.removeprefix(f"{{{SVG_NAMESPACE}}}")
        if name not in ALLOWED_ELEMENTS:
            fail(
                f"unsupported SVG element <{name}>; remove it or convert artwork to static paths. "
                "Scripts, styles, images, foreignObject, and animation elements "
                "(animate, set, animateMotion, animateTransform) are not supported"
            )
        unexpected = set(element.attrib) - ALLOWED_ATTRIBUTES[name]
        if unexpected:
            fail(
                f"unsupported attributes on <{name}>: {', '.join(sorted(unexpected))}; "
                "remove them and use self-contained path artwork"
            )
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
        fail("root element must contain a <title>; add a short, human-readable logo title")
    if f"{{{SVG_NAMESPACE}}}desc" not in direct_children:
        fail("root element must contain a <desc>; add a description of the logo")
    if not any(element.tag == f"{{{SVG_NAMESPACE}}}path" for element in root.iter()):
        fail("SVG must contain at least one <path>; convert the artwork to vector paths")

    print(f"Validated {SVG_PATH}")


if __name__ == "__main__":
    validate()
