# ECC sales orders due for delivery — source review

**Draft for human review.** ECC / ABAP 7.50 / OO Classical / files only. No SAP compilation, activation or ABAP Unit execution has occurred.

Shows positive outstanding confirmed quantity due at the cutoff date. Existing outbound deliveries count before goods issue. Uses cumulative earliest-demand allocation, not exact schedule-line allocation or full VL10 eligibility.

Business blocks remain visible. Only authorized sales areas and order types are included. See the analysis for exclusions, selection texts and reconciliation tests.

## ABAP source

```abap
REPORT ygtptr_sd_delivery_due.

DATA: gs_header TYPE vbak,
      gs_item   TYPE vbap.
SELECT-OPTIONS:
  s_vbeln FOR gs_header-vbeln,
  s_vkorg FOR gs_header-vkorg OBLIGATORY,
  s_vtweg FOR gs_header-vtweg,
  s_spart FOR gs_header-spart,
  s_kunnr FOR gs_header-kunnr,
  s_werks FOR gs_item-werks,
  s_vstel FOR gs_item-vstel.
PARAMETERS:
  p_due TYPE sy-datum DEFAULT sy-datum OBLIGATORY,
  p_max TYPE i DEFAULT 5000 OBLIGATORY.

CLASS ycl_due_quantity DEFINITION FINAL.
  PUBLIC SECTION.
    TYPES ty_quantity TYPE p LENGTH 16 DECIMALS 6.
    TYPES:
      BEGIN OF ty_result,
        total_open TYPE ty_quantity,
        due_open   TYPE ty_quantity,
      END OF ty_result.
    CLASS-METHODS calculate
      IMPORTING iv_ordered TYPE ty_quantity
                iv_due TYPE ty_quantity
                iv_delivered TYPE ty_quantity
      RETURNING VALUE(rs_result) TYPE ty_result.
ENDCLASS.

CLASS ycl_due_quantity IMPLEMENTATION.
  METHOD calculate.
    DATA lv_delivered TYPE ty_quantity.
    DATA lv_due TYPE ty_quantity.
    lv_delivered = nmax( val1 = iv_delivered val2 = 0 ).
    lv_due = nmax( val1 = iv_due val2 = 0 ).
    rs_result-total_open = nmax(
      val1 = iv_ordered - lv_delivered val2 = 0 ).
    rs_result-due_open = nmin(
      val1 = nmax( val1 = lv_due - lv_delivered val2 = 0 )
      val2 = rs_result-total_open ).
  ENDMETHOD.
ENDCLASS.

CLASS ycl_delivery_due DEFINITION FINAL.
  PUBLIC SECTION.
    METHODS run.
  PRIVATE SECTION.
    TYPES:
      BEGIN OF ty_item,
        vbeln TYPE vbak-vbeln,
        posnr TYPE vbap-posnr,
        auart TYPE vbak-auart,
        vkorg TYPE vbak-vkorg,
        vtweg TYPE vbak-vtweg,
        spart TYPE vbak-spart,
        kunnr TYPE vbak-kunnr,
        lifsk TYPE vbak-lifsk,
        matnr TYPE vbap-matnr,
        arktx TYPE vbap-arktx,
        werks TYPE vbap-werks,
        vstel TYPE vbap-vstel,
        kwmeng TYPE vbap-kwmeng,
        vrkme TYPE vbap-vrkme,
        meins TYPE vbap-meins,
        umvkz TYPE vbap-umvkz,
        umvkn TYPE vbap-umvkn,
        lfsta TYPE vbup-lfsta,
      END OF ty_item,
      BEGIN OF ty_schedule,
        vbeln TYPE vbep-vbeln,
        posnr TYPE vbep-posnr,
        etenr TYPE vbep-etenr,
        edatu TYPE vbep-edatu,
        bmeng TYPE vbep-bmeng,
        lifsp TYPE vbep-lifsp,
      END OF ty_schedule,
      BEGIN OF ty_flow,
        vbelv TYPE vbfa-vbelv,
        posnv TYPE vbfa-posnv,
        vbeln TYPE vbfa-vbeln,
        posnn TYPE vbfa-posnn,
        vbtyp_n TYPE vbfa-vbtyp_n,
        rfmng TYPE vbfa-rfmng,
        meins TYPE vbfa-meins,
        plmin TYPE vbfa-plmin,
      END OF ty_flow,
      BEGIN OF ty_output,
        vbeln TYPE vbak-vbeln,
        posnr TYPE vbap-posnr,
        auart TYPE vbak-auart,
        vkorg TYPE vbak-vkorg,
        vtweg TYPE vbak-vtweg,
        spart TYPE vbak-spart,
        kunnr TYPE vbak-kunnr,
        matnr TYPE vbap-matnr,
        arktx TYPE vbap-arktx,
        werks TYPE vbap-werks,
        vstel TYPE vbap-vstel,
        lfsta TYPE vbup-lfsta,
        first_due TYPE vbep-edatu,
        cutoff TYPE sy-datum,
        meins TYPE vbap-meins,
        ordered_qty TYPE ycl_due_quantity=>ty_quantity,
        confirmed_due TYPE ycl_due_quantity=>ty_quantity,
        delivery_qty TYPE ycl_due_quantity=>ty_quantity,
        total_open TYPE ycl_due_quantity=>ty_quantity,
        due_open TYPE ycl_due_quantity=>ty_quantity,
        header_block TYPE vbak-lifsk,
        schedule_block TYPE abap_bool,
        due_block TYPE abap_bool,
        data_warning TYPE c LENGTH 80,
      END OF ty_output.
    DATA mt_items TYPE SORTED TABLE OF ty_item
      WITH UNIQUE KEY vbeln posnr.
    DATA mt_schedule TYPE SORTED TABLE OF ty_schedule
      WITH UNIQUE KEY vbeln posnr etenr.
    DATA mt_flow TYPE SORTED TABLE OF ty_flow
      WITH NON-UNIQUE KEY vbelv posnv.
    DATA mt_output TYPE STANDARD TABLE OF ty_output WITH EMPTY KEY.
    METHODS read_items.
    METHODS restrict_authority.
    METHODS read_details.
    METHODS build_output.
    METHODS display RAISING cx_salv_msg cx_salv_not_found
                            cx_salv_data_error.
ENDCLASS.

CLASS ycl_delivery_due IMPLEMENTATION.
  METHOD run.
    TRY.
        read_items( ).
        restrict_authority( ).
        IF mt_items IS INITIAL.
          MESSAGE 'No authorized open sales-order items found' TYPE 'S'.
          RETURN.
        ENDIF.
        read_details( ).
        build_output( ).
        IF mt_output IS INITIAL.
          MESSAGE 'No outstanding confirmed delivery quantity is due' TYPE 'S'.
          RETURN.
        ENDIF.
        display( ).
      CATCH cx_root INTO DATA(lx_error).
        DATA(lv_message) = lx_error->get_text( ).
        MESSAGE lv_message TYPE 'S' DISPLAY LIKE 'E'.
    ENDTRY.
  ENDMETHOD.

  METHOD read_items.
    DATA lv_order_category TYPE vbak-vbtyp VALUE 'C'.
    DATA lv_no_rejection TYPE vbap-abgru.
    DATA lv_relevant TYPE vbap-lfrel VALUE 'X'.
    DATA(lv_limit) = p_max + 1.
    SELECT h~vbeln, i~posnr, h~auart, h~vkorg, h~vtweg,
           h~spart, h~kunnr, h~lifsk, i~matnr, i~arktx,
           i~werks, i~vstel, i~kwmeng, i~vrkme, i~meins,
           i~umvkz, i~umvkn, st~lfsta
      FROM vbak AS h
      INNER JOIN vbap AS i ON i~vbeln = h~vbeln
      INNER JOIN vbup AS st
        ON st~vbeln = i~vbeln AND st~posnr = i~posnr
      WHERE h~vbtyp = @lv_order_category
        AND h~vbeln IN @s_vbeln
        AND h~vkorg IN @s_vkorg
        AND h~vtweg IN @s_vtweg
        AND h~spart IN @s_spart
        AND h~kunnr IN @s_kunnr
        AND i~werks IN @s_werks
        AND i~vstel IN @s_vstel
        AND i~abgru = @lv_no_rejection
        AND i~lfrel = @lv_relevant
        AND ( st~lfsta = 'A' OR st~lfsta = 'B' )
      ORDER BY h~vbeln, i~posnr
      INTO CORRESPONDING FIELDS OF TABLE @mt_items
      UP TO @lv_limit ROWS.
    IF sy-subrc EQ 0.
      IF lines( mt_items ) > p_max.
        CLEAR mt_items.
        MESSAGE 'Candidate limit exceeded; narrow selection and rerun'
          TYPE 'S' DISPLAY LIKE 'E'.
      ENDIF.
    ELSE.
      CLEAR mt_items.
    ENDIF.
  ENDMETHOD.

  METHOD restrict_authority.
    DATA lt_allowed LIKE mt_items.
    LOOP AT mt_items INTO DATA(ls_item).
      AUTHORITY-CHECK OBJECT 'V_VBAK_VKO'
        ID 'ACTVT' FIELD '03'
        ID 'VKORG' FIELD ls_item-vkorg
        ID 'VTWEG' FIELD ls_item-vtweg
        ID 'SPART' FIELD ls_item-spart.
      IF sy-subrc = 0.
        AUTHORITY-CHECK OBJECT 'V_VBAK_AAT'
          ID 'ACTVT' FIELD '03'
          ID 'AUART' FIELD ls_item-auart.
        IF sy-subrc = 0.
          INSERT ls_item INTO TABLE lt_allowed.
        ENDIF.
      ENDIF.
    ENDLOOP.
    mt_items = lt_allowed.
  ENDMETHOD.

  METHOD read_details.
    IF mt_items IS INITIAL.
      RETURN.
    ENDIF.
    SELECT vbeln, posnr, etenr, edatu, bmeng, lifsp
      FROM vbep
      FOR ALL ENTRIES IN @mt_items
      WHERE vbeln = @mt_items-vbeln
        AND posnr = @mt_items-posnr
      INTO CORRESPONDING FIELDS OF TABLE @mt_schedule.
    IF sy-subrc EQ 0.
      ASSERT lines( mt_schedule ) > 0.
    ELSE.
      CLEAR mt_schedule.
    ENDIF.
    SELECT vbelv, posnv, vbeln, posnn, vbtyp_n,
           rfmng, meins, plmin
      FROM vbfa
      FOR ALL ENTRIES IN @mt_items
      WHERE vbelv = @mt_items-vbeln
        AND posnv = @mt_items-posnr
        AND vbtyp_v = 'C'
        AND vbtyp_n = 'J'
      INTO CORRESPONDING FIELDS OF TABLE @mt_flow.
    IF sy-subrc EQ 0.
      ASSERT lines( mt_flow ) > 0.
    ELSE.
      CLEAR mt_flow.
    ENDIF.
  ENDMETHOD.

  METHOD build_output.
    CLEAR mt_output.
    LOOP AT mt_items INTO DATA(ls_item).
      DATA(ls_out) = CORRESPONDING ty_output( ls_item ).
      ls_out-header_block = ls_item-lifsk.
      ls_out-cutoff = p_due.
      IF ls_item-umvkz <= 0 OR ls_item-umvkn <= 0.
        MESSAGE 'Invalid item unit conversion; report stopped'
          TYPE 'S' DISPLAY LIKE 'E'.
        CLEAR mt_output.
        RETURN.
      ENDIF.
      ls_out-ordered_qty = CONV decfloat34( ls_item-kwmeng )
        * ls_item-umvkz / ls_item-umvkn.
      DATA lv_confirmed TYPE ycl_due_quantity=>ty_quantity.
      CLEAR lv_confirmed.
      LOOP AT mt_schedule INTO DATA(ls_schedule)
          WHERE vbeln = ls_item-vbeln AND posnr = ls_item-posnr.
        IF ls_schedule-lifsp IS NOT INITIAL.
          ls_out-schedule_block = abap_true.
        ENDIF.
        IF ls_schedule-edatu <> '00000000'
            AND ls_schedule-edatu <= p_due
            AND ls_schedule-bmeng > 0.
          lv_confirmed = lv_confirmed + ls_schedule-bmeng.
          IF ls_out-first_due IS INITIAL
              OR ls_schedule-edatu < ls_out-first_due.
            ls_out-first_due = ls_schedule-edatu.
          ENDIF.
          IF ls_schedule-lifsp IS NOT INITIAL.
            ls_out-due_block = abap_true.
          ENDIF.
        ENDIF.
      ENDLOOP.
      ls_out-confirmed_due = CONV decfloat34( lv_confirmed )
        * ls_item-umvkz / ls_item-umvkn.
      LOOP AT mt_flow INTO DATA(ls_flow)
          WHERE vbelv = ls_item-vbeln AND posnv = ls_item-posnr.
        IF ls_flow-plmin = '+' OR ls_flow-plmin = '-'.
          IF ls_flow-meins <> ls_item-meins.
            MESSAGE 'Document-flow unit mismatch; report stopped'
              TYPE 'S' DISPLAY LIKE 'E'.
            CLEAR mt_output.
            RETURN.
          ENDIF.
          CASE ls_flow-plmin.
            WHEN '+'.
              ls_out-delivery_qty = ls_out-delivery_qty + ls_flow-rfmng.
            WHEN '-'.
              ls_out-delivery_qty = ls_out-delivery_qty - ls_flow-rfmng.
          ENDCASE.
        ELSEIF ls_flow-plmin <> '0'.
          MESSAGE 'Unknown document-flow quantity sign; report stopped'
            TYPE 'S' DISPLAY LIKE 'E'.
          CLEAR mt_output.
          RETURN.
        ENDIF.
      ENDLOOP.
      IF ls_out-delivery_qty < 0.
        ls_out-data_warning = 'Negative net flow; calculation clamps delivery to zero'.
      ELSEIF ls_out-delivery_qty > ls_out-ordered_qty.
        ls_out-data_warning = 'Delivery quantity exceeds ordered quantity'.
      ENDIF.
      DATA(ls_quantity) = ycl_due_quantity=>calculate(
        iv_ordered = ls_out-ordered_qty
        iv_due = ls_out-confirmed_due
        iv_delivered = ls_out-delivery_qty ).
      ls_out-total_open = ls_quantity-total_open.
      ls_out-due_open = ls_quantity-due_open.
      IF ls_out-due_open > 0.
        APPEND ls_out TO mt_output.
      ENDIF.
    ENDLOOP.
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
      'Delivery due overview - cumulative allocation, not VL10 eligibility' ).
    DATA(lo_columns) = lo_alv->get_columns( ).
    DATA lt_quantity_names TYPE STANDARD TABLE OF lvc_fname WITH EMPTY KEY.
    lt_quantity_names = VALUE #( ( 'ORDERED_QTY' ) ( 'CONFIRMED_DUE' )
      ( 'DELIVERY_QTY' ) ( 'TOTAL_OPEN' ) ( 'DUE_OPEN' ) ).
    LOOP AT lt_quantity_names INTO DATA(lv_name).
      DATA(lo_quantity) = CAST cl_salv_column_table(
        lo_columns->get_column( lv_name ) ).
      lo_quantity->set_quantity_column( 'MEINS' ).
      CASE lv_name.
        WHEN 'ORDERED_QTY'.
          lo_quantity->set_long_text( 'Ordered quantity (base unit)' ).
          lo_quantity->set_medium_text( 'Ordered qty' ).
          lo_quantity->set_short_text( 'Ordered' ).
        WHEN 'CONFIRMED_DUE'.
          lo_quantity->set_long_text( 'Confirmed quantity due (base unit)' ).
          lo_quantity->set_medium_text( 'Confirmed due' ).
          lo_quantity->set_short_text( 'Conf. due' ).
        WHEN 'DELIVERY_QTY'.
          lo_quantity->set_long_text( 'Delivery-created quantity (base unit)' ).
          lo_quantity->set_medium_text( 'Delivery-created' ).
          lo_quantity->set_short_text( 'Deliv. qty' ).
        WHEN 'TOTAL_OPEN'.
          lo_quantity->set_long_text( 'Total open quantity (base unit)' ).
          lo_quantity->set_medium_text( 'Total open qty' ).
          lo_quantity->set_short_text( 'Total open' ).
        WHEN 'DUE_OPEN'.
          lo_quantity->set_long_text( 'Open quantity due (base unit)' ).
          lo_quantity->set_medium_text( 'Due open qty' ).
          lo_quantity->set_short_text( 'Due open' ).
      ENDCASE.
    ENDLOOP.
    lo_alv->display( ).
  ENDMETHOD.
ENDCLASS.

CLASS ltc_due_quantity DEFINITION FINAL FOR TESTING
    DURATION SHORT RISK LEVEL HARMLESS.
  PRIVATE SECTION.
    METHODS undelivered FOR TESTING.
    METHODS partial_delivery FOR TESTING.
    METHODS future_only FOR TESTING.
    METHODS fully_delivered FOR TESTING.
    METHODS overconfirmed FOR TESTING.
    METHODS negative_flow FOR TESTING.
ENDCLASS.

CLASS ltc_due_quantity IMPLEMENTATION.
  METHOD undelivered.
    DATA(ls_result) = ycl_due_quantity=>calculate(
      iv_ordered = 100 iv_due = 40 iv_delivered = 0 ).
    cl_abap_unit_assert=>assert_equals( act = ls_result-due_open exp = 40 ).
    cl_abap_unit_assert=>assert_equals( act = ls_result-total_open exp = 100 ).
  ENDMETHOD.
  METHOD partial_delivery.
    DATA(ls_result) = ycl_due_quantity=>calculate(
      iv_ordered = 100 iv_due = 60 iv_delivered = 25 ).
    cl_abap_unit_assert=>assert_equals( act = ls_result-due_open exp = 35 ).
    cl_abap_unit_assert=>assert_equals( act = ls_result-total_open exp = 75 ).
  ENDMETHOD.
  METHOD future_only.
    DATA(ls_result) = ycl_due_quantity=>calculate(
      iv_ordered = 100 iv_due = 40 iv_delivered = 50 ).
    cl_abap_unit_assert=>assert_equals( act = ls_result-due_open exp = 0 ).
    cl_abap_unit_assert=>assert_equals( act = ls_result-total_open exp = 50 ).
  ENDMETHOD.
  METHOD fully_delivered.
    DATA(ls_result) = ycl_due_quantity=>calculate(
      iv_ordered = 100 iv_due = 100 iv_delivered = 110 ).
    cl_abap_unit_assert=>assert_equals( act = ls_result-due_open exp = 0 ).
    cl_abap_unit_assert=>assert_equals( act = ls_result-total_open exp = 0 ).
  ENDMETHOD.
  METHOD overconfirmed.
    DATA(ls_result) = ycl_due_quantity=>calculate(
      iv_ordered = 100 iv_due = 120 iv_delivered = 20 ).
    cl_abap_unit_assert=>assert_equals( act = ls_result-due_open exp = 80 ).
  ENDMETHOD.
  METHOD negative_flow.
    DATA(ls_result) = ycl_due_quantity=>calculate(
      iv_ordered = 100 iv_due = 40 iv_delivered = -10 ).
    cl_abap_unit_assert=>assert_equals( act = ls_result-due_open exp = 40 ).
    cl_abap_unit_assert=>assert_equals( act = ls_result-total_open exp = 100 ).
  ENDMETHOD.
ENDCLASS.

AT SELECTION-SCREEN.
  IF p_max < 1 OR p_max > 50000.
    MESSAGE 'Candidate limit must be between 1 and 50000' TYPE 'E'.
  ENDIF.

START-OF-SELECTION.
  NEW ycl_delivery_due( )->run( ).
```
