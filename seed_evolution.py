#!/usr/bin/env python3
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import server


def obj(object_type, code, name, properties, relations, status="In gebruik"):
    return {
        "type": object_type,
        "code": code,
        "name": name,
        "properties": properties,
        "relations": relations,
        "status": status,
    }


baseline = [
    obj("Productielijn", "PL-01", "Productielijn keramische granulaten", "Capaciteit: 120000 ton/jaar", ["STK-01", "WZI-01"]),
    obj("Stookinstallatie", "STK-01", "Stoomketel lijn 1", "Thermisch vermogen: 48 MW; brandstof: aardgas", ["PL-01", "EP-L-01"]),
    obj("Waterzuivering", "WZI-01", "Fysico-chemische waterzuivering", "Neutralisatie + sedimentatie + zandfilter; capaciteit: 35 m3/u", ["PL-01", "EP-W-01"]),
    obj("Grondwaterwinning", "GW-01", "Winning productieput noord", "Putdiepte: 82 m; vergund debiet: 180000 m3/jaar; watervoerende laag: HCOV 0600", ["PL-01"]),
    obj("Emissiepunt lucht", "EP-L-01", "Schoorsteen stoomketel", "Hoogte: 32 m; diameter: 1.2 m; Lambert 2008: 156420, 207880", ["STK-01"]),
    obj("Emissiepunt water", "EP-W-01", "Lozingspunt effluent WZI", "Lozend naar oppervlaktewater; Lambert 2008: 156385, 207842", ["WZI-01"]),
]

states = []

state_1 = copy.deepcopy(baseline)
states.append({
    "date": "2027-01-01",
    "title": "Exploitatietoestand d.d. 1-1-2027",
    "change": "Initiële toestand van de exploitatie.",
    "objects": state_1,
})

state_2 = copy.deepcopy(state_1)
state_2[0]["relations"].extend(["STK-02"])
state_2.extend([
    obj("Stookinstallatie", "STK-02", "Droogoven lijn 2", "Thermisch vermogen: 22 MW; brandstof: aardgas; ingebruikname: 20-03-2027", ["PL-01", "EP-L-02"]),
    obj("Emissiepunt lucht", "EP-L-02", "Schoorsteen droogoven lijn 2", "Hoogte: 28 m; diameter: 0.9 m; Lambert 2008: 156448, 207862", ["STK-02"]),
])
states.append({
    "date": "2027-03-20",
    "title": "Exploitatietoestand d.d. 20-3-2027",
    "change": "Droogoven lijn 2 en een bijbehorend luchtemissiepunt zijn in gebruik genomen.",
    "objects": state_2,
})

state_3 = copy.deepcopy(state_2)
state_3.append(obj("Productielijn", "PL-02", "Productielijn recyclaat", "Capaciteit: 45000 ton/jaar; verwerking van keramisch recyclaat", ["STK-02", "WZI-01"]))
state_3[2]["relations"].append("PL-02")
state_3[6]["relations"].append("PL-02")
states.append({
    "date": "2027-06-13",
    "title": "Exploitatietoestand d.d. 13-6-2027",
    "change": "Een tweede productielijn voor keramisch recyclaat is toegevoegd.",
    "objects": state_3,
})

state_4 = copy.deepcopy(state_3)
state_4[2]["properties"] = "Neutralisatie + sedimentatie + zandfilter + membraanfiltratie; capaciteit: 52 m3/u"
state_4[2]["relations"].append("GW-02")
state_4.append(obj("Grondwaterwinning", "GW-02", "Winning productieput zuid", "Putdiepte: 76 m; vergund debiet: 90000 m3/jaar; watervoerende laag: HCOV 0600", ["PL-02", "WZI-01"]))
states.append({
    "date": "2027-09-06",
    "title": "Exploitatietoestand d.d. 6-9-2027",
    "change": "De waterzuivering is uitgebreid en productieput zuid is in gebruik genomen.",
    "objects": state_4,
})

state_5 = copy.deepcopy(state_4)
for item in state_5:
    if item["code"] in {"STK-01", "EP-L-01"}:
        item["status"] = "Buiten gebruik"
state_5[0]["relations"] = [code for code in state_5[0]["relations"] if code != "STK-01"]
state_5[0]["relations"].append("STK-03")
state_5.append(obj("Stookinstallatie", "STK-03", "Elektrische stoomketel", "Elektrisch vermogen: 36 MW; emissievrije warmteopwekking op het terrein", ["PL-01"]))
states.append({
    "date": "2027-11-26",
    "title": "Exploitatietoestand d.d. 26-11-2027",
    "change": "De oude aardgasgestookte stoomketel is buiten gebruik gesteld en vervangen door een elektrische stoomketel.",
    "objects": state_5,
})


def main():
    manifests = []
    for manifest_path in server.SUBMISSIONS.glob("*/manifest.json"):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifests.append((manifest.get("submittedAt") or "", manifest_path, manifest))
    manifests.sort()
    if len(manifests) != len(states):
        raise RuntimeError(f"Verwacht {len(states)} indieningen, vond {len(manifests)}.")

    for index, ((_, manifest_path, manifest), state) in enumerate(zip(manifests, states), start=1):
        transaction_id = manifest["transactionId"]
        submission_dir = manifest_path.parent
        objects = copy.deepcopy(state["objects"])

        report = {
            "reportId": f"REPORT-{transaction_id}",
            "title": state["title"],
            "exploitatie": "Demo Exploitatie NV - DEMO-EXP-001",
            "effectiveFrom": state["date"],
            "location": server.DEFAULT_LOCATION,
            "changeSummary": state["change"],
            "objects": objects,
            "submittedAt": f"{state['date']}T09:15:00+01:00",
        }
        server.write_json(submission_dir / "payload" / server.REPORT_SNAPSHOT_FILE, report)

        ods_path = submission_dir / "original" / manifest["fileName"]
        server.write_ods(ods_path, report)
        manifest.update({
            "displayName": state["title"],
            "summary": state["change"],
            "fileSize": ods_path.stat().st_size,
            "contentHash": server.sha256(ods_path),
            "createdAt": f"{effective_date}T08:45:00+01:00",
            "submittedAt": f"{effective_date}T09:15:00+01:00",
            "receivedAt": f"{effective_date}T09:15:01+01:00",
            "reportHistoryVisible": True,
            "reportSequence": index,
        })
        manifest["storage"]["reportSnapshot"] = f"submissions/{transaction_id}/payload/{server.REPORT_SNAPSHOT_FILE}"
        server.write_json(manifest_path, manifest)
        (submission_dir / "receipt.txt").write_text(server.receipt_text(manifest), encoding="utf-8")
        print(f"{effective_date}: {transaction_id} — {len(objects)} objecten")


if __name__ == "__main__":
    main()
