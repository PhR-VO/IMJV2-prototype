#!/usr/bin/env python3
import hashlib
import json
import mimetypes
import shutil
import sys
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import formatdate
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

from lod import service as lod_service


ROOT = Path(__file__).resolve().parent
STORE = ROOT / "object-store"
DRAFT_SUBMISSIONS = STORE / "draft-submissions"
DRAFT_REPORTS = STORE / "draft-reports"
SUBMISSIONS = STORE / "submissions"
BASKET_FILE = STORE / "basket.json"
DEFAULT_EXPLOITATION_ID = "DEMO-EXP-001"
SOURCE_FILE = ROOT / "assets" / "structurele-gegevens-imjv2.ods"
FILE_NAME = SOURCE_FILE.name
DISPLAY_NAME = "Exploitatietoestand d.d. 1-1-2027"
DEFAULT_NACE_BEL_CODE = "23.990"
SUBMITTER_NAME = "Emiel Jeurens"
ORGANIZATION_NAME = "Demo Exploitatie NV"
REPORT_FILE = "report.json"
REPORT_SNAPSHOT_FILE = "exploitatietoestand.json"
WITHDRAWAL_FILE = "intrekking.json"
SCHEMA_FILE = "exploitatieschema.svg"
DEFAULT_LOCATION = {
    "address": {
        "street": "Zaha Hadidplein",
        "houseNumber": "1",
        "postalCode": "2030",
        "municipality": "Antwerpen",
        "country": "België",
    },
    "lambert2008": {
        "x": 652224,
        "y": 717046,
    },
}

DEFAULT_OBJECTS = [
    {"type": "Productielijn", "code": "PL-01", "name": "Productielijn keramische granulaten", "properties": "Capaciteit: 120000 ton/jaar", "relations": ["STK-01", "WZI-01"], "status": "In gebruik"},
    {"type": "Stookinstallatie", "code": "STK-01", "name": "Stoomketel lijn 1", "properties": "Thermisch vermogen: 48 MW; brandstof: aardgas", "relations": ["PL-01", "EP-L-01"], "status": "In gebruik"},
    {"type": "Waterzuivering", "code": "WZI-01", "name": "Fysico-chemische waterzuivering", "properties": "Neutralisatie + sedimentatie + zandfilter; capaciteit: 35 m3/u", "relations": ["PL-01", "EP-W-01"], "status": "In gebruik"},
    {"type": "Grondwaterwinning", "code": "GW-01", "name": "Winning productieput noord", "properties": "Putdiepte: 82 m; debietmeter: DM-4451; watervoerende laag: HCOV 0600", "relations": ["PL-01"], "status": "In gebruik"},
    {"type": "Emissiepunt lucht", "code": "EP-L-01", "name": "Schoorsteen stoomketel", "properties": "Hoogte: 32 m; diameter: 1.2 m; Lambert 2008: 156420, 207880", "relations": ["STK-01"], "status": "In gebruik"},
    {"type": "Emissiepunt water", "code": "EP-W-01", "name": "Lozingspunt effluent WZI", "properties": "Lozend naar oppervlaktewater; Lambert 2008: 156385, 207842", "relations": ["WZI-01"], "status": "In gebruik"},
]


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def make_transaction_id():
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    suffix = uuid.uuid4().hex[:8].upper()
    return f"MJV2-{stamp}-{suffix}"


def make_report_id():
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    suffix = uuid.uuid4().hex[:8].upper()
    return f"RPT-{stamp}-{suffix}"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def default_editor():
    return {
        "title": DISPLAY_NAME,
        "exploitatie": "Demo Exploitatie NV",
        "exploitatieId": DEFAULT_EXPLOITATION_ID,
        "effectiveFrom": "2027-01-01",
        "naceBelCode": DEFAULT_NACE_BEL_CODE,
        "location": DEFAULT_LOCATION,
        "objects": DEFAULT_OBJECTS,
        "updatedAt": now_iso(),
    }


def ods_cell(value):
    return (
        '<table:table-cell office:value-type="string">'
        f"<text:p>{escape(str(value))}</text:p>"
        "</table:table-cell>"
    )


def write_ods(path, editor):
    location = editor.get("location") or DEFAULT_LOCATION
    address = location.get("address", {})
    coordinates = location.get("lambert2008", {})
    metadata_rows = [
        ["Gegeven", "Waarde"],
        ["Naam van de exploitatie", editor.get("exploitatie", "")],
        ["Exploitatie-ID", editor.get("exploitatieId", DEFAULT_EXPLOITATION_ID)],
        ["Ingangsdatum toestand", editor.get("effectiveFrom", "")],
        ["NACE-BEL-code", editor.get("naceBelCode", DEFAULT_NACE_BEL_CODE)],
        [
            "Adres",
            f"{address.get('street', '')} {address.get('houseNumber', '')}, "
            f"{address.get('postalCode', '')} {address.get('municipality', '')}, "
            f"{address.get('country', '')}".strip(),
        ],
        ["Lambert 2008 X", coordinates.get("x", "")],
        ["Lambert 2008 Y", coordinates.get("y", "")],
    ]
    if editor.get("replacesReportId"):
        metadata_rows.append(["Vervangt toestand", editor["replacesReportId"]])
    rows = [["Type", "Code", "Naam", "Eigenschappen", "Verbonden met", "Status"]]
    rows.extend([
        [
            item.get("type", ""),
            item.get("code", ""),
            item.get("name", ""),
            item.get("properties", ""),
            "; ".join(item.get("relations", [])),
            item.get("status", ""),
        ]
        for item in editor.get("objects", [])
    ])
    metadata_table_rows = "".join(
        "<table:table-row>" + "".join(ods_cell(value) for value in row) + "</table:table-row>"
        for row in metadata_rows
    )
    object_table_rows = "".join(
        "<table:table-row>" + "".join(ods_cell(value) for value in row) + "</table:table-row>"
        for row in rows
    )
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
 xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
 xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0" office:version="1.2">
 <office:body><office:spreadsheet>
 <table:table table:name="Verslaggegevens">{metadata_table_rows}</table:table>
 <table:table table:name="Exploitatietoestand">{object_table_rows}</table:table>
 </office:spreadsheet></office:body>
</office:document-content>"""
    styles = """<?xml version="1.0" encoding="UTF-8"?><office:document-styles xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" office:version="1.2"><office:styles/></office:document-styles>"""
    manifest = """<?xml version="1.0" encoding="UTF-8"?><manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.2"><manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.spreadsheet"/><manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/><manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/></manifest:manifest>"""
    with ZipFile(path, "w") as archive:
        archive.writestr("mimetype", "application/vnd.oasis.opendocument.spreadsheet", compress_type=ZIP_STORED)
        archive.writestr("content.xml", content, compress_type=ZIP_DEFLATED)
        archive.writestr("styles.xml", styles, compress_type=ZIP_DEFLATED)
        archive.writestr("META-INF/manifest.xml", manifest, compress_type=ZIP_DEFLATED)


def schema_color(object_type):
    object_type = str(object_type).lower()
    if "productie" in object_type:
        return "#fffbd6", "#d6b900"
    if "waterzuivering" in object_type:
        return "#e7f4ec", "#008440"
    if "grondwater" in object_type:
        return "#e8f7fb", "#168aad"
    if "emissie" in object_type:
        return "#fff1dc", "#f39600"
    return "#e8f2fc", "#0064d4"


