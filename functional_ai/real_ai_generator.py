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
from .ai_test_generator import AITestCaseGenerator, AIAnalysisResult, TestCase, Priority, TestMethod

class AIProvider(Enum):
    """AI服务提供商"""
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    GOOGLE_GEMINI = "google_gemini"
    BAIDU_ERNIE = "baidu_ernie"
    ERNIE = "ernie"  # Alias for BAIDU_ERNIE
    ALIBABA_QWEN = "alibaba_qwen"
    QWEN = "qwen"  # Alias for ALIBABA_QWEN
    ZHIPU_GLM = "zhipu_glm"
    CHATGLM = "chatglm"  # Alias for ZHIPU_GLM
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
        
        elif self.ai_config.provider == AIProvider.DEEPSEEK:
            # DeepSeek默认模型
            self.model = self.ai_config.model or "deepseek-chat"
            print(f"✅ DeepSeek配置: model={self.model}, base_url={self.ai_config.base_url or 'https://api.deepseek.com'}")
            
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
            if self.ai_config.provider in [AIProvider.OPENAI, AIProvider.AZURE_OPENAI, AIProvider.DEEPSEEK, AIProvider.MOONSHOT]:
                return self._call_openai_api(prompt, system_prompt)
            elif self.ai_config.provider == AIProvider.ANTHROPIC:
                return self._call_anthropic_api(prompt, system_prompt)
            elif self.ai_config.provider == AIProvider.GOOGLE_GEMINI:
                return self._call_gemini_api(prompt, system_prompt)
            elif self.ai_config.provider in [AIProvider.BAIDU_ERNIE, AIProvider.ERNIE]:
                return self._call_ernie_api(prompt, system_prompt)
            elif self.ai_config.provider in [AIProvider.ALIBABA_QWEN, AIProvider.QWEN]:
                return self._call_qwen_api(prompt, system_prompt)
            elif self.ai_config.provider in [AIProvider.ZHIPU_GLM, AIProvider.CHATGLM]:
                return self._call_glm_api(prompt, system_prompt)
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
            
            # 设置base_url，DeepSeek需要指定
            base_url = self.ai_config.base_url
            if self.ai_config.provider == AIProvider.DEEPSEEK and not base_url:
                base_url = "https://api.deepseek.com/v1"
            if self.ai_config.provider == AIProvider.MOONSHOT and not base_url:
                base_url = "https://api.moonshot.cn/v1"

            client = OpenAI(
                api_key=self.ai_config.api_key,
                base_url=base_url
            )
            
            print(f"🔗 调用API: base_url={base_url}, model={self.model}")

            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                # 批量测试用例 JSON 很长，勿用 2000 硬上限截断（会导致未闭合字符串与解析失败）
                max_tokens=min(self.ai_config.max_tokens, 16384),
                temperature=self.ai_config.temperature,
                timeout=120,
            )
            
            print(f"✅ API响应成功")
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
        except Exception as e:
            print(f"❌ OpenAI API调用失败: {e}")
            raise
    
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
        """生成简单的AI测试用例（更可靠）- 两步法：先提取功能点，再生成用例"""

        # 第一步：提取功能点
        function_points = self._extract_function_points(requirement_text)
        print(f"📋 提取到 {len(function_points)} 个功能点")
        for i, fp in enumerate(function_points, 1):
            print(f"  {i}. {fp}")
        
        if not function_points:
            print("⚠️ 未能提取功能点，使用原始需求")
            function_points_text = requirement_text[:1500]
        else:
            function_points_text = "\n".join([f"{i}. {fp}" for i, fp in enumerate(function_points, 1)])
        
        # 分析需求文本，提取可能的模块信息
        module_hints = self._extract_module_hints(requirement_text)

        # 第二步：基于功能点生成测试用例
        simple_prompt = f"""
你是一名专业测试工程师。你的任务是为以下【已提取的核心功能点】生成测试用例。

🎯 **核心要求**：你必须ONLY为下面列出的功能点生成测试用例，不要生成任何不在列表中的功能！

【已提取的核心功能点】
{function_points_text}

【原始需求参考】
{requirement_text[:500]}

⛔ **严格限制**：
1. 只能为【已提取的核心功能点】中列出的每一个功能点生成测试用例
2. 每个功能点必须生成2-3个测试用例（正常场景+边界/异常场景）
3. 不要生成任何不在功能点列表中的测试用例
4. 不要生成通用的、与功能点无关的测试用例
5. 不要生成性能、安全等非功能测试

📋 **生成要求**：

对于每个功能点，按以下格式生成：

**功能点1**: {function_points[0] if function_points else '第一个功能点'}
- 用例1: [对象]+[正常验证] - 验证该功能点的正常工作流程
- 用例2: [对象]+[边界验证] - 验证该功能点的边界条件
- 用例3: [对象]+[异常验证] - 验证该功能点的异常处理

**用例字段规范**：

1. **case_id**: 小写英文_下划线_三位数字 (例: menu_record_001)
2. **module**: 从需求提取的主模块名(中文)
3. **submodule**: 具体子功能名(中文)
4. **title**: [对象]+[验证点] 格式，必须明确指向某个功能点
5. **precondition**: 编号列表，3-5项具体前置条件
6. **test_steps**: 6-8个步骤，每步必须有[操作]/[验证]/[清理]标签+具体参数
7. **expected**: 编号列表，5-7项量化结果（包含具体数值、时间、状态）
8. **priority**: P0(核心)/P1(重要)/P2(次要)/P3(边缘)
9. **remark**: "测试方法: [方法名] | 覆盖需求: [对应功能点]"

{module_hints}

⚠️ **示例（必须遵循此格式）**：

假设功能点是"手机端设备放置检测和蒙版提示"，则生成：

{{
    "module": "游戏管理",
    "submodule": "设备检测",
    "case_id": "game_device_001",
    "title": "设备方向检测功能验证",
    "precondition": "1. 手机端游戏已启动\n2. 游戏默认为横屏模式\n3. 设备支持方向感应",
    "test_steps": "1. [操作] 手机保持横屏状态，打开游戏\n2. [验证] 检查游戏正常显示，无蒙版\n3. [操作] 将手机旋转至竖屏\n4. [验证] 检查黑色蒙版出现，遮挡游戏画面\n5. [操作] 将手机旋转回横屏\n6. [验证] 检查蒙版消失，游戏画面恢复\n7. [清理] 关闭游戏",
    "expected": "1. 横屏时游戏正常显示\n2. 竖屏时立即出现黑色蒙版(不透明度=100%)\n3. 蒙版出现时游戏画面完全不可见\n4. 旋转回横屏时蒙版消失时间<0.5秒\n5. 设备检测响应时间<200ms",
    "priority": "P0",
    "remark": "测试方法: 场景测试 | 覆盖需求: 手机端设备放置检测和蒙版提示"
}}

❌ **严格禁止**：
1. case_id包含大写字母或不规范格式
2. title使用"验证XX功能"这种通用格式
3. test_steps没有[操作][验证][清理]标签
4. test_steps包含模糊描述("输入正确的", "点击相应的")
5. expected没有量化标准("功能正常", "显示正确")
6. 生成不在【已提取的核心功能点】列表中的测试用例
7. 生成通用测试用例而不针对具体功能点

✅ **输出格式**：
返回JSON数组，每个功能点2-3个用例，总共{len(function_points)*2 if function_points else 12}-{len(function_points)*3 if function_points else 18}个用例。

🎯 **最后确认**：
- 我已理解必须ONLY为【已提取的核心功能点】生成测试用例
- 每个用例的remark字段必须明确对应某个功能点
- 不生成任何通用的、与功能点无关的测试用例

现在请严格按照以上要求生成JSON格式的测试用例数组。
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
                        # 解析优先级
                        priority_str = str(case_data.get('priority', 'P1')).upper()
                        if 'P0' in priority_str:
                            priority = Priority.P0
                        elif 'P2' in priority_str:
                            priority = Priority.P2
                        else:
                            priority = Priority.P1
                        
                        # 🔧 严格格式校验和修正
                        case_id = self._fix_case_id_format(case_data.get('case_id', f'ai_gen_{i+1:03d}'))
                        title = self._fix_title_format(case_data.get('title', f'AI生成测试用例{i+1}'))
                        test_steps = self._fix_test_steps_format(case_data.get('test_steps', '待补充测试步骤'))
                        expected = self._fix_expected_format(case_data.get('expected', '待补充预期结果'))
                        precondition = self._fix_precondition_format(case_data.get('precondition', '系统正常运行'))
                        
                        test_case = TestCase(
                            module=case_data.get('module', 'AI生成模块'),
                            submodule=case_data.get('submodule', 'AI生成子模块'),
                            case_id=case_id,
                            title=title,
                            precondition=precondition,
                            test_steps=test_steps,
                            expected=expected,
                            priority=priority,
                            remark=case_data.get('remark', '测试方法: AI生成 | 覆盖需求: AI分析'),
                            methods_used=[TestMethod.AI_ENHANCED]
                        )
                        test_cases.append(test_case)
                        print(f"✅ 成功生成用例: {case_id} - {title}")

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
            '菜单': ('菜单管理', '菜单操作'),
            '游戏': ('游戏管理', '游戏功能'),
            '记录': ('记录管理', '数据记录'),
            '排行榜': ('排行榜管理', '排行榜显示'),
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
    
    def _extract_function_points(self, requirement_text: str) -> List[str]:
        """从需求中提取核心功能点"""
        extraction_prompt = f"""
