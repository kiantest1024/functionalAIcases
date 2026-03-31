#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
严格的AI测试用例生成器 - 完全基于功能点生成
确保每个测试用例都按照模板要求生成
"""

import json
import re
import datetime
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from .test_case_generator import TestCase, Priority, TestMethod
from .real_ai_generator import AIProvider


def _extract_balanced_json_container(text: str) -> Optional[str]:
    """
    截取第一个与 [...] 或 {...} 平衡的 JSON 片段，字符串内的 [ ] { } 不计入。
    避免用 rfind(']') 时误把 expected 里的列表（如 [0.5, 1, 2, 1000]）当成数组结尾而截断。
    """
    start = -1
    for i, c in enumerate(text):
        if c in "[{":
            start = i
            break
    if start < 0:
        return None
    stack: List[str] = []
    pair = {"[": "]", "{": "}"}
    in_string = False
    escape_next = False
    n = len(text)
    i = start
    while i < n:
        c = text[i]
        if in_string:
            if escape_next:
                escape_next = False
            elif c == "\\":
                escape_next = True
            elif c == '"':
                in_string = False
            i += 1
            continue
        if c == '"':
            in_string = True
            i += 1
            continue
        if c in "[{":
            stack.append(pair[c])
        elif c in "}]":
            if not stack or stack[-1] != c:
                return None
            stack.pop()
            if not stack:
                return text[start : i + 1]
        i += 1
    return None


def _comma_followed_by_json_field_separator(s: str, comma_idx: int) -> bool:
    """
    判断逗号是否为 JSON 对象里「字段之间」的分隔（后是 \"key\":）。
    用于区分英文标点，例如 Upon clicking \"PLAY\", the game 里的逗号不是 JSON 分隔符。
    """
    j = comma_idx + 1
    n = len(s)
    while j < n and s[j].isspace():
        j += 1
    if j >= n:
        return True
    if s[j] != '"':
        return False
    j += 1
    escape_next = False
    while j < n:
        c = s[j]
        if escape_next:
            escape_next = False
            j += 1
            continue
        if c == "\\":
            escape_next = True
            j += 1
            continue
        if c == '"':
            j += 1
            break
        j += 1
    else:
        return False
    while j < n and s[j].isspace():
        j += 1
    return j < n and s[j] == ":"


def _is_json_string_value_closer(s: str, close_idx: int) -> bool:
    """若 s[close_idx] 为双引号，判断其是否为当前 JSON 字符串 token 的结束（键名或值的结束引号）。"""
    j = close_idx + 1
    n = len(s)
    while j < n and s[j].isspace():
        j += 1
    if j >= n:
        return True
    ch = s[j]
    if ch in ":}]":
        return True
    if ch == ",":
        return _comma_followed_by_json_field_separator(s, j)
    return False


def _escape_interior_quotes_json(text: str) -> str:
    """
    将 LLM 在 JSON 字符串值内错误使用的双引号转义为 \"。
    典型错误：Click the "BET" button、user"s balance（未写成 \\"）。
    """
    out: List[str] = []
    i, n = 0, len(text)
    in_string = False
    escape_next = False
    while i < n:
        c = text[i]
        if not in_string:
            out.append(c)
            if c == '"':
                in_string = True
            i += 1
            continue
        if escape_next:
            out.append(c)
            escape_next = False
            i += 1
            continue
        if c == "\\":
            out.append(c)
            escape_next = True
            i += 1
            continue
        if c == '"':
            if _is_json_string_value_closer(text, i):
                out.append(c)
                in_string = False
            else:
                out.append("\\")
                out.append('"')
            i += 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _try_llm_json_repair(text: str) -> Optional[str]:
    """使用 json-repair 库修复 LLM 常见 JSON 错误（可选依赖）。"""
    try:
        from json_repair import repair_json
    except ImportError:
        return None
    try:
        out = repair_json(text)
        return out if isinstance(out, str) else None
    except Exception:
        return None


@dataclass
class FunctionPoint:
    """功能点"""
    id: int
    description: str
    module: str = "AI生成模块"
    submodule: str = "AI生成子模块"


def _clip(s: str, n: int) -> str:
    s = (s or "").strip()
    return s if len(s) <= n else s[: n - 20] + "\n…(已截断)…"


def _split_function_point_line(line: str) -> tuple:
    """
    解析「模块 | 子模块 | 功能点」或 Tab 分隔；若无分隔符则整行作为功能点描述。
    返回 (module, submodule, description) 其中 module/submodule 可能为空字符串。
    """
    raw = line.strip()
    if "\t" in raw:
        parts = [p.strip() for p in raw.split("\t", 2)]
    elif raw.count("|") >= 2:
        parts = [p.strip() for p in raw.split("|", 2)]
    else:
        return "", "", raw
    if len(parts) >= 3:
        return parts[0], parts[1], parts[2]
    if len(parts) == 2:
        return parts[0], "", parts[1]
    return "", "", parts[0] if parts else raw


class StrictAITestGenerator:
    """严格的AI测试用例生成器"""
    
    def __init__(self, ai_api_caller=None, language='zh'):
        """
        初始化生成器
        Args:
            ai_api_caller: AI API调用函数，应接受prompt参数并返回字符串响应
            language: 测试用例生成语言 ('zh' 或 'en')
        """
        self.ai_api_caller = ai_api_caller
        self.test_cases: List[TestCase] = []
        self.function_points: List[FunctionPoint] = []
        self.language = language  # 存储语言设置
        self._refined_requirement_brief: str = ""  # 生成前 AI 梳理的需求摘要，供写用例时使用
        self._historical_defects: str = ""
        self._iteration_context: str = ""
        self._code_change_summary: str = ""
        self._test_mindmap_table: str = ""
        
        # 如果AI API可用，验证配置
        if ai_api_caller:
            try:
                # 测试调用
                print(f"✅ AI API调用器已配置 (语言: {language})")
            except Exception as e:
                print(f"⚠️ AI API调用器配置异常: {e}")
                self.ai_api_caller = None
    
    def generate_test_cases(
        self,
        requirement_text: str,
        progress_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        partial_results_callback: Optional[Callable[[List[TestCase]], None]] = None,
        historical_defects: Optional[str] = None,
        iteration_context: Optional[str] = None,
        code_change_summary: Optional[str] = None,
    ) -> List[TestCase]:
        """
        严格按照要求生成测试用例
        
        流程：
        1. 提取功能点
        2. （可选）AI 梳理需求摘要
        3. 为每个功能点生成测试用例
        4. 严格格式验证和修正
        
        Args:
            requirement_text: 需求文档内容
            progress_callback: 可选回调 (event, payload)，event 含
                after_extract, refine_start, refine_done, function_point_start, function_point_done, validating_start
            partial_results_callback: 每完成一个功能点后回调当前已累积的 TestCase 列表（用于中断时落盘）
            historical_defects: 历史缺陷/故障列表（文本），用于错误推测与负面清单
            iteration_context: 迭代说明、旧版核心功能摘要、变更范围等（可选）
            code_change_summary: 本次代码变更/Git Diff 摘要（可选，便于分支与影响分析）
        
        Returns:
            List[TestCase]: 格式正确的测试用例列表
        """
        self._historical_defects = (historical_defects or "").strip()
        self._iteration_context = (iteration_context or "").strip()
        self._code_change_summary = (code_change_summary or "").strip()
        self._test_mindmap_table = ""

        print("=" * 80)
        print("🚀 开始严格AI测试用例生成")
        print("=" * 80)
        
        # 步骤1: 提取功能点
        self.function_points = self._extract_function_points(requirement_text)
        
        if not self.function_points:
            print("❌ 未能提取到功能点，无法生成测试用例")
            return []
        
        print(f"\n📋 成功提取 {len(self.function_points)} 个功能点:")
        for fp in self.function_points:
            print(f"   {fp.id}. {fp.description}")
        
        if progress_callback:
            progress_callback("after_extract", {"count": len(self.function_points)})
        
        self._refined_requirement_brief = ""
        if self.ai_api_caller:
            print("\n📚 正在梳理需求文档（先理顺业务再编写用例）...")
            if progress_callback:
                progress_callback("refine_start", {})
            self._refined_requirement_brief = self._refine_requirement_for_generation(requirement_text)
            print(f"   ✅ 需求梳理完成（约 {len(self._refined_requirement_brief)} 字）")
            if progress_callback:
                progress_callback("refine_done", {"length": len(self._refined_requirement_brief)})

        # 步骤1b: 测试点思维导图（结构化梳理，再展开详细用例）
        if self.ai_api_caller:
            print("\n🧠 正在生成测试点思维导图（ISTQB 多维度梳理）...")
            if progress_callback:
                progress_callback("mindmap_start", {})
            self._test_mindmap_table = self._generate_test_point_mindmap(requirement_text)
            if progress_callback:
                progress_callback(
                    "mindmap_done",
                    {"length": len(self._test_mindmap_table or "")},
                )
            print(f"   ✅ 思维导图完成（约 {len(self._test_mindmap_table or '')} 字）")
        
        # 步骤2: 为每个功能点生成测试用例
        all_test_cases = []
        n_fp = len(self.function_points)
        for idx, fp in enumerate(self.function_points, 1):
            if progress_callback:
                progress_callback(
                    "function_point_start",
                    {"index": idx, "total": n_fp, "description": fp.description},
                )
            print(f"\n🎯 正在为功能点 [{fp.description}] 生成测试用例...")
            cases = self._generate_cases_for_function_point(fp, requirement_text)
            all_test_cases.extend(cases)
            print(f"   ✅ 生成了 {len(cases)} 个测试用例")
            if partial_results_callback and all_test_cases:
                partial_results_callback(list(all_test_cases))
            if progress_callback:
                progress_callback(
                    "function_point_done",
                    {"index": idx, "total": n_fp, "description": fp.description, "cases": len(cases)},
                )
        
        # 步骤3: 严格格式验证
        print(f"\n🔧 开始格式验证和修正...")
        if progress_callback:
            progress_callback("validating_start", {"total_cases": len(all_test_cases)})
        validated_cases = self._validate_and_fix_all_cases(all_test_cases)
        if partial_results_callback and validated_cases:
            partial_results_callback(list(validated_cases))
        
        self.test_cases = validated_cases
        print(f"\n✅ 最终生成 {len(validated_cases)} 个符合规范的测试用例")
        print("=" * 80)
        
        return validated_cases
    
    def _extract_function_points(self, requirement_text: str) -> List[FunctionPoint]:
        """提取功能点（根据需求规模自适应数量）"""
        if not self.ai_api_caller:
            return self._extract_function_points_local(requirement_text)
        
        # 根据需求长度和复杂度决定提取数量上限
        max_function_points = self._calculate_max_function_points(requirement_text)
        
        if self.language == "en":
            prompt = f"""
