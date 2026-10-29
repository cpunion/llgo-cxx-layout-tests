# 布局草案与 SSA 原生矩阵

同名 artifact 按创建时间选择最新结果；首次崩溃也保留于归档。SSA 实验在各宿主上显式选择 amd64 Sizes；运行时测试使用实际目标。

| 平台 | gc | layout-runtime | padding | pr761 | ssa-patched-gc | ssa-patched-llgo |
|---|---|---|---|---|---|---|
| darwin-amd64 | PASS | PASS | XFAIL | XFAIL | PASS | PASS |
| darwin-arm64 | PASS | PASS | XFAIL | XFAIL | PASS | PASS |
| linux-amd64 | PASS | ERROR | XFAIL | XFAIL | PASS | PASS |
| linux-arm64 | PASS | PASS | XFAIL | XFAIL | PASS | PASS |
| windows-386 | PASS | PASS | XFAIL | 不适用 | PASS | PASS |
| windows-amd64 | PASS | PASS | XFAIL | 不适用 | PASS | PASS |
| windows-arm64 | PASS | PASS | XFAIL | 不适用 | PASS | PASS |

Linux amd64 的 layout-runtime 在首次、复跑和 -p=1 串行运行中均于 LLVM 代码生成期间 SIGSEGV；未执行到断言。macOS amd64 首次同样崩溃，复跑 PASS，不能将首次失败删除或认定已修复。原始日志在 proposal-ssa.zip 中。
