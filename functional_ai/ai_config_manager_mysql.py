#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI配置管理器（MySQL版本）
使用MySQL数据库作为主要存储，JSON文件作为备份
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict, Any, Literal
from .real_ai_generator import AIProvider, AIConfig
from .mysql_db_manager import mysql_db

class AIConfigManagerMySQL:
    """AI配置管理器（MySQL版本）"""
    
    def __init__(self, config_dir: str = None):
        if config_dir is None:
            from .paths import PROJECT_ROOT
            config_dir = os.path.join(PROJECT_ROOT, "config")
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "ai_config.json")
        self.backup_dir = os.path.join(config_dir, "backups")
        
        # 确保目录存在
        os.makedirs(config_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def save_config(self, ai_config: AIConfig) -> Optional[Literal["mysql", "json"]]:
        """保存AI配置（MySQL + JSON 备份）。返回 'mysql'、'json'（仅本地文件）或 None（失败）。"""
        try:
            # 1. 保存到MySQL数据库（主存储）
            mysql_success = mysql_db.save_ai_config(
                provider=ai_config.provider.value,
                api_key=ai_config.api_key,
                base_url=ai_config.base_url,
                model=ai_config.model,
                max_tokens=ai_config.max_tokens,
                temperature=ai_config.temperature,
                timeout=ai_config.timeout
            )
            
            # 2. 保存到JSON文件（备份）
            json_success = self._save_to_json(ai_config)
            
            # 3. 创建本地备份
            self._create_backup(ai_config)
            
            if mysql_success:
                print("✅ AI配置保存成功（MySQL + JSON备份）")
                return "mysql"
            if json_success:
                print("⚠️  AI配置仅保存到JSON（MySQL保存失败）")
                return "json"
            print("❌ AI配置保存失败")
            return None
                
        except Exception as e:
            print(f"❌ 保存AI配置时发生错误: {e}")
            return None
    
    def _save_to_json(self, ai_config: AIConfig) -> bool:
        """保存到JSON文件（备份）"""
        try:
            config_data = {
                'provider': ai_config.provider.value,
                'api_key': ai_config.api_key,
                'base_url': ai_config.base_url,
                'model': ai_config.model,
                'max_tokens': ai_config.max_tokens,
                'temperature': ai_config.temperature,
                'timeout': ai_config.timeout,
                'saved_at': datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ JSON配置备份成功: {self.config_file}")
            return True
            
        except Exception as e:
            print(f"❌ JSON配置备份失败: {e}")
            return False
    
    def _create_backup(self, ai_config: AIConfig) -> bool:
        """创建配置备份"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.backup_dir, f"ai_config_backup_{timestamp}.json")
            
            import hashlib
            api_key_hash = hashlib.sha256(ai_config.api_key.encode()).hexdigest()[:16]
            
            config_data = {
                'provider': ai_config.provider.value,
                'api_key_hash': api_key_hash,
                'base_url': ai_config.base_url,
                'model': ai_config.model,
                'max_tokens': ai_config.max_tokens,
                'temperature': ai_config.temperature,
                'timeout': ai_config.timeout,
                'backup_time': datetime.now().isoformat()
            }
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"❌ 配置备份创建失败: {e}")
            return False
    
    def load_config(self) -> Optional[AIConfig]:
        """加载AI配置（MySQL优先，JSON备用）"""
        try:
            # 1. 尝试从MySQL加载
            config_data = mysql_db.load_ai_config()
            if config_data:
                print("✅ 从MySQL加载配置成功")
                return AIConfig(
                    provider=AIProvider(config_data['provider']),
                    api_key=config_data['api_key'],
                    base_url=config_data.get('base_url'),
                    model=config_data.get('model'),
                    max_tokens=config_data.get('max_tokens', 4000),
                    temperature=config_data.get('temperature', 0.7),
                    timeout=config_data.get('timeout', 30)
                )
            
            # 2. 尝试从JSON文件加载
            config = self._load_from_json()
            if config:
                print("✅ 从JSON文件加载配置成功（MySQL不可用）")
                return config
            
            print("ℹ️  未找到有效的AI配置")
            return None
            
        except Exception as e:
            print(f"❌ 加载AI配置时发生错误: {e}")
            return None
    
    def _load_from_json(self) -> Optional[AIConfig]:
        """从JSON文件加载"""
        try:
            if not os.path.exists(self.config_file):
                return None
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            return AIConfig(
                provider=AIProvider(config_data['provider']),
                api_key=config_data['api_key'],
                base_url=config_data.get('base_url'),
                model=config_data.get('model'),
                max_tokens=config_data.get('max_tokens', 4000),
                temperature=config_data.get('temperature', 0.7),
                timeout=config_data.get('timeout', 30)
            )
            
        except Exception as e:
            print(f"❌ JSON配置加载失败: {e}")
            return None
    
    def get_config_status(self) -> Dict[str, Any]:
        """获取配置状态"""
        try:
            config = self.load_config()
            if config:
                return {
                    'configured': True,
                    'provider': config.provider.value,
                    'model': config.model or 'default',
                    'has_api_key': bool(config.api_key),
                    'storage': 'MySQL',
                    'config_file_exists': os.path.exists(self.config_file)
                }
            else:
                return {
                    'configured': False,
                    'storage': 'None',
                    'config_file_exists': os.path.exists(self.config_file)
                }
        except Exception as e:
            return {
                'configured': False,
                'error': str(e)
            }
    
    def delete_config(self) -> bool:
        """删除AI配置"""
        try:
            # 删除MySQL中的配置（设为非活跃）
            mysql_db.save_ai_config(
                provider='none',
                api_key='',
                base_url=None,
                model=None
            )
            
            # 删除JSON文件
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
            
            print("✅ AI配置删除成功")
            return True
            
        except Exception as e:
            print(f"❌ 删除AI配置失败: {e}")
            return False

# 全局配置管理器实例（MySQL版本）
config_manager = AIConfigManagerMySQL()
