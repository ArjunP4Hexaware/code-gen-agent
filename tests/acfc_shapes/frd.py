# ruff: noqa: E501  -- fixture data tables: documented header/label texts kept on one line
"""Synthetic FRD .docx fixtures for the two document families of
docs/acfc/SHAPES_FOR_PORT.md §2.

F1 — six metadata section tables (Descriptive, Structural, Administrative,
Technical, Data Quality, Vendor), each 3 columns: row 0 = section title,
row 1 = Name, row 2 = Description, row 3 = Functional Requirement, rows 4+
= label:value pairs (col 0 section prefix, col 1 label, col 2 value).
Two fixtures cover every label variant the document lists: the pair-1
variant (``Target Catalog and Schema``, ``Load Strategy STD (View)``,
``Inbound File Folder Path``, ``Functional Requirement``) describing the
pair-1 golden columns, and the pair-2 variant (``Target Schema``, ``Load
Strategy STD``, ``Inbound/outbound File Folder Path``) with the blanks §4
documents for pair 2.

F2 — no metadata tables; Heading 1/4 paragraphs and Solution Requirement
tables (10 rows x 4 cols) whose row 4 carries the metadata section label.
"""

from __future__ import annotations

from . import pair1
from .common import docx_bytes, merged, paragraph, table

# ---- F1 label sets (SHAPES_FOR_PORT §2, verbatim) ---------------------------

DESCRIPTIVE = ["Data Source", "Object Name", "Description", "Frequency", "LOBs", "Tags/Keywords",
               "Government Program", "Inbound Ingestion", "SFG template (Y/N)",
               "SR# for SFG Template", "Data Catalog Entry", "Impact Details",
               "Solution Acceptance Criteria", "Traced/Related Requirements", "IS Owner"]
STRUCTURAL_P1 = ["Object/data Format", "Target Catalog and Schema", "Target Table Name",
                 "Domain and Subdomain", "Load Strategy STG", "Load Strategy STD (View)",
                 "Load Strategy Consumption (EDH, BSL)", "Archive Schedule",
                 "Source Data Dictionary", "ADLS Location", "Inbound File Folder Path"]
STRUCTURAL_P2 = ["Object/data Format", "Target Schema", "Target Table Name",
                 "Domain and Subdomain", "Load Strategy STG", "Load Strategy STD",
                 "Load Strategy Consumption (EDH, BSL)", "Archive Schedule",
                 "Source Data Dictionary", "ADLS Location", "Inbound/outbound File Folder Path"]
ADMINISTRATIVE = ["Business Owner", "Technical Owner", "Business Steward (SMEs)",
                  "Technical Steward (SMEs)", "Contact Information (Internal)",
                  "Contact Information (External)", "Data Custodian",
                  "Access Rights/Permissions", "Access Exclusions", "Record Retention Schedule"]
TECHNICAL = ["Business Rules", "Filter Criteria", "Data Definitions", "Critical Data Elements",
             "PII Fields", "Transformation Logic", "Business Key", "Primary Key",
             "Foreign Key(s)", "Unique Key(s)", "Service Level Agreement"]
DATA_QUALITY = ["Uniqueness/Duplicate Record check/reject (HARD - In pipeline)",
                "Incomplete Record Rejection Process (HARD - In pipeline)",
                "Record Recycle Process (HARD - In pipeline)",
                "Date format validation (SOFT - flag)",
                "Referential check against member master (HARD - In pipeline)"]
VENDOR = ["Vendor Name", "Vendor Abbreviation", "Vendor Relationship Manager", "Service Grouping",
          "Data Type", "Vendor Type Agreement", "Delegated Entity"]

SECTION_TITLES = ["Descriptive Metadata", "Structural Metadata", "Administrative Metadata",
                  "Technical Metadata", "Data Quality", "Vendor Metadata"]


def _section(title: str, name: str, description: str, functional: str,
             labels: list[str], values: dict[str, str],
             functional_label: str = "Functional Requirement") -> str:
    rows = [[title, "", ""],
            [title, "Name", name],
            [title, "Description", description],
            [title, functional_label, functional]]
    for label in labels:
        rows.append([title, label, values.get(label, "")])
    return table(rows)


