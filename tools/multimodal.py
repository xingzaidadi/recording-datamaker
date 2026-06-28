#!/usr/bin/env python3
"""
多模态识别模块

调用 mimo-omni 识别截图，提取 SCM 采购申请详情页参数。
识别结果与默认数据合并后返回完整参数。
"""

import os
import json
import subprocess
import sys
from typing import Optional, Dict, Any, Tuple

# mimo-omni 脚本路径
MIMO_OMNI_SCRIPT = os.path.expanduser(
    "~/.openclaw/plugin-skills/mimo-omni/scripts/mimo_api.py"
)

# 识别提示词模板
RECOGNITION_PROMPT = """请识别这张 SCM 采购申请详情页截图，提取以下参数并以 JSON 格式返回：
{
  "sceneType": "场景类型（如 ZNB）",
  "sceneName": "场景名称",
  "stockOrg": "库存组织代码",
  "stockOrgCN": "库存组织中文名",
  "purchaseOrg": "采购组织代码",
  "purchaseOrgCN": "采购组织中文名",
  "supplierCode": "供应商编码",
  "supplierName": "供应商名称",
  "projectCode": "项目编号",
  "shipLocCode": "发货地点编码",
  "shipLocName": "发货地点名称",
  "currency": "币种",
  "materials": [
    {
      "materialCode": "物料编码",
      "materialName": "物料名称",
      "quantity": 数量,
      "unitPrice": 单价,
      "unit": "单位"
    }
  ]
}

请严格按照截图中实际显示的内容提取，如果某个字段在截图中无法识别，请设为 null。"""


class MultimodalRecognizer:
    """多模态识别器，调用 mimo-omni 识别截图参数"""

    def __init__(self):
        self._omni_available = os.path.exists(MIMO_OMNI_SCRIPT)

    def is_available(self) -> bool:
        """检查 mimo-omni 是否可用"""
        return self._omni_available

    def recognize_from_image(self, image_path: str, timeout: int = 120) -> Dict[str, Any]:
        """
        从图片路径识别参数。

        Args:
            image_path: 截图文件路径
            timeout: 超时时间（秒）

        Returns:
            识别出的参数字典
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"截图文件不存在: {image_path}")

        if not self._omni_available:
            print("⚠️  mimo-omni 脚本不可用，使用默认数据")
            return {}

        prompt_file = self._write_temp_prompt()

        try:
            cmd = [
                sys.executable,
                MIMO_OMNI_SCRIPT,
                "image",
                image_path,
                f"$(cat {prompt_file})",
                "--timeout", str(timeout)
            ]
            # 使用 shell=True 以便 $(cat ...) 语法生效
            result = subprocess.run(
                " ".join(cmd),
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout + 30
            )

            if result.returncode != 0:
                print(f"⚠️  mimo-omni 调用失败: {result.stderr}")
                return {}

            # 解析返回结果
            return self._parse_omni_response(result.stdout)

        except subprocess.TimeoutExpired:
            print(f"⚠️  mimo-omni 调用超时（{timeout}s）")
            return {}
        except Exception as e:
            print(f"⚠️  mimo-omni 调用异常: {e}")
            return {}
        finally:
            self._cleanup_temp_prompt(prompt_file)

    def recognize_from_json(self, screenshot_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        从已有 JSON 数据提取参数（截图已被预处理的情况）。

        Args:
            screenshot_json: 预处理后的截图 JSON

        Returns:
            参数字典
        """
        # 直接返回，由调用方做合并
        return screenshot_json

    def _write_temp_prompt(self) -> str:
        """写入临时提示词文件"""
        import tempfile
        fd, path = tempfile.mkstemp(suffix=".txt", prefix="mimo_prompt_")
        with os.fdopen(fd, "w") as f:
            f.write(RECOGNITION_PROMPT)
        return path

    def _cleanup_temp_prompt(self, path: str):
        """清理临时提示词文件"""
        try:
            if path and os.path.exists(path):
                os.unlink(path)
        except OSError:
            pass

    def _parse_omni_response(self, raw_output: str) -> Dict[str, Any]:
        """
        解析 mimo-omni 返回的原始输出，提取 JSON 参数。

        mimo-omni 可能返回包含 JSON 的文本，需要提取其中的 JSON 部分。
        """
        output = raw_output.strip()

        # 尝试直接解析整个输出为 JSON
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            pass

        # 尝试提取 ```json ... ``` 代码块
        import re
        json_block = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", output, re.DOTALL)
        if json_block:
            try:
                return json.loads(json_block.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试提取 { ... } 部分
        brace_match = re.search(r"\{.*\}", output, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass

        print(f"⚠️  无法解析 mimo-omni 输出为 JSON，将使用默认数据")
        return {}


# ============================================================
# 统一识别入口
# ============================================================

def recognize_params(
    screenshot_path: Optional[str] = None,
    screenshot_json: Optional[Dict[str, Any]] = None
) -> Tuple[Dict[str, Any], bool]:
    """
    统一参数识别入口。

    Args:
        screenshot_path: 截图文件路径（如有）
        screenshot_json: 截图 JSON 数据（如有）

    Returns:
        (识别出的参数, 是否使用了默认数据)
    """
    recognizer = MultimodalRecognizer()

    if screenshot_json:
        params = recognizer.recognize_from_json(screenshot_json)
        return params, False

    if screenshot_path:
        params = recognizer.recognize_from_image(screenshot_path)
        if params:
            return params, False
        else:
            return {}, True

    return {}, True


if __name__ == "__main__":
    # 测试
    recognizer = MultimodalRecognizer()
    print(f"mimo-omni available: {recognizer.is_available()}")

    params, is_default = recognize_params()
    print(f"Default data: {is_default}")
    print(f"Params: {json.dumps(params, ensure_ascii=False, indent=2)}")
