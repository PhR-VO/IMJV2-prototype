import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path


PUBLIC_BASE_URI = "https://data.omgeving.vlaanderen.be"
LOD_CONTEXT = {
    "dcterms": "http://purl.org/dc/terms/",
    "imjv": f"{PUBLIC_BASE_URI}/def/imjv#",
    "locn": "http://www.w3.org/ns/locn#",
    "prov": "http://www.w3.org/ns/prov#",
    "schema": "https://schema.org/",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "contentHash": "imjv:contentHash",
    "effectiveFrom": "imjv:effectiveFrom",
    "exploitatie": {"@id": "imjv:exploitatie", "@type": "@id"},
    "heeftObject": {"@id": "imjv:heeftObject", "@type": "@id"},
    "heeftToestand": {"@id": "imjv:heeftToestand", "@type": "@id"},
    "isIngetrokken": "imjv:isIngetrokken",
    "isVervangen": "imjv:isVervangen",
    "naceBelCode": "imjv:naceBelCode",
    "relatie": {"@id": "imjv:relatie", "@type": "@id"},
    "status": "imjv:status",
}


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_lod_store(store):
    for relative in [
        "lod-jobs/queued",
        "lod-jobs/processing",
        "lod-jobs/done",
        "lod-jobs/failed",
        "lod-publications/reports",
        "lod-publications/exploitations",
    ]:
        (store / relative).mkdir(parents=True, exist_ok=True)


def report_uri(report_id):
    return f"{PUBLIC_BASE_URI}/id/imjv/exploitatietoestand/{report_id}"


def exploitation_uri(exploitation_id):
    return f"{PUBLIC_BASE_URI}/id/imjv/exploitatie/{exploitation_id}"


def object_uri(report, item):
    exploitation_id = report.get("exploitatieId") or "onbekend"
    code = item.get("code") or "zonder-code"
    return f"{PUBLIC_BASE_URI}/id/imjv/object/{exploitation_id}/{code}"


def submission_uri(transaction_id):
    return f"{PUBLIC_BASE_URI}/id/imjv/indiening/{transaction_id}"


def nace_uri(code):
    return f"{PUBLIC_BASE_URI}/id/nace-bel/{code}"


def compact_ref(uri):
    return {"@id": uri}


def enqueue_submission(store, manifest):
    if not manifest or not manifest.get("transactionId"):
        return None
    ensure_lod_store(store)
    transaction_id = manifest["transactionId"]
    report_id = manifest.get("targetReportId") or f"REPORT-{transaction_id}"
    job_id = f"LOD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8].upper()}"
    job = {
        "jobId": job_id,
        "jobType": "publish-lod",
        "transactionId": transaction_id,
        "reportId": report_id,
        "submissionType": manifest.get("submissionType", "report"),
        "queuedAt": now_iso(),
    }
    write_json(store / "lod-jobs" / "queued" / f"{job_id}.json", job)
    return job


def enqueue_missing_reports(store, reports):
    ensure_lod_store(store)
    queued_report_ids = {
        read_json(path).get("reportId")
        for path in (store / "lod-jobs" / "queued").glob("*.json")
    }
    created = []
    for report in reports:
        report_id = report.get("reportId")
        transaction_id = report.get("transactionId")
        if not report_id or not transaction_id:
            continue
        if publication_path(store, "report", report_id).exists() or report_id in queued_report_ids:
            continue
        job_id = f"LOD-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8].upper()}"
        job = {
            "jobId": job_id,
            "jobType": "publish-lod",
            "transactionId": transaction_id,
            "reportId": report_id,
            "submissionType": "report",
            "queuedAt": now_iso(),
            "queuedReason": "missing-publication",
        }
        write_json(store / "lod-jobs" / "queued" / f"{job_id}.json", job)
        queued_report_ids.add(report_id)
        created.append(job)
    return created


