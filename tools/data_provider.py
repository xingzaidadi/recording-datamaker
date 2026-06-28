#!/usr/bin/env python3
"""
测试数据池 + 单号生成器

提供默认测试数据、单号规则生成、金额计算等能力。
用于 ai-dataforge-loop 录制保障模式下的数据造数流程。
"""

import os
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any

# ============================================================
# 默认测试数据（ZNB 普通物料采购申请）
# ============================================================

DEFAULT_SCENE: Dict[str, Any] = {
    "sceneType": "ZNB",
    "sceneName": "普通采购 PRPO 造数",
    "stockOrg": "MI_IOT",
    "stockOrgCN": "生态链",
    "purchaseOrg": "2120",
    "purchaseOrgCN": "生态链采购组织",
    "supplierCode": "108062",
    "supplierName": "威海市泓淋电力技术股份有限公司",
    "projectCode": "EcoOdmJdm20240708220947-EU",
    "shipLocCode": "129797",
    "shipLocName": "深圳发货地点",
    "currency": "CNY",
    "materials": [
        {
            "materialCode": "1710301000006A",
            "materialName": "生态链结构件_注塑件_注塑件_1_4 Kg_4_STL001_1234990_Longcheer",
            "quantity": 10000,
            "unitPrice": 18.50,
            "unit": "PC"
        },
        {
            "materialCode": "1710301000006B",
            "materialName": "生态链结构件_注塑件_注塑件_1_4 Kg_4_STL001_3443231_Longcheer",
            "quantity": 10000,
            "unitPrice": 22.00,
            "unit": "PC"
        }
    ]
}

# ============================================================
# 单号生成器
# ============================================================

class NumberGenerator:
    """单号生成器，按规则生成 Run ID / PR / BPM / PO / ERP 单号"""

    _seq_counters: Dict[str, int] = {}

    @classmethod
    def _next_seq(cls, prefix: str) -> int:
        """获取下一个序号"""
        if prefix not in cls._seq_counters:
            cls._seq_counters[prefix] = 0
        cls._seq_counters[prefix] += 1
        return cls._seq_counters[prefix]

    @classmethod
    def reset(cls):
        """重置所有序号计数器"""
        cls._seq_counters.clear()

    @classmethod
    def run_id(cls, date_str: Optional[str] = None) -> str:
        """生成 Run ID: RUN{YYYYMMDD}{seq}"""
        if date_str is None:
            date_str = datetime.now().strftime("%Y%m%d")
        seq = cls._next_seq("RUN")
        return f"RUN{date_str}{seq:04d}"

    @classmethod
    def pr_number(cls, date_str: Optional[str] = None) -> str:
        """生成 PR 单号: 84{MM}{DD}{seq:04d}（如 8440027538）"""
        if date_str is None:
            date_str = datetime.now().strftime("%Y%m%d")
        now = datetime.strptime(date_str, "%Y%m%d")
        mm = now.strftime("%m")
        dd = now.strftime("%d")
        seq = cls._next_seq("PR")
        return f"84{mm}{dd}{seq:04d}"

    @classmethod
    def bpm_number(cls, date_str: Optional[str] = None) -> str:
        """生成 BPM 审批单号: BPM{YYYYMMDD}{seq}"""
        if date_str is None:
            date_str = datetime.now().strftime("%Y%m%d")
        seq = cls._next_seq("BPM")
        return f"BPM{date_str}{seq:04d}"

    @classmethod
    def bpm_po_number(cls, date_str: Optional[str] = None) -> str:
        """生成 PO 审批 BPM 单号: BPM{YYYYMMDD}{seq}-PO"""
        if date_str is None:
            date_str = datetime.now().strftime("%Y%m%d")
        seq = cls._next_seq("BPM-PO")
        return f"BPM{date_str}{seq:04d}-PO"

    @classmethod
    def po_number(cls, date_str: Optional[str] = None) -> str:
        """生成 PO 单号: 60{MMDD}{seq:04d}（如 6000142883 → 6006280001）"""
        if date_str is None:
            date_str = datetime.now().strftime("%Y%m%d")
        now = datetime.strptime(date_str, "%Y%m%d")
        mmdd = now.strftime("%m%d")
        seq = cls._next_seq("PO")
        return f"60{mmdd}{seq:04d}"

    @classmethod
    def erp_number(cls, date_str: Optional[str] = None) -> str:
        """生成 ERP 单号: 45{MM}{seq:06d}（如 4500233605）"""
        if date_str is None:
            date_str = datetime.now().strftime("%Y%m%d")
        now = datetime.strptime(date_str, "%Y%m%d")
        mm = now.strftime("%m")
        seq = cls._next_seq("ERP")
        return f"45{mm}{seq:06d}"


# ============================================================
# 金额计算
# ============================================================

