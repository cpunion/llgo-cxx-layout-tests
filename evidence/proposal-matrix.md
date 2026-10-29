# 布局草案与 SSA 原生矩阵

| 平台 | gc | layout-runtime | padding | pr761 | ssa-patched-gc | ssa-patched-llgo |
|---|---|---|---|---|---|---|
| darwin-amd64 | PASS | ERROR | XFAIL | XFAIL | PASS | PASS |
| darwin-arm64 | PASS | PASS | XFAIL | XFAIL | PASS | PASS |
| linux-amd64 | PASS | ERROR | XFAIL | XFAIL | PASS | PASS |
| linux-arm64 | PASS | PASS | XFAIL | XFAIL | PASS | PASS |
| windows-386 | PASS | PASS | XFAIL | 不适用 | PASS | PASS |
| windows-amd64 | PASS | PASS | XFAIL | 不适用 | PASS | PASS |
| windows-arm64 | PASS | PASS | XFAIL | 不适用 | PASS | PASS |

Linux/macOS amd64 的 layout-runtime ERROR 是 LLVM 代码生成期间的 SIGSEGV；它们没有执行到断言，不能标为布局验证通过。原始日志在 proposal-ssa.zip 中。