def report_to_jsonld(report):
    objects = report.get("objects") or []
    object_nodes = []
    object_refs = []
    object_by_code = {item.get("code"): item for item in objects if item.get("code")}
    for item in objects:
        item_uri = object_uri(report, item)
        object_refs.append(compact_ref(item_uri))
        relations = []
        for related_code in item.get("relations") or []:
            related = object_by_code.get(related_code)
            if related:
                relations.append(compact_ref(object_uri(report, related)))
        object_nodes.append({
            "@id": item_uri,
            "@type": "imjv:Exploitatieobject",
            "dcterms:identifier": item.get("code"),
            "dcterms:title": item.get("name"),
            "imjv:objecttype": item.get("type"),
            "status": item.get("status"),
            "dcterms:description": item.get("properties"),
            "relatie": relations,
        })

    location = report.get("location") or {}
    address = location.get("address") or {}
    coordinates = location.get("lambert2008") or {}
    exploitation_id = report.get("exploitatieId")
    transaction_id = report.get("transactionId")
    publication = {
        "@context": LOD_CONTEXT,
        "@graph": [
            {
                "@id": report_uri(report["reportId"]),
                "@type": "imjv:Exploitatietoestand",
                "dcterms:identifier": report.get("reportId"),
                "dcterms:title": report.get("title"),
                "effectiveFrom": report.get("effectiveFrom"),
                "dcterms:issued": report.get("submittedAt"),
                "dcterms:modified": report.get("receivedAt"),
                "contentHash": report.get("contentHash"),
                "status": report_status(report),
                "isVervangen": bool(report.get("replacedByReportId")),
                "isIngetrokken": bool(report.get("withdrawnByTransactionId")),
                "exploitatie": exploitation_uri(exploitation_id),
                "heeftObject": object_refs,
                "prov:wasGeneratedBy": compact_ref(submission_uri(transaction_id)),
                "prov:wasRevisionOf": compact_ref(report_uri(report["replacesReportId"])) if report.get("replacesReportId") else None,
                "prov:wasDerivedFrom": compact_ref(report_uri(report["basedOnReportId"])) if report.get("basedOnReportId") else None,
            },
            {
                "@id": exploitation_uri(exploitation_id),
                "@type": "imjv:Exploitatie",
                "dcterms:identifier": exploitation_id,
                "dcterms:title": report.get("exploitatie"),
                "naceBelCode": compact_ref(nace_uri(report.get("naceBelCode"))) if report.get("naceBelCode") else None,
                "locn:address": {
                    "@type": "locn:Address",
                    "locn:thoroughfare": address.get("street"),
                    "locn:locatorDesignator": address.get("houseNumber"),
                    "locn:postCode": address.get("postalCode"),
                    "locn:postName": address.get("municipality"),
                    "schema:addressCountry": address.get("country"),
                },
                "schema:geo": {
                    "@type": "schema:GeoCoordinates",
                    "schema:additionalProperty": [
                        {"@type": "schema:PropertyValue", "schema:name": "Lambert 2008 X", "schema:value": coordinates.get("x")},
                        {"@type": "schema:PropertyValue", "schema:name": "Lambert 2008 Y", "schema:value": coordinates.get("y")},
                    ],
                },
                "heeftToestand": compact_ref(report_uri(report["reportId"])),
            },
            {
                "@id": submission_uri(transaction_id),
                "@type": "imjv:Indiening",
                "dcterms:identifier": transaction_id,
                "dcterms:issued": report.get("submittedAt"),
                "prov:generated": compact_ref(report_uri(report["reportId"])),
                "contentHash": report.get("contentHash"),
            },
            *object_nodes,
        ],
    }
    return strip_empty(publication)


def exploitation_to_jsonld(exploitation, reports):
    exploitation_id = exploitation.get("exploitatieId")
    related_reports = [
        report for report in reports
        if report.get("exploitatieId") == exploitation_id and report.get("reportId")
    ]
    return strip_empty({
        "@context": LOD_CONTEXT,
        "@id": exploitation_uri(exploitation_id),
        "@type": "imjv:Exploitatie",
        "dcterms:identifier": exploitation_id,
        "dcterms:title": exploitation.get("exploitatie"),
        "naceBelCode": compact_ref(nace_uri(exploitation.get("naceBelCode"))) if exploitation.get("naceBelCode") else None,
        "heeftToestand": [compact_ref(report_uri(report["reportId"])) for report in related_reports],
    })


