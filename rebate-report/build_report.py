from pathlib import Path
import re
p = Path(__file__).parent
code = '''REPORT ygtptr_rebate_report.

DATA gs_filter TYPE wcocoh.

SELECT-OPTIONS:
  s_num   FOR gs_filter-num,
  s_type  FOR gs_filter-contract_type,
  s_cust  FOR gs_filter-cust_owner,
  s_vkorg FOR gs_filter-vkorg OBLIGATORY,
  s_vtweg FOR gs_filter-vtweg,
  s_spart FOR gs_filter-spart.
PARAMETERS:
  p_keydt TYPE sy-datum DEFAULT sy-datum OBLIGATORY,
  p_inact AS CHECKBOX DEFAULT space,
  p_max   TYPE i DEFAULT 1000 OBLIGATORY.

CLASS ycl_rebate_report DEFINITION FINAL.
  PUBLIC SECTION.
    METHODS run.
  PRIVATE SECTION.
    TYPES:
      BEGIN OF ty_output,
        num           TYPE wcocoh-num,
        contract_type TYPE wcocoh-contract_type,
        cust_owner    TYPE wcocoh-cust_owner,
        bukrs         TYPE wcocoh-bukrs,
        vkorg         TYPE wcocoh-vkorg,
        vtweg         TYPE wcocoh-vtweg,
        spart         TYPE wcocoh-spart,
        date_from     TYPE wcocoh-date_from,
        date_to       TYPE wcocoh-date_to,
        deact         TYPE wcocoh-deact,
        cc_curr       TYPE wcocoh-cc_curr,
        reference     TYPE wcocoh-reference,
        created_by    TYPE wcocoh-created_by,
        created_on    TYPE wcocoh-created_on,
      END OF ty_output.
    DATA mt_output TYPE STANDARD TABLE OF ty_output WITH EMPTY KEY.
    METHODS check_authority RETURNING VALUE(rv_allowed) TYPE abap_bool.
    METHODS read_data.
    METHODS display.
ENDCLASS.

CLASS ycl_rebate_report IMPLEMENTATION.
  METHOD run.
    IF check_authority( ) = abap_false.
      MESSAGE 'Display authorization for table WCOCOH is required'
        TYPE 'S' DISPLAY LIKE 'E'.
      RETURN.
    ENDIF.
    TRY.
        read_data( ).
        IF mt_output IS INITIAL.
          MESSAGE 'No condition contracts match the selection' TYPE 'S'.
          RETURN.
        ENDIF.
        display( ).
      CATCH cx_root INTO DATA(lx_error).
        DATA(lv_error) = lx_error->get_text( ).
        MESSAGE lv_error TYPE 'S' DISPLAY LIKE 'E'.
    ENDTRY.
  ENDMETHOD.

  METHOD check_authority.
    rv_allowed = abap_false.
    AUTHORITY-CHECK OBJECT 'S_TABU_NAM'
      ID 'TABLE' FIELD 'WCOCOH'
      ID 'ACTVT' FIELD '03'.
    IF sy-subrc = 0.
      rv_allowed = abap_true.
    ENDIF.
  ENDMETHOD.

  METHOD read_data.
    DATA(lv_limit) = p_max + 1.
    DATA lv_blank_owner TYPE wcocoh-cust_owner.
    DATA lv_active TYPE wcocoh-deact.
    CLEAR mt_output.
    SELECT num, contract_type, cust_owner, bukrs,
           vkorg, vtweg, spart, date_from, date_to,
           deact, cc_curr, reference, created_by, created_on
      FROM wcocoh
      WHERE num IN @s_num
        AND contract_type IN @s_type
        AND cust_owner IN @s_cust
        AND cust_owner <> @lv_blank_owner
        AND vkorg IN @s_vkorg
        AND vtweg IN @s_vtweg
        AND spart IN @s_spart
        AND date_from <= @p_keydt
        AND date_to >= @p_keydt
        AND ( deact = @lv_active OR @p_inact = @abap_true )
      ORDER BY num
      INTO CORRESPONDING FIELDS OF TABLE @mt_output
      UP TO @lv_limit ROWS.
    IF sy-subrc EQ 0.
      IF lines( mt_output ) > p_max.
        DELETE mt_output INDEX lv_limit.
        MESSAGE 'Row limit reached; narrow the selection for complete results'
          TYPE 'I'.
      ENDIF.
    ELSE.
      CLEAR mt_output.
    ENDIF.
  ENDMETHOD.

  METHOD display.
    DATA lo_alv TYPE REF TO cl_salv_table.
    cl_salv_table=>factory(
      IMPORTING r_salv_table = lo_alv
      CHANGING t_table = mt_output ).
    lo_alv->get_functions( )->set_all( abap_true ).
    lo_alv->get_columns( )->set_optimize( abap_true ).
    lo_alv->get_display_settings( )->set_striped_pattern( abap_true ).
    lo_alv->get_display_settings( )->set_list_header(
      'Customer rebate condition contracts - header overview' ).
    lo_alv->display( ).
  ENDMETHOD.
ENDCLASS.

AT SELECTION-SCREEN.
  IF p_max < 1 OR p_max > 100000.
    MESSAGE 'Maximum rows must be between 1 and 100000' TYPE 'E'.
  ENDIF.

START-OF-SELECTION.
  NEW ycl_rebate_report( )->run( ).
'''
(p/'ygtptr_rebate_report.abap').write_text(code)
assert not re.search(r'SELECT\s+\*',code,re.I)
assert not re.search(r'\b(TODO|EXIT|UPDATE|INSERT|MODIFY|COMMIT)\b',code,re.I)
assert all(len(n)<=30 for n in re.findall(r'\bMETHOD\s+(\w+)',code))
assert len(re.findall(r'^\s*SELECT num',code,re.M)) == 1
assert 'IF sy-subrc EQ 0.' in code
analysis = '''---
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
Reviewer score: not yet supplied. Approval status: pending human review. Reviewer comments: not yet supplied. No approval or production-readiness score has been inferred by AI.
'''
(p/'rebate_report_analysis.md').write_text(analysis)
preview = '# S/4HANA 2025 — Rebate condition-contract starter\n\n**Review draft — not compiled or activated in SAP.** Read-only customer contract headers; direct table access is not Clean Core. Business authorization checks require target-system completion.\n\nDownload `ygtptr_rebate_report.abap` and consult the accompanying analysis before activation.\n\n## ABAP source\n\n```abap\n' + code + '\n```\n'
(p/'rebate_report_review.md').write_text(preview)
print('Written ABAP source, analysis Markdown and review preview. Static checks passed; SAP checks not executed.')
