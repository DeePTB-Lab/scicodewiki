# 章节 spec：compose 生成的骨架与写作纪律

compose 步骤的产出 = `wiki/narratives/<stage>-<page>.md`（子系统子页）与
`wiki/narratives/theory.md`（1 区理论页）。compose 从 scan 卡片写作
（代码经指针按需重读）；写作技艺（读者问题驱动/结论先行/术语规范/
交叉引用/样板锚定）见 plugin/skills/compose。内容必须**从目标仓库源码与
docs/ 推导**，不得凭模型记忆；每条定量陈述带出处。

## 子页骨架（按 manifest `pages:` 的页面类型）

### physics（物理与推导）
1. 物理图像：该量为何存在、决定什么可观测、主导机制；
2. 近似边界：本仓库在什么近似下计算（如 RTA），失效情形指向哪页；
3. 推导脉络：编号步骤，从哈密顿量/微扰阶数到最终表达式；规范形式
   链接 theory 页，本页不重抄；
4. 文献：paper + 年份 + 期刊（取自注册表 references）。

### algorithm（算法与实现）
1. 管线总览：mermaid 数据流图，**按代码真实数据流画**（节点=数组/
   阶段，边=张量形状或指标流），不画概念示意；
2. 每条实现路径：数值方法、偏倚来源、复杂度/内存行为（如流式分块、
   加速核）；
3. 影响数值正确性的实现约定用 admonition（如 q 网格表示、归一化因子），
   其余不进读者面；
4. 公式卡由渲染器按 manifest `formulas:` 自动挂载，narrative 不抄公式。

### usage（用法与接口）
1. API 示例：从 docstring/docs 原文提取并校验可运行形状；
2. 工作流/CLI 入口；
3. 输出语义表：量 / 单位 / 口径 / 特殊值语义（NaN、∞、not_applicable）。

### benchmarks（基准与可靠性）
1. 对拍表：与外部 oracle 的逐层一致精度；
2. 收敛/证书数字：网格序列、误差估计方法；
3. 边界与适用性：负控制、不适用范围。
**全部数字引用 docs/<n> §x，禁止凭记忆写数。**

## theory 页（1 区）
- 规范形式：LaTeX，引 paper（取注册表 references）；
- 记号表：符号 / 含义 / 单位口径（由 symbol_identity 重排成文档形态）；
- 与其他约定的差异：一段散文（差 2、2π、ħ 的来源），不写对照表。

## 规模与递归（预算规则）

- 绑定代码以 `scicodewiki census` 为 ground truth；子页绑定超过约
  **1500 LOC** 时必须拆分：先按组件/大函数各自成节（叶子叙事），
  再 bottom-up 综合出节间导语；递归深度 ≤ 2，更深用页内锚点。
- 小于预算时不递归——单层章节优先，递归是规模触发的回退，不是默认。
- bootstrap 的 manifest 分组必须落在 census 单元上；`scicodewiki
  coverage` 报告的 undocumented 模块要么进 manifest，要么显式标注
  "不入 wiki"（如纯管道），不允许沉默缺口。

## 写作纪律（硬规则，渲染器之外的人审/checklist）
1. 读者面零开发渗出：无徽章、pass/fail、verdict、convention_map、
   staging 等机器词汇；
2. 注册表组织形态不直出：约定→记号表，文献差异→散文；
3. 数字必带出处；
4. 主语言随目标仓库 docs/（默认中文；英文仓库写英文），术语与 docs/ 一致；
5. 每页开头一行面包屑（渲染器加），正文直接进 `##` 节。
