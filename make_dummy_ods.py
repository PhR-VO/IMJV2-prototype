from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED
from xml.sax.saxutils import escape


OUT = Path(__file__).parent / "assets" / "structurele-gegevens-imjv2.ods"

rows = [
    ["Type", "Code", "Naam", "Eigenschappen", "Verbonden met", "Status"],
    [
        "Productielijn",
        "PL-01",
        "Productielijn keramische granulaten",
        "Capaciteit: 120000 ton/jaar",
        "STK-01; WZI-01",
        "In gebruik",
    ],
    [
        "Stookinstallatie",
        "STK-01",
        "Stoomketel lijn 1",
        "Thermisch vermogen: 48 MW; brandstof: aardgas; datum ingebruikname: 2018-04-15",
        "PL-01; EP-L-01",
        "In gebruik",
    ],
    [
        "Waterzuivering",
        "WZI-01",
        "Fysico-chemische waterzuivering",
        "Techniek: neutralisatie + sedimentatie + zandfilter; capaciteit: 35 m3/u",
        "PL-01; EP-W-01",
        "In gebruik",
    ],
    [
        "Grondwaterwinning",
        "GW-01",
        "Winning productieput noord",
        "Putdiepte: 82 m; debietmeter: DM-4451; watervoerende laag: HCOV 0600",
        "PL-01",
        "In gebruik",
    ],
    [
        "Emissiepunt lucht",
        "EP-L-01",
        "Schoorsteen stoomketel",
        "Hoogte: 32 m; diameter: 1.2 m; Lambert 2008: 156420, 207880",
        "STK-01",
        "In gebruik",
    ],
    [
        "Emissiepunt water",
        "EP-W-01",
        "Lozingspunt effluent WZI",
        "Type: lozend; bestemming: oppervlaktewater; Lambert 2008: 156385, 207842",
        "WZI-01",
        "In gebruik",
    ],
]


def cell(value: str) -> str:
    return (
        '<table:table-cell office:value-type="string">'
        f"<text:p>{escape(value)}</text:p>"
        "</table:table-cell>"
    )


def row(values: list[str]) -> str:
    return "<table:table-row>" + "".join(cell(v) for v in values) + "</table:table-row>"


content_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<office:document-content
  xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
  xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
  xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
  xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
  office:version="1.2">
  <office:automatic-styles/>
  <office:body>
    <office:spreadsheet>
      <table:table table:name="Exploitatietoestand 1-1-2027">
        {''.join(row(r) for r in rows)}
      </table:table>
    </office:spreadsheet>
  </office:body>
</office:document-content>
"""

styles_xml = """<?xml version="1.0" encoding="UTF-8"?>
<office:document-styles
  xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
  xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
  office:version="1.2">
  <office:styles/>
</office:document-styles>
"""

manifest_xml = """<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest
  xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"
  manifest:version="1.2">
  <manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.spreadsheet"/>
  <manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>
  <manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/>
</manifest:manifest>
"""

OUT.parent.mkdir(parents=True, exist_ok=True)
with ZipFile(OUT, "w") as zf:
    zf.writestr("mimetype", "application/vnd.oasis.opendocument.spreadsheet", compress_type=ZIP_STORED)
    zf.writestr("content.xml", content_xml, compress_type=ZIP_DEFLATED)
    zf.writestr("styles.xml", styles_xml, compress_type=ZIP_DEFLATED)
    zf.writestr("META-INF/manifest.xml", manifest_xml, compress_type=ZIP_DEFLATED)

print(OUT)
