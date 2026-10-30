# Go 基本类型大小与跨架构测试覆盖盘点

本轮首先检查 Go 的 17 个基本类型，加上 `byte`、`rune` 两个别名，共 19 项。
`unsafe.Pointer`、指针、接口、函数、数组和结构体放在扩展结果中；不将 gc 与 LLGo 的函数值表示差异判作错误。
这里的大小是当前编译器的数据布局，不是声称 Go 语言规范固定了所有类型的字节数。

## 固定版本和方法

- LLGo main：`b2e1d4e84fcccdc893b77a652c2f5c9b2fc65836`（本轮开始时远端 main）。
- CI：Go `1.27.0`、LLVM `22`；本地补充运行使用 Go `1.27.3`。
- [CI 运行](https://github.com/cpunion/llgo-cxx-layout-tests/actions/runs/40981385469)。该工作流记录失败为数据；工作流绿色不等于断言全部通过。
- [同一份测试](../experiments/go_sizes/sizes_test.go)，每个用例同时检查具体类型的常量 `unsafe.Sizeof`、泛型 `Sizeof`、两元素数组大小、实际元素地址差、`reflect.Type.Size()`。
- 大小预期由目标架构的独立表给出，不从被测 `unsafe.Sizeof` 推导。普通 Go 函数值单独采用 gc 一个字、LLGo 两个字的预期。
- 共 62 个类型/组合用例。类型类别覆盖不等于穷尽所有递归、嵌套、泛型实例及编译选项组合。
- **`unsafe.Sizeof` 只是被测路径，不是布局的真值来源。** 另用 [SSA 后端测试](../experiments/go_ir/size_ir_test.go.txt) 取得 LLGo 实际生成的全局变量 LLVM 类型，调用 LLVM TargetData 读取 allocation/store size、ABI alignment、结构字段偏移，验证两元素数组的物理大小；不调用 `Program.SizeOf` 或 `types.Sizes.Sizeof` 来判断通过。
- IR 层共 21 个 target × 19 项 = 399 项。它使用当前 LLGo SSA 后端和实际 runtime String 声明，保存完整 `.ll` 与 TargetData JSON；不代表额外 target 已完成全链路编译或目标机器执行。原始 LLVM scalar ABI alignment 也不能替代 Go 的字段对齐规则。

## 仓库原有覆盖

| 位置 | 实际覆盖 | 缺口 |
|---|---|---|
| [`test/std/unsafe/unsafe_test.go`](https://github.com/xgo-dev/llgo/blob/b2e1d4e84fcccdc893b77a652c2f5c9b2fc65836/test/std/unsafe/unsafe_test.go) | `int`、`byte`、`string`、`[10]int`，少量对齐/偏移 | `int` 同时接受 4 或 8；`string` 同时接受 8 或 16，不能检出目标选错。未逐项覆盖所有基本类型 |
| [`test/std/go/types/sizes_test.go`](https://github.com/xgo-dev/llgo/blob/b2e1d4e84fcccdc893b77a652c2f5c9b2fc65836/test/std/go/types/sizes_test.go) | 固定 `SizesFor("gc", "arm64")` 的 int、指针和一个结构体 | 这是 sizes 模型测试，不是各目标编译后的存储验证 |
| [`ssa/wasm_storage_test.go`](https://github.com/xgo-dev/llgo/blob/b2e1d4e84fcccdc893b77a652c2f5c9b2fc65836/ssa/wasm_storage_test.go) | wasm32 Go64 存储、物理指针、原生边界、数组/结构体等 | 有针对性的 LLVM/SSA 测试，不是全部基本类型的 gc/LLGo 运行矩阵 |
| [`internal/build/testdata/wasm-profile`](https://github.com/xgo-dev/llgo/tree/b2e1d4e84fcccdc893b77a652c2f5c9b2fc65836/internal/build/testdata/wasm-profile) | 实际运行 Go uintptr/指针、指针字段、C pointer/long、边界收窄 | 有精确目标预期，但基本类型列表不完整 |
| [`ssa/abitype_layout_test.go`](https://github.com/xgo-dev/llgo/blob/b2e1d4e84fcccdc893b77a652c2f5c9b2fc65836/ssa/abitype_layout_test.go) | Windows 386 Go/C 结构体、末尾零大小字段等 | 局部布局回归测试，不是所有架构和类型 |
| `ssa/vector_layout_test.go`、`ssa/simd_test.go`、`test/simd` | SIMD、原生函数字段、容器和部分反射；含 amd64/arm64/wasm | 专项测试，不替代基本类型全表 |
| `cl/_testrt/unsafe`、`cl/_testrt/tpunsafe` | 原生/Go 函数、泛型结构体、Sizeof/Alignof/Offsetof 的 LLVM 检查 | 专项编译测试；没有覆盖所有基本类型及所有目标 |
| [`runtime/internal/test/typesize_test.go`](https://github.com/xgo-dev/llgo/blob/b2e1d4e84fcccdc893b77a652c2f5c9b2fc65836/runtime/internal/test/typesize_test.go) | C/POSIX 的 pthread、setjmp、OS 类型，Linux/macOS amd64/arm64 | 不属于 Go 基本类型全表，其他平台直接报 unsupported；runtime 是独立 module |

结论：原有测试包含不少布局回归用例，但没有发现“所有基本类型 × 目标架构 × 常量/泛型/物理存储/反射”的统一精确断言。现有 `test/std/unsafe` 通过也不足以证明所有 size 路径一致。

**CI 入口还有额外缺口**：`llgo.yml` 通过 `LLGO_TEST_SUITE=core` 调用 `dev/test_go_version.sh`，后者白名单排除了 `test/std/unsafe`、`test/std/go/types`。宿主 `go.yml` 的 `go test` 会跑这些包，但那是在测试 gc。wasm CI 有专门 profile/SSA/SIMD 检查，也未发现把全部基本类型的上述测试逐项运行的入口。本轮才在审计工作流中显式执行了旧 unsafe 测试和新的完整矩阵。

要形成 LLGo 持续保障，应将共享的基本类型断言加入 `test/go`，将 IR 映射测试加入 `ssa`，再让原生 CI 与 wasm profile CI 明确执行它们；本研究仓库尚未向 LLGo 提交该集成。

## 结果表

<!-- GENERATED_RESULTS -->

19 项基本类型在全部已执行运行目标上通过，并与对应 LLVM 存储大小一致。下表单位为字节，LLGo 一列为 **LLVM 实测 / 独立预期**；普通 Go 列由对应运行断言验证。

| 类型 | 386 Go | 386 LLGo 实/期 | amd64 Go | amd64 LLGo 实/期 | arm64 Go | arm64 LLGo 实/期 | wasm32 Go | wasm32 LLGo 实/期 | wasm64 Go | wasm64 LLGo 实/期 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| bool | 1 | 1/1 | 1 | 1/1 | 1 | 1/1 | 1 | 1/1 | — | 1/1 |
| int8 | 1 | 1/1 | 1 | 1/1 | 1 | 1/1 | 1 | 1/1 | — | 1/1 |
| uint8 | 1 | 1/1 | 1 | 1/1 | 1 | 1/1 | 1 | 1/1 | — | 1/1 |
| byte | 1 | 1/1 | 1 | 1/1 | 1 | 1/1 | 1 | 1/1 | — | 1/1 |
| int16 | 2 | 2/2 | 2 | 2/2 | 2 | 2/2 | 2 | 2/2 | — | 2/2 |
| uint16 | 2 | 2/2 | 2 | 2/2 | 2 | 2/2 | 2 | 2/2 | — | 2/2 |
| int32 | 4 | 4/4 | 4 | 4/4 | 4 | 4/4 | 4 | 4/4 | — | 4/4 |
| uint32 | 4 | 4/4 | 4 | 4/4 | 4 | 4/4 | 4 | 4/4 | — | 4/4 |
| rune | 4 | 4/4 | 4 | 4/4 | 4 | 4/4 | 4 | 4/4 | — | 4/4 |
| int64 | 8 | 8/8 | 8 | 8/8 | 8 | 8/8 | 8 | 8/8 | — | 8/8 |
| uint64 | 8 | 8/8 | 8 | 8/8 | 8 | 8/8 | 8 | 8/8 | — | 8/8 |
| int | 4 | 4/4 | 8 | 8/8 | 8 | 8/8 | 8 | 8/8 | — | 8/8 |
| uint | 4 | 4/4 | 8 | 8/8 | 8 | 8/8 | 8 | 8/8 | — | 8/8 |
| uintptr | 4 | 4/4 | 8 | 8/8 | 8 | 8/8 | 8 | 8/8 | — | 8/8 |
| float32 | 4 | 4/4 | 4 | 4/4 | 4 | 4/4 | 4 | 4/4 | — | 4/4 |
| float64 | 8 | 8/8 | 8 | 8/8 | 8 | 8/8 | 8 | 8/8 | — | 8/8 |
| complex64 | 8 | 8/8 | 8 | 8/8 | 8 | 8/8 | 8 | 8/8 | — | 8/8 |
| complex128 | 16 | 16/16 | 16 | 16/16 | 16 | 16/16 | 16 | 16/16 | — | 16/16 |
| string | 8 | 8/8 | 16 | 16/16 | 16 | 16/16 | 16 | 16/16 | — | 16/16 |

amd64、arm64 的运行结果覆盖 Linux/macOS/Windows；386 运行目标为 Windows MSVC。wasm32 覆盖 GoJS、Emscripten J32、WASI W32；wasm64 为 Emscripten J64。标准 Go 的 wasm64 格保留空缺，绝不使用 gc wasm32 控制冒充。

| 实际运行组合 | Go 基本类型 | LLGo 基本类型 | Go 扩展全表 | LLGo 扩展全表 | 原有 unsafe 测试 |
|---|---:|---:|---:|---:|---|
| darwin-amd64 | 19/19 | 19/19 | 62/62 | 56/62 | PASS |
| darwin-arm64 | 19/19 | 19/19 | 62/62 | 56/62 | PASS |
| linux-amd64 | 19/19 | 19/19 | 62/62 | 56/62 | PASS |
| linux-arm64 | 19/19 | 19/19 | 62/62 | 56/62 | PASS |
| emscripten | 19/19 | 19/19 | 62/62 | 59/62 | PASS |
| emscripten-memory64 | 无 wasm64；wasm32 控制 19/19 | 19/19 | 62/62（wasm32 控制） | 59/62 | PASS |
| gojs | 19/19 | 19/19 | 62/62 | 59/62 | PASS |
| wasi | 19/19 | 19/19 | 62/62 | 59/62 | PASS |
| windows-386 | 19/19 | 19/19 | 62/62 | 59/62 | PASS |
| windows-amd64 | 19/19 | 19/19 | 62/62 | 56/62 | PASS |
| windows-arm64 | 19/19 | 19/19 | 62/62 | 56/62 | PASS |

扩展用例中的失败不是基本类型失败。所有目标均复现普通函数类型 `reflect.Type.Size()` 只有 `unsafe.Sizeof` 的一半（386 为 4/8，其他为 8/16）；六个原生 64 位组合还复现末尾零大小字段的三个不一致用例。Windows 386 与四个 wasm profile 的末尾零大小字段用例均通过。

### LLVM IR 结果

| Go 类型 | LLVM 存储类型 | 字节数 |
|---|---|---:|
| bool | `i1`（分配不按 1 bit 紧密排列） | 1 |
| int8 / uint8 / byte | `i8` | 1 |
| int16 / uint16 | `i16` | 2 |
| int32 / uint32 / rune | `i32` | 4 |
| int64 / uint64 | `i64` | 8 |
| int / uint / uintptr | 原生 32 位为 `i32`；原生 64 位与 hosted wasm 为 `i64` | 4 / 8 |
| float32 | `float` | 4 |
| float64 | `double` | 8 |
| complex64 | `{float, float}` | 8 |
| complex128 | `{double, double}` | 16 |
| string，原生 32 位 | `{ptr, i32}` | 8 |
| string，原生 64 位 / wasm64 | `{ptr, i64}` | 16 |
| string，hosted wasm32 | `{{ptr, i32}, i64}` | 16 |

实际使用的 named LLVM struct 名称在表中展开为字段形状；原始 `.ll` 全部保留。21 个 target 的 399 项 IR、allocation size、数组大小、原始 LLVM ABI alignment 和 string 长度字段偏移断言全部通过。

额外仅做 IR 验证的目标：Linux 386、ARM32、RISC-V64、PPC64/PPC64LE、S390X、MIPS/MIPSLE/MIPS64/MIPS64LE、LoongArch64。不得把这些结果标为 Go/LLGo 原生执行通过。

复现命令：

```sh
python3 scripts/go_sizes.py --llgo /path/to/llgo
python3 scripts/go_sizes.py --llgo /path/to/llgo --profile emscripten-memory64
python3 scripts/go_ir.py --llgo-root /path/to/pinned/llgo
```

<!-- END_GENERATED_RESULTS -->

## 扩展结果的判定

允许不同编译器有不同的表示；不允许同一个 LLGo 类型的 `unsafe.Sizeof`、`reflect.Type.Size()` 和实际元素步长互相冲突。

本地 macOS arm64 的[独立复现](../experiments/go_sizes_repro/main.go)不依赖泛型测试框架、C 代码或 C ABI：

```go
type Tail struct {
    B byte
    Z struct{}
}
func size[T any]() uintptr { return unsafe.Sizeof(*new(T)) }
```

| 查询 | Go | LLGo |
|---|---:|---:|
| `unsafe.Sizeof(func() 类型变量)` | 8 | 16 |
| 同一个函数类型的 `reflect.Type.Size()` | 8 | 8 |
| `unsafe.Sizeof(Tail{})` | 2 | 2 |
| `size[Tail]()` | 2 | 1 |
| `reflect.TypeOf(Tail{}).Size()` | 2 | 2 |
| `unsafe.Sizeof([2]Tail{})` | 4 | 4 |
| `[2]Tail` 相邻元素实际地址差 | 2 | 1 |

函数值的 8/16 跨编译器差异是允许的；LLGo 自身 16/8 的查询差异则失败。`Tail` 的结论也不依赖“LLGo 必须复制 gc 尾部 padding”的假设：LLGo 自身已经给出了互相矛盾的数值。

## goplus/lib 的原始 sizetest

另保留了用户指定的 [`c/sizetest.go`](https://github.com/goplus/lib/blob/e39ad357aae4ed9f3962964caeeca0a1a75efbe5/c/sizetest.go) 直接执行记录：

- macOS arm64：`go test -tags=sizetest -v ./c` 通过。
- 同一源码、同一目标的 LLGo：链接失败，`github.com/goplus/lib/c.SizeTest` 未定义。该平台 c 包声明 `LLGoPackage = "decl"`，普通 Go 测试辅助函数无法按该包现有方式生成供外部调用的实现。
- Emscripten wasm32 的 LLGo：`c.SizeTest` 未定义，未执行到 size 断言；`import "C"` 源文件不能通过默认禁用的 wasm cgo 路径纳入。
- lib 自身 CI 的 LLGo 测试没有 `sizetest` 标签，因此其成功不代表这些断言经过 LLGo 验证。

按照用户后续收敛的范围，本轮没有继续改造 C 类型测试或验证 cgo 前处理与最终 C 编译选项的一致性。上述失败属于测试入口问题，不能据此判定 C 类型大小正确或错误。

## 边界

- 本轮实际运行目标以结果表为准；未把 ARM32、RISC-V、其他 Unix 或嵌入式目标标为已通过。
- 标准 Go 当前只有 `js/wasm` 和 `wasip1/wasm`，没有 wasm64 编译目标。Memory64 lane 中运行的 gc 控制仍为 `js/wasm`，不能冒充 gc wasm64 结果。
- wasm32 的 Go `int/uint/uintptr` 使用 8 字节；这不等于 C 指针或 C `size_t` 是 8 字节。
- 当前是 size 盘点；没有将完整 Alignof/Offsetof、C ABI、packed/padding、SIMD 或原生函数声明的验证纳入本轮“基本类型通过”的结论。
