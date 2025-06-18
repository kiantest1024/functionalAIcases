#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI增强功能测试用例生成器
结合人工智能和所有测试设计方法，生成完善全面的功能测试用例
"""

import re
import itertools
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

# 导入基础生成器
from test_case_generator import TestCaseGenerator, TestCase, Priority, TestMethod
from comprehensive_test_generator import RequirementAnalysis

class AITestMethod(Enum):
    """AI增强测试方法"""
    INTELLIGENT_BOUNDARY = "AI智能边界分析"
    SEMANTIC_EQUIVALENCE = "语义等价类划分"
    CONTEXT_SCENARIO = "上下文场景分析"
    PREDICTIVE_ERROR = "预测性错误分析"
    ADAPTIVE_COMBINATION = "自适应组合测试"
    RISK_BASED_PRIORITY = "基于风险的优先级"
    COVERAGE_OPTIMIZATION = "覆盖度优化"
    INTELLIGENT_REGRESSION = "智能回归测试"

@dataclass
class AIAnalysisResult:
    """AI分析结果"""
    complexity_score: float  # 复杂度评分 0-1
    risk_areas: List[str]    # 风险区域
    critical_paths: List[str]  # 关键路径
    data_patterns: List[Dict]  # 数据模式
    business_rules: List[Dict]  # 业务规则
    integration_points: List[str]  # 集成点
    performance_concerns: List[str]  # 性能关注点
    security_risks: List[str]  # 安全风险
    usability_factors: List[str]  # 可用性因素

class AITestCaseGenerator(TestCaseGenerator):
    """AI增强测试用例生成器"""
    
    def __init__(self, custom_headers: Optional[Dict[str, str]] = None):
        super().__init__(custom_headers)
        self.ai_analysis: Optional[AIAnalysisResult] = None
        self.knowledge_base = self._load_knowledge_base()
        self.pattern_library = self._load_pattern_library()
        
    def _load_knowledge_base(self) -> Dict:
        """加载测试知识库"""
        return {
            "common_vulnerabilities": [
                "SQL注入", "XSS跨站脚本", "CSRF跨站请求伪造", "文件上传漏洞",
                "权限绕过", "会话劫持", "缓冲区溢出", "路径遍历"
            ],
            "performance_patterns": [
                "高并发访问", "大数据量处理", "长时间运行", "内存泄漏",
                "数据库连接池", "缓存失效", "网络延迟", "资源竞争"
            ],
            "usability_issues": [
                "响应时间过长", "界面不友好", "操作复杂", "错误提示不清",
                "无障碍访问", "移动端适配", "浏览器兼容", "国际化支持"
            ],
            "integration_risks": [
                "API版本不兼容", "数据格式不匹配", "超时处理", "错误传播",
                "事务一致性", "消息队列", "第三方服务", "数据同步"
            ],
            "business_patterns": {
                "电商": ["购物车", "支付", "库存", "订单", "用户", "商品"],
                "金融": ["账户", "交易", "风控", "合规", "清算", "报表"],
                "教育": ["课程", "学员", "考试", "成绩", "资源", "互动"],
                "医疗": ["患者", "诊断", "处方", "检查", "病历", "预约"]
            }
        }
    
    def _load_pattern_library(self) -> Dict:
        """加载测试模式库"""
        return {
            "input_patterns": {
                "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                "phone": r"^1[3-9]\d{9}$",
                "id_card": r"^\d{17}[\dXx]$",
                "password": r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$"
            },
            "boundary_patterns": {
                "string_length": [0, 1, 255, 256, 1000, 4000, 65535],
                "numeric_range": [-2147483648, -1, 0, 1, 2147483647],
                "date_range": ["1900-01-01", "2000-01-01", "2024-12-31", "2099-12-31"]
            },
            "error_patterns": [
                "空值处理", "特殊字符", "超长输入", "并发冲突",
                "网络中断", "服务不可用", "权限不足", "资源耗尽"
            ]
        }
    
    def ai_analyze_requirements(self, requirement_text: str) -> AIAnalysisResult:
        """AI智能分析需求"""
        # 复杂度评分
        complexity_score = self._calculate_complexity(requirement_text)
        
        # 识别风险区域
        risk_areas = self._identify_risk_areas(requirement_text)
        
        # 提取关键路径
        critical_paths = self._extract_critical_paths(requirement_text)
        
        # 分析数据模式
        data_patterns = self._analyze_data_patterns(requirement_text)
        
        # 提取业务规则
        business_rules = self._extract_business_rules(requirement_text)
        
        # 识别集成点
        integration_points = self._identify_integration_points(requirement_text)
        
        # 性能关注点
        performance_concerns = self._identify_performance_concerns(requirement_text)
        
        # 安全风险
        security_risks = self._identify_security_risks(requirement_text)
        
        # 可用性因素
        usability_factors = self._identify_usability_factors(requirement_text)
        
        self.ai_analysis = AIAnalysisResult(
            complexity_score=complexity_score,
            risk_areas=risk_areas,
            critical_paths=critical_paths,
            data_patterns=data_patterns,
            business_rules=business_rules,
            integration_points=integration_points,
            performance_concerns=performance_concerns,
            security_risks=security_risks,
            usability_factors=usability_factors
        )
        
        return self.ai_analysis
    
    def _calculate_complexity(self, text: str) -> float:
        """计算需求复杂度"""
        factors = {
            "length": len(text) / 10000,  # 文本长度
            "rules": len(re.findall(r'规则|条件|如果|当.*时', text)) / 10,  # 业务规则数量
            "entities": len(re.findall(r'用户|订单|商品|账户|数据', text)) / 10,  # 实体数量
            "integrations": len(re.findall(r'接口|API|第三方|集成', text)) / 5,  # 集成点
            "states": len(re.findall(r'状态|阶段|步骤', text)) / 8  # 状态数量
        }
        
        # 加权计算复杂度
        weights = {"length": 0.1, "rules": 0.3, "entities": 0.2, "integrations": 0.2, "states": 0.2}
        complexity = sum(min(factors[k], 1.0) * weights[k] for k in factors)
        
        return min(complexity, 1.0)
    
    def _identify_risk_areas(self, text: str) -> List[str]:
        """识别风险区域"""
        risks = []
        
        # 安全风险
        if re.search(r'登录|密码|认证|权限', text, re.IGNORECASE):
            risks.append("身份认证安全")
        if re.search(r'支付|金额|交易', text, re.IGNORECASE):
            risks.append("支付安全")
        if re.search(r'上传|文件|附件', text, re.IGNORECASE):
            risks.append("文件上传安全")
        
        # 性能风险
        if re.search(r'大量|批量|并发|高频', text, re.IGNORECASE):
            risks.append("高并发性能")
        if re.search(r'查询|搜索|检索', text, re.IGNORECASE):
            risks.append("查询性能")
        
        # 数据风险
        if re.search(r'数据库|存储|备份', text, re.IGNORECASE):
            risks.append("数据一致性")
        if re.search(r'同步|异步|队列', text, re.IGNORECASE):
            risks.append("数据同步")
        
        return risks
    
    def _extract_critical_paths(self, text: str) -> List[str]:
        """提取关键路径"""
        paths = []
        
        # 查找流程描述
        flow_patterns = [
            r'流程[：:]\s*([^\n]+)',
            r'步骤[：:]\s*([^\n]+)',
            r'\d+[\.、]\s*([^\n]+)'
        ]
        
        for pattern in flow_patterns:
            matches = re.findall(pattern, text)
            paths.extend(matches)
        
        # 识别关键业务路径
        if re.search(r'注册|登录', text, re.IGNORECASE):
            paths.append("用户注册登录路径")
        if re.search(r'下单|支付|购买', text, re.IGNORECASE):
            paths.append("订单支付路径")
        if re.search(r'审核|审批|流转', text, re.IGNORECASE):
            paths.append("审批流转路径")
        
        return list(set(paths))
    
    def _analyze_data_patterns(self, text: str) -> List[Dict]:
        """分析数据模式"""
        patterns = []
        
        # 识别输入模式
        for pattern_name, regex in self.pattern_library["input_patterns"].items():
            if pattern_name in text.lower():
                patterns.append({
                    "type": "input_validation",
                    "name": pattern_name,
                    "pattern": regex,
                    "risk_level": "medium"
                })
        
        # 识别数据类型
        if re.search(r'数字|金额|价格|数量', text, re.IGNORECASE):
            patterns.append({
                "type": "numeric",
                "name": "数值类型",
                "validation": "范围检查",
                "risk_level": "high"
            })
        
        if re.search(r'日期|时间', text, re.IGNORECASE):
            patterns.append({
                "type": "datetime",
                "name": "日期时间",
                "validation": "格式和范围检查",
                "risk_level": "medium"
            })
        
        return patterns
    
    def _extract_business_rules(self, text: str) -> List[Dict]:
        """提取业务规则"""
        rules = []
        
        # 条件规则
        condition_patterns = [
            r'如果(.+?)那么(.+?)(?:\n|$)',
            r'当(.+?)时(.+?)(?:\n|$)',
            r'若(.+?)则(.+?)(?:\n|$)'
        ]
        
        for pattern in condition_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for condition, action in matches:
                rules.append({
                    "type": "conditional",
                    "condition": condition.strip(),
                    "action": action.strip(),
                    "complexity": "medium"
                })
        
        # 约束规则
        constraint_patterns = [
            r'必须(.+?)(?:\n|$)',
            r'不能(.+?)(?:\n|$)',
            r'限制(.+?)(?:\n|$)'
        ]
        
        for pattern in constraint_patterns:
            matches = re.findall(pattern, text)
            for constraint in matches:
                rules.append({
                    "type": "constraint",
                    "description": constraint.strip(),
                    "complexity": "low"
                })
        
        return rules
    
    def _identify_integration_points(self, text: str) -> List[str]:
        """识别集成点"""
        integrations = []
        
        integration_keywords = [
            "API", "接口", "第三方", "外部系统", "微服务",
            "数据库", "缓存", "消息队列", "文件系统"
        ]
        
        for keyword in integration_keywords:
            if keyword in text:
                integrations.append(f"{keyword}集成")
        
        return integrations
    
    def _identify_performance_concerns(self, text: str) -> List[str]:
        """识别性能关注点"""
        concerns = []
        
        if re.search(r'响应时间|延迟|速度', text, re.IGNORECASE):
            concerns.append("响应时间性能")
        if re.search(r'并发|同时|批量', text, re.IGNORECASE):
            concerns.append("并发处理性能")
        if re.search(r'大数据|海量|TB|GB', text, re.IGNORECASE):
            concerns.append("大数据处理性能")
        if re.search(r'内存|CPU|磁盘', text, re.IGNORECASE):
            concerns.append("资源使用性能")
        
        return concerns
    
    def _identify_security_risks(self, text: str) -> List[str]:
        """识别安全风险"""
        risks = []
        
        security_keywords = {
            "注入攻击": ["输入", "查询", "SQL"],
            "跨站脚本": ["输出", "显示", "HTML"],
            "权限控制": ["权限", "角色", "访问"],
            "数据泄露": ["敏感", "隐私", "加密"],
            "会话安全": ["登录", "会话", "token"]
        }
        
        for risk_type, keywords in security_keywords.items():
            if any(keyword in text for keyword in keywords):
                risks.append(risk_type)
        
        return risks
    
    def _identify_usability_factors(self, text: str) -> List[str]:
        """识别可用性因素"""
        factors = []
        
        if re.search(r'界面|UI|用户体验', text, re.IGNORECASE):
            factors.append("界面友好性")
        if re.search(r'提示|帮助|引导', text, re.IGNORECASE):
            factors.append("操作引导")
        if re.search(r'错误|异常|失败', text, re.IGNORECASE):
            factors.append("错误处理")
        if re.search(r'移动|手机|响应式', text, re.IGNORECASE):
            factors.append("移动端适配")
        
        return factors

    def generate_ai_enhanced_test_cases(self, requirement_text: str,
                                      historical_defects: List[str] = None) -> List[TestCase]:
        """AI增强测试用例生成"""
        # 首先进行AI分析
        ai_analysis = self.ai_analyze_requirements(requirement_text)

        # 基础分析
        basic_analysis = self.analyze_requirements(requirement_text)

        # 提取业务模块信息
        business_modules = self._extract_business_modules(requirement_text)

        # 生成基础测试用例
        basic_cases = super().generate_all_test_cases(requirement_text, historical_defects)

        # AI增强测试用例
        ai_cases = []

        # 1. 智能边界分析
        ai_cases.extend(self._generate_intelligent_boundary_cases(ai_analysis, basic_analysis, business_modules))

        # 2. 语义等价类划分
        ai_cases.extend(self._generate_semantic_equivalence_cases(ai_analysis, basic_analysis, business_modules))

        # 3. 上下文场景分析
        ai_cases.extend(self._generate_context_scenario_cases(ai_analysis, basic_analysis, business_modules))

        # 4. 预测性错误分析
        ai_cases.extend(self._generate_predictive_error_cases(ai_analysis, basic_analysis, business_modules))

        # 5. 自适应组合测试
        ai_cases.extend(self._generate_adaptive_combination_cases(ai_analysis, basic_analysis, business_modules))

        # 6. 基于风险的优先级调整
        self._adjust_risk_based_priority(basic_cases + ai_cases, ai_analysis)

        # 7. 覆盖度优化
        self._optimize_coverage(basic_cases + ai_cases, ai_analysis)

        # 8. 智能回归测试
        regression_cases = self._generate_intelligent_regression_cases(ai_analysis, historical_defects, business_modules)

        # 合并所有测试用例
        all_cases = basic_cases + ai_cases + regression_cases

        # 去重和优化
        final_cases = self._deduplicate_and_optimize(all_cases)

        self.test_cases = final_cases
        return final_cases

    def _extract_business_modules(self, requirement_text: str) -> Dict[str, str]:
        """从需求文本中提取业务模块信息"""
        text_lower = requirement_text.lower()

        # 业务模块关键词映射
        module_mapping = {
            # 用户相关
            '登录': ('用户管理', '用户登录'),
            '注册': ('用户管理', '用户注册'),
            '个人信息': ('个人中心', '基本信息'),
            '个人中心': ('个人中心', '个人资料'),
            '设置': ('个人中心', '账户设置'),
            '密码': ('用户管理', '密码管理'),

            # 页面相关
            '首页': ('首页', '页面展示'),
            '导航': ('首页', '导航栏'),
            '轮播': ('首页', '轮播图'),
            '菜单': ('首页', '菜单栏'),

            # 商品相关
            '商品': ('商品管理', '商品展示'),
            '分类': ('商品管理', '分类管理'),
            '搜索': ('搜索功能', '商品搜索'),
            '筛选': ('搜索功能', '条件筛选'),
            '详情': ('商品管理', '商品详情'),

            # 购物相关
            '购物车': ('购物车管理', '购物车操作'),
            '订单': ('订单管理', '订单处理'),
            '支付': ('支付管理', '支付处理'),
            '结算': ('订单管理', '订单结算'),

            # 库存相关
            '库存': ('库存管理', '库存控制'),
            '入库': ('库存管理', '商品入库'),
            '出库': ('库存管理', '商品出库'),

            # 其他功能
            '评价': ('评价管理', '商品评价'),
            '收藏': ('收藏管理', '商品收藏'),
            '地址': ('地址管理', '收货地址'),
            '优惠券': ('营销管理', '优惠券'),
            '积分': ('积分管理', '积分操作'),
            '客服': ('客服系统', '在线客服'),
            '消息': ('消息中心', '消息通知'),
            '反馈': ('意见反馈', '用户反馈'),
            '帮助': ('帮助中心', '使用帮助'),
            '关于': ('系统信息', '关于我们')
        }

        # 查找匹配的模块
        detected_modules = {}
        for keyword, (module, submodule) in module_mapping.items():
            if keyword in text_lower:
                detected_modules[keyword] = {'module': module, 'submodule': submodule}

        # 如果没有检测到特定模块，使用默认模块
        if not detected_modules:
            detected_modules['default'] = {'module': '功能模块', 'submodule': '基础功能'}

        return detected_modules

    def _generate_intelligent_boundary_cases(self, ai_analysis: AIAnalysisResult,
                                           basic_analysis: RequirementAnalysis,
                                           business_modules: Dict[str, str]) -> List[TestCase]:
        """智能边界分析测试用例"""
        cases = []

        # 获取主要业务模块
        main_module = list(business_modules.values())[0] if business_modules else {'module': '功能模块', 'submodule': '基础功能'}

        for pattern in ai_analysis.data_patterns:
            if pattern["type"] == "numeric":
                # 基于复杂度动态调整边界值
                if ai_analysis.complexity_score > 0.7:
                    # 高复杂度：更多边界值
                    boundary_values = [-1, 0, 1, 999, 1000]
                else:
                    # 低复杂度：标准边界值
                    boundary_values = [-1, 0, 1, 100]

                for value in boundary_values[:3]:  # 限制数量
                    submodule = f"{pattern['name']}边界测试"
                    case_id = self.generate_case_id(main_module['module'], submodule)
                    priority = Priority.P0 if value in [0, -1, 1] else Priority.P1

                    test_case = TestCase(
                        module=main_module['module'],
                        submodule=submodule,
                        case_id=case_id,
                        title=f"验证{f"{pattern['name']}边界测试"}功能",
                        precondition="系统正常运行，用户已登录",
                        test_steps=f"1. 在{pattern['name']}字段输入边界值{value}\n2. 点击提交按钮\n3. 验证系统响应\n4. 检查错误提示信息",
                        expected=f"系统正确处理边界值{value}，显示相应的提示信息",
                        priority=priority,
                        remark=f"边界值分析 - {pattern['name']}字段边界测试",
                        methods_used=[TestMethod.BOUNDARY_VALUE]
                    
                    )
                    cases.append(test_case)

        return cases

    def _generate_semantic_equivalence_cases(self, ai_analysis: AIAnalysisResult,
                                           basic_analysis: RequirementAnalysis,
                                           business_modules: Dict[str, str]) -> List[TestCase]:
        """语义等价类划分测试用例"""
        cases = []

        # 获取主要业务模块
        main_module = list(business_modules.values())[0] if business_modules else {'module': '数据验证', 'submodule': '等价类测试'}

        # 基于业务规则生成等价类测试
        for rule in ai_analysis.business_rules[:2]:  # 限制数量
            if rule["type"] == "conditional":
                # 正向等价类
                submodule = "条件满足测试"
                case_id = self.generate_case_id(main_module['module'], submodule)
                test_case = TestCase(
                        module=main_module['module'],
                        submodule=submodule,
                        case_id=case_id,
                        title=f"验证{"条件满足测试"}功能",
                        precondition="系统正常运行，用户已登录",
                        test_steps=f"1. 设置条件：{rule['condition']}\n2. 执行相关操作\n3. 验证业务结果\n4. 检查系统状态",
                        expected=f"满足条件时正确执行业务逻辑",
                        priority=Priority.P0,
                        remark=f"等价类分析 - 条件满足时的业务验证",
                        methods_used=[TestMethod.EQUIVALENCE]
                
                    )
                cases.append(test_case)

                # 反向等价类
                submodule = "条件不满足测试"
                case_id = self.generate_case_id(main_module['module'], submodule)
                test_case = TestCase(
                        module=main_module['module'],
                        submodule=submodule,
                        case_id=case_id,
                        title=f"验证{"条件不满足测试"}功能",
                        precondition="系统正常运行，用户已登录",
                        test_steps=f"1. 设置条件不满足：{rule['condition']}\n2. 尝试执行操作\n3. 验证错误处理\n4. 检查提示信息",
                        expected=f"条件不满足时正确处理，显示友好提示",
                        priority=Priority.P1,
                        remark=f"等价类分析 - 条件不满足时的处理验证",
                        methods_used=[TestMethod.EQUIVALENCE]
                
                    )
                cases.append(test_case)

        return cases

    def _generate_context_scenario_cases(self, ai_analysis: AIAnalysisResult,
                                       basic_analysis: RequirementAnalysis,
                                       business_modules: Dict[str, str]) -> List[TestCase]:
        """上下文场景分析测试用例"""
        cases = []

        # 获取主要业务模块
        main_module = list(business_modules.values())[0] if business_modules else {'module': '业务流程', 'submodule': '场景测试'}

        # 基于关键路径生成上下文场景
        for path in ai_analysis.critical_paths[:2]:  # 限制数量
            # 正常场景
            case_id = self.generate_case_id(main_module['module'])
            test_case = TestCase(
                        module=main_module['module'],
                        submodule="正常流程测试",
                        case_id=case_id,
                        title=f"验证{"正常流程测试"}功能",
                        precondition="系统正常运行，用户已登录",
                        test_steps=f"1. 准备测试环境\n2. 执行业务流程：{path}\n3. 验证流程结果\n4. 检查数据完整性",
                        expected="业务流程正常执行，结果符合预期",
                        priority=Priority.P0,
                        remark=f"场景测试 - 正常业务流程验证",
                        methods_used=[TestMethod.SCENARIO]
            
                    )
            cases.append(test_case)

            # 异常场景
            case_id = self.generate_case_id(main_module['module'])
            test_case = TestCase(
                        module=main_module['module'],
                        submodule="异常流程测试",
                        case_id=case_id,
                        title=f"验证{"异常流程测试"}功能",
                        precondition="系统运行中，存在异常条件",
                        test_steps=f"1. 模拟异常环境\n2. 尝试执行：{path}\n3. 验证错误处理\n4. 检查系统恢复",
                        expected="系统正确处理异常，显示友好错误信息",
                        priority=Priority.P1,
                        remark=f"场景测试 - 异常情况处理验证",
                        methods_used=[TestMethod.SCENARIO]
            
                    )
            cases.append(test_case)

        return cases

    def _generate_predictive_error_cases(self, ai_analysis: AIAnalysisResult,
                                       basic_analysis: RequirementAnalysis,
                                       business_modules: Dict[str, str]) -> List[TestCase]:
        """预测性错误分析测试用例"""
        cases = []

        # 基于风险区域预测错误
        for risk in ai_analysis.risk_areas:
            # 安全风险测试
            if "安全" in risk:
                case_id = self.generate_case_id("AI预测错误")
                test_case = TestCase(
                        module="AI预测错误",
                        submodule="安全风险预测",
                        case_id=case_id,
                        title=f"验证{"安全风险预测"}功能",
                        precondition="系统正常运行，具备安全测试环境",
                        test_steps=f"1. 模拟{risk}相关的攻击场景\n2. 执行潜在的恶意操作\n3. 验证安全防护机制\n4. 检查日志记录",
                        expected="系统正确识别和阻止安全威胁，记录安全事件",
                        priority=Priority.P0,
                        remark=f"{AITestMethod.PREDICTIVE_ERROR.value}。基于{risk}的预测性测试",
                        methods_used=[TestMethod.ERROR_GUESSING]
                
                    )
                cases.append(test_case)

            # 性能风险测试
            elif "性能" in risk:
                case_id = self.generate_case_id("AI预测错误")
                test_case = TestCase(
                        module="AI预测错误",
                        submodule="性能风险预测",
                        case_id=case_id,
                        title=f"验证{"性能风险预测"}功能",
                        precondition="系统正常运行，性能监控已启用",
                        test_steps=f"1. 模拟{risk}相关的性能压力\n2. 监控系统响应时间\n3. 检查资源使用情况\n4. 验证性能阈值",
                        expected="系统在压力下保持稳定，性能指标在可接受范围内",
                        priority=Priority.P1,
                        remark=f"{AITestMethod.PREDICTIVE_ERROR.value}。基于{risk}的性能预测测试",
                        methods_used=[TestMethod.ERROR_GUESSING]
                
                    )
                cases.append(test_case)

        return cases

    def _generate_adaptive_combination_cases(self, ai_analysis: AIAnalysisResult,
                                           basic_analysis: RequirementAnalysis,
                                           business_modules: Dict[str, str]) -> List[TestCase]:
        """自适应组合测试用例"""
        cases = []

        # 基于复杂度自适应选择组合策略
        if ai_analysis.complexity_score > 0.8:
            # 高复杂度：使用更全面的组合
            combination_strategy = "全组合"
            combinations = list(itertools.product([True, False], repeat=min(4, len(ai_analysis.business_rules))))
        elif ai_analysis.complexity_score > 0.5:
            # 中等复杂度：使用正交组合
            combination_strategy = "正交组合"
            combinations = [(True, True, False), (True, False, True), (False, True, True), (False, False, False)]
        else:
            # 低复杂度：使用基本组合
            combination_strategy = "基本组合"
            combinations = [(True, True), (True, False), (False, True), (False, False)]

        for i, combination in enumerate(combinations[:8]):  # 限制组合数量
            case_id = self.generate_case_id("AI自适应组合")

            # 构建组合条件描述
            conditions = []
            for j, value in enumerate(combination):
                if j < len(ai_analysis.business_rules):
                    rule = ai_analysis.business_rules[j]
                    condition_desc = f"{rule.get('condition', f'条件{j+1}')}={'满足' if value else '不满足'}"
                    conditions.append(condition_desc)

            test_case = TestCase(
                        module="AI自适应组合",
                        submodule=f"{combination_strategy}测试",
                        case_id=case_id,
                        title=f"验证{f"{combination_strategy}测试"}功能",
                        precondition="系统正常运行，测试环境已准备",
                        test_steps=f"1. 设置组合条件：{'; '.join(conditions)}\n2. 执行业务操作\n3. 验证组合结果\n4. 检查系统状态一致性",
                        expected="系统正确处理条件组合，业务逻辑符合预期",
                        priority=Priority.P1,
                        remark=f"{AITestMethod.ADAPTIVE_COMBINATION.value}。{combination_strategy}，复杂度：{ai_analysis.complexity_score:.2f}",
                        methods_used=[TestMethod.ORTHOGONAL]
            
                    )
            cases.append(test_case)

        return cases

    def _adjust_risk_based_priority(self, test_cases: List[TestCase], ai_analysis: AIAnalysisResult):
        """基于风险调整优先级"""
        high_risk_keywords = ["安全", "支付", "认证", "权限", "数据"]

        for case in test_cases:
            # 检查是否涉及高风险区域
            case_text = f"{case.module} {case.submodule} {case.test_steps} {case.remark}".lower()

            # 高风险提升优先级
            if any(keyword in case_text for keyword in high_risk_keywords):
                if case.priority == Priority.P2:
                    case.priority = Priority.P1
                elif case.priority == Priority.P1:
                    case.priority = Priority.P0

            # 基于AI分析的风险区域调整
            for risk in ai_analysis.risk_areas:
                if risk.lower() in case_text:
                    case.priority = Priority.P0
                    case.remark += f"。高风险区域：{risk}"
                    break

    def _optimize_coverage(self, test_cases: List[TestCase], ai_analysis: AIAnalysisResult) -> List[TestCase]:
        """覆盖度优化"""
        # 分析覆盖度
        coverage_analysis = {
            "modules": set(),
            "methods": set(),
            "risk_areas": set(),
            "business_rules": set()
        }

        for case in test_cases:
            coverage_analysis["modules"].add(case.module)
            coverage_analysis["methods"].update(case.methods_used)

            # 检查风险区域覆盖
            case_text = f"{case.module} {case.submodule} {case.test_steps}".lower()
            for risk in ai_analysis.risk_areas:
                if risk.lower() in case_text:
                    coverage_analysis["risk_areas"].add(risk)

        # 生成补充测试用例以提高覆盖度
        missing_coverage = []

        # 检查未覆盖的风险区域
        for risk in ai_analysis.risk_areas:
            if risk not in coverage_analysis["risk_areas"]:
                missing_coverage.append(f"风险区域：{risk}")

        # 检查未覆盖的集成点
        for integration in ai_analysis.integration_points:
            integration_covered = any(integration.lower() in case.test_steps.lower() for case in test_cases)
            if not integration_covered:
                missing_coverage.append(f"集成点：{integration}")

        # 为未覆盖的区域生成补充测试用例
        supplementary_cases = []
        for missing in missing_coverage[:5]:  # 限制补充用例数量
            case_id = self.generate_case_id("AI覆盖度优化")
            test_case = TestCase(
                        module="AI覆盖度优化",
                        submodule="补充覆盖",
                        case_id=case_id,
                        title=f"验证{"补充覆盖"}功能",
                        precondition="系统正常运行，覆盖度分析已完成",
                        test_steps=f"1. 针对{missing}进行专项测试\n2. 验证功能完整性\n3. 检查边界情况\n4. 确认错误处理",
                        expected=f"完整覆盖{missing}，功能正常",
                        priority=Priority.P2,
                        remark=f"{AITestMethod.COVERAGE_OPTIMIZATION.value}。补充覆盖：{missing}",
                        methods_used=[TestMethod.ERROR_GUESSING]
            
                    )
            supplementary_cases.append(test_case)

        return test_cases + supplementary_cases

    def _generate_intelligent_regression_cases(self, ai_analysis: AIAnalysisResult,
                                             historical_defects: List[str] = None,
                                             business_modules: Dict[str, str] = None) -> List[TestCase]:
        """智能回归测试用例"""
        cases = []

        if not historical_defects:
            return cases

        # AI分析历史缺陷模式
        defect_patterns = self._analyze_defect_patterns(historical_defects)

        for defect in historical_defects:
            # 基础回归测试
            case_id = self.generate_case_id("AI智能回归")
            basic_regression = TestCase(
                        module="AI智能回归",
                        submodule="历史缺陷回归",
                        case_id=case_id,
                        title=f"验证{"历史缺陷回归"}功能",
                        precondition="系统已修复相关缺陷，测试环境已准备",
                        test_steps=f"1. 复现历史缺陷场景：{defect}\n2. 验证缺陷已修复\n3. 检查修复的完整性\n4. 验证无新的副作用",
                        expected="历史缺陷已完全修复，无回归问题",
                        priority=Priority.P0,
                        remark=f"{AITestMethod.INTELLIGENT_REGRESSION.value}。历史缺陷：{defect}",
                        methods_used=[TestMethod.ERROR_GUESSING]
            
                    )
            cases.append(basic_regression)

            # 扩展回归测试（基于AI分析）
            if defect_patterns.get("similar_scenarios"):
                case_id = self.generate_case_id("AI智能回归")
                extended_regression = TestCase(
                        module="AI智能回归",
                        submodule="扩展回归测试",
                        case_id=case_id,
                        title=f"验证{"扩展回归测试"}功能",
                        precondition="系统已修复相关缺陷，扩展测试环境已准备",
                        test_steps=f"1. 基于{defect}分析相似场景\n2. 测试相关功能模块\n3. 验证修复的影响范围\n4. 检查潜在的关联问题",
                        expected="相关功能模块正常，无潜在回归风险",
                        priority=Priority.P1,
                        remark=f"{AITestMethod.INTELLIGENT_REGRESSION.value}。扩展回归，基于缺陷模式分析",
                        methods_used=[TestMethod.ERROR_GUESSING]
                
                    )
                cases.append(extended_regression)

        return cases

    def _analyze_defect_patterns(self, historical_defects: List[str]) -> Dict:
        """分析缺陷模式"""
        patterns = {
            "security_related": [],
            "performance_related": [],
            "ui_related": [],
            "data_related": [],
            "similar_scenarios": True
        }

        for defect in historical_defects:
            defect_lower = defect.lower()
            if any(keyword in defect_lower for keyword in ["安全", "权限", "注入", "xss"]):
                patterns["security_related"].append(defect)
            elif any(keyword in defect_lower for keyword in ["性能", "慢", "超时", "内存"]):
                patterns["performance_related"].append(defect)
            elif any(keyword in defect_lower for keyword in ["界面", "显示", "ui", "页面"]):
                patterns["ui_related"].append(defect)
            elif any(keyword in defect_lower for keyword in ["数据", "库", "同步", "一致"]):
                patterns["data_related"].append(defect)

        return patterns

    def _deduplicate_and_optimize(self, test_cases: List[TestCase]) -> List[TestCase]:
        """去重和优化测试用例"""
        # 基于测试步骤的相似度去重
        unique_cases = []
        seen_signatures = set()

        for case in test_cases:
            # 创建测试用例签名
            signature = f"{case.module}_{case.submodule}_{hash(case.test_steps) % 10000}"

            if signature not in seen_signatures:
                seen_signatures.add(signature)
                unique_cases.append(case)
            else:
                # 如果重复，保留优先级更高的
                existing_case = next(c for c in unique_cases if f"{c.module}_{c.submodule}_{hash(c.test_steps) % 10000}" == signature)
                if case.priority.value < existing_case.priority.value:  # P0 < P1 < P2
                    unique_cases.remove(existing_case)
                    unique_cases.append(case)

        # 按优先级和模块排序
        unique_cases.sort(key=lambda x: (x.priority.value, x.module, x.submodule))

        return unique_cases

    def generate_ai_analysis_report(self) -> str:
        """生成AI分析报告"""
        if not self.ai_analysis:
            return "AI分析未完成"

        report = "\n## 🤖 AI智能分析报告\n\n"

        # 复杂度分析
        report += f"### 📊 需求复杂度分析\n"
        report += f"**复杂度评分**: {self.ai_analysis.complexity_score:.2f}/1.0\n"

        complexity_level = "低"
        if self.ai_analysis.complexity_score > 0.7:
            complexity_level = "高"
        elif self.ai_analysis.complexity_score > 0.4:
            complexity_level = "中"

        report += f"**复杂度等级**: {complexity_level}\n\n"

        # 风险分析
        if self.ai_analysis.risk_areas:
            report += f"### ⚠️ 风险区域识别\n"
            for i, risk in enumerate(self.ai_analysis.risk_areas, 1):
                report += f"{i}. **{risk}** - 需要重点关注\n"
            report += "\n"

        # 关键路径
        if self.ai_analysis.critical_paths:
            report += f"### 🛤️ 关键路径分析\n"
            for i, path in enumerate(self.ai_analysis.critical_paths, 1):
                report += f"{i}. {path}\n"
            report += "\n"

        # 数据模式
        if self.ai_analysis.data_patterns:
            report += f"### 📋 数据模式分析\n"
            for pattern in self.ai_analysis.data_patterns:
                report += f"- **{pattern['name']}** ({pattern['type']}) - 风险等级: {pattern.get('risk_level', 'unknown')}\n"
            report += "\n"

        # 业务规则
        if self.ai_analysis.business_rules:
            report += f"### 📜 业务规则提取\n"
            for i, rule in enumerate(self.ai_analysis.business_rules, 1):
                if rule['type'] == 'conditional':
                    report += f"{i}. **条件规则**: 如果 {rule['condition']} 那么 {rule['action']}\n"
                else:
                    report += f"{i}. **约束规则**: {rule['description']}\n"
            report += "\n"

        # 集成点
        if self.ai_analysis.integration_points:
            report += f"### 🔗 集成点识别\n"
            for i, integration in enumerate(self.ai_analysis.integration_points, 1):
                report += f"{i}. {integration}\n"
            report += "\n"

        # 性能关注点
        if self.ai_analysis.performance_concerns:
            report += f"### ⚡ 性能关注点\n"
            for i, concern in enumerate(self.ai_analysis.performance_concerns, 1):
                report += f"{i}. {concern}\n"
            report += "\n"

        # 安全风险
        if self.ai_analysis.security_risks:
            report += f"### 🔒 安全风险评估\n"
            for i, risk in enumerate(self.ai_analysis.security_risks, 1):
                report += f"{i}. {risk}\n"
            report += "\n"

        # 可用性因素
        if self.ai_analysis.usability_factors:
            report += f"### 👥 可用性因素\n"
            for i, factor in enumerate(self.ai_analysis.usability_factors, 1):
                report += f"{i}. {factor}\n"
            report += "\n"

        return report

    def generate_ai_enhanced_statistics(self) -> str:
        """生成AI增强统计报告"""
        if not self.test_cases:
            return "暂无测试用例数据"

        # 基础统计
        basic_stats = self.generate_statistics_report()

        # AI增强统计
        ai_stats = "\n## 🤖 AI增强测试统计\n\n"

        # AI方法统计
        ai_methods = {}
        for case in self.test_cases:
            if any(ai_method.value in case.remark for ai_method in AITestMethod):
                for ai_method in AITestMethod:
                    if ai_method.value in case.remark:
                        ai_methods[ai_method.value] = ai_methods.get(ai_method.value, 0) + 1

        if ai_methods:
            ai_stats += "### 🧠 AI测试方法应用\n"
            total_ai_cases = sum(ai_methods.values())
            for method, count in sorted(ai_methods.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(self.test_cases) * 100)
                ai_stats += f"- **{method}**: {count} 个用例 ({percentage:.1f}%)\n"
            ai_stats += f"\n**AI增强用例占比**: {total_ai_cases}/{len(self.test_cases)} ({total_ai_cases/len(self.test_cases)*100:.1f}%)\n\n"

        # 复杂度分布
        if self.ai_analysis:
            ai_stats += "### 📊 复杂度驱动的测试分布\n"
            complexity_score = self.ai_analysis.complexity_score

            if complexity_score > 0.7:
                ai_stats += f"- **高复杂度系统** (评分: {complexity_score:.2f})\n"
                ai_stats += "  - 采用全面的边界值测试\n"
                ai_stats += "  - 增强的组合测试覆盖\n"
                ai_stats += "  - 深度的错误场景分析\n"
            elif complexity_score > 0.4:
                ai_stats += f"- **中等复杂度系统** (评分: {complexity_score:.2f})\n"
                ai_stats += "  - 标准的测试方法组合\n"
                ai_stats += "  - 重点关注关键路径\n"
            else:
                ai_stats += f"- **低复杂度系统** (评分: {complexity_score:.2f})\n"
                ai_stats += "  - 基础测试方法覆盖\n"
                ai_stats += "  - 重点验证核心功能\n"
            ai_stats += "\n"

        # 风险覆盖分析
        if self.ai_analysis and self.ai_analysis.risk_areas:
            ai_stats += "### ⚠️ 风险覆盖分析\n"
            covered_risks = set()
            for case in self.test_cases:
                case_text = f"{case.module} {case.submodule} {case.test_steps} {case.remark}".lower()
                for risk in self.ai_analysis.risk_areas:
                    if risk.lower() in case_text:
                        covered_risks.add(risk)

            coverage_rate = len(covered_risks) / len(self.ai_analysis.risk_areas) * 100
            ai_stats += f"**风险覆盖率**: {len(covered_risks)}/{len(self.ai_analysis.risk_areas)} ({coverage_rate:.1f}%)\n\n"

            ai_stats += "**已覆盖风险**:\n"
            for risk in covered_risks:
                ai_stats += f"- ✅ {risk}\n"

            uncovered_risks = set(self.ai_analysis.risk_areas) - covered_risks
            if uncovered_risks:
                ai_stats += "\n**未覆盖风险**:\n"
                for risk in uncovered_risks:
                    ai_stats += f"- ❌ {risk}\n"
            ai_stats += "\n"

        # 智能优化建议
        ai_stats += "### 💡 AI优化建议\n"

        # 基于优先级分布的建议
        priority_stats = {}
        for case in self.test_cases:
            priority = case.priority.value
            priority_stats[priority] = priority_stats.get(priority, 0) + 1

        p0_ratio = priority_stats.get('P0', 0) / len(self.test_cases)
        if p0_ratio > 0.4:
            ai_stats += "- ⚠️ **P0用例比例较高** - 建议重新评估优先级分配\n"
        elif p0_ratio < 0.1:
            ai_stats += "- ⚠️ **P0用例比例较低** - 建议增加核心功能测试\n"
        else:
            ai_stats += "- ✅ **优先级分配合理** - P0用例比例适中\n"

        # 基于复杂度的建议
        if self.ai_analysis:
            if self.ai_analysis.complexity_score > 0.8:
                ai_stats += "- 🔍 **高复杂度系统** - 建议增加集成测试和端到端测试\n"
            if len(self.ai_analysis.security_risks) > 3:
                ai_stats += "- 🔒 **安全风险较多** - 建议进行专项安全测试\n"
            if len(self.ai_analysis.performance_concerns) > 2:
                ai_stats += "- ⚡ **性能关注点较多** - 建议进行性能压力测试\n"

        return basic_stats + ai_stats

    def export_ai_enhanced_report(self, filename: str = None) -> str:
        """导出AI增强报告"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ai_enhanced_test_report_{timestamp}.md"

        # 生成完整报告
        report_content = "# 🤖 AI增强功能测试用例报告\n\n"
        report_content += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report_content += f"**总测试用例数**: {len(self.test_cases)}\n\n"

        # AI分析报告
        report_content += self.generate_ai_analysis_report()

        # 测试用例表格
        report_content += self.export_to_markdown()

        # AI增强统计
        report_content += self.generate_ai_enhanced_statistics()

        # 保存文件
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report_content)

        return filename
