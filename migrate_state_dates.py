#!/usr/bin/env python3
import re
from datetime import datetime

import server


TITLE_DATE = re.compile(r"d\.d\.\s*(\d{1,2})-(\d{1,2})-(\d{4})", re.IGNORECASE)


def infer_effective_from(report, manifest=None):
    if report.get("effectiveFrom"):
        return str(report["effectiveFrom"])
    legacy_dates = sorted(
        str(item["effectiveDate"])
        for item in report.get("objects", [])
        if item.get("effectiveDate")
    )
    if legacy_dates:
        return legacy_dates[0]
    match = TITLE_DATE.search(str(report.get("title") or (manifest or {}).get("displayName") or ""))
    if match:
        day, month, year = map(int, match.groups())
        return f"{year:04d}-{month:02d}-{day:02d}"
    submitted_at = (manifest or {}).get("submittedAt")
    if submitted_at:
        return datetime.fromisoformat(submitted_at).date().isoformat()
    return "2027-01-01"


def migrate_report(report, manifest=None):
    report["effectiveFrom"] = infer_effective_from(report, manifest)
    for item in report.get("objects", []):
        item.pop("effectiveDate", None)
    return report


def update_artifacts(manifest_path, report):
    manifest = server.read_json(manifest_path)
    original_dir = manifest_path.parent / "original"
    ods_path = original_dir / manifest["fileName"]
    server.write_ods(ods_path, report)
    server.write_schema(original_dir / server.SCHEMA_FILE, report)
    manifest["fileSize"] = ods_path.stat().st_size
    manifest["contentHash"] = server.sha256(ods_path)
    manifest["reportUpdatedAt"] = report.get("updatedAt", manifest.get("reportUpdatedAt"))
    server.write_json(manifest_path, manifest)
    if manifest.get("receiptAvailable"):
        (manifest_path.parent / "receipt.txt").write_text(
            server.receipt_text(manifest), encoding="utf-8"
        )


def main():
    migrated = 0
    for report_path in server.DRAFT_REPORTS.glob(f"*/{server.REPORT_FILE}"):
        report = migrate_report(server.read_json(report_path))
        server.write_json(report_path, report)
        migrated += 1

    for manifest_path in server.DRAFT_SUBMISSIONS.glob("*/manifest.json"):
        manifest = server.read_json(manifest_path)
        report_path = (
            server.DRAFT_REPORTS
            / str(manifest.get("reportDraftId") or "")
            / server.REPORT_FILE
        )
        if report_path.exists():
            report = migrate_report(server.read_json(report_path), manifest)
            server.write_json(report_path, report)
            update_artifacts(manifest_path, report)

    for manifest_path in server.SUBMISSIONS.glob("*/manifest.json"):
        manifest = server.read_json(manifest_path)
        snapshot_path = manifest_path.parent / "payload" / server.REPORT_SNAPSHOT_FILE
        if not snapshot_path.exists():
            continue
        report = migrate_report(server.read_json(snapshot_path), manifest)
        server.write_json(snapshot_path, report)
        update_artifacts(manifest_path, report)
        migrated += 1

    default_report = migrate_report(server.default_editor())
    server.write_ods(server.SOURCE_FILE, default_report)
    server.write_schema(
        server.ROOT / "assets" / "exploitatieschema-1-1-2027.svg",
        default_report,
    )
    print(f"{migrated} toestanden gemigreerd.")


if __name__ == "__main__":
    main()
