#!/usr/bin/env python3
"""Generate target-specific bindings on a supported llcppg host for native target tests."""
import argparse,json,pathlib,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--target',required=True);p.add_argument('--generator',default='bin/generate');p.add_argument('--out',required=True);a=p.parse_args();out=ROOT/a.out;out.mkdir(parents=True,exist_ok=True);records=[]
for case in sorted((ROOT/'cases').iterdir()):
 lang=(case/'language').read_text().strip();cmd=[str(ROOT/a.generator),'-target',a.target,'-header',str(case/'input.h'),'-output',str(out/(case.name+'-generated.go.txt')),'-language',lang]
 if lang=='c++':cmd+=['-std','c++20']
 r=subprocess.run(cmd,capture_output=True,text=True);(out/(case.name+'-generate.log')).write_text(r.stdout+r.stderr);records.append({'case':case.name,'generate_exit':r.returncode,'command':cmd})
(out/'generation.json').write_text(json.dumps({'target':a.target,'pins':json.loads((ROOT/'pins.json').read_text()),'records':records},indent=2)+'\n')
