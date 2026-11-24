---
title: Sales Orders Due for Delivery
subtitle: Code Generation Analysis — ECC / ABAP 7.50
date: 2026-11-24
toc: false
---
# 1. Overview
This read-only Classical OO ABAP report identifies sales-order items with positive confirmed quantities still needing an outbound delivery by a cutoff date. Target: SAP ECC on NetWeaver 7.50, standard ABAP language version and SAP GUI. Delivery means outbound delivery creation, not posted goods issue. Delivery and financial documents are never created or changed.

Document auto-selection found only the previous, unrelated rebate analysis. The user explicitly chose the current request as the specification and confirmed the requirements summary, quantity meaning and DR-01 through DR-10. No input technical specification was used or modified. No GitHub upload is part of this request.

# 2. Requirements traceability
| Requirement | Implementation | Validation state |
|---|---|---|
| DR-01 OO executable report | YGTPTR_SD_DELIVERY_DUE; YCL_DELIVERY_DUE | Source generated; SAP syntax pending |
| DR-02 Selection filters and cutoff | Selection screen; READ_ITEMS | Implemented; target tests pending |
| DR-03 Open, relevant, non-rejected standard sales orders | VBAK category C; VBAP-LFREL and ABGRU; VBUP-LFSTA A/B | Requires reconciliation with local item-category configuration |
| DR-04 Due confirmations in base unit | BUILD_OUTPUT; VBEP-EDATU/BMENG; VBAP conversion factors | Conversion metadata and rounding need target validation |
| DR-05 Signed delivery-created quantity | VBFA C-to-J direct flow, RFMNG/MEINS/PLMIN | Standard-flow assumptions; local reconciliation required |
| DR-06 Positive due-open output | YCL_DUE_QUANTITY=>CALCULATE | Six Python formula cases passed; ABAP Unit pending |
| DR-07 Visible delivery blocks | Header block code; schedule and due-schedule block flags | Standard header/schedule sources implemented; see limitations |
| DR-08 Authorization | V_VBAK_VKO activity 03; additional V_VBAK_AAT display check | Detail retrieval follows checks; security review pending |
| DR-09 SALV and tests | DISPLAY; LTC_DUE_QUANTITY | GUI and ABAP Unit execution pending |
| DR-10 Offline deliverables | ABAP source, analysis, source review and local check results | Files generated; user approved draft at 10/10 |

# 3. Generated object inventory
| Object | Kind | Responsibility |
|---|---|---|
| YGTPTR_SD_DELIVERY_DUE | Executable report | Selection screen and event entry point |
| YCL_DELIVERY_DUE | Local class | Read, authorize, assemble and display |
| YCL_DUE_QUANTITY | Local class | Pure cumulative open-quantity calculation |
| LTC_DUE_QUANTITY | Local ABAP Unit test class | Six quantity-calculation test cases |
Only the executable report is a repository object. There are no custom Dictionary objects or separately deployed classes. The ABAP file includes the local test class.

# 4. Design decisions
- Use ECC standard tables VBAK, VBAP, VBUP, VBEP and VBFA with explicit fields. No SELECT appears inside a loop. This conventional ECC reporting design is not a Clean Core or released-API claim; released alternatives were not validated against a connected system.
- Select ordinary sales orders, category C, with delivery-relevant and unrejected items in not-started or partial item delivery status. Returns and scheduling agreements are outside scope.
- Calculate due confirmation by summing positive VBEP-BMENG for nonblank VBEP-EDATU up to the inclusive cutoff. The requested order date, material-availability date and goods-issue date are not used as substitutes.
- Convert order quantity and confirmed sales quantity to item base units using UMVKZ divided by UMVKN. Use decimal floating-point intermediate multiplication and six-decimal output. VBFA-RFMNG is already a base-unit reference quantity; compare its unit with VBAP-MEINS before aggregation.
- Aggregate direct category-C to category-J flow with PLMIN plus/minus signs; neutral sign 0 does not consume quantity. Assume standard maintenance of flow when deliveries change or are deleted. Stop on unknown signs or mismatched units rather than presenting partial results.
- Clamp negative net delivery to zero for calculation while flagging the raw negative value. Set total open to max(ordered minus nonnegative delivery-created, zero). Set due open to min(total open, max(due-confirmed minus nonnegative delivery-created, zero)).
- This cumulative formula allocates deliveries to earliest confirmed demand first. It is not exact schedule-line allocation and cannot guarantee the result of standard delivery proposal processing in complex scenarios.
- Require display access for each item's sales area and order type. Discard unauthorized candidates before retrieving schedules or flow; never display their details. These checks must be reconciled with local SU24, exits and customer-specific policies.
- Require a sales-organization selection and limit candidate reads to P_MAX plus one. If exceeded, reject the run rather than return a misleading truncated due list. Candidate limit applies before due-date and authorization reduction. Both FOR ALL ENTRIES reads are guarded against an empty driver table and include key fields that prevent accidental collapse of distinct schedule/flow records.
- Flag header delivery-block code, any schedule block and any due-confirmed schedule block. A standard independent item delivery-block field is not assumed: item-relevant standard schedule blocks are rolled up to item rows. Custom item-level block logic is not implemented.

