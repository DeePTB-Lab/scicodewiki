# scicodewiki 设计文档

> 状态：v0 施工蓝图（2026-08-11 对齐定稿）
> 参考：CodeWiki, arXiv:2510.24428（MIT）；phonax 内部文档 docs/01–15

## 1. 定位

scicodewiki 是面向科学计算仓库的**仓库原生、持续验证的文档生成工具链**。
与 CodeWiki/DeepWiki 同品类，但补上该品类结构性缺失的三层：**公式层、约定层、文献层**。

- **原子产品 = 被验证的公式断言**。站点、徽章、审计报告都是它的投影。
- 认识论分野：code wiki 的隐含假设是"代码即规格"（对业务软件成立）；
  科学软件里**代码不是规格，物理才是**。代码是"它算了什么"的事实来源，
  但不是"物理对不对"的事实来源（后者靠 oracle 测试兜底）。

## 2. 产品章程（已对齐）

| 维度 | 决定 |
|---|---|
| 核心形态 | 仓库原生工具链：注册表住在目标仓库里，验证是文档能力（按需/build 时跑），CI 集成可选不强制 |
| 原子产品 | 被验证的公式断言 |
| 读者端 | 独立 mkdocs wiki 站，与目标仓库现有 docs/ 并存互链 |
| 生成端 | 用户自己的 coding agent CLI（Claude Code 为主，codex 等薄适配）；零 API key、零自有基建 |
| 数据主权 | 注册表永远在被文档化的仓库内 |
| 足迹纪律 | scicodewiki 在目标仓库的产出全部 confined 在 `wiki/` 一个目录内
（注册表 wiki/formulas/、页面 wiki/pages/、构建 wiki/_site/）；
唯一例外 `.github/workflows`（GitHub 强制路径）；AGENTS.md/CLAUDE.md 注入须
`init --agents-md` 显式 opt-in |
| 入口 | CLI 是骨、plugin 是皮：v0 建命令层，v0 末包 plugin，v1 起 plugin 是日常主界面 |
| 路线图 | 开源工具 + phonax 样板间 + JOSS/CPC 论文；不做托管服务 |
| 协议 | MIT |

## 3. 认识论与信任模型

1. **LLM 是提议者，不是权威**。LLM/agent 的全部产出（公式、符号身份、约定声明）
   是候选，必须过机械门或标为人审。
2. **trust nothing**：agent 通过文件通信，不通过对话通信；agent 的自述对管线零影响，
   只有它写下的文件被解析，只有 harness 自己跑的测试被相信。
3. **防过拟合**：测试分两级——迭代级（agent 自选输入，用于自我修正）与
   门槛级（验证时当场新生成的 holdout 随机输入，判决依据）。
4. **产品红线**：未验证公式永不以事实面目渲染。
5. **借能力不借权威**：agent 的一切能力（web search、仓库探索、跑测试、读文献）
   都是提升提议质量的腿；权威始终在机械门与人审。

### 信任徽章四态

| 徽章 | 含义 |
|---|---|
| ✅ verified | 在当前 commit 上通过门槛级验证 |
| 🕐 stale | 绑定文件在当前 HEAD 已变更，判决停留在旧 commit（git 比对得出，不需 CI） |
| ❌ failing | 上次验证失败，附比值诊断 |
| ⚪ unverified | 未验证（含 novel 条目仅挂 oracle 佐证者） |

徽章真相 = 判决记录（commit hash + 时间戳 + 种子 + 容差）+ git 新鲜度比对。

## 4. 五阶段架构

```
repo ──▶ S1 结构分解 ──▶ S2 公式提取与验证 ──▶ S3 代码层叙事
              │                  │                   │
              │            registry YAML             │
              └────────┬─────────┴───────────────────┘
                       ▼
                S4 组装渲染（mkdocs + KaTeX）
                       ▲
                S5 漂移维护（git 比对 → 按需复验 → 漂移报告）
```

### S1 结构分解：双树

- **模块树**：Tree-Sitter AST + 依赖图（v1）。v0 手工指定单元。
  科学仓库的实际切分需求是**文件内按方法粒度切**（phonax `linewidth.py` 单文件 3800 行），
  CodeWiki 的 32k 叶子预算思想在此适用。