def _common_tables(project: str, feed: str) -> tuple[list[str], list[str]]:
    """(leading tables, trailing tables) an F1 document carries around its
    six metadata sections: version history, LOB crosswalk, ACD items,
    stakeholders, solution requirements, approvers, glossary, references."""
    leading = [
        paragraph(f"Functional Requirements Document — {project}"),
        table([["Version", "Date", "Author", "Description"],
               ["1.0", "2026-01-10", "SYN Author", "Initial"],
               ["1.1", "2026-02-01", "SYN Author", "Reviewed"]]),
        table([["LOB", "Region", "In Scope"], ["ALL", "REGION_A", "Y"], ["ALL", "REGION_B", "Y"]]),
        table([["ACD Type", "Name", "Description"],
               ["Assumption", "Files arrive complete", f"{feed} files arrive as complete drops."],
               ["Constraint", "No transformation", "Stage loads the file as-is."],
               ["Dependency", "Source dictionary", "The vendor data dictionary is current."]]),
        table([["Stakeholder", "Role"], ["SYN Owner", "Business Owner"], ["SYN Lead", "Technical Owner"]]),
    ]
    trailing = [
        table([["Solution Requirement: 1", "", "", ""],
               ["Name", f"Ingest {feed}", "", ""],
               ["Business Requirement", f"Land {feed} files in the lakehouse.", "", ""],
               ["Functional Requirement", "Load stage then standard.", "", ""]]),
        table([["Approver", "Role", "Date"], ["SYN Approver", "Data Governance", ""]]),
        table([["Term", "Definition"], ["STG", "Stage layer"], ["STD", "Standard layer"]]),
        table([["Reference", "Location"], ["STTM", f"{feed} STTM workbook"]]),
    ]
    return leading, trailing


def build_f1_pair1(landing: str | None = None,
                   object_format: str | None = None) -> bytes:
    """F1 pair-1 variant, in the shape the REAL pair-1 FRD has (M9.0; the
    two ACFC captures on ``acfc-hotfix-1``: HANDOVER_GENIE.md §4 error 6 and
    PAIR1_HEADERS.md §2). Structural Metadata: the ``Target Table Name`` cell
    holds an inline layer block (``Staging Layer:`` / ``Table: …`` /
    ``Standard Layer:`` / ``Table: …``) and the ``Target Catalog and Schema``
    cell is blank — the document states no schema and no catalog.
    Descriptive Metadata: the label IS ``Object Name``, but its cell names no
    feed — it lists the inbound FILES as stanzas, a ``<label>:`` line then the
    file name pattern on the next line (PAIR1_REAL_RUN.md §1, the verified
    shape); the ``Name`` row is a sentence about the requirement, and
    ``Tags/Keywords`` holds ``Domain: …`` / ``Subdomain: …`` lines. (NOT
    modelled: the real ``Frequency`` cell is a compound schedule sentence —
    open item.) Other blanks as §4 lists for pair 1. Values are synthetic /
    the aliased golden's (pair1.py)."""
    feed = pair1.FEED_NAME
    stage = f"{pair1.STAGE_CATALOG}.{pair1.STAGE_SCHEMA}"
    standard = f"{pair1.STANDARD_CATALOG}.{pair1.STANDARD_SCHEMA}"
    columns = pair1.columns()
    distinct = list(dict.fromkeys(c.name for c in columns))
    date_columns = [n for n in distinct if pair1.DDL_TYPES[n] == "Date"]
    decimal_columns = [n for n in distinct if pair1.DDL_TYPES[n].startswith("Decimal")]
    functional = (f"Ingest the {feed} fixed-width files from {pair1.VENDOR_NAME} into the stage "
                  f"table {stage}.{pair1.TABLE} and the standard table {standard}.{pair1.TABLE}.")
    sections = [
        _section("Descriptive Metadata", pair1.FRD_REQUIREMENT_NAME, f"{feed} file ingestion",
                 functional, DESCRIPTIVE, {
            "Data Source": pair1.VENDOR_NAME,
            "Object Name": pair1.FRD_OBJECT_NAME_CELL,
            "Description": f"Accumulator balances exchanged with {pair1.VENDOR_NAME}",
            "Frequency": pair1.FREQUENCY,
            "LOBs": pair1.LOB,
            "Tags/Keywords": f"Domain: {pair1.DOMAIN}\nSubdomain: {pair1.SUB_DOMAIN}",
            "Government Program": "Medicaid",
            "Inbound Ingestion": "Yes",
            "SFG template (Y/N)": "Y",
            "SR# for SFG Template": "SYN-SR-001",
            "Data Catalog Entry": "Yes",
            "Solution Acceptance Criteria": (
                "1. Header, Detail and Trailer records land in the single stage table "
                f"{pair1.TABLE} keyed by SEGMENT_IDENTIFIER (00 header, 10 detail, 99 trailer). "
                f"2. Date fields ({', '.join(date_columns)}) are converted from yyyyMMdd to yyyy-MM-dd. "
                f"3. Amount fields ({', '.join(decimal_columns)}) are cast to their STTM decimal types."),
            "Traced/Related Requirements": "SYN-BR-001",
            "IS Owner": "SYN IS Owner",
        }),
        _section("Structural Metadata", feed, f"{feed} structure", functional, STRUCTURAL_P1, {
            # M11 variant (`object_format`): an .xlsx inbound format.
            "Object/data Format": object_format or pair1.FILE_FORMAT,
            "Target Catalog and Schema": "",
            "Target Table Name": pair1.FRD_TARGET_BLOCK,
            "Domain and Subdomain": f"{pair1.DOMAIN} / {pair1.SUB_DOMAIN}",
            "Load Strategy STG": "Append",
            "Load Strategy STD (View)": "Append",
            "Load Strategy Consumption (EDH, BSL)": "N/A",
            "Archive Schedule": "Archive after load; retain 7 years",
            "Source Data Dictionary": f"{feed} VDD (VENDOR_A layout v2)",
            # M10.1 variant (`landing`): the v0.6.0 ACFC cell read
            # "/Path : <storage>/<landing>/..." - a label token before the path.
            "ADLS Location": (landing if landing is not None
                              else f"/{pair1.DOMAIN}/{pair1.SUB_DOMAIN}/"),
            "Inbound File Folder Path": f"inbound\\{pair1.DOMAIN.lower()}\\{pair1.SUB_DOMAIN.lower()}",
        }),
        _section("Administrative Metadata", feed, "", functional, ADMINISTRATIVE, {
            "Business Owner": "SYN Business Owner",
            "Technical Owner": "SYN Technical Owner",
            "Business Steward (SMEs)": "SYN Steward",
            "Technical Steward (SMEs)": "SYN Tech Steward",
            "Contact Information (Internal)": "syn.internal@synthetic.example",
            "Contact Information (External)": "syn.vendor@synthetic.example",
            "Data Custodian": "SYN Custodian",
            "Access Rights/Permissions": "Data engineering group",
            "Access Exclusions": "None",
            "Record Retention Schedule": "7 years",
        }),
        _section("Technical Metadata", feed, f"{feed} technical rules", functional, TECHNICAL, {
            "Business Rules": "Load the file as received; no business filtering.",
            "Filter Criteria": "None",
            "Data Definitions": "Per the STTM",
            "Critical Data Elements": "CARDHOLDER_ID, PLAN_ID",
            "PII Fields": "CARDHOLDER_ID",
            "Transformation Logic": "Dates yyyyMMdd to yyyy-MM-dd; amounts to decimal",
            "Business Key": "CARDHOLDER_ID, PLAN_ID, PLAN_YEAR_START_DATE",
            "Primary Key": "None",
            "Foreign Key(s)": "None",
            "Unique Key(s)": "None",
            "Service Level Agreement": "Loaded within 4 hours of arrival",
        }),
        _section("Data Quality", feed, "", functional, DATA_QUALITY, {
            DATA_QUALITY[0]: "Exact duplicate detail records are rejected.",
            DATA_QUALITY[1]: "Records failing the fixed-width layout are rejected.",
            DATA_QUALITY[2]: "Not applicable — no recycle process for this feed.",
            DATA_QUALITY[3]: "Date fields validated as yyyyMMdd.",
            DATA_QUALITY[4]: "",
        }),
        _section("Vendor Metadata", feed, "", functional, VENDOR, {
            "Vendor Name": pair1.VENDOR_NAME,
            "Vendor Abbreviation": pair1.VENDOR_ABBREVIATION,
            "Vendor Relationship Manager": "SYN VRM",
            "Service Grouping": "Pharmacy Benefit",
            "Data Type": "Accumulator",
            "Vendor Type Agreement": "Delegated",
            "Delegated Entity": "Yes",
        }),
    ]
    leading, trailing = _common_tables("PROJECT_ALPHA", feed)
    return docx_bytes(leading + sections + trailing)