# 5. Validation results
| Check | Result |
|---|---|
| Source created; naming and maximum method-name length | Passed local static checks |
| No SELECT star, placeholders, loop SELECT, loop MODIFY or loop EXIT | Passed local static checks |
| Three SELECT statements followed by SY-SUBRC handling | Passed local static checks |
| Empty-driver guards and authorization statements | Present; static inspection only |
| Six formula cases executed independently in Python | Passed: undelivered, partial, future-only remainder, full/overdelivery, overconfirmation, negative flow |
| Six ABAP Unit methods | Included; not executed |
| ECC Dictionary, SQL syntax, SALV signatures and activation | Not executed; no SAP connection |
| ATC, integration tests, security tests and performance tests | Not executed |
Local validation is not an ABAP compiler, an SAP test run or evidence of production readiness. Source review removed explicit SORT operations on sorted tables. No secrets or credentials are embedded. SALV quantity columns reference the row base-unit field; aggregation across unlike materials or units must not be interpreted as a business total.

# 6. Known limitations and implementation checklist
This is an item-level reporting overview, not a replacement for VL10. ATP, delivery groups, complete/partial-delivery rules, credit blocks, shipping calendars, picking rules, delivery splits, availability checks and all application eligibility logic are not reproduced. Header and schedule delivery blocks are visible but not used to exclude demand. Credit blocks and custom item blocks are not displayed. Existing deliveries awaiting goods issue consume quantity by the confirmed definition.

Validate references and ABAP syntax in your ECC development system, especially VBAP-LFREL, VBUP-LFSTA, VBFA-PLMIN/RFMNG/MEINS and SALV quantity-column methods. Confirm standard document-flow behavior for delivery deletion, quantity changes, batch splits, hierarchy items, cancellations and custom copying control. Exclude or extend unsupported scenarios after reconciliation; no claim of exact historical reconstruction is made.

Pure calculation tests do not cover unit conversion, database retrieval, authorization or SALV. Execute ABAP Unit and ATC, then compare representative item quantities and flow against VA03, delivery display and the relevant standard delivery-due list. Test multiple schedule lines before/after cutoff, date boundaries, zero confirmations, fractional units, partial/full/overdelivery, rejected items, inactive delivery relevance, all blocks, authorization denial, no candidates and candidate overflow. Reconcile negative flow warnings before relying on quantities.

Check unit-specific decimal display and business rounding with fractional conversion factors. Restrict runtime permissions and export access appropriately; set an executable-report authorization group and controlled transaction. Large orders may still yield substantial schedule and flow volumes under the candidate cap. Establish indexes and performance using SQL trace before production use. Text literals are English only.

Maintain report selection texts in SE38/ADT:
| Field | Suggested text |
|---|---|
| S_VBELN | Sales order |
| S_VKORG | Sales organization |
| S_VTWEG | Distribution channel |
| S_SPART | Division |
| S_KUNNR | Sold-to party |
| S_WERKS | Plant |
| S_VSTEL | Shipping point |
| P_DUE | Confirmed delivery due by |
| P_MAX | Maximum candidate items |
The FIRST_DUE output is the earliest confirmed date through cutoff before cumulative delivery allocation, not necessarily the first still-open schedule date. SCHEDULE_BLOCK indicates any schedule block, including future schedules; DUE_BLOCK indicates a block on a due-confirmed schedule. Interpret both with HEADER_BLOCK.

# 7. Human review record
Reviewer score: 10/10, explicitly selected by the user. Approval status: Approved. Reviewer comments: No corrections requested; accept the documented limitations. This explicit approval supersedes the earlier conflicting review selections. SAP compilation, ABAP Unit execution, security testing and delivery-due reconciliation remain outstanding; approval of the draft does not establish production readiness. SAP repository deployment: not requested; no objects created, updated or activated.