- **管线树**：物理工作流（如 relax → FC2 → FC3 → linewidth），wiki 顶层组织原则。
  v0 手写 manifest；v1 agent 推断 + 人确认。
- **科学核识别**：把智能按科学含量分配而非文件体积。
  启发式（einsum/linalg/物理常量/docstring 含公式）+ 调用图，区分核与管道（CLI/IO/配置）。

### S2 公式提取与验证（品类差异所在）

1. 候选生成：agent CLI（v1 批量；v0 手写转录 + agent 辅助文献 grounding）
2. 机械门：SymPy → lambdify → holdout 随机输入 → 与绑定实现比对；量纲检查（pint）可选
3. 过门 → tier-1 verified；不过 → 记录诊断、降级或待办，**不静默丢弃**
4. 约定挖掘：docstring 中的单位/归一化声明 → convention_map
5. 文献 grounding（agent 原生能力，不后置）：agent 用 web search/arXiv 定位规范文献、
   读公式，作为候选与 references（paper + eq. no.）的依据；付费墙文献回退到
   用户提供的本地 PDF 路径。搜索提升提议质量、引用精确到公式编号
   （人审 = 打开被引公式看一眼），但不改变权威：候选仍过机械门，
   文献↔SymPy 腿保持 agent 提议 + 人审

### S3 代码层叙事

- v1 = agent 逐页读码生成（phonax 量级足够）。CodeWiki 的递归聚合/DP 分割
  解决的是规模不是深度，降级为 v2 大仓库可选项——复杂度预算属于验证层。
  跨模块引用代替重复文本。v0 手写/单次生成。
- **内容纪律**：代码叙事永远不复述注册表拥有的数学。
  散文写"此函数计算三声子矩阵元（→ `linewidth.matrix_element_V`）"，
  讲输入输出、职责、内存布局、性能；公式让给公式卡片。单一事实来源。
- **理论叙事**（理论层，agent 借 web search/读文献生成）：成熟领域的理论背景
  （deeptb-jax 的 TB/Slater-Koster；phonax 的三声子微扰/Maradudin-Fein）。
  内容纪律的唯一例外：**理论页展示文献规范形式**（LaTeX）+ 约定换算框
  （规范形式 ↔ 代码形式），并链接代码绑定公式卡——否则读者只见代码求值形式，
  文献层落空。理论散文属 👤 审级，引用（paper+eq）是使人审极便宜的锚。
  **范围纪律**：理论叙事以注册表 implements 边界为界——每页只写到理解其
  公式卡所需的深度，止于钉死规范形式的文献；不写教科书。
  文献覆盖两条腿：web search/arXiv 覆盖新文献，用户本地 PDF 覆盖付费墙老文献。
### 图生成（一等交付物）

| 类型 | Mermaid 形态 | 来源 | 页面归属 |
|---|---|---|---|
| 架构总览图 | flowchart + subgraph 分组 | 模块树 + 子系统间边 | 项目概述 |
| 调用链时序图 | sequence + alt 分支 | 入口调用迹（拓扑排序找入口；子命令 dispatch → alt 片段） | 概述 / CLI 页 |
| 数据流图 | flowchart | 数据依赖 | 子系统页 |
| 依赖图 | graph | import 图 | 开发与参考 |
| 张量数据流图 | flowchart，节点带形状/指标 | 核内 einsum/reshape 迹（如 `einsum("ai,qabc,qbj,qck->qijk")`） | 子系统页；科研特有 |

生成两段式（同公式层认识论）：
- **机械 grounding**：AST/调用图提供节点与边的全集，保证图中一切真实存在
- **LLM 抽象选择**：展示哪个层级、组命名、省略哪些边——提议性质

**结构验证**：图里每个节点须为真实符号、每条边须为真实 call/import 边
（或在 provenance 中显式声明的"抽象边"）。验证不过的图不渲染。
图同样进 S5 漂移维护：相关 call 边变化 → 图 stale → 重生成。

### S4 组装渲染

mkdocs + KaTeX；页面结构见 §7；徽章渲染读判决记录 + git 新鲜度。
**双向源码链接**（代码地图）：implements 绑定渲染为 公式卡→源码行 与
源码行→公式卡 的双向链接，渲染器必做。

