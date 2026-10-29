#!/usr/bin/env python3
"""Regenerate every binding, run real LLGo tests, distinguish known failures from infrastructure errors."""
import argparse, datetime, json, os, pathlib, platform, re, shutil, subprocess, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
KNOWN={'bit_nested':'AUDIT_LAYOUT','base_bits':'AUDIT_LAYOUT','bit_callback':'AUDIT_LAYOUT','bit_align':'AUDIT_LAYOUT','flexible':'AUDIT_LAYOUT','union_bits':'AUDIT_UNION_BITS','union_hfa':'AUDIT_HFA','covariant':'AUDIT_COVARIANT','bool_typedef':r'cannot convert .*uint64.*(?:Flag|bool)'}
def run(cmd,env=None):
 p=subprocess.run(list(map(str,cmd)),cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 return p.returncode,p.stdout

def main():
 p=argparse.ArgumentParser();p.add_argument('--llgo',default='llgo');p.add_argument('--generator',default='bin/generate');p.add_argument('--target');p.add_argument('--out',default='results/llgo');p.add_argument('--case',action='append'); a=p.parse_args()
 out=ROOT/a.out;out.mkdir(parents=True,exist_ok=True); records=[]
 work=ROOT/'.work'/out.name;work.mkdir(parents=True,exist_ok=True)
 for source in sorted((ROOT/'cases').iterdir()):
  if not source.is_dir() or (a.case and source.name not in a.case):continue
  name=source.name; d=work/name
  if d.exists():shutil.rmtree(d)
  shutil.copytree(source,d)
  lang=(d/'language').read_text().strip(); cmd=[ROOT/a.generator,'-header',d/'input.h','-output',d/'generated.go','-language',lang]
  if a.target:cmd+=['-target',a.target]
  if lang=='c++':cmd+=['-std','c++20']
  rc,log=run(cmd);(out/(name+'-generate.log')).write_text(log)
  record={'case':name,'generate_exit':rc,'generator_command':list(map(str,cmd))}
  if rc:record.update(status='ERROR',reason='generation failed')
  else:
   shutil.copyfile(d/'generated.go',out/(name+'-generated.go.txt'))
   cmd=[a.llgo,'test','-count=1','-v','./'+str(d.relative_to(ROOT))]
   rc,log=run(cmd);(out/(name+'-test.log')).write_text(log)
   pattern=KNOWN.get(name)
   if rc==0:status='XPASS' if pattern else 'PASS'
   elif pattern and re.search(pattern,log,re.S):status='XFAIL'
   elif '--- FAIL:' in log:status='FAIL'
   else:status='ERROR'
   record.update(status=status,test_exit=rc,test_command=cmd)
  records.append(record); print(name,record['status'],flush=True)
 version=run([a.llgo,'version'])[1].strip()
 result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'host':platform.platform(),'llgo':version,'llgo_root':os.environ.get('LLGO_ROOT'),'target':a.target,'pins':json.loads((ROOT/'pins.json').read_text()),'records':records}
 (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
 # XFAIL is preserved as a failed compatibility check, never reported as a pass.
 # The harness succeeds if all failures were classified; XPASS is visible and welcome.
 return int(any(r['status'] in ['ERROR','FAIL'] for r in records))
if __name__=='__main__':sys.exit(main())