def calc_total_amount(materials: list) -> float:
    """计算物料总金额"""
    total = 0.0
    for m in materials:
        qty = m.get("quantity", 0)
        price = m.get("unitPrice", 0.0)
        total += qty * price
    return round(total, 2)


def format_currency(amount: float, currency: str = "CNY") -> str:
    """格式化金额显示"""
    if currency == "CNY":
        return f"¥{amount:,.2f} CNY"
    elif currency == "USD":
        return f"${amount:,.2f} USD"
    else:
        return f"{currency} {amount:,.2f}"


# ============================================================
# 截图参数合并
# ============================================================

def merge_screenshot_params(screenshot_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    将截图识别的参数与默认数据合并。
    截图参数优先，缺失字段从默认数据补齐。
    """
    merged = json.loads(json.dumps(DEFAULT_SCENE))  # deep copy

    # 覆盖顶层字段
    for key in ["sceneType", "sceneName", "stockOrg", "stockOrgCN",
                "purchaseOrg", "purchaseOrgCN", "supplierCode", "supplierName",
                "projectCode", "shipLocCode", "shipLocName", "currency"]:
        if key in screenshot_params and screenshot_params[key]:
            merged[key] = screenshot_params[key]

    # 覆盖物料列表
    if "materials" in screenshot_params and screenshot_params["materials"]:
        merged["materials"] = screenshot_params["materials"]

    return merged


# ============================================================
# 获取完整场景数据
# ============================================================

def get_default_scene() -> Dict[str, Any]:
    """获取默认测试场景数据（深拷贝）"""
    return json.loads(json.dumps(DEFAULT_SCENE))


def prepare_execution_data(scene: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    准备执行数据：将场景数据与单号、金额合并为完整执行上下文。
    """
    if scene is None:
        scene = get_default_scene()

    now = datetime.now()
    date_str = now.strftime("%Y%m%d")

    materials = scene.get("materials", [])
    total_amount = calc_total_amount(materials)

    run_id = NumberGenerator.run_id(date_str)
    pr_no = NumberGenerator.pr_number(date_str)
    bpm_no = NumberGenerator.bpm_number(date_str)
    po_no = NumberGenerator.po_number(date_str)
    bpm_po_no = NumberGenerator.bpm_po_number(date_str)
    erp_no = NumberGenerator.erp_number(date_str)

    return {
        "runId": run_id,
        "dateStr": date_str,
        "scene": scene,
        "totalAmount": total_amount,
        "totalAmountFormatted": format_currency(total_amount, scene.get("currency", "CNY")),
        "prNumber": pr_no,
        "bpmNumber": bpm_no,
        "poNumber": po_no,
        "bpmPoNumber": bpm_po_no,
        "erpNumber": erp_no,
        "materialCount": len(materials),
    }


# ============================================================
# 预检数据
# ============================================================

PRE_CHECK_ITEMS = [
    {"key": "supplierRelation", "label": "供应商物料关系验证", "detail": "关系有效", "passed": True},
    {"key": "aslRelation", "label": "ASL 关系验证", "detail": "物料已维护 ASL", "passed": True},
    {"key": "feePnBinding", "label": "费用 PN 绑定", "detail": "费用 PN 已绑定", "passed": True},
    {"key": "feeConfig", "label": "费用项配置", "detail": "费用项有效", "passed": True},
    {"key": "pricingStatus", "label": "定价单状态", "detail": "物料 1710301000006A 定价单缺失，需补充", "passed": False},
    {"key": "orgProjectMapping", "label": "组织与项目映射", "detail": "组织项目关系正确", "passed": True},
]

# 前置检查发现的问题 → 触发数据清洗
PRE_CHECK_ISSUES = [
    "物料 1710301000006A 缺少有效定价单",
    "供应商 108062 在采购组织 2120 下的价格信息未维护",
]

DATA_CLEAN_ITEMS = [
    {"label": "物料主数据有效", "status": True},
    {"label": "供应商状态正常", "status": True},
    {"label": "采购组织权限已分配", "status": True},
    {"label": "价格信息有效", "status": True},
    {"label": "项目预算充足", "status": True},
]

APPROVAL_FLOW_PR = ["发起", "主管审批", "采购经理审批"]
APPROVAL_FLOW_PO = ["发起", "主管审批", "采购经理审批", "财务审批"]


if __name__ == "__main__":
    data = prepare_execution_data()
    print(f"Run ID: {data['runId']}")
    print(f"PR: {data['prNumber']}")
    print(f"BPM: {data['bpmNumber']}")
    print(f"PO: {data['poNumber']}")
    print(f"BPM-PO: {data['bpmPoNumber']}")
    print(f"ERP: {data['erpNumber']}")
    print(f"Total: {data['totalAmountFormatted']}")
    print(f"Materials: {data['materialCount']}")
