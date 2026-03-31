#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试用例生成器基础模块
提供测试用例生成的核心类和方法
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import pandas as pd
from datetime import datetime


class Priority(Enum):
    """测试用例优先级"""
    P0 = "P0"  # 最高优先级 - 核心功能
    P1 = "P1"  # 高优先级 - 重要功能
    P2 = "P2"  # 中优先级 - 一般功能
    P3 = "P3"  # 低优先级 - 次要功能


class TestMethod(Enum):
    """测试设计方法"""
    EQUIVALENCE = "等价类划分"
    BOUNDARY_VALUE = "边界值分析"
    DECISION_TABLE = "判定表"
    CAUSE_EFFECT = "因果图"
    STATE_TRANSITION = "状态转换"
    SCENARIO = "场景法"
    ERROR_GUESSING = "错误推测"
    ORTHOGONAL = "正交试验"
    COMBINATION = "组合测试"
    FLOW_ANALYSIS = "流程分析"
    AI_ENHANCED = "AI增强"  # 新增：AI增强测试方法


@dataclass
class RequirementAnalysis:
    """需求分析结果"""
    complexity_score: float = 0.0  # 复杂度评分
    risk_areas: List[str] = field(default_factory=list)  # 风险区域
    key_paths: List[str] = field(default_factory=list)  # 关键路径
    business_rules: List[str] = field(default_factory=list)  # 业务规则
    integration_points: List[str] = field(default_factory=list)  # 集成点


@dataclass
class TestCase:
    """测试用例数据类"""
    module: str  # 模块
    submodule: str  # 子模块
    case_id: str  # 用例编号
    title: str  # 用例标题
    precondition: str  # 前置条件
    test_steps: str  # 测试步骤
    expected: str  # 预期结果
    priority: Priority  # 优先级
    remark: str = ""  # 备注
    methods_used: List[TestMethod] = field(default_factory=list)  # 使用的测试方法
    
    def to_dict(self, custom_fields: Optional[List[str]] = None) -> Dict:
        """转换为字典 - 支持自定义字段
        
        Args:
            custom_fields: 自定义字段列表，如果为None则使用默认双语模板
            
        Returns:
            Dict: 包含测试用例数据的字典
        """
        # 默认双语模板
        default_template = {
            '用例编号 | Use Case #': self.case_id,
            '模块 | Module': self.module,
            '子模块 | Submodule': self.submodule,
            '用例标题 | Use Case Title': self.title,
            '预置条件 | Present Condition': self.precondition,
            '用例步骤 | Use case steps': self.test_steps,
            '预期结果 | Expected result': self.expected,
            '实际结果 | Actual result': '',
            '测试负责人 | Test owner': '',
            '优先级 | Priority': self.priority.value,
            '是否执行 | Whether to implement': '',
            '是否评审 | Whether to review': '',
            '备注 | Remarks': self.remark if self.remark else ''
        }
        
        # 如果没有自定义字段，返回默认模板
        if not custom_fields:
            return default_template
        
        # 字段值映射表 - 将字段名映射到实际值
        field_value_map = {
            # 用例编号相关
            '用例编号': self.case_id,
            'Use Case #': self.case_id,
            '用例编号 | Use Case #': self.case_id,
            '用例ID': self.case_id,
            'case_id': self.case_id,
            
            # 模块相关
            '模块': self.module,
            'Module': self.module,
            '模块 | Module': self.module,
            '功能模块': self.module,
            
            # 子模块相关
            '子模块': self.submodule,
            'Submodule': self.submodule,
            '子模块 | Submodule': self.submodule,
            
            # 标题相关
            '用例标题': self.title,
            'Use Case Title': self.title,
            '用例标题 | Use Case Title': self.title,
            'title': self.title,
            
            # 前置条件相关
            '预置条件': self.precondition,
            'Present Condition': self.precondition,
            '预置条件 | Present Condition': self.precondition,
            '前置条件': self.precondition,
            'precondition': self.precondition,
            
            # 测试步骤相关
            '用例步骤': self.test_steps,
            'Use case steps': self.test_steps,
            '用例步骤 | Use case steps': self.test_steps,
            '测试步骤': self.test_steps,
            'test_steps': self.test_steps,
            
            # 预期结果相关
            '预期结果': self.expected,
            'Expected result': self.expected,
            '预期结果 | Expected result': self.expected,
            'expected': self.expected,
            
            # 实际结果相关
            '实际结果': '',
            'Actual result': '',
            '实际结果 | Actual result': '',
            
            # 测试负责人相关
            '测试负责人': '',
            'Test owner': '',
            '测试负责人 | Test owner': '',
            
            # 优先级相关
            '优先级': self.priority.value,
            'Priority': self.priority.value,
            '优先级 | Priority': self.priority.value,
            
            # 是否执行相关
            '是否执行': '',
            'Whether to implement': '',
            '是否执行 | Whether to implement': '',
            
            # 是否评审相关
            '是否评审': '',
            'Whether to review': '',
            '是否评审 | Whether to review': '',
            
            # 备注相关
            '备注': self.remark if self.remark else '',
            'Remarks': self.remark if self.remark else '',
            '备注 | Remarks': self.remark if self.remark else ''
        }
        
        # 使用自定义字段构建字典
        result = {}
        for field in custom_fields:
            field = field.strip()
            # 在映射表中查找对应的值
            if field in field_value_map:
                result[field] = field_value_map[field]
            else:
                # 如果找不到映射，设置为空字符串
                result[field] = ''
        
        return result


