#!/usr/bin/env python3
import argparse, json, pathlib, re, subprocess, sys
from fact_names import NAMES
ROOT=pathlib.Path(__file__).resolve().parents[1]
def run(cmd):
 try:
  p=subprocess.run(list(map(str,cmd)),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=25)
  return p.returncode,p.stdout
 except subprocess.TimeoutExpired as e:return 124,str(e)
def main():
 p=argparse.ArgumentParser();p.add_argument('--clang',default='clang++');p.add_argument('--out',default='results/embedded');p.add_argument('--case',action='append');a=p.parse_args()
 out=ROOT/a.out;out.mkdir(parents=True,exist_ok=True);recs=[]
 common=['-std=c++20','-O1','-ffreestanding','-fno-exceptions','-fno-rtti','-fno-stack-protector','-Wno-invalid-offsetof','-ffunction-sections','-fdata-sections']
 cases={
 'cortex-m3':(['--target=arm-none-eabi','-mcpu=cortex-m3','-mthumb'],['-Wl,-T,'+str(ROOT/'probes/embedded/arm.ld'),ROOT/'probes/embedded/arm.S'],['qemu-system-arm','-M','mps2-an385','-nographic','-semihosting-config','enable=on,target=native','-kernel']),
 'riscv32':(['--target=riscv32-unknown-elf','-march=rv32imac','-mabi=ilp32','-mcmodel=medany','-msmall-data-limit=0'],['-Wl,-T,'+str(ROOT/'probes/embedded/riscv.ld'),ROOT/'probes/embedded/riscv.S'],['qemu-system-riscv32','-M','virt','-bios','none','-nographic','-semihosting-config','enable=on,target=native','-kernel']),
 'wasm32':(['--target=wasm32-wasip1'],['-Wl,--entry=_start','-Wl,--export-memory'],['wasmtime','run'])}
 for name,(flags,link,execute) in cases.items():
  if a.case and name not in a.case:continue
  ir=out/(name+'.ll');exe=out/(name+('.wasm' if name=='wasm32' else '.elf'))
  rc,log=run([a.clang,*flags,*common,'-S','-emit-llvm',ROOT/'probes/layout.cpp','-o',ir]);(out/(name+'-ir.log')).write_text(log)
  rec={'case':name,'flags':flags,'status':'ERROR','emulator':run([execute[0],'--version'])[1].strip()}
  if rc==0:
   values=[int(x) for x in re.findall(r'i64 (-?\d+)',re.search(r'^@audit_facts\s*=.*$',ir.read_text(),re.M).group())]
   assert len(values)==len(NAMES)
   cmd=[a.clang,*flags,*common,'-fuse-ld=lld','-nostdlib','-Wl,--gc-sections',*link,ROOT/'probes/embedded/runtime.cpp','-o',exe]
   rc,log=run(cmd);(out/(name+'-build.log')).write_text(log);rec['build_command']=list(map(str,cmd));rec['build_exit']=rc
   if rc==0:
    rc,log=run([*execute,exe]);(out/(name+'-run.log')).write_text(log);rec['run_command']=[*execute,str(exe)];rec['run_exit']=rc
    if rc==0:
     actual=json.loads(log);rec.update(status='EMULATED_PASS' if actual['facts']==values else 'FAIL',facts=dict(zip(NAMES,values)),dynamic=actual['dynamic'])
  print(name,rec['status'],flush=True);recs.append(rec)
 (out/'summary.json').write_text(json.dumps({'compiler':run([a.clang,'--version'])[1],'records':recs},indent=2)+'\n')
 return int(any(r['status']!='EMULATED_PASS' for r in recs))
if __name__=='__main__':sys.exit(main())
