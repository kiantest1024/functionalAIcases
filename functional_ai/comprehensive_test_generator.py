#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面的测试用例生成器
解决用例标题缺失和覆盖面不足的问题
"""

from .test_case_generator import TestCase, TestCaseGenerator, Priority, TestMethod, RequirementAnalysis
from .test_step_optimizer import TestStepOptimizer
from typing import List
import re

class ComprehensiveTestGenerator(TestCaseGenerator):
    """全面的测试用例生成器"""
    
    def __init__(self, custom_headers=None):
        super().__init__(custom_headers)
        self.step_optimizer = TestStepOptimizer()
        
    def add_comprehensive_test_case(self, module: str, submodule: str, title: str,
                                   precondition: str, test_steps: str, expected: str,
                                   priority: Priority, methods: List[TestMethod],
                                   remark: str = ""):
        """添加全面的测试用例（包含标题）"""
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
            title=title,
            precondition=precondition,
            test_steps=test_steps,
            expected=expected,
            priority=priority,
            remark=full_remark,
            methods_used=methods
        )

        self.test_cases.append(test_case)
    
    def generate_comprehensive_test_cases(self, requirement_text: str, historical_defects: List[str] = None):
        """生成全面的测试用例覆盖"""
        print("🔍 分析需求...")
        analysis = self.analyze_requirements(requirement_text)
        
        print("📝 生成全面测试用例...")
        
        # 1. 功能测试用例
        self._generate_functional_cases(analysis, requirement_text)
        
        # 2. 界面测试用例
        self._generate_ui_cases(analysis, requirement_text)
        
        # 3. 数据验证测试用例
        self._generate_data_validation_cases(analysis)
        
        # 4. 业务流程测试用例
        self._generate_business_process_cases(analysis, requirement_text)
        
        # 5. 异常处理测试用例
        self._generate_exception_handling_cases(analysis, requirement_text)
        
        # 6. 性能测试用例
        self._generate_performance_cases(analysis, requirement_text)
        
        # 7. 安全测试用例
        self._generate_security_cases(analysis, requirement_text)
        
        # 8. 兼容性测试用例
        self._generate_compatibility_cases(analysis, requirement_text)
        
        # 9. 易用性测试用例
        self._generate_usability_cases(analysis, requirement_text)
        
        # 10. 回归测试用例
        if historical_defects:
            self._generate_regression_cases(analysis, historical_defects)
        
        print(f"✅ 生成完成，共 {len(self.test_cases)} 个测试用例")
        return self.test_cases


    
    def _extract_main_function(self, requirement_text: str) -> str:
        """提取主要功能名称"""
        # 查找功能名称的模式
        patterns = [
            r'功能[：:]\s*([^\n，。]+)',
            r'([^，。\n]+)功能',
            r'系统[：:]\s*([^\n，。]+)',
            r'用户([^，。\n]+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, requirement_text)
            if matches:
                return matches[0].strip()
        
        return "核心功能"
    
    def _generate_functional_cases(self, analysis: RequirementAnalysis, requirement_text: str):
        """生成功能测试用例"""
        main_function = self._extract_main_function(requirement_text)
        
        # 正常功能测试
        self.add_comprehensive_test_case(
            module="功能测试",
            submodule="核心功能",
            title=f"验证{main_function}的正常功能",
            precondition="系统正常运行，用户已登录，数据准备完成",
            test_steps=f"1. 进入{main_function}页面\n2. 按照正常流程操作\n3. 完成{main_function}操作\n4. 验证操作结果",
            expected=f"{main_function}功能正常执行，结果符合预期",
            priority=Priority.P0,
            methods=[TestMethod.SCENARIO],
            remark="核心功能正常流程验证"
        )
        
        # 功能边界测试
        self.add_comprehensive_test_case(
            module="功能测试",
            submodule="边界功能",
            title=f"验证{main_function}的边界条件处理",
            precondition="系统正常运行，准备边界测试数据",
            test_steps=f"1. 使用边界值数据进行{main_function}操作\n2. 测试最小值、最大值情况\n3. 验证边界处理逻辑",
            expected="系统正确处理边界条件，不出现异常",
            priority=Priority.P1,
            methods=[TestMethod.BOUNDARY_VALUE],
            remark="功能边界条件验证"
        )
        
        # 功能组合测试
        self.add_comprehensive_test_case(
            module="功能测试",
            submodule="功能组合",
            title=f"验证{main_function}与其他功能的组合使用",
            precondition="系统正常运行，相关功能模块可用",
            test_steps=f"1. 同时使用{main_function}和其他相关功能\n2. 测试功能间的交互\n3. 验证组合使用的稳定性\n4. 检查数据一致性",
            expected="功能组合使用正常，无冲突，数据保持一致",
            priority=Priority.P1,
            methods=[TestMethod.SCENARIO],
            remark="功能组合使用验证"
        )
    
    def _generate_ui_cases(self, analysis: RequirementAnalysis, requirement_text: str):
        """生成界面测试用例"""
        main_function = self._extract_main_function(requirement_text)
        
        # 界面元素测试
        self.add_comprehensive_test_case(
            module="界面测试",
            submodule="界面元素",
            title=f"验证{main_function}页面界面元素显示",
            precondition="系统正常运行，用户已登录",
            test_steps=f"1. 打开{main_function}页面\n2. 检查所有界面元素是否正确显示\n3. 验证按钮、输入框、标签等元素\n4. 检查页面布局和样式",
            expected="所有界面元素正确显示，布局合理，样式正常",
            priority=Priority.P1,
            methods=[TestMethod.SCENARIO],
            remark="界面元素显示验证"
        )
        
        # 界面交互测试
        self.add_comprehensive_test_case(
            module="界面测试",
            submodule="界面交互",
            title=f"验证{main_function}页面交互功能",
            precondition="系统正常运行，页面已加载",
            test_steps="1. 测试所有可点击元素的响应\n2. 验证输入框的输入和验证\n3. 测试下拉框、复选框等控件\n4. 验证页面跳转和刷新",
            expected="所有界面交互功能正常，响应及时，操作流畅",
            priority=Priority.P1,
            methods=[TestMethod.SCENARIO],
            remark="界面交互功能验证"
        )
        
        # 响应式设计测试
        self.add_comprehensive_test_case(
            module="界面测试",
            submodule="响应式设计",
            title=f"验证{main_function}页面在不同屏幕尺寸下的显示",
            precondition="系统正常运行，准备不同尺寸的测试环境",
            test_steps="1. 在桌面端浏览器测试页面显示\n2. 在平板设备测试页面适配\n3. 在手机端测试页面响应\n4. 验证各种分辨率下的显示效果",
            expected="页面在不同设备和分辨率下都能正常显示和使用",
            priority=Priority.P2,
            methods=[TestMethod.SCENARIO],
            remark="响应式设计适配验证"
        )
        
        # 界面可访问性测试
        self.add_comprehensive_test_case(
            module="界面测试",
            submodule="可访问性",
            title=f"验证{main_function}页面的可访问性",
            precondition="系统正常运行，准备可访问性测试工具",
            test_steps="1. 使用屏幕阅读器测试页面\n2. 验证键盘导航功能\n3. 检查颜色对比度\n4. 测试alt文本和标签",
            expected="页面符合可访问性标准，支持辅助技术",
            priority=Priority.P2,
            methods=[TestMethod.SCENARIO],
            remark="界面可访问性验证"
        )
    
    def _generate_data_validation_cases(self, analysis: RequirementAnalysis):
        """生成数据验证测试用例"""
        for field in analysis.input_fields:
            field_name = field.get('name', '输入字段')
            
            # 必填字段验证
            if field.get('required', True):
                self.add_comprehensive_test_case(
                    module="数据验证",
                    submodule="必填验证",
                    title=f"验证{field_name}必填字段校验",
                    precondition="系统正常运行，用户在输入页面",
                    test_steps=f"1. 保持{field_name}字段为空\n2. 填写其他必填字段\n3. 点击提交按钮\n4. 观察系统提示",
                    expected=f"系统显示{field_name}为必填字段的错误提示，阻止提交",
                    priority=Priority.P0,
                    methods=[TestMethod.EQUIVALENCE],
                    remark="必填字段校验"
                )
            
            # 数据格式验证
            self.add_comprehensive_test_case(
                module="数据验证",
                submodule="格式验证",
                title=f"验证{field_name}数据格式校验",
                precondition="系统正常运行，用户在输入页面",
                test_steps=f"1. 在{field_name}字段输入错误格式数据\n2. 尝试提交表单\n3. 验证格式校验提示\n4. 输入正确格式数据确认通过",
                expected="系统正确识别格式错误并提示，正确格式数据能正常通过",
                priority=Priority.P1,
                methods=[TestMethod.EQUIVALENCE],
                remark="数据格式校验"
            )
            
            # 数据长度验证
            min_len = field.get('min_length', 1)
            max_len = field.get('max_length', 100)
            
            self.add_comprehensive_test_case(
                module="数据验证",
                submodule="长度验证",
                title=f"验证{field_name}数据长度限制",
                precondition="系统正常运行，用户在输入页面",
                test_steps=f"1. 输入少于{min_len}个字符的数据\n2. 输入超过{max_len}个字符的数据\n3. 输入正常长度数据\n4. 分别验证系统响应",
                expected=f"系统正确限制{field_name}长度在{min_len}-{max_len}字符之间",
                priority=Priority.P1,
                methods=[TestMethod.BOUNDARY_VALUE],
                remark="数据长度限制验证"
            )
            
            # 特殊字符验证
            self.add_comprehensive_test_case(
                module="数据验证",
                submodule="特殊字符",
                title=f"验证{field_name}对特殊字符的处理",
                precondition="系统正常运行，用户在输入页面",
                test_steps=f"1. 在{field_name}字段输入各种特殊字符\n2. 测试HTML标签、脚本代码\n3. 验证系统过滤和转义机制\n4. 确认数据安全性",
                expected="系统正确过滤或转义特殊字符，防止安全风险",
                priority=Priority.P1,
                methods=[TestMethod.EQUIVALENCE],
                remark="特殊字符处理验证"
            )
    
    def _generate_business_process_cases(self, analysis: RequirementAnalysis, requirement_text: str):
        """生成业务流程测试用例"""
        main_function = self._extract_main_function(requirement_text)
        context = {'main_function': main_function}

        # 完整业务流程测试
        self.add_comprehensive_test_case(
            module="业务流程",
            submodule="完整流程",
            title=f"验证{main_function}完整业务流程",
            precondition="系统正常运行，用户已登录，业务数据准备完成",
            test_steps=f"1. 从流程起点开始{main_function}操作\n2. 按照标准业务流程逐步执行\n3. 处理流程中的各个节点\n4. 完成整个业务流程\n5. 验证最终结果和状态",
            expected="完整业务流程顺利执行，各节点状态正确，最终结果符合预期",
            priority=Priority.P0,
            methods=[TestMethod.SCENARIO],
            remark="完整业务流程验证"
        )

        # 备选流程测试 - 使用步骤优化器生成详细步骤
        context['requirement_text'] = requirement_text
        base_steps = "1. 触发备选流程条件\n2. 执行备选路径\n3. 验证备选结果"
        optimized_steps = self.step_optimizer.optimize_test_steps(base_steps, context)

        self.add_comprehensive_test_case(
            module="业务流程",
            submodule="备选流程",
            title=f"验证{main_function}备选流程的正确执行",
            precondition="系统正常运行，用户已登录，存在备选路径触发条件",
            test_steps=optimized_steps,
            expected="备选流程正确执行，页面正常显示，功能完整可用，系统状态正确",
            priority=Priority.P1,
            methods=[TestMethod.SCENARIO],
            remark="备选流程场景测试"
        )
        
        # 业务规则验证
        for i, rule in enumerate(analysis.business_rules[:3]):
            self.add_comprehensive_test_case(
                module="业务流程",
                submodule="业务规则",
                title=f"验证业务规则：{rule[:20]}...",
                precondition="系统正常运行，业务规则测试环境准备",
                test_steps=f"1. 设置符合业务规则的测试条件\n2. 执行相关业务操作\n3. 验证业务规则的执行结果\n4. 测试规则边界情况",
                expected="业务规则正确执行，符合业务逻辑要求",
                priority=Priority.P1,
                methods=[TestMethod.DECISION_TABLE],
                remark=f"业务规则{i+1}验证"
            )
        
        # 流程中断恢复测试
        self.add_comprehensive_test_case(
            module="业务流程",
            submodule="流程恢复",
            title=f"验证{main_function}流程中断后的恢复能力",
            precondition="系统正常运行，业务流程执行中",
            test_steps=f"1. 开始{main_function}业务流程\n2. 在流程中间模拟中断（网络断开、页面刷新等）\n3. 重新连接或重新进入系统\n4. 验证流程状态和数据恢复",
            expected="系统能正确恢复中断的业务流程，数据不丢失",
            priority=Priority.P1,
            methods=[TestMethod.ERROR_GUESSING],
            remark="业务流程恢复验证"
        )

    def _generate_exception_handling_cases(self, analysis: RequirementAnalysis, requirement_text: str):
        """生成异常处理测试用例"""
        main_function = self._extract_main_function(requirement_text)

        # 网络异常测试
        self.add_comprehensive_test_case(
            module="异常处理",
            submodule="网络异常",
            title=f"验证{main_function}在网络异常时的处理",
            precondition="系统正常运行，准备网络异常模拟环境",
            test_steps=f"1. 开始{main_function}操作\n2. 模拟网络中断或超时\n3. 观察系统响应和错误处理\n4. 恢复网络后验证系统状态",
            expected="系统正确处理网络异常，显示友好错误提示，不丢失用户数据",
            priority=Priority.P1,
            methods=[TestMethod.ERROR_GUESSING],
            remark="网络异常处理验证"
        )

        # 服务器异常测试
        self.add_comprehensive_test_case(
            module="异常处理",
            submodule="服务器异常",
            title=f"验证{main_function}在服务器异常时的处理",
            precondition="系统运行中，准备服务器异常模拟",
            test_steps=f"1. 执行{main_function}操作\n2. 模拟服务器错误（500、503等）\n3. 验证客户端错误处理\n4. 测试重试机制和降级方案",
            expected="系统优雅处理服务器异常，提供重试选项或降级服务",
            priority=Priority.P1,
            methods=[TestMethod.ERROR_GUESSING],
            remark="服务器异常处理验证"
        )

        # 数据异常测试
        self.add_comprehensive_test_case(
            module="异常处理",
            submodule="数据异常",
            title=f"验证{main_function}对异常数据的处理",
            precondition="系统正常运行，准备异常测试数据",
            test_steps=f"1. 使用异常数据进行{main_function}操作\n2. 测试空数据、脏数据、格式错误数据\n3. 验证数据校验和过滤机制\n4. 确认系统稳定性",
            expected="系统正确识别和处理异常数据，不影响系统稳定性",
            priority=Priority.P1,
            methods=[TestMethod.ERROR_GUESSING],
            remark="异常数据处理验证"
        )

        # 并发异常测试
        self.add_comprehensive_test_case(
            module="异常处理",
            submodule="并发异常",
            title=f"验证{main_function}在高并发情况下的异常处理",
            precondition="系统正常运行，准备并发测试环境",
            test_steps=f"1. 模拟大量用户同时进行{main_function}操作\n2. 观察系统在高负载下的表现\n3. 验证资源竞争和死锁处理\n4. 测试系统降级和限流机制",
            expected="系统在高并发下保持稳定，正确处理资源竞争",
            priority=Priority.P2,
            methods=[TestMethod.ERROR_GUESSING],
            remark="并发异常处理验证"
        )

    def _generate_performance_cases(self, analysis: RequirementAnalysis, requirement_text: str):
        """生成性能测试用例"""
        main_function = self._extract_main_function(requirement_text)

        # 响应时间测试
        self.add_comprehensive_test_case(
            module="性能测试",
            submodule="响应时间",
            title=f"验证{main_function}的响应时间性能",
            precondition="系统正常运行，性能测试环境准备",
            test_steps=f"1. 记录{main_function}操作的开始时间\n2. 执行标准操作流程\n3. 记录操作完成时间\n4. 计算响应时间\n5. 重复测试多次取平均值",
            expected=f"{main_function}响应时间在可接受范围内（通常<3秒）",
            priority=Priority.P2,
            methods=[TestMethod.SCENARIO],
            remark="响应时间性能验证"
        )

        # 并发性能测试
        self.add_comprehensive_test_case(
            module="性能测试",
            submodule="并发性能",
            title=f"验证{main_function}的并发处理能力",
            precondition="系统正常运行，准备并发测试工具和环境",
            test_steps=f"1. 模拟多用户同时进行{main_function}操作\n2. 逐步增加并发用户数\n3. 监控系统响应时间和资源使用\n4. 记录系统性能指标",
            expected="系统在合理并发量下保持稳定性能，无明显性能下降",
            priority=Priority.P2,
            methods=[TestMethod.SCENARIO],
            remark="并发性能验证"
        )

        # 内存使用测试
        self.add_comprehensive_test_case(
            module="性能测试",
            submodule="内存使用",
            title=f"验证{main_function}的内存使用情况",
            precondition="系统正常运行，准备内存监控工具",
            test_steps=f"1. 监控{main_function}操作前的内存使用\n2. 执行大量{main_function}操作\n3. 监控内存使用变化\n4. 验证内存释放情况",
            expected="系统内存使用合理，无内存泄漏，能正确释放资源",
            priority=Priority.P2,
            methods=[TestMethod.SCENARIO],
            remark="内存使用性能验证"
        )

    def _generate_security_cases(self, analysis: RequirementAnalysis, requirement_text: str):
        """生成安全测试用例"""
        main_function = self._extract_main_function(requirement_text)

        # 权限验证测试
        self.add_comprehensive_test_case(
            module="安全测试",
            submodule="权限验证",
            title=f"验证{main_function}的访问权限控制",
            precondition="系统正常运行，准备不同权限级别的测试账户",
            test_steps=f"1. 使用无权限用户尝试访问{main_function}\n2. 使用有权限用户正常访问\n3. 测试权限边界情况\n4. 验证权限提升攻击防护",
            expected="系统正确控制访问权限，无权限用户无法访问受保护功能",
            priority=Priority.P1,
            methods=[TestMethod.ERROR_GUESSING],
            remark="访问权限控制验证"
        )

        # 输入安全测试
        self.add_comprehensive_test_case(
            module="安全测试",
            submodule="输入安全",
            title=f"验证{main_function}对恶意输入的防护",
            precondition="系统正常运行，准备安全测试数据",
            test_steps=f"1. 在{main_function}输入框中输入SQL注入代码\n2. 尝试XSS攻击脚本\n3. 测试命令注入和路径遍历\n4. 验证输入过滤和转义机制",
            expected="系统正确过滤和转义恶意输入，不受注入攻击影响",
            priority=Priority.P1,
            methods=[TestMethod.ERROR_GUESSING],
            remark="恶意输入防护验证"
        )

        # 会话安全测试
        self.add_comprehensive_test_case(
            module="安全测试",
            submodule="会话安全",
            title=f"验证{main_function}的会话安全机制",
            precondition="系统正常运行，用户已登录",
            test_steps=f"1. 正常使用{main_function}功能\n2. 测试会话超时机制\n3. 验证会话劫持防护\n4. 测试并发登录控制",
            expected="系统正确管理用户会话，防止会话相关安全风险",
            priority=Priority.P1,
            methods=[TestMethod.ERROR_GUESSING],
            remark="会话安全验证"
        )

    def _generate_compatibility_cases(self, analysis: RequirementAnalysis, requirement_text: str):
        """生成兼容性测试用例"""
        main_function = self._extract_main_function(requirement_text)

        # 浏览器兼容性测试
        self.add_comprehensive_test_case(
            module="兼容性测试",
            submodule="浏览器兼容",
            title=f"验证{main_function}在不同浏览器中的兼容性",
            precondition="准备多种主流浏览器测试环境",
            test_steps=f"1. 在Chrome浏览器中测试{main_function}\n2. 在Firefox浏览器中测试\n3. 在Safari浏览器中测试\n4. 在Edge浏览器中测试\n5. 对比各浏览器中的功能表现",
            expected=f"{main_function}在所有主流浏览器中都能正常工作",
            priority=Priority.P2,
            methods=[TestMethod.SCENARIO],
            remark="浏览器兼容性验证"
        )

        # 操作系统兼容性测试
        self.add_comprehensive_test_case(
            module="兼容性测试",
            submodule="操作系统兼容",
            title=f"验证{main_function}在不同操作系统中的兼容性",
            precondition="准备Windows、Mac、Linux等操作系统环境",
            test_steps=f"1. 在Windows系统中测试{main_function}\n2. 在macOS系统中测试\n3. 在Linux系统中测试\n4. 验证各系统下的功能一致性",
            expected=f"{main_function}在不同操作系统中表现一致",
            priority=Priority.P2,
            methods=[TestMethod.SCENARIO],
            remark="操作系统兼容性验证"
        )

    def _generate_usability_cases(self, analysis: RequirementAnalysis, requirement_text: str):
        """生成易用性测试用例"""
        main_function = self._extract_main_function(requirement_text)

        # 用户体验测试
        self.add_comprehensive_test_case(
            module="易用性测试",
            submodule="用户体验",
            title=f"验证{main_function}的用户体验",
            precondition="系统正常运行，准备用户体验测试场景",
            test_steps=f"1. 模拟新用户首次使用{main_function}\n2. 评估操作流程的直观性\n3. 测试帮助信息和提示的有效性\n4. 验证错误信息的友好性",
            expected=f"{main_function}操作直观易懂，新用户能快速上手",
            priority=Priority.P2,
            methods=[TestMethod.SCENARIO],
            remark="用户体验验证"
        )

        # 操作效率测试
        self.add_comprehensive_test_case(
            module="易用性测试",
            submodule="操作效率",
            title=f"验证{main_function}的操作效率",
            precondition="系统正常运行，准备效率测试场景",
            test_steps=f"1. 记录完成{main_function}操作所需的步骤数\n2. 测试快捷键和批量操作功能\n3. 验证操作流程的简化程度\n4. 评估重复操作的便利性",
            expected=f"{main_function}操作步骤简洁，支持高效操作方式",
            priority=Priority.P2,
            methods=[TestMethod.SCENARIO],
            remark="操作效率验证"
        )

    def _generate_regression_cases(self, analysis: RequirementAnalysis, historical_defects: List[str]):
        """生成回归测试用例"""
        for i, defect in enumerate(historical_defects[:5]):  # 限制前5个历史缺陷
            self.add_comprehensive_test_case(
                module="回归测试",
                submodule="历史缺陷",
                title=f"验证历史缺陷修复：{defect[:30]}...",
                precondition="系统正常运行，历史缺陷已修复",
                test_steps=f"1. 重现历史缺陷的触发条件\n2. 执行导致缺陷的操作步骤\n3. 验证缺陷是否已修复\n4. 测试相关功能是否受影响",
                expected="历史缺陷已完全修复，相关功能正常工作",
                priority=Priority.P1,
                methods=[TestMethod.ERROR_GUESSING],
                remark=f"历史缺陷{i+1}回归验证"
            )
