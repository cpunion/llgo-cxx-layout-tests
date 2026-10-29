#!/usr/bin/env python3
"""Record final Clang layout/IR and optionally execute native C++ assertions."""
import argparse, json, pathlib, re, subprocess, sys, platform, datetime
from fact_names import NAMES
ROOT = pathlib.Path(__file__).resolve().parents[1]
TARGETS = ['x86_64-unknown-linux-gnu','aarch64-unknown-linux-gnu','i686-unknown-linux-gnu','armv7-unknown-linux-gnueabihf','x86_64-apple-darwin','arm64-apple-darwin','x86_64-pc-windows-msvc','i686-pc-windows-msvc','aarch64-pc-windows-msvc','x86_64-w64-windows-gnu','arm-none-eabi','riscv32-unknown-elf','riscv64-unknown-elf','wasm32-unknown-unknown','powerpc64-unknown-linux-gnu']
def run(cmd):
 p=subprocess.run(list(map(str,cmd)),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 return p.returncode,p.stdout

def main():
 p=argparse.ArgumentParser(); p.add_argument('--clang',default='clang++'); p.add_argument('--target',action='append'); p.add_argument('--std',action='append'); p.add_argument('--out',default='results/reference'); p.add_argument('--native',action='store_true'); p.add_argument('--flag',action='append',default=[])
 a=p.parse_args(); out=pathlib.Path(a.out); out.mkdir(parents=True,exist_ok=True)
 rc,version=run([a.clang,'--version'])
 if rc: raise SystemExit(version)
 records=[]
 for target in a.target or TARGETS:
  for std in a.std or ['c++17','c++20','c++23','c++2c']:
   key=re.sub(r'[^a-zA-Z0-9_.-]','_',target+'-'+std)
   ir=out/(key+'.ll'); flags=['--target='+target,'-std='+std,'-Wno-invalid-offsetof',*a.flag]
   cmd=[a.clang,*flags,'-S','-emit-llvm',ROOT/'probes/layout.cpp','-o',ir]
   rc,log=run(cmd); (out/(key+'.log')).write_text(log)
   entry={'target':target,'std':std,'flags':a.flag,'command':list(map(str,cmd)),'compile_exit':rc}
   if rc:
    entry['status']='ERROR'; entry['diagnostic']=log[-3000:]
   else:
    text=ir.read_text(); match=re.search(r'^@audit_facts\s*=.*$',text,re.M)
    values=[int(x) for x in re.findall(r'i64 (-?\d+)',match.group(0))] if match else []
    if len(values)!=len(NAMES): raise RuntimeError(f'{key}: {len(values)} facts, expected {len(NAMES)}')
    entry.update(status='COMPILE_PASS',facts=dict(zip(NAMES,values)),call_ir=re.findall(r'^define .*@call_.*$',text,re.M))
    if a.native:
     exe=out/(key+('.exe' if sys.platform=='win32' else '.bin'))
     cmd=[a.clang,*flags,'-DAUDIT_NATIVE',ROOT/'probes/layout.cpp','-o',exe]
     bc,bl=run(cmd); (out/(key+'-native-build.log')).write_text(bl)
     entry['native_build_exit']=bc
     if bc: entry.update(status='ERROR',native_diagnostic=bl[-3000:])
     else:
      ec,el=run([exe.resolve()]); (out/(key+'-native.log')).write_text(el); entry['native_exit']=ec
      if ec: entry.update(status='FAIL',native_diagnostic=el[-3000:])
      else:
       actual=json.loads(el); entry['native']=actual
       entry['status']='NATIVE_PASS' if actual['facts']==values else 'FAIL'
   print(target,std,entry['status'],flush=True); records.append(entry)
 data={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'host':platform.platform(),'compiler':version.strip(),'records':records}
 (out/'summary.json').write_text(json.dumps(data,indent=2)+'\n')
 return int(any(r['status'] in ['ERROR','FAIL'] for r in records))
if __name__=='__main__': sys.exit(main())