You are a senior test architect (ISTQB, destructive mindset). Extract **all testable function points** from the requirement.

【Requirement】
{requirement_text}

【Rules】
1. Each line MUST follow: `Module | Submodule | Function point summary` (use " | " with spaces).
   - Module/Submodule: short English names from the **actual domain** of this document (e.g. Order Checkout, Payment, Admin RBAC). Never use generic placeholders like "Game Management".
2. Part 3 = one concrete, verifiable point (behavior, API rule, state transition, permission, UI correctness).
3. Include implicit rules, state machines, validations, data constraints where applicable.
4. If APIs/schemas exist, add points for field type/length/required/enums.
5. Keep part 3 concise (prefer < 100 chars). One point per line.
6. Do not number lines; no extra commentary.

【Output】
Lines only, format: Module | Submodule | Function point summary
"""
        else:
            prompt = f"""
你是一名遵循 ISTQB、具备破坏性思维、熟悉业务上下文的资深测试架构师。请从需求中拆解并提取**全部可测试功能点**（先理解全貌再枚举）。

【需求内容】
{requirement_text}

【提取规则】
1. **每行必须严格使用格式**：`模块 | 子模块 | 功能点简述`（竖线两侧建议各有一个空格）。
   - 模块、子模块须依据**本文档真实业务域**命名（如「订单」「支付回调」「权限管理」），禁止使用与需求无关的占位词（如泛泛的「游戏管理」）。
2. 第 3 段为一条独立、可验证的功能点（行为、接口规则、状态转移、权限、UI 正确性等）。
3. 覆盖显性功能、隐性规则、接口字段约束等；每行一条，勿合并。
4. 第 3 段建议不超过 100 字。
5. 不要编号，不要段落说明。

【输出格式】
仅输出多行文本，每行：模块 | 子模块 | 功能点简述
"""
        
        try:
            response = self.ai_api_caller(prompt)
            lines = response.strip().split('\n')
            
            function_points = []
            for i, line in enumerate(lines, 1):
                line = line.strip().lstrip('-*•· ').strip()
                line = re.sub(r'^\d+[\.\)、]\s*', '', line)
                if not line:
                    continue
                mod_guess, sub_guess, desc = _split_function_point_line(line)
                if not desc or len(desc) < 3:
                    continue
                if len(desc) > 220:
                    desc = desc[:217] + "..."
                exclude_plain = [
                    '示例', '说明', '注意', '提取', '需求', '输出格式', '功能点', '以下', '如下', 'figma', 'Figma',
                ]
                if '|' not in line and any(kw in line for kw in exclude_plain):
                    continue
                low = line.lower()
                if '|' in line and (
                    low.startswith('module |')
                    or low.startswith('module|')
                    or ('submodule' in low[:50] and 'summary' in low)
                    or ('子模块' in line[:40] and ('简述' in line or '功能点' in line[:20]))
                ):
                    continue
                if mod_guess and sub_guess:
                    module, submodule = mod_guess[:80], sub_guess[:80]
                else:
                    module, submodule = self._guess_module_from_text(desc, requirement_text)
                fp = FunctionPoint(
                    id=i,
                    description=desc,
                    module=module,
                    submodule=submodule,
                )
                function_points.append(fp)
            
            # 去重
            seen = set()
            unique_fps = []
            for fp in function_points:
                if fp.description not in seen:
                    seen.add(fp.description)
                    unique_fps.append(fp)
            
            # 返回所有提取到的功能点，不做数量限制
            print(f"✅ 成功提取 {len(unique_fps)} 个功能点（无上限限制）")
            return unique_fps
            
        except Exception as e:
            print(f"⚠️ AI提取失败: {e}，使用本地提取")
            return self._extract_function_points_local(requirement_text)
    
    def _extract_function_points_local(self, requirement_text: str) -> List[FunctionPoint]:
        """本地关键词匹配提取功能点"""
        function_points = []
        
        action_keywords = ['查看', '显示', '切换', '创建', '添加', '删除', '修改',
                          '检测', '弹', '恢复', '支持', '加载', '刷新', '保存']
        
        lines = requirement_text.split('\n')
        fp_id = 1
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 5:
                continue
            
            for keyword in action_keywords:
                if keyword in line:
                    sub_sentences = line.replace('。', '|').replace('；', '|').split('|')
                    for sub in sub_sentences:
                        sub = sub.strip()
                        if keyword in sub and 5 < len(sub) < 80:
                            sub = re.sub(r'^\d+[\.\)、]\s*', '', sub).strip()
                            
                            module, submodule = self._guess_module_from_text(sub, requirement_text)
                            fp = FunctionPoint(
                                id=fp_id,
                                description=sub,
                                module=module,
                                submodule=submodule
                            )
                            function_points.append(fp)
                            fp_id += 1
                    break
        
        # 去重
        seen = set()
        unique_fps = []
        for fp in function_points:
            if fp.description not in seen:
                seen.add(fp.description)
                unique_fps.append(fp)
        
        # 返回所有提取到的功能点，不做数量限制
        print(f"✅ 本地提取到 {len(unique_fps)} 个功能点（无上限限制）")
        return unique_fps
    
    def _guess_module_from_text(self, text: str, full_requirement: str) -> tuple:
        """从文本与需求摘录猜测模块和子模块（兜底，避免一律「游戏管理」）。"""
        blob = (text or "") + "\n" + (full_requirement or "")
        text_lower = blob.lower()

        if self.language == "en":
            module_map = {
                'order': ('Order', 'Flow'),
                'payment': ('Payment', 'Transaction'),
                'checkout': ('Checkout', 'Cart'),
                'login': ('Account', 'Authentication'),
                'register': ('Account', 'Sign up'),
                'admin': ('Admin', 'Console'),
                'permission': ('Security', 'RBAC'),
                'api': ('API', 'Contract'),
                'upload': ('Content', 'Upload'),
                'search': ('Search', 'Query'),
            }
            for keyword, pair in module_map.items():
                if keyword in text_lower:
                    return pair
            title = self._first_requirement_title_line(full_requirement)
            if title:
                return (title[:40], "Feature verification")
            return ("Requirement scope", "Functional verification")

        module_map = {
            '菜单': ('界面', '菜单'),
            '游戏': ('业务', '游戏玩法'),
            '订单': ('订单', '交易流程'),
            '支付': ('支付', '收单'),
            '登录': ('账号', '登录认证'),
            '注册': ('账号', '注册'),
            '权限': ('安全', '权限控制'),
            '接口': ('接口', '契约校验'),
            '设备': ('终端', '设备能力'),
            '横竖屏': ('显示', '屏幕方向'),
            '蒙版': ('界面', '蒙层'),
            '搜索': ('检索', '查询'),
        }
        for keyword, pair in module_map.items():
            if keyword in text_lower:
                return pair
        title = self._first_requirement_title_line(full_requirement)
        if title:
            return (title[:20], "功能验证")
        return ("需求范围", "功能验证")

    def _first_requirement_title_line(self, full_requirement: str) -> str:
        if not full_requirement:
            return ""
        for ln in full_requirement.strip().split("\n"):
            s = ln.strip().lstrip('#').strip()
            if 2 < len(s) < 60:
                return s
        return ""
    
    def _calculate_max_function_points(self, requirement_text: str) -> int:
        """
        分析需求规模（仅用于统计信息，不限制功能点数量）
        返回一个建议值用于日志记录，实际提取时不做限制
        """
        text_length = len(requirement_text.strip())
        line_count = len([line for line in requirement_text.split('\n') if line.strip()])
        
        action_keywords = ['查看', '显示', '切换', '创建', '添加', '删除', '修改',
                          '检测', '弹', '恢复', '支持', '加载', '刷新', '保存',
                          '选择', '输入', '配置', '计算', '验证', '匹配', '比较',
                          '排序', '筛选', '搜索', '提交', '发送', '接收', '进入']
        keyword_count = sum(1 for keyword in action_keywords if keyword in requirement_text)
        
        print(f"📊 需求规模分析: 文本{text_length}字, 行数{line_count}, 关键词{keyword_count}个")
        
        # 返回999999表示不限制（实际会返回所有提取到的功能点）
        return 999999
    
    def _refine_requirement_for_generation(self, requirement_text: str) -> str:
        """
        调用 AI 将原始需求整理为结构化摘要（纯文本），降低后续用例生成时理解偏差。
        失败时退回原文摘录，不阻断流程。
        """
        max_in = min(len(requirement_text), 32000)
        body = requirement_text[:max_in]
        if self.language == "en":
            prompt = f"""You are a senior business analyst and test architect (ISTQB-aligned). Read the requirement and output a structured plain-text summary for downstream test design.
