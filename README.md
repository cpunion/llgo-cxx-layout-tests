# LLGo / C / C++ layout compatibility audit

公开研究仓库，包含原生参考代码、真实 llcppg 生成、LLGo 失败断言、跨平台/编译器版本矩阵与中文调研报告。

- **[完整调研报告](reports/layout-audit.zh-CN.md)**：提案/实现不准确部分、不完整部分、建议；较新语言规范放在最后。
- **[Go 基本类型 size 与 LLVM IR 验证](reports/go-type-sizes.zh-CN.md)**：19 项基本类型、原生/wasm 运行矩阵、21 个 target 的 LLVM 类型和实际分配大小，以及反射/零大小尾字段的不一致。
- **[证据索引与覆盖矩阵](evidence/README.md)**：区分原生执行、模拟器执行、仅交叉编译和未覆盖项。
- 修复跟踪：[LLGo #2943](https://github.com/xgo-dev/llgo/issues/2943)、[llcppg #1123](https://github.com/goplus/llcppg/issues/1123)。
- [固定版本](pins.json)、[当前生成器探针](cases)、[padding/pack 与 PR #761 探针](proposals)、[SSA 实验](experiments/ssa)。

C++ 参考测试通过不表示 Go 绑定兼容。`XFAIL` 表示实际失败，`XPASS` 表示该平台上未复现既知问题，`ERROR` 表示测试没有完成。CI 绿色意味着参考检查通过且兼容性失败已分类，**不代表所有兼容性测试通过**。

## 原生 C++、跨目标及版本验证

需要 Python 3 和 Clang。交叉布局检查不需要目标 SDK，原生执行需要对应平台开发工具链。

```sh
# 15 个目标 × C++17/20/23/2c；保留 LLVM IR、诊断和 JSON。
python3 scripts/reference.py --clang clang++ --out results/reference
# 必须指定可以在当前主机实际执行的目标。
python3 scripts/reference.py --clang clang++ --target x86_64-unknown-linux-gnu --native
# GNU C 空结构、严格 C17 拒绝、跨版本 packed 最小例。
python3 scripts/extra_compiler_probes.py --clang clang
# 版本可重复以上命令；不要把 Apple Clang 与同主版本 upstream Clang混为一谈。
```

## llcppg 生成与 LLGo 测试

使用 [pins.json](pins.json) 对应 LLGo，并将 `LLGO_ROOT` 指向其源码根目录。依赖包括 LLVM/Clang 22、BDW GC、libffi；安装方式遵循 LLGo/llcppg 的安装说明。不要用普通 `go build` 构建 libclang 绑定生成器。

```sh
llgo build -o bin/generate ./cmd/generate
python3 scripts/llgo_cases.py --llgo llgo --generator bin/generate --out results/llgo
# 只复现一个问题；生成的源码和 *_test.go 在 .work/llgo/union_hfa。
python3 scripts/llgo_cases.py --case union_hfa
# 直接运行失败断言时，命令本身应返回非零。
llgo test -v ./.work/llgo/union_hfa
```

运行器设置 `AUDIT_CXXFLAGS=-std=c++20`，并保存每个用例的生成日志、生成源码、测试日志、退出码和分类。`cases/*/generated.snapshot.txt` 是最初 macOS arm64 生成结果，仅供对照；运行器默认每次重新生成，不能拿快照当作跨平台绑定。

Windows 当前生成器缺少 `clang.Mangling`，因此 CI 在 Linux 用目标 triple 生成绑定，然后在对应 Windows 目标执行：

```sh
# 在支持的生成器主机上执行；target 配置进入 libclang。
python3 scripts/generate_cases.py --target x86_64-pc-windows-msvc --out results/windows-bindings
# 将生成目录连同 generation.json 搬到 Windows，并配置对应的 LLGo target。
python3 scripts/llgo_cases.py --target x86_64-pc-windows-msvc --bindings results/windows-bindings
```

## 布局草案、普通 Go 和 SSA

```sh
go test -v ./proposals/padding ./proposals/layout_runtime
# 以下需使用 pins.json 中 layout_pr 对应的 LLGo，设置其 LLGO_ROOT：
AUDIT_CXXFLAGS=-std=c++20 llgo test -v ./proposals/padding       # 预期 C++ 映射断言失败
llgo test -v ./proposals/layout_runtime                       # 静态/泛型/反射一致性；平台结果见报告，Linux amd64 有编译崩溃
# PR #761 快照绑定只用于 Itanium 目标：
AUDIT_CXXFLAGS=-std=c++20 llgo test -v ./proposals/pr761        # 预期失败
cd experiments/ssa
go run . -sizes gc
go run . -sizes custom
# 使用 patched go/types 的 LLGo：
llgo run . -sizes llgo
llgo run . -sizes gc    # 在该 patch 内两者均采用 LLGo 语义
```

## 嵌入与 wasm

```sh
# 需要 Clang/LLD、qemu-system-arm、qemu-system-riscv32、wasmtime。
python3 scripts/embedded.py --clang clang++
# Espressif Clang 可做 Xtensa 布局交叉编译；不冒充 ESP32 实机执行。
python3 scripts/reference.py --clang /path/to/esp-clang/bin/clang++ \
  --target xtensa-esp32-elf --std c++20 --out results/xtensa
```

QEMU 使用 Cortex-M3 `mps2-an385` 和 RV32 `virt`；wasm32 通过 WASI 在 Wasmtime 执行。源码不依赖目标标准库。工具链、原生 SDK 和 ABI 是实验条件的一部分，详细限制见报告。

## 仓库约定

`probes/` 是原生 oracle；`cases/` 是生成器输入与 Go 断言；`proposals/` 单独保存未合并提案实验；`results/`、`.work/`、`bin/` 是忽略的本地输出；`evidence/` 保存此次审计的压缩原始证据与可读摘要。不要手改生成快照来让测试通过，也不要把预期失败改成普通 PASS。

## 修复归属对照

`python3 scripts/ownership_controls.py --llgo /path/to/llgo` 在 macOS arm64 上修改两份生成快照，隔离生成表示与编译器问题。它不会修改生成器：callback 仅补 cdecl，union 改用保留浮点分类的 carrier。设置对应 `LLGO_ROOT`；main 的 callback 查询/反射断言仍失败，布局草案通过。日志在 `evidence/llgo.zip` 的 ownership / ownership-proposal 目录；这些控制不能当作已修复的生成器或跨平台结论。
