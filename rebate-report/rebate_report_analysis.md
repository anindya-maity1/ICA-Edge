---
title: Rebate Condition-Contract Report
subtitle: Code Generation Analysis — S/4HANA 2025
date: 2026-11-24
toc: false
---
# 1. Overview
The deliverable is a read-only OO Classical ABAP starter for S/4HANA 2025 on-premise or Private Cloud, delivered offline. No SAP repository objects have been created or changed. The user confirmed the starter scope and detailed requirements. The shared input folder was empty, so no specification was auto-selected; requirements came from the confirmed conversation, not a document. ABAP language syntax is intended for the standard ABAP language version, not ABAP Cloud.

# 2. Requirements traceability
| Requirement | Implementation | Status |
|---|---|---|
| DR-01 OO executable report | YGTPTR_REBATE_REPORT; local class YCL_REBATE_REPORT | Implemented; SAP validation pending |
| DR-02 Contract/type, customer owner, sales area and key-date filters | Selection screen and READ_DATA | Implemented |
| DR-03 Header SALV with sorting/export | DISPLAY; CL_SALV_TABLE standard functions | Implemented; GUI test pending |
| DR-04 Display authorization and bounded rows | CHECK_AUTHORITY; P_MAX; ordered extra-row detection | Coarse table-level check only; business authorization design open |
| DR-05 Offline delivery and limitations | ABAP source and this analysis | Implemented |

# 3. Generated object inventory
| Object | Type | Purpose |
|---|---|---|
| YGTPTR_REBATE_REPORT | Executable report | Selection screen and read-only ALV |
| YCL_REBATE_REPORT | Local class inside report | Authorization, selection and display; not a separate repository object |
No custom tables, function modules or global classes are required. Selection labels should be maintained as report text elements in SE38/ADT.

# 4. Design decisions
- WCOCOH represents condition-contract headers, unlike ECC classic rebate table KONA. A public third-party Dictionary reference supports the field names; actual S/4HANA 2025 system metadata was not available.
- Direct WCOCOH access is a consciously limited classic starter design. No claim is made that this is the preferred released API or Clean Core design. An appropriate released API/CDS alternative has not been evaluated against the target system.
- Customer owner must be nonblank. Customer owner is not necessarily the settlement payee or every eligible business-volume partner. Vendor-only contracts are excluded.
- Validity is inclusive: DATE_FROM <= key date <= DATE_TO. Deactivated contracts are excluded unless P_INACT is selected. Blank end dates are not treated as unlimited dates.
- Contract type is configurable and deliberately not hard-coded. Select the rebate contract types configured in your system: a customer-owned contract is not automatically a rebate contract.
- One explicit-field SELECT uses current-client Open SQL behavior, server-side filters and deterministic ordering by contract number. It reads at most P_MAX + 1 rows and removes the extra row after a truncation warning. No totals or financial measures are inferred.
- S_TABU_NAM with activity 03 and table WCOCOH is a fail-closed, coarse display gate. This does not reproduce standard condition-contract business authorization checks.
- SALV offers standard sorting, filtering and export in SAP GUI. No write-back or settlement processing is included. Runtime exceptions are displayed without treating them as successful results.

# 5. Validation results
| Check | Result |
|---|---|
| ABAP source exists and contains report/class/selection | Passed local inspection |
| Explicit fields; no SELECT * | Passed local check |
| SELECT inside LOOP; EXIT or MODIFY in LOOP | None; no loops exist |
| Method names at most 30 characters | Passed local check |
| SELECT followed by SY-SUBRC handling | Present after the completed SELECT statement |
| Embedded credentials or incomplete implementation markers | None |
| Requirement traceability | All confirmed requirements mapped; authorization remains partial for production |
| SAP strict syntax, activation, ATC and ABAP Unit | Not executed: no target-system connection |
| Dictionary and authorization-object validation in S/4HANA 2025 | Not executed |
| Functional and performance testing | Not executed |
Local checks are static safeguards, not an ABAP compiler result or evidence of production readiness.

# 6. Known limitations and open items
Before production use, validate all WCOCOH components in SE11 and replace or supplement the coarse table gate with the exact condition-contract, contract-type and organizational authorization checks required by your security design. Do not grant broad table access merely to run this report. Direct Open SQL does not automatically enforce application authorization checks.

Set up a restricted report authorization group and transaction as appropriate. Sales organization is mandatory but a selection restriction is not an authorization check. Exported partner data requires your normal access and data-protection controls.

Maintain selection texts: S_NUM = Condition contract; S_TYPE = Contract type; S_CUST = Customer owner; S_VKORG = Sales organization; S_VTWEG = Distribution channel; S_SPART = Division; P_KEYDT = Valid on; P_INACT = Include deactivated; P_MAX = Maximum rows. Use the configured customer rebate contract types when running the report.

Run syntax check, ATC and activation in a development system. Test no matches, exact start/end dates, inactive inclusion, customer/type/sales-area restrictions, denied table authorization and P_MAX + 1 matches. Verify deterministic truncation and SALV export under the user's authorizations. Compare representative results with standard condition-contract display.

This is an overview of contract headers, not a financial rebate agreement balance report. It does not read accruals, business volume, rates, settlement calendars, settlement documents, settlement payment recipients or calculated payable amounts. It does not join customer names or retrieve all business-volume partners. No automated ABAP Unit test suite is included; target-system tests remain required.

Reference checked: https://leanx.eu/sap/table/wcocoh/ — third-party field metadata, accessed 2026-11-24; not an authoritative release-specific API contract.

# 7. Human review record
Reviewer score: 10/10, explicitly selected by the user. Approval status: Approved. Reviewer comments: No code corrections requested; accept the starter's stated limitations. Business authorizations and SAP syntax/runtime checks remain outstanding. Approval applies to the starter deliverable and does not establish production readiness.
