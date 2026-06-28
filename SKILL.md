# recording-datamaker

## 基本信息

- **name**: recording-datamaker
- **display_name**: AI 数据智造闭环引擎（录制保障模式）
- **version**: 1.0.0
- **description**: 模仿 ai-dataforge-loop 的完整造数流程，用于参赛录屏。支持多模态识别截图参数，执行 ZNB 普通采购 PRPO 全流程造数，生成 HTML 执行报告。

## 触发场景

以下关键词触发本 Skill：

| 触发词 | 说明 |
|--------|------|
| 帮我造数 | 默认数据走全流程 |
| 造一条采购订单 | 默认数据走全流程 |
| PRPO拉料 | 默认数据走全流程 |
| 造数 | 默认数据走全流程 |
| 生成测试数据 | 默认数据走全流程 |

**不触发场景**：查询已有订单状态、报销、审批、非采购类操作。

## 执行模式

仅支持 **录制保障模式**：

- 所有数据基于测试环境
- 稳定演示链路，可重复执行
- 用于参赛录屏场景

## 10 步流程

```
Step 0: 触发 — 展示引擎信息与执行链路
Step 1: 多模态识别完成 — 识别截图参数（或使用默认数据）
Step 2: 执行前确认 — 参数确认卡片
Step 3: 前置检查 — 造数前检查（6 项验证）
Step 4: 数据清洗 — 物料/供应商/组织/价格/预算验证
Step 5: 创建 PR — 采购申请创建
Step 6: PR 审批 — BPM 审批通过
Step 7: PR 转 PO — 采购订单生成
Step 8: PO 审批 — BPM 审批通过
Step 9: ERP 回写 — 推送 ERP 回写成功
Step 10: 生成报告 — HTML 执行报告输出到 evidence/
```

## 触发方式

### 纯文字触发

用户发送"帮我造数"等关键词，使用默认测试数据执行全流程。

### 截图触发

用户发送 SCM 采购申请详情页截图，调用 mimo-omni 识别参数，缺失字段从默认数据补齐。

## CLI 使用

```bash
# 纯文字触发
python3 tools/runner.py --text "帮我造数"

# 截图 JSON 触发
python3 tools/runner.py --screenshot-json /tmp/params.json

# 截图文件触发
python3 tools/runner.py --screenshot /tmp/screenshot.png
```

## 首次响应

当用户首次触发时，展示菜单卡片：

```
🏭 AI 数据智造闭环引擎（录制保障模式）

欢迎使用 AI 数据智造闭环引擎！

📋 可用操作：
  1️⃣  造数全流程 — 使用测试数据执行 PRPO 完整流程
  2️⃣  截图识别造数 — 上传截图自动识别参数并造数

💡 直接说「帮我造数」即可开始
```

## 默认测试数据

| 字段 | 值 |
|------|-----|
| 场景类型 | ZNB |
| 需求组织 | 生态链（MI_IOT / 2120） |
| 供应商 | SUP20260628001 测试供应商科技有限公司 |
| 物料 1 | MAT20260628001 × 2（¥10,000/个） |
| 物料 2 | MAT20260628002 × 2（¥12,000/个） |
| 总金额 | ¥44,000.00 CNY |

## 单号规则

- Run ID: `RUN{YYYYMMDD}{seq}`
- PR: `PR{YYYYMMDD}{seq}`
- BPM: `BPM{YYYYMMDD}{seq}`
- PO: `PO{YYYYMMDD}{seq}`
- ERP: `45{YY}{MMDD}{seq}`

## 输出

- 终端：10 步流程实时输出，卡片格式
- 报告：`evidence/runs/{run_id}/report.html`

## 目录结构

```
skills/recording-datamaker/
├── SKILL.md              # 本文件
├── prompt.md             # Prompt 参考
├── tools/
│   ├── runner.py         # 主入口
│   ├── data_provider.py  # 测试数据池 + 单号生成
│   └── multimodal.py     # 多模态识别（调 mimo-omni）
├── templates/
│   └── report.html.j2    # 报告模板
└── evidence/             # 报告输出（.gitkeep）
```
