#!/usr/bin/env python3
"""Regenerate every binding, run real LLGo tests, distinguish known failures from infrastructure errors."""
import argparse, datetime, json, os, pathlib, platform, re, shutil, subprocess, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
KNOWN={'bit_nested':'AUDIT_LAYOUT','base_bits':'AUDIT_LAYOUT','bit_callback':'AUDIT_LAYOUT','bit_align':'AUDIT_LAYOUT','flexible':'AUDIT_LAYOUT','union_bits':'AUDIT_UNION_BITS','union_hfa':'AUDIT_HFA','covariant':'AUDIT_COVARIANT','bool_typedef':r'cannot convert .*uint64.*(?:Flag|bool)'}
KNOWN.update({name:'AUDIT_LAYOUT' for name in ['packed_plain','aligned_plain','empty_plain','empty_nua','nonvirtual_tail']})
KNOWN.update({'nontrivial_value':'AUDIT_NONTRIVIAL','member_pointers':'undefined: Holder','template_specialization':'undefined: B','atomic_member':'undefined: AtomicMember'})
GEN_KNOWN={'concept_specialization':'loadDecl: unknown kind - 604'}
def classify(name,code,log,generation_log,target):
 pattern=KNOWN.get(name)
 if code==0:return ('XPASS' if pattern else 'PASS'),None
 # Independently verified Win32 failures. They are different failure modes
 # from the native 64-bit case, so preserve a separate reason in the JSON.
 if target=='i686-pc-windows-msvc':
  if name=='bit_callback' and 'opaque storage' in generation_log and 'type CallbackBits has no field or method Callback' in log:
   return 'XFAIL','win32_opaque_callback_access'
  if name=='nontrivial_value' and 'undefined symbol: __accept_nontrivial' in log:
   return 'XFAIL','win32_symbol_double_decoration'
  if name=='union_hfa' and 'AUDIT_LAYOUT align Go=4 C=8' in log:
   return 'XFAIL','win32_union_alignment'
 if pattern and re.search(pattern,log,re.S):return 'XFAIL',name
 return ('FAIL' if '--- FAIL:' in log else 'ERROR'),None

def run(cmd,env=None):
 p=subprocess.run(list(map(str,cmd)),cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 return p.returncode,p.stdout

def main():
 os.environ.setdefault('AUDIT_CXXFLAGS','-std=c++20')
 p=argparse.ArgumentParser();p.add_argument('--llgo',default='llgo');p.add_argument('--generator',default='bin/generate');p.add_argument('--target');p.add_argument('--bindings');p.add_argument('--out',default='results/llgo');p.add_argument('--case',action='append'); a=p.parse_args()
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
  if a.bindings:
   bindings=ROOT/a.bindings
   generation=json.loads((bindings/'generation.json').read_text())
   previous=next(r for r in generation['records'] if r['case']==name)
   rc=previous['generate_exit'];log=(bindings/(name+'-generate.log')).read_text()
   cmd=previous['command']
   if rc==0:shutil.copyfile(bindings/(name+'-generated.go.txt'),d/'generated.go')
  else:rc,log=run(cmd)
  (out/(name+'-generate.log')).write_text(log)
  generation_log=log
  record={'case':name,'generate_exit':rc,'generator_command':list(map(str,cmd))}
  if rc:record.update(status='XFAIL' if GEN_KNOWN.get(name) and GEN_KNOWN[name] in log else 'ERROR',reason='generation failed')
  else:
   shutil.copyfile(d/'generated.go',out/(name+'-generated.go.txt'))
   cmd=[a.llgo,'test','-count=1','-v','./'+str(d.relative_to(ROOT))]
   rc,log=run(cmd);(out/(name+'-test.log')).write_text(log)
   status,reason=classify(name,rc,log,generation_log,a.target)
   record.update(status=status,failure_kind=reason,test_exit=rc,test_command=cmd)
  records.append(record); print(name,record['status'],flush=True)
 version=run([a.llgo,'version'])[1].strip()
 result={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'host':platform.platform(),'llgo':version,'llgo_root':os.environ.get('LLGO_ROOT'),'target':a.target,'bindings':a.bindings,'pins':json.loads((ROOT/'pins.json').read_text()),'records':records}
 (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
 # XFAIL is preserved as a failed compatibility check, never reported as a pass.
 # The harness succeeds if all failures were classified; XPASS is visible and welcome.
 return int(any(r['status'] in ['ERROR','FAIL'] for r in records))
if __name__=='__main__':sys.exit(main())
