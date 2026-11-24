REPORT ygtptr_rebate_report.

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
