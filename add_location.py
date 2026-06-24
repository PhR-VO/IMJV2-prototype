#!/usr/bin/env python3
import json
from pathlib import Path

import server


def update_report(path):
    report = server.read_json(path)
    report["location"] = server.DEFAULT_LOCATION
    server.write_json(path, report)
    return report


def main():
    for report_path in server.DRAFT_REPORTS.glob(f"*/{server.REPORT_FILE}"):
        report = update_report(report_path)
        report_id = report_path.parent.name
        for manifest_path in server.DRAFT_SUBMISSIONS.glob("*/manifest.json"):
            manifest = server.read_json(manifest_path)
            if manifest.get("reportDraftId") != report_id:
                continue
            ods_path = manifest_path.parent / "original" / manifest["fileName"]
            server.write_ods(ods_path, report)
            manifest["fileSize"] = ods_path.stat().st_size
            manifest["contentHash"] = server.sha256(ods_path)
            server.write_json(manifest_path, manifest)
            print(f"Draft bijgewerkt: {report_id}")

    for snapshot_path in server.SUBMISSIONS.glob(f"*/payload/{server.REPORT_SNAPSHOT_FILE}"):
        report = update_report(snapshot_path)
        submission_dir = snapshot_path.parent.parent
        manifest_path = submission_dir / "manifest.json"
        manifest = server.read_json(manifest_path)
        ods_path = submission_dir / "original" / manifest["fileName"]
        server.write_ods(ods_path, report)
        manifest["fileSize"] = ods_path.stat().st_size
        manifest["contentHash"] = server.sha256(ods_path)
        server.write_json(manifest_path, manifest)
        (submission_dir / "receipt.txt").write_text(server.receipt_text(manifest), encoding="utf-8")
        print(f"Indiening bijgewerkt: {manifest['transactionId']}")


if __name__ == "__main__":
    main()
