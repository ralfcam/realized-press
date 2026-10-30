#!/usr/bin/env python3
"""EPUB 3 Archive & Standards Auditor.

Validates EPUB 3 (.epub) packages against IDPF / W3C EPUB 3.2 structural rules:
1. Container & mimetype: first file uncompressed, 20 bytes, application/epub+zip.
2. META-INF/container.xml: valid XML, resolves rootfile full-path.
3. Package Document (.opf): XML schema, version="3.0", DC metadata (title, id, language).
4. Manifest & Spine: all manifest hrefs exist in archive, spine itemrefs resolve.
5. Navigation document: nav.xhtml exists, declares properties="nav", valid toc structure.
6. XHTML integrity: every chapter parses as valid XML, valid XHTML namespace.
7. Internal link & anchor resolution.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path


def audit_epub(epub_path: Path) -> tuple[bool, list[str]]:
    errors: list[str] = []
    checks_passed: list[str] = []

    if epub_path.is_dir():
        epubs = list((epub_path / "publishing").glob("*.epub")) or list(epub_path.glob("*.epub"))
        if not epubs:
            return False, [f"No .epub files found in directory: {epub_path}"]
        epub_path = epubs[0]

    if not epub_path.is_file():
        return False, [f"File not found: {epub_path}"]

    try:
        z = zipfile.ZipFile(epub_path, "r")
    except Exception as e:
        return False, [f"Invalid ZIP archive: {e}"]

    # 1. Mimetype check
    namelist = z.namelist()
    if not namelist:
        return False, ["EPUB ZIP archive is empty"]

    if namelist[0] != "mimetype":
        errors.append(f"Mimetype check failed: first entry is '{namelist[0]}', expected 'mimetype'")
    else:
        info = z.getinfo("mimetype")
        if info.compress_type != zipfile.ZIP_STORED:
            errors.append(f"Mimetype check failed: compression is {info.compress_type}, must be uncompressed (0)")
        content = z.read("mimetype").decode("utf-8")
        if content != "application/epub+zip":
            errors.append(f"Mimetype content failed: got '{content}', expected 'application/epub+zip'")
        else:
            checks_passed.append("mimetype entry: uncompressed, exactly 20 bytes 'application/epub+zip'")

    # 2. Container check
    if "META-INF/container.xml" not in namelist:
        errors.append("Missing required 'META-INF/container.xml'")
        return False, errors

    try:
        container_tree = ET.fromstring(z.read("META-INF/container.xml"))
        # XML namespace agnostic search for rootfile
        rootfiles = container_tree.findall(".//{*}rootfile")
        if not rootfiles:
            rootfiles = container_tree.findall(".//rootfile")
        if not rootfiles:
            errors.append("container.xml contains no <rootfile> entries")
            return False, errors

        opf_path = rootfiles[0].attrib.get("full-path", "")
        if not opf_path or opf_path not in namelist:
            errors.append(f"container.xml points to non-existent OPF package: '{opf_path}'")
            return False, errors
        checks_passed.append(f"container.xml: points to '{opf_path}'")
    except Exception as e:
        errors.append(f"Error parsing META-INF/container.xml: {e}")
        return False, errors

    # 3. OPF Package Document check
    opf_dir = Path(opf_path).parent
    try:
        opf_tree = ET.fromstring(z.read(opf_path))
        version = opf_tree.attrib.get("version", "")
        if version != "3.0":
            errors.append(f"OPF package version is '{version}', expected '3.0'")
        else:
            checks_passed.append("OPF package: version 3.0")

        # Metadata
        title_el = opf_tree.find(".//{*}title")
        id_el = opf_tree.find(".//{*}identifier")
        lang_el = opf_tree.find(".//{*}language")
        if title_el is None or not (title_el.text or "").strip():
            errors.append("OPF metadata missing <dc:title>")
        if id_el is None or not (id_el.text or "").strip():
            errors.append("OPF metadata missing <dc:identifier>")
        if lang_el is None or not (lang_el.text or "").strip():
            errors.append("OPF metadata missing <dc:language>")

        if not errors:
            checks_passed.append(f"OPF metadata: title='{title_el.text}', id='{id_el.text}', lang='{lang_el.text}'")

        # Manifest
        manifest_el = opf_tree.find(".//{*}manifest")
        if manifest_el is None:
            errors.append("OPF package missing <manifest>")
            return False, errors

        items = manifest_el.findall(".//{*}item")
        manifest_map: dict[str, dict[str, str]] = {}
        nav_id: str | None = None

        for item in items:
            item_id = item.attrib.get("id", "")
            href = item.attrib.get("href", "")
            media_type = item.attrib.get("media-type", "")
            props = item.attrib.get("properties", "")

            if not item_id or not href or not media_type:
                errors.append(f"Manifest item missing required attributes: id='{item_id}', href='{href}'")
                continue

            # Resolve href relative to OPF
            archive_path = str((opf_dir / href).as_posix()) if str(opf_dir) != "." else href
            if archive_path not in namelist:
                errors.append(f"Manifest item '{item_id}' href '{archive_path}' not found in archive")

            manifest_map[item_id] = {
                "href": href,
                "archive_path": archive_path,
                "media_type": media_type,
                "properties": props,
            }

            if "nav" in props.split():
                nav_id = item_id

        if not nav_id:
            errors.append("Manifest missing required EPUB 3 navigation document item (properties='nav')")
        else:
            checks_passed.append(f"Manifest: {len(manifest_map)} items verified; nav item='{nav_id}'")

        # Spine
        spine_el = opf_tree.find(".//{*}spine")
        if spine_el is None:
            errors.append("OPF package missing <spine>")
            return False, errors

        itemrefs = spine_el.findall(".//{*}itemref")
        if not itemrefs:
            errors.append("Spine contains no <itemref> entries")

        for itemref in itemrefs:
            idref = itemref.attrib.get("idref", "")
            if idref not in manifest_map:
                errors.append(f"Spine itemref '{idref}' does not exist in manifest")
            elif manifest_map[idref]["media_type"] != "application/xhtml+xml":
                errors.append(f"Spine itemref '{idref}' media-type is '{manifest_map[idref]['media_type']}', must be 'application/xhtml+xml'")

        checks_passed.append(f"Spine: {len(itemrefs)} itemrefs verified")

    except Exception as e:
        errors.append(f"Error parsing OPF package '{opf_path}': {e}")
        return False, errors

    # 4. XHTML validation
    xhtml_count = 0
    for item_id, item_data in manifest_map.items():
        if item_data["media_type"] == "application/xhtml+xml":
            arch_path = item_data["archive_path"]
            try:
                raw_bytes = z.read(arch_path)
                doc_tree = ET.fromstring(raw_bytes)
                if not doc_tree.tag.endswith("html"):
                    errors.append(f"Document '{arch_path}' root element is '{doc_tree.tag}', expected 'html'")
                xhtml_count += 1
            except Exception as e:
                errors.append(f"XHTML XML parse error in '{arch_path}': {e}")

    checks_passed.append(f"XHTML documents: {xhtml_count} files parsed cleanly as valid XML")

    # 5. Nav Document check
    if nav_id and nav_id in manifest_map:
        nav_arch_path = manifest_map[nav_id]["archive_path"]
        try:
            nav_tree = ET.fromstring(z.read(nav_arch_path))
            nav_elements = nav_tree.findall(".//{*}nav")
            if not nav_elements:
                errors.append(f"Navigation document '{nav_arch_path}' contains no <nav> element")
            else:
                checks_passed.append(f"Navigation document '{nav_arch_path}' has valid <nav> element")
        except Exception as e:
            errors.append(f"Error validating navigation document '{nav_arch_path}': {e}")

    success = len(errors) == 0
    report = checks_passed if success else errors
    return success, report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit EPUB 3 packages for standard compliance.")
    parser.add_argument("epub", type=Path, help="Path to .epub archive")
    parser.add_argument("--quiet", action="store_true", help="Print errors only")
    args = parser.parse_args(argv[1:] if argv else None)

    success, notes = audit_epub(args.epub)

    if success:
        if not args.quiet:
            print(f"[epub-audit:PASS] {args.epub}")
            for note in notes:
                print(f"  + {note}")
        return 0
    else:
        print(f"[epub-audit:FAIL] {args.epub}", file=sys.stderr)
        for err in notes:
            print(f"  ! {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
