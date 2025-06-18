#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI增强功能测试用例生成器 - Web版本
结合人工智能和所有测试设计方法的Web应用
"""

from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
import os
import json
import tempfile
import time
from datetime import datetime
import io
import zipfile
from ai_test_generator import AITestCaseGenerator
from comprehensive_test_generator import ComprehensiveTestGenerator
from ai_test_generator import AITestMethod, AIAnalysisResult
from real_ai_generator import RealAITestCaseGenerator, AIProvider, AIConfig
from ai_config_manager import config_manager

app = Flask(__name__)
app.secret_key = 'ai_test_case_generator_secret_key_2025'

# 配置上传文件夹
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# 确保文件夹存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def create_ai_generator(custom_headers=None):
    """创建AI生成器（优先使用真实AI）"""
    ai_config = config_manager.load_config()
    if ai_config and ai_config.api_key:
        try:
            return RealAITestCaseGenerator(ai_config, custom_headers)
        except Exception as e:
            print(f"创建真实AI生成器失败，降级到模拟AI: {e}")

    # 降级到全面测试生成器
    return ComprehensiveTestGenerator(custom_headers)

@app.route('/')
def index():
    """AI增强主页"""
    return render_template('ai_index.html')

@app.route('/ai_generate', methods=['GET', 'POST'])
def ai_generate():
    """AI增强生成测试用例页面"""
    if request.method == 'GET':
        return render_template('ai_generate.html')
    
    try:
        # 获取表单数据
        requirement_text = request.form.get('requirement_text', '').strip()
        historical_defects = request.form.get('historical_defects', '').strip()
        custom_headers = request.form.get('custom_headers', '').strip()
        ai_enhancement_level = request.form.get('ai_enhancement_level', 'medium')
        
        if not requirement_text:
            flash('请输入需求文档内容', 'error')
            return redirect(url_for('ai_generate'))
        
        # 处理历史缺陷
        defects_list = []
        if historical_defects:
            defects_list = [d.strip() for d in historical_defects.split('\n') if d.strip()]
        
        # 处理自定义字段标题
        headers_dict = None
        if custom_headers:
            try:
                headers_dict = json.loads(custom_headers)
            except json.JSONDecodeError:
                flash('自定义字段格式错误，请使用正确的JSON格式', 'error')
                return redirect(url_for('ai_generate'))
        
        # 创建AI增强生成器（优先使用真实AI）
        ai_generator = create_ai_generator(headers_dict)
        
        # AI分析需求（优先使用真实AI）
        if hasattr(ai_generator, 'real_ai_analyze_requirements'):
            print("🤖 使用真实AI分析需求...")
            ai_analysis = ai_generator.real_ai_analyze_requirements(requirement_text)
        else:
            print("🔧 使用模拟AI分析需求...")
            ai_analysis = ai_generator.ai_analyze_requirements(requirement_text)
        
        # 根据增强级别调整生成策略
        if ai_enhancement_level == 'basic':
            # 基础增强 - 使用全面测试生成器
            if hasattr(ai_generator, 'generate_comprehensive_test_cases'):
                test_cases = ai_generator.generate_comprehensive_test_cases(requirement_text, defects_list)
            else:
                test_cases = ai_generator.generate_all_test_cases(requirement_text, defects_list)
        elif ai_enhancement_level == 'advanced':
            # 高级AI增强 - 使用真实AI
            if hasattr(ai_generator, 'generate_real_ai_enhanced_test_cases'):
                test_cases = ai_generator.generate_real_ai_enhanced_test_cases(requirement_text, defects_list)
            elif hasattr(ai_generator, 'generate_comprehensive_test_cases'):
                test_cases = ai_generator.generate_comprehensive_test_cases(requirement_text, defects_list)
            else:
                test_cases = ai_generator.generate_ai_enhanced_test_cases(requirement_text, defects_list)
        else:
            # 中等AI增强（默认）
            if hasattr(ai_generator, 'generate_real_ai_enhanced_test_cases'):
                test_cases = ai_generator.generate_real_ai_enhanced_test_cases(requirement_text, defects_list)
            elif hasattr(ai_generator, 'generate_comprehensive_test_cases'):
                test_cases = ai_generator.generate_comprehensive_test_cases(requirement_text, defects_list)
            else:
                test_cases = ai_generator.generate_ai_enhanced_test_cases(requirement_text, defects_list)
        
        # 生成文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Excel文件
        excel_filename = f"ai_test_cases_{timestamp}.xlsx"
        excel_path = os.path.join(app.config['OUTPUT_FOLDER'], excel_filename)

        print(f"📊 准备生成Excel文件: {excel_filename}")
        print(f"📁 Excel文件路径: {excel_path}")

        try:
            ai_generator.export_to_excel(excel_path)
            if os.path.exists(excel_path):
                file_size = os.path.getsize(excel_path)
                print(f"✅ Excel文件生成成功: {excel_path} ({file_size} bytes)")
            else:
                print(f"❌ Excel文件生成失败: 文件不存在 {excel_path}")
        except Exception as e:
            print(f"❌ Excel文件生成异常: {e}")

        # AI增强报告
        ai_report_filename = f"ai_enhanced_report_{timestamp}.md"
        ai_report_path = os.path.join(app.config['OUTPUT_FOLDER'], ai_report_filename)

        print(f"📝 准备生成Markdown报告: {ai_report_filename}")
        print(f"📁 Markdown文件路径: {ai_report_path}")

        try:
            ai_generator.export_ai_enhanced_report(ai_report_path)
            if os.path.exists(ai_report_path):
                file_size = os.path.getsize(ai_report_path)
                print(f"✅ Markdown报告生成成功: {ai_report_path} ({file_size} bytes)")
            else:
                print(f"❌ Markdown报告生成失败: 文件不存在 {ai_report_path}")
        except Exception as e:
            print(f"❌ Markdown报告生成异常: {e}")
        
        # 生成统计信息
        stats = generate_ai_statistics(test_cases, ai_analysis)
        
        return render_template('ai_result.html', 
                             test_cases=test_cases[:10],  # 只显示前10个
                             ai_analysis=ai_analysis,
                             stats=stats,
                             excel_file=excel_filename,
                             ai_report_file=ai_report_filename,
                             total_cases=len(test_cases),
                             enhancement_level=ai_enhancement_level)
        
    except Exception as e:
        flash(f'AI生成测试用例时发生错误: {str(e)}', 'error')
        return redirect(url_for('ai_generate'))

@app.route('/ai_analysis', methods=['POST'])
def ai_analysis():
    """AI需求分析接口"""
    try:
        data = request.get_json()
        requirement_text = data.get('requirement_text', '')
        
        if not requirement_text:
            return jsonify({'error': '需求文档内容不能为空'}), 400
        
        # 创建AI生成器并分析（优先使用真实AI）
        ai_generator = create_ai_generator()

        # 使用真实AI分析（如果可用）
        if hasattr(ai_generator, 'real_ai_analyze_requirements'):
            print("🤖 AI分析接口使用真实AI...")
            ai_analysis = ai_generator.real_ai_analyze_requirements(requirement_text)
        else:
            print("🔧 AI分析接口使用模拟AI...")
            ai_analysis = ai_generator.ai_analyze_requirements(requirement_text)
        
        # 转换为JSON格式
        analysis_data = {
            'complexity_score': ai_analysis.complexity_score,
            'complexity_level': get_complexity_level(ai_analysis.complexity_score),
            'risk_areas': ai_analysis.risk_areas,
            'critical_paths': ai_analysis.critical_paths,
            'data_patterns': ai_analysis.data_patterns,
            'business_rules': ai_analysis.business_rules,
            'integration_points': ai_analysis.integration_points,
            'performance_concerns': ai_analysis.performance_concerns,
            'security_risks': ai_analysis.security_risks,
            'usability_factors': ai_analysis.usability_factors
        }
        
        return jsonify({
            'success': True,
            'analysis': analysis_data,
            'recommendations': generate_ai_recommendations(ai_analysis)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ai_smart_template')
def ai_smart_template():
    """AI智能模板页面"""
    # 加载配置文件中的模板
    try:
        with open('test_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        templates = config.get('sample_requirements', {})
    except:
        templates = {}
    
    return render_template('ai_smart_template.html', templates=templates)

@app.route('/ai_generate_from_smart_template', methods=['POST'])
def ai_generate_from_smart_template():
    """从AI智能模板生成测试用例"""
    try:
        template_name = request.form.get('template_name')
        ai_enhancement_options = request.form.getlist('ai_enhancement_options')
        custom_params = request.form.get('custom_params', '').strip()
        
        # 加载模板
        with open('test_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        templates = config.get('sample_requirements', {})
        if template_name not in templates:
            flash('模板不存在', 'error')
            return redirect(url_for('ai_smart_template'))
        
        template = templates[template_name]
        requirement_text = template['content']
        
        # 应用自定义参数
        if custom_params:
            try:
                params = json.loads(custom_params)
                for key, value in params.items():
                    requirement_text = requirement_text.replace(f"{{{key}}}", str(value))
            except json.JSONDecodeError:
                flash('自定义参数格式错误', 'error')
                return redirect(url_for('ai_smart_template'))
        
        # 创建AI增强生成器（优先使用真实AI）
        ai_generator = create_ai_generator()
        
        # 根据AI增强选项调整生成策略
        if 'deep_analysis' in ai_enhancement_options:
            # 深度分析模式 - 使用真实AI
            if hasattr(ai_generator, 'real_ai_analyze_requirements'):
                print("🤖 智能模板使用真实AI深度分析...")
                ai_analysis = ai_generator.real_ai_analyze_requirements(requirement_text)
                if hasattr(ai_generator, 'generate_real_ai_enhanced_test_cases'):
                    test_cases = ai_generator.generate_real_ai_enhanced_test_cases(requirement_text)
                else:
                    test_cases = ai_generator.generate_ai_enhanced_test_cases(requirement_text)
            else:
                print("🔧 智能模板使用模拟AI分析...")
                ai_analysis = ai_generator.ai_analyze_requirements(requirement_text)
                test_cases = ai_generator.generate_ai_enhanced_test_cases(requirement_text)
        else:
            # 标准模式 - 使用全面测试生成器
            if hasattr(ai_generator, 'generate_comprehensive_test_cases'):
                test_cases = ai_generator.generate_comprehensive_test_cases(requirement_text)
            else:
                test_cases = ai_generator.generate_all_test_cases(requirement_text)
            if hasattr(ai_generator, 'real_ai_analyze_requirements'):
                ai_analysis = ai_generator.real_ai_analyze_requirements(requirement_text)
            else:
                ai_analysis = ai_generator.ai_analyze_requirements(requirement_text)
        
        # 应用AI增强选项
        if 'risk_prioritization' in ai_enhancement_options:
            ai_generator._adjust_risk_based_priority(test_cases, ai_analysis)
        
        if 'coverage_optimization' in ai_enhancement_options:
            test_cases = ai_generator._optimize_coverage(test_cases, ai_analysis)
        
        # 生成文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        excel_filename = f"ai_smart_template_{template_name}_{timestamp}.xlsx"
        excel_path = os.path.join(app.config['OUTPUT_FOLDER'], excel_filename)
        ai_generator.export_to_excel(excel_path)
        
        ai_report_filename = f"ai_smart_report_{template_name}_{timestamp}.md"
        ai_report_path = os.path.join(app.config['OUTPUT_FOLDER'], ai_report_filename)
        ai_generator.export_ai_enhanced_report(ai_report_path)
        
        flash(f'成功从AI智能模板"{template["title"]}"生成了{len(test_cases)}个测试用例', 'success')
        
        stats = generate_ai_statistics(test_cases, ai_analysis)
        
        return render_template('ai_smart_template_result.html',
                             template_title=template['title'],
                             test_cases=test_cases[:10],
                             ai_analysis=ai_analysis,
                             stats=stats,
                             total_cases=len(test_cases),
                             excel_file=excel_filename,
                             ai_report_file=ai_report_filename,
                             enhancement_options=ai_enhancement_options)
        
    except Exception as e:
        flash(f'从AI智能模板生成测试用例时发生错误: {str(e)}', 'error')
        return redirect(url_for('ai_smart_template'))

@app.route('/download/<filename>')
def download_file(filename):
    """下载文件"""
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)

        print(f"🔍 下载请求: {filename}")
        print(f"📁 完整路径: {file_path}")
        print(f"📂 输出目录: {app.config['OUTPUT_FOLDER']}")

        # 首先检查文件是否存在
        if os.path.exists(file_path):
            print(f"✅ 文件存在，开始下载")
            # 使用绝对路径确保Flask能找到文件
            abs_file_path = os.path.abspath(file_path)
            print(f"📁 使用绝对路径: {abs_file_path}")

            # 再次验证绝对路径文件存在
            if os.path.exists(abs_file_path):
                try:
                    return send_file(abs_file_path, as_attachment=True)
                except Exception as e:
                    print(f"❌ send_file失败: {e}")
                    # 如果send_file失败，尝试手动读取文件
                    try:
                        from flask import Response
                        with open(abs_file_path, 'rb') as f:
                            file_data = f.read()

                        response = Response(
                            file_data,
                            mimetype='application/octet-stream',
                            headers={
                                'Content-Disposition': f'attachment; filename={filename}',
                                'Content-Length': len(file_data)
                            }
                        )
                        print(f"✅ 使用手动读取方式下载文件")
                        return response
                    except Exception as e2:
                        print(f"❌ 手动读取也失败: {e2}")
            else:
                print(f"❌ 绝对路径文件不存在: {abs_file_path}")

        # 如果文件不存在，尝试查找类似的文件
        print(f"⚠️ 文件不存在: {file_path}")

        # 列出outputs目录中的所有文件
        output_dir = app.config['OUTPUT_FOLDER']
        if os.path.exists(output_dir):
            all_files = os.listdir(output_dir)
            print(f"📄 目录中的文件: {all_files}")
        else:
            print(f"❌ 输出目录不存在: {output_dir}")
            flash('输出目录不存在', 'error')
            return redirect(url_for('index'))

        # 提取文件名模式（去掉时间戳）
        if filename.startswith('ai_test_cases_'):
            pattern = 'ai_test_cases_'
            extension = '.xlsx'
        elif filename.startswith('ai_enhanced_report_'):
            pattern = 'ai_enhanced_report_'
            extension = '.md'
        elif filename.startswith('ai_smart_template_'):
            pattern = 'ai_smart_template_'
            extension = '.xlsx'
        else:
            pattern = None
            extension = None

        print(f"🔍 查找模式: {pattern}{extension}")

        # 查找最新的匹配文件
        if pattern and extension:
            matching_files = [f for f in all_files if f.startswith(pattern) and f.endswith(extension)]
            print(f"📋 匹配的文件: {matching_files}")

            if matching_files:
                # 按修改时间排序，获取最新的文件
                latest_file = max(matching_files, key=lambda f: os.path.getmtime(os.path.join(output_dir, f)))
                latest_path = os.path.join(output_dir, latest_file)

                print(f"✅ 找到最新文件: {latest_file}")
                print(f"📁 最新文件路径: {latest_path}")

                if os.path.exists(latest_path):
                    return send_file(latest_path, as_attachment=True)
                else:
                    print(f"❌ 最新文件不存在: {latest_path}")

        # 如果还是找不到，返回错误
        print(f"❌ 无法找到匹配的文件")
        flash(f'文件不存在: {filename}。请重新生成测试用例。', 'error')
        return redirect(url_for('ai_generate'))

    except Exception as e:
        print(f"❌ 下载文件异常: {e}")
        import traceback
        traceback.print_exc()
        flash(f'下载文件时发生错误: {str(e)}', 'error')
        return redirect(url_for('ai_generate'))

def generate_ai_statistics(test_cases, ai_analysis):
    """生成AI统计信息"""
    stats = {
        'total_cases': len(test_cases),
        'complexity_score': ai_analysis.complexity_score,
        'complexity_level': get_complexity_level(ai_analysis.complexity_score),
        'priority_stats': {},
        'ai_method_stats': {},
        'risk_coverage': {},
        'enhancement_metrics': {}
    }
    
    # 优先级统计
    for case in test_cases:
        priority = case.priority.value
        stats['priority_stats'][priority] = stats['priority_stats'].get(priority, 0) + 1
    
    # AI方法统计
    for case in test_cases:
        for ai_method in AITestMethod:
            if ai_method.value in case.remark:
                stats['ai_method_stats'][ai_method.value] = stats['ai_method_stats'].get(ai_method.value, 0) + 1
    
    # 风险覆盖统计
    if ai_analysis.risk_areas:
        covered_risks = set()
        for case in test_cases:
            case_text = f"{case.module} {case.submodule} {case.test_steps} {case.remark}".lower()
            for risk in ai_analysis.risk_areas:
                if risk.lower() in case_text:
                    covered_risks.add(risk)
        
        stats['risk_coverage'] = {
            'total_risks': len(ai_analysis.risk_areas),
            'covered_risks': len(covered_risks),
            'coverage_rate': len(covered_risks) / len(ai_analysis.risk_areas) * 100 if ai_analysis.risk_areas else 0
        }
    
    # AI增强指标
    ai_enhanced_cases = sum(1 for case in test_cases if any(ai_method.value in case.remark for ai_method in AITestMethod))
    stats['enhancement_metrics'] = {
        'ai_enhanced_cases': ai_enhanced_cases,
        'enhancement_rate': ai_enhanced_cases / len(test_cases) * 100 if test_cases else 0
    }
    
    return stats

def get_complexity_level(score):
    """获取复杂度等级"""
    if score > 0.7:
        return "高"
    elif score > 0.4:
        return "中"
    else:
        return "低"

def generate_ai_recommendations(ai_analysis):
    """生成AI建议"""
    recommendations = []
    
    if ai_analysis.complexity_score > 0.8:
        recommendations.append("系统复杂度较高，建议增加集成测试和端到端测试")
    
    if len(ai_analysis.security_risks) > 3:
        recommendations.append("检测到多个安全风险，建议进行专项安全测试")
    
    if len(ai_analysis.performance_concerns) > 2:
        recommendations.append("存在多个性能关注点，建议进行性能压力测试")
    
    if len(ai_analysis.integration_points) > 5:
        recommendations.append("集成点较多，建议重点关注接口测试和数据一致性")
    
    return recommendations

@app.route('/ai_config')
def ai_config():
    """AI配置页面"""
    return render_template('ai_config.html')

@app.route('/save_ai_config', methods=['POST'])
def save_ai_config():
    """保存AI配置"""
    try:
        ai_provider = AIProvider(request.form.get('ai_provider'))
        api_key = request.form.get('api_key', '').strip()
        base_url = request.form.get('base_url', '').strip() or None
        model = request.form.get('model', '').strip() or None
        max_tokens = int(request.form.get('max_tokens', 4000))
        temperature = float(request.form.get('temperature', 0.7))
        timeout = int(request.form.get('timeout', 30))

        if not api_key:
            flash('API密钥不能为空', 'error')
            return redirect(url_for('ai_config'))

        ai_config = AIConfig(
            provider=ai_provider,
            api_key=api_key,
            base_url=base_url,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout
        )

        if config_manager.save_config(ai_config):
            flash('AI配置保存成功！现在可以使用真实AI大模型生成测试用例', 'success')
        else:
            flash('AI配置保存失败', 'error')

    except Exception as e:
        flash(f'保存AI配置时发生错误: {str(e)}', 'error')

    return redirect(url_for('ai_config'))

@app.route('/test_ai_connection', methods=['POST'])
def test_ai_connection():
    """测试AI连接"""
    try:
        ai_provider = AIProvider(request.form.get('ai_provider'))
        api_key = request.form.get('api_key', '').strip()
        base_url = request.form.get('base_url', '').strip() or None
        model = request.form.get('model', '').strip() or None
        max_tokens = int(request.form.get('max_tokens', 4000))
        temperature = float(request.form.get('temperature', 0.7))
        timeout = int(request.form.get('timeout', 30))

        if not api_key:
            return jsonify({'success': False, 'error': 'API密钥不能为空'})

        ai_config = AIConfig(
            provider=ai_provider,
            api_key=api_key,
            base_url=base_url,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout
        )

        # 创建测试生成器
        test_generator = RealAITestCaseGenerator(ai_config)

        # 测试连接
        start_time = time.time()
        test_prompt = "请回复'AI连接测试成功'来确认连接正常。"
        response = test_generator.call_ai_api(test_prompt)
        response_time = int((time.time() - start_time) * 1000)

        return jsonify({
            'success': True,
            'response_time': response_time,
            'model': model or 'default',
            'response': response[:100] + '...' if len(response) > 100 else response
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_ai_status')
def get_ai_status():
    """获取AI状态"""
    status = config_manager.get_config_status()
    return jsonify(status)

@app.route('/delete_ai_config', methods=['POST'])
def delete_ai_config():
    """删除AI配置"""
    try:
        if config_manager.delete_config():
            return jsonify({'success': True, 'message': 'AI配置删除成功'})
        else:
            return jsonify({'success': False, 'error': '删除失败'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
