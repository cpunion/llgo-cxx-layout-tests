# Linux amd64 代码生成隔离

目录名保留最初从 packed 测试缩小的来源；`promoted*` 和 `direct_offset` **没有布局指令**。

- `promoted`：泛型嵌入结构，返回 size/align/offset。
- `promoted_fixed`：非泛型嵌入结构。
- `promoted_offset`：泛型嵌入结构，只返回 Offsetof。
- `direct_offset`：普通泛型字段 Offsetof 正向对照。
- `packed_arg`、`pack2_arg`、`native_func`：草案布局指令的独立对照。

固定 main 与布局草案都在前三个程序的 LLVM 代码生成阶段 SIGSEGV；直接字段返回 4。前三个程序的普通 Go 执行成功。草案另有 packed=5/1/1、pack2=6/2/2、native func=8 的成功运行。该结果不能归因于 packed，也不能归因于泛型独有逻辑；具体后端根因尚待定位。

```sh
python3 scripts/isolate_codegen.py --plain-only --llgo /path/to/main/llgo --out results/main-isolation
python3 scripts/isolate_codegen.py --llgo /path/to/proposal/llgo
```

为每次命令设置对应源码根目录 `LLGO_ROOT`。手动工作流固定两版编译器，逐项保留命令、退出码和日志。诊断脚本不会因为某一例崩溃提前结束，工作流绿色不表示所有例子通过；请读取 summary 中的 COMPILER_CRASH。

[已执行的对照 CI](https://github.com/cpunion/llgo-cxx-layout-tests/actions/runs/40816298326)。
