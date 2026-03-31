#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试步骤优化器
提供测试步骤的智能优化功能
"""

from typing import Dict, List, Optional
import re


class TestStepOptimizer:
    """测试步骤优化器"""
    
    def __init__(self):
        """初始化测试步骤优化器"""
        self.step_templates = {
            '登录': [
                '1. 打开系统登录页面',
                '2. 输入用户名',
                '3. 输入密码',
                '4. 点击登录按钮'
            ],
            '搜索': [
                '1. 定位到搜索框',
                '2. 输入搜索关键词',
                '3. 点击搜索按钮',
                '4. 等待搜索结果加载'
            ],
            '提交': [
                '1. 填写必填字段',
                '2. 检查输入内容',
                '3. 点击提交按钮',
                '4. 等待提交结果'
            ],
            '验证': [
                '1. 检查页面元素显示',
                '2. 验证数据正确性',
                '3. 确认操作结果'
            ]
        }
        
        # 常见操作的详细化
        self.action_expansions = {
            '打开': '在浏览器地址栏输入URL并访问',
            '输入': '定位到输入框，清空原有内容，输入',
            '点击': '定位到按钮/链接，点击',
            '选择': '定位到下拉框/选项，选择',
            '上传': '定位到文件上传控件，选择本地文件并上传',
            '删除': '定位到目标项，点击删除按钮，确认删除操作',
            '编辑': '定位到目标项，点击编辑按钮，修改内容',
            '提交': '填写完所有必填字段后，点击提交按钮',
            '保存': '修改完成后，点击保存按钮',
            '取消': '点击取消按钮，放弃当前操作',
            '关闭': '点击关闭按钮或窗口右上角X',
            '刷新': '点击浏览器刷新按钮或按F5键',
            '返回': '点击返回按钮或浏览器后退按钮'
        }
    
    def optimize_test_steps(self, steps: str, context: Dict = None) -> str:
        """
        优化测试步骤
        
        Args:
            steps: 原始测试步骤
            context: 上下文信息（可选）
            
        Returns:
            str: 优化后的测试步骤
        """
        if not steps or not steps.strip():
            return steps
        
        # 确保步骤是列表格式
        step_list = self._parse_steps(steps)
        
        # 优化每个步骤
        optimized_steps = []
        for i, step in enumerate(step_list, 1):
            optimized_step = self._optimize_single_step(step, i)
            optimized_steps.append(optimized_step)
        
        # 添加验证步骤（如果没有）
        if not any('验证' in step or '检查' in step or '确认' in step for step in optimized_steps):
            optimized_steps.append(f"{len(optimized_steps) + 1}. 验证操作结果符合预期")
        
        return '\n'.join(optimized_steps)
    
    def _parse_steps(self, steps: str) -> List[str]:
        """
        解析步骤文本为列表
        
        Args:
            steps: 步骤文本
            
        Returns:
            List[str]: 步骤列表
        """
        # 移除步骤编号
        lines = steps.strip().split('\n')
        parsed_steps = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 移除常见的步骤编号格式
            line = re.sub(r'^\d+[\.\)、]\s*', '', line)
            line = re.sub(r'^[一二三四五六七八九十]+[\.\)、]\s*', '', line)
            line = re.sub(r'^[⑴⑵⑶⑷⑸⑹⑺⑻⑼⑽]\s*', '', line)
            
            if line:
                parsed_steps.append(line)
        
        return parsed_steps
    
    def _optimize_single_step(self, step: str, step_number: int) -> str:
        """
        优化单个测试步骤
        
        Args:
            step: 单个步骤文本
            step_number: 步骤编号
            
        Returns:
            str: 优化后的步骤
        """
        # 确保步骤有编号
        if not step.startswith(f"{step_number}."):
            step = f"{step_number}. {step}"
        
        # 扩展简单动作为详细步骤
        for action, expansion in self.action_expansions.items():
            if step.find(action) > 0 and len(step) < 20:
                # 如果步骤很短且包含动作词，进行扩展
                step = step.replace(action, expansion)
                break
        
        return step
    
    def add_verification_steps(self, steps: str) -> str:
        """
        为测试步骤添加验证点
        
        Args:
            steps: 原始测试步骤
            
        Returns:
            str: 添加验证点后的步骤
        """
        step_list = self._parse_steps(steps)
        enhanced_steps = []
        
        for i, step in enumerate(step_list, 1):
            enhanced_steps.append(f"{i}. {step}")
            
            # 在关键操作后添加验证
            if any(keyword in step for keyword in ['提交', '保存', '删除', '登录', '支付']):
                enhanced_steps.append(f"{i + 0.5}. 验证：确认{step}操作成功")
        
        # 重新编号
        final_steps = []
        for i, step in enumerate(enhanced_steps, 1):
            if isinstance(i, float):
                continue
            step_text = step.split('. ', 1)[1] if '. ' in step else step
            final_steps.append(f"{i}. {step_text}")
        
        return '\n'.join(final_steps)
    
    def optimize_for_automation(self, steps: str) -> str:
        """
        优化测试步骤以适应自动化测试
        
        Args:
            steps: 原始测试步骤
            
        Returns:
            str: 适合自动化的步骤描述
        """
        step_list = self._parse_steps(steps)
        automation_steps = []
        
        for i, step in enumerate(step_list, 1):
            # 添加定位器提示
            if '输入' in step:
                step = f"{i}. [定位输入框] {step}"
            elif '点击' in step:
                step = f"{i}. [定位按钮] {step}"
            elif '选择' in step:
                step = f"{i}. [定位选择器] {step}"
            elif '验证' in step or '检查' in step:
                step = f"{i}. [断言] {step}"
            else:
                step = f"{i}. {step}"
            
            automation_steps.append(step)
        
        return '\n'.join(automation_steps)
    
    def suggest_test_data(self, steps: str) -> Dict[str, List[str]]:
        """
        根据测试步骤建议测试数据
        
        Args:
            steps: 测试步骤
            
        Returns:
            Dict[str, List[str]]: 测试数据建议
        """
        suggestions = {
            '正常数据': [],
            '边界数据': [],
            '异常数据': []
        }
        
        # 分析步骤中的输入类型
        if '用户名' in steps or '账号' in steps:
            suggestions['正常数据'].append('有效的用户名（6-20字符）')
            suggestions['边界数据'].extend(['5字符用户名', '21字符用户名'])
            suggestions['异常数据'].extend(['空用户名', '特殊字符用户名', 'SQL注入字符'])
        
        if '密码' in steps:
            suggestions['正常数据'].append('符合规则的密码（8-16字符，含数字和字母）')
            suggestions['边界数据'].extend(['7字符密码', '17字符密码'])
            suggestions['异常数据'].extend(['空密码', '纯数字密码', '纯字母密码'])
        
        if '邮箱' in steps or 'email' in steps.lower():
            suggestions['正常数据'].append('有效的邮箱地址')
            suggestions['异常数据'].extend(['无@符号', '无域名', '格式错误'])
        
        if '手机' in steps or '电话' in steps:
            suggestions['正常数据'].append('11位有效手机号')
            suggestions['边界数据'].extend(['10位号码', '12位号码'])
            suggestions['异常数据'].extend(['非数字字符', '空号码'])
        
        if '金额' in steps or '价格' in steps:
            suggestions['正常数据'].append('正常金额（0-999999）')
            suggestions['边界数据'].extend(['0元', '最大金额'])
            suggestions['异常数据'].extend(['负数', '超大金额', '非数字'])
        
        return suggestions
    
    def extract_preconditions(self, steps: str) -> str:
        """
        从测试步骤中提取前置条件
        
        Args:
            steps: 测试步骤
            
        Returns:
            str: 前置条件描述
        """
        preconditions = []
        
        step_list = self._parse_steps(steps)
        first_step = step_list[0] if step_list else ""
        
        # 根据第一步推断前置条件
        if '登录' in first_step:
            preconditions.append('系统处于未登录状态')
            preconditions.append('已有有效的测试账号')
        elif '打开' in first_step and '页面' in first_step:
            preconditions.append('浏览器已打开')
            preconditions.append('网络连接正常')
        
        # 检查是否需要数据准备
        if any(keyword in steps for keyword in ['编辑', '删除', '查看详情']):
            preconditions.append('系统中已存在测试数据')
        
        if '管理员' in steps or '权限' in steps:
            preconditions.append('使用具有相应权限的账号登录')
        
        return '；'.join(preconditions) if preconditions else '无特殊前置条件'
