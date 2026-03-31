#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MySQL数据库管理器
将AI配置、智能模板、测试用例历史迁移到MySQL数据库
"""

import os
import threading
import pymysql
import json
import hashlib
import base64
from datetime import datetime
from typing import Optional, Dict, Any, List
from contextlib import contextmanager


def _mysql_env(name: str, default: str = "") -> str:
    v = os.environ.get(name)
    if v is None:
        return default
    v = v.strip()
    if v == "":
        return default
    # .env 中 MYSQL_PASSWORD="xxx" 时去掉外层引号，避免把引号当作密码的一部分
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        v = v[1:-1].strip()
    return v if v != "" else default


class MySQLDBManager:
    """MySQL数据库管理器（连接信息来自环境变量 MYSQL_*）"""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
    ):
        self.host = host or _mysql_env("MYSQL_HOST", "localhost")
        self.port = int(port if port is not None else _mysql_env("MYSQL_PORT", "3306") or "3306")
        self.user = user or _mysql_env("MYSQL_USER", "root")
        self.password = password if password is not None else _mysql_env("MYSQL_PASSWORD", "")
        self.database = database or _mysql_env("MYSQL_DATABASE", "test_case_generator")

        self._init_lock = threading.Lock()
        self._initialized = False
        # 初始化失败后缓存异常，避免每次请求都重试连接并刷屏日志
        self._init_error: Optional[Exception] = None

    def _ensure_initialized(self) -> None:
        """首次访问数据库时再建库建表，避免导入模块时就连网（本机无法解析集群 DNS 时也能先启动 Web）。"""
        if self._initialized:
            return
        if self._init_error is not None:
            raise self._init_error
        with self._init_lock:
            if self._initialized:
                return
            if self._init_error is not None:
                raise self._init_error
            try:
                self._init_database()
                self._initialized = True
            except pymysql.Error as e:
                self._init_error = e
                print(f"❌ MySQL数据库初始化失败: {e}")
                h = (self.host or "").lower()
                errno = e.args[0] if getattr(e, "args", None) else None
                err_s = str(e).lower()
                if errno == 1045:
                    print(
                        "提示: 访问被拒（1045）。MySQL 报错里的 'root@172.17.0.1' 表示「服务器看到的客户端地址」，"
                        "不是 .env 里填错的地址：你连的是 localhost，但 Docker 里的 MySQL 常把宿主机显示成 172.17.x.x。"
                        "请在 MySQL 内为 root（或你的用户）授权该来源，例如："
                        "CREATE USER 'root'@'172.17.%' IDENTIFIED BY '你的密码'; GRANT ALL ON *.* TO 'root'@'172.17.%'; FLUSH PRIVILEGES;"
                        "或改用 127.0.0.1 并确保用户 'root'@'127.0.0.1' 存在。"
                        "若 .env 中密码写了双引号，请确认未被当作密码字符（本应用已自动去掉外层引号）。"
                    )
                elif "cluster.local" in h or ".svc." in h:
                    print(
                        "提示: 当前 MYSQL_HOST 为 Kubernetes 集群内域名，在本机通常无法解析。\n"
                        "      请使用 kubectl port-forward 后把 .env 中 MYSQL_HOST 设为 127.0.0.1。"
                    )
                elif errno == 2003 or "10061" in err_s or "refused" in err_s:
                    print(
                        "提示: 无法建立 TCP 连接（端口未监听或被拒绝）。请确认 MySQL 已启动、"
                        "MYSQL_PORT 正确，或 Docker/K8s 已做端口映射。"
                    )
                elif h in ("127.0.0.1", "localhost"):
                    print(
                        "提示: 连接本机 MySQL 失败。请确认服务已启动且 .env 中账号密码正确。"
                    )
                raise

    @contextmanager
    def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        self._ensure_initialized()
        conn = pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_database(self):
        """初始化数据库和表结构"""
        try:
            # 首先创建数据库（如果不存在）
            conn = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                charset='utf8mb4'
            )
            
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{self.database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            
            conn.close()
            
            # 创建表结构（此处不能调用 get_connection，否则会递归触发 _ensure_initialized）
            conn_tables = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
            )
            try:
                with conn_tables.cursor() as cursor:
                    # 1. AI配置表
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS ai_configs (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            provider VARCHAR(50) NOT NULL COMMENT 'AI提供商',
                            api_key_hash VARCHAR(64) NOT NULL COMMENT 'API密钥哈希值',
                            api_key_encrypted TEXT NOT NULL COMMENT 'API密钥（加密）',
                            base_url VARCHAR(255) COMMENT 'API基础URL',
                            model VARCHAR(100) COMMENT '模型名称',
                            max_tokens INT DEFAULT 4000 COMMENT '最大令牌数',
                            temperature DECIMAL(3,2) DEFAULT 0.70 COMMENT '温度参数',
                            timeout INT DEFAULT 30 COMMENT '超时时间（秒）',
                            is_active TINYINT(1) DEFAULT 1 COMMENT '是否激活',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                            INDEX idx_provider (provider),
                            INDEX idx_is_active (is_active)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI配置表'
                    ''')
                    
                    # 2. AI配置操作历史表
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS ai_config_history (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            config_id INT COMMENT '配置ID',
                            action VARCHAR(50) NOT NULL COMMENT '操作类型',
                            details TEXT COMMENT '操作详情',
                            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
                            FOREIGN KEY (config_id) REFERENCES ai_configs(id) ON DELETE SET NULL,
                            INDEX idx_config_id (config_id),
                            INDEX idx_timestamp (timestamp)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI配置操作历史表'
                    ''')
                    
                    # 3. 智能模板表
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS smart_templates (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            template_key VARCHAR(100) NOT NULL UNIQUE COMMENT '模板键名',
                            title VARCHAR(255) NOT NULL COMMENT '模板标题',
                            content TEXT NOT NULL COMMENT '模板内容',
                            category VARCHAR(50) COMMENT '模板分类',
                            description TEXT COMMENT '模板描述',
                            is_active TINYINT(1) DEFAULT 1 COMMENT '是否激活',
                            usage_count INT DEFAULT 0 COMMENT '使用次数',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                            INDEX idx_template_key (template_key),
                            INDEX idx_category (category),
                            INDEX idx_is_active (is_active)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='智能模板表'
                    ''')
                    
                    # 4. 测试用例生成会话表
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS test_case_sessions (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            session_id VARCHAR(36) NOT NULL UNIQUE COMMENT '会话UUID',
                            requirement_title VARCHAR(500) NOT NULL COMMENT '需求标题',
                            requirement_preview TEXT COMMENT '需求预览',
                            requirement_full_text LONGTEXT COMMENT '完整需求文本',
                            total_cases INT DEFAULT 0 COMMENT '生成用例总数',
                            test_type VARCHAR(50) COMMENT '测试类型',
                            generation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '生成时间',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                            INDEX idx_session_id (session_id),
                            INDEX idx_generation_time (generation_time),
                            INDEX idx_test_type (test_type)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='测试用例生成会话表'
                    ''')
                    
                    # 5. 会话关联文件表
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS session_files (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            session_id VARCHAR(36) NOT NULL COMMENT '会话UUID',
                            file_type VARCHAR(50) NOT NULL COMMENT '文件类型（excel/report/markdown）',
                            file_path VARCHAR(500) NOT NULL COMMENT '文件路径',
                            file_name VARCHAR(255) NOT NULL COMMENT '文件名',
                            file_size INT COMMENT '文件大小（字节）',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                            FOREIGN KEY (session_id) REFERENCES test_case_sessions(session_id) ON DELETE CASCADE,
                            INDEX idx_session_id (session_id),
                            INDEX idx_file_type (file_type)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='会话关联文件表'
                    ''')
                    
                    # 6. 系统配置表（用于存储test_config.json中的其他配置）
                    cursor.execute('''
                        CREATE TABLE IF NOT EXISTS system_configs (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            config_key VARCHAR(100) NOT NULL UNIQUE COMMENT '配置键',
                            config_value LONGTEXT NOT NULL COMMENT '配置值（JSON格式）',
                            config_type VARCHAR(50) COMMENT '配置类型',
                            description TEXT COMMENT '配置描述',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                            INDEX idx_config_key (config_key),
                            INDEX idx_config_type (config_type)
                        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置表'
                    ''')
                conn_tables.commit()
            finally:
                conn_tables.close()
                    
            print("✅ MySQL数据库和表结构初始化成功")
            
        except pymysql.Error:
            # 日志与提示在 _ensure_initialized 中统一输出一次
            raise
    
    # ==================== AI配置管理 ====================
    
    def _encrypt_api_key(self, api_key: str) -> str:
        """加密API密钥"""
        return base64.b64encode(api_key.encode()).decode()
    
    def _decrypt_api_key(self, encrypted_key: str) -> str:
        """解密API密钥"""
        return base64.b64decode(encrypted_key.encode()).decode()
    
    def _hash_api_key(self, api_key: str) -> str:
        """生成API密钥哈希值"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def save_ai_config(self, provider: str, api_key: str, base_url: str = None, 
                       model: str = None, max_tokens: int = 4000, 
                       temperature: float = 0.7, timeout: int = 30) -> bool:
        """保存AI配置"""
        if self._init_error is not None:
            return False
        try:
            api_key_hash = self._hash_api_key(api_key)
            api_key_encrypted = self._encrypt_api_key(api_key)
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # 先将所有配置设为非活跃
                    cursor.execute('UPDATE ai_configs SET is_active = 0')
                    
                    # 插入新配置
                    cursor.execute('''
                        INSERT INTO ai_configs 
                        (provider, api_key_hash, api_key_encrypted, base_url, model, 
                         max_tokens, temperature, timeout, is_active)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1)
                    ''', (provider, api_key_hash, api_key_encrypted, base_url, model, 
                          max_tokens, temperature, timeout))
                    
                    config_id = cursor.lastrowid
                    
                    # 记录操作历史
                    cursor.execute('''
                        INSERT INTO ai_config_history (config_id, action, details)
                        VALUES (%s, %s, %s)
                    ''', (config_id, 'SAVE', f'Provider: {provider}'))
                    
            print("✅ AI配置保存到MySQL成功")
            return True
            
        except pymysql.Error as e:
            if e is not self._init_error:
                print(f"❌ AI配置保存到MySQL失败: {e}")
            return False
    
    def load_ai_config(self) -> Optional[Dict[str, Any]]:
        """加载AI配置"""
        if self._init_error is not None:
            return None
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
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
                    
                    return {
                        'provider': row['provider'],
                        'api_key': self._decrypt_api_key(row['api_key_encrypted']),
                        'base_url': row['base_url'],
                        'model': row['model'],
                        'max_tokens': row['max_tokens'],
                        'temperature': float(row['temperature']),
                        'timeout': row['timeout']
                    }
                    
        except pymysql.Error as e:
            if e is not self._init_error:
                print(f"❌ 从MySQL加载AI配置失败: {e}")
            return None
    
    # ==================== 智能模板管理 ====================
    
    def save_smart_template(self, template_key: str, title: str, content: str, 
                           category: str = None, description: str = None) -> bool:
        """保存智能模板"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('''
                        INSERT INTO smart_templates 
                        (template_key, title, content, category, description)
                        VALUES (%s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                        title = VALUES(title),
                        content = VALUES(content),
                        category = VALUES(category),
                        description = VALUES(description),
                        updated_at = CURRENT_TIMESTAMP
                    ''', (template_key, title, content, category, description))
                    
            print(f"✅ 智能模板 '{template_key}' 保存成功")
            return True
            
        except pymysql.Error as e:
            print(f"❌ 智能模板保存失败: {e}")
            return False
    
    def load_smart_templates(self) -> Dict[str, Dict[str, Any]]:
        """加载所有智能模板"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('''
                        SELECT template_key, title, content, category, description
                        FROM smart_templates 
                        WHERE is_active = 1
                        ORDER BY usage_count DESC, created_at DESC
                    ''')
                    
                    rows = cursor.fetchall()
                    templates = {}
                    for row in rows:
                        templates[row['template_key']] = {
                            'title': row['title'],
                            'content': row['content'],
                            'category': row['category'],
                            'description': row['description']
                        }
                    
                    return templates
                    
        except pymysql.Error as e:
            print(f"❌ 从MySQL加载智能模板失败: {e}")
            return {}
    
    def increment_template_usage(self, template_key: str) -> bool:
        """增加模板使用次数"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('''
                        UPDATE smart_templates 
                        SET usage_count = usage_count + 1 
                        WHERE template_key = %s
                    ''', (template_key,))
            return True
        except pymysql.Error as e:
            print(f"❌ 更新模板使用次数失败: {e}")
            return False
    
    # ==================== 测试用例会话管理 ====================
    
    def save_test_case_session(self, session_id: str, requirement_title: str, 
                               requirement_preview: str, requirement_full_text: str,
                               total_cases: int, test_type: str, 
                               files: Dict[str, str] = None) -> bool:
        """保存测试用例生成会话"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # 插入会话记录
                    cursor.execute('''
                        INSERT INTO test_case_sessions 
                        (session_id, requirement_title, requirement_preview, 
                         requirement_full_text, total_cases, test_type)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    ''', (session_id, requirement_title, requirement_preview, 
                          requirement_full_text, total_cases, test_type))
                    
                    # 保存关联文件
                    if files:
                        for file_type, file_name in files.items():
                            cursor.execute('''
                                INSERT INTO session_files 
                                (session_id, file_type, file_path, file_name)
                                VALUES (%s, %s, %s, %s)
                            ''', (session_id, file_type, f'outputs/{file_name}', file_name))
                    
            print(f"✅ 测试用例会话 '{session_id}' 保存成功")
            return True
            
        except pymysql.Error as e:
            print(f"❌ 测试用例会话保存失败: {e}")
            return False
    
    def get_recent_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的测试用例会话"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('''
                        SELECT s.session_id as id, s.requirement_title, s.requirement_preview,
                               s.total_cases, s.test_type, 
                               s.generation_time as timestamp,
                               GROUP_CONCAT(
                                   CONCAT(f.file_type, ':', f.file_name) 
                                   SEPARATOR '||'
                               ) as files
                        FROM test_case_sessions s
                        LEFT JOIN session_files f ON s.session_id = f.session_id
                        GROUP BY s.session_id
                        ORDER BY s.generation_time DESC
                        LIMIT %s
                    ''', (limit,))
                    
                    rows = cursor.fetchall()
                    sessions = []
                    for row in rows:
                        # 解析文件列表
                        files_dict = {}
                        if row['files']:
                            for file_pair in row['files'].split('||'):
                                file_type, file_name = file_pair.split(':', 1)
                                files_dict[file_type] = file_name
                        
                        sessions.append({
                            'id': row['id'],
                            'timestamp': row['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                            'requirement_title': row['requirement_title'],
                            'requirement_preview': row['requirement_preview'],
                            'total_cases': row['total_cases'],
                            'test_type': row['test_type'],
                            'files': files_dict
                        })
                    
                    return sessions
                    
        except pymysql.Error as e:
            print(f"❌ 从MySQL获取会话记录失败: {e}")
            return []
    
    def update_session_title(self, session_id: str, new_title: str) -> bool:
        """更新会话标题"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('''
                        UPDATE test_case_sessions 
                        SET requirement_title = %s 
                        WHERE session_id = %s
                    ''', (new_title, session_id))
                    
                    if cursor.rowcount == 0:
                        return False
                    
            return True
            
        except pymysql.Error as e:
            print(f"❌ 更新会话标题失败: {e}")
            return False
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """获取会话统计数据"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    # 总用例数和会话数
                    cursor.execute('''
                        SELECT 
                            COUNT(*) as total_sessions,
                            COALESCE(SUM(total_cases), 0) as total_generated
                        FROM test_case_sessions
                    ''')
                    totals = cursor.fetchone()
                    
                    # 今天的统计
                    cursor.execute('''
                        SELECT COALESCE(SUM(total_cases), 0) as today_count
                        FROM test_case_sessions
                        WHERE DATE(generation_time) = CURDATE()
                    ''')
                    today = cursor.fetchone()
                    
                    # 本周的统计
                    cursor.execute('''
                        SELECT COALESCE(SUM(total_cases), 0) as week_count
                        FROM test_case_sessions
                        WHERE generation_time >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                    ''')
                    week = cursor.fetchone()
                    
                    # 本月的统计
                    cursor.execute('''
                        SELECT COALESCE(SUM(total_cases), 0) as month_count
                        FROM test_case_sessions
                        WHERE generation_time >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                    ''')
                    month = cursor.fetchone()
                    
                    return {
                        'total_generated': int(totals['total_generated']),
                        'total_sessions': int(totals['total_sessions']),
                        'statistics': {
                            'today': int(today['today_count']),
                            'this_week': int(week['week_count']),
                            'this_month': int(month['month_count'])
                        }
                    }
                    
        except pymysql.Error as e:
            print(f"❌ 获取统计数据失败: {e}")
            return {
                'total_generated': 0,
                'total_sessions': 0,
                'statistics': {'today': 0, 'this_week': 0, 'this_month': 0}
            }
    
    # ==================== 系统配置管理 ====================
    
    def save_system_config(self, config_key: str, config_value: Any, 
                          config_type: str = None, description: str = None) -> bool:
        """保存系统配置"""
        try:
            # 将配置值转换为JSON字符串
            if isinstance(config_value, (dict, list)):
                config_value_json = json.dumps(config_value, ensure_ascii=False)
            else:
                config_value_json = str(config_value)
            
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('''
                        INSERT INTO system_configs 
                        (config_key, config_value, config_type, description)
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                        config_value = VALUES(config_value),
                        config_type = VALUES(config_type),
                        description = VALUES(description),
                        updated_at = CURRENT_TIMESTAMP
                    ''', (config_key, config_value_json, config_type, description))
                    
            print(f"✅ 系统配置 '{config_key}' 保存成功")
            return True
            
        except pymysql.Error as e:
            print(f"❌ 系统配置保存失败: {e}")
            return False
    
    def load_system_config(self, config_key: str) -> Optional[Any]:
        """加载系统配置"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute('''
                        SELECT config_value 
                        FROM system_configs 
                        WHERE config_key = %s
                    ''', (config_key,))
                    
                    row = cursor.fetchone()
                    if not row:
                        return None
                    
                    # 尝试解析JSON
                    try:
                        return json.loads(row['config_value'])
                    except:
                        return row['config_value']
                    
        except pymysql.Error as e:
            print(f"❌ 加载系统配置失败: {e}")
            return None

# 全局数据库管理器实例
mysql_db = MySQLDBManager()
