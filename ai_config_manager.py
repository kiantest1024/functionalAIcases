#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI配置管理器
提供可靠的AI配置保存、加载和管理功能
"""

import os
import json
import sqlite3
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from real_ai_generator import AIProvider, AIConfig

class AIConfigManager:
    """AI配置管理器"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "ai_config.json")
        self.db_file = os.path.join(config_dir, "ai_config.db")
        self.backup_dir = os.path.join(config_dir, "backups")
        
        # 确保目录存在
        os.makedirs(config_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # 初始化数据库
        self._init_database()
    
    def _init_database(self):
        """初始化SQLite数据库"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_configs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        provider TEXT NOT NULL,
                        api_key_hash TEXT NOT NULL,
                        api_key_encrypted TEXT NOT NULL,
                        base_url TEXT,
                        model TEXT,
                        max_tokens INTEGER DEFAULT 4000,
                        temperature REAL DEFAULT 0.7,
                        timeout INTEGER DEFAULT 30,
                        is_active INTEGER DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS config_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        config_id INTEGER,
                        action TEXT NOT NULL,
                        details TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (config_id) REFERENCES ai_configs (id)
                    )
                ''')
                
                conn.commit()
                print("✅ AI配置数据库初始化成功")
        except Exception as e:
            print(f"❌ 数据库初始化失败: {e}")
    
    def _encrypt_api_key(self, api_key: str) -> str:
        """简单加密API密钥（实际项目中应使用更强的加密）"""
        # 这里使用简单的base64编码，实际项目中应使用更强的加密
        import base64
        return base64.b64encode(api_key.encode()).decode()
    
    def _decrypt_api_key(self, encrypted_key: str) -> str:
        """解密API密钥"""
        import base64
        return base64.b64decode(encrypted_key.encode()).decode()
    
    def _hash_api_key(self, api_key: str) -> str:
        """生成API密钥的哈希值"""
        return hashlib.sha256(api_key.encode()).hexdigest()[:16]
    
    def save_config(self, ai_config: AIConfig) -> bool:
        """保存AI配置（多重保存策略）"""
        try:
            # 1. 保存到JSON文件
            json_success = self._save_to_json(ai_config)
            
            # 2. 保存到数据库
            db_success = self._save_to_database(ai_config)
            
            # 3. 创建备份
            backup_success = self._create_backup(ai_config)
            
            if json_success or db_success:
                print("✅ AI配置保存成功")
                self._log_action("SAVE", f"Provider: {ai_config.provider.value}")
                return True
            else:
                print("❌ AI配置保存失败")
                return False
                
        except Exception as e:
            print(f"❌ 保存AI配置时发生错误: {e}")
            return False
    
    def _save_to_json(self, ai_config: AIConfig) -> bool:
        """保存到JSON文件"""
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
            
            print(f"✅ JSON配置保存成功: {self.config_file}")
            return True
            
        except Exception as e:
            print(f"❌ JSON配置保存失败: {e}")
            return False
    
    def _save_to_database(self, ai_config: AIConfig) -> bool:
        """保存到数据库"""
        try:
            api_key_hash = self._hash_api_key(ai_config.api_key)
            api_key_encrypted = self._encrypt_api_key(ai_config.api_key)
            
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                # 先将所有配置设为非活跃
                cursor.execute('UPDATE ai_configs SET is_active = 0')
                
                # 插入新配置
                cursor.execute('''
                    INSERT INTO ai_configs 
                    (provider, api_key_hash, api_key_encrypted, base_url, model, 
                     max_tokens, temperature, timeout, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
                ''', (
                    ai_config.provider.value,
                    api_key_hash,
                    api_key_encrypted,
                    ai_config.base_url,
                    ai_config.model,
                    ai_config.max_tokens,
                    ai_config.temperature,
                    ai_config.timeout
                ))
                
                conn.commit()
                print("✅ 数据库配置保存成功")
                return True
                
        except Exception as e:
            print(f"❌ 数据库配置保存失败: {e}")
            return False
    
    def _create_backup(self, ai_config: AIConfig) -> bool:
        """创建配置备份"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(self.backup_dir, f"ai_config_backup_{timestamp}.json")
            
            config_data = {
                'provider': ai_config.provider.value,
                'api_key_hash': self._hash_api_key(ai_config.api_key),
                'base_url': ai_config.base_url,
                'model': ai_config.model,
                'max_tokens': ai_config.max_tokens,
                'temperature': ai_config.temperature,
                'timeout': ai_config.timeout,
                'backup_time': datetime.now().isoformat()
            }
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 配置备份创建成功: {backup_file}")
            return True
            
        except Exception as e:
            print(f"❌ 配置备份创建失败: {e}")
            return False
    
    def load_config(self) -> Optional[AIConfig]:
        """加载AI配置（多重加载策略）"""
        try:
            # 1. 尝试从JSON文件加载
            config = self._load_from_json()
            if config:
                print("✅ 从JSON文件加载配置成功")
                return config
            
            # 2. 尝试从数据库加载
            config = self._load_from_database()
            if config:
                print("✅ 从数据库加载配置成功")
                return config
            
            # 3. 尝试从备份加载
            config = self._load_from_backup()
            if config:
                print("✅ 从备份文件加载配置成功")
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
    
    def _load_from_database(self) -> Optional[AIConfig]:
        """从数据库加载"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT provider, api_key_encrypted, base_url, model, 
                           max_tokens, temperature, timeout
                    FROM ai_configs 
                    WHERE is_active = 1 
                    ORDER BY updated_at DESC 
                    LIMIT 1
                ''')
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                provider, api_key_encrypted, base_url, model, max_tokens, temperature, timeout = row
                api_key = self._decrypt_api_key(api_key_encrypted)
                
                return AIConfig(
                    provider=AIProvider(provider),
                    api_key=api_key,
                    base_url=base_url,
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=timeout
                )
                
        except Exception as e:
            print(f"❌ 数据库配置加载失败: {e}")
            return None
    
    def _load_from_backup(self) -> Optional[AIConfig]:
        """从最新备份加载"""
        try:
            if not os.path.exists(self.backup_dir):
                return None
            
            backup_files = [f for f in os.listdir(self.backup_dir) if f.startswith('ai_config_backup_')]
            if not backup_files:
                return None
            
            # 获取最新的备份文件
            latest_backup = sorted(backup_files)[-1]
            backup_path = os.path.join(self.backup_dir, latest_backup)
            
            with open(backup_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 备份文件不包含API密钥，需要用户重新输入
            print("⚠️  从备份恢复配置，请重新输入API密钥")
            return None
            
        except Exception as e:
            print(f"❌ 备份配置加载失败: {e}")
            return None
    
    def _log_action(self, action: str, details: str = ""):
        """记录操作日志"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO config_history (action, details)
                    VALUES (?, ?)
                ''', (action, details))
                conn.commit()
        except Exception as e:
            print(f"❌ 日志记录失败: {e}")
    
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
                    'config_file_exists': os.path.exists(self.config_file),
                    'database_exists': os.path.exists(self.db_file)
                }
            else:
                return {
                    'configured': False,
                    'config_file_exists': os.path.exists(self.config_file),
                    'database_exists': os.path.exists(self.db_file)
                }
        except Exception as e:
            return {
                'configured': False,
                'error': str(e)
            }
    
    def delete_config(self) -> bool:
        """删除AI配置"""
        try:
            # 删除JSON文件
            if os.path.exists(self.config_file):
                os.remove(self.config_file)
            
            # 在数据库中标记为非活跃
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE ai_configs SET is_active = 0')
                conn.commit()
            
            self._log_action("DELETE", "AI配置已删除")
            print("✅ AI配置删除成功")
            return True
            
        except Exception as e:
            print(f"❌ 删除AI配置失败: {e}")
            return False

# 全局配置管理器实例
config_manager = AIConfigManager()
