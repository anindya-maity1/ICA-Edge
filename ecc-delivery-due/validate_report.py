from pathlib import Path
import re, json
p=Path(__file__).parent
s=(p/'ygtptr_sd_delivery_due.abap').read_text()
checks={
 'no_select_star':not re.search(r'SELECT\s+\*',s,re.I),
 'no_placeholders':not any(x in s for x in ['TODO','<IMPLEMENT>','...']),
 'method_names':all(len(x)<=30 for x in re.findall(r'^\s*METHOD\s+(\w+)\.',s,re.M)),
 'three_selects_checked':len(re.findall(r'^\s*SELECT\s',s,re.M))==len(re.findall(r'IF sy-subrc EQ 0\.',s)),
 'six_unit_tests':len(re.findall(r'METHODS \w+ FOR TESTING\.',s))==6,
 'guarded_fae':'IF mt_items IS INITIAL.\n      RETURN.' in s,
 'sales_area_authority':"OBJECT 'V_VBAK_VKO'" in s,
 'order_type_authority':"OBJECT 'V_VBAK_AAT'" in s,
}
depth=0
for line in s.splitlines():
 if re.match(r'\s*LOOP\b',line): depth+=1
 if depth and re.match(r'\s*(SELECT|MODIFY|EXIT)\b',line): raise AssertionError(line)
 if re.match(r'\s*ENDLOOP\.',line): depth-=1
assert all(checks.values()),checks
cases=[(100,40,0,100,40),(100,60,25,75,35),(100,40,50,50,0),(100,100,110,0,0),(100,120,20,80,80),(100,40,-10,100,40)]
for ordered,due,delivered,total,expected in cases:
 d=max(delivered,0); t=max(ordered-d,0); q=min(max(max(due,0)-d,0),t)
 assert (t,q)==(total,expected)
(p/'static_validation.json').write_text(json.dumps({'static_checks':checks,'python_formula_cases_passed':6,'abap_compilation':'NOT RUN','abap_unit':'NOT RUN'},indent=2))
(p/'source_review.md').write_text('# ECC sales orders due for delivery — source review\n\n**Draft for human review.** ECC / ABAP 7.50 / OO Classical / files only. No SAP compilation, activation or ABAP Unit execution has occurred.\n\nShows positive outstanding confirmed quantity due at the cutoff date. Existing outbound deliveries count before goods issue. Uses cumulative earliest-demand allocation, not exact schedule-line allocation or full VL10 eligibility.\n\nBusiness blocks remain visible. Only authorized sales areas and order types are included. See the analysis for exclusions, selection texts and reconciliation tests.\n\n## ABAP source\n\n```abap\n'+s+'```\n')
print(json.dumps(checks,indent=2)); print('Six independent Python formula checks passed. ABAP Unit tests are included but NOT executed.')
