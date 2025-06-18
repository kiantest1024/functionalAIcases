#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
功能测试用例生成器
基于多种测试设计方法生成高覆盖度的功能测试用例
"""

import pandas as pd
import re
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import itertools
from datetime import datetime

class Priority(Enum):
    """测试用例优先级"""
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"

class TestMethod(Enum):
    """测试设计方法"""
    CAUSE_EFFECT = "因果图"
    SCENARIO = "场景法"
    EQUIVALENCE = "等价类"
    DECISION_TABLE = "判定表"
    ORTHOGONAL = "正交实验"
    STATE_TRANSITION = "状态转换"
    BOUNDARY_VALUE = "边界值"
    ERROR_GUESSING = "错误推测"
    AI_ENHANCED = "AI增强"

@dataclass
class TestCase:
    """测试用例数据结构"""
    module: str
    submodule: str
    case_id: str
    title: str  # 新增：测试用例标题
    precondition: str
    test_steps: str
    expected: str
    actual: str = ""
    priority: Priority = Priority.P1
    remark: str = ""
    methods_used: List[TestMethod] = field(default_factory=list)

@dataclass
class RequirementAnalysis:
    """需求分析结果"""
    modules: List[str]
    business_rules: List[str]
    input_fields: List[Dict]
    states: List[str]
    workflows: List[str]
    ui_elements: List[str]
    constraints: List[str]

class TestCaseGenerator:
    """功能测试用例生成器"""
    
    def __init__(self, custom_headers: Optional[Dict[str, str]] = None):
        """初始化测试用例生成器"""
        self.default_headers = {
            "Module": "模块",
            "Submodule": "子模块",
            "CaseID": "用例编号",
            "Title": "用例标题",  # 新增标题字段
            "Precondition": "前置条件",
            "TestSteps": "测试步骤",
            "Expected": "预期结果",
            "Actual": "实际结果",
            "Priority": "优先级",
            "Remark": "备注"
        }
        
        if custom_headers:
            self.headers = {**self.default_headers, **custom_headers}
        else:
            self.headers = self.default_headers
            
        self.test_cases: List[TestCase] = []
        self.case_counter = 0
        self.method_stats = {method: 0 for method in TestMethod}
        
    def analyze_requirements(self, requirement_text: str) -> RequirementAnalysis:
        """分析需求文档，提取关键信息"""

        modules = self._extract_modules(requirement_text)
        business_rules = self._extract_business_rules(requirement_text)
        input_fields = self._extract_input_fields(requirement_text)
        states = self._extract_states(requirement_text)
        workflows = self._extract_workflows(requirement_text)
        ui_elements = self._extract_ui_elements(requirement_text)
        constraints = self._extract_constraints(requirement_text)
        
        return RequirementAnalysis(
            modules=modules,
            business_rules=business_rules,
            input_fields=input_fields,
            states=states,
            workflows=workflows,
            ui_elements=ui_elements,
            constraints=constraints
        )
    
    def _extract_modules(self, text: str) -> List[str]:
        """提取功能模块"""
        # 查找模块相关关键词
        module_patterns = [
            r'模块[：:]\s*([^\n]+)',
            r'功能[：:]\s*([^\n]+)',
            r'系统[：:]\s*([^\n]+)'
        ]
        
        modules = []
        for pattern in module_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            modules.extend(matches)
            
        # 如果没有找到明确的模块定义，使用默认分类
        if not modules:
            modules = ["用户管理", "数据处理", "界面交互"]
            
        return list(set(modules))
    
    def _extract_business_rules(self, text: str) -> List[str]:
        """提取业务规则"""
        rule_patterns = [
            r'规则[：:]\s*([^\n]+)',
            r'条件[：:]\s*([^\n]+)',
            r'当.*时.*则',
            r'如果.*那么'
        ]
        
        rules = []
        for pattern in rule_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            rules.extend(matches)
            
        return rules
    
    def _extract_input_fields(self, text: str) -> List[Dict]:
        """提取输入字段信息"""
        # 查找输入字段相关信息
        field_patterns = [
            r'输入[：:]?\s*([^\n]+)',
            r'字段[：:]?\s*([^\n]+)',
            r'参数[：:]?\s*([^\n]+)'
        ]
        
        fields = []
        for pattern in field_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                fields.append({
                    "name": match.strip(),
                    "type": "string",  # 默认类型
                    "required": True,
                    "min_length": 1,
                    "max_length": 100
                })
                
        return fields
    
    def _extract_states(self, text: str) -> List[str]:
        """提取状态信息"""
        state_patterns = [
            r'状态[：:]\s*([^\n]+)',
            r'阶段[：:]\s*([^\n]+)',
            r'步骤[：:]\s*([^\n]+)'
        ]
        
        states = []
        for pattern in state_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            states.extend(matches)
            
        return list(set(states))
    
    def _extract_workflows(self, text: str) -> List[str]:
        """提取工作流程"""
        workflow_patterns = [
            r'流程[：:]\s*([^\n]+)',
            r'步骤[：:]\s*([^\n]+)',
            r'\d+[\.、]\s*([^\n]+)'
        ]
        
        workflows = []
        for pattern in workflow_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            workflows.extend(matches)
            
        return workflows
    
    def _extract_ui_elements(self, text: str) -> List[str]:
        """提取UI元素"""
        ui_patterns = [
            r'按钮[：:]?\s*([^\n]+)',
            r'页面[：:]?\s*([^\n]+)',
            r'界面[：:]?\s*([^\n]+)',
            r'表单[：:]?\s*([^\n]+)'
        ]
        
        elements = []
        for pattern in ui_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            elements.extend(matches)
            
        return list(set(elements))
    
    def _extract_constraints(self, text: str) -> List[str]:
        """提取约束条件"""
        constraint_patterns = [
            r'限制[：:]\s*([^\n]+)',
            r'约束[：:]\s*([^\n]+)',
            r'不能[：:]?\s*([^\n]+)',
            r'必须[：:]?\s*([^\n]+)'
        ]
        
        constraints = []
        for pattern in constraint_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            constraints.extend(matches)
            
        return constraints

    def generate_case_id(self, module: str, submodule: str = "") -> str:
        """生成测试用例ID - 格式：模块英文简写_子模块英文简写_数字编号"""
        self.case_counter += 1

        # 模块和子模块的中英文映射
        module_mapping = {
            # 功能相关
            "功能测试": "func",
            "界面测试": "ui",
            "数据验证": "data",
            "业务流程": "biz",
            "异常处理": "error",
            "性能测试": "perf",
            "安全测试": "sec",
            "兼容性测试": "compat",
            "易用性测试": "usability",
            "回归测试": "regress",

            # 业务模块
            "用户管理": "user",
            "个人中心": "personal",
            "首页": "home",
            "商品管理": "product",
            "搜索功能": "search",
            "购物车管理": "cart",
            "订单管理": "order",
            "支付管理": "payment",
            "库存管理": "inventory",
            "评价管理": "review",
            "收藏管理": "favorite",
            "地址管理": "address",
            "营销管理": "marketing",
            "积分管理": "points",
            "客服系统": "service",
            "消息中心": "message",
            "意见反馈": "feedback",
            "帮助中心": "help",
            "系统信息": "system",

            # 通用模块
            "功能模块": "func",
            "测试模块": "test"
        }

        submodule_mapping = {
            # 功能测试子模块
            "核心功能": "core",
            "边界功能": "boundary",
            "功能组合": "combo",

            # 界面测试子模块
            "界面元素": "element",
            "界面交互": "interact",
            "响应式设计": "responsive",
            "可访问性": "access",

            # 数据验证子模块
            "必填验证": "required",
            "格式验证": "format",
            "长度验证": "length",
            "特殊字符": "special",

            # 业务流程子模块
            "完整流程": "complete",
            "业务规则": "rule",
            "流程恢复": "recovery",

            # 异常处理子模块
            "网络异常": "network",
            "服务器异常": "server",
            "数据异常": "data_err",
            "并发异常": "concurrent",

            # 性能测试子模块
            "响应时间": "response",
            "并发性能": "concurrent_perf",
            "内存使用": "memory",

            # 安全测试子模块
            "权限验证": "auth",
            "输入安全": "input_sec",
            "会话安全": "session",

            # 兼容性测试子模块
            "浏览器兼容": "browser",
            "操作系统兼容": "os",

            # 易用性测试子模块
            "用户体验": "ux",
            "操作效率": "efficiency",

            # 业务子模块
            "用户登录": "login",
            "用户注册": "register",
            "基本信息": "info",
            "个人资料": "profile",
            "账户设置": "settings",
            "密码管理": "password",
            "页面展示": "display",
            "导航栏": "nav",
            "轮播图": "banner",
            "菜单栏": "menu",
            "商品展示": "show",
            "分类管理": "category",
            "商品搜索": "search_prod",
            "条件筛选": "filter",
            "商品详情": "details",
            "购物车操作": "cart_op",
            "订单处理": "order_proc",
            "支付处理": "pay_proc",
            "订单结算": "checkout",
            "库存控制": "stock",
            "商品入库": "inbound",
            "商品出库": "outbound",
            "商品评价": "review_prod",
            "商品收藏": "fav_prod",
            "收货地址": "ship_addr",
            "优惠券": "coupon",
            "积分操作": "points_op",
            "在线客服": "online_service",
            "消息通知": "notification",
            "用户反馈": "user_feedback",
            "使用帮助": "usage_help",
            "关于我们": "about",

            # 测试方法相关
            "等价类划分": "equiv",
            "边界值分析": "boundary_val",
            "判定表": "decision",
            "因果图": "cause_effect",
            "正交实验": "orthogonal",
            "场景法": "scenario",
            "错误推测": "error_guess",
            "状态转换": "state",
            "历史缺陷回归": "defect_regress",
            "非法状态转换": "illegal_state"
        }

        # 获取模块英文简写
        module_abbr = module_mapping.get(module, self._generate_abbr(module))

        # 获取子模块英文简写
        if submodule:
            submodule_abbr = submodule_mapping.get(submodule, self._generate_abbr(submodule))
            return f"{module_abbr}_{submodule_abbr}_{self.case_counter:03d}"
        else:
            return f"{module_abbr}_{self.case_counter:03d}"

    def _generate_abbr(self, text: str) -> str:
        """为未映射的文本生成英文简写"""
        # 移除常见的中文词汇
        text = text.replace("测试", "").replace("管理", "").replace("功能", "")

        # 如果是英文，取前几个字符
        if text.isascii():
            return text.lower()[:6]

        # 如果是中文，使用拼音首字母（简化处理）
        chinese_mapping = {
            "用户": "user", "个人": "personal", "首页": "home", "商品": "product",
            "搜索": "search", "购物车": "cart", "订单": "order", "支付": "payment",
            "库存": "inventory", "评价": "review", "收藏": "favorite", "地址": "address",
            "营销": "marketing", "积分": "points", "客服": "service", "消息": "message",
            "反馈": "feedback", "帮助": "help", "系统": "system", "界面": "ui",
            "数据": "data", "业务": "biz", "异常": "error", "性能": "perf",
            "安全": "sec", "兼容": "compat", "易用": "usability", "回归": "regress"
        }

        for chinese, english in chinese_mapping.items():
            if chinese in text:
                return english

        # 默认使用前3个字符的ASCII表示
        return ''.join([c for c in text if c.isalnum()])[:6].lower() or "test"

    def add_test_case(self, module: str, submodule: str, title: str, precondition: str,
                     test_steps: str, expected: str, priority: Priority,
                     methods: List[TestMethod], remark: str = ""):
        """添加测试用例"""
        case_id = self.generate_case_id(module, submodule)

        # 更新方法统计
        for method in methods:
            self.method_stats[method] += 1

        # 生成备注信息
        method_names = "+".join([method.value for method in methods])
        full_remark = f"{method_names}。{remark}" if remark else method_names

        test_case = TestCase(
            module=module,
            submodule=submodule,
            case_id=case_id,
            title=title,  # 新增标题字段
            precondition=precondition,
            test_steps=test_steps,
            expected=expected,
            priority=priority,
            remark=full_remark,
            methods_used=methods
        )

        self.test_cases.append(test_case)

    def generate_boundary_value_cases(self, analysis: RequirementAnalysis):
        """生成边界值测试用例"""
        for field in analysis.input_fields:
            module = "数据验证"
            submodule = f"{field['name']}边界值测试"

            # 最小值测试
            self.add_test_case(
                module=module,
                submodule=submodule,
                title=f"验证{field['name']}字段最小值边界",
                precondition="系统正常运行，用户已登录",
                test_steps=f"1. 在{field['name']}字段输入最小值{field.get('min_length', 1)}\n2. 点击提交按钮",
                expected="系统接受输入，处理成功",
                priority=Priority.P1,
                methods=[TestMethod.BOUNDARY_VALUE],
                remark="最小边界值测试"
            )

            # 最大值测试
            self.add_test_case(
                module=module,
                submodule=submodule,
                title=f"验证{field['name']}字段最大值边界",
                precondition="系统正常运行，用户已登录",
                test_steps=f"1. 在{field['name']}字段输入最大值{field.get('max_length', 100)}\n2. 点击提交按钮",
                expected="系统接受输入，处理成功",
                priority=Priority.P1,
                methods=[TestMethod.BOUNDARY_VALUE],
                remark="最大边界值测试"
            )

            # 超出最小值测试
            min_val = field.get('min_length', 1)
            if min_val > 0:
                self.add_test_case(
                    module=module,
                    submodule=submodule,
                    title=f"验证{field['name']}字段小于最小值的边界处理",
                    precondition="系统正常运行，用户已登录",
                    test_steps=f"1. 在{field['name']}字段输入小于最小值的数据{min_val-1}\n2. 点击提交按钮",
                    expected="系统显示错误提示信息，拒绝提交",
                    priority=Priority.P1,
                    methods=[TestMethod.BOUNDARY_VALUE],
                    remark="小于最小值边界测试"
                )

            # 超出最大值测试
            max_val = field.get('max_length', 100)
            self.add_test_case(
                module=module,
                submodule=submodule,
                title=f"验证{field['name']}字段大于最大值的边界处理",
                precondition="系统正常运行，用户已登录",
                test_steps=f"1. 在{field['name']}字段输入大于最大值的数据{max_val+1}\n2. 点击提交按钮",
                expected="系统显示错误提示信息，拒绝提交",
                priority=Priority.P1,
                methods=[TestMethod.BOUNDARY_VALUE],
                remark="大于最大值边界测试"
            )

    def generate_equivalence_class_cases(self, analysis: RequirementAnalysis):
        """生成等价类测试用例"""
        for field in analysis.input_fields:
            module = "数据验证"
            submodule = f"{field['name']}等价类测试"

            # 有效等价类
            self.add_test_case(
                module=module,
                submodule=submodule,
                title=f"验证{field['name']}字段有效数据输入",
                precondition="系统正常运行，用户已登录",
                test_steps=f"1. 在{field['name']}字段输入有效数据\n2. 点击提交按钮",
                expected="系统接受输入，处理成功",
                priority=Priority.P0,
                methods=[TestMethod.EQUIVALENCE],
                remark="有效等价类测试"
            )

            # 无效等价类 - 空值
            if field.get('required', True):
                self.add_test_case(
                    module=module,
                    submodule=submodule,
                    title=f"验证{field['name']}字段为空时的错误提示",
                    precondition="系统正常运行，用户已登录",
                    test_steps=f"1. {field['name']}字段保持为空\n2. 点击提交按钮",
                    expected="系统显示必填字段错误提示",
                    priority=Priority.P1,
                    methods=[TestMethod.EQUIVALENCE],
                    remark="无效等价类-空值测试"
                )

            # 无效等价类 - 特殊字符
            self.add_test_case(
                module=module,
                submodule=submodule,
                title=f"验证{field['name']}字段特殊字符处理",
                precondition="系统正常运行，用户已登录",
                test_steps=f"1. 在{field['name']}字段输入特殊字符@#$%\n2. 点击提交按钮",
                expected="系统显示格式错误提示或自动过滤特殊字符",
                priority=Priority.P2,
                methods=[TestMethod.EQUIVALENCE],
                remark="无效等价类-特殊字符测试"
            )

    def generate_scenario_cases(self, analysis: RequirementAnalysis):
        """生成场景法测试用例"""
        # 主流程场景
        for i, workflow in enumerate(analysis.workflows[:3]):  # 限制前3个主要流程
            module = "业务流程"
            submodule = f"主流程{i+1}"

            self.add_test_case(
                module=module,
                submodule=submodule,
                title=f"验证{workflow}主流程执行",
                precondition="系统正常运行，用户已登录，数据准备完成",
                test_steps=f"1. 执行{workflow}\n2. 验证每个步骤的结果\n3. 确认最终状态",
                expected="流程顺利执行完成，达到预期状态",
                priority=Priority.P0,
                methods=[TestMethod.SCENARIO],
                remark="主流程场景测试"
            )

        # 备选流程场景 - 具体化步骤描述
        self.add_test_case(
            module="业务流程",
            submodule="备选流程",
            title="验证备选流程的正确执行",
            precondition="系统正常运行，用户已登录，存在备选路径触发条件",
            test_steps="1. 触发备选流程条件：直接从网址进入目标页面（跳过主流程）\n2. 执行备选路径：点击快捷入口或使用备选导航\n3. 验证页面正确加载和功能可用\n4. 检查数据完整性和状态一致性",
            expected="备选流程正确执行，页面正常显示，功能完整可用，系统状态正确",
            priority=Priority.P1,
            methods=[TestMethod.SCENARIO],
            remark="备选流程场景测试"
        )

        # 异常流程场景
        self.add_test_case(
            module="业务流程",
            submodule="异常流程",
            title="验证异常情况下的错误处理",
            precondition="系统运行中，存在异常条件",
            test_steps="1. 触发异常情况（网络中断、服务不可用等）\n2. 观察系统响应\n3. 验证错误处理",
            expected="系统正确处理异常，显示友好错误信息，不崩溃",
            priority=Priority.P1,
            methods=[TestMethod.SCENARIO],
            remark="异常流程场景测试"
        )

    def generate_state_transition_cases(self, analysis: RequirementAnalysis):
        """生成状态转换测试用例"""
        if not analysis.states:
            return

        module = "状态管理"

        # 状态转换路径测试
        for i in range(len(analysis.states) - 1):
            current_state = analysis.states[i]
            next_state = analysis.states[i + 1]

            self.add_test_case(
                module=module,
                submodule="状态转换",
                title=f"验证从{current_state}到{next_state}的状态转换",
                precondition=f"系统处于{current_state}状态",
                test_steps=f"1. 执行状态转换操作\n2. 验证状态从{current_state}转换到{next_state}\n3. 确认状态转换的完整性",
                expected=f"系统成功从{current_state}转换到{next_state}，状态数据正确",
                priority=Priority.P1,
                methods=[TestMethod.STATE_TRANSITION],
                remark=f"状态转换：{current_state}→{next_state}"
            )

        # 非法状态转换测试
        if len(analysis.states) >= 2:
            self.add_test_case(
                module=module,
                submodule="非法状态转换",
                title="验证非法状态转换的拒绝处理",
                precondition=f"系统处于{analysis.states[0]}状态",
                test_steps=f"1. 尝试执行非法状态转换操作\n2. 验证系统拒绝转换\n3. 确认状态保持不变",
                expected="系统拒绝非法状态转换，显示错误信息，当前状态不变",
                priority=Priority.P1,
                methods=[TestMethod.STATE_TRANSITION],
                remark="非法状态转换测试"
            )

    def generate_decision_table_cases(self, analysis: RequirementAnalysis):
        """生成判定表测试用例"""
        if not analysis.business_rules:
            return

        module = "业务规则"
        submodule = "判定表测试"

        # 简化的判定表逻辑：基于业务规则生成组合测试
        conditions = ["条件A", "条件B", "条件C"]  # 简化示例

        # 生成所有可能的条件组合
        for i, combination in enumerate(itertools.product([True, False], repeat=len(conditions))):
            condition_desc = ", ".join([f"{conditions[j]}={'满足' if combination[j] else '不满足'}"
                                      for j in range(len(conditions))])

            expected_result = "执行动作A" if all(combination) else "执行动作B或显示错误"

            self.add_test_case(
                module=module,
                submodule=submodule,
                title=f"验证判定表组合{i+1}条件",
                precondition="系统正常运行，测试数据准备完成",
                test_steps=f"1. 设置测试条件：{condition_desc}\n2. 执行业务操作\n3. 验证结果",
                expected=expected_result,
                priority=Priority.P1 if all(combination) else Priority.P2,
                methods=[TestMethod.DECISION_TABLE],
                remark=f"判定表组合{i+1}：{condition_desc}"
            )

    def generate_orthogonal_cases(self, analysis: RequirementAnalysis):
        """生成正交实验测试用例"""
        if len(analysis.input_fields) < 3:
            return

        module = "参数组合"
        submodule = "正交实验"

        # L9正交表示例 (3^4)
        l9_table = [
            [1, 1, 1, 1],
            [1, 2, 2, 2],
            [1, 3, 3, 3],
            [2, 1, 2, 3],
            [2, 2, 3, 1],
            [2, 3, 1, 2],
            [3, 1, 3, 2],
            [3, 2, 1, 3],
            [3, 3, 2, 1]
        ]

        # 参数值映射
        param_values = {
            1: "最小值",
            2: "中间值",
            3: "最大值"
        }

        for i, combination in enumerate(l9_table):
            param_desc = ", ".join([f"参数{j+1}={param_values[combination[j]]}"
                                  for j in range(min(4, len(analysis.input_fields)))])

            self.add_test_case(
                module=module,
                submodule=submodule,
                title=f"验证L9正交表第{i+1}组参数组合",
                precondition="系统正常运行，参数配置环境准备完成",
                test_steps=f"1. 设置参数组合：{param_desc}\n2. 执行功能操作\n3. 验证结果正确性",
                expected="系统正确处理参数组合，功能正常执行",
                priority=Priority.P1,
                methods=[TestMethod.ORTHOGONAL],
                remark=f"L9正交表第{i+1}组：{param_desc}"
            )

    def generate_error_guessing_cases(self, analysis: RequirementAnalysis, historical_defects: List[str] = None):
        """生成错误推测测试用例"""
        module = "错误推测"

        # 基于历史缺陷的测试用例
        if historical_defects:
            for i, defect in enumerate(historical_defects):
                self.add_test_case(
                    module=module,
                    submodule="历史缺陷回归",
                    title=f"验证历史缺陷{i+1}的修复效果",
                    precondition="系统正常运行，具备缺陷复现条件",
                    test_steps=f"1. 复现历史缺陷场景：{defect}\n2. 验证修复效果\n3. 确认无回归",
                    expected="历史缺陷已修复，功能正常，无新的回归问题",
                    priority=Priority.P0,
                    methods=[TestMethod.ERROR_GUESSING],
                    remark=f"历史缺陷{i+1}回归测试"
                )

        # 常见错误场景推测
        common_errors = [
            ("并发访问", "多用户同时操作相同数据", "系统正确处理并发，数据一致性保持"),
            ("内存泄漏", "长时间运行系统，执行大量操作", "系统内存使用稳定，无内存泄漏"),
            ("SQL注入", "在输入框中输入SQL注入代码", "系统正确过滤恶意代码，数据安全"),
            ("XSS攻击", "输入包含脚本的恶意代码", "系统正确转义特殊字符，防止XSS"),
            ("缓存问题", "修改数据后立即查询", "系统显示最新数据，缓存更新及时")
        ]

        for error_type, test_scenario, expected in common_errors:
            self.add_test_case(
                module=module,
                submodule=error_type,
                title=f"验证{error_type}场景的处理",
                precondition="系统正常运行，具备测试环境",
                test_steps=f"1. {test_scenario}\n2. 观察系统行为\n3. 验证安全性和稳定性",
                expected=expected,
                priority=Priority.P1,
                methods=[TestMethod.ERROR_GUESSING],
                remark=f"错误推测-{error_type}测试"
            )

    def generate_ui_validation_cases(self, analysis: RequirementAnalysis):
        """生成UI验证测试用例"""
        module = "界面验证"

        for element in analysis.ui_elements:
            # 界面元素显示测试
            self.add_test_case(
                module=module,
                submodule="界面元素",
                title=f"验证{element}界面元素显示",
                precondition="系统正常运行，用户已登录",
                test_steps=f"1. 导航到包含{element}的页面\n2. 验证{element}是否正确显示\n3. 检查样式和布局",
                expected=f"{element}正确显示，样式符合设计要求",
                priority=Priority.P2,
                methods=[TestMethod.SCENARIO],
                remark=f"UI元素验证-{element}"
            )

            # 界面交互测试
            if "按钮" in element:
                self.add_test_case(
                    module=module,
                    submodule="界面交互",
                    title=f"验证{element}界面交互功能",
                    precondition="系统正常运行，用户已登录",
                    test_steps=f"1. 点击{element}\n2. 验证响应时间\n3. 检查页面跳转或功能执行",
                    expected=f"{element}响应及时，功能正确执行",
                    priority=Priority.P1,
                    methods=[TestMethod.SCENARIO],
                    remark=f"UI交互验证-{element}"
                )

    def generate_all_test_cases(self, requirement_text: str, historical_defects: List[str] = None) -> List[TestCase]:
        """
        生成所有类型的测试用例

        Args:
            requirement_text: 需求文档内容
            historical_defects: 历史缺陷列表

        Returns:
            List[TestCase]: 生成的测试用例列表
        """
        # 分析需求
        analysis = self.analyze_requirements(requirement_text)

        # 生成各种类型的测试用例
        self.generate_boundary_value_cases(analysis)
        self.generate_equivalence_class_cases(analysis)
        self.generate_scenario_cases(analysis)
        self.generate_state_transition_cases(analysis)
        self.generate_decision_table_cases(analysis)
        self.generate_orthogonal_cases(analysis)
        self.generate_error_guessing_cases(analysis, historical_defects)
        self.generate_ui_validation_cases(analysis)

        return self.test_cases

    def export_to_excel(self, filename: str = None) -> str:
        """
        导出测试用例到Excel文件

        Args:
            filename: 输出文件名，如果为None则自动生成

        Returns:
            str: 生成的文件路径
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_cases_{timestamp}.xlsx"

        # 转换为DataFrame
        data = []
        for case in self.test_cases:
            data.append({
                self.headers["Module"]: case.module,
                self.headers["Submodule"]: case.submodule,
                self.headers["CaseID"]: case.case_id,
                self.headers["Title"]: getattr(case, 'title', ''),  # 添加标题字段
                self.headers["Precondition"]: case.precondition,
                self.headers["TestSteps"]: case.test_steps,
                self.headers["Expected"]: case.expected,
                self.headers["Actual"]: case.actual,
                self.headers["Priority"]: case.priority.value,
                self.headers["Remark"]: case.remark
            })

        df = pd.DataFrame(data)

        # 导出到Excel
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='测试用例', index=False)

            # 设置列宽
            worksheet = writer.sheets['测试用例']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width

        return filename

    def export_to_markdown(self, filename: str = None) -> str:
        """
        导出测试用例到Markdown格式

        Returns:
            str: Markdown格式的测试用例
        """
        # 构建表头
        headers = [
            self.headers["Module"],
            self.headers["Submodule"],
            self.headers["CaseID"],
            self.headers["Title"],  # 添加标题字段
            self.headers["Precondition"],
            self.headers["TestSteps"],
            self.headers["Expected"],
            self.headers["Actual"],
            self.headers["Priority"],
            self.headers["Remark"]
        ]

        markdown = "# 功能测试用例\n\n"
        markdown += "| " + " | ".join(headers) + " |\n"
        markdown += "| " + " | ".join(["---"] * len(headers)) + " |\n"

        # 添加测试用例数据
        for case in self.test_cases:
            row = [
                case.module,
                case.submodule,
                case.case_id,
                getattr(case, 'title', ''),  # 添加标题字段
                case.precondition.replace('\n', '<br>'),
                case.test_steps.replace('\n', '<br>'),
                case.expected.replace('\n', '<br>'),
                case.actual,
                case.priority.value,
                case.remark
            ]
            markdown += "| " + " | ".join(row) + " |\n"

        # 如果提供了文件名，保存到文件
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(markdown)
            return filename

        return markdown

    def generate_statistics_report(self) -> str:
        """
        生成测试方法应用统计报告

        Returns:
            str: 统计报告
        """
        total_cases = len(self.test_cases)

        report = "\n## 测试方法应用统计\n\n"
        report += f"**总测试用例数：** {total_cases}\n\n"

        # 按优先级统计
        priority_stats = {}
        for case in self.test_cases:
            priority = case.priority.value
            priority_stats[priority] = priority_stats.get(priority, 0) + 1

        report += "### 优先级分布\n"
        for priority, count in sorted(priority_stats.items()):
            percentage = (count / total_cases * 100) if total_cases > 0 else 0
            report += f"- {priority}: {count} 个用例 ({percentage:.1f}%)\n"

        report += "\n### 测试方法覆盖\n"
        for method, count in self.method_stats.items():
            if count > 0:
                percentage = (count / total_cases * 100) if total_cases > 0 else 0
                report += f"- {method.value}: {count} 个用例 ({percentage:.1f}%)\n"

        # 模块分布统计
        module_stats = {}
        for case in self.test_cases:
            module = case.module
            module_stats[module] = module_stats.get(module, 0) + 1

        report += "\n### 模块覆盖分布\n"
        for module, count in sorted(module_stats.items()):
            percentage = (count / total_cases * 100) if total_cases > 0 else 0
            report += f"- {module}: {count} 个用例 ({percentage:.1f}%)\n"

        return report

    def generate_state_diagram_plantuml(self, states: List[str]) -> str:
        """
        生成状态转换图的PlantUML代码

        Args:
            states: 状态列表

        Returns:
            str: PlantUML代码
        """
        if not states:
            return ""

        plantuml = "@startuml\n"
        plantuml += "title 状态转换图\n\n"

        # 添加状态
        for state in states:
            plantuml += f"state {state}\n"

        plantuml += "\n"

        # 添加转换关系
        for i in range(len(states) - 1):
            plantuml += f"{states[i]} --> {states[i+1]}\n"

        # 添加初始和结束状态
        if states:
            plantuml += f"[*] --> {states[0]}\n"
            plantuml += f"{states[-1]} --> [*]\n"

        plantuml += "@enduml\n"

        return plantuml

    def generate_decision_table_display(self, conditions: List[str], actions: List[str]) -> str:
        """
        生成判定表展示

        Args:
            conditions: 条件列表
            actions: 动作列表

        Returns:
            str: 判定表的Markdown格式
        """
        table = "\n## 判定表示例\n\n"

        # 表头
        headers = ["规则"] + [f"R{i+1}" for i in range(4)]  # 示例4个规则
        table += "| " + " | ".join(headers) + " |\n"
        table += "| " + " | ".join(["---"] * len(headers)) + " |\n"

        # 条件行
        for i, condition in enumerate(conditions[:3]):  # 限制3个条件
            row = [condition] + ["T", "T", "F", "F"][i:i+1] * 4
            table += "| " + " | ".join(row[:5]) + " |\n"

        # 分隔线
        table += "| **动作** | | | | |\n"

        # 动作行
        for action in actions[:2]:  # 限制2个动作
            row = [action] + ["X", "", "X", ""]
            table += "| " + " | ".join(row) + " |\n"

        return table

    def generate_orthogonal_table_display(self) -> str:
        """
        生成L9正交表展示

        Returns:
            str: L9正交表的Markdown格式
        """
        table = "\n## L9正交实验表\n\n"

        headers = ["实验号", "因子A", "因子B", "因子C", "因子D"]
        table += "| " + " | ".join(headers) + " |\n"
        table += "| " + " | ".join(["---"] * len(headers)) + " |\n"

        l9_table = [
            [1, 1, 1, 1, 1],
            [2, 1, 2, 2, 2],
            [3, 1, 3, 3, 3],
            [4, 2, 1, 2, 3],
            [5, 2, 2, 3, 1],
            [6, 2, 3, 1, 2],
            [7, 3, 1, 3, 2],
            [8, 3, 2, 1, 3],
            [9, 3, 3, 2, 1]
        ]

        for row in l9_table:
            table += "| " + " | ".join(map(str, row)) + " |\n"

        table += "\n**说明：** 1=最小值, 2=中间值, 3=最大值\n"

        return table


