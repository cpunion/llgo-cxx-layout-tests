#!/usr/bin/env python3
"""Publish only sizes backed by passing runtime assertions and LLVM data."""
import hashlib
import json
import pathlib
import shutil
import zipfile

ROOT=pathlib.Path(__file__).resolve().parents[1]
results=ROOT/'results'
ci=results/'go-sizes-ci-final'
ir=results/'go-ir'
basics=[('bool',1),('int8',1),('uint8',1),('byte',1),('int16',2),('uint16',2),
        ('int32',4),('uint32',4),('rune',4),('int64',8),('uint64',8),
        ('int','word'),('uint','word'),('uintptr','word'),('float32',4),('float64',8),
        ('complex64',8),('complex128',16),('string','string')]
def load(p): return json.loads(p.read_text())
def value(n,w): return w if n=='word' else 2*w if n=='string' else n
data={}
for p in sorted(ci.rglob('summary.json')):
    name=str(p.parent.relative_to(ci)).removeprefix('go-sizes-').replace('wasm/','')
    data[name]={r['name']:r for r in load(p)}
    for compiler in ['gc','llgo']:
        for name2,_ in basics:
            assert 'TestGoTypeSizes/'+name2 in data[name][compiler]['passed'], (name,compiler,name2)
physical={p.stem:load(p) for p in ir.glob('*.json') if p.stem!='provenance'}
assert len(physical)==21 and all(x['pass'] for x in physical.values())
for item in physical.values():
    assert len(item['rows'])==19 and all(r['pass'] for r in item['rows'])
columns=[('386','windows-386',4),('amd64','linux-amd64',8),('arm64','linux-arm64',8),
         ('wasm32','wasm-j32',8),('wasm64','wasm-j64',8)]
lines=['19 项基本类型在全部已执行运行目标上通过，并与对应 LLVM 存储大小一致。下表单位为字节，LLGo 一列为 **LLVM 实测 / 独立预期**；普通 Go 列由对应运行断言验证。', '',
       '| 类型 | '+' | '.join(f'{a} Go | {a} LLGo 实/期' for a,_,_ in columns)+' |',
       '|---|'+'---:|'*10]
for name,n in basics:
    row=[name]
    for arch,target,w in columns:
        r=next(r for r in physical[target]['rows'] if r['type']==name)
        expected=value(n,w)
        assert r['alloc_bytes']==r['expected_bytes']==expected
        row += ['—' if arch=='wasm64' else str(expected),f'{r["alloc_bytes"]}/{expected}']
    lines += ['| '+' | '.join(row)+' |']
lines += ['', 'amd64、arm64 的运行结果覆盖 Linux/macOS/Windows；386 运行目标为 Windows MSVC。wasm32 覆盖 GoJS、Emscripten J32、WASI W32；wasm64 为 Emscripten J64。标准 Go 的 wasm64 格保留空缺，绝不使用 gc wasm32 控制冒充。', '',
          '| 实际运行组合 | Go 基本类型 | LLGo 基本类型 | Go 扩展全表 | LLGo 扩展全表 | 原有 unsafe 测试 |',
          '|---|---:|---:|---:|---:|---|']
for name,rows in data.items():
    counts={c:sum(x.startswith('TestGoTypeSizes/') for x in rows[c]['passed']) for c in ['gc','llgo']}
    gc='19/19' if name!='emscripten-memory64' else '无 wasm64；wasm32 控制 19/19'
    lines += [f'| {name} | {gc} | 19/19 | {counts["gc"]}/62'+('（wasm32 控制）' if name=='emscripten-memory64' else '')+f' | {counts["llgo"]}/62 | {rows["existing-unsafe"]["status"]} |']
lines += ['', '扩展用例中的失败不是基本类型失败。所有目标均复现普通函数类型 `reflect.Type.Size()` 只有 `unsafe.Sizeof` 的一半（386 为 4/8，其他为 8/16）；六个原生 64 位组合还复现末尾零大小字段的三个不一致用例。Windows 386 与四个 wasm profile 的末尾零大小字段用例均通过。', '',
          '### LLVM IR 结果', '',
          '| Go 类型 | LLVM 存储类型 | 字节数 |', '|---|---|---:|',
          '| bool | `i1`（分配不按 1 bit 紧密排列） | 1 |',
          '| int8 / uint8 / byte | `i8` | 1 |',
          '| int16 / uint16 | `i16` | 2 |',
          '| int32 / uint32 / rune | `i32` | 4 |',
          '| int64 / uint64 | `i64` | 8 |',
          '| int / uint / uintptr | 原生 32 位为 `i32`；原生 64 位与 hosted wasm 为 `i64` | 4 / 8 |',
          '| float32 | `float` | 4 |', '| float64 | `double` | 8 |',
          '| complex64 | `{float, float}` | 8 |', '| complex128 | `{double, double}` | 16 |',
          '| string，原生 32 位 | `{ptr, i32}` | 8 |',
          '| string，原生 64 位 / wasm64 | `{ptr, i64}` | 16 |',
          '| string，hosted wasm32 | `{{ptr, i32}, i64}` | 16 |', '',
          '实际使用的 named LLVM struct 名称在表中展开为字段形状；原始 `.ll` 全部保留。21 个 target 的 399 项 IR、allocation size、数组大小、原始 LLVM ABI alignment 和 string 长度字段偏移断言全部通过。', '',
          '额外仅做 IR 验证的目标：Linux 386、ARM32、RISC-V64、PPC64/PPC64LE、S390X、MIPS/MIPSLE/MIPS64/MIPS64LE、LoongArch64。不得把这些结果标为 Go/LLGo 原生执行通过。', '',
          '复现命令：', '', '```sh',
          'python3 scripts/go_sizes.py --llgo /path/to/llgo',
          'python3 scripts/go_sizes.py --llgo /path/to/llgo --profile emscripten-memory64',
          'python3 scripts/go_ir.py --llgo-root /path/to/pinned/llgo', '```']
report=ROOT/'reports/go-type-sizes.zh-CN.md'
text=report.read_text()
start='<!-- GENERATED_RESULTS -->'
end='<!-- END_GENERATED_RESULTS -->'
generated='\n'.join(lines)
if end in text:
    text=text[:text.index(start)+len(start)]+'\n\n'+generated+'\n\n'+text[text.index(end):]
else:
    text=text.replace(start,start+'\n\n'+generated+'\n\n'+end)
report.write_text(text)
(ROOT/'evidence/go-basic-sizes-table.md').write_text('\n'.join(lines[:24])+'\n')
paths=[]
for folder in ['go-sizes-ci-final','go-sizes-local','go-ir']:
    paths += [p for p in (results/folder).rglob('*') if p.suffix in {'.json','.log','.ll'}]
archive=ROOT/'evidence/go-sizes.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in sorted(paths): z.write(p,p.relative_to(results))
with zipfile.ZipFile(archive) as z: assert z.testzip() is None
(ROOT/'evidence/go-sizes-archive.json').write_text(json.dumps({archive.name:dict(
    sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),bytes=archive.stat().st_size,files=len(paths))},indent=2)+'\n')
print('runtime combinations:',len(data),'IR targets:',len(physical),'basic types:',len(basics),'archive files:',len(paths))
