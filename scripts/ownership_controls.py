#!/usr/bin/env python3
"""Manually repair two generated representations to isolate compiler ownership.

These are diagnostic controls, not regenerated bindings or general fixes.
"""
import argparse,json,os,pathlib,shutil,subprocess
p=argparse.ArgumentParser();p.add_argument('--llgo',default='llgo');p.add_argument('--out',default='results/ownership');a=p.parse_args()
root=pathlib.Path(__file__).resolve().parents[1];out=root/a.out;out.mkdir(parents=True,exist_ok=True)
work=root/'.work/ownership';work.mkdir(parents=True,exist_ok=True);rows=[]
for name in ['bit_callback','union_hfa']:
 source=root/'cases'/name;dest=work/name
 if dest.exists():shutil.rmtree(dest)
 shutil.copytree(source,dest)
 before=(source/'generated.snapshot.txt').read_text()
 if name=='bit_callback':
  after=before.replace('type CallbackBits struct {','//llgo:cdecl\ntype CallbackBits struct {')
 else:
  after=before.replace('_xgo_union [1]uint64','_align [0]uint64\n\t_xgo_union [2]float32')
 assert before!=after
 (dest/'generated.go').write_text(after);(out/(name+'-generated.go.txt')).write_text(after)
 cmd=[a.llgo,'test','-count=1','-v','./'+str(dest.relative_to(root))]
 r=subprocess.run(cmd,cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 (out/(name+'.log')).write_text(r.stdout)
 rows.append({'case':name,'command':cmd,'status':'PASS' if r.returncode==0 else 'FAIL','exit':r.returncode})
 print(name,rows[-1]['status'],flush=True)
version=subprocess.run([a.llgo,'version'],capture_output=True,text=True)
(out/'summary.json').write_text(json.dumps({'llgo_root':os.environ.get('LLGO_ROOT'),'version':version.stdout+version.stderr,'pins':json.loads((root/'pins.json').read_text()),'note':'Manual representation controls; generated snapshots originate from macOS arm64. Not a generator fix or universal union ABI representation.','records':rows},indent=2)+'\n')
raise SystemExit(int(any(x['exit'] for x in rows)))
