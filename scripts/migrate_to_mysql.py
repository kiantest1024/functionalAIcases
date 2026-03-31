#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据迁移脚本：将现有 JSON 数据迁移到 MySQL。

在仓库根目录执行: python scripts/migrate_to_mysql.py

运行前请设置环境变量 MYSQL_HOST、MYSQL_PORT、MYSQL_USER、MYSQL_PASSWORD、MYSQL_DATABASE
（可参考项目根目录 .env.example）。
"""

import os
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from functional_ai.mysql_db_manager import mysql_db


def _test_config_path() -> Path:
    p = ROOT / "data" / "test_config.json"
    if p.is_file():
        return p
    legacy = ROOT / "test_config.json"
    if legacy.is_file():
        return legacy
    return p


def _history_path() -> Path:
    p = ROOT / "data" / "test_case_history.json"
    if p.is_file():
        return p
    legacy = ROOT / "test_case_history.json"
    if legacy.is_file():
        return legacy
    return p


def migrate_ai_config():
    """迁移AI配置"""
    print("\n" + "="*50)
    print("开始迁移AI配置...")
    print("="*50)
    
    config_file = ROOT / "config" / "ai_config.json"
    if not config_file.is_file():
        print("⚠️  AI配置文件不存在，跳过迁移")
        return
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        success = mysql_db.save_ai_config(
            provider=config_data.get('provider', 'openai'),
            api_key=config_data.get('api_key', ''),
            base_url=config_data.get('base_url'),
            model=config_data.get('model'),
            max_tokens=config_data.get('max_tokens', 4000),
            temperature=config_data.get('temperature', 0.7),
            timeout=config_data.get('timeout', 30)
        )
        
        if success:
            print(f"✅ AI配置迁移成功: Provider={config_data.get('provider')}")
        else:
            print("❌ AI配置迁移失败")
            
    except Exception as e:
        print(f"❌ AI配置迁移出错: {e}")

def migrate_smart_templates():
    """迁移智能模板"""
    print("\n" + "="*50)
    print("开始迁移智能模板...")
    print("="*50)
    
    config_file = _test_config_path()
    if not config_file.is_file():
        print("⚠️  未找到 data/test_config.json（或根目录 test_config.json），跳过迁移")
        return
    
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config_data = json.load(f)
        
        templates = config_data.get('sample_requirements', {})
        if not templates:
            print("⚠️  没有找到智能模板数据")
            return
        
        success_count = 0
        for template_key, template_data in templates.items():
            # 确定分类
            category = None
            if 'login' in template_key or 'registration' in template_key:
                category = 'user_management'
            elif 'order' in template_key or 'payment' in template_key:
                category = 'business_process'
            elif 'api' in template_key:
                category = 'api_testing'
            elif 'upload' in template_key:
                category = 'file_operation'
            
            success = mysql_db.save_smart_template(
                template_key=template_key,
                title=template_data.get('title', ''),
                content=template_data.get('content', ''),
                category=category,
                description=f"模板类型: {category or '通用'}"
            )
            
            if success:
                success_count += 1
        
        print(f"✅ 智能模板迁移完成: {success_count}/{len(templates)} 成功")
        
        # 迁移其他系统配置
        print("\n迁移其他系统配置...")
        
        # custom_fields
        if 'custom_fields' in config_data:
            mysql_db.save_system_config(
                config_key='custom_fields',
                config_value=config_data['custom_fields'],
                config_type='dict',
                description='自定义字段映射'
            )
            print("✅ 自定义字段配置迁移成功")
        
        # test_methods
        if 'test_methods' in config_data:
            mysql_db.save_system_config(
                config_key='test_methods',
                config_value=config_data['test_methods'],
                config_type='list',
                description='测试方法列表'
            )
            print("✅ 测试方法列表迁移成功")
            
    except Exception as e:
        print(f"❌ 智能模板迁移出错: {e}")

def migrate_test_case_history():
    """迁移测试用例历史"""
    print("\n" + "="*50)
    print("开始迁移测试用例历史...")
    print("="*50)
    
    history_file = _history_path()
    if not history_file.is_file():
        print("⚠️  未找到 data/test_case_history.json（或根目录 test_case_history.json），跳过迁移")
        return
    
    try:
        with open(history_file, "r", encoding="utf-8") as f:
            history_data = json.load(f)
        
        sessions = history_data.get('sessions', [])
        if not sessions:
            print("⚠️  没有找到历史会话数据")
            return
        
        success_count = 0
        for session in sessions:
            # 提取完整需求文本（如果有的话）
            requirement_full_text = session.get('requirement_full_text', 
                                                session.get('requirement_preview', ''))
            
            success = mysql_db.save_test_case_session(
                session_id=session.get('id', ''),
                requirement_title=session.get('requirement_title', '未命名需求'),
                requirement_preview=session.get('requirement_preview', ''),
                requirement_full_text=requirement_full_text,
                total_cases=session.get('total_cases', 0),
                test_type=session.get('test_type', 'Unknown'),
                files=session.get('files', {})
            )
            
            if success:
                success_count += 1
        
        print(f"✅ 测试用例历史迁移完成: {success_count}/{len(sessions)} 成功")
        
    except Exception as e:
        print(f"❌ 测试用例历史迁移出错: {e}")

def verify_migration():
    """验证迁移结果"""
    print("\n" + "="*50)
    print("验证迁移结果...")
    print("="*50)
    
    # 验证AI配置
    ai_config = mysql_db.load_ai_config()
    if ai_config:
        print(f"✅ AI配置: Provider={ai_config.get('provider')}, Model={ai_config.get('model')}")
    else:
        print("⚠️  未找到AI配置")
    
    # 验证智能模板
    templates = mysql_db.load_smart_templates()
    print(f"✅ 智能模板: 共 {len(templates)} 个")
    for key in list(templates.keys())[:3]:
        print(f"   - {key}: {templates[key]['title']}")
    if len(templates) > 3:
        print(f"   - ... 还有 {len(templates) - 3} 个模板")
    
    # 验证系统配置
    custom_fields = mysql_db.load_system_config('custom_fields')
    if custom_fields:
        print(f"✅ 自定义字段: {len(custom_fields.get('default_headers', {}))} 个字段")
    
    test_methods = mysql_db.load_system_config('test_methods')
    if test_methods:
        print(f"✅ 测试方法: {len(test_methods)} 个方法")
    
    # 验证测试用例历史
    stats = mysql_db.get_session_statistics()
    print(f"✅ 测试用例会话: {stats['total_sessions']} 个会话, {stats['total_generated']} 个用例")
    print(f"   - 今天: {stats['statistics']['today']} 个")
    print(f"   - 本周: {stats['statistics']['this_week']} 个")
    print(f"   - 本月: {stats['statistics']['this_month']} 个")
    
    # 显示最近的会话
    recent_sessions = mysql_db.get_recent_sessions(limit=3)
    if recent_sessions:
        print(f"\n✅ 最近的会话:")
        for session in recent_sessions:
            print(f"   - {session['timestamp']}: {session['requirement_title'][:50]}... ({session['total_cases']} 用例)")

def main():
    """主函数"""
    print("\n" + "="*70)
    print(" "*20 + "数据迁移到MySQL")
    print("="*70)
    print(f"目标数据库: {mysql_db.host}:{mysql_db.port}/{mysql_db.database}")
    print("="*70)
    
    try:
        # 执行迁移
        migrate_ai_config()
        migrate_smart_templates()
        migrate_test_case_history()
        
        # 验证结果
        verify_migration()
        
        print("\n" + "="*70)
        print(" "*25 + "迁移完成！")
        print("="*70)
        print("\n提示:")
        print("1. 原有JSON文件已保留，可以作为备份")
        print("2. 后续操作将使用MySQL数据库")
        print("3. 可以删除以下文件以完全切换到MySQL:")
        print("   - data/test_case_history.json（或根目录旧版 test_case_history.json）")
        print("   - config/ai_config.json")
        print("   - config/ai_config.db (SQLite)")
        print("\n注意: 建议先备份这些文件，确认MySQL运行正常后再删除")
        
    except Exception as e:
        print(f"\n❌ 迁移过程发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
