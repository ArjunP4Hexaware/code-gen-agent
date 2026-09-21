# Pair 1 — Header and Label Capture

## 1. STTM Sheet "Accumulator - Optum Daily File" — Rows 14–15

### Row 14 (column letter → cell text)

| Col | Text |
| --- | --- |
| A | Source Data |
| B | *(merged — see A14:I14)* |
| C | *(merged — see A14:I14)* |
| D | *(merged — see A14:I14)* |
| E | *(merged — see A14:I14)* |
| F | *(merged — see A14:I14)* |
| G | *(merged — see A14:I14)* |
| H | *(merged — see A14:I14)* |
| I | *(merged — see A14:I14)* |
| J | *(empty)* |
| K | Data Rules and Primary Keys |
| L | *(merged — see K14:P14)* |
| M | *(merged — see K14:P14)* |
| N | *(merged — see K14:P14)* |
| O | *(merged — see K14:P14)* |
| P | *(merged — see K14:P14)* |
| Q | *(empty)* |
| R | Staging Layer Table |
| S | *(merged — see R14:W14)* |
| T | *(merged — see R14:W14)* |
| U | *(merged — see R14:W14)* |
| V | *(merged — see R14:W14)* |
| W | *(merged — see R14:W14)* |
| X | *(empty)* |
| Y | Standard Layer Table |
| Z | *(merged — see Y14:AD14)* |
| AA | *(merged — see Y14:AD14)* |
| AB | *(merged — see Y14:AD14)* |
| AC | *(merged — see Y14:AD14)* |
| AD | *(merged — see Y14:AD14)* |

### Merged ranges in rows 14–15

| Range | Anchor text |
| --- | --- |
| A14:I14 | Source Data |
| K14:P14 | Data Rules and Primary Keys |
| R14:W14 | Staging Layer Table |
| Y14:AD14 | Standard Layer Table |

### Row 15 (column letter → cell text)

| Col | Text |
| --- | --- |
| A | S.No |
| B | Segment |
| C | Field Name |
| D | Required? |
| E | Format |
| F | Start |
| G | Length |
| H | End |
| I | Description |
| J | *(empty)* |
| K | Data Definition |
| L | PII |
| M | Primary Key |
| N | Critical Data |
| O | Not NULL |
| P | Load Rules |
| Q | *(empty)* |
| R | Workspace |
| S | Target Catalog |
| T | Target Schema Name in DL |
| U | Target Table Name in DL |
| V | Target_Column_Name_in_DL |
| W | Target Data Type in DL |
| X | *(empty)* |
| Y | Workspace |
| Z | Target Catalog |
| AA | Target Schema Name in DL |
| AB | Target Table Name in DL |
| AC | Target_Column_Name_in_DL |
| AD | Target Data Type in DL |

---

## 2. FRD Descriptive Metadata Table (label → value)

> Labels are verbatim from the FRD. Values that name people, systems, or
> vendors are replaced by `<value>`.

| Label | Value |
| --- | --- |
| Name | Descriptive Metadata for the ingestion of Pharmacy Accumulators Inbound files from <value> into Lake House |
| Description | Ingest the Pharmacy Accumulators Inbound files from <value> into Lake House |
| Functional Requirement | Capture Descriptive Metadata |
| Data Source | <value> |
| Object Name | Exchange: AHCHIX_RXACCUM_YYYYMMDD_HHMMSS.txt / Medicare: AHCMEDB_RXACCUM_YYYYMMDD_HHMMSS.txt / Medicare PA: AHCMEDBPA_RXACCUM_YYYYMMDD_HHMMSS.txt |
| Description | This file represents the accumulated deductible and out of pocket balances applied to member claims processed by <value> |
| Frequency | Daily 3:00am Exchange / 4:30am Medicare/Medicare PA |
| LOBs | NCEX, DEEX, FLEX, SCEX, OHEX, INEX, LAEX, 2100, PA01, PA02, SCDS, DEDS, FLDS, LADS, MIDS, NCDS |
| Tags/Keywords | Domain: Pharmacy / Subdomain: Accumulators |
| Government Program | Medicare and Exchange |
| Inbound Ingestion | <value> |
| SFG template (Y/N) | Y |
| SR# for SFG Template | TBD |
| Data Catalog Entry | N/A |
| Impact Details | *(empty)* |
| Solution Acceptance Criteria | The Pharmacy Accumulators Inbound Files with the above descriptive meta data will be ingested into Lake House. |
| Traced/Related Requirements | <value> |
| IS Owner | <value> |
