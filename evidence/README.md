# 2026-10-29 审计证据

源代码和精确项目版本见 [pins.json](../pins.json)。每份 JSON 包含实际命令、编译器完整版本、目标与退出状态；生成器日志记录真正加载的 libclang。

| 证据 | 内容 |
|---|---|
| [原生 C++ 运行表](native-reference.md) | Windows/macOS/Linux 八个目标组合；upstream Clang 18～23 在 Linux 的独立执行 |
| [草案/SSA 矩阵](proposal-matrix.md) | 七个平台的 patched go/types、泛型布局与编译器崩溃记录 |
| [LLGo 逐用例矩阵](llgo-matrix.md) | 各原生平台的 PASS/XFAIL/XPASS/ERROR，不能仅以 CI 绿色判断兼容 |
| [local-reference.zip](local-reference.zip) | 本地 Clang 18～23、Apple Clang 的 420 条 cross 配置；最终 IR、诊断、版本兼容选项实验；C 扩展/严格模式、Cortex-M3/RV32/wasm32 执行、Xtensa 交叉编译 |
| [ci-reference.zip](ci-reference.zip) | GitHub Actions 原生/版本/目标参考程序的原始结果 |
| [llgo.zip](llgo.zip) | 本地与 CI 的实际生成源码、测试日志、逐用例退出码；Linux 生成 Windows-target 绑定的 provenance；ownership/ownership-proposal 为手动表示对照及原始非零退出码 |
| [libclang.zip](libclang.zip) | 固定生成器加载不同 libclang：18～20 的缺符号启动失败；21～23 的输出哈希与日志 |
| [proposal-ssa.zip](proposal-ssa.zip) | padding 草案失败断言、PR #761 的原生对比、gc/自定义/patch 三种 SSA 输出、运行时泛型一致性以及 main/草案编译崩溃对照 |
| [archives.json](archives.json) | 每个压缩包的 SHA-256、文件数与字节数 |

执行来源：

- [原生 C++ 和编译器版本矩阵](https://github.com/cpunion/llgo-cxx-layout-tests/actions/runs/40815588967)：保存的 C/C++ 与嵌入参考运行，8 个 native target 组合与 6 个 compiler version lane。
- [LLGo 原生兼容探针](https://github.com/cpunion/llgo-cxx-layout-tests/actions/runs/40812047905)：20 个用例；Windows 使用明确的 target-specific cross-generation 路径。
- [布局草案与 SSA 运行](https://github.com/cpunion/llgo-cxx-layout-tests/actions/runs/40812590996)：Linux amd64 复跑仍崩溃；macOS amd64 首次崩溃、复跑通过，全部记录保留。
- [代码生成隔离实验](https://github.com/cpunion/llgo-cxx-layout-tests/actions/runs/40815304481)：串行运行及普通泛型嵌入字段程序可复现 Linux amd64 崩溃。
- [main / 布局草案对照](https://github.com/cpunion/llgo-cxx-layout-tests/actions/runs/40816298326)：无布局指令、非泛型示例也复现，排除“patch 新增回归”的归因。
- [原始 Windows 生成器构建失败](https://github.com/cpunion/llgo-cxx-layout-tests/actions/runs/40807924588/job/123231183216)：缺少 `clang.Mangling`，不是内存布局断言失败。

本地嵌入执行使用 QEMU 11.1.1 / Wasmtime 48.0.1；没有 ESP32 实机执行证据。CI 和本地版本可能不同，以各 summary 的完整字符串为准。

压缩包只包含文本证据，不包括编译出来的可执行文件。源码发生变化后重新运行测试，并执行 `python3 scripts/archive_evidence.py` 更新归档；不要只更新表格中的状态。

同一次 workflow 的复跑可能留下多个同名 artifact。`scripts/download_evidence.py` 按 `created_at` 选择最新项，保存 run/head SHA/artifact ID；不能按 ID 大小或列表顺序推断新旧。
