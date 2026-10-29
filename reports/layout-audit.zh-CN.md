# LLGo / llcppg 的 C、C++ 布局兼容性调研

日期：2026-10-29。测试仓库：[cpunion/llgo-cxx-layout-tests](https://github.com/cpunion/llgo-cxx-layout-tests)。这是一个有边界、可复现的兼容性审计，不是“已覆盖全部 C++ 语言”的证明。

## 结论

`padding`、`no-padding`、`padding-if` 和 `pack` 可以作为 LLGo 的布局控制原语，但不足以完整表达 C++ 对象模型。除了总大小与对齐，还必须考虑子对象重叠、完整对象与基类子对象的不同占用范围、动态虚基类寻址、vtable/thunk、非平凡对象生命周期和目标平台的传参分类。

当前 llcppg **已经有** bit-field、union、普通继承、vtable、引用和定长数组实现。此次发现的是这些实现的具体错误、组合使用时的缺口，以及尚未支持的类型；不能将它们统称为“都没有实现”。

同一个 Clang 也不提供跨平台、跨 ABI、跨版本完全相同的布局。测试中既复现了 Linux/Windows 的 bit-field 差异，也发现了 Clang 22→23 在同一 MinGW 目标上的 `packed` 布局变化。仅记录“Clang”或“LLVM 22”不足以描述生成绑定的兼容条件。

## 审计对象与证据等级

精确版本记录在 [pins.json](../pins.json)：

| 对象 | 提交 / 版本 | 用途 |
|---|---|---|
| llcppg main | `d5f2252953e3a89004821afae4de9e2ff947607e` | 当前生成器行为 |
| LLGo main | `b2e1d4e84fcccdc893b77a652c2f5c9b2fc65836` | 当前编译与运行 |
| llcppg PR #761 | `fcfde2b6b240bfe8e470d363b412cbe79b7adf78` | 虚继承新实现，单独测试 |
| LLGo 布局草案 PR #2937 | `2ed55ca77532f91e145f407a3528c8051a27c362` | padding/pack/go-types patch；不能混同 main |
| 本机参考工具链 | upstream Clang 18.1.8 / 19.1.7 / 20.1.8 / 21.1.8 / 22.1.8 / 23.1.4；Apple Clang 21.0.0 | macOS arm64 主机交叉编译 |
| CI 参考工具链 | 每份 JSON 记录完整版本；包含 Clang 23.1.5 和 Apple Clang 17 / 21 | 独立主机与补丁版本复核 |
| SSA 单独实验 | `golang.org/x/tools v0.52.0` | 常量折叠与泛型内建调用 |

结果区分：

- `NATIVE_PASS`：在目标操作系统、目标架构执行 C++ 程序；32 位程序可在兼容的 64 位 OS 上执行。
- `EMULATED_PASS`：在 QEMU 或 Wasmtime 执行，不能声称经过芯片实机测试。
- `COMPILE_PASS`：目标 Clang 的最终 LLVM IR 给出布局常量，未执行目标机器码。
- `PASS`：LLGo 测试中的兼容性断言通过。
- `XFAIL`：实际失败且诊断匹配已知问题；不是兼容性通过。
- `XPASS`：该平台上的已知问题探针通过，记录平台差异，不强行制造失败。
- `ERROR`：无法完成验证，例如基础设施或未分类的编译失败；不能解释成重现布局错误。

Windows 当前 llcppg 本机生成器还存在独立的构建阻塞：`clang.Mangling` 仅有 Linux、Darwin 文件，Windows 编译报告 undefined。仓库的 Windows 绑定运行方案是在 Linux 上按 **Windows 目标**生成，再在 Windows 上编译运行，并明确记录这条路径。不能用此方案声称 Windows 本机生成器已可用。

## 一、提案与实现不准确的部分

### 1. #1029 的兼容性判据需要重写

[llcppg #1029](https://github.com/goplus/llcppg/issues/1029) 中单靠字段大小、偏移、结构大小及对齐来定义兼容性，既有过强的部分，也有不足的部分。

过强：C++ 引用字段的 `sizeof(obj.ref)` 是被引用类型的大小，不是引用在对象中的物理槽大小。例如 `struct Ref { int &value; };` 在 64 位 Itanium 目标中对象占 8 字节，而 `sizeof(value)` 为 4。若映射为 Go 指针，表达式大小不同并不直接说明物理槽不兼容。bit-field 也不能用普通字段的 `sizeof`、取地址或 `offsetof` 检验。

不足：两个类型即使 size/align/offset 全部相同，也可能使用不同的参数和返回值 ABI。本文的 `union_hfa` 和 `nontrivial_value` 是实际执行证据。还需要区分“内存访问兼容”“可按值复制”“可作为原生调用参数”“具备完整 C++ 对象行为”。

建议改用明确的分层契约：存储布局、访问语义、调用 ABI、生命周期；每一层声明支持范围，不能从前一层通过推断后一层通过。

### 2. `no_unique_address` 不是“必须唯一地址”，也不保证合并地址

标准属性允许成员成为 potentially-overlapping subobject，可复用它的存储或尾部 padding；这是允许优化，不是要求优化。同类型、同生命周期的有关子对象仍受地址区分约束。**限制不等于“b 永远不能和 a 共址”**：不同类型的空成员可以共址，且空成员可能与普通数据成员共址；同类型冲突还可能隐藏在嵌套子对象中。

下列结果来自本仓库实际编译；其中具体偏移是目标 ABI / Clang 行为，不是 C++ 标准对所有实现的固定数值。参见 [C++ 属性条款](https://eel.is/c++draft/dcl.attr.nouniqueaddr) 和 [对象模型条款](https://eel.is/c++draft/intro.object)。

MSVC 目标还需区分属性拼写：本次 Clang 对标准 `[[no_unique_address]]` 给出忽略诊断，`Bar2` 为 size 12/f@8；`[[msvc::no_unique_address]]` 的独立探针得到 size 4/x@0。不能把 Itanium 下标准属性的具体行为直接移植到 Windows。

### 3. 只增加 padding 不能表达向前重叠

以下为 macOS arm64、Clang 22.1.8 的参考结果；相同源文件也进入跨平台和版本矩阵。`Empty`、`Empty2` 是不同空类。

| C++ 例子 | 原生结果 | 提案映射 / 草案测试结果 | 问题 |
|---|---|---|---|
| `Bar2 { int a,b; [[no_unique_address]] Empty f; }` | size 8，f@0，`sizeof(f)=1` | `no-padding` 能得到 size 8，但 f@8、字段 size 0 | 总大小正确掩盖地址不一致 |
| 两个同类型 NUA 空成员 a、b，随后 int x | size 4，a@0，b@1，x@0 | 插入 byte 的 Go 映射 size 8、x@4 | x 需要回到较早存储位置 |
| a:Empty、b:Empty2、c:Empty，再跟 int x | size 4，a@0，b@0，c@1，x@0 | Go size 8、x@4 | 顺序累加布局无法表达重叠 |
| `Single { Empty e; }` | size 1 | Go size 0 | 完整对象与零大小 Go 类型不同 |
| NUA `Inner{NUA Empty e;}` 再跟 NUA Empty | 第二个 Empty@1 | `padding-if` 只检查直接成员，得到 @0 | 必须递归检查空子对象冲突 |
| NUA 非平凡 `Tail{long long x; char y;}` 再跟 char z | Tail size 16；外层 size 16，z@9 | 外层 size 24，z@16 | 复用非空成员尾部 padding |
| 两个不同空类型的 NUA Pair | 完整对象 size 1 | Go size 0 | 即使所有成员可重叠，完整对象仍需正大小 |
| `Pair<int,Empty>` | 空成员可 @0 | Go 末尾空成员 @4 | 去掉尾部 padding 不等于移动字段 |
| `Wrapper{Empty e;}`，再将 Wrapper 作为 NUA 成员 | Wrapper 不是 C++ 空类，后续 int@4 | Go Wrapper 零大小，后续 int@0 | C++ 的 empty 与 Go sizeof==0 不能等同 |
| `Empty e[5]; int x;` | 元素 stride 1，size 12、x@8 | Go 零大小元素，size 4、x@0 | 数组步长随完整类型大小变化 |
| `alignas(16) Empty`；普通成员后跟 char | 空类 size/align 16；外层 size 32、char@16 | “空类统一补 1 byte”不足 | 空对象也可能过度对齐 |

C++ 源代码在 [probes/layout.cpp](../probes/layout.cpp)；提案映射的 Go 源和失败断言在 [proposals/padding](../proposals/padding)。GC Go 的独立测试与共同反射测试也在同目录；Go 忽略 LLGo 注释可以正常编译，并不证明采用了 C++ 布局。

另外，单独的 [GNU C 空结构探针](../probes/empty.c) 实测：Clang 22 在 Linux/macOS 等目标得到 size 0、align 1，而 MSVC 目标得到 size 4、align 1；严格 C17 模式拒绝这个扩展。GNU C 的空结构扩展和 C++ 空类是不同规则，不能用一个“空结构大小”规则同时概括两种语言。C++ 完整对象、空基类子对象、NUA 成员也应分开描述。[GNU C 空结构说明](https://gcc.gnu.org/onlinedocs/gcc/Empty-Structures.html)。

### 4. 当前 llcppg 的已验证错误

下表默认数值来自 macOS arm64、本仓库固定版本。其他平台的逐项结果独立保存，不能把这一列外推到所有 ABI。

| 编号 | 问题与实际结果 | 复现目录 | 主要代码位置 |
|---|---|---|---|
| M1 | bit-field 加嵌套 union 被按普通整数字段生成：C Packet size 8、payload@4；Go size 12、payload@8 | [bit_nested](../cases/bit_nested) | `cl/class.go` bit-field 分流和普通字段路径 |
| M1b | 继承加 bit-field 同样丢失位存储：C Derived 12/tail@8，Go 16/tail@12 | [base_bits](../cases/base_bits) | 同上 |
| M2 | bit-field lowering 丢失 callback 的 native 属性：C struct 16，Go 24；Go callback 占 16 而原生指针占 8 | [bit_callback](../cases/bit_callback) | `cl/bitfield.go:461`、`cl/class.go:240` |
| M3 | `_Bool` typedef 的 getter 生成 uint64→bool 非法转换，LLGo 编译失败 | [bool_typedef](../cases/bool_typedef) | `cl/bitfield.go:174,580` |
| M4 | aligned(16) bit-field 仅警告后降为 align 8；外层 C 48、flags@16，Go 32、flags@8 | [bit_align](../cases/bit_align) | `cl/bitfield.go:300,335` |
| M5 | union bit-field accessor 返回整个整数指针；raw=0xa4，写 a=1 后变 0x01，正确应为 0xa5 | [union_bits](../cases/union_bits) | `cl/union.go:102,269`；已有 [#1034](https://github.com/goplus/llcppg/issues/1034) |
| M6 | HFA union 大小/对齐都为 8/8，但生成整数 carrier 改变 ARM64 传参类别；原生加法应得 (4,7)，实际 (3,5) | [union_hfa](../cases/union_hfa) | `cl/union.go:189` 的 float carrier 判断 |
| M7 | 协变返回覆盖把基类调整 thunk 当作返回派生指针的槽调用；返回指针偏移 +4 | [covariant](../cases/covariant) | `cl/vtable.go:237` |
| M8 | flexible array 被生成为指针：C size 4、data@4；Go 16、data@8 | [flexible](../cases/flexible) | `cl/type.go:220`；已有 [#1035](https://github.com/goplus/llcppg/issues/1035) |
| M9 | 普通 packed 结构没有保留布局：C `{char;int}` size 5、align 1、x@1；Go 8/4/x@4 | [packed_plain](../cases/packed_plain) | 普通 record lowering |
| M10 | 普通 alignas(16) record 未保留过度对齐，影响嵌套成员与数组 | [aligned_plain](../cases/aligned_plain) | 普通 record lowering |
| M11 | C++ 空类直接成为零大小 Go struct，普通成员和空类数组错误 | [empty_plain](../cases/empty_plain) | 空 record lowering |
| M12 | NUA 同类型空成员的地址冲突未处理；总 size 可碰巧相同而 b 偏移错误 | [empty_nua](../cases/empty_nua) | NUA 未参与布局 |
| M13 | 普通非虚继承也有尾部 padding 复用：C derived size 8、d@5；Go 12、d@8 | [nonvirtual_tail](../cases/nonvirtual_tail) | 将完整 Base 嵌入 Derived |
| M14 | 非平凡析构类型 `{int value; ~T();}` 按值实参应使用对象地址，Go 生成普通整数字段 aggregate；原生接收方观察到地址数值恰为 payload 37 | [nontrivial_value](../cases/nontrivial_value) | C++ 对象属性没有进入调用 ABI |

`extern "C"` 并不会把 C++ 非平凡类变成普通 C record；对象参数是否间接传递仍取决于目标 ABI 的 C++ 规则。M14 的原生函数只返回 `&argument` 的数值，不解引用错误地址，避免把崩溃作为唯一证据。M6 与 M14 说明：即使修复所有 Sizeof/Alignof/Offsetof，仍然不能自动修复调用 ABI。[Itanium 调用约定](https://itanium-cxx-abi.github.io/cxx-abi/abi.html#non-trivial)。

实现链接固定到审计提交：[class.go](https://github.com/goplus/llcppg/blob/d5f2252953e3a89004821afae4de9e2ff947607e/cl/class.go)、[bitfield.go](https://github.com/goplus/llcppg/blob/d5f2252953e3a89004821afae4de9e2ff947607e/cl/bitfield.go)、[union.go](https://github.com/goplus/llcppg/blob/d5f2252953e3a89004821afae4de9e2ff947607e/cl/union.go)、[vtable.go](https://github.com/goplus/llcppg/blob/d5f2252953e3a89004821afae4de9e2ff947607e/cl/vtable.go)。

正向控制 `basic_bits` 验证相邻 unsigned / signed bit-field 的读写不会互相破坏。原仓库的 bitfield、nested_union、union_basic、base_class、virtual_method 等六个选定 fixture，以及 `goplus/lib/c/bitfield` 的测试已通过；这不是全套测试均通过的声明。

这 20 个 main 探针在 Linux amd64/arm64、macOS amd64/arm64 的原生 CI 中均完成：1 个正向控制 PASS，19 个 XFAIL（包括上述错误和后文的支持缺口）。这四组结果没有未分类 ERROR。

Windows ARM64 的同批用例为 1 PASS、17 XFAIL、2 XPASS（非平凡传参和非虚基类尾部复用）；HFA union 在 Windows ARM64 仍失败。Windows amd64 的同一批用例得到 1 PASS、16 XFAIL、3 XPASS：`nontrivial_value`、`nonvirtual_tail`、`union_hfa` 在该 MSVC ABI 下没有复现相同错误。XPASS 只表示这个具体断言通过，不代表已验证全部生命周期规则。

Windows x86 又实际暴露三个不同失败模式，不能硬套 64 位用例的解释：

- `bit_callback`：生成器警告 callback 放不进其原生偏移，退化为 opaque storage；size 可保留，但 Callback 字段和所需访问 API 缺失。它是明确降级后的功能缺口，不是成功生成了一个可访问的 callback 结构。
- `nontrivial_value`：Linux 主机按 i686 MSVC 目标生成的绑定保留 `_accept_nontrivial` 前缀；LLGo 再进行目标符号装饰，链接器报告 `__accept_nontrivial` 未定义。该平台上尚未执行到非平凡传参断言。
- `union_hfa`：测试先观察到 Go align 4、C align 8，因此没有继续把结果归因于 HFA 传参。这是独立的 32 位 union 对齐错误。

运行器以独立 `failure_kind` 保存这三个诊断；旧 CI 首次遇到它们时按 ERROR/FAIL 暴露，确认原因后才加入已知失败分类。原始非零退出码保留。

### 5. PR #761 不能按旧说明判断最新实现

[PR #761](https://github.com/goplus/llcppg/pull/761) 的旧正文仍描述拒绝 diamond join，但审计提交已经有 flattening。最新代码实际验证出三个问题：

1. **近空虚主基类重复占用。** `V{virtual int value();}; A:virtual V{int a;};`，C A size 16、V@0；生成 Go size 24、V@16。
2. **flattening 没有正确选择并前置主基类。** `Join:Plain,Left`，Left 有虚基类 Shared。C Plain@12、Left@0、left@8、Shared@16；Go Plain@0、vptr@8、left@16、Shared@20；两边总大小都为 24。
3. **不同基类同名成员冲突。** Left/Right 各自合法声明 `value`，Join flatten 后生成器 panic `multiple fields with the same name`。

[proposals/pr761](../proposals/pr761) 保存该 PR 的真实生成结果、C++ 实体地址 oracle、LLGo 断言与碰撞日志，和 main 生成器分开维护。

## 二、不完整的部分

### 1. 完整对象、基类子对象与虚继承

对象的 `sizeof` 是编译期已知的，不应将虚继承概括成“大小无法静态确定”。真正动态的是：通过某个基类视图访问虚基类时，其相对位置可能依赖最派生对象。

本仓库的 `A; L:virtual A; R:virtual A; D:L,R; E:D`：macOS arm64 上，独立 L→A 为 12，D 内的 L→A 为 32，E 内的 L→A 为 40。虚菱形的 A 只有一份；非虚菱形有两份。完整 D/E 的 size 分别为 40/48；MSVC x64 目标则为 48/56。实际地址转换在 Windows/macOS/Linux 本机以及嵌入模拟器上执行。

一套完整模型至少需要区分完整对象布局与 base-subobject 布局，记录 size、data size、non-virtual size、alignment、主基类、共享虚基类、动态 base adjustment。Itanium 的 vbase offset / vcall offset / construction vtable / VTT 与 MSVC 的 vfptr / vbptr / vbtable / vtordisp 不是同一种数据结构。[Itanium ABI](https://itanium-cxx-abi.github.io/cxx-abi/abi.html)、[Clang 的 MSVC 兼容说明](https://clang.llvm.org/docs/MSVCCompatibility.html)。

这次没有穷尽 construction vtable、析构期间动态类型、所有 vtordisp 开关、异常展开、RTTI 与 dynamic_cast；它们是明确的未覆盖项，不应写成已验证通过。

### 2. vtable 与调用不能仅凭源代码顺序推导

除了本次已执行的协变返回错误，还需表示：多主/次虚表、this adjustment、return adjustment、析构函数槽的 ABI 差异、虚继承中的调用 thunk、不同调用约定。模板特化可改变上述属性。

按字节恢复对象布局不等于允许 Go 调用任意虚槽。若不直接使用 Clang 的 ABI 信息，应优先生成 C++ 包装函数，由 Clang 处理具体对象模型。包装方案仍需正确管理对象生命周期和异常边界。

### 3. 模板、concept 与 Go 泛型不等价

本仓库验证了：

- 显式特化可以把 `Special<T>{T value}` 改为 `Special<Empty>{long long cookie}`；不是给一个 Go 泛型结构加 padding 能表达的。
- constrained partial specialization 可让 `Choice<int>` 只有一个 int，而 `Choice<long long>` 多一个 tag。concept 本身不是对象中的字段，但会影响选择哪一个具有不同布局/行为的特化。
- 当前生成器对测试中的特化/别名没有提供所需 B 类型；使用其 Go API 会编译失败。概念声明则触发 `loadDecl: unknown kind - 604`。
- dependent `alignas(T)`、数组长度、基类集合、虚函数集合和 triviality 都可随实例化变化。

[template_specialization](../cases/template_specialization)、[concept_specialization](../cases/concept_specialization) 是生成器探针；参考 Clang 矩阵中的 `SpecialEmpty`、`AlignedGeneric`、`ChoiceInt`、`ChoiceLongLong` 是已选定原生实例的布局事实。

建议把“可以映射的简单泛型模板”和“必须由 Clang 实例化的模板”分开。对具体实例生成目标绑定，通常比宣称所有 C++ template 能统一映射到 Go generics 更可验证。

### 4. 成员指针、原子、扩展类型

`T::*` 不是普通地址指针；成员函数指针也不能一律等同函数指针。Itanium macOS arm64 上，测试中的 data-member pointer 为 8、member-function pointer 为 16；MSVC 的大小随 single/multiple/virtual inheritance model 变化。大小正确也不够，还需要正确处理 null 编码与 this 调整。

当前生成器对 member pointer 和 `_Atomic` 成员有 unsupported 诊断，并省略包含类型；本仓库的 [member_pointers](../cases/member_pointers)、[atomic_member](../cases/atomic_member) 会让这个缺口表现为可见失败。它们应归入“不支持”，不能当作普通字段成功映射。

其他需要单列契约的类型包括 long double、`_Float16`、`_BitInt`、向量/SIMD、scalable vector、地址空间指针以及 ABI 相关枚举。它们未全部进入本次运行矩阵，因此这里是后续支持清单，不是已发现的具体错误清单。尤其不能把已有 SIMD/C 类型映射功能整体判为缺失。

### 5. 端序、位布局和目标参数传递

当前 `cl/bitfield.go` 中有两个清晰的移植边界：`types.StdSizes{WordSize:8,MaxAlign:8}` 被硬编码，`isBigEndianTarget` 始终返回 false。大端目标的 Clang 布局已交叉编译，但 Go bit-field accessor 没有在大端 CPU 执行；源码风险与实测破坏必须分开描述。

生成器解析头文件、编译 wrapper、编译 Go、链接原生库必须共享同一套目标配置。配置至少包括 triple、ABI、CPU/features、packing、bit-field 模式、short-enum/wchar 选项、语言标准、宏、sysroot/header 版本、编译器 ABI 兼容版本。仅把 CFlags 传给 wrapper，无法保证解析阶段看到相同布局。

还实际复现了 host/target 的符号处理错误：[cross_mangling.h](../probes/cross_mangling.h) 声明 `extern "C" int audit_symbol(int)`，在 Darwin 主机上生成 Linux x86_64 或 Windows x64 目标时，绑定写成 `C.udit_symbol`，误删了 `a`。Darwin 主机的 `Mangling` 实现无条件删除首字符；这不是通用的跨目标处理规则。Windows 本机又缺少实现。跨编译能力需要独立定义和测试，不能从“libclang 接受 --target”推导生成器已完整支持该目标。

## 三、平台与编译器版本验证

### 1. “Linux 8，Windows 24”的精确例子

```cpp
struct BitsABI {
    unsigned a : 3;
    unsigned long long b : 40;
    char tail;
};
```

同一个 Clang 22.1.8、不同 `--target` 得到：

| 目标 | sizeof | alignof | tail 偏移 |
|---|---:|---:|---:|
| Linux x86_64 | 8 | 8 | 6 |
| Linux aarch64 | 8 | 8 | 6 |
| Linux i686 | 8 | 4 | 6 |
| Linux armv7 hard-float | 8 | 8 | 6 |
| Windows MSVC x86_64 | 24 | 8 | 16 |
| Windows MSVC i686 | 24 | 8 | 16 |
| Windows MSVC aarch64 | 24 | 8 | 16 |
| wasm32 | 8 | 8 | 6 |

MSVC 模型中 a 从 0 开始占用 unsigned 的分配单元，b 从 8 开始占用另一种宽度的单元。Linux x86_64 中 b 可以从 bit 3 开始。这些 Windows 值由 **Clang 的 MSVC 目标**产生，不需要调用 cl.exe；Windows CI 又独立执行了对应目标程序。

### 2. 编译器版本确实会改变布局

```cpp
struct PackedABI {
    char lead;
    unsigned a : 3;
    unsigned : 0;
    unsigned short b : 9;
    int value;
} __attribute__((packed));
```

同为 `x86_64-w64-windows-gnu`，同为 C++20：

| Clang | sizeof | alignof | value 偏移 |
|---|---:|---:|---:|
| 18.1.8～22.1.8（逐版本执行） | 16 | 4 | 10 |
| 23.1.4 | 12 | 4 | 6 |
| 23.1.4 + `-fclang-abi-compat=22` | 12 | 4 | 6 |

兼容选项在本例中**没有恢复**旧布局。不能把 `-fclang-abi-compat` 当作所有布局变更的回滚开关。本地六个 upstream 版本与 Apple Clang 的其余已测事实需以矩阵为准；“这组探针相同”不等于所有代码跨版本 ABI 相同。

同一 packed 例子在 Clang 22 的 Linux x86_64 为 10/1/value@6，Linux aarch64 为 12/4/value@6，Windows MSVC x86_64 为 11/1/value@7。零宽 bit-field 可改变对齐规则，`packed` 不能概括为跨 ABI 的统一逐字节紧排算法。

版本审计还必须单列 libclang：以固定 llcppg/LLGo 构建的生成器，替换加载 libclang 18～20 时，实际因缺少 `clang_Cursor_isGCCAssemblyVolatile` 等符号而无法启动；21、22、23 可启动，本次成功生成的用例源码哈希相同。此实验说明这份固定二进制的动态库兼容边界（不等价于更换绑定版本或裁剪符号后的所有构建下限），**不代表 libclang 18～20 的语言布局错误**，也不代表 LLGo 已支持 LLVM 18～23 后端构建。后端始终固定为 LLVM 22。

### 3. 验证覆盖与方法限制

C++ 参考矩阵使用 C++17、20、23、2c 模式。C++17 接受某些 C++20 属性可能属于 Clang 扩展，诊断被保留；不能据此声称该特性属于 C++17。C++2c 模式运行这些例子，也不证明实现了全部 C++26 特性。

已覆盖的目标包含 Linux amd64/arm64/x86/armv7、大端 powerpc64；macOS amd64/arm64；Windows MSVC amd64/arm64/x86、MinGW amd64；ARM EABI、RISC-V 32/64、wasm32，另有 Espressif Clang 的 Xtensa ESP32 交叉编译。**不是所有目标都原生执行**：以 JSON 中状态和下述命令为准。

Windows/macOS/Linux 的八个原生 C++ 目标组合均已运行。Clang 18～23 另在 Linux amd64 执行，并进行跨目标编译。macOS 没有虚构一个现代 32 位 x86 原生环境。

Cortex-M3 在 QEMU `mps2-an385`、RISC-V 32 在 QEMU `virt`、wasm32 在 Wasmtime 中运行了完整 facts 输出和虚/非虚菱形、虚函数调用、空成员地址断言。Xtensa 目前仅完成 Espressif Clang 交叉编译；没有 ESP32 板卡或匹配 ESP32 machine 的模拟器执行证据，不应写成硬件验证通过。

不要把 `-fdump-record-layouts-complete` 单独当作最终 oracle：实测它可能在尾部 `__attribute__((packed))` 生效前输出布局。本仓库读取最终 `sizeof/alignof/offsetof` 的 LLVM 全局常量，再与目标执行值比较，并保留原始 IR/诊断。

## 四、go/types、unsafe 与 SSA

[experiments/ssa](../experiments/ssa) 用真实 `golang.org/x/tools/go/ssa` 构建并输出 SSA，区分两个路径：

1. **具体类型。** `go/types` 在类型检查阶段通过 `types.Config.Sizes` 求值，把结果写入 `types.Info.Types[expr].Value`。SSA 构建器将其转换为 `*ssa.Const`。本例的 packed `{byte; int32}`：普通 gc 为 8/4/4，自定义 Sizes 和 patched LLGo go/types 为 5/1/1。
2. **含类型参数的可变大小表达式。** 类型检查没有常量值，SSA 保留内建调用。`InstantiateGenerics` 的 `Generic[int32]` 中仍观察到 Sizeof/Alignof/Offsetof 调用；由 LLGo 后端使用实例化后的布局处理。

所以“源码中看起来像函数调用”不等于 SSA 有普通函数调用；“最终能变成常量”也不等于在 go/types 阶段已经是常量。

SSA 本身不解析 LLGo 布局指令，不持有可用于事后重算全部 unsafe 常量的 Sizes 配置。必须在类型检查前保留注释并登记布局属性，正确设置目标 Sizes，恢复导入类型的布局元数据；不能先用 gc 检查，再期望仅构建 SSA 就自动修正。显式传入其他 Sizes 时也不能假设 patch 会覆盖调用方选择。

[proposals/layout_runtime](../proposals/layout_runtime) 在布局草案编译器上验证了 packed、pack(2)、泛型提升字段、native callback、Go closure 的静态大小与泛型结果，以及反射/实际字段地址之间的关系。下述成功执行的平台上具体值检查通过；普通 Go 的共同一致性测试也通过。它不证明未支持的 C++ 重叠布局能被 Sizeof 接口凭空恢复。

跨平台补测给出了一个重要限制：[草案/SSA 结果矩阵](../evidence/proposal-matrix.md) 中，七个平台的普通 Go 检查和两种 patched SizesFor 名称的 SSA 常量检查均通过（SSA 实验显式使用 amd64 Sizes；运行时测试采用实际目标）；Windows amd64/arm64/x86、Linux arm64、macOS arm64 的 `layout-runtime` 也通过。但是 Linux amd64 与 macOS amd64 在编译该测试时均于 `LLVMTargetMachineEmitToMemoryBuffer` 中发生 SIGSEGV，Linux 复跑继续失败；macOS amd64 复跑通过，首次失败日志仍保留。Linux 最新状态为 ERROR，尚未执行到布局断言；macOS 为复跑 PASS，不能由此宣称崩溃根因已经修复。

这个结果不说明 `go/types` 已折叠的常量错误。独立的 [代码生成隔离运行](https://github.com/cpunion/llgo-cxx-layout-tests/actions/runs/40815304481) 中，完整测试在 `-p=1` 下仍崩溃；单独 packed 参数、pack(2)、native func 程序编译运行成功，但普通泛型嵌入字段的 `promoted` 小程序崩溃。这个小程序**没有布局指令**，因此不能直接归因于 packed。源码位于 [小型代码生成探针](../experiments/packed_codegen)；进一步对照 main、具体类型与直接字段 Offsetof，避免把已有后端问题误判为布局 patch 回归。

进一步的 [main / 草案对照运行](https://github.com/cpunion/llgo-cxx-layout-tests/actions/runs/40816298326) 得到：

| Linux amd64 小程序 | 固定 LLGo main | 布局草案 |
|---|---|---|
| 泛型嵌入字段，返回 size/align/offset | 编译器 SIGSEGV | 编译器 SIGSEGV |
| 非泛型嵌入字段，返回 size/align/offset | 编译器 SIGSEGV | 编译器 SIGSEGV |
| 泛型嵌入字段，只返回 Offsetof | 编译器 SIGSEGV | 编译器 SIGSEGV |
| 泛型直接字段，只返回 Offsetof | PASS，4 | PASS，4 |
| packed / pack(2) 参数 | 未执行 | 分别输出 5/1/1、6/2/2 |
| native 函数值 | 未执行 | 输出 8 |

三个崩溃程序都没有 LLGo 布局注释，且普通 Go 执行通过。由此可以确认它是本次固定 main 已存在的后端问题，不能称为布局 patch 新增回归，也不能归为泛型独有问题。尚未定位到 LLVM/LLGo 的具体责任代码；`Offsetof`、嵌入、聚合参数传递之间的根因仍需后续调试。诊断工作流为了收集后续案例而正常结束，每例的 `COMPILER_CRASH` 与非零退出码仍明确保留，不能把其绿色状态当作兼容性通过。

源码链路可直接复核：[go/types 的 unsafe 内建处理](https://github.com/golang/go/blob/go1.27.3/src/go/types/builtins.go)、[Sizes 接口及 Config 的调用转发](https://github.com/golang/go/blob/go1.27.3/src/go/types/sizes.go)、[SSA builder 从 Info.Types 读取常量](https://github.com/golang/tools/blob/v0.52.0/go/ssa/builder.go#L585)。Sizeof/Alignof 对具体类型调用 Sizes 的对应方法；Offsetof 沿选择路径累加各层 Offsetsof，不能只看最后一层字段偏移。

自定义 Sizes 对已编码的布局模型有效，无法替代 C++ 对象模型和 ABI 信息源。`types.Sizes` 的三个方法本身也不提供 vtable、虚基类寻址、bit-field 位宽、参数寄存器分类或析构信息。参见 [Go 规范](https://go.dev/ref/spec#Size_and_alignment_guarantees)、[SSA API](https://pkg.go.dev/golang.org/x/tools/go/ssa#Program.CreatePackage)。

## 五、建议与需要补充的提案

### 1. 修订现有提案，而不是重复提出已有功能

- 修订 #1029 的兼容性判据和空对象示例，明确每个例子的语言、ABI、版本以及允许失败的范围。
- 同步 [LLGo #2788](https://github.com/xgo-dev/llgo/issues/2788) 与 #1029 对指令放置和非泛型使用范围的描述。布局草案已经明确其原语不是完整 C++ 对象模型，不应把这个限制写成草案违反了自己的承诺。
- 对 [#1030](https://github.com/goplus/llcppg/issues/1030) 的自动验证方案补上 bit-field、引用、base subobject、真实地址、调用和生命周期验证；只比 sizeof 会漏掉本文多个错误。
- 继续扩展现有 union、bit-field、特殊 C 类型、数组和虚继承工作；分别对齐 #1034、#1035、#1033、PR #761 等已有入口，避免重复立项。

### 2. 建议新增或独立明确的契约

| 优先级 | 契约 / 提案 | 最小范围与验收 |
|---|---|---|
| P0 | 目标与工具链配置契约 | header parse、wrapper、Go 后端、native library 共用目标参数；生成物记录版本/目标/宏/头文件指纹；不匹配时诊断 |
| P0 | Native record layout descriptor | 由 Clang 导出完整对象、base subobject、size/align/data size、成员/base 偏移与重叠关系；明确类型身份与导入导出格式 |
| P0 | 调用 ABI 与对象生命周期边界 | nontrivial argument/result、HFA/SIMD/union、this/return adjustment；不支持时生成 wrapper 或拒绝直接传值 |
| P1 | C++ 继承与对象视图 | 主/次基类、虚基类动态转换、construction/destruction 规则；先分别实现 Itanium/MSVC，不假定同一虚表结构 |
| P1 | 空子对象及尾部复用 | 完整对象正大小、递归同类型地址冲突、NUA overlap、base tail reuse、数组步长 |
| P1 | 位字段、union、FAM 完整性 | signed/bool/typedef、零宽/跨单元/端序/volatile/atomic 约束、union 活动成员、FAM offset 与分配责任 |
| P1 | 具体模板实例化与支持诊断 | specialization/concept/dependent layout 在 Clang 侧确定；缺失类型不伪装成功生成 |
| P2 | 成员指针与扩展原生类型 | 各 ABI 表示、null 编码、转换/调用；不能转换的类型使用 opaque handle + wrapper |

布局描述应优先成为编译器、go/types patch、反射和生成器共同消费的元数据。共享纯布局实现、代码生成一致性检查和 LLVM/native oracle 三者互补：源码一致性只能防止实现漂移，不能证明规则本身正确。

新增重叠布局时，还需验证赋值是否会写入别的子对象正在复用的尾部 padding；不能默认按完整 `sizeof(Base)` 做 memcpy 就等同于 C++ 的基类赋值。字节 carrier 的 Go equality/hash 也不自动等于 C++ 的语义比较。这些是扩展重叠支持时的验收要求，本次未把它们写成已实现路径上的独立运行错误。

布局草案已对普通 packed Go 存储中的未对齐 managed reference 做限制；native 存储指向 Go 对象时仍需要独立保活。未来的 overlap、union active member 和对象生命周期描述也必须与 GC 扫描、复制、反射规则一起设计。

`go/types` 标准补丁不能反向依赖整个 llgo 编译器包；可维护纯 Go 的共享模型/生成适配层。遇到完整 C++ 语义时由 Clang 提供描述或包装，不应在运行时库中再实现一份 C++ ABI。

### 3. 工程落地顺序

先修复会悄悄生成错误绑定的当前实现；对尚不支持的类型提供明确诊断。随后建立目标/ABI 指纹和原生 oracle，再扩展重叠布局及调用模型。每增加一种布局规则，同时验证嵌套、数组、copy、接口、反射、export/import、泛型、unsafe 常量、SSA 内建调用与原生传参。

对于完整 C++ 类，优先选择 opaque handle + C++ wrapper 的可验证路线。确实需要直接内存映射的类型应经过白名单式能力判定与 native oracle；不要把所有 record 自动当作可安全复制的普通 Go struct。

### 4. 修复归属：编译器问题与生成器问题需要分别隔离

汇总跟踪：[LLGo #2943](https://github.com/xgo-dev/llgo/issues/2943) 负责编译器失败和原生表示能力；[llcppg #1123](https://github.com/goplus/llcppg/issues/1123) 负责生成错误和编译器依赖。已有专项 issue 继续作为对应问题的主入口，不逐用例重复建单。

归属不能仅按“布局错误”或“ABI 错误”的名称判断。先看生成表示是否准确传递了原生类型信息，再检查 LLGo 对该表示的存储、查询、反射和调用是否一致。某个原生语义没有可表达的 LLGo 契约时，编译器能力建设与生成器接入分别跟踪；wrapper 或明确拒绝也是生成器可以采用的边界，不代表必须先修改 LLVM。

新增 [ownership_controls.py](../scripts/ownership_controls.py) 对两份真实生成快照做最小手动修改，再运行原来的原生 oracle 和 Go 断言。以下补测仅在 macOS arm64、LLVM 22 上执行，不替代七平台生成器矩阵：

| 控制修改 | 固定 main | 布局草案 | 归属结论 |
|---|---|---|---|
| 仅给 CallbackBits 增加 `//llgo:cdecl` | struct size/offset 正确，但 callback Sizeof=16（C=8）、reflect struct size=24（C=16） | 全部断言 PASS | llcppg 缺标记；LLGo 还存在独立查询/元数据问题，关联 #2796、#2873 和 PR #2937 |
| union 存储改为 `[2]float32`，加 `[0]uint64` 保持 alignment=8 | size/align 与真实传参全部 PASS | 全部 PASS | 本例是 llcppg 丢失浮点分类，不能仅凭失败就指认为 LLGo HFA lowering 错误 |

第二项只是这个具体 union 的诊断表示，不是所有 ABI 上通用的 union 实现。Windows x86 的 union align 4/8 差异尚未完成同样的 native 标记与物理存储对照，暂不强行归责。

需要 LLGo 跟踪的部分：

- 无布局指令的嵌入结构触发 Linux amd64 编译崩溃，main 与草案均复现。
- 已有 native 声明仍出现 unsafe/go-types、反射和物理布局不一致；优先关联现有 #2796、#2873、#2872，不重复建同类 bug。本次补测没有执行 reflect.Call，不能将其写成对 #2872 的新运行复现。
- packed 的编译器支持由 PR #2937 跟踪；显式提高 record 对齐、overlap/base-subobject 描述需要额外契约。`pack N` 只是降低字段对齐上限，不能表达 `alignas(N)`。
- 如果选择直接传递非平凡 C++ 值或通用原生 union，需要讨论导入 Clang ABI 信息的编译器接口；这是条件性的能力提案，不能称为 LLGo 已拿到正确 C++ 元数据却错误处理。生成器也可以选择 C++ wrapper 或明确拒绝不支持的直接调用。

llcppg 负责生成错误、指令接入和不支持类型的诊断：位字段组合/typedef bool、callback 属性、union carrier、协变返回槽、基类 flatten、模板特化/concept、符号装饰与 host/target 配置。packed、过度对齐、非平凡值等需要编译器能力时，生成器条目链接对应依赖，避免两个仓库重复记录同一个修复目标。

## 六、较新语言规范的后续建议

这部分优先级低于已复现的基础对象模型问题。

- C++23 explicit object parameter：其函数地址语义可能不同于传统 member-function pointer，不能按所有成员函数同一种表示处理。
- C++20/23 concepts、约束特化、结构化非类型模板参数：重点是实例选择、名字编码和导出的 API，不是给 concept 设计内存槽。
- C++26 pack indexing、static reflection、新的 lifetime/relocation 能力：按具体 Clang 版本与 feature-test macro 开启独立探针，避免仅因接受 `-std=c++2c` 就宣称支持。
- modules/PCH、标准库 ABI、`std::string`/`std::function`/容器：版本、标准库实现和 ABI 开关也需进入绑定指纹；本次没有宣称跨 libc++/libstdc++/MSVC STL 验证。
- 异常、coroutine frame、`atomic_ref`、over-aligned allocation 等应建立单独的行为测试；不能仅从 record layout 判断可互操作。

较新 Clang 的 ABI 与诊断仍会调整，查阅对应版本的 [release notes](https://releases.llvm.org/23.1.0/tools/clang/docs/ReleaseNotes.html)，并保留最小回归例。本文已经给出一个无需新语言特性的实际跨版本反例，因此基本布局也需要持续版本矩阵。

## 复现与结果导航

主入口与构建命令见 [README](../README.md)，机器可读结果与覆盖表由 [证据索引](../evidence/README.md) 导航。所有生成器用例的输入头文件、Go 断言和原生 oracle 均在仓库中；临时工作目录和编译产物不纳入源码。

原始 CI 日志应保留：修复测试驱动的工具链版本/参数错误，不等于修复被审计项目。判定兼容性以每个用例的 PASS/XFAIL/XPASS 和实际断言为准，而不是只看 Actions 工作流是否绿色。