### S5 漂移维护

git diff 定位受影响条目 → 复验 → 漂移报告（带比值诊断）→ 受影响页标 stale。
**验证先于再生成**：比 CodeWiki 的"diff → 重新生成散文"便宜几个数量级且结论确定。
plugin hooks 可让"绑定文件变更 → 自动复验"成为默认行为。

## 5. 验证机制细则

- **没有 `tests/formulas/` 目录，没有手写测试**。检查由工具从注册表条目合成：
  条目自带验证所需全部信息（sympy 表达式、implements 绑定、采样配置），
  条目与它的检查是同一个东西，检查不跟公式漂移。
- 验证是**文档能力**，不是开发门禁：什么时候跑是团队的选择（build 时/按需）；
  CI 只是可选集成之一。
- **比值诊断**：门槛测试失败时输出诊断而非断言——
  常数比值 → 乘性漂移（自动枚举常见因子 1/2、1/3!、2π、ħ）；
  非常数比值 → 结构性差异（打印最大偏差输入）。
  维护者拿到的是半个答案，不是红叉。

## 6. 注册表 schema

住在目标仓库 `wiki/formulas/`（YAML + SymPy 源；足迹纪律见 §2）。草图（非定稿）：

```yaml
id: linewidth.matrix_element_V
kind: algebraic              # algebraic | quadrature | novel | convention-map
sympy: V == Rational(1,6) * sqrt(hbar**3 / (8*N*w1*w2*w3)) * Phi3_contract
implements:
  module: phonax.phonons.linewidth
  function: interaction_strength_batch     # 绑函数名+命名数组；行号仅渲染提示
symbol_identity:             # 人审层，机器不判
  - einsum 轴 a：笛卡尔方向，随晶体位点协变
  - w* 为角频率 rad/s；输出端换算 cyclic THz
convention_map:
  - ours: V 显式含 1/3!
    theirs: Togo2015 用 |V|^2 + 18π/ħ² 前置
    verified_by: tests/oracles/test_linewidth_oracle.py   # 链接，不是依赖
references:
  - {paper: Togo2015, where: PRB 91 094306, eq: null, pdf_anchor: null}
provenance: {origin: human, at: 2026-08-11, via: docstring-transcription}
test: {type: exact, tol: 1e-12}   # exact | convergent | oracle
verdicts:                  # 追加式判决记录 = 审计语料 + 徽章来源 + 论文证据链
  - {at: 2026-08-11, commit: abc1234, seed: 42, result: pass}
```

测试语义三档：
- `exact`：代数阶段，holdout 随机输入 machine-precision 比对
- `convergent`：数值积分阶段（如 δ 积分的高斯 vs 四面体两实现），断言细化序列下一致，带显式容差
- `oracle`：novel/创新公式，无文献对应，验证依据为外部 oracle 对拍 + 内部自洽

**研究钩子（现在留，事后补会破坏数据连续性）**：
- `provenance` 全程留痕（human / agent:\<worker\>:\<prompt-hash\> / 文献转录）
- `verdicts` 持久化每次运行（时间戳、种子、容差、诊断原文）
- 预留 `scicodewiki export-benchmark`：claim 级导出（公式+绑定+文献+判决历史）
- 文献引用机器可寻址（paper + eq + pdf_anchor）

## 7. 页面结构（读者视角，Qoder 式三段骨架）

根节点只留五项；导航标签由 manifest 数据驱动，不写死。

```
项目概述
核心概念与理论基础        ← 公式层+约定层规范形式首页（人审为主）
入门 ▾（安装与环境 / 快速开始 / 配置系统 / 命令行接口）
子系统 ▾（按领域语义单元切，非 Python 模块名）
开发与参考 ▾
```

子系统页（wiki 主体）内部骨架：
概述 → 公式卡片（注册表，带徽章）→ 本子系统约定 → 代码走读 + 张量数据流图
→ 验证状态 → 文献。

审计面收进"开发与参考"，不占顶层导航：
**公式注册表与验证状态**（徽章全集）、**约定总表**（convention_map 自动聚合）。

phonax 实例：