Rules:
- Do NOT use JSON or markdown code fences.
- Numbered sections:
  (1) Overview & scope — explicit features vs implicit rules / assumptions
  (2) Core user flows & state machines (states, transitions, illegal jumps if mentioned)
  (3) Business rules — formulas, thresholds, validations, permission matrix (roles vs actions)
  (4) UI/UX — visual consistency (font, spacing, color vs spec), interaction feedback (loading, errors, empty), responsive breakpoints if any
  (5) APIs / data contracts — field types, lengths, required, enums, constraints (if present in text)
  (6) Cross-cutting impacts — upstream/downstream dependencies, data consistency
  (7) Iteration / regression hints — if the text describes deltas vs an existing system, list change points and impacted legacy areas
  (8) Edge cases, failures, security-sensitive areas (money, identity, PII)
- Keep proper nouns, numbers, and button/label names exactly as in the source.
- Be concise; include layout details when they affect correctness or accessibility.

=== REQUIREMENT ===
{body}

Output only the structured summary."""
        else:
            prompt = f"""你是资深需求分析师兼测试架构师视角（对齐 ISTQB 测试思维）。请阅读以下需求，输出结构化纯文本摘要，供后续设计黑盒/探索性测试用例使用。
规则：
- 不要使用 JSON、不要用 markdown 代码块。
- 分节编号输出：
  （1）概述与范围 — 显性功能 vs 隐性规则/假设
  （2）核心用户流程与状态机 — 状态、转移、非法跳转（若文档提及）
  （3）业务规则 — 计算公式、阈值、校验规则、权限矩阵（角色×操作）
  （4）界面与体验 — 视觉一致性（字体/间距/颜色与设计稿）、交互反馈（加载态/错误提示/空态）、响应式断点（若有）
  （5）接口与数据结构 — 字段类型、长度、必填、枚举、约束（若文档中有定义）
  （6）关联影响 — 上游/下游模块、数据一致性与同步
  （7）迭代与回归线索 — 若属增量迭代，列出变更点及可能影响的历史功能
  （8）异常、容错、安全敏感面（金额、身份、敏感数据脱敏等）
- 保留专有名词、数字、按钮/文案原文；与正确性相关的视觉规格需保留。

【原始需求】
{body}

只输出梳理结果。"""
        try:
            r = self.ai_api_caller(prompt)
            out = (r or "").strip()
            return out[:16000] if len(out) > 16000 else out
        except Exception as e:
            print(f"   ⚠️ 需求梳理失败，将使用原文摘录: {e}")
            return requirement_text[:8000]

    def _generate_test_point_mindmap(self, requirement_text: str) -> str:
        """
        在输出详细用例前，先生成测试点思维导图（Markdown 表格），便于模型自检覆盖率。
        """
        if not self.ai_api_caller:
            return ""
        refined = (self._refined_requirement_brief or "").strip()
        ctx = refined[:12000] if refined else requirement_text[:12000]
        iter_note = _clip(self._iteration_context, 4000)
        diff_note = _clip(self._code_change_summary, 6000)
        hist_note = _clip(self._historical_defects, 3000)

        if self.language == "en":
            prompt = f"""You are a senior test architect (ISTQB, ~20 years). **Do NOT output detailed test cases yet.**

First, produce a **test-point mind map** as a single **Markdown table** so reviewers can check coverage before case authoring.

Columns: Dimension | Focus | Key test ideas (bullet phrases) | Traceability (requirement fragment or section)

Rows MUST cover these dimensions (add rows if empty: write "N/A — not mentioned in doc"):
- UI look & feel (layout across resolutions, spacing/color vs design, control states: normal/disabled/hover/active)
- Functional logic (positive/negative, equivalence classes, boundary min-1/max+1)
- API validation (types, length, required, enums) — if applicable
- Database / persistence checks — if applicable
- Permission / authorization matrix
- Resilience (network loss, retry, HTTP 500, timeout, concurrency)
- Compatibility (browser/OS/viewport) — if applicable

If **code change / diff summary** is provided, add a section below the table (still markdown): **Change-driven must-test** (branches/conditions implied) and **Regression ripple** (upstream/downstream).

If **historical defects** are provided, add **Negative list from past failures** (patterns to harden this release).

=== Requirement context ===
{ctx}

=== Iteration / legacy context (optional) ===
{iter_note or "N/A"}

=== Code change / diff summary (optional) ===
{diff_note or "N/A"}

=== Historical defects (optional) ===
{hist_note or "N/A"}

Output ONLY the markdown table and optional sections below it. No JSON."""
        else:
            prompt = f"""你是一名拥有约 20 年经验的测试架构师，精通 ISTQB、黑盒、白盒与探索性测试，具备**破坏性思维**。**请先不要输出详细测试用例。**

第一步：请输出「测试点思维导图」，格式为 **Markdown 表格**，用于在写用例前自检覆盖率是否遗漏。

表头列：**维度** | **测试关注点** | **关键测试思路（短语列举即可）** | **需求溯源（原文片段或章节）**

行维度必须覆盖（若文档未提及该行，写「文档未提及 — N/A」）：
- UI外观（多分辨率下布局错位、设计稿间距/颜色还原、控件可点/不可点/悬停/按下的视觉反馈）
- 功能逻辑（正向/负向、等价类有效/无效、边界值含最小值-1与最大值+1）
- 接口校验（字段类型、长度、必填、枚举）— 有则展开，无则 N/A
- 数据库校验 — 有则展开，无则 N/A
- 权限控制（越权、角色矩阵）
- 异常容错（断网重试、服务端500、超时、并发操作）
- 兼容性（浏览器/操作系统/视口）— 有则展开

若提供了**代码变更/Diff 摘要**，在表格下方用 markdown 小节输出：**变更点必测**（从分支/循环/异常捕获反推覆盖）与**关联回归范围**（上游调用方/下游被调方）。

若提供了**历史缺陷列表**，在表格下方输出：**历史故障负面清单**（本次需重点防御的模式）。

=== 需求梳理上下文 ===
{ctx}

=== 迭代/旧版摘要（可选）===
{iter_note or "无"}

=== 代码变更/Git Diff 摘要（可选）===
{diff_note or "无"}

=== 历史缺陷（可选）===
{hist_note or "无"}

只输出 Markdown 表格及上述可选小节，不要输出 JSON，不要写详细用例步骤。"""

        try:
            r = self.ai_api_caller(prompt)
            out = (r or "").strip()
            return out[:8000] if len(out) > 8000 else out
        except Exception as e:
            print(f"   ⚠️ 思维导图生成失败，将跳过该步骤: {e}")
            return ""

    def _build_architect_context_block(self) -> str:
        """注入到逐功能点提示中的共享上下文（历史缺陷、迭代、Diff）。"""
        parts = []
        if self.language == "en":
            if self._historical_defects:
                parts.append(
                    "【Historical defect patterns — use error guessing; add defensive cases】\n"
                    + _clip(self._historical_defects, 3500)
                )
            if self._iteration_context:
                parts.append(
                    "【Iteration / legacy context — change-driven & regression scope】\n"
                    + _clip(self._iteration_context, 3500)
                )
            if self._code_change_summary:
                parts.append(
                    "【Code change / diff summary — aim for branch-aware cases; map if-else/loops/exceptions】\n"
                    + _clip(self._code_change_summary, 5000)
                )
        else:
            if self._historical_defects:
                parts.append(
                    "【历史缺陷负面清单 — 采用错误推测法，补充针对性防御用例】\n"
                    + _clip(self._historical_defects, 3500)
                )
            if self._iteration_context:
                parts.append(
                    "【迭代与基线上下文 — 变更点驱动；必须做关联影响与回归范围思考】\n"
                    + _clip(self._iteration_context, 3500)
                )
            if self._code_change_summary:
                parts.append(
                    "【代码变更/Git Diff 摘要 — 结合白盒思路覆盖分支/循环/异常路径】\n"
                    + _clip(self._code_change_summary, 5000)
                )
        return "\n\n".join(parts) if parts else ""

    def _generate_cases_for_function_point(self, fp: FunctionPoint, 
                                           requirement_text: str) -> List[TestCase]:
        """为单个功能点生成测试用例（根据复杂度自动调整数量）"""
        if not self.ai_api_caller:
            return self._generate_cases_local(fp)
        
        # 根据功能点复杂度决定生成用例数量
        case_count = self._determine_case_count(fp)
        
        # 语言提示
        language_instruction = ""
        if self.language == 'en':
            language_instruction = (
                "\n【Language — English only】\n"
                "- All human-readable case fields MUST be in **English**: title, precondition, test_steps, expected, remark, **module**, **submodule**.\n"
                "- Do **not** use Chinese in those fields unless it is a **proper noun** copied verbatim from the requirement.\n"
                "- **module** / **submodule** must match the **actual business domain** (same idea as the function point), in English — never generic Chinese placeholders.\n"
                "- case_id: lowercase_snake + digits as specified."
            )
        else:
            language_instruction = (
                "\n【语言要求】\n"
                "请用**中文**编写 title、precondition、test_steps、expected、remark；**module** 与 **submodule** 也用中文，"
                "且须与需求域一致（可与当前功能点的模块/子模块对齐或细化），勿使用与需求无关的固定占位词。"
            )
        
        # 根据用例数量生成提示
        scenarios_text = self._generate_scenario_text(case_count)
        
        refined = (self._refined_requirement_brief or "").strip()
        if refined:
            req_context = refined[:5000]
            req_extra_note = "（上文为全量需求梳理；下列功能点为当前唯一测试范围。）"
        else:
            req_context = requirement_text[:3500]
            req_extra_note = "（原文摘录；若过长请聚焦与下列功能点相关的规则与界面。）"

        mindmap_block = _clip(self._test_mindmap_table, 3800)
        if not mindmap_block:
            mindmap_block = (
                "（思维导图未生成或为空；请仍按 ISTQB 多维度与下列分层要求自行穷举测试点。）"
                if self.language != "en"
                else "(Mind map unavailable; still apply full ISTQB/layered coverage below.)"
            )
        arch_extra = self._build_architect_context_block()

        if self.language == "en":
            prompt = f"""
