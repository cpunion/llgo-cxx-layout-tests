#!/usr/bin/env python3
"""macOS libclang compatibility experiment; keeps LLGo backend and generator source fixed."""
import argparse,hashlib,json,os,pathlib,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--lib',action='append',required=True,help='label=/absolute/lib/directory');p.add_argument('--generator',default='bin/generate');p.add_argument('--out',default='results/libclang-versions');a=p.parse_args();out=ROOT/a.out;out.mkdir(parents=True,exist_ok=True);rows=[]
 for item in a.lib:
  label,directory=item.split('=',1);env=os.environ.copy();env['DYLD_LIBRARY_PATH']=directory
  for case in sorted((ROOT/'cases').iterdir()):
   dest=out/label/case.name;dest.mkdir(parents=True,exist_ok=True);lang=(case/'language').read_text().strip()
   cmd=[str(ROOT/a.generator),'-header',str(case/'input.h'),'-output',str(dest/'generated.go'),'-language',lang]
   if lang=='c++':cmd+=['-std','c++20']
   proc=subprocess.run(cmd,env=env,text=True,capture_output=True);log=proc.stdout+proc.stderr;(dest/'generate.log').write_text(log)
   source=dest/'generated.go';row={'library_label':label,'library_directory':directory,'case':case.name,'exit':proc.returncode,'libclang':log.splitlines()[0] if log else '', 'sha256':hashlib.sha256(source.read_bytes()).hexdigest() if source.exists() else None};rows.append(row)
  print(label,'done',flush=True)
 (out/'summary.json').write_text(json.dumps(rows,indent=2)+'\n')
if __name__=='__main__':main()