def build_f1_pair2() -> bytes:
    """F1 pair-2 variant: label variants ``Target Schema``, ``Load Strategy
    STD``, ``Inbound/outbound File Folder Path``; Functional Requirement
    blank in every section; blanks per §4 (Object Name, Description,
    Tags/Keywords, Load Strategy Consumption, Archive Schedule, ADLS
    Location, most Admin sub-fields, most DQ rows, Vendor past Abbreviation).
    Two complete metadata sets (one per sub-domain) like the 40-table FRDs."""
    parts: list[str] = []
    leading, trailing = _common_tables("PROJECT_BETA", "FEED_2")
    parts += leading
    for sub in ("Claims", "Members"):
        parts += [
            _section("Descriptive Metadata", f"FEED_2 {sub}", "", "", DESCRIPTIVE, {
                "Data Source": "VENDOR_B", "Frequency": "Daily", "LOBs": "ALL",
                "Government Program": "Medicaid", "Inbound Ingestion": "Yes",
                "SFG template (Y/N)": "N", "SR# for SFG Template": "N/A",
                "Data Catalog Entry": "Pending",
            }),
            _section("Structural Metadata", f"FEED_2 {sub}", "", "", STRUCTURAL_P2, {
                "Object/data Format": "csv", "Target Schema": "stg_vendor_b / vendor_b",
                "Target Table Name": f"feed_2_{sub.lower()}",
                "Domain and Subdomain": f"Claims / {sub}",
                "Load Strategy STG": "Truncate and Load", "Load Strategy STD": "Upsert",
                "Source Data Dictionary": "FEED_2 VDD",
                "Inbound/outbound File Folder Path": "inbound/vendor_b",
            }),
            _section("Administrative Metadata", f"FEED_2 {sub}", "", "", ADMINISTRATIVE, {
                "Business Owner": "SYN Business Owner", "Technical Owner": "SYN Technical Owner",
                "Access Rights/Permissions": "Data engineering group", "Access Exclusions": "None",
                "Record Retention Schedule": "7 years",
            }),
            _section("Technical Metadata", f"FEED_2 {sub}", "", "", TECHNICAL, {
                "Business Rules": "Load as is", "Data Definitions": "Per the STTM",
                "PII Fields": "MEMBER_ID, FIRST_NAME, LAST_NAME, DOB",
                "Transformation Logic": "None", "Business Key": "MEMBER_ID",
                "Primary Key": "MEMBER_ID", "Foreign Key(s)": "None", "Unique Key(s)": "MEMBER_ID",
            }),
            _section("Data Quality", f"FEED_2 {sub}", "", "", DATA_QUALITY, {
                DATA_QUALITY[0]: "Duplicates on MEMBER_ID rejected.",
            }),
            _section("Vendor Metadata", f"FEED_2 {sub}", "", "", VENDOR, {
                "Vendor Name": "VENDOR_B", "Vendor Abbreviation": "VNB",
                "Vendor Relationship Manager": "SYN VRM",
            }),
            # NFR placeholder tables duplicated per set, as in the real documents.
            table([["Non-Functional Requirement", "Value"], ["Availability", ""], ["Performance", ""]]),
        ]
    parts += trailing
    return docx_bytes(parts)