```
项目概述
核心概念与理论基础
入门 ▾
子系统 ▾
  对称性引擎
  谐波拟合与 FC2
  声子谱、稳定性与软模        ← docs 05/06 归位
  非谐拟合与 FC3
  三声子线宽与寿命            ← v0 样板页
  可靠性评估
  工作流与 CLI 编排
  IO 与 providers
  示例与教程
  高级专题：创新层/性能工程/对称性分辨   ← docs 04/12/14 归位
开发与参考 ▾
  开发者指南 / API 参考文档 / 架构与设计文档
  公式注册表与验证状态
  约定总表
  附录
```

生成成本分配：1、3 区通用内容用 CodeWiki 式叙事（轻验证）；
2 区子系统页走完整注册表管线；1 区理论页人审为主。
结构借 Qoder，内容才是护城河。

## 8. 分发形态与入口

一个仓库，一份核心源码，两种分发：

```
scicodewiki/
  core/                 # 确定性机械（纯 Python，零 agent 依赖）= 权威层
    registry/ verify/ render/ drift/
  plugin/               # Claude Code plugin = 交互层/主界面（v0 末起）
    .claude-plugin/plugin.json
    skills/             # 剧本 = SKILL.md + 对 core/ 脚本的子进程调用
      extract-formula/ fix-drift/ build-wiki/
    hooks/              # 绑定文件变更 → 自动复验
  pyproject.toml        # pip/CLI = 无 agent 场景、CI、审稿复现
  schemas/
```

- 权威层必须是**作为外部进程运行的确定性代码**：agent 无法跳过、CI 无需 agent、
  JOSS 可引用。PyPI 上架是 v1 包装步骤，不挡 v0。
- skill = 指令 + 打包工具；剧本步骤落到 `python core/verify.py ...` 子进程，
  判决来自退出码与结构化输出，不来自 agent 叙述。
- 跨 CLI：共同层 = 开放标准（AGENTS.md + Agent Skills 开放标准 + MCP + hooks，
  两厂商均支持，2026-08 核实）；厂商特有仅 plugin 打包/marketplace 分发渠道。
  v0 先落 Claude Code 分发，codex 分发 v1（内容原样复用，薄适配：
  hook 事件语义、skills 目录约定）。
- MCP 暂不做（v1 重议，见下表）。

### 生态能力借用（Claude Code / codex）

已借：skills+打包工具、hooks、headless 单调用、agent web search/读文献。

| 能力 | 用法 | 时点 |
|---|---|---|
| CLAUDE.md/AGENTS.md 约定注入 | init --agents-md（opt-in，足迹纪律）写文档约定段：注册表存在、绑定清单位置、"改绑定代码后跑 verify"——任何进入仓库的 agent 会话成为文档维护参与者 | v0（opt-in） |
| PostToolUse(Edit) hook | 编辑绑定源文件即验证，结果注入当前会话；漂移闭环在造成漂移的编辑里闭合 | v0 |
| slash commands | /verify /build 薄 UX | v0 |
| plugin 内 MCP server | 注册表作为结构化知识源（绑定查询/verdict 历史）供任意对话使用 | v1 |
| 专用 subagent 定义 | formula-extractor / theory-writer，窄化提示+工具集 | v1 |
| 宿主 agent subagent fan-out | S3 递归生成：skill 指示宿主按子系统派 subagent，用生态并行，不自造编排 | v1 |

纪律：生态面全是 UX 糖，护城河在 core/；裸 CLI 永远完整可用，
产品存活于生态变迁。生态集成面向开放标准（AGENTS.md/Skills/MCP/hooks）而非
单一厂商机制；plugin 只是 Claude 侧的分发包装。

### preview 模式（漏斗宽口，v1）

最低要求入口：不建注册表/不写公式/不配 CI/不改仓库；一条命令生成代码层 wiki
（叙事 + 结构 grounding 的图），**零公式断言**，叙事显式标 ⚪ 未验证。
比 deepwiki-open 更轻：不起服务、不建向量索引、不要 embedding key。
价值 = 升级路径：preview 推断的树 = `init` 的 manifest 草稿；逐条 ⚪→✅。
这是对 deepwiki-open 17.6k stars 提出的采用摩擦问题的回答。

## 9. Agent 任务契约