作为业务分析师，请从以下需求描述中提取**所有可测试的功能点**。

【需求内容】
{requirement_text}

【提取要求】
1. 提取出所有具体、可测试的功能点
2. 功能点应该简洁、明确、可执行
3. 每个功能点应该是一个具体的用户操作或系统行为
4. 不要包含设计、美术、开发方案等非功能内容
5. 每个功能点应该能够生成2-3个测试用例

【示例】
需求："菜单作为公共模块调整，所有控件用同一套。支持查看其他游戏记录。"
提取的功能点：
- 查看其他游戏记录
- 菜单界面元素显示一致性验证
- 切换不同游戏记录
- 游戏记录数据加载

请以简洁的列表形式返回，每行一个功能点，不要编号，不要其他解释。
直接返回功能点列表，每行一个。
"""
        
        try:
            print("🔍 正在提取功能点...")
            ai_response = self.call_ai_api(extraction_prompt)
            
            # 解析响应，提取功能点
            lines = ai_response.strip().split('\n')
            function_points = []
            
            for line in lines:
                line = line.strip()
                # 移除常见的列表标记
                line = line.lstrip('-*•· ').strip()
                # 移除数字编号
                import re
                line = re.sub(r'^\d+[\.\)、]\s*', '', line)
                
                # 过滤空行和太短的行
                if line and len(line) > 3 and len(line) < 100:
                    # 过滤明显不是功能点的内容
                    exclude_keywords = ['示例', '说明', '注意', '提取', '需求', '功能点', 
                                      '以下', '如下', 'figma', 'Figma', '等']
                    if not any(keyword in line for keyword in exclude_keywords):
                        function_points.append(line)
            
            # 去重
            function_points = list(dict.fromkeys(function_points))
            
            # 如果提取失败，使用简单的关键字匹配作为后备
            if not function_points:
                print("⚠️ AI提取失败，使用关键字匹配后备方案")
                function_points = self._extract_function_points_fallback(requirement_text)
            
            return function_points[:10]  # 最多返回10个功能点
            
        except Exception as e:
            print(f"❌ 功能点提取失败: {e}")
            # 使用后备方案
            return self._extract_function_points_fallback(requirement_text)
    
    def _extract_function_points_fallback(self, requirement_text: str) -> List[str]:
        """后备方案：使用关键字匹配提取功能点"""
        function_points = []
        
        print("🔍 使用本地关键字匹配提取功能点...")
        
        # 常见的功能动词
        action_keywords = ['查看', '显示', '切换', '创建', '添加', '删除', '修改', 
                          '编辑', '搜索', '筛选', '排序', '上传', '下载',
                          '提交', '取消', '确认', '验证', '登录', '注册',
                          '支持', '启用', '禁用', '加载', '刷新', '更新',
                          '检测', '弹', '恢复', '提示', '设置', '保存',
                          '选择', '调整', '分享', '收藏', '打开', '关闭']
    
    def _fix_case_id_format(self, case_id: str) -> str:
        """修正case_id格式为小写_下划线_数字"""
        import re
        
        # 移除TC_、TestCase_等前缀
        case_id = re.sub(r'^(TC|TestCase|Test)_', '', case_id, flags=re.IGNORECASE)
        
        # 转换为小写
        case_id = case_id.lower()
        
        # 将驼峰命名转为下划线
        case_id = re.sub(r'([a-z])([A-Z])', r'\1_\2', case_id).lower()
        
        # 确保符合格式: module_submodule_nnn
        if not re.match(r'^[a-z_]+_\d{3}$', case_id):
            # 如果不符合，尝试修复
            parts = case_id.split('_')
            if len(parts) >= 2 and parts[-1].isdigit():
                # 确保数字部分是3位
                num = int(parts[-1])
                parts[-1] = f"{num:03d}"
                case_id = '_'.join(parts)
            else:
                # 如果格式不对，生成默认格式
                case_id = f"ai_generated_{case_id}_{1:03d}"
        
        return case_id
    
    def _fix_title_format(self, title: str) -> str:
        """修正title格式为[对象]+[验证点]"""
        # 移除常见的不符合格式的前缀
        bad_patterns = ['验证', '测试', 'Test', '检查']
        for pattern in bad_patterns:
            if title.startswith(pattern):
                title = title[len(pattern):].lstrip()
        
        # 如果不包含验证、检查等动词，添加验证
        if not any(keyword in title for keyword in ['验证', '检查', '检测', '测试', '确认']):
            title = f"{title}验证"
        
        return title
    
    def _fix_test_steps_format(self, test_steps: str) -> str:
        """修正test_steps格式，添加[操作][验证][清理]标签"""
        if not test_steps or test_steps == '待补充测试步骤':
            return test_steps
        
        # 检查是否已经有标签
        if '[操作]' in test_steps or '[验证]' in test_steps:
            return test_steps
        
        # 按行分割
        lines = test_steps.split('\n')
        fixed_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 移除已有的编号
            import re
            line = re.sub(r'^\d+[\.\)、]\s*', '', line)
            
            # 根据关键词添加标签
            if any(keyword in line for keyword in ['检查', '验证', '确认', '判断']):
                line = f"[验证] {line}"
            elif any(keyword in line for keyword in ['清理', '关闭', '退出', '删除']):
                line = f"[清理] {line}"
            else:
                line = f"[操作] {line}"
            
            fixed_lines.append(line)
        
        # 重新编号
        numbered_lines = [f"{i+1}. {line}" for i, line in enumerate(fixed_lines)]
        return '\n'.join(numbered_lines)
    
    def _fix_expected_format(self, expected: str) -> str:
        """修正expected格式，确保有编号列表"""
        if not expected or expected == '待补充预期结果':
            return expected
        
        # 检查是否已经有编号
        import re
        if re.match(r'^\d+[\.\)]', expected.strip()):
            return expected
        
        # 按行分割
        lines = expected.split('\n')
        fixed_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                # 移除已有的编号
                line = re.sub(r'^\d+[\.\)、]\s*', '', line)
                fixed_lines.append(line)
        
        # 重新编号
        numbered_lines = [f"{i+1}. {line}" for i, line in enumerate(fixed_lines)]
        return '\n'.join(numbered_lines)
    
    def _fix_precondition_format(self, precondition: str) -> str:
        """修正precondition格式，确保有编号列表"""
        if not precondition or precondition == '系统正常运行':
            return precondition
        
        # 检查是否已经有编号
        import re
        if re.match(r'^\d+[\.\)]', precondition.strip()):
            return precondition
        
        # 按行分割
        lines = precondition.split('\n')
        fixed_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                # 移除已有的编号
                line = re.sub(r'^\d+[\.\)、]\s*', '', line)
                fixed_lines.append(line)
        
        # 重新编号
        numbered_lines = [f"{i+1}. {line}" for i, line in enumerate(fixed_lines)]
        return '\n'.join(numbered_lines)
        
        # 按句号和句子分割
        lines = requirement_text.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # 跳过空行和太短的行
            if not line or len(line) < 5:
                continue
            
            # 跳过图片标记
            if line.startswith('[Image:') or 'img_' in line:
                continue
            
            # 跳过编号行（如“1、”、“2、”）
            if len(line) < 15 and ('、' in line or '：' in line) and line[0].isdigit():
                continue
            
            # 提取包含功能动词的句子
            for keyword in action_keywords:
                if keyword in line:
                    # 按句号分割
                    sub_sentences = line.replace('。', '|').replace('；', '|').replace('，', '|').split('|')
                    for sub in sub_sentences:
                        sub = sub.strip()
                        if keyword in sub and 5 < len(sub) < 100:
                            # 清理编号
                            import re
                            sub = re.sub(r'^\d+[\.\)、]\s*', '', sub)
                            sub = sub.strip()
                            
                            # 过滤非功能描述
                            exclude_words = ['figma', 'Figma', '设计', '美术', '组件', 
                                           '待补充', '待调整', '样式', '色值',
                                           '字体', '大小', '开发', '后端', '前端']
                            
                            if not any(word in sub for word in exclude_words) and sub:
                                function_points.append(sub)
                    break
        
        # 去重
        function_points = list(dict.fromkeys(function_points))
        
        # 如果提取到的功能点太少，尝试更宽松的匹配
        if len(function_points) < 3:
            print("⚠️ 功能点过少，使用宽松匹配...")
            # 宽松匹配：提取所有包含“功能”、“H5”、“模块”等关键词的句子
            broad_keywords = ['功能', 'H5', '模块', '系统', '页面', '界面', 
                            '游戏', '设备', '手机', '电脑', '横版', '竖版',
                            '蒙版', '提示', '检测', '加载', '进程']
            
            for line in lines:
                line = line.strip()
                if not line or len(line) < 5:
                    continue
                if line.startswith('[Image:') or 'img_' in line:
                    continue
                    
                for keyword in broad_keywords:
                    if keyword in line:
                        # 按句号分割
                        sub_sentences = line.replace('。', '|').replace('；', '|').split('|')
                        for sub in sub_sentences:
                            sub = sub.strip()
                            if keyword in sub and 5 < len(sub) < 150:
                                import re
                                sub = re.sub(r'^\d+[\.\)、]\s*', '', sub)
                                sub = sub.strip()
                                
                                exclude_words = ['figma', 'Figma', '待补充', '待调整']
                                if not any(word in sub for word in exclude_words) and sub:
                                    function_points.append(sub)
                        break
            
            # 再次去重
            function_points = list(dict.fromkeys(function_points))
        
        print(f"✅ 本地提取到 {len(function_points)} 个功能点")
        for i, fp in enumerate(function_points[:10], 1):
            print(f"  {i}. {fp}")
        
        return function_points[:10]