# ---- F2 ---------------------------------------------------------------------

F2_SECTION_LABELS = ["Descriptive Metadata", "Structural Metadata", "Administrative Metadata",
                     "Technical Metadata", "Data Quality Considerations/Options", "Vendor Metadata",
                     "Reject /Recycle Process", "Email"]


def _solution_requirement(number: int, name: str, business: str, functional: str,
                          section_label: str, section_text: str) -> str:
    return table([
        [f"Solution Requirement: {number}", "", "", ""],
        ["Name", name, "", ""],
        ["Business \nRequirement", business, "", ""],
        ["Functional Requirement:", functional, "", ""],
        [section_label, section_text, "", ""],
        ["Impact Details", "", "", ""],
        ["Solution Acceptance Criteria", f"{name} verified in QA.", "", ""],
        ["Priority", "High", "Source/Reference", "SYN-BR-00" + str(number)],
        ["Traced Requirements", f"SYN-BR-00{number}", "", ""],
        ["IS Owner", "SYN IS Owner", "", ""],
    ])


def build_f2_pair8() -> bytes:
    """F2 (pairs 8/9/10 shape): Heading 1 / Heading 4 paragraphs, no
    metadata section tables; one Solution Requirement table per section
    label, the label sitting in row 4 as a cell value. Business Requirement
    carries the embedded newline and Functional Requirement the trailing
    colon that §2 documents for this family."""
    feed = "FEED_8"
    requirements = _f2_pair8_requirements(feed)
    parts = [
        paragraph(f"{feed} Functional Requirements", style="Heading1"),
        table([["Version", "Date", "Author", "Description"], ["1.0", "2026-02-05", "SYN Author", "Initial"]]),
        paragraph("1. Overview", style="Heading1"),
        paragraph(f"{feed} is a multi-segment flat file (HR/DR/TR/FT records) from VENDOR_H."),
        paragraph("2. Solution Requirements", style="Heading1"),
    ]
    for number, (label, name, business, functional, text) in enumerate(requirements, start=1):
        parts.append(paragraph(f"2.{number} {name}", style="Heading4"))
        parts.append(_solution_requirement(number, name, business, functional, label, text))
    parts.append(paragraph("3. Approvals", style="Heading1"))
    parts.append(table([["Approver", "Role"], ["SYN Approver", "Data Governance"]]))
    return docx_bytes(parts)