```
scicodewiki 交给 agent 的任务包（一个 prompt + 目录）：
  目标函数:     <module>::<function>
  schema:      schemas/formula-entry.schema.json
  迭代 harness: core/verify.py --staging
  交付位置:     formulas/staging/<id>.yaml + <id>_formula.py

agent：探索代码 → 写候选 → 自测 → 修 → 交付文件（汇报随便）
harness：parse staging（失败打回，最多 N 次，超限转人工）
        → holdout 新种子门槛复验 → 过门入注册表 / 不过诊断归档
```

进程形态：一个任务一次 headless 调用，进程级隔离，可并行。
权限边界（v2 议题）：任务声明"只写 staging 目录"。

## 10. v0 施工顺序与验收

1. core 骨架：registry schema、verify（等价门 + holdout + 比值诊断）、render（mkdocs+KaTeX+徽章四态）、drift
2. phonax 数据：手写 6 阶段 manifest；三条条目手写转录——
   `matrix_element_V`、`gamma_assembly`（exact），`degenerate_redistribution`（novel/oracle）
3. 命令层 + 一页子系统页（线宽），渲染出徽章四态各一次
4. 验收：改 phonax 一个前因子 → `scicodewiki verify` 失败 →
   输出"比值恒为 6.0 → 疑似缺 1/3!"诊断。同时验证护城河机制与维护摩擦
5. v0 末：plugin 包装（skills + hooks 由刚跑通的流程沉淀，不猜）

v0 非目标：Tree-Sitter 自动分解、agent 批量提取、递归叙事、PyPI 上架、
marketplace 发布、第二个 CLI 适配、MCP、CI 集成。

## 11. 研究路线图接口

- **审计线**：首选靶子 deepwiki-open（零评测、开源、可本地跑、用户量最大），
  加 CodeWiki/裸 LLM 跑科学仓库，人工审计公式断言错误率；
  散文层评分参考 CodeWikiBench 的 rubric 法（官方文档→层次 rubric→多 judge），
  公式层用我们的机械判定，不用 judge。
- **基准线**：ground truth = 注册表条目（SymPy + 绑定 + 文献）；
  声子输运代码家族（phono3py/ALAMODE/ShengBTE/almaBTE）= 现成跨代码语料，
  约定差异有据可查，团队有 oracle 判定能力。
- **跨领域案例**：deeptb-jax（TB/Slater-Koster，规范形式由 SK-1954 钉死；
  手握其 Qoder wiki 作基线对比）——v1 回答审稿人"能泛化吗"。
- 发表位置：CPC / ICSE·ASE·FSE / JOSS（工具成熟后）/ AI4Code workshops。
- schema 的 provenance + verdicts + export-benchmark 即研究数据管线。

## 12. 明确不做

托管服务（v2+ 才议，且只是薄分发渠道）；IDE 插件；代码库 RAG 向量索引
（chunking 切断公式完整性、索引维护引入额外漂移；chat 与上下文供给被 agent 环境原生替代）；
CI 强制；`tests/formulas/` 手写测试目录；自渲染 web UI（mkdocs 足够）；
多后端 LLM client 抽象（agent CLI 即后端抽象）。
注：文献 grounding 的 web search/本地 PDF 不属于此列（那是提议腿，非代码索引）。

## 13. 同类工作对比

| | deepwiki-open | CodeWiki | scicodewiki |
|---|---|---|---|
| 上下文策略 | RAG 向量索引 | AST+DP 分割，下游只传标识符 | agent 原生探索 + 调用图 grounding |
| 生成 | LLM 起草 TOC + 逐节 RAG 生成 | 递归 bottom-up multi-agent | 代码层递归叙事；公式层提议+机械门 |
| 形态 | web 服务（FastAPI+Next.js）+ chat | CLI + 静态产物 | 仓库原生 + 开放标准 skill pack |
| 验证 | 无 | LLM judge（CodeWikiBench） | 机械门 + verdict 记录 |
| 公式 | 无 | 无 | 注册表驱动 |
| 许可/热度 | MIT，17.6k stars | MIT，研究产物 | MIT（本品） |

deepwiki-open 的 17.6k stars = "开源本地 repo wiki" 需求的实证；
本品差异化 = 验证层，恰为两者共同缺失的维度。