def catalog_to_jsonld(reports, generated_at=None):
    report_datasets = [
        {
            "@id": report_uri(report["reportId"]),
            "@type": "dcterms:Dataset",
            "dcterms:title": report.get("title"),
            "dcterms:identifier": report.get("reportId"),
            "dcterms:issued": report.get("submittedAt"),
            "dcterms:source": compact_ref(submission_uri(report.get("transactionId"))),
        }
        for report in reports
        if report.get("reportId")
    ]
    return strip_empty({
        "@context": LOD_CONTEXT,
        "@id": f"{PUBLIC_BASE_URI}/doc/imjv/catalog",
        "@type": "dcterms:Catalog",
        "dcterms:title": "IMJV2 LOD-publicatiecatalogus",
        "dcterms:modified": generated_at or now_iso(),
        "dcterms:hasPart": report_datasets,
    })


def report_status(report):
    if report.get("withdrawnByTransactionId"):
        return "ingetrokken"
    if report.get("replacedByReportId"):
        return "vervangen"
    return "actueel"


def strip_empty(value):
    if isinstance(value, dict):
        return {
            key: stripped
            for key, item in value.items()
            if (stripped := strip_empty(item)) is not None
        }
    if isinstance(value, list):
        return [stripped for item in value if (stripped := strip_empty(item)) is not None]
    if value == "":
        return None
    return value


def process_pending(store, reports, exploitations):
    ensure_lod_store(store)
    queued_dir = store / "lod-jobs" / "queued"
    processing_dir = store / "lod-jobs" / "processing"
    done_dir = store / "lod-jobs" / "done"
    failed_dir = store / "lod-jobs" / "failed"
    processed = []
    failed = []
    reports_by_id = {report.get("reportId"): report for report in reports}
    for queued_path in sorted(queued_dir.glob("*.json")):
        processing_path = processing_dir / queued_path.name
        shutil.move(str(queued_path), str(processing_path))
        job = read_json(processing_path)
        try:
            report = reports_by_id.get(job.get("reportId"))
            if report:
                publish_report(store, report)
                exploitation = next(
                    (item for item in exploitations if item.get("exploitatieId") == report.get("exploitatieId")),
                    None,
                )
                if exploitation:
                    publish_exploitation(store, exploitation, reports)
            publish_catalog(store, reports)
            job["processedAt"] = now_iso()
            write_json(done_dir / processing_path.name, job)
            processing_path.unlink()
            processed.append(job)
        except Exception as exc:
            job["failedAt"] = now_iso()
            job["error"] = str(exc)
            write_json(failed_dir / processing_path.name, job)
            processing_path.unlink(missing_ok=True)
            failed.append(job)
    return {"processed": processed, "failed": failed, "status": publication_status(store)}


def publish_report(store, report):
    write_json(store / "lod-publications" / "reports" / f"{report['reportId']}.jsonld", report_to_jsonld(report))


def publish_exploitation(store, exploitation, reports):
    exploitation_id = exploitation.get("exploitatieId")
    if exploitation_id:
        write_json(
            store / "lod-publications" / "exploitations" / f"{exploitation_id}.jsonld",
            exploitation_to_jsonld(exploitation, reports),
        )


def publish_catalog(store, reports):
    write_json(store / "lod-publications" / "catalog.jsonld", catalog_to_jsonld(reports))


def publication_status(store):
    ensure_lod_store(store)
    jobs_root = store / "lod-jobs"
    publications_root = store / "lod-publications"
    return {
        "jobs": {
            "queued": count_json(jobs_root / "queued"),
            "processing": count_json(jobs_root / "processing"),
            "done": count_json(jobs_root / "done"),
            "failed": count_json(jobs_root / "failed"),
        },
        "publications": {
            "reports": sorted(path.stem for path in (publications_root / "reports").glob("*.jsonld")),
            "exploitations": sorted(path.stem for path in (publications_root / "exploitations").glob("*.jsonld")),
            "catalogAvailable": (publications_root / "catalog.jsonld").exists(),
        },
    }


def count_json(path):
    return len(list(path.glob("*.json")))


def publication_path(store, kind, identifier=None):
    root = store / "lod-publications"
    if kind == "catalog":
        return root / "catalog.jsonld"
    if kind == "report":
        return root / "reports" / f"{identifier}.jsonld"
    if kind == "exploitation":
        return root / "exploitations" / f"{identifier}.jsonld"
    return None