def _f2_pair8_requirements(feed: str) -> list[tuple[str, str, str, str, str]]:
    """The documented pair-8 requirement content (label, name, business,
    functional, section text) — shared by the round-1 fixture and the
    round-2 geometries, so the two can be compared value for value."""
    return [
        ("Descriptive Metadata", f"Describe the {feed} feed",
         f"Catalog the {feed} feed.", "Register the feed in the data catalog.",
         "Data Source: VENDOR_H; Frequency: Weekly; LOBs: ALL; Object Name: FEED_8"),
        ("Structural Metadata", f"Define {feed} structure",
         "Land the file in stage and standard.", "Create feed_8_hdr/dtl/trl/ftr tables in both layers.",
         "Object/data Format: Fixed Width Text; Target Schema: stg_feed8 / feed8; "
         "Target Table Name: feed_8_hdr, feed_8_dtl, feed_8_trl, feed_8_ftr; "
         "Domain and Subdomain: Claims / Encounters; Load Strategy STG: Truncate and Load; "
         "Load Strategy STD: Append"),
        ("Administrative Metadata", "Ownership", "Assign owners.", "Record owners and stewards.",
         "Business Owner: SYN Business Owner; Technical Owner: SYN Technical Owner"),
        ("Technical Metadata", "Keys and rules", "Identify keys.", "Apply the STTM load rules.",
         "Business Key: MEMBER_KEY, SERVICE_DATE; Primary Key: None; PII Fields: MEMBER_KEY"),
        ("Data Quality Considerations/Options", "Data quality", "Reject malformed records.",
         "Reject records whose length does not match the segment layout.",
         "Incomplete Record Rejection Process (HARD - In pipeline): reject short records"),
        ("Vendor Metadata", "Vendor", "Identify the vendor.", "Record vendor facts.",
         "Vendor Name: VENDOR_H; Vendor Abbreviation: VNH"),
        ("Reject /Recycle Process", "Recycle", "Recycle unmatched members.",
         "Recycle DR records whose MEMBER_KEY is not found; retain 10 days.",
         "Record Recycle Process (HARD - In pipeline): recycle for 10 days"),
        ("Email", "Notifications", "Notify on completion.", "Send success and failure emails.",
         "Success and failure alerts to the production support distribution list"),
    ]


# ---- F2, round 2 (SHAPES_ROUND2 §1 — the REAL pairs 8 / 9 / 10 geometry) ------
#
# The capture: every Solution Requirement table leads with a MERGED column;
# "Solution Requirement: N" sits in a cell merged across columns B-D; rows
# below are Name / Business Requirement / Functional Requirement / <section
# label> / Impact Details / Solution Acceptance Criteria / Priority /
# Source/Reference / Traced Requirements. What the leading column holds is
# not stated, so both plausible Word structures are built: a VERTICAL merge
# down the whole table ("vmerge"), or an empty lead cell in row 0 only
# ("lead"). Pairs 9 and 10 are the topic-organized shape — F3 (M11 item 9),
# built below from §1.2 / §1.3.


def _round2_requirement(number: str, name: str, business: str, functional: str,
                        section_label: str, section_text: str, geometry: str,
                        extra_row: bool = False) -> str:
    rows = [
        ["Name", name],
        ["Business \nRequirement", business],
        ["Functional Requirement:", functional],
        [section_label, section_text],
        ["Impact Details", ""],
        ["Solution Acceptance Criteria", f"{name} verified in QA."],
        ["Priority", "High"],
        ["Source/Reference", f"SYN-BR-{number}"],
        ["Traced/Related Requirements", f"SYN-BR-{number}"],
    ]
    if extra_row:
        rows.insert(0, ["Requirement Type", "Inbound File Data Ingestion"])
    if geometry == "vmerge":
        body = [[merged(vmerge="continue"), label, merged(text, span=2)] for label, text in rows]
        head = [merged(vmerge="restart"), merged(f"Solution Requirement: {number}", span=3)]
    else:                                                    # "lead"
        body = [[label, merged(text, span=3)] for label, text in rows]
        head = ["", merged(f"Solution Requirement: {number}", span=3)]
    return table([head, *body])


def _nfr_tables(count: int) -> list[str]:
    titles = ["Data Management", "Data Migration", "Disaster Recovery Plan",
              "Legal/ Regulatory Requirements", "System Interference",
              "Supportability Requirement", "Performance Requirement", "Security Requirement",
              "Software Quality Attributes", "Code Review", "Service Level Agreement",
              "Data Access", "Email Notification"]
    return [table([[merged(f"Non-Functional Requirement ID: {n}", span=2)],
                   ["Name", titles[(n - 1) % len(titles)]], ["Description", "Not Applicable"]])
            for n in range(1, count + 1)]


def _boilerplate(feed: str) -> list[str]:
    return [
        paragraph("Revision History", style="Title"),
        table([["Date", "Version", "Author(s)", "Description of Version/Changes"],
               ["12/15/25", "1.0", "SYN Author", "Initial"]]),
        paragraph("Intended Audience", style="Heading2"),
        table([["Name", "Role", "Title", "Department"],
               ["SYN Approver", "Approver", "Manager - IS", "EDO Management"]]),
        paragraph("Definitions and Acronyms", style="Heading2"),
        table([["Acronym", "Definition"], ["DL", "Data Lake"]]),
        paragraph("Systems Overview", style="Heading2"),
        table([["Name", "Description"],
               ["System Overview", f"{feed} files processed via scheduling"],
               ["Target", "DL2.0"]]),
        paragraph(f"{feed} Functional Requirements", style="Heading1"),
        table([["Functional Requirement #", "Functional Requirement Definition",
                "Business Requirement #"],
               ["1", f"Descriptive Metadata for the ingestion of {feed} into DL2.0", ""]]),
    ]


