#!/usr/bin/env python3
"""Manual diagnostic lane: serialized compilation and smaller packed/generic programs."""
import argparse,json,pathlib,subprocess
p=argparse.ArgumentParser();p.add_argument('--llgo',default='llgo');p.add_argument('--out',default='results/codegen-isolation');p.add_argument('--plain-only',action='store_true');a=p.parse_args()
ROOT=pathlib.Path(__file__).resolve().parents[1];out=ROOT/a.out;out.mkdir(parents=True,exist_ok=True);rows=[]
items=[] if a.plain_only else [('full-serial',[a.llgo,'test','-p=1','-count=1','-v','./proposals/layout_runtime'])]
names=['promoted','promoted_fixed','promoted_offset','direct_offset']
if not a.plain_only:names+=['packed_arg','pack2_arg','native_func']
for name in names:items.append((name,[a.llgo,'run','-p=1','./experiments/packed_codegen/'+name]))
for name,cmd in items:
 r=subprocess.run(cmd,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(out/(name+'.log')).write_text(r.stdout);rows.append({'case':name,'command':cmd,'exit':r.returncode,'status':'PASS' if r.returncode==0 else 'COMPILER_CRASH' if 'SIGSEGV' in r.stdout else 'ERROR'});print(name,rows[-1]['status'],flush=True)
(out/'summary.json').write_text(json.dumps(rows,indent=2)+'\n')
# Diagnostic lane records compiler failures as data; it does not mark them passing.
