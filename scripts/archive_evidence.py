#!/usr/bin/env python3
"""Bundle the selected audit outputs; excludes binaries and records content hashes."""
import collections,hashlib,json,pathlib,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1];RESULTS=ROOT/'results';OUT=ROOT/'evidence';OUT.mkdir(exist_ok=True)
groups={
 'local-reference': ['clang18','clang19','clang20','clang21','clang22','clang23','clangapple21','clang23-compat22','local-native','embedded','xtensa-esp32','c-native',*['extra'+str(v) for v in range(18,24)]],
 'ci-reference':['ci-reference-verified'],
 'llgo':['llgo-final','ci-llgo-verified'],
 'libclang':['libclang-versions','cross-mangling'],
 'proposal-ssa':['ci-proposals','ci-proposals-first','proposals-local','padding-gc.log','padding-final.log','pr761-layout.log','ssa-custom.log','ssa-gc.log','ssa-patched-llgo.log','ssa-patched-gc.log','ssa-layout-final.log','ssa-layout-gc.log'],
}
index={}
for name,items in groups.items():
 files=[]
 for item in items:
  p=RESULTS/item
  if not p.exists():raise SystemExit('Missing evidence: '+str(p))
  files.extend([p] if p.is_file() else [x for x in p.rglob('*') if x.is_file() and (x.suffix in ['.json','.ll','.log','.go'] or x.name.endswith('.go.txt'))])
 dest=OUT/(name+'.zip')
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for f in sorted(files):z.write(f,f.relative_to(RESULTS))
 index[dest.name]={'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'files':len(files),'bytes':dest.stat().st_size}
(OUT/'archives.json').write_text(json.dumps(index,indent=2)+'\n')
# A readable per-case matrix. Raw logs and full generated source remain in the archive.
data={}
for p in (RESULTS/'ci-llgo-verified').rglob('summary.json'):
 obj=json.loads(p.read_text());data[obj['target']]=obj
lines=['# LLGo 原生运行矩阵','', '固定 main 版本，每个平台重新生成或使用注明目标的 Linux 交叉生成结果。XFAIL 是实际失败；不是 PASS。','']
platforms=sorted(data)
lines+=['| case | '+' | '.join(platforms)+' |','|---|'+'---|'*len(platforms)]
for case in sorted({r['case'] for obj in data.values() for r in obj['records']}):
 row=[next((r['status'] for r in data[t]['records'] if r['case']==case),'未执行') for t in platforms]
 lines+=['| '+case+' | '+' | '.join(row)+' |']
(OUT/'llgo-matrix.md').write_text('\n'.join(lines)+'\n')
lines=['# 原生 C++ 参考运行','', '| 目标 | 编译器 | 语言模式 | 状态 |','|---|---|---|---|']
for p in sorted((RESULTS/'ci-reference-verified').rglob('summary.json')):
 obj=json.loads(p.read_text())
 for r in obj['records']:
  if 'native' in r:lines+=['| '+r['target']+' | '+obj['compiler'].splitlines()[0]+' | '+r['std']+' | '+r['status']+' |']
(OUT/'native-reference.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(index,indent=2))

# Keep proposal compiler failures visible independently of binding failures.
lines=['# 布局草案与 SSA 原生矩阵','', '| 平台 | '+ ' | '.join(['gc','layout-runtime','padding','pr761','ssa-patched-gc','ssa-patched-llgo'])+' |','|---|---|---|---|---|---|---|']
for p in sorted((RESULTS/'ci-proposals-first').rglob('summary.json')):
 obj=json.loads(p.read_text()); name=p.parent.parent.name.removeprefix('proposals-')
 row=[next((r['status'] for r in obj['records'] if r['case']==c),'不适用') for c in ['gc','layout-runtime','padding','pr761','ssa-patched-gc','ssa-patched-llgo']]
 lines+=['| '+name+' | '+' | '.join(row)+' |']
lines+=['','Linux/macOS amd64 的 layout-runtime ERROR 是 LLVM 代码生成期间的 SIGSEGV；它们没有执行到断言，不能标为布局验证通过。原始日志在 proposal-ssa.zip 中。']
(OUT/'proposal-matrix.md').write_text('\n'.join(lines)+'\n')
