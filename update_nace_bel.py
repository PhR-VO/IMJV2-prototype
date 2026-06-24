#!/usr/bin/env python3
import re

import server


NACE_CODE = server.DEFAULT_NACE_BEL_CODE
NACE_PATTERN = re.compile(
    r"(?:;\s*)?(?:hoofdactiviteit\s+)?NACE[- ]?BEL(?:-code)?\s*[: ]?\s*23\.990",
    re.IGNORECASE,
)


def migrate_report(report):
    report["naceBelCode"] = NACE_CODE
    report["exploitatieId"] = report.get("exploitatieId") or server.DEFAULT_EXPLOITATION_ID
    suffix = f" - {report['exploitatieId']}"
    if str(report.get("exploitatie", "")).endswith(suffix):
        report["exploitatie"] = report["exploitatie"][: -len(suffix)]
    if not report.get("effectiveFrom"):
        dates = sorted(
            item.get("effectiveDate")
            for item in report.get("objects", [])
            if item.get("effectiveDate")
        )
        report["effectiveFrom"] = dates[0] if dates else "2027-01-01"
    for item in report.get("objects", []):
        item.pop("effectiveDate", None)
        properties = str(item.get("properties") or "")
        properties = NACE_PATTERN.sub("", properties)
        properties = re.sub(r"\s*;\s*;\s*", "; ", properties)
        item["properties"] = properties.strip(" ;")
    return report


def update_manifest_files(manifest_path, report):
    manifest = server.read_json(manifest_path)
    manifest["naceBelCode"] = NACE_CODE
    manifest["exploitatieId"] = report.get("exploitatieId")
    manifest["exploitatie"] = report.get("exploitatie")
    original_dir = manifest_path.parent / "original"
    ods_path = original_dir / manifest["fileName"]
    server.write_ods(ods_path, report)
    server.write_schema(original_dir / server.SCHEMA_FILE, report)
    manifest["fileSize"] = ods_path.stat().st_size
    manifest["contentHash"] = server.sha256(ods_path)
    server.write_json(manifest_path, manifest)
    if manifest.get("receiptAvailable"):
        (manifest_path.parent / "receipt.txt").write_text(
            server.receipt_text(manifest), encoding="utf-8"
        )


def main():
    for report_path in server.DRAFT_REPORTS.glob(f"*/{server.REPORT_FILE}"):
        report = migrate_report(server.read_json(report_path))
        server.write_json(report_path, report)

    for manifest_path in server.DRAFT_SUBMISSIONS.glob("*/manifest.json"):
        manifest = server.read_json(manifest_path)
        report_path = (
            server.DRAFT_REPORTS
            / str(manifest.get("reportDraftId") or "")
            / server.REPORT_FILE
        )
        if report_path.exists():
            update_manifest_files(manifest_path, server.read_json(report_path))

    for manifest_path in server.SUBMISSIONS.glob("*/manifest.json"):
        snapshot_path = manifest_path.parent / "payload" / server.REPORT_SNAPSHOT_FILE
        if not snapshot_path.exists():
            continue
        report = migrate_report(server.read_json(snapshot_path))
        server.write_json(snapshot_path, report)
        update_manifest_files(manifest_path, report)

    default_report = migrate_report(server.default_editor())
    server.write_ods(server.SOURCE_FILE, default_report)
    server.write_schema(
        server.ROOT / "assets" / "exploitatieschema-1-1-2027.svg",
        default_report,
    )


if __name__ == "__main__":
    main()
