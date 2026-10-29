#!/usr/bin/env python3
"""Compare GC Go and the pinned layout-proposal LLGo; preserve expected C++ mapping failures."""
import argparse,json,os,pathlib,platform,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--llgo',default='llgo');p.add_argument('--out',default='results/proposals');a=p.parse_args();out=ROOT/a.out;out.mkdir(parents=True,exist_ok=True)
env=os.environ.copy();env['AUDIT_CXXFLAGS']='-std=c++20'
items=[('gc',['go','test','-count=1','-v','./proposals/padding','./proposals/layout_runtime'],ROOT,None),('layout-runtime',[a.llgo,'test','-count=1','-v','./proposals/layout_runtime'],ROOT,None),('padding',[a.llgo,'test','-count=1','-v','./proposals/padding'],ROOT,'AUDIT_PADDING')]
if sys.platform!='win32':items.append(('pr761',[a.llgo,'test','-count=1','-v','./proposals/pr761'],ROOT,'AUDIT_VIRTUAL'))
for mode in ['gc','llgo']:items.append(('ssa-patched-'+mode,[a.llgo,'run','.','-sizes',mode],ROOT/'experiments/ssa',None))
records=[]
for name,cmd,cwd,marker in items:
 r=subprocess.run(cmd,cwd=cwd,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(out/(name+'.log')).write_text(r.stdout)
 status='PASS' if r.returncode==0 else 'XFAIL' if marker and marker in r.stdout else 'ERROR'
 if not r.returncode and marker:status='XPASS'
 if name.startswith('ssa-patched-') and status=='PASS' and 'return 5:uintptr, 1:uintptr, 1:uintptr' not in r.stdout:status='FAIL'
 records.append({'case':name,'status':status,'exit':r.returncode,'command':cmd});print(name,status,flush=True)
(out/'summary.json').write_text(json.dumps({'host':platform.platform(),'pins':json.loads((ROOT/'pins.json').read_text()),'records':records},indent=2)+'\n')
sys.exit(int(any(r['status'] in ['ERROR','FAIL'] for r in records)))