def _signoff() -> list[str]:
    return [paragraph("Stakeholder Signoff", style="Heading1"),
            table([["Approver Name", "Signature/Proof", "Date"], ["SYN Approver", "", ""]]),
            paragraph("Reference Documents", style="Heading2"),
            table([["Document Name", "Description", "Network Path"],
                   ["SYN_MAPPING", "Mapping Document", "SharePoint URL"]])]


def build_f2_round2_pair8(geometry: str = "vmerge") -> bytes:
    """Pair 8 in the REAL round-2 geometry (SHAPES_ROUND2 §1.1): 14 tables —
    revision history, audience, glossary, systems overview, requirement
    index, SEVEN Solution Requirement tables (Descriptive, Structural,
    Administrative, Technical, Data Quality, Vendor, Notification), sign-off,
    references. The requirement content is round 1's documented pair-8
    content; only the geometry is round 2's."""
    feed = "FEED_8"
    parts = _boilerplate(feed)
    requirements = [r for r in _f2_pair8_requirements(feed)
                    if r[0] != "Reject /Recycle Process"]
    for number, (label, name, business, functional, text) in enumerate(
            requirements, start=1):
        parts.append(_round2_requirement(str(number), name, business, functional, label,
                                         text, geometry))
    return docx_bytes(parts + _signoff())


def _f3_requirement(number: str, name: str, geometry: str = "vmerge",
                    rows_total: int = 10, merged_name: bool = False) -> str:
    """One topic-organized requirement table (SHAPES_ROUND2 §1.2 / §1.3):
    the round-2 geometry, but its row-4 label names NO metadata section."""
    body = [["Name", name], ["Business \nRequirement", f"{name}."],
            ["Functional Requirement:", f"Deliver: {name}."],
            ["Requirement Detail", "See the mapping document."],
            ["Impact Details", ""], ["Solution Acceptance Criteria", f"{name} verified in QA."],
            ["Priority", "High"], ["Source/Reference", "SYN-BR"],
            ["Traced/Related Requirements", "SYN-BR"]]
    while len(body) < rows_total - 1:
        body.append(["Notes", ""])
    if merged_name:                                   # §1.2 table 9: col B/C merged name
        body[0] = ["Name", merged(name, span=2)]
    head = [merged(vmerge="restart"), merged(f"Solution Requirement: {number}", span=3)]
    rows = [[merged(vmerge="continue"), label, merged(text, span=2)
             if not isinstance(text, dict) else text] for label, text in body]
    return table([head, *rows])


def _f3_front(feed: str, *, domain: bool) -> list[str]:
    parts = [paragraph("Waterfall Lite", style="VerNo"),
             paragraph("Revision History", style="Title"),
             table([["Date", "Version", "Author(s)", "Description of Version/Changes"],
                    ["12/23/2025", "1.0", "SYN Author", "Initial Version."]])]
    if domain:                                        # §1.3 table 1 (pair 10 only)
        parts += [paragraph("Purpose", style="Heading2"),
                  table([["Domain", "SubDomain"], ["Care Management", "Assessments"]])]
    parts += [paragraph("Intended Audience", style="Heading2"),
              table([["Name", "Role", "Title", "Department"],
                     ["SYN Reviewer", "Reviewer", "Director", "Data Products"]]),
              paragraph("Definitions and Acronyms", style="Heading2"),
              table([["Acronym", "Definition"], ["DL", "Data Lake"]]),
              paragraph("Assumptions, Constraints & Dependencies", style="Heading2"),
              table([["ID #", "Name", "Description", "ACD Type"],
                     ["1", "Data Accessibility", f"{feed} data is accessible.", "Assumptions"]])]
    return parts


def _f3_back(nfr: int) -> list[str]:
    return [paragraph("Business Rules", style="Heading2"),
            table([[merged("Business Rule ID: 1", span=2)], ["Name", "NA"],
                   ["Description", "NA"], ["Priority", "NA"], ["Source", "NA"]]),
            *_nfr_tables(nfr),
            paragraph("Stakeholder Signoff", style="Heading1"),
            table([["Approver Name", "Date", "Signature/Proof", "Role"],
                   ["SYN Approver", "", "", ""]]),
            paragraph("Reference Documents", style="Heading2"),
            table([["Document Name", "Description", "Network Path", "Attachment"],
                   ["SYN_MAPPING", "Mapping Document", "SharePoint URL", ""]])]


