import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path


PUBLIC_BASE_URI = "https://data.omgeving.vlaanderen.be"
RIEPR_BASE_URI = "https://data.riepr.omgeving.vlaanderen.be"
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

RIEPR_CONTEXT = {
    "id": "@id",
    "type": "@type",
    "geo": "http://www.opengis.net/ont/geosparql#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "adms": "http://www.w3.org/ns/adms#",
    "dct": "http://purl.org/dc/terms/",
    "locn": "http://www.w3.org/ns/locn#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "prov": "http://www.w3.org/ns/prov#",
    "schema": "http://schema.org/",
    "riepr": f"{RIEPR_BASE_URI}/ns/riepr#",
    "meetpunt": f"{RIEPR_BASE_URI}/id/meetpunt/",
    "emissiepunt": f"{RIEPR_BASE_URI}/id/emissiepunt/",
    "activiteit": f"{RIEPR_BASE_URI}/id/activiteit/",
    "procedure": f"{RIEPR_BASE_URI}/id/procedure/",
    "sosa": "http://www.w3.org/ns/sosa/",
    "ssn": "http://www.w3.org/ns/ssn/",
    "p-plan": "http://purl.org/net/p-plan#",
    "concept": f"{RIEPR_BASE_URI}/id/concept/",
    "apparaat": f"{RIEPR_BASE_URI}/id/apparaat/",
    "qudt": "http://qudt.org/schema/qudt/",
    "localId": "riepr:localId",
    "label": {"@language": "nl", "@id": "rdfs:label"},
    "comment": {"@language": "nl", "@id": "rdfs:comment"},
    "identifier": {"@type": "@id", "@id": "adms:identifier"},
    "atLocation": {"@type": "@id", "@id": "prov:atLocation"},
    "hadPrimarySource": {"@type": "@id", "@id": "prov:hadPrimarySource"},
    "wasAttributedTo": {"@type": "@id", "@id": "prov:wasAttributedTo"},
    "wasDerivedFrom": {"@id": "prov:wasDerivedFrom", "@type": "@id"},
    "wasRevisionOf": {"@id": "prov:wasRevisionOf", "@type": "@id"},
    "deployedOnPlatform": {"@id": "ssn:deployedOnPlatform", "@type": "@id"},
    "deployedSystem": {"@id": "ssn:deployedSystem", "@type": "@id"},
    "hasDeployment": {"@id": "ssn:hasDeployment", "@type": "@id"},
    "hasSubSystem": {"@id": "ssn:hasSubSystem", "@type": "@id"},
    "hasGeometry": {"@type": "@id", "@id": "geo:hasGeometry"},
    "hasSerialization": {"@id": "geo:hasSerialization", "@type": "geo:WKTLiteral"},
    "status": {"@id": "adms:status", "@type": "@id"},
    "issued": {"@id": "dct:issued", "@type": "xsd:date"},
    "created": {"@id": "dct:created", "@type": "xsd:dateTime"},
    "modified": {"@id": "dct:modified", "@type": "xsd:dateTime"},
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
        "lod-publications/riepr/reports",
        "lod-publications/riepr/exploitations",
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


def riepr_report_uri(report_id):
    return f"{RIEPR_BASE_URI}/id/aangifte/{report_id}"


def riepr_exploitation_uri(exploitation_id, effective_from=None):
    suffix = f"/{effective_from}" if effective_from else ""
    return f"{RIEPR_BASE_URI}/id/exploitatie/{exploitation_id}{suffix}"


def riepr_location_uri(exploitation_id, effective_from=None):
    suffix = f"/{effective_from}" if effective_from else ""
    return f"{RIEPR_BASE_URI}/id/exploitatielocatie/{exploitation_id}{suffix}"


def riepr_object_uri(report, item):
    exploitation_id = report.get("exploitatieId") or "onbekend"
    code = item.get("code") or "zonder-code"
    return f"{RIEPR_BASE_URI}/id/object/{exploitation_id}/{code}"


def riepr_transaction_uri(transaction_id):
    return f"{RIEPR_BASE_URI}/id/transactie/{transaction_id}"


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
        if (publication_path(store, "report", report_id).exists()
                and publication_path(store, "report", report_id, profile="riepr").exists()) or report_id in queued_report_ids:
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


def riepr_status_uri(report):
    if report.get("withdrawnByTransactionId"):
        return f"{RIEPR_BASE_URI}/id/concept/status/ingetrokken"
    if report.get("replacedByReportId"):
        return f"{RIEPR_BASE_URI}/id/concept/status/vervangen"
    return f"{RIEPR_BASE_URI}/id/concept/status/in_gebruik"


def riepr_object_type(item):
    item_type = str(item.get("type") or "").lower()
    if "emissiepunt" in item_type:
        return "riepr:Emissiepunt"
    if "grondwater" in item_type or "onttrek" in item_type:
        return "riepr:Onttrekkingspunt"
    if "productielijn" in item_type or "proces" in item_type:
        return "riepr:Proces"
    return "riepr:Installatie"


def lambert_wkt(location):
    coordinates = (location or {}).get("lambert2008") or {}
    x = coordinates.get("x")
    y = coordinates.get("y")
    if x is None or y is None:
        return None
    return f"<http://www.opengis.net/def/crs/EPSG/0/3812> POINT({x} {y})"


def riepr_report_to_jsonld(report):
    effective_from = report.get("effectiveFrom")
    created = report.get("submittedAt") or report.get("receivedAt")
    modified = report.get("receivedAt") or report.get("submittedAt")
    exploitation_id = report.get("exploitatieId")
    exploitation_ref = riepr_exploitation_uri(exploitation_id, effective_from)
    location_ref = riepr_location_uri(exploitation_id, effective_from)
    transaction_ref = riepr_transaction_uri(report.get("transactionId"))
    objects = report.get("objects") or []
    object_by_code = {item.get("code"): item for item in objects if item.get("code")}
    object_nodes = []
    object_refs = []
    for item in objects:
        item_ref = riepr_object_uri(report, item)
        object_refs.append(compact_ref(item_ref))
        relation_refs = []
        for related_code in item.get("relations") or []:
            related = object_by_code.get(related_code)
            if related:
                relation_refs.append(compact_ref(riepr_object_uri(report, related)))
        object_nodes.append({
            "id": item_ref,
            "type": [riepr_object_type(item), "ssn:System"],
            "localId": item.get("code"),
            "label": item.get("name"),
            "comment": item.get("properties"),
            "issued": effective_from,
            "created": created,
            "modified": modified,
            "status": compact_ref(riepr_status_uri(report)),
            "hasDeployment": compact_ref(exploitation_ref),
            "hasSubSystem": relation_refs,
            "dct:type": item.get("type"),
        })

    location = report.get("location") or {}
    address = location.get("address") or {}
    graph = [
        {
            "id": riepr_report_uri(report["reportId"]),
            "type": "riepr:Aangifte",
            "localId": report.get("reportId"),
            "label": report.get("title"),
            "issued": effective_from,
            "created": created,
            "modified": modified,
            "hadPrimarySource": compact_ref(submission_uri(report.get("transactionId"))),
            "wasDerivedFrom": compact_ref(riepr_report_uri(report.get("basedOnReportId"))) if report.get("basedOnReportId") else None,
            "wasRevisionOf": compact_ref(riepr_report_uri(report.get("replacesReportId"))) if report.get("replacesReportId") else None,
        },
        {
            "id": exploitation_ref,
            "type": "riepr:Exploitatie",
            "localId": exploitation_id,
            "label": report.get("exploitatie"),
            "issued": effective_from,
            "created": created,
            "modified": modified,
            "status": compact_ref(riepr_status_uri(report)),
            "deployedOnPlatform": compact_ref(location_ref),
            "deployedSystem": object_refs,
            "riepr:aangifte": compact_ref(riepr_report_uri(report["reportId"])),
        },
        {
            "id": location_ref,
            "type": ["riepr:Exploitatielocatie", "geo:Feature", "sosa:Platform"],
            "localId": exploitation_id,
            "label": report.get("exploitatie"),
            "issued": effective_from,
            "created": created,
            "modified": modified,
            "locn:address": {
                "type": "locn:Address",
                "locn:thoroughfare": address.get("street"),
                "locn:locatorDesignator": address.get("houseNumber"),
                "locn:postCode": address.get("postalCode"),
                "locn:postName": address.get("municipality"),
                "schema:addressCountry": address.get("country"),
            },
            "hasGeometry": {
                "id": f"{location_ref}/geometrie",
                "type": "geo:Geometry",
                "hasSerialization": lambert_wkt(location),
            } if lambert_wkt(location) else None,
            "ssn:inDeployment": compact_ref(exploitation_ref),
        },
        {
            "id": transaction_ref,
            "type": "riepr:Transactie",
            "localId": report.get("transactionId"),
            "label": f"Indiening {report.get('transactionId')}",
            "created": created,
            "modified": modified,
            "prov:generated": compact_ref(riepr_report_uri(report["reportId"])),
            "hadPrimarySource": compact_ref(submission_uri(report.get("transactionId"))),
        },
        *object_nodes,
    ]
    return strip_empty({"@context": RIEPR_CONTEXT, "@graph": graph})


def riepr_exploitation_to_jsonld(exploitation, reports):
    exploitation_id = exploitation.get("exploitatieId")
    related_reports = [
        report for report in reports
        if report.get("exploitatieId") == exploitation_id and report.get("reportId")
    ]
    systems = []
    for report in related_reports:
        for item in report.get("objects") or []:
            systems.append(compact_ref(riepr_object_uri(report, item)))
    latest = related_reports[0] if related_reports else {}
    return strip_empty({
        "@context": RIEPR_CONTEXT,
        "id": riepr_exploitation_uri(exploitation_id),
        "type": "riepr:Exploitatie",
        "localId": exploitation_id,
        "label": exploitation.get("exploitatie"),
        "issued": latest.get("effectiveFrom"),
        "created": latest.get("submittedAt"),
        "modified": latest.get("receivedAt"),
        "status": compact_ref(riepr_status_uri(latest)) if latest else None,
        "deployedSystem": systems,
        "wasDerivedFrom": [compact_ref(riepr_report_uri(report["reportId"])) for report in related_reports],
    })


def riepr_catalog_to_jsonld(reports, generated_at=None):
    return strip_empty({
        "@context": RIEPR_CONTEXT,
        "id": f"{RIEPR_BASE_URI}/doc/imjv/catalog",
        "type": "dct:Catalog",
        "label": "IMJV2 RIEPR LOD-publicatiecatalogus",
        "modified": generated_at or now_iso(),
        "dct:hasPart": [
            {
                "id": riepr_report_uri(report["reportId"]),
                "type": "dct:Dataset",
                "label": report.get("title"),
                "localId": report.get("reportId"),
                "issued": report.get("effectiveFrom"),
                "hadPrimarySource": compact_ref(submission_uri(report.get("transactionId"))),
            }
            for report in reports
            if report.get("reportId")
        ],
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
    write_json(
        store / "lod-publications" / "riepr" / "reports" / f"{report['reportId']}.jsonld",
        riepr_report_to_jsonld(report),
    )


def publish_exploitation(store, exploitation, reports):
    exploitation_id = exploitation.get("exploitatieId")
    if exploitation_id:
        write_json(
            store / "lod-publications" / "exploitations" / f"{exploitation_id}.jsonld",
            exploitation_to_jsonld(exploitation, reports),
        )
        write_json(
            store / "lod-publications" / "riepr" / "exploitations" / f"{exploitation_id}.jsonld",
            riepr_exploitation_to_jsonld(exploitation, reports),
        )


def publish_catalog(store, reports):
    write_json(store / "lod-publications" / "catalog.jsonld", catalog_to_jsonld(reports))
    write_json(store / "lod-publications" / "riepr" / "catalog.jsonld", riepr_catalog_to_jsonld(reports))


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
            "riepr": {
                "reports": sorted(path.stem for path in (publications_root / "riepr" / "reports").glob("*.jsonld")),
                "exploitations": sorted(path.stem for path in (publications_root / "riepr" / "exploitations").glob("*.jsonld")),
                "catalogAvailable": (publications_root / "riepr" / "catalog.jsonld").exists(),
            },
        },
    }


def count_json(path):
    return len(list(path.glob("*.json")))


def publication_path(store, kind, identifier=None, profile="imjv"):
    root = store / "lod-publications"
    if profile == "riepr":
        root = root / "riepr"
    if kind == "catalog":
        return root / "catalog.jsonld"
    if kind == "report":
        return root / "reports" / f"{identifier}.jsonld"
    if kind == "exploitation":
        return root / "exploitations" / f"{identifier}.jsonld"
    return None
