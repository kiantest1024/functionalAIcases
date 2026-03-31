#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专业测试用例生成器
基于专业测试工程师要求的高质量测试用例生成系统
"""

import json
import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

from .real_ai_generator import RealAITestCaseGenerator, AIConfig
from .comprehensive_test_generator import ComprehensiveTestGenerator
from .test_case_generator import TestCase, Priority, TestMethod
from .professional_ai_prompt import ProfessionalAIPrompt

@dataclass
class ProfessionalTestCase:
    """专业测试用例数据结构"""
    case_id: str
    feature_module: str
    title: str
    test_type: str
    preconditions: str
    test_steps: str
    expected_result: str
    related_requirement_id: str
    priority: str
    notes: str = ""

class ProfessionalTestGenerator:
    """专业测试用例生成器"""
    
    def __init__(self, ai_config: Optional[AIConfig] = None):
        self.ai_config = ai_config
        self.prompt_generator = ProfessionalAIPrompt()
        self.test_cases: List[ProfessionalTestCase] = []
        self.case_counter = 0
        
        # 初始化AI生成器
        if ai_config and ai_config.api_key:
            try:
                self.ai_generator = RealAITestCaseGenerator(ai_config)
                self.use_real_ai = True
                print("✅ 使用真实AI生成器")
            except Exception as e:
                print(f"⚠️ 真实AI初始化失败，使用备用生成器: {e}")
                self.ai_generator = ComprehensiveTestGenerator()
                self.use_real_ai = False
        else:
            self.ai_generator = ComprehensiveTestGenerator()
            self.use_real_ai = False
            print("🔧 使用备用生成器")
    
    def generate_professional_test_cases(self, requirement_text: str) -> List[ProfessionalTestCase]:
        """生成专业测试用例"""
        print("🚀 开始专业测试用例生成...")
        
        try:
            if self.use_real_ai:
                # 使用真实AI生成
                test_cases = self._generate_with_real_ai(requirement_text)
            else:
                # 使用备用方案
                test_cases = self._generate_with_fallback(requirement_text)
            
            print(f"✅ 成功生成 {len(test_cases)} 个专业测试用例")
            self.test_cases = test_cases
            return test_cases
            
        except Exception as e:
            print(f"❌ 专业测试用例生成失败: {e}")
            # 最终备用方案
            return self._generate_basic_cases(requirement_text)
    
    def _generate_with_real_ai(self, requirement_text: str) -> List[ProfessionalTestCase]:
        """使用真实AI生成专业测试用例"""
        print("🤖 使用真实AI生成专业测试用例...")
        
        # 构建专业提示词
        system_prompt = self.prompt_generator.get_system_prompt()
        analysis_prompt = self.prompt_generator.get_analysis_prompt(requirement_text)
        
        try:
            # 调用AI API
            ai_response = self.ai_generator.call_ai_api(analysis_prompt, system_prompt)
            print(f"✅ AI响应成功，长度: {len(ai_response)}")
            
            # 解析AI响应
            test_cases = self._parse_ai_response(ai_response)
            
            if not test_cases:
                print("⚠️ AI响应解析失败，使用备用方案")
                return self._generate_with_fallback(requirement_text)
            
            return test_cases
            
        except Exception as e:
            print(f"❌ 真实AI生成失败: {e}")
            return self._generate_with_fallback(requirement_text)
    
    def _parse_ai_response(self, ai_response: str) -> List[ProfessionalTestCase]:
        """解析AI响应为专业测试用例"""
        try:
            # 尝试提取JSON部分
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            
            if json_start == -1:
                json_start = ai_response.find('[')
                json_end = ai_response.rfind(']') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = ai_response[json_start:json_end]
                data = json.loads(json_str)
                
                # 处理不同的JSON结构
                if isinstance(data, dict) and 'test_cases' in data:
                    cases_data = data['test_cases']
                elif isinstance(data, list):
                    cases_data = data
                else:
                    cases_data = [data] if isinstance(data, dict) else []
                
                # 转换为专业测试用例
                test_cases = []
                for i, case_data in enumerate(cases_data):
                    try:
                        test_case = ProfessionalTestCase(
                            case_id=case_data.get('case_id', f'TC_AI_{i+1:03d}'),
                            feature_module=case_data.get('feature_module', '功能模块'),
                            title=case_data.get('title', '测试用例标题'),
                            test_type=case_data.get('test_type', '正向'),
                            preconditions=case_data.get('preconditions', '系统正常运行'),
                            test_steps=case_data.get('test_steps', '1. 执行操作'),
                            expected_result=case_data.get('expected_result', '操作成功'),
                            related_requirement_id=case_data.get('related_requirement_id', ''),
                            priority=case_data.get('priority', '中'),
                            notes=case_data.get('notes', '')
                        )
                        test_cases.append(test_case)
                    except Exception as e:
                        print(f"⚠️ 解析第{i+1}个用例失败: {e}")
                        continue
                
                print(f"✅ 成功解析 {len(test_cases)} 个AI生成的测试用例")
                return test_cases
            
            else:
                print("❌ 无法找到有效的JSON格式")
                return []
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON解析失败: {e}")
            return []
        except Exception as e:
            print(f"❌ 响应解析异常: {e}")
            return []
    
    def _generate_with_fallback(self, requirement_text: str) -> List[ProfessionalTestCase]:
        """使用备用方案生成测试用例"""
        print("🔧 使用备用方案生成测试用例...")
        
        try:
            # 使用现有的全面测试生成器
            basic_cases = self.ai_generator.generate_comprehensive_test_cases(requirement_text)
            
            # 转换为专业格式
            professional_cases = []
            for case in basic_cases:
                professional_case = self._convert_to_professional(case)
                professional_cases.append(professional_case)
            
            print(f"✅ 备用方案生成 {len(professional_cases)} 个测试用例")
            return professional_cases
            
        except Exception as e:
            print(f"❌ 备用方案失败: {e}")
            return self._generate_basic_cases(requirement_text)
    
    def _convert_to_professional(self, basic_case: TestCase) -> ProfessionalTestCase:
        """将基础测试用例转换为专业格式"""
        # 映射测试类型
        test_type_mapping = {
            "边界值": "边界",
            "等价类": "正向",
            "异常处理": "异常",
            "业务流程": "正向",
            "功能测试": "正向"
        }
        
        test_type = "正向"
        for key, value in test_type_mapping.items():
            if key in basic_case.remark:
                test_type = value
                break
        
        # 映射优先级
        priority_mapping = {
            Priority.P0: "高",
            Priority.P1: "中", 
            Priority.P2: "低"
        }
        
        return ProfessionalTestCase(
            case_id=basic_case.case_id,
            feature_module=basic_case.module,
            title=getattr(basic_case, 'title', f"验证{basic_case.submodule}功能"),
            test_type=test_type,
            preconditions=basic_case.precondition,
            test_steps=basic_case.test_steps,
            expected_result=basic_case.expected,
            related_requirement_id="",
            priority=priority_mapping.get(basic_case.priority, "中"),
            notes=basic_case.remark
        )
    
    def _generate_basic_cases(self, requirement_text: str) -> List[ProfessionalTestCase]:
        """生成基础测试用例（最终备用方案）"""
        print("🔧 使用基础方案生成测试用例...")
        
        # 简单的需求分析
        modules = self._extract_modules(requirement_text)
        
        basic_cases = []
        for i, module in enumerate(modules[:5]):  # 限制数量
            case = ProfessionalTestCase(
                case_id=f"TC_BASIC_{i+1:03d}",
                feature_module=module,
                title=f"验证{module}基本功能",
                test_type="正向",
                preconditions="系统正常运行，用户已登录",
                test_steps=f"1. 进入{module}页面\n2. 执行基本操作\n3. 验证操作结果",
                expected_result=f"{module}功能正常工作，操作成功",
                related_requirement_id="",
                priority="中",
                notes="基础功能验证"
            )
            basic_cases.append(case)
        
        return basic_cases
    
    def _extract_modules(self, text: str) -> List[str]:
        """提取功能模块"""
        # 简单的模块提取逻辑
        common_modules = ["用户管理", "个人信息", "数据处理", "界面交互", "业务流程"]
        
        detected_modules = []
        for module in common_modules:
            if module in text or module.replace("管理", "") in text:
                detected_modules.append(module)
        
        if not detected_modules:
            detected_modules = ["核心功能"]
        
        return detected_modules
    
    def export_to_excel(self, file_path: str):
        """导出为Excel格式"""
        try:
            import pandas as pd
            
            # 转换为DataFrame
            data = []
            for case in self.test_cases:
                data.append({
                    '用例ID': case.case_id,
                    '功能模块': case.feature_module,
                    '用例标题': case.title,
                    '测试类型': case.test_type,
                    '前置条件': case.preconditions,
                    '测试步骤': case.test_steps,
                    '预期结果': case.expected_result,
                    '关联需求ID': case.related_requirement_id,
                    '优先级': case.priority,
                    '备注': case.notes
                })
            
            df = pd.DataFrame(data)
            df.to_excel(file_path, index=False, engine='openpyxl')
            print(f"✅ Excel文件导出成功: {file_path}")
            
        except Exception as e:
            print(f"❌ Excel导出失败: {e}")
    
    def export_to_markdown(self, file_path: str):
        """导出为Markdown格式"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("# 专业功能测试用例报告\n\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(f"测试用例总数: {len(self.test_cases)}\n\n")
                
                for i, case in enumerate(self.test_cases, 1):
                    f.write(f"## 测试用例 {i}: {case.title}\n\n")
                    f.write(f"**用例ID**: {case.case_id}\n\n")
                    f.write(f"**功能模块**: {case.feature_module}\n\n")
                    f.write(f"**测试类型**: {case.test_type}\n\n")
                    f.write(f"**优先级**: {case.priority}\n\n")
                    f.write(f"**前置条件**: {case.preconditions}\n\n")
                    f.write("**测试步骤**:\n")
                    f.write(f"{case.test_steps}\n\n")
                    f.write(f"**预期结果**: {case.expected_result}\n\n")
                    if case.related_requirement_id:
                        f.write(f"**关联需求ID**: {case.related_requirement_id}\n\n")
                    if case.notes:
                        f.write(f"**备注**: {case.notes}\n\n")
                    f.write("---\n\n")
            
            print(f"✅ Markdown文件导出成功: {file_path}")
            
        except Exception as e:
            print(f"❌ Markdown导出失败: {e}")