def build_f3_pair9() -> bytes:
    """SHAPES_ROUND2 §1.2 (pair 9): boilerplate, NINE topic-organized
    requirement tables each after a Heading 4 "Functional Requirement N – …"
    (table 9 with a merged Name cell), a business rule, 12 NFR tables, two
    empty template tables, sign-off, references. No metadata section label
    and no domain table: every field comes from the chain."""
    feed = "FEED_9"
    topics = ["VENDOR_I Source system integration", "New Schemas creation in DL 2.0 Layers",
              "New Tables creation in new HR Schema in DL 2.0",
              "VENDOR_I data Extraction and ingestion into DL 2.0",
              "HR Data Ingestion into Target - Data Lake 2.0",
              "CM Automation – File Ingestion – Process Failure Alert",
              "Administrative information for the HR data ingestion Process",
              "Source to target metadata mapping (STTM)", "ETL Data Quality Rules"]
    parts = _f3_front(feed, domain=False)
    for number, topic in enumerate(topics, start=1):
        parts.append(paragraph(f"Functional Requirement {number} – {topic}", style="Heading4"))
        parts.append(_f3_requirement(str(number), topic, merged_name=number == 6))
    back = _f3_back(12)
    # §1.2 tables 26 / 27: empty template tables before the sign-off
    parts += back[:-4] + [
        paragraph("Technical Implementation", style="Heading1"),
        table([["Component", "Description", "Schema", "Notes"], ["", "", "", ""]]),
        paragraph("Business Rules & Data Transformation", style="Heading1"),
        table([["Rule ID", "Rule Description", "Applicable Table/View", "Transformation Logic"],
               ["", "", "", ""]]),
    ] + back[-4:]
    return docx_bytes(parts)


def build_f3_pair10() -> bytes:
    """SHAPES_ROUND2 §1.3 (pair 10): a Domain / SubDomain table (unique among
    the F2/F3 documents), FOUR sub-numbered requirement tables with trailing
    titles (2.1 … 2.4, outbound vs inbound), 11 rows each, a business rule,
    13 NFR tables, sign-off, references."""
    feed = "FEED_10"
    requirements = [("2.1", "Automated Data Ingestion for Outbound FEED_10 Data"),
                    ("2.2 – Inbound File Data Ingestion",
                     "Automated Data Ingestion for Inbound FEED_10 Data"),
                    ("2.3 - Outbound File Amendments",
                     "Amend the Target schema for the Outbound table in DL."),
                    ("2.4 – Inbound File Data Ingestion",
                     "Automated Data Ingestion for Inbound FEED_10 Data (region B)")]
    parts = _f3_front(feed, domain=True)
    parts.append(paragraph("Solution Requirements", style="Heading2"))
    for number, name in requirements:
        parts.append(_f3_requirement(number, name, rows_total=11))
    parts += _f3_back(13)
    return docx_bytes(parts)


# ---- F1, one block / many files (the pair-11 shape) --------------------------

PAIR11_FILES = ["enrollment_package_YYYY_MM.csv", "disenrollment_package_YYYY_MM.csv",
                "vc_ind_risk_data_package_REGION_A_YYYYMMDD_HHMM.psv"]
PAIR11_OBJECTS = ["Enrollment", "Disenrollment", "Individual Risk"]
PAIR11_PATHS = ["mftlanding\\inbound\\dom_a\\public\\vendor_c",
                "mftlanding\\inbound\\dom_a\\public\\vendor_c",
                "mftlanding\\inbound\\dom_b\\dom_a\\vendor_c"]
PAIR11_DOMAINS = [("Domain Alpha", "Public"), ("Domain Alpha", "Public"),
                  ("Domain Beta", "Domain Alpha")]
PAIR11_POINTER = ("Please refer to the File Details tab of the mapping document attached in \n"
                  "the appendix section.")
PAIR11_DATA_SOURCE = "Vendor Files = Enrollment, Disenrollment & \nIndividual Risk Reports"
PAIR11_VENDOR = "VENDOR_C \u2013 VC 00000"


