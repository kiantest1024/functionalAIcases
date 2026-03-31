#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试MySQL数据库连接和数据。在仓库根目录执行: python scripts/test_mysql_connection.py"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from functional_ai.mysql_db_manager import mysql_db

print("\n" + "="*50)
print(" "*15 + "MySQL Database Status")
print("="*50)

# 测试会话统计
stats = mysql_db.get_session_statistics()
print(f"\n📊 Test Case Statistics:")
print(f"   Total Sessions: {stats['total_sessions']}")
print(f"   Total Test Cases: {stats['total_generated']}")
print(f"   Today: {stats['statistics']['today']}")
print(f"   This Week: {stats['statistics']['this_week']}")
print(f"   This Month: {stats['statistics']['this_month']}")

# 测试AI配置
print(f"\n🤖 AI Configuration:")
ai_config = mysql_db.load_ai_config()
if ai_config:
    print(f"   Provider: {ai_config['provider']}")
    print(f"   Model: {ai_config.get('model', 'default')}")
    print(f"   Has API Key: {'Yes' if ai_config.get('api_key') else 'No'}")
else:
    print("   ⚠️  No AI configuration found")

# 测试智能模板
print(f"\n📋 Smart Templates:")
templates = mysql_db.load_smart_templates()
print(f"   Total Templates: {len(templates)}")
for i, (key, template) in enumerate(list(templates.items())[:3]):
    print(f"   {i+1}. {key}: {template['title']}")
if len(templates) > 3:
    print(f"   ... and {len(templates) - 3} more")

# 测试系统配置
print(f"\n⚙️  System Configuration:")
custom_fields = mysql_db.load_system_config('custom_fields')
if custom_fields:
    print(f"   Custom Fields: {len(custom_fields.get('default_headers', {}))} fields")

test_methods = mysql_db.load_system_config('test_methods')
if test_methods:
    print(f"   Test Methods: {len(test_methods)} methods")

# 最近的会话
print(f"\n📝 Recent Sessions (Top 5):")
recent = mysql_db.get_recent_sessions(limit=5)
for i, session in enumerate(recent):
    print(f"   {i+1}. {session['timestamp']}: {session['requirement_title'][:40]}... ({session['total_cases']} cases)")

print("\n" + "="*50)
print("✅ MySQL Connection and Data Verified!")
print("="*50 + "\n")