You are a **senior test architect (~20y exp)**, ISTQB-aligned, with **destructive / exploratory** mindset and strong business context. You master black-box, white-box reasoning, and automation-friendly case design.

**Chain of thought (do not output your reasoning):** map the function point to UI / functional / flow / data-security layers; choose techniques: equivalence partitioning, boundary values, scenario-based, error guessing; align with the mind map; add regression/defect-driven cases when context is given.

Then output **only** the JSON array of test cases.

【Test-point mind map (coverage checklist)】
{mindmap_block}

{arch_extra}

【Requirement context】
{req_context}
(The function point below is the **only** scope for this batch.)

【Critical methods & layers】
- Techniques: equivalence classes (valid/invalid), boundary (min-1, max+1), scenarios, error guessing.
- Functional: never only "valid input → save OK"; include negatives, exceptions (network drop/retry, HTTP 500, concurrency).
- State machines: if relevant, cover illegal transitions (state-event matrix style in steps).
- Flow / E2E: where applicable write **user-story style** preconditions ("As a VIP user, …") for happy path, alternates, reverse flows.
- Data & security: IDOR (user A vs B), parameter tampering, SQLi/XSS payloads in inputs, sensitive data masking in logs.
- UI: layout at key resolutions, spacing/color vs spec, control states (enabled/disabled/hover/active), loading/error feedback.
- Iteration: if legacy context exists, include **change-point** tests and **ripple regression** to related modules.
- Prefer steps and expected results that are **machine-checkable** where possible.

{scenarios_text}
{language_instruction}

【Current function point (sole scope)】
{fp.description}

【Requirement excerpt (detail)】
{requirement_text[:1800]}

【Hard rules】
1. Test **only** this function point: {fp.description}
2. Each case = distinct objective; no duplicates
3. Suggested minimum {case_count} cases; generate more if complexity demands
4. case_id: lowercase_snake_### (e.g. menu_func_001)
5. title: [target]+[check]+[condition]
6. test_steps: each step tagged [Action] / [Verify] / [Cleanup]
7. expected: measurable acceptance criteria
8. remark: include methods & layer tags, e.g. "Methods: EP/BV/Scenario | Layer: Functional+Security | Covers requirement: {fp.description}"
9. priority: P0/P1/P2
10. **module** and **submodule** keys: English, domain-specific; align with this function point ({fp.module} / {fp.submodule}) unless you refine them more accurately from the requirement.
11. Valid JSON only: double quotes for strings; use single quotes inside English text for product names (e.g. Click the 'SAVE' button).

【JSON output】
[
  {{
    "case_id": "{self._generate_case_id_prefix(fp)}001",
    "module": "{fp.module}",
    "submodule": "{fp.submodule}",
    "title": "[target]+[check]",
    "precondition": "1. Environment ready\\n2. …",
    "test_steps": "1. [Action] …\\n2. [Verify] …",
    "expected": "1. …\\n2. …",
    "priority": "P0",
    "remark": "Methods: EP,BV | Layer: Functional | Covers requirement: {fp.description}"
  }}
]

Return **only** the JSON array.
"""
        else:
            prompt = f"""
你是一名拥有约 **20 年经验**的**测试架构师**，遵循 **ISTQB** 思想，具备**破坏性思维**与**探索性测试**能力，熟悉业务上下文与可自动化设计。精通黑盒（等价类、边界值、场景法、错误推测）并结合必要的白盒思路（分支/异常路径，尤其当提供 Diff 摘要时）。

**思考链（不要在输出中展示推理过程）：** 先将本功能点映射到 UI层 / 功能层 / 流程层 / 数据与安全层；对照下方「测试点思维导图」自检是否遗漏；结合历史缺陷做错误推测；迭代场景下思考变更点与关联回归。

最终**只输出** JSON 测试用例数组。

【测试点思维导图（写用例前已梳理，请对照补全）】
{mindmap_block}

{arch_extra}

【需求上下文】
{req_context}
{req_extra_note}

【方法与分层（必须体现到用例设计与 remark 中）】
- 黑盒：等价类（有效/无效）、边界值（最小值-1、最大值+1）、场景法、错误推测法。
- 功能层：禁止只写「输入合法点击保存成功」；必须包含负向、异常（断网重试、服务端500、超时、并发）。
- 状态机：若与本功能点相关，用步骤体现**非法状态跳转**与状态-事件覆盖思路。
- 流程层：适用时用**用户故事**式前置或标题（例：作为VIP用户在优惠券过期前5分钟下单），覆盖主成功路径、备选流、逆向/回滚。
- 数据与安全：接口越权（用户A访问用户B数据）、参数篡改、SQL注入/XSS 特殊字符、敏感数据脱敏（日志无明文密码）。
- UI层：关键分辨率下布局、设计稿间距/颜色、控件状态视觉反馈、加载与错误提示。
- 迭代回归：若有「迭代/旧版」上下文，必须包含**变更点精准测试**与**关联影响**（上游/下游模块的回归思路反映在用例中）。

{scenarios_text}
{language_instruction}

【当前功能点（唯一测试范围）】
{fp.description}

【原始需求摘录（补充细节，可与上文对照）】
{requirement_text[:1800]}

【严格要求】
1. 必须只测试该功能点: {fp.description}，勿发散到其他功能点。
2. 每条用例目标唯一，互不重复。
3. 建议至少 {case_count} 条；复杂功能应显著多于该数（如 15–40+）。
4. case_id: 小写英文_下划线_三位数字
5. title: [对象]+[验证点]+[场景]
6. test_steps: 每步带 [操作]、[验证] 或 [清理]
7. expected: 可量化、可判定
8. remark: 必须含「覆盖需求: {fp.description}」，并标注所用测试方法缩写与分层，例如：测试方法: 等价类+边界值+场景法 | 分层: 功能+安全 | 覆盖需求: {fp.description}
9. 优先级: P0 / P1 / P2
10. 每条用例必须包含 **module**、**submodule** 字段（中文，与需求域一致）；可与当前功能点预设「{fp.module}」「{fp.submodule}」一致，也可按需求细化，禁止填与文档无关的固定词。
11. JSON 合法：字符串内英文产品名用单引号，避免未转义双引号。

【JSON格式输出】
[
  {{
    "case_id": "{self._generate_case_id_prefix(fp)}001",
    "module": "{fp.module}",
    "submodule": "{fp.submodule}",
    "title": "[对象]+[验证点]",
    "precondition": "1. 系统已启动\\n2. 测试环境已就绪",
    "test_steps": "1. [操作] 打开功能\\n2. [验证] 检查显示正常\\n3. [清理] 关闭功能",
    "expected": "1. 功能正常启动\\n2. 显示内容正确\\n3. 响应时间<2秒",
    "priority": "P0",
    "remark": "测试方法: 等价类+边界值 | 分层: 功能 | 覆盖需求: {fp.description}"
  }}
]