def build_f1_pair11_multi_file(catalog: str | None = None) -> bytes:
    """F1 variant reproducing the one-block / many-files cell shapes: the
    'Object Name' cell is a 5-column nested table (one row per file), 'ADLS
    Location' a 2-column nested table (object | path), 'Domain and Subdomain'
    holds per-file blocks introduced by "<File> file Ingestion from <Src>:"
    heading lines with "Domain = …" / "Subdomain = …" lines, 'Data Source' is
    a label-prefixed description ("Vendor Files = …") whose label is not the
    field, 'Frequency' is the pointer sentence, 'Target Table Name' lists the
    FILE names, and the section titles carry requirement-ID suffixes. Three
    feeds derive from the one document. ``catalog=None`` reproduces the
    multi-line schema cell that names no catalog; a catalog renders the
    clean "STG: cat.schema; STD: cat.schema" line instead."""
    functional = "Ingest the vendor's three files into the Lakehouse."
    object_rows = [["Vendor", "INB/OUB", "FileName", "FileName", "Vendor"]]
    object_rows += [["VC", "INB", f, f"{o} File", "REGION_A"]
                    for f, o in zip(PAIR11_FILES, PAIR11_OBJECTS, strict=True)]
    location_rows = [["File_Name", "mftlanding path"]]
    location_rows += [[o, p] for o, p in zip(PAIR11_OBJECTS, PAIR11_PATHS, strict=True)]
    domain_blocks = "\n\n".join(
        f"{o} file Ingestion from VC:\nDomain = {d}\nSubdomain = {s}"
        for o, (d, s) in zip(PAIR11_OBJECTS, PAIR11_DOMAINS, strict=True))
    if catalog is None:
        schema = ("stg_dom_a/dom_a \u2013 Enrollment & Disenrollment File\n"
                  "stg_dom_b/dom_b \u2013 Individual Risk File")
    else:
        schema = f"STG: {catalog}.stg_dom_a; STD: {catalog}.dom_a"
    descriptive = table([
        ["Descriptive Metadata: MDD000011", "", ""],
        ["Descriptive Metadata: MDD000011", "Name", "Descriptive Metadata"],
        ["Descriptive Metadata: MDD000011", "Description",
         "The FRD is developed to ingest the region's monthly Enrollment,\n"
         "Disenrollment & Individual Risk reports from the VC vendor."],
        ["Descriptive Metadata: MDD000011", "Functional Requirement", functional],
        ["Descriptive Metadata", "Data Source", PAIR11_DATA_SOURCE],
        ["", "Object Name", object_rows],
        ["", "Description", ""],
        ["", "Frequency", PAIR11_POINTER],
        ["", "LOBs", "LOB_A"],
        ["", "Tags/Keywords", ""],
        ["", "Government Program", "Y"],
        ["", "Inbound Ingestion", "Yes"],
        ["", "SFG template (Y/N)", "Yes"],
        ["", "SR# for SFG Template", "<TBD>"],
        ["", "Data Catalog Entry", "<TBD>"],
    ])
    structural = table([
        ["Structural Metadata: MDST000011", "", ""],
        ["Structural Metadata: MDST000011", "Name", "Structural Metadata"],
        ["Structural Metadata: MDST000011", "Description",
         "The vendor shall provide the data in files brought to the raw layer of ADLS."],
        ["Structural Metadata: MDST000011", "Functional Requirement", functional],
        ["Structural Metadata", "Object/data Format", "File Data Ingestion"],
        ["", "Target Schema", schema],
        ["", "Target Table Name", "\n".join(PAIR11_FILES)],
        ["", "Domain and Subdomain", domain_blocks],
        ["", "Load Strategy STG", "Truncate and Load"],
        ["", "Load Strategy STD", "Append"],
        ["", "Load Strategy Consumption (EDH, BSL)", ""],
        ["", "Archive Schedule", ""],
        ["", "Source Data Dictionary",
         "File and field descriptions are mentioned in the mapping document."],
        ["", "ADLS Location", location_rows],
        ["", "Inbound/outbound File Folder Path", "Inbound"],
    ])
    technical = table([
        ["Technical Metadata: MDT000011", "", ""],
        ["Technical Metadata: MDT000011", "Name", "Technical Metadata"],
        ["Technical Metadata: MDT000011", "Description", ""],
        ["Technical Metadata: MDT000011", "Functional Requirement", functional],
        ["Technical Metadata", "Business Rules", "Data Quality Rules Provided in the Mapping document."],
        ["", "Filter Criteria", ""],
        ["", "PII Fields", "Included in the Mapping Document"],
        ["", "Transformation Logic", "NA"],
        ["", "Primary Key", "NA"],
    ])
    vendor = table([
        ["Vendor Metadata: MDV000011", "", ""],
        ["Vendor Metadata: MDV000011", "Name", "Vendor Metadata"],
        ["Vendor Metadata: MDV000011", "Description", ""],
        ["Vendor Metadata: MDV000011", "Functional Requirement", functional],
        ["Vendor Metadata", "Vendor Name", PAIR11_VENDOR],
        ["", "Vendor Abbreviation", "VC \u2013 Vendor C"],
        ["", "Service Grouping", ""],
    ])
    leading, trailing = _common_tables("PROJECT_GAMMA", "VC files")
    return docx_bytes(leading + [descriptive, structural, technical, vendor] + trailing)


def build_f1_pair11_multi_file_catalog() -> bytes:
    return build_f1_pair11_multi_file(catalog="cat_syn")


BUILDERS = {
    "frd/f1_pair_1.docx": build_f1_pair1,
    "frd/f1_pair_2_variant.docx": build_f1_pair2,
    "frd/f2_pair_8.docx": build_f2_pair8,
    "frd/f1_pair_11_multi_file.docx": build_f1_pair11_multi_file,
    "frd/f1_pair_11_multi_file_catalog.docx": build_f1_pair11_multi_file_catalog,
}