class TestCaseGenerator:
    """测试用例生成器基类"""
    
    def __init__(self, custom_headers: Optional[Dict[str, str]] = None):
        """
        初始化测试用例生成器
        
        Args:
            custom_headers: 自定义字段标题映射，格式为 {'字段1': '新名称1', ...}
                          或者是一个字段列表 ['字段1', '字段2', ...]
        """
        self.test_cases: List[TestCase] = []
        self.case_counter = 0
        
        # 处理自定义字段
        self.custom_fields = None
        if custom_headers:
            if isinstance(custom_headers, dict):
                # 如果是字典，提取字段列表
                self.custom_fields = list(custom_headers.keys())
            elif isinstance(custom_headers, list):
                # 如果已经是列表，直接使用
                self.custom_fields = custom_headers
        
    def generate_case_id(self, module: str, submodule: str = "") -> str:
        """生成测试用例编号"""
        self.case_counter += 1
        prefix = f"{module[:2].upper()}"
        if submodule:
            prefix += f"_{submodule[:2].upper()}"
        return f"TC_{prefix}_{self.case_counter:03d}"
    
    def add_test_case(self, 
                     module: str,
                     submodule: str,
                     precondition: str,
                     test_steps: str,
                     expected: str,
                     priority: Priority,
                     methods: List[TestMethod],
                     remark: str = "",
                     title: str = "") -> TestCase:
        """
        添加测试用例
        
        Args:
            module: 模块名称
            submodule: 子模块名称
            precondition: 前置条件
            test_steps: 测试步骤
            expected: 预期结果
            priority: 优先级
            methods: 使用的测试方法
            remark: 备注
            title: 用例标题（如果为空则自动生成）
            
        Returns:
            TestCase: 生成的测试用例
        """
        case_id = self.generate_case_id(module, submodule)
        
        if not title:
            # 从测试步骤中提取标题
            first_step = test_steps.split('\n')[0].strip()
            title = first_step[:50] if len(first_step) > 50 else first_step
        
        test_case = TestCase(
            module=module,
            submodule=submodule,
            case_id=case_id,
            title=title,
            precondition=precondition,
            test_steps=test_steps,
            expected=expected,
            priority=priority,
            remark=remark,
            methods_used=methods
        )
        
        self.test_cases.append(test_case)
        return test_case
    
    def analyze_requirements(self, requirement_text: str) -> RequirementAnalysis:
        """
        分析需求文档（基础版本）
        
        Args:
            requirement_text: 需求文档文本
            
        Returns:
            RequirementAnalysis: 需求分析结果
        """
        analysis = RequirementAnalysis()
        
        # 基础复杂度分析
        text_length = len(requirement_text)
        if text_length < 500:
            analysis.complexity_score = 0.3
        elif text_length < 1500:
            analysis.complexity_score = 0.6
        else:
            analysis.complexity_score = 0.9
        
        # 简单的关键词识别
        keywords = {
            'risk': ['安全', '权限', '支付', '金额', '密码', 'security', 'payment'],
            'integration': ['接口', '集成', '第三方', 'API', 'integration'],
            'business': ['规则', '条件', '如果', '当', 'rule', 'condition']
        }
        
        for keyword in keywords['risk']:
            if keyword in requirement_text:
                analysis.risk_areas.append(f"包含{keyword}相关功能")
        
        for keyword in keywords['integration']:
            if keyword in requirement_text:
                analysis.integration_points.append(f"包含{keyword}相关功能")
                
        for keyword in keywords['business']:
            if keyword in requirement_text:
                analysis.business_rules.append(f"包含{keyword}相关逻辑")
        
        return analysis
    
    def export_to_excel(self, file_path: str) -> str:
        """
        导出测试用例到Excel文件
        
        Args:
            file_path: 导出文件路径
            
        Returns:
            str: 导出文件的完整路径
        """
        if not self.test_cases:
            raise ValueError("没有可导出的测试用例")
        
        # 转换为DataFrame - 传递自定义字段
        data = [tc.to_dict(custom_fields=self.custom_fields) for tc in self.test_cases]
        df = pd.DataFrame(data)
        
        # 如果有自定义字段，确保列顺序与自定义字段顺序一致
        if self.custom_fields:
            df = df[self.custom_fields]
        
        # 导出到Excel
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='测试用例')
            
            # 自动调整列宽
            worksheet = writer.sheets['测试用例']
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).map(len).max(),
                    len(str(col))
                ) + 2
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)
        
        return file_path
    
    def export_to_markdown(self, file_path: str) -> str:
        """
        导出测试用例到Markdown文件
        
        Args:
            file_path: 导出文件路径
            
        Returns:
            str: 导出文件的完整路径
        """
        if not self.test_cases:
            raise ValueError("没有可导出的测试用例")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# 测试用例文档\n\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"测试用例总数: {len(self.test_cases)}\n\n")
            f.write("---\n\n")
            
            # 按模块分组
            modules = {}
            for tc in self.test_cases:
                if tc.module not in modules:
                    modules[tc.module] = []
                modules[tc.module].append(tc)
            
            # 输出每个模块的测试用例
            for module, cases in modules.items():
                f.write(f"## {module}\n\n")
                
                for tc in cases:
                    f.write(f"### {tc.case_id}: {tc.title}\n\n")
                    f.write(f"**子模块**: {tc.submodule}\n\n")
                    f.write(f"**优先级**: {tc.priority.value}\n\n")
                    f.write(f"**前置条件**: {tc.precondition}\n\n")
                    f.write(f"**测试步骤**:\n\n{tc.test_steps}\n\n")
                    f.write(f"**预期结果**: {tc.expected}\n\n")
                    
                    if tc.methods_used:
                        methods_str = ', '.join([m.value for m in tc.methods_used])
                        f.write(f"**测试方法**: {methods_str}\n\n")
                    
                    if tc.remark:
                        f.write(f"**备注**: {tc.remark}\n\n")
                    
                    f.write("---\n\n")
        
        return file_path
    
    def clear(self):
        """清空所有测试用例"""
        self.test_cases.clear()
        self.case_counter = 0
    
    def get_statistics(self) -> Dict:
        """获取测试用例统计信息"""
        stats = {
            'total': len(self.test_cases),
            'by_priority': {},
            'by_module': {},
            'by_method': {}
        }
        
        for tc in self.test_cases:
            # 按优先级统计
            priority_key = tc.priority.value
            stats['by_priority'][priority_key] = stats['by_priority'].get(priority_key, 0) + 1
            
            # 按模块统计
            stats['by_module'][tc.module] = stats['by_module'].get(tc.module, 0) + 1
            
            # 按测试方法统计
            for method in tc.methods_used:
                method_key = method.value
                stats['by_method'][method_key] = stats['by_method'].get(method_key, 0) + 1
        
        return stats
    
    def export_ai_enhanced_report(self, file_path: str) -> str:
        """
        导出AI增强报告（基础版本）
        
        Args:
            file_path: 导出文件路径
            
        Returns:
            str: 导出文件的完整路径
        """
        if not self.test_cases:
            raise ValueError("没有可导出的测试用例")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# 🤖 AI增强功能测试用例报告\n\n")
            f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**总测试用例数**: {len(self.test_cases)}\n\n")
            
            # AI分析报告（如果有）
            if hasattr(self, 'ai_analysis') and self.ai_analysis:
                f.write("## 📊 AI需求分析\n\n")
                f.write(f"**复杂度评分**: {self.ai_analysis.complexity_score:.2f}\n\n")
                
                if self.ai_analysis.risk_areas:
                    f.write("### ⚠️ 风险区域\n")
                    for i, risk in enumerate(self.ai_analysis.risk_areas, 1):
                        f.write(f"{i}. {risk}\n")
                    f.write("\n")
                
                if self.ai_analysis.critical_paths:
                    f.write("### 🎯 关键路径\n")
                    for i, path in enumerate(self.ai_analysis.critical_paths, 1):
                        f.write(f"{i}. {path}\n")
                    f.write("\n")
            
            # 测试用例详细列表
            f.write("## 📋 测试用例详情\n\n")
            
            # 按模块分组
            modules = {}
            for tc in self.test_cases:
                if tc.module not in modules:
                    modules[tc.module] = []
                modules[tc.module].append(tc)
            
            # 输出每个模块的测试用例
            for module, cases in modules.items():
                f.write(f"### {module}\n\n")
                
                for tc in cases:
                    f.write(f"#### {tc.case_id}: {tc.title}\n\n")
                    f.write(f"**子模块**: {tc.submodule}\n\n")
                    f.write(f"**优先级**: {tc.priority.value}\n\n")
                    f.write(f"**前置条件**: {tc.precondition}\n\n")
                    f.write(f"**测试步骤**:\n\n{tc.test_steps}\n\n")
                    f.write(f"**预期结果**: {tc.expected}\n\n")
                    
                    if tc.methods_used:
                        methods_str = ', '.join([m.value for m in tc.methods_used])
                        f.write(f"**测试方法**: {methods_str}\n\n")
                    
                    if tc.remark:
                        f.write(f"**备注**: {tc.remark}\n\n")
                    
                    f.write("---\n\n")
            
            # 统计信息
            stats = self.get_statistics()
            f.write("## 📊 统计信息\n\n")
            f.write(f"**总用例数**: {stats['total']}\n\n")
            
            if stats['by_priority']:
                f.write("### 优先级分布\n")
                for priority, count in sorted(stats['by_priority'].items()):
                    percentage = (count / stats['total'] * 100) if stats['total'] > 0 else 0
                    f.write(f"- **{priority}**: {count} 个用例 ({percentage:.1f}%)\n")
                f.write("\n")
            
            if stats['by_module']:
                f.write("### 模块分布\n")
                for module, count in sorted(stats['by_module'].items(), key=lambda x: x[1], reverse=True):
                    percentage = (count / stats['total'] * 100)
                    f.write(f"- **{module}**: {count} 个用例 ({percentage:.1f}%)\n")
                f.write("\n")
        
        return file_path