只返回JSON数组，不要其他内容。
"""
        
        max_retries = 5  # 增加重试次数
        # 指数退避策略
        base_delay = 2  # 基础延迟时间（秒）
        max_delay = 30  # 最大延迟时间（秒）
        
        for attempt in range(max_retries):
            try:
                _bound = getattr(self.ai_api_caller, "__self__", None)
                _bu = _mu = None
                if _bound is not None:
                    _cfg = getattr(_bound, "ai_config", None)
                    _bu = getattr(_cfg, "base_url", None) if _cfg else None
                    if not _bu and _cfg is not None and getattr(_cfg, "provider", None) == AIProvider.DEEPSEEK:
                        _bu = "https://api.deepseek.com"
                    _mu = getattr(_bound, "model", None)
                print(f"🔗 调用API: base_url={_bu or 'N/A'}, model={_mu or 'N/A'}")
                response = self.ai_api_caller(prompt)
                print(f"✅ API响应成功")
                
                # 如果响应非常短，可能是错误响应，增加重试
                if len(response.strip()) < 50:
                    print(f"   ⚠️ 响应过短({len(response)}字符)，可能是错误响应")
                    if attempt < max_retries - 1:
                        raise Exception("Response too short, retrying...")
                
                # 清理响应数据，移除可能导致JSON解析失败的内容
                response = self._clean_json_response(response)
                
                # 提取 JSON（须忽略字符串内的 ]，不能用 rfind(']')）
                json_str = _extract_balanced_json_container(response)
                if not json_str:
                    json_start = response.find("[")
                    json_end = response.rfind("]") + 1
                    if json_start == -1:
                        json_start = response.find("{")
                        json_end = response.rfind("}") + 1
                    if json_start != -1 and json_end > json_start:
                        json_str = response[json_start:json_end]
                    else:
                        json_str = ""
                
                if json_str:
                    
                    # 尝试修复JSON格式问题
                    json_str = self._fix_json_format(json_str)
                    json_for_aggressive = json_str
                    cases_data = None
                    try:
                        cases_data = json.loads(json_str)
                    except json.JSONDecodeError as je:
                        print(f"   ⚠️ JSON解析失败，尝试修复: {je}")
                        try:
                            with open('debug_failed_response.txt', 'w', encoding='utf-8') as f:
                                f.write(f"=== 原始响应 ({len(json_str)} 字符) ===\n")
                                f.write(json_str)
                                f.write(f"\n\n=== 错误信息 ===\n{je}")
                            print(f"   💾 原始响应已保存到 debug_failed_response.txt 用于调试")
                        except Exception:
                            pass
                        repaired = _try_llm_json_repair(json_str)
                        if repaired:
                            try:
                                cases_data = json.loads(repaired)
                                print(f"   ✅ json-repair 库修复后解析成功")
                            except json.JSONDecodeError:
                                cases_data = None
                        if cases_data is None:
                            json_str = self._aggressive_json_fix(json_for_aggressive)
                            try:
                                cases_data = json.loads(json_str)
                            except json.JSONDecodeError:
                                print(f"   ❌ 修复后仍无法解析，跳过此次尝试")
                                cases_data = []
                    
                    if isinstance(cases_data, dict):
                        cases_data = [cases_data]
                    
                    # 检查是否有有效数据
                    if not cases_data or len(cases_data) == 0:
                        print(f"   ⚠️ 尝试 {attempt + 1}/{max_retries}: JSON解析成功但无有效数据")
                        # 继续重试
                        if attempt < max_retries - 1:
                            continue
                        else:
                            # 最后一次尝试也失败，跳到本地生成
                            break
                    
                    test_cases = []
                    # 完全不限制用例数量，AI生成多少就全部接收
                    for i, case_data in enumerate(cases_data):  # 移除任何切片限制
                        priority = self._parse_priority(case_data.get('priority', 'P1'))
                        
                        mod = (case_data.get('module') or '').strip() or fp.module
                        sub = (case_data.get('submodule') or '').strip() or fp.submodule
                        test_case = TestCase(
                            module=mod,
                            submodule=sub,
                            case_id=case_data.get('case_id', f'{self._generate_case_id_prefix(fp)}{i+1:03d}'),
                            title=case_data.get('title', f'{fp.description}验证'),
                            precondition=case_data.get('precondition', '系统正常运行'),
                            test_steps=case_data.get('test_steps', '待补充'),
                            expected=case_data.get('expected', '待补充'),
                            priority=priority,
                            remark=case_data.get('remark', f'测试方法: AI生成 | 覆盖需求: {fp.description}'),
                            methods_used=[TestMethod.AI_ENHANCED]
                        )
                        test_cases.append(test_case)
                    
                    if test_cases:
                        print(f"   ✅ 实际生成了 {len(test_cases)} 个测试用例")
                        return test_cases
                    else:
                        print(f"   ⚠️ 尝试 {attempt + 1}/{max_retries}: JSON解析成功但无有效数据")
                else:
                    print(f"   ⚠️ 尝试 {attempt + 1}/{max_retries}: 响应中找不到JSON数据")
            
            except json.JSONDecodeError as e:
                error_msg = f"JSON解析失败: {str(e)}"
                print(f"   ⚠️ 尝试 {attempt + 1}/{max_retries}: {error_msg}")
                # 保存错误详情用于调试
                try:
                    with open(f'debug_json_error_{attempt+1}.txt', 'w', encoding='utf-8') as f:
                        f.write(f"错误信息: {e}\n")
                        f.write(f"响应内容前500字符: {response[:500] if response else '无响应'}\n")
                        f.write(f"响应内容后500字符: {response[-500:] if response and len(response) > 500 else '内容不足'}\n")
                    print(f"   💾 错误详情已保存到 debug_json_error_{attempt+1}.txt")
                except Exception as file_err:
                    print(f"   ⚠️ 保存错误详情失败: {file_err}")
            except Exception as e:
                error_msg = f"API调用失败: {str(e)}"
                print(f"   ⚠️ 尝试 {attempt + 1}/{max_retries}: {error_msg}")
                import traceback
                traceback.print_exc()
                # 记录更多错误上下文
                print(f"   📋 错误上下文: 功能点='{fp.description}', 建议用例数={case_count}")
            
            if attempt < max_retries - 1:
                import time
                # 使用指数退避策略
                wait_time = min(base_delay * (2 ** attempt), max_delay)
                print(f"   🔄 等待{wait_time}秒后重试 (第{attempt + 1}/{max_retries}次)...")
                time.sleep(wait_time)
        
        print(f"   ❌ 所有API调用尝试均失败，使用本地生成")
        # 记录失败日志
        try:
            with open('ai_generation_failure.log', 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.datetime.now()}] 功能点'{fp.description}'生成失败，已降级到本地生成\n")
        except Exception as log_err:
            print(f"   ⚠️ 记录失败日志时出错: {log_err}")
        return self._generate_cases_local(fp, case_count)
    
    def _clean_json_response(self, response: str) -> str:
        """清理 AI 响应中的 markdown 代码块（如 ```json ... ```）。"""
        response = re.sub(r"```json\s*```\s*", "", response)
        response = re.sub(r'```\s*', '', response)
        
        # 仅从全文开头去掉 [{ 之前的说明。禁止对每行用 ^...MULTILINE：会把 "case_id": 等整行删光，只剩碎片。
        response = response.strip()
        m = re.search(r'[\[{]', response)
        if m:
            response = response[m.start():]
        
        # 修复编码问题和多余字符
        
        # 移除多余的回车符
        response = re.sub(r'\r\r', '\r', response)
        
        # 移除文件头信息（如果存在）
        if response.startswith('==='):
            # 找到第一个真正的JSON开始位置
            json_start = response.find('[')
            if json_start != -1:
                response = response[json_start:]
        
        # 移除错误信息部分（如果存在）
        error_pos = response.find('=== 错误信息 ===')
        if error_pos != -1:
            response = response[:error_pos]
        
        # 清理控制字符和不可见字符
        response = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F\uFFFD]', '', response)
        # 移除零宽字符
        response = re.sub(r'[\u200B-\u200D\uFEFF]', '', response)
        
        # 修复多余的换行和空格
        response = re.sub(r'\r\n', '\n', response)
        response = re.sub(r'\n\s*\n', '\n', response)
        
        return response.strip()
    
    def _fix_json_format(self, json_str: str) -> str:
        """Fix JSON format issues"""
        print(f"   🔧 开始修复JSON格式，原始长度: {len(json_str)} 字符")
        
        import re
        
        # 移除控制字符和不可见字符
        original_len = len(json_str)
        json_str = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F\uFFFD]', '', json_str)
        # 移除零宽字符
        json_str = re.sub(r'[\u200B-\u200D\uFEFF]', '', json_str)
        if len(json_str) != original_len:
            print(f"   ✅ 移除了控制字符")
        
        # 修复多余的回车符
        original_len = len(json_str)
        json_str = re.sub(r'\r\r', '\r', json_str)
        json_str = re.sub(r'\r\n', '\n', json_str)
        if len(json_str) != original_len:
            print(f"   ✅ 修复了回车符问题")
        
        _pre_esc = json_str
        json_str = _escape_interior_quotes_json(json_str)
        # 再跑一轮：嵌套/多处未转义引号时一轮可能仍剩非法 "
        json_str = _escape_interior_quotes_json(json_str)
        if json_str != _pre_esc:
            print(f"   ✅ 转义了 JSON 字符串值内的非法双引号")
        original_len = len(json_str)
        json_str = json_str.replace('\\\\\\\\', '\\\\')
        if len(json_str) != original_len:
            print(f"   ✅ 修复了双反斜杠问题")
        
        # 移除末尾逗号（如果存在）
        original_len = len(json_str)
        json_str = re.sub(r',\s*([\]}])', r'\1', json_str)
        if len(json_str) != original_len:
            print(f"   ✅ 移除了末尾逗号")
        
        # 修复引号问题 - 更保守的方法
        original_len = len(json_str)
        # 只修复明显的单引号问题，避免破坏JSON结构
        # 仅在明显不是JSON结构的地方替换单引号
        json_str = re.sub(r"(?<!\\)'", '"', json_str)
        if len(json_str) != original_len:
            print(f"   ✅ 修复了引号问题")
        
        print(f"   🔧 JSON格式修复完成，新长度: {len(json_str)} 字符")
        return json_str
    
    def _aggressive_json_fix(self, json_str: str) -> str:
        """Aggressively fix JSON format issues (handle unfinished strings)"""
        print(f"   🔧 开始积极修复JSON，原始长度: {len(json_str)} 字符")
        
        # 保存原始字符串用于调试
        try:
            with open('debug_original_json.txt', 'w', encoding='utf-8') as f:
                f.write(json_str)
            print(f"   💾 原始JSON已保存到 debug_original_json.txt")
        except Exception as e:
            print(f"   ⚠️ 保存原始JSON失败: {e}")
        
        # 方案0: AI响应专用修复 - 头部修复策略
        try:
            import re
            test_str = _escape_interior_quotes_json(json_str.rstrip())
            # 移除控制字符和不可见字符
            test_str = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F\uFFFD]', '', test_str)
            test_str = re.sub(r'[\u200B-\u200D\uFEFF]', '', test_str)
            
            # 特别处理：如果字符串以 "[Verify] 结尾，说明被截断在字符串中间
            if test_str.endswith('[Verify]') or '[Verify]\n' in test_str[-50:]:
                # 在末尾添加合理的结束内容
                test_str = test_str + ' the progress accuracy against the known data size."}]'
                print(f"   ✅ 修复被截断的测试步骤字符串")
            
            # 补全可能缺失的结尾括号
            open_square = test_str.count('[')
            close_square = test_str.count(']')
            open_curly = test_str.count('{')
            close_curly = test_str.count('}')
            
            missing_square = open_square - close_square
            missing_curly = open_curly - close_curly
            
            if missing_square > 0:
                test_str += ']' * missing_square
                print(f"   ✅ 补全 {missing_square} 个缺失的方括号")
            if missing_curly > 0:
                test_str += '}' * missing_curly
                print(f"   ✅ 补全 {missing_curly} 个缺失的花括号")
                
            # 移除末尾可能的逗号
            if test_str.endswith(','):
                test_str = test_str[:-1]
                print(f"   ✅ 移除末尾多余的逗号")
                
            # 再次清理控制字符
            test_str = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', test_str)
                
            # 尝试解析
            test_data = json.loads(test_str)
            if isinstance(test_data, list) and len(test_data) > 0:
                print(f"   ✅ AI专用修复成功: {len(json_str)} → {len(test_str)} 字符，得到 {len(test_data)} 个对象")
                # 保存修复后的JSON用于调试
                try:
                    with open('debug_fixed_json.txt', 'w', encoding='utf-8') as f:
                        f.write(test_str)
                    print(f"   💾 修复后的JSON已保存到 debug_fixed_json.txt")
                except Exception as e:
                    print(f"   ⚠️ 保存修复后的JSON失败: {e}")
                return test_str
            elif isinstance(test_data, dict):
                print(f"   ✅ AI专用修复成功: 找到单个对象")
                # 保存修复后的JSON用于调试
                try:
                    with open('debug_fixed_json.txt', 'w', encoding='utf-8') as f:
                        f.write(test_str)
                    print(f"   💾 修复后的JSON已保存到 debug_fixed_json.txt")
                except Exception as e:
                    print(f"   ⚠️ 保存修复后的JSON失败: {e}")
                return test_str
        except json.JSONDecodeError as e:
            print(f"   ⚠️ AI专用修复仍无法解析 JSON: {e}")
        except Exception as e:
            print(f"   ⚠️ AI专用修复失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 方案1: 查找最后一个完整对象
        print(f"   🔍 方案1: 查找最后一个完整对象...")
        for i in range(len(json_str) - 1, -1, -1):
            if json_str[i] in ['}', ']']:
                test_str = json_str[:i+1]
                try:
                    # 清理后再尝试解析
                    import re
                    clean_str = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', test_str)
                    clean_str = re.sub(r'[\u200B-\u200D\uFEFF]', '', clean_str)
                    clean_str = _escape_interior_quotes_json(clean_str)
                    test_data = json.loads(clean_str)
                    if isinstance(test_data, list) and len(test_data) > 0:
                        print(f"   ✅ 找到有效JSON位置 {i+1}，包含 {len(test_data)} 个对象")
                        return clean_str
                    elif isinstance(test_data, dict):
                        print(f"   ✅ 找到单个对象位置 {i+1}")
                        return clean_str
                except:
                    continue
        
        # 方案2: 逐步截断修复
        print(f"   🔍 方案2: 逐步截断修复...")
        for i in range(len(json_str), max(0, len(json_str) - 2000), -50):
            test_str = json_str[:i].rstrip()
            
            # 跳过不合理的位置
            if not test_str or test_str[-1] not in ['}', ']', '"', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
                continue
            
            # 补全括号
            open_square = test_str.count('[')
            close_square = test_str.count(']')
            open_curly = test_str.count('{')
            close_curly = test_str.count('}')
            
            if open_square > close_square:
                test_str += ']' * (open_square - close_square)
            if open_curly > close_curly:
                test_str += '}' * (open_curly - close_curly)
            
            # 移除控制字符
            import re
            test_str = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F\uFFFD]', '', test_str)
            test_str = re.sub(r'[\u200B-\u200D\uFEFF]', '', test_str)
            test_str = _escape_interior_quotes_json(test_str)
            
            try:
                test_data = json.loads(test_str)
                if isinstance(test_data, list) and len(test_data) > 0:
                    print(f"   ✅ 截断修复成功: {len(json_str)} → {len(test_str)} 字符，得到 {len(test_data)} 个对象")
                    return test_str
                elif isinstance(test_data, dict):
                    print(f"   ✅ 截断修复成功: 找到单个对象")
                    return test_str
            except (json.JSONDecodeError, ValueError):
                continue
            except Exception:
                continue
        
        print(f"   ❌ 所有修复方案均失败")
        return '[]'  # 返回空数组

    def _determine_case_count(self, fp: FunctionPoint) -> int:
        """
        分析功能点复杂度，给出建议数量（AI可以超出此建议值）
        
        策略：
        - 返回一个建议基准值供AI参考
        - AI可以根据实际情况生成更多用例
        - 不对AI生成数量做任何限制
        """
        desc = fp.description
        
        # 复杂功能关键词（需要更多测试用例）
        complex_keywords = ['选择', '输入', '配置', '计算', '验证', '匹配', '比较', '排序', '筛选', '搜索']
        medium_keywords = ['显示', '查看', '切换', '加载', '保存', '删除', '修改']
        simple_keywords = ['打开', '关闭', '跳转', '返回', '刷新']
        
        # 计算复杂度得分
        complexity_score = 0
        
        # 检查复杂关键词
        for kw in complex_keywords:
            if kw in desc:
                complexity_score += 4
                break
        
        # 检查中等关键词
        for kw in medium_keywords:
            if kw in desc:
                complexity_score += 2
                break
        
        # 检查简单关键词
        for kw in simple_keywords:
            if kw in desc:
                complexity_score += 1
                break
        
        # 描述长度影响复杂度
        if len(desc) > 40:
            complexity_score += 3
        elif len(desc) > 30:
            complexity_score += 2
        elif len(desc) > 20:
            complexity_score += 1
        
        # 包含数字/范围的功能（如 "1~40"、"4个"）
        if re.search(r'\d+[~–-]\d+', desc):
            complexity_score += 3  # 范围选择很复杂
        elif re.search(r'\d+个', desc):
            complexity_score += 2
        
        # 包含多个条件词（"且"、"或"、"同时"）
        condition_words = ['且', '或', '同时', '并且', '以及', '和']
        condition_count = sum(1 for word in condition_words if word in desc)
        complexity_score += condition_count
        
        # 根据得分给出建议基准值（AI可以生成更多）
        if complexity_score >= 10:
            suggested_count = 20  # 超复杂功能建议基准
        elif complexity_score >= 7:
            suggested_count = 15  # 高复杂度建议基准
        elif complexity_score >= 5:
            suggested_count = 10  # 复杂功能建议基准
        elif complexity_score >= 3:
            suggested_count = 8   # 中等复杂建议基准
        else:
            suggested_count = 5   # 简单功能建议基准
        
        print(f"  📈 功能点复杂度: {complexity_score}分 -> 建议基准 {suggested_count} 个用例（AI可生成更多）")
        return suggested_count
    
    def _generate_scenario_text(self, case_count: int) -> str:
        """根据建议数量生成场景描述（鼓励AI生成更多）"""
        if self.language == "en":
            return f"""
