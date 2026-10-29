#!/usr/bin/env python3
import argparse,json,pathlib,re,subprocess,sys
from reference import TARGETS
ROOT=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--clang',default='clang');p.add_argument('--out',default='results/extra');p.add_argument('--target',action='append');p.add_argument('--native',action='store_true');a=p.parse_args();out=ROOT/a.out;out.mkdir(parents=True,exist_ok=True);rows=[]
for source,standards,targets in [('empty.c',['gnu17','c17'],TARGETS),('version_packed.c',['gnu17','c++20'],['x86_64-w64-windows-gnu'])]:
 for target in a.target or targets:
  for std in standards:
   flags=['-std='+std]
   if std=='c17': flags+=['-pedantic-errors']
   key=source+'-'+target+'-'+std.replace('+','_');ir=out/(key+'.ll');cmd=[a.clang,'--target='+target,'-x','c++' if '++' in std else 'c',*flags,'-S','-emit-llvm',str(ROOT/'probes'/source),'-o',str(ir)]
   proc=subprocess.run(cmd,text=True,capture_output=True);log=proc.stdout+proc.stderr;(out/(key+'.log')).write_text(log)
   row={'source':source,'target':target,'standard':std,'exit':proc.returncode,'flags':flags,'command':cmd}
   if not proc.returncode:
    line=re.search(r'^@audit_\w+\s*=.*$',ir.read_text(),re.M).group();row['facts']=[int(x) for x in re.findall(r'i64 (-?\d+)',line)];row['status']='FAIL' if source=='empty.c' and std=='c17' else 'COMPILE_PASS'
    if a.native and source=='empty.c':
     exe=out/(key+('.exe' if sys.platform=='win32' else '.bin'))
     cmd=[a.clang,'--target='+target,'-x','c',*flags,'-DAUDIT_NATIVE',str(ROOT/'probes'/source),'-o',str(exe)]
     build=subprocess.run(cmd,text=True,capture_output=True);(out/(key+'-native-build.log')).write_text(build.stdout+build.stderr)
     row['native_build_exit']=build.returncode
     if build.returncode:row['status']='ERROR'
     else:
      result=subprocess.run([str(exe.resolve())],text=True,capture_output=True);(out/(key+'-native.log')).write_text(result.stdout+result.stderr)
      row['native_facts']=[int(n) for n in result.stdout.split()] if result.returncode==0 else []
      row['status']='NATIVE_PASS' if result.returncode==0 and row['native_facts']==row['facts'] else 'FAIL'
   elif std=='c17' and 'error: empty struct is a GNU extension' in log:row['status']='EXPECTED_EXTENSION_REJECTION'
   else:row.update(status='ERROR',diagnostic=log)
   rows.append(row)
(out/'summary.json').write_text(json.dumps({'compiler':subprocess.check_output([a.clang,'--version'],text=True),'records':rows},indent=2)+'\n')

raise SystemExit(int(any(r['status'] in ['ERROR','FAIL'] for r in rows)))
