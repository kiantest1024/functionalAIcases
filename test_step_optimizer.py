#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试步骤优化器
生成详细、具体的测试步骤描述
"""

import re
from typing import Dict, List

class TestStepOptimizer:
    """测试步骤优化器"""
    
    def __init__(self):
        # 功能类型映射
        self.function_patterns = {
            '登录': ['登录', '用户认证', '身份验证'],
            '注册': ['注册', '用户注册', '账户创建'],
            '个人信息': ['个人信息', '用户信息', '个人资料', '用户资料'],
            '购物车': ['购物车', '购物', '商品购买'],
            '支付': ['支付', '付款', '结算'],
            '搜索': ['搜索', '查找', '检索'],
            '商品管理': ['商品', '产品', '商品管理'],
            '订单': ['订单', '订单管理'],
            '评价': ['评价', '评论', '反馈'],
            '收藏': ['收藏', '收藏夹', '心愿单']
        }
        
        # 备选流程模板
        self.alternative_flow_templates = {
            '登录': {
                'triggers': [
                    '直接通过URL访问需要登录的页面（跳过登录页面）',
                    '使用第三方登录方式（微信、QQ、支付宝等）',
                    '通过记住密码功能自动登录',
                    '使用手机验证码登录'
                ],
                'paths': [
                    '点击第三方登录按钮，选择微信登录',
                    '输入手机号，点击获取验证码，输入验证码登录',
                    '使用浏览器保存的密码自动填充登录',
                    '通过扫码登录功能进入系统'
                ]
            },
            '个人信息': {
                'triggers': [
                    '直接从网址进入个人信息页面（跳过主页导航）',
                    '通过用户头像下拉菜单快速访问',
                    '从消息通知中点击链接进入',
                    '通过搜索功能找到个人信息入口'
                ],
                'paths': [
                    '点击页面右上角用户头像，选择"个人信息"',
                    '使用快捷键Ctrl+P打开个人信息页面',
                    '从侧边栏菜单中选择"个人中心"',
                    '点击导航栏中的"我的账户"链接'
                ]
            },
            '购物车': {
                'triggers': [
                    '直接从商品详情页进入购买流程（跳过购物车页面）',
                    '通过搜索结果直接添加到购物车',
                    '使用"立即购买"功能跳过购物车',
                    '从收藏夹批量添加到购物车'
                ],
                'paths': [
                    '点击商品页面的"立即购买"按钮',
                    '使用"一键下单"功能直接结算',
                    '从购物车图标的下拉菜单快速操作',
                    '批量选择收藏商品添加到购物车'
                ]
            },
            '支付': {
                'triggers': [
                    '使用快捷支付方式（跳过常规支付流程）',
                    '从购物车直接结算',
                    '使用移动端扫码支付',
                    '通过第三方支付平台跳转'
                ],
                'paths': [
                    '选择支付宝快捷支付',
                    '使用微信扫码支付',
                    '选择银行卡快捷支付',
                    '使用数字钱包支付'
                ]
            },
            '搜索': {
                'triggers': [
                    '通过语音搜索功能进行查询',
                    '使用搜索建议和自动补全',
                    '通过扫码搜索商品',
                    '使用高级搜索筛选功能'
                ],
                'paths': [
                    '点击搜索框右侧的语音图标进行语音搜索',
                    '使用搜索历史记录快速搜索',
                    '点击搜索建议中的关键词',
                    '使用条件筛选器精确搜索'
                ]
            }
        }
    
    def optimize_test_steps(self, base_steps: str, context: Dict) -> str:
        """优化测试步骤，使其更加详细和具体"""
        main_function = context.get('main_function', '功能')
        requirement_text = context.get('requirement_text', '')
        
        # 识别功能类型
        function_type = self._identify_function_type(main_function, requirement_text)
        
        # 解析基础步骤
        steps = base_steps.split('\n')
        optimized_steps = []
        
        for i, step in enumerate(steps, 1):
            # 移除原有的编号
            step_content = re.sub(r'^\d+\.\s*', '', step.strip())
            
            # 根据步骤内容进行优化
            if "触发备选流程" in step_content:
                optimized_step = self._optimize_alternative_trigger_step(step_content, function_type)
            elif "执行备选路径" in step_content or "备选路径" in step_content:
                optimized_step = self._optimize_alternative_path_step(step_content, function_type)
            elif "验证" in step_content and ("结果" in step_content or "响应" in step_content):
                optimized_step = self._optimize_verification_step(step_content, function_type)
            elif "检查" in step_content:
                optimized_step = self._optimize_check_step(step_content, function_type)
            else:
                optimized_step = self._optimize_general_step(step_content, function_type, context)
            
            optimized_steps.append(f"{i}. {optimized_step}")
        
        return '\n'.join(optimized_steps)
    
    def _identify_function_type(self, main_function: str, requirement_text: str) -> str:
        """识别功能类型"""
        text_to_check = f"{main_function} {requirement_text}".lower()
        
        for func_type, patterns in self.function_patterns.items():
            for pattern in patterns:
                if pattern in text_to_check:
                    return func_type
        
        return '通用功能'
    
    def _optimize_alternative_trigger_step(self, step: str, function_type: str) -> str:
        """优化备选流程触发步骤"""
        if function_type in self.alternative_flow_templates:
            triggers = self.alternative_flow_templates[function_type]['triggers']
            # 选择第一个触发方式作为具体示例
            specific_trigger = triggers[0] if triggers else "通过非常规路径访问功能"
            return f"触发备选流程：{specific_trigger}"
        else:
            return f"触发备选流程：通过非常规路径进入{function_type}（如直接URL访问、快捷入口等）"
    
    def _optimize_alternative_path_step(self, step: str, function_type: str) -> str:
        """优化备选路径执行步骤"""
        if function_type in self.alternative_flow_templates:
            paths = self.alternative_flow_templates[function_type]['paths']
            # 选择第一个路径作为具体示例
            specific_path = paths[0] if paths else f"使用{function_type}的快捷操作方式"
            return f"执行备选路径：{specific_path}"
        else:
            return f"执行备选路径：使用{function_type}的快捷操作方式或辅助入口"
    
    def _optimize_verification_step(self, step: str, function_type: str) -> str:
        """优化验证步骤"""
        if "备选" in step:
            return "验证备选流程执行结果：检查页面是否正确加载，功能是否完整可用，数据是否正确显示，用户状态是否正常，与主流程结果保持一致"
        elif "响应" in step:
            return "检查系统响应结果：验证响应时间是否合理（<3秒），返回数据是否正确完整，错误处理是否得当，用户体验是否良好"
        else:
            return f"验证{function_type}操作结果：确认功能执行成功，数据保存正确，界面状态更新，无异常错误"
    
    def _optimize_check_step(self, step: str, function_type: str) -> str:
        """优化检查步骤"""
        if "响应" in step:
            return "检查系统响应：验证HTTP状态码为200，响应时间在可接受范围内，返回数据格式正确，无JavaScript错误"
        else:
            return f"检查{function_type}状态：确认页面元素正确显示，数据加载完成，交互功能正常，无异常提示"
    
    def _optimize_general_step(self, step: str, function_type: str, context: Dict) -> str:
        """优化一般步骤"""
        # 如果步骤过于简单，添加更多细节
        if len(step) < 20:
            if "进入" in step or "打开" in step:
                return f"进入{function_type}页面：通过主导航菜单或直接URL访问，确认页面完全加载"
            elif "操作" in step:
                return f"执行{function_type}操作：按照标准流程进行操作，注意每步的反馈信息"
            elif "完成" in step:
                return f"完成{function_type}流程：确认所有必要步骤已执行，检查最终状态"
        
        return step
    
    def generate_detailed_business_steps(self, function_type: str, scenario: str = "normal") -> str:
        """生成详细的业务流程步骤"""
        if scenario == "alternative" and function_type in self.alternative_flow_templates:
            template = self.alternative_flow_templates[function_type]
            trigger = template['triggers'][0]
            path = template['paths'][0]
            
            return f"""1. 触发备选流程：{trigger}
2. 执行备选路径：{path}
3. 验证页面正确加载：检查所有必要元素是否显示，功能是否可用
4. 检查数据完整性：确认用户状态、权限、数据都正确传递
5. 验证功能一致性：确保备选流程的结果与主流程一致"""
        
        return self._generate_standard_steps(function_type)
    
    def _generate_standard_steps(self, function_type: str) -> str:
        """生成标准流程步骤"""
        return f"""1. 进入{function_type}页面：通过主导航或直接访问
2. 验证页面加载：检查所有元素正确显示
3. 执行{function_type}操作：按照标准流程操作
4. 验证操作结果：确认功能执行成功
5. 检查最终状态：确保数据正确保存"""