【Scenario depth — ISTQB black-box + exploratory】
Target **{case_count}+** cases; expand freely by risk.

1. **Equivalence & boundaries** (must): valid/invalid classes; min-1 / max+1; off-by-one; representative mid-values.
2. **Scenarios & flows**: happy path; alternates; reverse/rollback; user-story style where E2E applies.
3. **State machines** (if any): legal transitions + **illegal** state-event attempts.
4. **Resilience**: network loss & retry; HTTP 5xx; timeout; double-submit / concurrency.
5. **Security & data**: IDOR, tampered params, SQLi/XSS strings, PII not in logs.
6. **UI/UX**: key viewports/resolutions; loading & error states; disabled/hover/active visuals vs spec.
7. **Regression / change-driven** (when context provided): smoke on main flow + targeted regression on coupled modules.

**Minimum ~5 for trivial features; 20–40+ for complex or high-risk areas.**"""
        return f"""
【测试场景深度 — ISTQB 黑盒 + 探索性】
建议 **{case_count}+** 条用例；按风险与复杂度可大幅增加。

1. **等价类与边界值**（必选）：有效/无效等价类；最小值-1、最大值+1；临界与差一错误；典型中间值。
2. **场景法 / 流程**：主成功路径；备选流；逆向与状态回滚；端到端处可用「用户故事」式描述。
3. **状态机**（若相关）：合法转移 + **非法**状态-事件跳转（矩阵思维落实在步骤与预期中）。
4. **异常与容错**：断网与重试、服务端500、超时、重复提交、并发冲突。
5. **安全与数据**：越权、篡改参数、SQL注入/XSS 载荷、敏感信息脱敏与日志安全。
6. **UI/UX**：关键分辨率/视口；加载态与错误提示；控件禁用/悬停/按下等与设计稿一致性。
7. **变更驱动回归**（若提供迭代上下文）：变更点全分支覆盖 + 与变更模块高频交互的历史功能回归思路。

