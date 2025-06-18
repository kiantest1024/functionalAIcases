#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真正的AI增强功能测试用例生成器
集成真实的AI大模型API，支持多种AI服务
"""

import os
import json
import requests
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import openai
from ai_test_generator import AITestCaseGenerator, AIAnalysisResult, TestCase, Priority, TestMethod

class AIProvider(Enum):
    """AI服务提供商"""
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    ANTHROPIC = "anthropic"
    GOOGLE_GEMINI = "google_gemini"
    BAIDU_ERNIE = "baidu_ernie"
    ALIBABA_QWEN = "alibaba_qwen"
    ZHIPU_GLM = "zhipu_glm"
    MOONSHOT = "moonshot"

@dataclass
class AIConfig:
    """AI配置"""
    provider: AIProvider
    api_key: str
    base_url: Optional[str] = None
    model: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout: int = 30

class RealAITestCaseGenerator(AITestCaseGenerator):
    """真正的AI增强测试用例生成器"""
    
    def __init__(self, ai_config: AIConfig, custom_headers: Optional[Dict[str, str]] = None):
        super().__init__(custom_headers)
        self.ai_config = ai_config
        self.setup_ai_client()
        
    def setup_ai_client(self):
        """设置AI客户端"""
        if self.ai_config.provider == AIProvider.OPENAI:
            openai.api_key = self.ai_config.api_key
            if self.ai_config.base_url:
                openai.api_base = self.ai_config.base_url
            self.model = self.ai_config.model or "gpt-3.5-turbo"
            
        elif self.ai_config.provider == AIProvider.AZURE_OPENAI:
            openai.api_type = "azure"
            openai.api_key = self.ai_config.api_key
            openai.api_base = self.ai_config.base_url
            openai.api_version = "2023-05-15"
            self.model = self.ai_config.model or "gpt-35-turbo"
            
        else:
            # 其他AI服务使用HTTP请求
            self.model = self.ai_config.model or "default"
    
    def call_ai_api(self, prompt: str, system_prompt: str = None) -> str:
        """调用AI API"""
        try:
            if self.ai_config.provider in [AIProvider.OPENAI, AIProvider.AZURE_OPENAI]:
                return self._call_openai_api(prompt, system_prompt)
            elif self.ai_config.provider == AIProvider.ANTHROPIC:
                return self._call_anthropic_api(prompt, system_prompt)
            elif self.ai_config.provider == AIProvider.GOOGLE_GEMINI:
                return self._call_gemini_api(prompt, system_prompt)
            elif self.ai_config.provider == AIProvider.BAIDU_ERNIE:
                return self._call_ernie_api(prompt, system_prompt)
            elif self.ai_config.provider == AIProvider.ALIBABA_QWEN:
                return self._call_qwen_api(prompt, system_prompt)
            elif self.ai_config.provider == AIProvider.ZHIPU_GLM:
                return self._call_glm_api(prompt, system_prompt)
            elif self.ai_config.provider == AIProvider.MOONSHOT:
                return self._call_moonshot_api(prompt, system_prompt)
            else:
                raise ValueError(f"不支持的AI提供商: {self.ai_config.provider}")
                
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                error_msg = f"AI API认证失败 (401): API密钥无效或已过期"
                print(f"❌ {error_msg}")
                raise Exception(error_msg)
            elif e.response.status_code == 403:
                error_msg = f"AI API权限不足 (403): 没有访问权限"
                print(f"❌ {error_msg}")
                raise Exception(error_msg)
            elif e.response.status_code == 429:
                error_msg = f"AI API请求过于频繁 (429): 请稍后重试"
                print(f"❌ {error_msg}")
                raise Exception(error_msg)
            else:
                error_msg = f"AI API HTTP错误 ({e.response.status_code}): {e}"
                print(f"❌ {error_msg}")
                raise Exception(error_msg)
        except requests.exceptions.Timeout:
            error_msg = "AI API请求超时，请检查网络连接"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
        except requests.exceptions.ConnectionError:
            error_msg = "AI API连接失败，请检查网络连接和API地址"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"AI API调用失败: {str(e)}"
            print(f"❌ {error_msg}")
            # 降级到模拟AI分析
            return self._fallback_analysis(prompt)
    
    def _call_openai_api(self, prompt: str, system_prompt: str = None) -> str:
        """调用OpenAI API"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            # 尝试使用新版本OpenAI API (>=1.0.0)
            from openai import OpenAI
            client = OpenAI(
                api_key=self.ai_config.api_key,
                base_url=self.ai_config.base_url
            )

            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=min(self.ai_config.max_tokens, 2000),  # 限制token数量
                temperature=self.ai_config.temperature,
                timeout=60  # 增加超时时间到60秒
            )
            return response.choices[0].message.content

        except ImportError:
            # 降级到旧版本OpenAI API (<1.0.0)
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                max_tokens=self.ai_config.max_tokens,
                temperature=self.ai_config.temperature,
                timeout=self.ai_config.timeout
            )
            return response.choices[0].message.content
    
    def _call_anthropic_api(self, prompt: str, system_prompt: str = None) -> str:
        """调用Anthropic Claude API"""
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.ai_config.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        data = {
            "model": self.model or "claude-3-sonnet-20240229",
            "max_tokens": self.ai_config.max_tokens,
            "temperature": self.ai_config.temperature,
            "messages": [{"role": "user", "content": full_prompt}]
        }
        
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data,
            timeout=self.ai_config.timeout
        )
        response.raise_for_status()
        return response.json()["content"][0]["text"]
    
    def _call_gemini_api(self, prompt: str, system_prompt: str = None) -> str:
        """调用Google Gemini API"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model or 'gemini-pro'}:generateContent"
        
        headers = {
            "Content-Type": "application/json",
        }
        
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        
        data = {
            "contents": [{
                "parts": [{"text": full_prompt}]
            }],
            "generationConfig": {
                "temperature": self.ai_config.temperature,
                "maxOutputTokens": self.ai_config.max_tokens
            }
        }
        
        response = requests.post(
            f"{url}?key={self.ai_config.api_key}",
            headers=headers,
            json=data,
            timeout=self.ai_config.timeout
        )
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"]
    
    def _call_ernie_api(self, prompt: str, system_prompt: str = None) -> str:
        """调用百度文心一言API"""
        # 首先获取access_token
        token_url = "https://aip.baidubce.com/oauth/2.0/token"
        token_params = {
            "grant_type": "client_credentials",
            "client_id": self.ai_config.api_key,
            "client_secret": self.ai_config.base_url  # 这里用base_url存储secret
        }
        
        token_response = requests.post(token_url, params=token_params)
        access_token = token_response.json()["access_token"]
        
        # 调用ERNIE API
        url = f"https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/{self.model or 'completions_pro'}"
        
        headers = {"Content-Type": "application/json"}
        
        messages = []
        if system_prompt:
            messages.append({"role": "user", "content": system_prompt})
            messages.append({"role": "assistant", "content": "好的，我明白了。"})
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "messages": messages,
            "temperature": self.ai_config.temperature,
            "max_output_tokens": self.ai_config.max_tokens
        }
        
        response = requests.post(
            f"{url}?access_token={access_token}",
            headers=headers,
            json=data,
            timeout=self.ai_config.timeout
        )
        response.raise_for_status()
        return response.json()["result"]
    
    def _call_qwen_api(self, prompt: str, system_prompt: str = None) -> str:
        """调用阿里云通义千问API"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.ai_config.api_key}"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "model": self.model or "qwen-turbo",
            "messages": messages,
            "temperature": self.ai_config.temperature,
            "max_tokens": self.ai_config.max_tokens
        }
        
        response = requests.post(
            self.ai_config.base_url or "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
            headers=headers,
            json=data,
            timeout=self.ai_config.timeout
        )
        response.raise_for_status()
        return response.json()["output"]["choices"][0]["message"]["content"]
    
    def _call_glm_api(self, prompt: str, system_prompt: str = None) -> str:
        """调用智谱GLM API"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.ai_config.api_key}"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "model": self.model or "glm-4",
            "messages": messages,
            "temperature": self.ai_config.temperature,
            "max_tokens": self.ai_config.max_tokens
        }
        
        response = requests.post(
            self.ai_config.base_url or "https://open.bigmodel.cn/api/paas/v4/chat/completions",
            headers=headers,
            json=data,
            timeout=self.ai_config.timeout
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    
    def _call_moonshot_api(self, prompt: str, system_prompt: str = None) -> str:
        """调用月之暗面Moonshot API"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.ai_config.api_key}"
        }
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "model": self.model or "moonshot-v1-8k",
            "messages": messages,
            "temperature": self.ai_config.temperature,
            "max_tokens": self.ai_config.max_tokens
        }
        
        response = requests.post(
            self.ai_config.base_url or "https://api.moonshot.cn/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=self.ai_config.timeout
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    
    def _fallback_analysis(self, prompt: str) -> str:
        """降级分析（当AI API失败时）"""
        return "AI API调用失败，使用本地分析算法生成结果。"
    
    def real_ai_analyze_requirements(self, requirement_text: str) -> AIAnalysisResult:
        """真正的AI需求分析"""
        system_prompt = """
        你是一个资深的软件测试架构师和AI专家。请分析给定的需求文档，并按照以下JSON格式返回分析结果：

        {
            "complexity_score": 0.75,
            "risk_areas": ["安全风险", "性能风险"],
            "critical_paths": ["用户登录路径", "支付流程"],
            "data_patterns": [
                {"type": "input_validation", "name": "用户名", "risk_level": "medium"}
            ],
            "business_rules": [
                {"type": "conditional", "condition": "用户名正确", "action": "允许登录"}
            ],
            "integration_points": ["支付接口", "用户系统"],
            "performance_concerns": ["高并发", "响应时间"],
            "security_risks": ["SQL注入", "XSS攻击"],
            "usability_factors": ["界面友好性", "错误提示"]
        }

        请仔细分析需求文档的复杂度（0-1评分）、识别风险区域、提取关键路径和业务规则。
        """
        
        analysis_prompt = f"""
        请分析以下需求文档：

        {requirement_text}

        请从以下维度进行分析：
        1. 复杂度评分（0-1，考虑业务规则数量、集成点、状态转换等）
        2. 风险区域识别（安全、性能、数据、集成、可用性风险）
        3. 关键业务路径提取
        4. 数据模式和验证规则
        5. 业务规则和约束条件
        6. 系统集成点
        7. 性能关注点
        8. 安全风险评估
        9. 可用性因素

        请返回JSON格式的分析结果。
        """
        
        try:
            ai_response = self.call_ai_api(analysis_prompt, system_prompt)
            
            # 尝试解析AI返回的JSON
            try:
                # 提取JSON部分
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_str = ai_response[json_start:json_end]
                    analysis_data = json.loads(json_str)
                    
                    # 创建AIAnalysisResult对象
                    return AIAnalysisResult(
                        complexity_score=analysis_data.get('complexity_score', 0.5),
                        risk_areas=analysis_data.get('risk_areas', []),
                        critical_paths=analysis_data.get('critical_paths', []),
                        data_patterns=analysis_data.get('data_patterns', []),
                        business_rules=analysis_data.get('business_rules', []),
                        integration_points=analysis_data.get('integration_points', []),
                        performance_concerns=analysis_data.get('performance_concerns', []),
                        security_risks=analysis_data.get('security_risks', []),
                        usability_factors=analysis_data.get('usability_factors', [])
                    )
                else:
                    raise ValueError("无法找到有效的JSON格式")
                    
            except (json.JSONDecodeError, ValueError) as e:
                print(f"AI返回结果解析失败: {e}")
                print(f"AI原始返回: {ai_response}")
                # 降级到本地分析
                return super().ai_analyze_requirements(requirement_text)
                
        except Exception as e:
            print(f"AI分析失败: {e}")
            # 降级到本地分析
            return super().ai_analyze_requirements(requirement_text)
    
    def real_ai_generate_test_cases(self, requirement_text: str, ai_analysis: AIAnalysisResult, 
                                   historical_defects: List[str] = None) -> List[TestCase]:
        """真正的AI测试用例生成"""
        system_prompt = """
        你是一个资深的软件测试专家。请根据需求分析结果生成详细的测试用例。

        重要说明 - 模块层级结构：
        - module（模块）：指系统的大功能模块，如"首页"、"个人信息"、"订单管理"、"商品管理"等
        - submodule（子模块）：指大模块下的具体功能，如"首页"下的"导航栏"、"轮播图"；"个人信息"下的"基本信息"、"账户设置"等

        请严格按照以下JSON格式返回测试用例数组：

        [
          {
            "module": "首页",
            "submodule": "导航栏",
            "case_id": "TC_001",
            "precondition": "用户已打开网站首页",
            "test_steps": "1. 查看页面顶部导航栏\n2. 点击'商品分类'菜单\n3. 验证下拉菜单显示",
            "expected": "导航栏正常显示，下拉菜单包含所有商品分类",
            "priority": "P1",
            "remark": "导航功能测试"
          }
        ]

        要求：
        1. 根据需求内容识别正确的业务模块层级
        2. module必须是系统的主要功能模块
        3. submodule必须是该模块下的具体子功能
        4. 生成3-6个高质量测试用例
        5. 测试步骤要具体可执行
        6. 只返回JSON数组，不要其他内容
        """
        
        # 构建简化的生成提示
        generation_prompt = f"""
        请为以下需求生成测试用例：

        {requirement_text}

        重点关注：
        - 正常功能流程测试
        - 异常情况处理
        - 边界值和输入验证
        - 业务规则验证

        请返回JSON格式的测试用例数组。
        """
        
        try:
            ai_response = self.call_ai_api(generation_prompt, system_prompt)
            print(f"✅ AI生成响应成功，长度: {len(ai_response)}")

            # 解析AI生成的测试用例
            try:
                # 先尝试直接解析整个响应
                try:
                    test_cases_data = json.loads(ai_response)
                    print("✅ 直接JSON解析成功")
                except json.JSONDecodeError:
                    # 提取JSON部分
                    print("🔍 尝试提取JSON部分...")
                    json_start = ai_response.find('[')
                    json_end = ai_response.rfind(']') + 1
                    if json_start == -1:
                        json_start = ai_response.find('{')
                        json_end = ai_response.rfind('}') + 1

                    if json_start != -1 and json_end != -1:
                        json_str = ai_response[json_start:json_end]
                        print(f"🔍 提取的JSON长度: {len(json_str)}")
                        test_cases_data = json.loads(json_str)
                        print("✅ 提取JSON解析成功")
                    else:
                        raise ValueError("无法找到有效的JSON格式")

                # 如果是单个对象，转换为数组
                if isinstance(test_cases_data, dict):
                    if 'test_cases' in test_cases_data:
                        test_cases_data = test_cases_data['test_cases']
                    else:
                        test_cases_data = [test_cases_data]

                print(f"🔍 解析到 {len(test_cases_data)} 个测试用例数据")

                # 转换为TestCase对象
                test_cases = []
                for i, case_data in enumerate(test_cases_data):
                    try:
                        priority_str = case_data.get('priority', 'P1')
                        if priority_str == 'P0':
                            priority = Priority.P0
                        elif priority_str == 'P2':
                            priority = Priority.P2
                        else:
                            priority = Priority.P1

                        test_case = TestCase(
                            module=case_data.get('module', 'AI生成模块'),
                            submodule=case_data.get('submodule', 'AI生成子模块'),
                            case_id=case_data.get('case_id', f'AI_TC_{i+1:03d}'),
                            title=case_data.get('title', f'AI生成测试用例{i+1}'),
                            precondition=case_data.get('precondition', '系统正常运行'),
                            test_steps=case_data.get('test_steps', '待补充测试步骤'),
                            expected=case_data.get('expected', '待补充预期结果'),
                            priority=priority,
                            remark=f"AI生成 - {case_data.get('remark', '使用真实AI大模型生成')}",
                            methods_used=[TestMethod.AI_ENHANCED]
                        )
                        test_cases.append(test_case)
                        print(f"✅ 成功解析测试用例 {i+1}: {test_case.case_id}")
                    except Exception as e:
                        print(f"❌ 解析测试用例 {i} 失败: {e}")
                        continue

                if test_cases:
                    print(f"✅ 成功生成 {len(test_cases)} 个AI测试用例")
                    return test_cases
                else:
                    raise ValueError("没有成功解析任何测试用例")

            except (json.JSONDecodeError, ValueError) as e:
                print(f"❌ AI测试用例解析失败: {e}")
                print(f"AI原始返回前500字符: {ai_response[:500]}...")
                print("🔧 降级到本地生成...")
                # 降级到本地生成
                return super().generate_ai_enhanced_test_cases(requirement_text, historical_defects)

        except Exception as e:
            print(f"❌ AI测试用例生成失败: {e}")
            print("🔧 降级到本地生成...")
            # 降级到本地生成
            return super().generate_ai_enhanced_test_cases(requirement_text, historical_defects)
    
    def generate_simple_ai_test_cases(self, requirement_text: str) -> List[TestCase]:
        """生成简单的AI测试用例（更可靠）"""

        # 分析需求文本，提取可能的模块信息
        module_hints = self._extract_module_hints(requirement_text)

        simple_prompt = f"""
        请为以下功能需求生成5-8个测试用例，返回JSON数组格式：

        需求：{requirement_text[:800]}

        模块层级说明：
        - module（模块）：系统的主要功能模块，如"用户管理"、"商品管理"、"订单管理"、"首页"、"个人中心"等
        - submodule（子模块）：模块下的具体功能，如"用户管理"下的"用户注册"、"用户登录"；"首页"下的"导航栏"、"轮播图"等

        {module_hints}

        请返回JSON数组格式：
        [
          {{
            "module": "根据需求确定的主要功能模块",
            "submodule": "该模块下的具体子功能",
            "case_id": "TC_001",
            "title": "简洁明确的测试用例标题（如：验证用户登录的正常流程）",
            "precondition": "具体的前置条件",
            "test_steps": "1. 具体操作步骤一\\n2. 具体操作步骤二\\n3. 具体验证步骤",
            "expected": "明确的预期结果",
            "priority": "P1",
            "remark": "测试方法说明"
          }}
        ]

        标题编写要求：
        - 格式：验证[功能/场景]的[具体行为]
        - 示例："验证用户登录的正常流程"、"验证密码错误时的提示信息"、"验证用户名长度超限的边界处理"

        测试覆盖要求：
        1. 正常流程测试 - 验证主要功能的正常执行
        2. 边界值测试 - 验证输入字段的边界条件
        3. 异常处理测试 - 验证错误输入和异常情况
        4. 业务规则测试 - 验证特定的业务逻辑
        """

        try:
            print("🤖 使用简化AI生成...")
            ai_response = self.call_ai_api(simple_prompt)
            print(f"✅ AI响应成功，长度: {len(ai_response)}")

            # 解析JSON
            try:
                # 提取JSON部分
                json_start = ai_response.find('[')
                json_end = ai_response.rfind(']') + 1
                if json_start == -1:
                    json_start = ai_response.find('{')
                    json_end = ai_response.rfind('}') + 1

                if json_start != -1 and json_end != -1:
                    json_str = ai_response[json_start:json_end]
                    test_cases_data = json.loads(json_str)

                    if isinstance(test_cases_data, dict):
                        test_cases_data = [test_cases_data]

                    test_cases = []
                    for i, case_data in enumerate(test_cases_data):
                        test_case = TestCase(
                            module=case_data.get('module', 'AI生成模块'),
                            submodule=case_data.get('submodule', 'AI生成子模块'),
                            case_id=case_data.get('case_id', f'AI_TC_{i+1:03d}'),
                            title=case_data.get('title', f'AI生成测试用例{i+1}'),
                            precondition=case_data.get('precondition', '系统正常运行'),
                            test_steps=case_data.get('test_steps', '待补充测试步骤'),
                            expected=case_data.get('expected', '待补充预期结果'),
                            priority=Priority.P1,
                            remark=f"AI生成 - {case_data.get('remark', '使用真实AI生成')}",
                            methods_used=[TestMethod.AI_ENHANCED]
                        )
                        test_cases.append(test_case)

                    print(f"✅ 成功解析 {len(test_cases)} 个AI测试用例")
                    return test_cases
                else:
                    print("❌ 无法找到JSON格式")
                    return []

            except Exception as e:
                print(f"❌ JSON解析失败: {e}")
                return []

        except Exception as e:
            print(f"❌ AI调用失败: {e}")
            return []

    def generate_real_ai_enhanced_test_cases(self, requirement_text: str,
                                           historical_defects: List[str] = None) -> List[TestCase]:
        """生成真正的AI增强测试用例（优化版）"""
        print("🤖 正在使用真实AI大模型分析需求...")

        # 简化的AI需求分析
        try:
            ai_analysis = self.real_ai_analyze_requirements(requirement_text)
            self.ai_analysis = ai_analysis
            print(f"✅ AI分析完成 - 复杂度: {ai_analysis.complexity_score:.2f}")
        except Exception as e:
            print(f"⚠️  AI分析失败，使用本地分析: {e}")
            ai_analysis = super().ai_analyze_requirements(requirement_text)
            self.ai_analysis = ai_analysis

        # 尝试简化的AI生成
        ai_test_cases = self.generate_simple_ai_test_cases(requirement_text)

        if ai_test_cases:
            print(f"✅ AI生成成功 - 生成用例: {len(ai_test_cases)}个")
        else:
            print("⚠️  AI生成失败，使用本地生成")

        # 结合本地增强方法
        print("🔧 结合本地增强方法...")
        local_test_cases = super().generate_ai_enhanced_test_cases(requirement_text, historical_defects)

        # 合并测试用例
        all_test_cases = ai_test_cases + local_test_cases

        # 去重和优化
        final_test_cases = self._deduplicate_and_optimize(all_test_cases)

        self.test_cases = final_test_cases
        print(f"🎉 最终生成: {len(final_test_cases)}个测试用例")
        print(f"   其中AI生成: {len(ai_test_cases)}个，本地生成: {len(local_test_cases)}个")

        return final_test_cases

    def _extract_module_hints(self, requirement_text: str) -> str:
        """从需求文本中提取模块提示"""
        text_lower = requirement_text.lower()

        # 常见的模块关键词映射
        module_keywords = {
            '登录': ('用户管理', '用户登录'),
            '注册': ('用户管理', '用户注册'),
            '个人信息': ('个人中心', '基本信息'),
            '个人中心': ('个人中心', '个人资料'),
            '设置': ('个人中心', '账户设置'),
            '首页': ('首页', '页面展示'),
            '导航': ('首页', '导航栏'),
            '轮播': ('首页', '轮播图'),
            '搜索': ('搜索功能', '商品搜索'),
            '购物车': ('购物车管理', '购物车操作'),
            '订单': ('订单管理', '订单处理'),
            '支付': ('支付管理', '支付处理'),
            '商品': ('商品管理', '商品展示'),
            '分类': ('商品管理', '分类管理'),
            '库存': ('库存管理', '库存控制'),
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

        # 查找匹配的关键词
        found_modules = []
        for keyword, (module, submodule) in module_keywords.items():
            if keyword in text_lower:
                found_modules.append(f"- 可能的模块: {module} -> {submodule}")

        if found_modules:
            return f"根据需求内容，建议的模块层级：\n" + "\n".join(found_modules[:3])
        else:
            return "请根据需求内容确定合适的模块层级结构"