def write_schema(path, editor):
    objects = editor.get("objects", [])
    columns = 3
    node_width = 320
    node_height = 112
    gap_x = 45
    gap_y = 72
    left = 55
    top = 155
    rows = max(1, (len(objects) + columns - 1) // columns)
    width = left * 2 + columns * node_width + (columns - 1) * gap_x
    height = top + rows * node_height + max(0, rows - 1) * gap_y + 75
    positions = {}
    for index, item in enumerate(objects):
        column = index % columns
        row = index // columns
        positions[str(item.get("code", ""))] = (
            left + column * (node_width + gap_x),
            top + row * (node_height + gap_y),
        )

    edges = []
    seen_edges = set()
    for item in objects:
        source_code = str(item.get("code", ""))
        if source_code not in positions:
            continue
        source_x, source_y = positions[source_code]
        for target_code in item.get("relations", []):
            target_code = str(target_code)
            if target_code not in positions:
                continue
            edge_key = tuple(sorted((source_code, target_code)))
            if edge_key in seen_edges:
                continue
            seen_edges.add(edge_key)
            target_x, target_y = positions[target_code]
            x1 = source_x + node_width / 2
            y1 = source_y + node_height / 2
            x2 = target_x + node_width / 2
            y2 = target_y + node_height / 2
            edges.append(
                f'<path class="edge" d="M {x1:.0f} {y1:.0f} L {x2:.0f} {y2:.0f}"/>'
            )

    nodes = []
    for item in objects:
        code = str(item.get("code", ""))
        x, y = positions[code]
        fill, stroke = schema_color(item.get("type", ""))
        status = str(item.get("status", ""))
        nodes.append(
            f"""<g>
  <rect class="node" x="{x}" y="{y}" width="{node_width}" height="{node_height}" fill="{fill}" stroke="{stroke}"/>
  <text class="type" x="{x + 20}" y="{y + 28}">{escape(str(item.get("type", "")))}</text>
  <text class="name" x="{x + 20}" y="{y + 57}">{escape(str(item.get("name", "")))}</text>
  <text class="code" x="{x + 20}" y="{y + 84}">{escape(code)} · {escape(status)}</text>
</g>"""
        )

    title = str(editor.get("title") or DISPLAY_NAME).replace("Exploitatietoestand", "Exploitatieschema", 1)
    exploitation = str(editor.get("exploitatie") or "")
    nace_bel_code = str(editor.get("naceBelCode") or DEFAULT_NACE_BEL_CODE)
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
  <title id="title">{escape(title)}</title>
  <desc id="desc">Visuele weergave van de objecten en relaties uit de exploitatietoestand.</desc>
  <defs>
    <style>
      .background {{ fill: #f8fafc; }}
      .edge {{ fill: none; stroke: #8a969f; stroke-width: 3; }}
      .node {{ stroke-width: 2; rx: 6; }}
      .title {{ font: 700 30px Arial, sans-serif; fill: #1f2937; }}
      .subtitle {{ font: 16px Arial, sans-serif; fill: #4b5563; }}
      .type {{ font: 700 13px Arial, sans-serif; fill: #4b5563; text-transform: uppercase; }}
      .name {{ font: 700 17px Arial, sans-serif; fill: #1f2937; }}
      .code {{ font: 14px Arial, sans-serif; fill: #4b5563; }}
    </style>
  </defs>
  <rect class="background" width="{width}" height="{height}"/>
  <rect width="{width}" height="10" fill="#ffe615"/>
  <text class="title" x="55" y="62">{escape(title)}</text>
  <text class="subtitle" x="55" y="92">{escape(exploitation)} · NACE-BEL {escape(nace_bel_code)} · {len(objects)} objecten{escape(f" · vervangt {editor.get('replacesReportId')}" if editor.get('replacesReportId') else "")}</text>
  {"".join(edges)}
  {"".join(nodes)}
</svg>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8")


def validate_editor(editor):
    objects = editor.get("objects")
    errors = []
    if not str(editor.get("exploitatie") or "").strip():
        errors.append("Naam van de exploitatie is verplicht.")
    if not str(editor.get("exploitatieId") or "").strip():
        errors.append("Exploitatie-ID is verplicht.")
    if not isinstance(objects, list):
        errors.append("De objectenlijst heeft een ongeldig formaat.")
        return errors
    codes = [str(item.get("code", "")).strip().upper() for item in objects]
    if any(not code for code in codes):
        errors.append("Elk object heeft een code nodig.")
    if len(codes) != len(set(codes)):
        errors.append("Objectcodes moeten uniek zijn.")
    known = set(codes)
    for item in objects:
        if not str(item.get("name", "")).strip():
            errors.append(f"Object {item.get('code') or '?'} heeft een naam nodig.")
        missing = [code for code in item.get("relations", []) if code not in known]
        if missing:
            errors.append(f"Object {item.get('code') or '?'} verwijst naar onbekende code(s): {', '.join(missing)}.")
    return errors


def normalized_objects(objects):
    return [
        {key: value for key, value in item.items() if key != "effectiveDate"}
        for item in objects
    ]


def save_editor(transaction_id, editor):
    draft_submission_dir = DRAFT_SUBMISSIONS / transaction_id
    manifest_path = draft_submission_dir / "manifest.json"
    if not manifest_path.exists():
        return None, ["Concept niet gevonden."]
    errors = validate_editor(editor)
    if errors:
        return None, errors
    normalized = {
        "title": str(editor.get("title") or DISPLAY_NAME),
        "exploitatie": str(editor.get("exploitatie") or "Demo Exploitatie NV"),
        "exploitatieId": str(editor.get("exploitatieId") or DEFAULT_EXPLOITATION_ID),
        "effectiveFrom": str(editor.get("effectiveFrom") or "2027-01-01"),
        "naceBelCode": str(editor.get("naceBelCode", "")),
        "location": editor.get("location") or DEFAULT_LOCATION,
        "objects": normalized_objects(editor["objects"]),
        "updatedAt": now_iso(),
    }
    if editor.get("replacesReportId"):
        normalized["replacesReportId"] = editor["replacesReportId"]
        normalized["replacesTransactionId"] = editor.get("replacesTransactionId")
    if editor.get("basedOnReportId"):
        normalized["basedOnReportId"] = editor["basedOnReportId"]
        normalized["basedOnTransactionId"] = editor.get("basedOnTransactionId")
    if editor.get("changeType"):
        normalized["changeType"] = editor["changeType"]
    manifest = read_json(manifest_path)
    report_id = manifest.get("reportDraftId")
    if not report_id:
        return None, ["Rapportconcept niet gevonden."]
    report_dir = DRAFT_REPORTS / report_id
    existing_report_path = report_dir / REPORT_FILE
    if not existing_report_path.exists():
        return None, ["Rapportconcept niet gevonden."]
    existing_report = read_json(existing_report_path)
    existing_exploitation_id = str(existing_report.get("exploitatieId") or "")
    requested_exploitation_id = str(editor.get("exploitatieId") or "")
    if requested_exploitation_id != existing_exploitation_id:
        return None, ["De exploitatie-ID kan niet worden gewijzigd."]
    normalized["exploitatieId"] = existing_exploitation_id
    report = {
        "reportDraftId": report_id,
        **normalized,
    }
    write_json(report_dir / REPORT_FILE, report)
    target = draft_submission_dir / "original" / manifest["fileName"]
    write_ods(target, normalized)
    write_schema(draft_submission_dir / "original" / SCHEMA_FILE, normalized)
    manifest.update({
        "displayName": normalized["title"],
        "exploitatie": normalized["exploitatie"],
        "exploitatieId": normalized["exploitatieId"],
        "naceBelCode": normalized["naceBelCode"],
        "fileSize": target.stat().st_size,
        "contentHash": sha256(target),
        "summary": f"Structurele toestand met {len(normalized['objects'])} objecten",
        "reportUpdatedAt": normalized["updatedAt"],
    })
    write_json(manifest_path, manifest)
    return {"editor": report, "manifest": public_manifest(manifest)}, []


def save_draft_report(report_id, editor):
    report_path = DRAFT_REPORTS / report_id / REPORT_FILE
    if not report_path.exists():
        return None, ["Toestand in opmaak niet gevonden."]
    existing_report = read_json(report_path)
    existing_exploitation_id = str(existing_report.get("exploitatieId") or "")
    requested_exploitation_id = str(editor.get("exploitatieId") or "")
    if requested_exploitation_id != existing_exploitation_id:
        return None, ["De exploitatie-ID kan niet worden gewijzigd."]
    errors = validate_editor(editor)
    if errors:
        return None, errors
    report = {
        "reportDraftId": report_id,
        "title": str(editor.get("title") or DISPLAY_NAME),
        "exploitatie": str(editor.get("exploitatie") or "Exploitatie"),
        "exploitatieId": existing_exploitation_id,
        "effectiveFrom": str(editor.get("effectiveFrom") or ""),
        "naceBelCode": str(editor.get("naceBelCode", "")),
        "location": editor.get("location") or {"address": {}, "lambert2008": {}},
        "objects": normalized_objects(editor["objects"]),
        "updatedAt": now_iso(),
    }
    if editor.get("replacesReportId"):
        report["replacesReportId"] = editor["replacesReportId"]
        report["replacesTransactionId"] = editor.get("replacesTransactionId")
    if editor.get("basedOnReportId"):
        report["basedOnReportId"] = editor["basedOnReportId"]
        report["basedOnTransactionId"] = editor.get("basedOnTransactionId")
    if editor.get("changeType"):
        report["changeType"] = editor["changeType"]
    write_json(report_path, report)
    return report, []


def public_manifest(manifest):
    result = dict(manifest)
    result.setdefault("submittedBy", f"{SUBMITTER_NAME} namens {ORGANIZATION_NAME}")
    result.setdefault("submitterName", SUBMITTER_NAME)
    result.setdefault("organizationName", ORGANIZATION_NAME)
    result.pop("storage", None)
    return result


def ensure_store():
    DRAFT_SUBMISSIONS.mkdir(parents=True, exist_ok=True)
    DRAFT_REPORTS.mkdir(parents=True, exist_ok=True)
    SUBMISSIONS.mkdir(parents=True, exist_ok=True)
    lod_service.ensure_lod_store(STORE)
    migrate_legacy_drafts()
    migrate_display_names()
    ensure_schemas()
    regenerate_receipts()
    cleanup_submitted_draft_reports()


def cleanup_submitted_draft_reports():
    active_report_ids = {
        read_json(path).get("reportDraftId")
        for path in DRAFT_SUBMISSIONS.glob("*/manifest.json")
    }
    submitted_report_ids = set()
    for snapshot_path in SUBMISSIONS.glob(f"*/payload/{REPORT_SNAPSHOT_FILE}"):
        try:
            source_id = read_json(snapshot_path).get("sourceReportDraftId")
        except (OSError, json.JSONDecodeError):
            continue
        if source_id:
            submitted_report_ids.add(source_id)
    for report_id in submitted_report_ids - active_report_ids:
        report_dir = DRAFT_REPORTS / report_id
        if report_dir.exists():
            shutil.rmtree(report_dir)


def ensure_schemas():
    for manifest_path in DRAFT_SUBMISSIONS.glob("*/manifest.json"):
        manifest = read_json(manifest_path)
        report_path = DRAFT_REPORTS / manifest.get("reportDraftId", "") / REPORT_FILE
        if report_path.exists():
            write_schema(manifest_path.parent / "original" / SCHEMA_FILE, read_json(report_path))
            manifest.setdefault("storage", {})["schema"] = (
                f"draft-submissions/{manifest['transactionId']}/original/{SCHEMA_FILE}"
            )
            write_json(manifest_path, manifest)
    for manifest_path in SUBMISSIONS.glob("*/manifest.json"):
        manifest = read_json(manifest_path)
        snapshot_path = manifest_path.parent / "payload" / REPORT_SNAPSHOT_FILE
        if snapshot_path.exists():
            write_schema(manifest_path.parent / "original" / SCHEMA_FILE, read_json(snapshot_path))
            manifest.setdefault("storage", {})["schema"] = (
                f"submissions/{manifest['transactionId']}/original/{SCHEMA_FILE}"
            )
            write_json(manifest_path, manifest)


def migrate_legacy_drafts():
    legacy_drafts = STORE / "drafts"
    if not legacy_drafts.exists():
        return
    for legacy_dir in legacy_drafts.iterdir():
        if not legacy_dir.is_dir():
            continue
        target_dir = DRAFT_SUBMISSIONS / legacy_dir.name
        if not target_dir.exists():
            shutil.move(str(legacy_dir), str(target_dir))
        manifest_path = target_dir / "manifest.json"
        if not manifest_path.exists():
            continue
        manifest = read_json(manifest_path)
        report_id = manifest.get("reportDraftId") or f"RPT-{manifest['transactionId']}"
        legacy_editor = target_dir / "editor.json"
        report_path = DRAFT_REPORTS / report_id / REPORT_FILE
        if legacy_editor.exists() and not report_path.exists():
            editor = read_json(legacy_editor)
            write_json(report_path, {"reportDraftId": report_id, **editor})
            legacy_editor.unlink()
        elif not report_path.exists():
            write_json(report_path, {"reportDraftId": report_id, **default_editor()})
        manifest["reportDraftId"] = report_id
        manifest["storage"] = {
            "original": f"draft-submissions/{manifest['transactionId']}/original/{manifest['fileName']}",
            "manifest": f"draft-submissions/{manifest['transactionId']}/manifest.json",
            "reportDraft": f"draft-reports/{report_id}/{REPORT_FILE}",
        }
        write_json(manifest_path, manifest)
    try:
        legacy_drafts.rmdir()
    except OSError:
        pass


def migrate_display_names():
    for manifest_path in STORE.glob("*/**/manifest.json"):
        try:
            manifest = read_json(manifest_path)
        except (OSError, json.JSONDecodeError):
            continue
        report = None
        if manifest_path.parent.parent == SUBMISSIONS:
            snapshot_path = manifest_path.parent / "payload" / REPORT_SNAPSHOT_FILE
            if snapshot_path.exists():
                report = read_json(snapshot_path)
        elif manifest_path.parent.parent == DRAFT_SUBMISSIONS:
            report_id = manifest.get("reportDraftId")
            report_path = DRAFT_REPORTS / str(report_id or "") / REPORT_FILE
            if report_path.exists():
                report = read_json(report_path)
        display_name = (report or {}).get("title") or manifest.get("displayName") or DISPLAY_NAME
        if manifest.get("displayName") == display_name:
            continue
        manifest["displayName"] = display_name
        write_json(manifest_path, manifest)
        if manifest.get("receiptAvailable"):
            receipt_path = manifest_path.parent / "receipt.txt"
            receipt_path.write_text(receipt_text(manifest), encoding="utf-8")


def regenerate_receipts():
    for manifest_path in SUBMISSIONS.glob("*/manifest.json"):
        try:
            manifest = read_json(manifest_path)
        except (OSError, json.JSONDecodeError):
            continue
        if manifest.get("receiptAvailable"):
            (manifest_path.parent / "receipt.txt").write_text(
                receipt_text(manifest),
                encoding="utf-8",
            )


def create_draft_submission(report_id, editor):
    transaction_id = make_transaction_id()
    draft_dir = DRAFT_SUBMISSIONS / transaction_id
    original_dir = draft_dir / "original"
    original_dir.mkdir(parents=True)
    target = original_dir / FILE_NAME
    write_ods(target, editor)
    write_schema(original_dir / SCHEMA_FILE, editor)
    manifest = {
        "transactionId": transaction_id,
        "reportDraftId": report_id,
        "status": "Nog niet ingediend",
        "displayName": DISPLAY_NAME,
        "fileName": FILE_NAME,
        "fileSize": target.stat().st_size,
        "contentHash": sha256(target),
        "exploitatie": editor["exploitatie"],
        "exploitatieId": editor.get("exploitatieId", DEFAULT_EXPLOITATION_ID),
        "naceBelCode": editor.get("naceBelCode", DEFAULT_NACE_BEL_CODE),
        "submittedBy": f"{SUBMITTER_NAME} namens {ORGANIZATION_NAME}",
        "submitterName": SUBMITTER_NAME,
        "organizationName": ORGANIZATION_NAME,
        "summary": "Structurele toestand op het terrein",
        "createdAt": now_iso(),
        "submittedAt": None,
        "receivedAt": None,
        "receiptAvailable": False,
        "storage": {
            "original": f"draft-submissions/{transaction_id}/original/{FILE_NAME}",
            "manifest": f"draft-submissions/{transaction_id}/manifest.json",
            "reportDraft": f"draft-reports/{report_id}/{REPORT_FILE}",
            "schema": f"draft-submissions/{transaction_id}/original/{SCHEMA_FILE}",
        },
    }
    write_json(draft_dir / "manifest.json", manifest)
    set_active_basket(transaction_id)
    return manifest


def create_draft_report(editor=None):
    report_id = make_report_id()
    editor = editor or default_editor()
    write_json(DRAFT_REPORTS / report_id / REPORT_FILE, {"reportDraftId": report_id, **editor})
    return {"reportDraftId": report_id, **editor}


def active_basket_transaction_id():
    if not BASKET_FILE.exists():
        return None
    try:
        payload = read_json(BASKET_FILE)
    except (OSError, json.JSONDecodeError):
        return None
    return payload.get("transactionId")


def set_active_basket(transaction_id):
    write_json(BASKET_FILE, {
        "transactionId": transaction_id,
        "updatedAt": now_iso(),
    })


def clear_active_basket(transaction_id=None):
    active_transaction_id = active_basket_transaction_id()
    if transaction_id and active_transaction_id and active_transaction_id != transaction_id:
        return
    if BASKET_FILE.exists():
        BASKET_FILE.unlink()


def current_draft():
    transaction_id = active_basket_transaction_id()
    if not transaction_id:
        return None
    manifest = draft_manifest(transaction_id)
    if not manifest:
        clear_active_basket(transaction_id)
    return manifest


def current_editor():
    manifest = current_draft()
    if manifest:
        report_id = manifest.get("reportDraftId")
        if report_id:
            path = DRAFT_REPORTS / report_id / REPORT_FILE
            if path.exists():
                return read_json(path)
    reports = sorted(DRAFT_REPORTS.glob(f"*/{REPORT_FILE}"), key=lambda path: path.stat().st_mtime, reverse=True)
    if reports:
        return read_json(reports[0])
    return create_draft_report()


def draft_manifest(transaction_id):
    path = DRAFT_SUBMISSIONS / transaction_id / "manifest.json"
    return read_json(path) if path.exists() else None


def draft_editor(transaction_id):
    manifest = draft_manifest(transaction_id)
    if not manifest:
        return None
    path = DRAFT_REPORTS / str(manifest.get("reportDraftId") or "") / REPORT_FILE
    return read_json(path) if path.exists() else None


def delete_draft_submission(transaction_id):
    manifest = draft_manifest(transaction_id)
    if not manifest:
        return False
    draft_dir = DRAFT_SUBMISSIONS / transaction_id
    if draft_dir.exists():
        shutil.rmtree(draft_dir)
    clear_active_basket(transaction_id)
    return True


def delete_draft_report(report_id):
    report_dir = DRAFT_REPORTS / str(report_id or "")
    if not report_id or not report_dir.exists():
        return False
    for manifest_path in DRAFT_SUBMISSIONS.glob("*/manifest.json"):
        manifest = read_json(manifest_path)
        if manifest.get("reportDraftId") == report_id:
            clear_active_basket(manifest.get("transactionId"))
            shutil.rmtree(manifest_path.parent)
    shutil.rmtree(report_dir)
    return True


def prepare_report_submission(report_id, editor):
    report_path = DRAFT_REPORTS / report_id / REPORT_FILE
    if not report_path.exists():
        return None, ["Toestand in opmaak niet gevonden."]
    errors = validate_editor(editor)
    if errors:
        return None, errors
    normalized = {
        "reportDraftId": report_id,
        "title": str(editor.get("title") or DISPLAY_NAME),
        "exploitatie": str(editor.get("exploitatie") or "Exploitatie"),
        "exploitatieId": str(editor.get("exploitatieId") or ""),
        "effectiveFrom": str(editor.get("effectiveFrom") or ""),
        "naceBelCode": str(editor.get("naceBelCode", "")),
        "location": editor.get("location") or {"address": {}, "lambert2008": {}},
        "objects": editor["objects"],
        "updatedAt": now_iso(),
    }
    if editor.get("replacesReportId"):
        normalized["replacesReportId"] = editor["replacesReportId"]
        normalized["replacesTransactionId"] = editor.get("replacesTransactionId")
    if editor.get("basedOnReportId"):
        normalized["basedOnReportId"] = editor["basedOnReportId"]
        normalized["basedOnTransactionId"] = editor.get("basedOnTransactionId")
    if editor.get("changeType"):
        normalized["changeType"] = editor["changeType"]
    if normalized.get("changeType") == "new-state" and not normalized.get("effectiveFrom"):
        return None, ["Vul de ingangsdatum van de nieuwe toestand in."]
    write_json(report_path, normalized)
    manifest = create_draft_submission(report_id, normalized)
    return {"editor": normalized, "manifest": public_manifest(manifest)}, []


def list_submissions():
    result = []
    for path in SUBMISSIONS.glob("*/manifest.json"):
        try:
            result.append(public_manifest(read_json(path)))
        except (OSError, json.JSONDecodeError):
            continue
    return sorted(result, key=lambda item: item.get("receivedAt") or item.get("createdAt") or "", reverse=True)


def get_submission(transaction_id):
    path = SUBMISSIONS / transaction_id / "manifest.json"
    if not path.exists():
        return None
    return public_manifest(read_json(path))


def read_report_from_ods(path):
    try:
        with ZipFile(path) as archive:
            root = ET.fromstring(archive.read("content.xml"))
    except (OSError, KeyError, ET.ParseError):
        return None
    namespace = {
        "table": "urn:oasis:names:tc:opendocument:xmlns:table:1.0",
        "text": "urn:oasis:names:tc:opendocument:xmlns:text:1.0",
    }
    tables = []
    for table in root.findall(".//table:table", namespace):
        rows = []
        for row in table.findall("table:table-row", namespace):
            values = []
            for cell in row.findall("table:table-cell", namespace):
                paragraphs = cell.findall(".//text:p", namespace)
                values.append("\n".join("".join(paragraph.itertext()) for paragraph in paragraphs))
            rows.append(values)
        tables.append(rows)
    if not tables:
        return None
    metadata = {}
    object_rows = []
    for rows in tables:
        if rows and rows[0][:2] == ["Gegeven", "Waarde"]:
            metadata.update({row[0]: row[1] for row in rows[1:] if len(row) >= 2})
        elif rows and rows[0][:2] == ["Type", "Code"]:
            object_rows = rows[1:]
    if not object_rows and tables:
        legacy_rows = tables[-1]
        object_rows = legacy_rows[1:] if legacy_rows else []
    objects = []
    legacy_dates = []
    for values in object_rows:
        values += [""] * (7 - len(values))
        objects.append({
            "type": values[0],
            "code": values[1],
            "name": values[2],
            "properties": values[3],
            "relations": [value.strip() for value in values[4].split(";") if value.strip()],
            "status": values[5],
        })
        if values[6]:
            legacy_dates.append(values[6])
    return {
        "effectiveFrom": metadata.get("Ingangsdatum toestand") or (sorted(legacy_dates)[0] if legacy_dates else None),
        "objects": objects,
    }


def report_for_submission(manifest):
    if manifest.get("submissionType") == "withdrawal":
        return None
    transaction_id = manifest["transactionId"]
    snapshot_path = SUBMISSIONS / transaction_id / "payload" / REPORT_SNAPSHOT_FILE
    if snapshot_path.exists():
        report = read_json(snapshot_path)
        source = "snapshot"
    else:
        ods_path = SUBMISSIONS / transaction_id / "original" / manifest["fileName"]
        report = read_report_from_ods(ods_path)
        source = "ods"
    if not report:
        return None
    return {
        "reportId": report.get("reportId") or f"REPORT-{transaction_id}",
        "title": report.get("title") or manifest.get("displayName") or DISPLAY_NAME,
        "exploitatie": report.get("exploitatie") or manifest.get("exploitatie"),
        "exploitatieId": report.get("exploitatieId") or manifest.get("exploitatieId") or DEFAULT_EXPLOITATION_ID,
        "naceBelCode": report["naceBelCode"] if "naceBelCode" in report else DEFAULT_NACE_BEL_CODE,
        "location": report.get("location") or DEFAULT_LOCATION,
        "objects": report.get("objects", []),
        "objectCount": len(report.get("objects", [])),
        "effectiveFrom": report.get("effectiveFrom"),
        "submittedAt": manifest.get("submittedAt"),
        "receivedAt": manifest.get("receivedAt"),
        "transactionId": transaction_id,
        "contentHash": manifest.get("contentHash"),
        "changeSummary": report.get("changeSummary"),
        "replacesReportId": report.get("replacesReportId"),
        "replacesTransactionId": report.get("replacesTransactionId"),
        "basedOnReportId": report.get("basedOnReportId"),
        "basedOnTransactionId": report.get("basedOnTransactionId"),
        "changeType": report.get("changeType"),
        "source": source,
    }


def list_reports():
    result = []
    withdrawals = []
    for manifest_path in SUBMISSIONS.glob("*/manifest.json"):
        try:
            manifest = read_json(manifest_path)
            if manifest.get("submissionType") == "withdrawal":
                withdrawal_path = manifest_path.parent / "payload" / WITHDRAWAL_FILE
                if withdrawal_path.exists():
                    withdrawals.append({
                        "manifest": manifest,
                        "payload": read_json(withdrawal_path),
                    })
                continue
            report = report_for_submission(manifest)
        except (OSError, json.JSONDecodeError):
            continue
        if report:
            result.append(report)
    by_id = {item["reportId"]: item for item in result}
    for replacement in result:
        original_id = replacement.get("replacesReportId")
        if original_id in by_id:
            original = by_id[original_id]
            original["replacedByReportId"] = replacement["reportId"]
            original["replacedByTransactionId"] = replacement["transactionId"]
    for withdrawal in withdrawals:
        payload = withdrawal["payload"]
        manifest = withdrawal["manifest"]
        target_id = payload.get("targetReportId")
        if target_id in by_id:
            target = by_id[target_id]
            target["withdrawnByTransactionId"] = manifest["transactionId"]
            target["withdrawnAt"] = manifest.get("submittedAt")
            target["withdrawalReason"] = payload.get("reason")
    for draft_path in DRAFT_REPORTS.glob(f"*/{REPORT_FILE}"):
        try:
            draft = read_json(draft_path)
        except (OSError, json.JSONDecodeError):
            continue
        source_id = draft.get("replacesReportId") or draft.get("basedOnReportId")
        if source_id in by_id:
            draft_key = "correctionDraft" if draft.get("changeType") == "correction" else "followUpDraft"
            by_id[source_id][draft_key] = {
                "reportDraftId": draft.get("reportDraftId") or draft_path.parent.name,
                "title": draft.get("title"),
                "updatedAt": draft.get("updatedAt"),
            }
    return sorted(
        result,
        key=lambda item: (
            item.get("effectiveFrom") or "",
            item.get("submittedAt") or "",
        ),
        reverse=True,
    )


def create_derived_draft(report_id, change_type):
    reports = list_reports()
    original = next((item for item in reports if item.get("reportId") == report_id), None)
    if not original:
        return None, ["Geregistreerde toestand niet gevonden."]
    if change_type == "correction" and original.get("replacedByReportId"):
        return None, ["Deze toestand is al vervangen."]
    draft_key = "correctionDraft" if change_type == "correction" else "followUpDraft"
    if original.get(draft_key):
        draft_id = original[draft_key]["reportDraftId"]
        draft_path = DRAFT_REPORTS / draft_id / REPORT_FILE
        return read_json(draft_path), []
    for draft_path in DRAFT_REPORTS.glob(f"*/{REPORT_FILE}"):
        draft = read_json(draft_path)
        if draft.get("exploitatieId") == original.get("exploitatieId"):
            return None, ["Er bestaat al een toestand in opmaak voor deze exploitatie."]
    report_id_new = make_report_id()
    draft = {
        "reportDraftId": report_id_new,
        "title": original["title"],
        "exploitatie": original["exploitatie"],
        "exploitatieId": original["exploitatieId"],
        "effectiveFrom": original["effectiveFrom"] if change_type == "correction" else "",
        "naceBelCode": original["naceBelCode"],
        "location": original["location"],
        "objects": original["objects"],
        "changeType": change_type,
        "updatedAt": now_iso(),
    }
    if change_type == "correction":
        draft["replacesReportId"] = original["reportId"]
        draft["replacesTransactionId"] = original["transactionId"]
    else:
        draft["basedOnReportId"] = original["reportId"]
        draft["basedOnTransactionId"] = original["transactionId"]
    write_json(DRAFT_REPORTS / report_id_new / REPORT_FILE, draft)
    return draft, []


def submit_withdrawal(report_id, payload):
    reason = str((payload or {}).get("reason") or "").strip()
    if not reason:
        return None, ["Vul een motivatie voor de intrekking in."]
    reports = list_reports()
    target = next((item for item in reports if item.get("reportId") == report_id), None)
    if not target:
        return None, ["Geregistreerde toestand niet gevonden."]
    if target.get("replacedByReportId"):
        return None, ["Deze toestand is al vervangen en kan niet meer afzonderlijk worden ingetrokken."]
    if target.get("withdrawnByTransactionId"):
        return None, ["Deze toestand is al ingetrokken."]

    transaction_id = make_transaction_id()
    submitted_at = now_iso()
    received_at = now_iso()
    submission_dir = SUBMISSIONS / transaction_id
    payload_dir = submission_dir / "payload"
    payload_dir.mkdir(parents=True, exist_ok=False)
    withdrawal = {
        "submissionType": "withdrawal",
        "targetReportId": target["reportId"],
        "targetTransactionId": target["transactionId"],
        "exploitatie": target.get("exploitatie"),
        "exploitatieId": target.get("exploitatieId"),
        "effectiveFrom": target.get("effectiveFrom"),
        "reason": reason,
        "submittedAt": submitted_at,
        "targetSnapshot": target,
    }
    withdrawal_path = payload_dir / WITHDRAWAL_FILE
    write_json(withdrawal_path, withdrawal)
    content_hash = sha256(withdrawal_path)
    display_name = f"Intrekking registratie {target.get('exploitatie') or target.get('exploitatieId') or ''}".strip()
    manifest = {
        "transactionId": transaction_id,
        "submissionType": "withdrawal",
        "displayName": display_name,
        "summary": f"Intrekking van geregistreerde toestand sinds {target.get('effectiveFrom') or '—'}",
        "status": "Ontvangen",
        "exploitatie": target.get("exploitatie"),
        "exploitatieId": target.get("exploitatieId"),
        "naceBelCode": target.get("naceBelCode"),
        "targetReportId": target["reportId"],
        "targetTransactionId": target["transactionId"],
        "withdrawalReason": reason,
        "contentHash": content_hash,
        "submittedBy": f"{SUBMITTER_NAME} namens {ORGANIZATION_NAME}",
        "submitterName": SUBMITTER_NAME,
        "organizationName": ORGANIZATION_NAME,
        "submittedAt": submitted_at,
        "receivedAt": received_at,
        "receiptAvailable": True,
        "storage": {
            "manifest": f"submissions/{transaction_id}/manifest.json",
            "receipt": f"submissions/{transaction_id}/receipt.txt",
            "withdrawalPayload": f"submissions/{transaction_id}/payload/{WITHDRAWAL_FILE}",
        },
    }
    write_json(submission_dir / "manifest.json", manifest)
    (submission_dir / "receipt.txt").write_text(receipt_text(manifest), encoding="utf-8")
    lod_service.enqueue_submission(STORE, manifest)
    return public_manifest(manifest), []


def list_exploitations():
    latest = {}
    for report in list_reports():
        key = report.get("exploitatieId") or report.get("exploitatie")
        if key not in latest:
            latest[key] = {
                "exploitatieId": report.get("exploitatieId"),
                "exploitatie": report.get("exploitatie"),
                "naceBelCode": report.get("naceBelCode"),
                "location": report.get("location"),
                "latestEffectiveFrom": report.get("effectiveFrom"),
                "latestSubmittedAt": report.get("submittedAt"),
                "objectCount": report.get("objectCount"),
                "reportId": report.get("reportId"),
            }
    submissions_by_report = {}
    for manifest_path in DRAFT_SUBMISSIONS.glob("*/manifest.json"):
        manifest = read_json(manifest_path)
        submissions_by_report[manifest.get("reportDraftId")] = manifest
    report_paths = sorted(
        DRAFT_REPORTS.glob(f"*/{REPORT_FILE}"),
        key=lambda path: path.stat().st_mtime,
    )
    for report_path in report_paths:
        report = read_json(report_path)
        report_id = report.get("reportDraftId") or report_path.parent.name
        manifest = submissions_by_report.get(report_id)
        key = report.get("exploitatieId") or report.get("exploitatie")
        item = latest.setdefault(key, {
            "exploitatieId": report.get("exploitatieId"),
            "exploitatie": report.get("exploitatie"),
            "naceBelCode": report.get("naceBelCode"),
            "location": report.get("location"),
            "latestEffectiveFrom": None,
            "latestSubmittedAt": None,
            "objectCount": 0,
            "reportId": None,
        })
        draft_sort = (report.get("updatedAt") or "", bool(manifest))
        if draft_sort < item.get("_draftSort", ("", False)):
            continue
        item["_draftSort"] = draft_sort
        item["draftReportId"] = report_id
        item["draftTransactionId"] = manifest.get("transactionId") if manifest else None
        item["draftObjectCount"] = len(report.get("objects", []))
        item["draftEffectiveFrom"] = report.get("effectiveFrom")
        item["draftUpdatedAt"] = report.get("updatedAt")
    for item in latest.values():
        item.pop("_draftSort", None)
    return sorted(latest.values(), key=lambda item: item.get("exploitatie") or "")


def create_first_state(payload):
    required = {
        "name": "Naam van de exploitatie",
        "exploitatieId": "Exploitatie-ID",
    }
    missing = [label for key, label in required.items() if not str(payload.get(key, "")).strip()]
    if missing:
        return None, [f"Vul {', '.join(missing)} in."]
    exploitation_id = str(payload["exploitatieId"]).strip().upper()
    if any(item.get("exploitatieId") == exploitation_id for item in list_exploitations()):
        return None, ["Deze exploitatie-ID bestaat al."]
    effective_from = str(payload.get("effectiveFrom") or "").strip()
    display_date = ""
    if effective_from:
        date = datetime.strptime(effective_from, "%Y-%m-%d")
        display_date = f"{date.day}-{date.month}-{date.year}"
    lambert_x = str(payload.get("lambertX") or "").strip()
    lambert_y = str(payload.get("lambertY") or "").strip()
    editor = {
        "title": f"Exploitatietoestand d.d. {display_date}" if display_date else "Toestand in opmaak",
        "exploitatie": str(payload["name"]).strip(),
        "exploitatieId": exploitation_id,
        "effectiveFrom": effective_from,
        "naceBelCode": str(payload.get("naceBelCode") or "").strip(),
        "location": {
            "address": {
                "street": str(payload.get("street", "")).strip(),
                "houseNumber": str(payload.get("houseNumber", "")).strip(),
                "postalCode": str(payload.get("postalCode", "")).strip(),
                "municipality": str(payload.get("municipality", "")).strip(),
                "country": "België",
            },
            "lambert2008": {
                "x": int(lambert_x) if lambert_x else None,
                "y": int(lambert_y) if lambert_y else None,
            },
        },
        "objects": [],
        "updatedAt": now_iso(),
    }
    editor = create_draft_report(editor)
    return {
        "editor": editor,
    }, []


def receipt_text(manifest):
    transaction_id = manifest["transactionId"]
    if manifest.get("submissionType") == "withdrawal":
        withdrawal_path = SUBMISSIONS / transaction_id / "payload" / WITHDRAWAL_FILE
        withdrawal = read_json(withdrawal_path) if withdrawal_path.exists() else {}
        target = withdrawal.get("targetSnapshot") or {}
        content_lines = [
            f"- Type indiening: Intrekking van een geregistreerde toestand",
            f"- Naam exploitatie: {withdrawal.get('exploitatie') or manifest.get('exploitatie') or '—'}",
            f"- Exploitatie-ID: {withdrawal.get('exploitatieId') or manifest.get('exploitatieId') or '—'}",
            f"- Ingetrokken toestand sinds: {withdrawal.get('effectiveFrom') or target.get('effectiveFrom') or '—'}",
            f"- Referentie oorspronkelijke indiening: {withdrawal.get('targetTransactionId') or '—'}",
            f"- Referentie toestand: {withdrawal.get('targetReportId') or '—'}",
            f"- Motivatie: {withdrawal.get('reason') or manifest.get('withdrawalReason') or '—'}",
        ]
        return "\n".join(
            [
                "ONTVANGSTBEWIJS IMJV2",
                "",
                f"Transactie-ID: {manifest['transactionId']}",
                "Status: Ontvangen",
                f"Bestand: {manifest['displayName']}",
                f"Content hash: sha256:{manifest['contentHash']}",
                f"Exploitatie: {manifest.get('exploitatie') or '—'}",
                f"Ingediend door: {manifest.get('submittedBy', f'{SUBMITTER_NAME} namens {ORGANIZATION_NAME}')}",
                f"Tijdstip indiening: {manifest['submittedAt']}",
                f"Tijdstip ontvangst: {manifest['receivedAt']}",
                "Kanaal: IMJV2 loket prototype",
                "",
                "Inhoud:",
                *content_lines,
                "",
                "Dit ontvangstbewijs bevestigt dat de hierboven genoemde intrekking werd ontvangen.",
            ]
        )
    snapshot_path = SUBMISSIONS / transaction_id / "payload" / REPORT_SNAPSHOT_FILE
    report = read_json(snapshot_path) if snapshot_path.exists() else {}
    location = report.get("location") or {}
    address = location.get("address") or {}
    address_line = " ".join(filter(None, [
        address.get("street"),
        address.get("houseNumber"),
    ]))
    municipality_line = " ".join(filter(None, [
        address.get("postalCode"),
        address.get("municipality"),
    ]))
    formatted_address = ", ".join(filter(None, [address_line, municipality_line]))
    coordinates = location.get("lambert2008") or {}
    content_lines = [
        f"- Naam exploitatie: {report.get('exploitatie') or manifest.get('exploitatie') or '—'}",
        f"- Exploitatie-ID: {report.get('exploitatieId') or manifest.get('exploitatieId') or '—'}",
        f"- Ingangsdatum: {report.get('effectiveFrom') or '—'}",
        f"- NACE-BEL-code: {report.get('naceBelCode') or manifest.get('naceBelCode') or '—'}",
        f"- Adres: {formatted_address or '—'}",
        (
            "- Lambert 2008 X-Y: "
            f"{coordinates.get('x') if coordinates.get('x') is not None else '—'} - "
            f"{coordinates.get('y') if coordinates.get('y') is not None else '—'}"
        ),
        f"- Aantal rapporteringsplichtige onderdelen: {len(report.get('objects', []))}",
    ]
    objects = report.get("objects", [])
    if objects:
        for item in objects:
            properties = f" · {item.get('properties')}" if item.get("properties") else ""
            content_lines.append(
                f"  - {item.get('type') or 'Onderdeel'}: "
                f"{item.get('name') or 'Naamloos onderdeel'} "
                f"({item.get('code') or 'zonder code'})"
                f" · {item.get('status') or 'status onbekend'}"
                f"{properties}"
            )
    else:
        content_lines.append("  - Geen rapporteringsplichtige onderdelen")
    return "\n".join(
        [
            "ONTVANGSTBEWIJS IMJV2",
            "",
            f"Transactie-ID: {manifest['transactionId']}",
            "Status: Ontvangen",
            f"Bestand: {manifest['displayName']}",
            f"Content hash: sha256:{manifest['contentHash']}",
            f"Exploitatie: {manifest['exploitatie']}",
            f"Ingediend door: {manifest.get('submittedBy', f'{SUBMITTER_NAME} namens {ORGANIZATION_NAME}')}",
            f"Tijdstip indiening: {manifest['submittedAt']}",
            f"Tijdstip ontvangst: {manifest['receivedAt']}",
            "Kanaal: IMJV2 loket prototype",
            "",
            "Inhoud:",
            *content_lines,
            "",
            "Dit ontvangstbewijs bevestigt dat het hierboven genoemde geheel werd ontvangen.",
        ]
    )


def submit_draft(transaction_id):
    draft_dir = DRAFT_SUBMISSIONS / transaction_id
    draft_manifest_path = draft_dir / "manifest.json"
    if not draft_manifest_path.exists():
        existing = get_submission(transaction_id)
        return existing

    draft = read_json(draft_manifest_path)
    draft.setdefault("submittedBy", f"{SUBMITTER_NAME} namens {ORGANIZATION_NAME}")
    draft.setdefault("submitterName", SUBMITTER_NAME)
    draft.setdefault("organizationName", ORGANIZATION_NAME)
    submitted_at = now_iso()
    received_at = now_iso()
    submission_dir = SUBMISSIONS / transaction_id
    submission_dir.mkdir(parents=True, exist_ok=False)
    original_dir = submission_dir / "original"
    original_dir.mkdir()
    source = draft_dir / "original" / draft["fileName"]
    target = original_dir / draft["fileName"]
    shutil.copy2(source, target)
    report_source = DRAFT_REPORTS / draft.get("reportDraftId", "") / REPORT_FILE
    payload_dir = submission_dir / "payload"
    if report_source.exists():
        payload_dir.mkdir()
        report_snapshot = read_json(report_source)
        report_snapshot["reportId"] = f"REPORT-{transaction_id}"
        report_snapshot["sourceReportDraftId"] = draft.get("reportDraftId")
        report_snapshot["submittedAt"] = submitted_at
        write_json(payload_dir / REPORT_SNAPSHOT_FILE, report_snapshot)
        write_schema(original_dir / SCHEMA_FILE, report_snapshot)

    manifest = {
        **draft,
        "status": "Ontvangen",
        "submittedAt": submitted_at,
        "receivedAt": received_at,
        "receiptAvailable": True,
        "storage": {
            "original": f"submissions/{transaction_id}/original/{draft['fileName']}",
            "manifest": f"submissions/{transaction_id}/manifest.json",
            "receipt": f"submissions/{transaction_id}/receipt.txt",
            "reportSnapshot": f"submissions/{transaction_id}/payload/{REPORT_SNAPSHOT_FILE}",
            "schema": f"submissions/{transaction_id}/original/{SCHEMA_FILE}",
        },
    }
    write_json(submission_dir / "manifest.json", manifest)
    (submission_dir / "receipt.txt").write_text(receipt_text(manifest), encoding="utf-8")
    lod_service.enqueue_submission(STORE, manifest)
    shutil.rmtree(draft_dir)
    clear_active_basket(transaction_id)
    if report_source.exists():
        shutil.rmtree(report_source.parent)
    return public_manifest(manifest)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, fmt, *args):
        sys.stdout.write(f"{self.address_string()} - {fmt % args}\n")
        sys.stdout.flush()

    def send_json(self, value, status=HTTPStatus.OK):
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_ld_json_file(self, path):
        if not path or not path.exists() or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/ld+json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Last-Modified", formatdate(path.stat().st_mtime, usegmt=True))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def read_json_body(self):
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def send_file(self, path, download_name=None):
        if not path.exists() or not path.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        content = path.read_bytes()
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Last-Modified", formatdate(path.stat().st_mtime, usegmt=True))
        self.send_header("X-Content-Type-Options", "nosniff")
        if download_name:
            self.send_header("Content-Disposition", f'attachment; filename="{download_name}"')
        else:
            self.send_header("Content-Disposition", f'inline; filename="{path.name}"')
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        route = unquote(urlparse(self.path).path)
        if route == "/api/current":
            draft = current_draft()
            self.send_json(public_manifest(draft) if draft else None)
            return
        if route == "/api/editor":
            self.send_json(current_editor())
            return
        if route.startswith("/api/draft-reports/"):
            parts = route.strip("/").split("/")
            report_id = parts[2] if len(parts) == 3 else ""
            report_path = DRAFT_REPORTS / report_id / REPORT_FILE
            if not report_path.exists():
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self.send_json(read_json(report_path))
            return
        if route.startswith("/api/draft-submissions/") and route.endswith("/editor"):
            parts = route.strip("/").split("/")
            transaction_id = parts[2] if len(parts) == 4 else ""
            editor = draft_editor(transaction_id)
            if not editor:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self.send_json(editor)
            return
        if route.startswith("/api/draft-submissions/") and len(route.strip("/").split("/")) == 3:
            transaction_id = route.strip("/").split("/")[2]
            manifest = draft_manifest(transaction_id)
            if not manifest:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self.send_json(public_manifest(manifest))
            return
        if route.startswith("/api/draft-submissions/") and route.endswith("/file"):
            parts = route.strip("/").split("/")
            transaction_id = parts[2] if len(parts) == 4 else ""
            manifest_path = DRAFT_SUBMISSIONS / transaction_id / "manifest.json"
            if not manifest_path.exists():
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            manifest = read_json(manifest_path)
            self.send_file(DRAFT_SUBMISSIONS / transaction_id / "original" / manifest["fileName"], manifest["fileName"])
            return
        if route.startswith("/api/draft-submissions/") and route.endswith("/schema"):
            parts = route.strip("/").split("/")
            transaction_id = parts[2] if len(parts) == 4 else ""
            self.send_file(
                DRAFT_SUBMISSIONS / transaction_id / "original" / SCHEMA_FILE,
                SCHEMA_FILE if urlparse(self.path).query == "download=1" else None,
            )
            return
        if route == "/api/submissions":
            self.send_json(list_submissions())
            return
        if route == "/api/reports":
            self.send_json(list_reports())
            return
        if route == "/api/exploitations":
            self.send_json(list_exploitations())
            return
        if route == "/api/lod/status":
            self.send_json(lod_service.publication_status(STORE))
            return
        if route == "/api/lod/catalog.jsonld":
            self.send_ld_json_file(lod_service.publication_path(STORE, "catalog"))
            return
        if route.startswith("/api/lod/reports/") and route.endswith(".jsonld"):
            report_id = route.removeprefix("/api/lod/reports/").removesuffix(".jsonld")
            self.send_ld_json_file(lod_service.publication_path(STORE, "report", report_id))
            return
        if route.startswith("/api/lod/exploitations/") and route.endswith(".jsonld"):
            exploitation_id = route.removeprefix("/api/lod/exploitations/").removesuffix(".jsonld")
            self.send_ld_json_file(lod_service.publication_path(STORE, "exploitation", exploitation_id))
            return
        if route.startswith("/api/submissions/"):
            parts = route.strip("/").split("/")
            transaction_id = parts[2] if len(parts) >= 3 else ""
            manifest = get_submission(transaction_id)
            if not manifest:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            if len(parts) == 3:
                self.send_json(manifest)
                return
            if len(parts) == 4 and parts[3] == "receipt":
                self.send_file(SUBMISSIONS / transaction_id / "receipt.txt")
                return
            if len(parts) == 5 and parts[3] == "receipt" and parts[4] == "download":
                self.send_file(
                    SUBMISSIONS / transaction_id / "receipt.txt",
                    f"ontvangstbewijs-{transaction_id}.txt",
                )
                return
            if len(parts) == 4 and parts[3] == "file":
                if manifest.get("submissionType") == "withdrawal":
                    self.send_error(HTTPStatus.NOT_FOUND)
                    return
                self.send_file(
                    SUBMISSIONS / transaction_id / "original" / manifest["fileName"],
                    manifest["fileName"],
                )
                return
            if len(parts) == 4 and parts[3] == "schema":
                if manifest.get("submissionType") == "withdrawal":
                    self.send_error(HTTPStatus.NOT_FOUND)
                    return
                self.send_file(
                    SUBMISSIONS / transaction_id / "original" / SCHEMA_FILE,
                    SCHEMA_FILE if urlparse(self.path).query == "download=1" else None,
                )
                return
        super().do_GET()

    def do_POST(self):
        route = unquote(urlparse(self.path).path)
        if route.startswith("/api/reports/") and (
            route.endswith("/correction") or route.endswith("/new-state")
        ):
            parts = route.strip("/").split("/")
            report_id = parts[2] if len(parts) == 4 else ""
            change_type = "correction" if route.endswith("/correction") else "new-state"
            result, errors = create_derived_draft(report_id, change_type)
            if errors:
                self.send_json({"errors": errors}, HTTPStatus.UNPROCESSABLE_ENTITY)
                return
            self.send_json(result, HTTPStatus.CREATED)
            return
        if route.startswith("/api/reports/") and route.endswith("/withdraw"):
            parts = route.strip("/").split("/")
            report_id = parts[2] if len(parts) == 4 else ""
            try:
                payload = self.read_json_body()
            except (ValueError, json.JSONDecodeError):
                self.send_json({"errors": ["Ongeldige invoer."]}, HTTPStatus.BAD_REQUEST)
                return
            result, errors = submit_withdrawal(report_id, payload)
            if errors:
                self.send_json({"errors": errors}, HTTPStatus.UNPROCESSABLE_ENTITY)
                return
            self.send_json(result, HTTPStatus.CREATED)
            return
        if route.startswith("/api/draft-reports/") and route.endswith("/submission"):
            parts = route.strip("/").split("/")
            report_id = parts[2] if len(parts) == 4 else ""
            try:
                payload = self.read_json_body()
            except (ValueError, json.JSONDecodeError):
                self.send_json({"errors": ["Ongeldige invoer."]}, HTTPStatus.BAD_REQUEST)
                return
            result, errors = prepare_report_submission(report_id, payload)
            if errors:
                self.send_json({"errors": errors}, HTTPStatus.UNPROCESSABLE_ENTITY)
                return
            self.send_json(result, HTTPStatus.CREATED)
            return
        if route == "/api/exploitations":
            try:
                payload = self.read_json_body()
                result, errors = create_first_state(payload)
            except (ValueError, TypeError, json.JSONDecodeError):
                self.send_json({"errors": ["Ongeldige invoer."]}, HTTPStatus.BAD_REQUEST)
                return
            if errors:
                self.send_json({"errors": errors}, HTTPStatus.UNPROCESSABLE_ENTITY)
                return
            self.send_json(result, HTTPStatus.CREATED)
            return
        if route == "/api/lod/process":
            reports = list_reports()
            queued = lod_service.enqueue_missing_reports(STORE, reports)
            result = lod_service.process_pending(STORE, reports, list_exploitations())
            result["queuedMissingPublications"] = queued
            self.send_json(result)
            return
        if route.startswith("/api/draft-submissions/") and route.endswith("/submit"):
            parts = route.strip("/").split("/")
            transaction_id = parts[2] if len(parts) == 4 else ""
            try:
                manifest = submit_draft(transaction_id)
            except FileExistsError:
                manifest = get_submission(transaction_id)
            if not manifest:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self.send_json(manifest, HTTPStatus.CREATED)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_PUT(self):
        route = unquote(urlparse(self.path).path)
        if route.startswith("/api/draft-reports/"):
            parts = route.strip("/").split("/")
            report_id = parts[2] if len(parts) == 3 else ""
            try:
                payload = self.read_json_body()
            except (ValueError, json.JSONDecodeError):
                self.send_json({"errors": ["Ongeldige invoer."]}, HTTPStatus.BAD_REQUEST)
                return
            result, errors = save_draft_report(report_id, payload)
            if errors:
                self.send_json({"errors": errors}, HTTPStatus.UNPROCESSABLE_ENTITY)
                return
            self.send_json(result)
            return
        if route.startswith("/api/draft-submissions/") and route.endswith("/editor"):
            parts = route.strip("/").split("/")
            transaction_id = parts[2] if len(parts) == 4 else ""
            try:
                payload = self.read_json_body()
            except (ValueError, json.JSONDecodeError):
                self.send_json({"errors": ["Ongeldige invoer."]}, HTTPStatus.BAD_REQUEST)
                return
            result, errors = save_editor(transaction_id, payload)
            if errors:
                status = HTTPStatus.NOT_FOUND if errors == ["Concept niet gevonden."] else HTTPStatus.UNPROCESSABLE_ENTITY
                self.send_json({"errors": errors}, status)
                return
            self.send_json(result)
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_DELETE(self):
        route = unquote(urlparse(self.path).path)
        if route.startswith("/api/draft-submissions/"):
            parts = route.strip("/").split("/")
            transaction_id = parts[2] if len(parts) == 3 else ""
            if not delete_draft_submission(transaction_id):
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self.send_json({"deleted": True, "transactionId": transaction_id})
            return
        if route.startswith("/api/draft-reports/"):
            parts = route.strip("/").split("/")
            report_id = parts[2] if len(parts) == 3 else ""
            if not delete_draft_report(report_id):
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            self.send_json({"deleted": True, "reportDraftId": report_id})
            return
        self.send_error(HTTPStatus.NOT_FOUND)


if __name__ == "__main__":
    ensure_store()
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"IMJV2 object-store server: http://127.0.0.1:{port}")
    server.serve_forever()