**简单功能不少于约 5 条；复杂或高风险功能建议 20–40+ 条。**"""
    
    def _generate_cases_local(self, fp: FunctionPoint, case_count: int = 3) -> List[TestCase]:
        """
        本地生成测试用例（后备方案）- 根据复杂度动态生成无限场景
        当AI不可用时，智能生成足够多的测试场景
        """
        case_id_prefix = self._generate_case_id_prefix(fp)
        
        # 基础场景库（按优先级排序）
        base_scenarios = [
            # 核心场景 (P0)
            ("正常场景-标准流程", "P0", "正常功能验证"),
            ("正常场景-备选流程", "P0", "备选路径验证"),
            
            # 边界场景 (P1)
            ("边界最小值", "P1", "最小边界值验证"),
            ("边界最大值", "P1", "最大边界值验证"),
            ("边界临界值-下限", "P1", "下限临界值验证"),
            ("边界临界值-上限", "P1", "上限临界值验证"),
            ("边界组合值", "P1", "边界组合验证"),
            
            # 特殊值场景 (P2)
            ("空值场景", "P2", "空值处理验证"),
            ("Null值场景", "P2", "Null处理验证"),
            ("零值场景", "P2", "零值处理验证"),
            ("负值场景", "P2", "负值处理验证"),
            ("极大值场景", "P2", "极大值处理验证"),
            ("极小值场景", "P2", "极小值处理验证"),
            ("特殊字符场景", "P2", "特殊字符处理验证"),
            
            # 数据有效性场景 (P1)
            ("重复数据场景", "P1", "重复数据验证"),
            ("格式错误场景", "P1", "格式错误验证"),
            ("类型错误场景", "P1", "类型错误验证"),
            ("长度超限场景", "P1", "长度超限验证"),
            ("数据不完整场景", "P1", "数据完整性验证"),
            
            # 操作场景 (P1)
            ("重复操作场景", "P1", "重复操作验证"),
            ("快速操作场景", "P1", "快速操作验证"),
            ("延迟操作场景", "P2", "操作延迟验证"),
            ("中断操作场景", "P1", "操作中断验证"),
            ("撤销操作场景", "P2", "操作撤销验证"),
            
            # 性能场景 (P2)
            ("大数据量场景", "P2", "大数据量验证"),
            ("高频操作场景", "P2", "高频操作验证"),
            ("超时场景", "P2", "超时处理验证"),
            ("响应时间场景", "P2", "响应时间验证"),
            
            # 并发场景 (P2)
            ("并发读场景", "P2", "并发读取验证"),
            ("并发写场景", "P2", "并发写入验证"),
            ("资源竞争场景", "P2", "资源竞争验证"),
            ("锁定冲突场景", "P2", "锁定冲突验证"),
            
            # 组合场景 (P1)
            ("多条件组合-与", "P1", "多条件AND验证"),
            ("多条件组合-或", "P1", "多条件OR验证"),
            ("复杂流程组合", "P1", "复杂流程验证"),
            ("跨模块组合", "P2", "跨模块交互验证"),
            
            # 状态场景 (P1)
            ("初始状态场景", "P1", "初始状态验证"),
            ("中间状态场景", "P1", "中间状态验证"),
            ("最终状态场景", "P1", "最终状态验证"),
            ("状态转换场景", "P1", "状态转换验证"),
            
            # 异常场景 (P1)
            ("异常输入-格式", "P1", "格式异常验证"),
            ("异常输入-范围", "P1", "范围异常验证"),
            ("系统异常-崩溃", "P2", "系统崩溃验证"),
            ("系统异常-资源", "P2", "资源不足验证"),
            ("网络异常-超时", "P2", "网络超时验证"),
            ("网络异常-断开", "P2", "网络断开验证"),
            ("依赖服务异常", "P2", "依赖服务验证"),
            ("数据库异常", "P2", "数据库异常验证"),
            
            # 安全场景 (P1)
            ("SQL注入场景", "P1", "SQL注入防护验证"),
            ("XSS攻击场景", "P1", "XSS防护验证"),
            ("权限验证场景", "P1", "权限控制验证"),
            ("敏感数据场景", "P1", "数据安全验证"),
            
            # 兼容性场景 (P2)
            ("浏览器兼容性", "P2", "浏览器兼容验证"),
            ("设备兼容性", "P2", "设备兼容验证"),
            ("版本兼容性", "P2", "版本兼容验证"),
            ("语言兼容性", "P2", "多语言验证"),
        ]
        
        # 根据case_count智能选择场景（不限制总数）
        # 优先选择高优先级场景，然后根据功能特点选择相关场景
        selected_scenarios = []
        
        # 始终包含核心场景
        p0_scenarios = [s for s in base_scenarios if s[1] == "P0"]
        selected_scenarios.extend(p0_scenarios[:min(2, case_count // 3)])
        
        # 根据功能描述智能选择相关场景
        desc_lower = fp.description.lower()
        
        # 如果包含数字/范围关键词，增加边界场景
        if any(kw in fp.description for kw in ['选择', '输入', '数字', '范围', '~', '-']):
            boundary_scenarios = [s for s in base_scenarios if '边界' in s[0]]
            selected_scenarios.extend(boundary_scenarios)
        
        # 如果包含验证/计算关键词，增加数据有效性场景
        if any(kw in fp.description for kw in ['验证', '计算', '配置', '设置']):
            validation_scenarios = [s for s in base_scenarios if any(kw in s[0] for kw in ['格式', '类型', '有效性'])]
            selected_scenarios.extend(validation_scenarios)
        
        # 如果包含操作关键词，增加操作场景
        if any(kw in fp.description for kw in ['点击', '操作', '执行', '处理']):
            operation_scenarios = [s for s in base_scenarios if '操作' in s[0]]
            selected_scenarios.extend(operation_scenarios)
        
        # 如果是复杂功能，增加性能和并发场景
        if case_count >= 15:
            performance_scenarios = [s for s in base_scenarios if any(kw in s[0] for kw in ['性能', '并发', '大数据'])]
            selected_scenarios.extend(performance_scenarios)
        
        # 始终包含异常场景
        exception_scenarios = [s for s in base_scenarios if '异常' in s[0]]
        selected_scenarios.extend(exception_scenarios[:min(5, case_count // 4)])
        
        # 去重
        seen_names = set()
        unique_scenarios = []
        for scenario in selected_scenarios:
            if scenario[0] not in seen_names:
                seen_names.add(scenario[0])
                unique_scenarios.append(scenario)
        
        # 如果选择的场景不够，从剩余场景中补充
        if len(unique_scenarios) < case_count:
            remaining_scenarios = [s for s in base_scenarios if s[0] not in seen_names]
            unique_scenarios.extend(remaining_scenarios[:case_count - len(unique_scenarios)])
        
        # 如果还不够，继续添加所有剩余场景（无限制）
        if len(unique_scenarios) < case_count:
            all_remaining = [s for s in base_scenarios if s[0] not in seen_names]
            unique_scenarios.extend(all_remaining)
        
        print(f"  📦 本地生成: 从{len(base_scenarios)}个场景库中选择了{len(unique_scenarios)}个场景（请求{case_count}个）")
        
        test_cases = []
        for i, (scenario, priority_str, desc) in enumerate(unique_scenarios, 1):
            priority = Priority.P0 if priority_str == "P0" else (Priority.P2 if priority_str == "P2" else Priority.P1)
            
            # 根据场景类型生成不同的测试步骤
            test_steps = self._generate_scenario_specific_steps(scenario, fp.description)
            expected = self._generate_scenario_specific_expected(scenario, fp.description)
            
            test_case = TestCase(
                module=fp.module,
                submodule=fp.submodule,
                case_id=f"{case_id_prefix}{i:03d}",
                title=f"{fp.description}-{desc}",
                precondition=f"1. 系统已启动\n2. {fp.description}功能可用\n3. 测试环境已就绪",
                test_steps=test_steps,
                expected=expected,
                priority=priority,
                remark=f"测试方法: {scenario} | 覆盖需求: {fp.description}",
                methods_used=[TestMethod.AI_ENHANCED]
            )
            test_cases.append(test_case)
        
        return test_cases
    
    def _generate_scenario_specific_steps(self, scenario: str, func_desc: str) -> str:
        """根据场景类型生成特定的测试步骤"""
        if "正常" in scenario:
            return f"1. [操作] 执行{func_desc}\n2. [验证] 检查功能正常执行\n3. [验证] 确认结果符合预期\n4. [清理] 恢复初始状态"
        elif "边界" in scenario:
            return f"1. [操作] 准备边界条件数据\n2. [操作] 执行{func_desc}\n3. [验证] 检查边界值处理正确\n4. [验证] 确认无异常提示\n5. [清理] 清除测试数据"
        elif "空值" in scenario or "Null" in scenario:
            return f"1. [操作] 输入空值/Null\n2. [操作] 执行{func_desc}\n3. [验证] 检查空值处理机制\n4. [验证] 确认有适当提示\n5. [清理] 恢复默认值"
        elif "异常" in scenario:
            return f"1. [操作] 构造异常场景\n2. [操作] 执行{func_desc}\n3. [验证] 检查异常处理机制\n4. [验证] 确认错误提示清晰\n5. [清理] 清理异常状态"
        elif "性能" in scenario or "并发" in scenario:
            return f"1. [操作] 准备性能测试环境\n2. [操作] 执行{func_desc}（高负载）\n3. [验证] 检查响应时间\n4. [验证] 确认系统稳定性\n5. [清理] 清理测试数据"
        elif "安全" in scenario:
            return f"1. [操作] 构造安全测试用例\n2. [操作] 执行{func_desc}\n3. [验证] 检查安全防护机制\n4. [验证] 确认无安全漏洞\n5. [清理] 清理测试数据"
        else:
            return f"1. [操作] 执行{func_desc}\n2. [验证] 检查{scenario}处理\n3. [验证] 确认结果正确\n4. [清理] 恢复初始状态"
    
    def _generate_scenario_specific_expected(self, scenario: str, func_desc: str) -> str:
        """根据场景类型生成特定的预期结果"""
        if "正常" in scenario:
            return f"1. {func_desc}执行成功\n2. 结果符合业务规则\n3. 响应时间<2秒\n4. 无错误提示"
        elif "边界" in scenario:
            return f"1. 边界值被正确识别\n2. 边界处理符合规范\n3. 返回明确结果\n4. 无异常抛出"
        elif "空值" in scenario or "Null" in scenario:
            return f"1. 空值被正确识别\n2. 显示友好提示信息\n3. 系统不崩溃\n4. 可恢复正常使用"
        elif "异常" in scenario:
            return f"1. 异常被正确捕获\n2. 错误提示清晰明确\n3. 系统保持稳定\n4. 日志记录完整"
        elif "性能" in scenario:
            return f"1. 响应时间满足要求\n2. 并发处理正确\n3. 资源占用合理\n4. 系统保持稳定"
        elif "并发" in scenario:
            return f"1. 并发请求处理正确\n2. 数据一致性保证\n3. 无死锁现象\n4. 性能满足要求"
        elif "安全" in scenario:
            return f"1. 安全防护机制生效\n2. 恶意输入被拦截\n3. 敏感信息被保护\n4. 记录安全日志"
        else:
            return f"1. {scenario}处理正确\n2. 结果符合预期\n3. 系统运行稳定\n4. 无异常发生"
    
    def _generate_case_id_prefix(self, fp: FunctionPoint) -> str:
        """根据功能点生成case_id前缀"""
        # 从功能点描述中提取关键词
        desc = fp.description
        
        # 提取动词和名词
        keywords = []
        action_words = ['查看', '显示', '切换', '创建', '添加', '删除', '修改',
                       '检测', '恢复', '支持', '加载', '保存']
        
        for word in action_words:
            if word in desc:
                keywords.append(word)
                desc = desc.replace(word, '', 1)
                break
        
        # 提取剩余的关键名词
        noun_words = ['菜单', '游戏', '记录', '设备', '蒙版', '数据', '功能']
        for word in noun_words:
            if word in desc:
                keywords.append(word)
                break
        
        if not keywords:
            keywords = ['func']
        
        # 转换为拼音首字母或英文
        word_map = {
            '菜单': 'menu', '游戏': 'game', '记录': 'record', '设备': 'device',
            '蒙版': 'mask', '数据': 'data', '功能': 'func', '查看': 'view',
            '显示': 'show', '切换': 'switch', '检测': 'detect', '恢复': 'restore',
            '支持': 'support', '加载': 'load', '保存': 'save'
        }
        
        prefix_parts = []
        for kw in keywords[:2]:  # 最多2个关键词
            prefix_parts.append(word_map.get(kw, 'func'))
        
        return '_'.join(prefix_parts) + '_'
    
    def _validate_and_fix_all_cases(self, test_cases: List[TestCase]) -> List[TestCase]:
        """验证并修正所有测试用例格式"""
        fixed_cases = []
        
        for i, tc in enumerate(test_cases):
            print(f"   🔧 验证用例 {i+1}/{len(test_cases)}: {tc.case_id}")
            
            # 修正各字段格式
            fixed_tc = TestCase(
                module=tc.module,
                submodule=tc.submodule,
                case_id=self._fix_case_id(tc.case_id, i+1),
                title=self._fix_title(tc.title),
                precondition=self._fix_precondition(tc.precondition),
                test_steps=self._fix_test_steps(tc.test_steps),
                expected=self._fix_expected(tc.expected),
                priority=tc.priority,
                remark=tc.remark,
                methods_used=tc.methods_used
            )
            
            fixed_cases.append(fixed_tc)
            print(f"      ✅ 修正后: {fixed_tc.case_id} - {fixed_tc.title[:30]}...")
        
        return fixed_cases
    
    def _fix_case_id(self, case_id: str, index: int) -> str:
        """修正case_id格式"""
        # 移除TC_等前缀
        case_id = re.sub(r'^(TC|TestCase|Test)_', '', case_id, flags=re.IGNORECASE)
        case_id = case_id.lower()
        
        # 确保格式: xxx_yyy_nnn
        if not re.match(r'^[a-z_]+_\d{3}$', case_id):
            parts = case_id.split('_')
            if len(parts) >= 2 and parts[-1].isdigit():
                num = int(parts[-1])
                parts[-1] = f"{num:03d}"
                case_id = '_'.join(parts)
            else:
                case_id = f"ai_gen_{index:03d}"
        
        return case_id
    
    def _fix_title(self, title: str) -> str:
        """修正title格式"""
        # 移除"验证"、"测试"前缀
        for prefix in ['验证', '测试', 'Test']:
            if title.startswith(prefix):
                title = title[len(prefix):].lstrip()
        
        # 确保有验证类动词
        if not any(kw in title for kw in ['验证', '检查', '检测', '测试', '确认']):
            title = f"{title}验证"
        
        return title
    
    def _fix_test_steps(self, steps: str) -> str:
        """修正test_steps格式，添加标签"""
        if not steps or '[操作]' in steps:
            return steps
        
        lines = steps.split('\n')
        fixed_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 移除编号
            line = re.sub(r'^\d+[\.\)、]\s*', '', line)
            
            # 添加标签
            if any(kw in line for kw in ['检查', '验证', '确认', '判断']):
                line = f"[验证] {line}"
            elif any(kw in line for kw in ['清理', '关闭', '退出', '删除', '恢复']):
                line = f"[清理] {line}"
            else:
                line = f"[操作] {line}"
            
            fixed_lines.append(line)
        
        # 重新编号
        return '\n'.join([f"{i+1}. {line}" for i, line in enumerate(fixed_lines)])
    
    def _fix_expected(self, expected: str) -> str:
        """修正expected格式，确保编号"""
        if not expected or re.match(r'^\d+[\.\)]', expected.strip()):
            return expected
        
        lines = [line.strip() for line in expected.split('\n') if line.strip()]
        lines = [re.sub(r'^\d+[\.\)、]\s*', '', line) for line in lines]
        
        return '\n'.join([f"{i+1}. {line}" for i, line in enumerate(lines)])
    
    def _fix_precondition(self, precondition: str) -> str:
        """修正precondition格式，确保编号"""
        if not precondition or re.match(r'^\d+[\.\)]', precondition.strip()):
            return precondition
        
        lines = [line.strip() for line in precondition.split('\n') if line.strip()]
        lines = [re.sub(r'^\d+[\.\)、]\s*', '', line) for line in lines]
        
        return '\n'.join([f"{i+1}. {line}" for i, line in enumerate(lines)])
    
    def _parse_priority(self, priority_str: str) -> Priority:
        """解析优先级"""
        priority_str = str(priority_str).upper()
        if 'P0' in priority_str:
            return Priority.P0
        elif 'P2' in priority_str:
            return Priority.P2
        else:
            return Priority.P1