def main():
    """主函数 - 使用示例"""

    # 示例需求文档
    sample_requirement = """
    用户登录系统需求文档

    功能：用户登录管理
    模块：用户认证系统

    输入字段：
    - 用户名：长度3-20字符，必填
    - 密码：长度6-16字符，必填
    - 验证码：4位数字，必填

    业务规则：
    1. 用户名和密码正确时，登录成功
    2. 连续3次登录失败，账户锁定30分钟
    3. 验证码错误时，需要重新获取

    状态：未登录 -> 登录中 -> 已登录

    流程：
    1. 用户输入登录信息
    2. 系统验证用户信息
    3. 验证成功跳转到主页

    界面元素：
    - 登录按钮
    - 忘记密码链接
    - 注册页面链接

    约束：
    - 密码必须包含字母和数字
    - 用户名不能包含特殊字符
    """

    # 历史缺陷示例
    historical_defects = [
        "登录时SQL注入漏洞",
        "密码明文传输安全问题",
        "验证码可以重复使用",
        "登录状态在浏览器关闭后未清除"
    ]

    # 自定义字段标题（可选）
    custom_headers = {
        "Module": "功能模块",
        "CaseID": "测试编号",
        "TestSteps": "操作步骤"
    }

    # 创建测试用例生成器
    generator = TestCaseGenerator(custom_headers)

    print("🚀 开始生成功能测试用例...")

    # 生成测试用例
    test_cases = generator.generate_all_test_cases(sample_requirement, historical_defects)

    print(f"✅ 成功生成 {len(test_cases)} 个测试用例")

    # 导出Excel文件
    excel_file = generator.export_to_excel()
    print(f"📊 Excel文件已生成: {excel_file}")

    # 生成Markdown报告
    markdown_content = generator.export_to_markdown()

    # 添加统计报告
    stats_report = generator.generate_statistics_report()
    markdown_content += stats_report

    # 添加状态转换图
    analysis = generator.analyze_requirements(sample_requirement)
    if analysis.states:
        plantuml_code = generator.generate_state_diagram_plantuml(analysis.states)
        markdown_content += f"\n## 状态转换图\n\n```plantuml\n{plantuml_code}\n```\n"

    # 添加判定表
    decision_table = generator.generate_decision_table_display(
        ["用户名正确", "密码正确", "验证码正确"],
        ["登录成功", "显示错误信息"]
    )
    markdown_content += decision_table

    # 添加正交表
    orthogonal_table = generator.generate_orthogonal_table_display()
    markdown_content += orthogonal_table

    # 保存Markdown文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    markdown_file = f"test_cases_report_{timestamp}.md"
    with open(markdown_file, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    print(f"📝 Markdown报告已生成: {markdown_file}")

    # 显示部分测试用例
    print("\n📋 测试用例预览（前5个）:")
    print("=" * 80)
    for i, case in enumerate(test_cases[:5]):
        print(f"\n{i+1}. {case.case_id} - {case.module}/{case.submodule}")
        print(f"   优先级: {case.priority.value}")
        print(f"   方法: {case.remark}")
        print(f"   步骤: {case.test_steps[:100]}...")

    print(f"\n🎯 完成！共生成 {len(test_cases)} 个测试用例")
    print(f"📁 输出文件:")
    print(f"   - Excel: {excel_file}")
    print(f"   - Markdown: {markdown_file}")


if __name__ == "__main__":
    main()
