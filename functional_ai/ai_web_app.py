#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI增强功能测试用例生成器 - Web版本
结合人工智能和所有测试设计方法的Web应用
"""

from dotenv import load_dotenv

from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for, Response, session, g
import os
import json
import time
import pickle
import threading
import uuid
from datetime import datetime

from .paths import PROJECT_ROOT

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from .ai_test_generator import AITestMethod
from .comprehensive_test_generator import ComprehensiveTestGenerator
from .real_ai_generator import RealAITestCaseGenerator, AIProvider, AIConfig
from .test_case_generator import TestCaseGenerator
from .ai_config_manager_mysql import config_manager  # 使用MySQL版本
from .ai_model_presets import get_preset, AI_MODEL_PRESETS
from .mysql_db_manager import mysql_db  # 导入MySQL数据库管理器
from .generation_history import (
    append_job,
    list_jobs,
    load_request_snapshot,
    persist_request_snapshot,
    scan_active_jobs,
    update_job,
)
from .professional_test_generator import ProfessionalTestGenerator
from .translations import get_all_texts, get_text

app = Flask(
    __name__,
    template_folder=os.path.join(PROJECT_ROOT, "templates"),
    static_folder=os.path.join(PROJECT_ROOT, "static"),
    static_url_path="/static",
)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "ai_test_case_generator_secret_key_2025")

# 进度跟踪系统 - 使用线程锁保证并发安全
progress_tracker_lock = threading.Lock()
progress_tracker = {}  # {session_id: {progress, total, status, message, start_time}}
generation_results = {}  # {session_id: {test_cases, ai_analysis}} - 存储实际结果

# 生成进度落盘：避免 Flask debug 重载或进程重启导致「会话不存在」
GENERATION_STATE_DIR = os.path.join(PROJECT_ROOT, "data", "generation_state")


def _ensure_generation_state_dir():
    os.makedirs(GENERATION_STATE_DIR, exist_ok=True)


def persist_generation_progress_snapshot(generation_id: str, data: dict):
    _ensure_generation_state_dir()
    path = os.path.join(GENERATION_STATE_DIR, f"{generation_id}.progress.json")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, default=str)
    except Exception as ex:
        print(f"⚠️ 持久化生成进度失败: {ex}")


def update_generation_progress(generation_id: str, **kwargs):
    with progress_tracker_lock:
        if generation_id not in progress_tracker:
            return
        progress_tracker[generation_id].update(kwargs)
        snapshot = dict(progress_tracker[generation_id])
    persist_generation_progress_snapshot(generation_id, snapshot)


def load_generation_progress_from_disk(generation_id: str) -> bool:
    path = os.path.join(GENERATION_STATE_DIR, f"{generation_id}.progress.json")
    if not os.path.isfile(path):
        return False
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        st = data.get("start_time")
        if isinstance(st, str):
            try:
                data["start_time"] = float(st)
            except ValueError:
                data["start_time"] = time.time()
        with progress_tracker_lock:
            progress_tracker[generation_id] = data
        return True
    except Exception as ex:
        print(f"⚠️ 读取生成进度失败: {ex}")
        return False


def persist_generation_results_snapshot(generation_id: str):
    _ensure_generation_state_dir()
    path = os.path.join(GENERATION_STATE_DIR, f"{generation_id}.results.pkl")
    with progress_tracker_lock:
        if generation_id not in generation_results:
            return
        blob = generation_results[generation_id]
    try:
        with open(path, "wb") as f:
            pickle.dump(blob, f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as ex:
        print(f"⚠️ 持久化生成结果失败: {ex}")


def load_generation_results_from_disk(generation_id: str) -> bool:
    path = os.path.join(GENERATION_STATE_DIR, f"{generation_id}.results.pkl")
    if not os.path.isfile(path):
        return False
    try:
        with open(path, "rb") as f:
            data = pickle.load(f)
        with progress_tracker_lock:
            generation_results[generation_id] = data
        return True
    except Exception as ex:
        print(f"⚠️ 读取生成结果失败: {ex}")
        return False


def partial_cases_pickle_path(generation_id: str) -> str:
    return os.path.join(GENERATION_STATE_DIR, f"{generation_id}.partial_cases.pkl")


def persist_partial_test_cases(generation_id: str, cases) -> None:
    if not cases:
        return
    _ensure_generation_state_dir()
    path = partial_cases_pickle_path(generation_id)
    try:
        with open(path, "wb") as f:
            pickle.dump(cases, f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as ex:
        print(f"⚠️ 暂存部分用例失败: {ex}")


def clear_partial_test_cases(generation_id: str) -> None:
    path = partial_cases_pickle_path(generation_id)
    if os.path.isfile(path):
        try:
            os.remove(path)
        except OSError:
            pass


def try_export_partial_excel(generation_id: str, headers_dict) -> tuple:
    """若存在暂存用例，导出为 outputs 下 Excel。返回 (文件名, 条数)，失败为 (None, 0)。"""
    path = partial_cases_pickle_path(generation_id)
    if not os.path.isfile(path):
        return None, 0
    try:
        with open(path, "rb") as f:
            cases = pickle.load(f)
    except Exception as ex:
        print(f"⚠️ 读取暂存用例失败: {ex}")
        return None, 0
    if not cases:
        return None, 0
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_id = generation_id.replace("-", "")[:8]
    fn = f"ai_partial_{short_id}_{ts}.xlsx"
    outp = os.path.join(app.config["OUTPUT_FOLDER"], fn)
    try:
        gen = TestCaseGenerator(headers_dict)
        gen.test_cases = cases
        gen.export_to_excel(outp)
        return fn, len(cases)
    except Exception as ex:
        print(f"⚠️ 导出部分用例 Excel 失败: {ex}")
        return None, len(cases)


def collect_my_incomplete_jobs() -> list:
    """本会话最近提交的、尚未终态的生成任务（用于返回进度页）。"""
    gids = session.get("generation_jobs", [])
    out = []
    for gid in reversed(gids[-15:]):
        if gid not in progress_tracker:
            load_generation_progress_from_disk(gid)
        with progress_tracker_lock:
            data = progress_tracker.get(gid)
        if not data:
            continue
        st = data.get("status", "")
        if st in ("completed", "error"):
            continue
        out.append(
            {
                "generation_id": gid,
                "status": st,
                "message": (data.get("message") or "")[:120],
                "progress": data.get("progress", 0),
            }
        )
    return out


# Language support
SUPPORTED_LANGUAGES = ['zh', 'en']
DEFAULT_LANGUAGE = 'zh'

def get_locale():
    """Get user's preferred language"""
    # Check URL parameter
    lang = request.args.get('lang')
    if lang in SUPPORTED_LANGUAGES:
        session['language'] = lang
        return lang
    
    # Check session
    if 'language' in session:
        return session['language']
    
    # Check browser language
    accept_language = request.headers.get('Accept-Language', '')
    if accept_language:
        # Parse accept-language header
        for lang_code in accept_language.split(','):
            lang = lang_code.split(';')[0].strip()[:2].lower()
            if lang in SUPPORTED_LANGUAGES:
                session['language'] = lang
                return lang
    
    # Default language
    session['language'] = DEFAULT_LANGUAGE
    return DEFAULT_LANGUAGE

@app.before_request
def before_request():
    """Set language before each request"""
    g.lang = get_locale()
    if "client_id" not in session:
        session["client_id"] = str(uuid.uuid4())

@app.context_processor
def inject_translations():
    """Inject translations into all templates"""
    return {
        'texts': get_all_texts(g.lang),
        'lang': g.lang
    }

# 配置上传文件夹（相对仓库根目录，避免受启动工作目录影响）
UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, "uploads")
OUTPUT_FOLDER = os.path.join(PROJECT_ROOT, "outputs")
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
    """首页 - 显示最近生成的测试用例数据"""
    # 获取最近的测试用例数据
    recent_data = get_recent_test_cases()
    return render_template('ai_index.html', recent_data=recent_data)

@app.route('/ai_generate', methods=['GET', 'POST'])
def ai_generate():
    """�AI增强生成测试用例页面"""
    if request.method == 'GET':
        # 获取当前AI配置
        try:
            ai_config = config_manager.load_config()
        except Exception as e:
            print(f"⚠️ 加载AI配置失败: {e}")
            ai_config = None
        
        my_running = collect_my_incomplete_jobs()
        return render_template(
            'ai_generate.html',
            ai_config=ai_config,
            my_running_jobs=my_running,
            prefill_requirement="",
            prefill_custom_headers="",
            prefill_test_case_language="auto",
            prefill_source_id="",
            prefill_historical_defects="",
            prefill_iteration_context="",
            prefill_code_change_summary="",
        )
    
    try:
        # 生成唯一会话session ID
        generation_id = str(uuid.uuid4())
        
        # 初始化进度并落盘（避免热重载丢会话）
        _init_progress = {
            'progress': 0,
            'total': 100,
            'status': 'starting',
            'message': get_text('progress_initializing', g.lang),
            'start_time': time.time(),
            'current_step': '',
            'estimated_time': 0,
        }
        with progress_tracker_lock:
            progress_tracker[generation_id] = dict(_init_progress)
        persist_generation_progress_snapshot(generation_id, dict(_init_progress))

        client_id = session.get("client_id", "")
        
        # 获取表单数据
        requirement_text = request.form.get('requirement_text', '').strip()
        historical_defects = request.form.get('historical_defects', '').strip()
        iteration_context = request.form.get('iteration_context', '').strip()
        code_change_summary = request.form.get('code_change_summary', '').strip()
        custom_headers = request.form.get('custom_headers', '').strip()
        ai_enhancement_level = request.form.get('ai_enhancement_level', 'medium')
        test_case_language = request.form.get('test_case_language', 'auto')  # 获取语言选择
        
        # 处理自动语言选择
        if test_case_language == 'auto':
            # 根据session中的lang决定
            current_lang = session.get('language', 'zh')
            test_case_language = current_lang  # 'zh' or 'en'
        
        print(f"✅ 测试用例生成语言: {test_case_language}")
        
        if not requirement_text:
            flash(get_text('flash_requirement_required', g.lang), 'error')
            return redirect(url_for('ai_generate'))

        req_snap = {
            "requirement_text": requirement_text,
            "historical_defects": historical_defects,
            "iteration_context": iteration_context,
            "code_change_summary": code_change_summary,
            "custom_headers": custom_headers,
            "ai_enhancement_level": ai_enhancement_level,
            "test_case_language": test_case_language,
        }
        persist_request_snapshot(generation_id, req_snap)
        append_job(generation_id, client_id, requirement_text)
        gj = session.get("generation_jobs", [])
        session["generation_jobs"] = (gj + [generation_id])[-25:]
        session.modified = True
        
        # 在后台线程中生成
        def generate_in_background(language='zh'):
            headers_dict = None
            try:
                # 获取用户语言（从参数传入）
                from .translations import get_all_texts
                texts = get_all_texts(language)
                
                # 处理自定义字段标题
                if custom_headers:
                    try:
                        # 先尝试解析为JSON
                        headers_dict = json.loads(custom_headers)
                    except:
                        # 如果JSON解析失败，尝试按逗号分隔的字段列表解析
                        # 同时支持中文逗号（，）和英文逗号（,）
                        import re
                        # 先将中文逗号替换为英文逗号
                        normalized_headers = custom_headers.replace('，', ',')
                        fields = [f.strip() for f in normalized_headers.split(',') if f.strip()]
                        if fields:
                            headers_dict = fields  # 直接传递字段列表
                            print(f"✅ 自定义字段 ({len(fields)} 个): {fields[:3]}..." if len(fields) > 3 else f"✅ 自定义字段: {fields}")
                        else:
                            print("⚠️  无法解析自定义字段，将使用默认模板")
                
                # 更新进度: 分析需求
                update_generation_progress(
                    generation_id,
                    progress=10,
                    status='analyzing',
                    message=texts.get('analyzing_requirements', '正在分析需求文档...'),
                    current_step=texts.get('requirement_analysis', '需求分析'),
                )
                
                # 添加健康检查
                try:
                    print("🔍 执行AI服务健康检查...")
                    # 这里可以添加对AI服务的健康检查逻辑
                except Exception as health_err:
                    print(f"⚠️ 健康检查失败: {health_err}")
                
                from .strict_ai_generator import StrictAITestGenerator
                
                # 获取AI API调用器
                ai_api_caller = None
                ai_generator = None
                try:
                    ai_generator = create_ai_generator(headers_dict)
                    if hasattr(ai_generator, 'call_ai_api'):
                        ai_api_caller = ai_generator.call_ai_api
                except Exception as e:
                    print(f"⚠️  创建AI生成器失败: {e}")
                    import traceback
                    traceback.print_exc()
                
                # 更新进度: 即将进入严格生成（提取/梳理/逐点生成均在 generate_test_cases 内）
                update_generation_progress(
                    generation_id,
                    progress=22,
                    status='strict_pipeline',
                    message=texts.get('progress_strict_pipeline', '进入严格生成流程（提取功能点→梳理需求→逐条写用例）...'),
                    current_step=texts.get('function_point_extraction', '功能点提取'),
                )
                
                # 检查是否需要降级到本地生成
                if not ai_api_caller:
                    print("⚠️ AI API调用器不可用，将使用本地生成")
                
                # 使用严格AI生成器，传入语言参数与进度回调（与界面阶段一致）
                strict_generator = StrictAITestGenerator(ai_api_caller=ai_api_caller, language=test_case_language)
                
                generation_start_time = time.time()
                
                def strict_progress(event, payload=None):
                    payload = payload or {}
                    if event == "after_extract":
                        update_generation_progress(
                            generation_id,
                            progress=27,
                            status="extracted",
                            message=texts.get("progress_points_extracted", "已从需求中提取 {n} 个功能点").format(
                                n=payload.get("count", 0)),
                            current_step=texts.get("function_point_extraction", "功能点提取"),
                        )
                    elif event == "refine_start":
                        update_generation_progress(
                            generation_id,
                            progress=30,
                            status="refining_requirement",
                            message=texts.get("progress_refining_requirement", "正在梳理需求文档（整理上下文）..."),
                            current_step=texts.get("step_requirement_refine", "需求梳理"),
                        )
                    elif event == "refine_done":
                        update_generation_progress(
                            generation_id,
                            progress=36,
                            status="refining_done",
                            message=texts.get("progress_refine_done", "需求梳理完成（{n} 字），开始按功能点生成用例").format(
                                n=payload.get("length", 0)),
                            current_step=texts.get("test_case_generation", "测试用例生成"),
                        )
                    elif event == "mindmap_start":
                        update_generation_progress(
                            generation_id,
                            progress=37,
                            status="mindmap",
                            message=texts.get("progress_mindmap_start", "正在生成测试点思维导图（ISTQB 多维度）..."),
                            current_step=texts.get("step_test_mindmap", "测试点思维导图"),
                        )
                    elif event == "mindmap_done":
                        update_generation_progress(
                            generation_id,
                            progress=39,
                            status="mindmap_done",
                            message=texts.get("progress_mindmap_done", "思维导图完成（{n} 字），开始逐功能点生成用例").format(
                                n=payload.get("length", 0)),
                            current_step=texts.get("test_case_generation", "测试用例生成"),
                        )
                    elif event == "function_point_start":
                        tot = max(payload.get("total", 1), 1)
                        idx = payload.get("index", 1)
                        name = (payload.get("description") or "")[:80]
                        pct = 40 + int((idx - 1) / tot * 22)
                        update_generation_progress(
                            generation_id,
                            progress=min(pct, 61),
                            status="generating_function_point",
                            message=texts.get("progress_fp_item", "{i}/{t}：{name}").format(
                                i=idx, t=tot, name=name),
                            current_step=texts.get("test_case_generation", "测试用例生成"),
                        )
                    elif event == "function_point_done":
                        tot = max(payload.get("total", 1), 1)
                        idx = payload.get("index", 1)
                        update_generation_progress(
                            generation_id,
                            progress=min(40 + int(idx / tot * 22), 62),
                            message=texts.get("progress_fp_done_short", "已完成 {i}/{t}，本功能点 {c} 条用例").format(
                                i=idx, t=tot, c=payload.get("cases", 0)),
                        )
                    elif event == "validating_start":
                        update_generation_progress(
                            generation_id,
                            progress=63,
                            status="validating",
                            message=texts.get('validating_format', '验证格式规范... (已生成 {count} 个用例)').format(
                                count=payload.get("total_cases", 0)),
                            current_step=texts.get('format_validation', '格式验证'),
                            total=payload.get("total_cases", 0),
                        )
                
                def on_partial_cases(cases_list):
                    persist_partial_test_cases(generation_id, cases_list)
                    update_generation_progress(generation_id, total=len(cases_list))

                test_cases = strict_generator.generate_test_cases(
                    requirement_text,
                    progress_callback=strict_progress,
                    partial_results_callback=on_partial_cases,
                    historical_defects=historical_defects or None,
                    iteration_context=iteration_context or None,
                    code_change_summary=code_change_summary or None,
                )
                
                # 更新进度: 验证格式（导出前阶段）
                update_generation_progress(
                    generation_id,
                    progress=65,
                    status='validating',
                    message=texts.get('validating_format', '验证格式规范... (已生成 {count} 个用例)').format(count=len(test_cases)),
                    current_step=texts.get('format_validation', '格式验证'),
                    total=len(test_cases),
                )
                
                # 添加生成统计信息
                generation_duration = time.time() - generation_start_time
                print(f"⏱️  测试用例生成耗时: {generation_duration:.2f}秒")
                if generation_duration > 300:  # 超过5分钟
                    print("⚠️  生成时间较长，可能需要优化提示或检查AI服务性能")
                
                #创建普通生成器用于导出
                base_generator = TestCaseGenerator(headers_dict)
                base_generator.test_cases = test_cases
                
                # AI分析需求
                update_generation_progress(
                    generation_id,
                    progress=75,
                    message=texts.get('ai_analyzing', 'AI分析需求...'),
                    current_step=texts.get('ai_analysis', 'AI分析'),
                )
                
                ai_analysis = None
                try:
                    if ai_generator and hasattr(ai_generator, 'real_ai_analyze_requirements'):
                        ai_analysis = ai_generator.real_ai_analyze_requirements(requirement_text)
                    elif ai_generator and hasattr(ai_generator, 'ai_analyze_requirements'):
                        ai_analysis = ai_generator.ai_analyze_requirements(requirement_text)
                    else:
                        # 没有AI生成器，使用默认分析
                        raise Exception("未AI生成器可用")
                except Exception as e:
                    print(f"⚠️  AI分析失败: {e}，使用默认分析")
                    from .ai_test_generator import AIAnalysisResult
                    ai_analysis = AIAnalysisResult(
                        complexity_score=5.0,
                        risk_areas=[],
                        critical_paths=[],
                        data_patterns=[],
                        business_rules=[],
                        integration_points=[],
                        performance_concerns=[],
                        security_risks=[],
                        usability_factors=[]
                    )
                
                base_generator.ai_analysis = ai_analysis
                
                # 生成文件
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                excel_filename = f"ai_test_cases_{timestamp}.xlsx"
                excel_path = os.path.join(app.config['OUTPUT_FOLDER'], excel_filename)
                
                update_generation_progress(
                    generation_id,
                    progress=85,
                    message=texts.get('generating_excel', '生成Excel报告...'),
                    current_step=texts.get('excel_generation', 'Excel生成'),
                )
                
                base_generator.export_to_excel(excel_path)
                
                # AI增强报告
                ai_report_filename = f"ai_enhanced_report_{timestamp}.md"
                ai_report_path = os.path.join(app.config['OUTPUT_FOLDER'], ai_report_filename)
                
                update_generation_progress(
                    generation_id,
                    progress=95,
                    message=texts.get('generating_report', '生成AI增强报告...'),
                    current_step=texts.get('report_generation', '报告生成'),
                )
                
                try:
                    base_generator.export_ai_enhanced_report(ai_report_path)
                except:
                    ai_report_filename = None
                
                # 保存结果
                update_generation_progress(
                    generation_id,
                    progress=100,
                    status='completed',
                    message=texts.get('generation_complete', '完成！共生成 {count} 个测试用例').format(count=len(test_cases)),
                    current_step=texts.get('complete', '完成'),
                    excel_file=excel_filename,
                    ai_report_file=ai_report_filename,
                    generation_time=round(time.time() - generation_start_time, 2),
                    case_count=len(test_cases),
                )
                
                # 单独存储不能序列化的对象
                with progress_tracker_lock:
                    generation_results[generation_id] = {
                        'test_cases': test_cases,
                        'ai_analysis': ai_analysis,
                        'excel_file': excel_filename,
                        'ai_report_file': ai_report_filename,
                        'requirement_text': requirement_text,
                    }
                persist_generation_results_snapshot(generation_id)
                clear_partial_test_cases(generation_id)
                update_job(
                    generation_id,
                    status="completed",
                    case_count=len(test_cases),
                    excel_file=excel_filename,
                )
                
            except Exception as e:
                print(f"❌ 生成过程中出现错误: {e}")
                import traceback
                traceback.print_exc()
                try:
                    _tx = texts
                except NameError:
                    from .translations import get_all_texts as _gat
                    _tx = _gat(language)
                
                # 记录错误日志（勿在函数内再 import datetime，否则会令整个函数作用域把 datetime 视为未赋值的局部变量）
                try:
                    error_log = {
                        'timestamp': datetime.now().isoformat(),
                        'error': str(e),
                        'traceback': traceback.format_exc(),
                        'requirement_preview': requirement_text[:100] if requirement_text else 'N/A'
                    }
                    with open(os.path.join(PROJECT_ROOT, "generation_error.log"), "a", encoding="utf-8") as f:
                        f.write(json.dumps(error_log, ensure_ascii=False) + '\n')
                    print("📝 错误日志已记录到 generation_error.log")
                except Exception as log_err:
                    print(f"⚠️ 记录错误日志失败: {log_err}")
                
                # 提供更详细的错误信息
                error_message = str(e)
                detailed_message = _tx.get('error_occurred', '错误: {error}').format(error=error_message)
                
                # 根据错误类型提供不同的错误信息
                if 'JSON' in error_message or 'json' in error_message.lower():
                    detailed_message += ' ' + _tx.get('json_error_hint', '这通常是因为AI响应格式有问题，请稍后重试或联系管理员。')
                elif 'timeout' in error_message.lower() or 'time out' in error_message.lower():
                    detailed_message += ' ' + _tx.get('timeout_error_hint', '这可能是因为网络连接较慢，请稍后重试。')
                elif 'API' in error_message or 'api' in error_message.lower():
                    detailed_message += ' ' + _tx.get('api_error_hint', 'AI服务暂时不可用，请检查配置或稍后重试。')
                else:
                    detailed_message += ' ' + _tx.get('general_error_hint', '请稍后重试，如果问题持续存在请联系管理员。')
                
                pfile, pcount = try_export_partial_excel(generation_id, headers_dict)
                if pfile:
                    detailed_message += " " + _tx.get(
                        "partial_save_hint",
                        "已导出已生成的 {n} 条用例：{file}（可在下方下载）",
                    ).format(n=pcount, file=pfile)
                
                update_generation_progress(
                    generation_id,
                    progress=0,
                    status='error',
                    message=detailed_message,
                    current_step=_tx.get('error_status', '错误'),
                    error_details=error_message,
                    partial_excel_file=pfile or "",
                    partial_case_count=pcount,
                )
                update_job(generation_id, status="error", error_summary=error_message[:500])
        
        # 启动后台线程，传入当前语言
        current_lang = session.get('language', 'zh')
        thread = threading.Thread(target=generate_in_background, args=(current_lang,))
        thread.daemon = True
        thread.start()
        
        # 跳转到可收藏/可分享的进度 URL（关闭标签后也可从历史进入）
        return redirect(url_for('ai_generation_status_page', generation_id=generation_id))
        
    except Exception as e:
        flash(get_text('flash_ai_generate_error', g.lang).format(error=str(e)), 'error')
        return redirect(url_for('ai_generate'))

@app.route('/ai_generation_status/<generation_id>')
def ai_generation_status_page(generation_id):
    """再次打开某次生成的进度页（可分享链接；关闭标签后从历史进入）。"""
    return render_template('ai_progress.html', generation_id=generation_id)


@app.route('/ai_generation_history')
def ai_generation_history():
    mine_only = request.args.get("mine") == "1"
    cid = session.get("client_id") if mine_only else None
    history_jobs = list_jobs(client_id=cid, limit=300)
    active_jobs = scan_active_jobs(GENERATION_STATE_DIR)
    all_meta = list_jobs(client_id=None, limit=500)
    id_to_client = {e["generation_id"]: (e.get("client_id") or "")[:8] for e in all_meta}
    id_to_title = {e["generation_id"]: (e.get("title") or "")[:80] for e in all_meta}
    now_ts = time.time()
    for a in active_jobs:
        gid = a["generation_id"]
        a["client_short"] = id_to_client.get(gid, "")
        a["title"] = id_to_title.get(gid, "")
        stale_sec = 4 * 3600
        a["maybe_stale"] = (now_ts - a.get("mtime", now_ts)) > stale_sec
    return render_template(
        "ai_generation_history.html",
        history_jobs=history_jobs,
        active_jobs=active_jobs,
        mine_only=mine_only,
    )


@app.route('/ai_regenerate/<generation_id>')
def ai_regenerate(generation_id):
    snap = load_request_snapshot(generation_id)
    if not snap:
        flash(get_text("flash_regenerate_missing", g.lang), "warning")
        return redirect(url_for("ai_generation_history"))
    try:
        ai_config = config_manager.load_config()
    except Exception as e:
        print(f"⚠️ 加载AI配置失败: {e}")
        ai_config = None
    my_running = collect_my_incomplete_jobs()
    return render_template(
        "ai_generate.html",
        ai_config=ai_config,
        my_running_jobs=my_running,
        prefill_requirement=snap.get("requirement_text") or "",
        prefill_custom_headers=snap.get("custom_headers") or "",
        prefill_test_case_language=snap.get("test_case_language") or "auto",
        prefill_source_id=generation_id,
        prefill_historical_defects=snap.get("historical_defects") or "",
        prefill_iteration_context=snap.get("iteration_context") or "",
        prefill_code_change_summary=snap.get("code_change_summary") or "",
    )

@app.route('/ai_progress/<generation_id>')
def ai_progress_stream(generation_id):
    """进度流（Server-Sent Events）"""
    ui_lang = getattr(g, 'lang', 'zh')

    def generate():
        while True:
            if generation_id not in progress_tracker:
                load_generation_progress_from_disk(generation_id)
            if generation_id in progress_tracker:
                data = progress_tracker[generation_id]
                
                # 创建一个只包含可序列化字段的副本
                stream_data = {
                    'progress': data.get('progress', 0),
                    'total': data.get('total', 100),
                    'status': data.get('status', 'starting'),
                    'message': data.get('message', ''),
                    'current_step': data.get('current_step', ''),
                    'excel_file': data.get('excel_file', ''),
                    'ai_report_file': data.get('ai_report_file', ''),
                    'partial_excel_file': data.get('partial_excel_file', ''),
                    'partial_case_count': data.get('partial_case_count', 0),
                    'error_details': data.get('error_details', ''),
                }
                
                # 计算预计时间
                if stream_data['progress'] > 0:
                    elapsed = time.time() - data.get('start_time', time.time())
                    estimated_total = (elapsed / stream_data['progress']) * 100
                    estimated_remaining = max(0, estimated_total - elapsed)
                    stream_data['estimated_time'] = int(estimated_remaining)
                else:
                    stream_data['estimated_time'] = 0
                
                yield f"data: {json.dumps(stream_data, ensure_ascii=False)}\n\n"
                
                # 如果完成或错误，停止流
                if stream_data['status'] in ['completed', 'error']:
                    break
            else:
                # 如果找不到generation_id，返回错误
                error_data = {
                    'progress': 0,
                    'status': 'error',
                    'message': get_text('progress_no_session', ui_lang),
                    'current_step': get_text('progress_step_error', ui_lang)
                }
                yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                break
            
            time.sleep(0.5)  # 每0.5秒更新一次
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/ai_result/<generation_id>')
def ai_result(generation_id):
    """显示生成结果"""
    if generation_id not in progress_tracker:
        load_generation_progress_from_disk(generation_id)
    if generation_id not in progress_tracker:
        flash(get_text('flash_session_not_found', g.lang), 'error')
        return redirect(url_for('ai_generate'))
    
    progress_data = progress_tracker[generation_id]
    
    if progress_data['status'] != 'completed':
        flash(get_text('flash_generation_incomplete', g.lang), 'warning')
        return redirect(url_for('ai_generate'))
    
    # 从单独存储获取结果（进程重启后从磁盘恢复）
    if generation_id not in generation_results:
        load_generation_results_from_disk(generation_id)
    if generation_id not in generation_results:
        flash(get_text('flash_result_missing', g.lang), 'error')
        return redirect(url_for('ai_generate'))
    
    result_data = generation_results[generation_id]
    test_cases = result_data.get('test_cases', [])
    ai_analysis = result_data.get('ai_analysis')
    excel_file = result_data.get('excel_file')
    ai_report_file = result_data.get('ai_report_file')
    requirement_text = result_data.get('requirement_text', '')  # 获取需求文本
    
    # 获取生成统计信息
    generation_time = request.args.get('gen_time', 'N/A')
    case_count = request.args.get('case_count', len(test_cases))
    
    # 生成统计信息
    stats = generate_ai_statistics(test_cases, ai_analysis, g.lang)
    
    # 保存到历史记录
    files_dict = {'excel': excel_file}
    if ai_report_file:
        files_dict['report'] = ai_report_file
    
    save_test_case_session(
        requirement_text=requirement_text,  # 使用实际的需求文本
        total_cases=len(test_cases),
        test_type='AI Generate',
        files=files_dict,
        ui_lang=g.lang
    )
    
    # 清理进度数据
    del progress_tracker[generation_id]
    del generation_results[generation_id]
    
    return render_template('ai_result.html', 
                         test_cases=test_cases[:10],
                         ai_analysis=ai_analysis,
                         stats=stats,
                         excel_file=excel_file,
                         ai_report_file=ai_report_file,
                         total_cases=len(test_cases),
                         generation_time=generation_time,
                         case_count=case_count)

@app.route('/ai_analysis', methods=['POST'])
def ai_analysis():
    """AI需求分析接口"""
    try:
        data = request.get_json()
        requirement_text = data.get('requirement_text', '')
        
        if not requirement_text:
            return jsonify({'error': get_text('api_requirement_empty', g.lang)}), 400
        
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
            'complexity_level': get_complexity_level(ai_analysis.complexity_score, g.lang),
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
            'recommendations': generate_ai_recommendations(ai_analysis, g.lang)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload_image', methods=['POST'])
def upload_image():
    """上传图片接口"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': get_text('api_no_image_file', g.lang)}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'error': get_text('api_filename_empty', g.lang)}), 400
        
        # 验证文件类型
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_ext not in allowed_extensions:
            return jsonify({'error': get_text('api_unsupported_image', g.lang)}), 400
        
        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"img_{timestamp}_{file.filename}"
        
        # 保存图片
        upload_folder = os.path.join(app.config['OUTPUT_FOLDER'], 'images')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        # 返回图片信息
        return jsonify({
            'success': True,
            'filename': filename,
            'filepath': filepath,
            'url': f"/outputs/images/{filename}",
            'size': os.path.getsize(filepath)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ai_smart_template')
def ai_smart_template():
    """AI智能模板页面（使用MySQL）"""
    # 从MySQL加载模板
    try:
        templates = mysql_db.load_smart_templates()
    except Exception as e:
        print(f"加载智能模板失败: {e}")
        templates = {}
    
    return render_template('ai_smart_template.html', templates=templates)

@app.route('/ai_generate_from_smart_template', methods=['POST'])
def ai_generate_from_smart_template():
    """从AI智能模板生成测试用例（使用MySQL）"""
    try:
        template_name = request.form.get('template_name')
        ai_enhancement_options = request.form.getlist('ai_enhancement_options')
        custom_params = request.form.get('custom_params', '').strip()
        
        # 从MySQL加载模板
        templates = mysql_db.load_smart_templates()
        if template_name not in templates:
            flash(get_text('flash_template_not_found', g.lang), 'error')
            return redirect(url_for('ai_smart_template'))
        
        template = templates[template_name]
        requirement_text = template['content']
        
        # 增加模板使用次数
        try:
            mysql_db.increment_template_usage(template_name)
        except Exception as e:
            print(f"更新模板使用次数失败: {e}")
        
        # 应用自定义参数
        if custom_params:
            try:
                params = json.loads(custom_params)
                for key, value in params.items():
                    requirement_text = requirement_text.replace(f"{{{key}}}", str(value))
            except json.JSONDecodeError:
                flash(get_text('flash_custom_params_invalid', g.lang), 'error')
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
        
        flash(get_text('flash_template_success', g.lang).format(title=template["title"], count=len(test_cases)), 'success')
        
        stats = generate_ai_statistics(test_cases, ai_analysis, g.lang)
        
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
        flash(get_text('flash_template_error', g.lang).format(error=str(e)), 'error')
        return redirect(url_for('ai_smart_template'))

@app.route('/download/<filename>')
def download_file(filename):
    """下载文件"""
    try:
        if ".." in filename or filename.startswith(("/", "\\")):
            flash(get_text('flash_download_error', g.lang).format(error="invalid path"), 'error')
            return redirect(url_for('ai_generate'))
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)

        if os.path.exists(file_path):
            abs_file_path = os.path.abspath(file_path)
            if os.path.exists(abs_file_path):
                try:
                    return send_file(abs_file_path, as_attachment=True)
                except Exception:
                    try:
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
                        return response
                    except Exception:
                        pass

        # 查找类似文件
        output_dir = app.config['OUTPUT_FOLDER']
        if not os.path.exists(output_dir):
            flash(get_text('flash_output_dir_missing', g.lang), 'error')
            return redirect(url_for('index'))

        all_files = os.listdir(output_dir)

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

        # 查找最新的匹配文件
        if pattern and extension:
            matching_files = [f for f in all_files if f.startswith(pattern) and f.endswith(extension)]
            if matching_files:
                latest_file = max(matching_files, key=lambda f: os.path.getmtime(os.path.join(output_dir, f)))
                latest_path = os.path.join(output_dir, latest_file)
                if os.path.exists(latest_path):
                    return send_file(latest_path, as_attachment=True)
        flash(get_text('flash_file_not_found', g.lang).format(filename=filename), 'error')
        return redirect(url_for('ai_generate'))

    except Exception as e:
        flash(get_text('flash_download_error', g.lang).format(error=str(e)), 'error')
        return redirect(url_for('ai_generate'))

def generate_ai_statistics(test_cases, ai_analysis, ui_lang='zh'):
    """生成AI统计信息"""
    stats = {
        'total_cases': len(test_cases),
        'complexity_score': ai_analysis.complexity_score,
        'complexity_level': get_complexity_level(ai_analysis.complexity_score, ui_lang),
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

def get_complexity_level(score, ui_lang='zh'):
    """获取复杂度等级（随界面语言）"""
    if score > 0.7:
        return get_text('complexity_high', ui_lang)
    if score > 0.4:
        return get_text('complexity_medium', ui_lang)
    return get_text('complexity_low', ui_lang)

def generate_ai_recommendations(ai_analysis, ui_lang='zh'):
    """生成AI建议（随界面语言）"""
    recommendations = []

    if ai_analysis.complexity_score > 0.8:
        recommendations.append(get_text('reco_complexity', ui_lang))

    if len(ai_analysis.security_risks) > 3:
        recommendations.append(get_text('reco_security', ui_lang))

    if len(ai_analysis.performance_concerns) > 2:
        recommendations.append(get_text('reco_performance', ui_lang))

    if len(ai_analysis.integration_points) > 5:
        recommendations.append(get_text('reco_integration', ui_lang))

    return recommendations

def generate_professional_statistics(test_cases):
    """生成专业测试用例统计信息"""
    stats = {
        'total_cases': len(test_cases),
        'test_type_stats': {},
        'priority_stats': {},
        'module_stats': {},
        'quality_metrics': {}
    }

    # 测试类型统计
    for case in test_cases:
        test_type = case.test_type
        stats['test_type_stats'][test_type] = stats['test_type_stats'].get(test_type, 0) + 1

    # 优先级统计
    for case in test_cases:
        priority = case.priority
        stats['priority_stats'][priority] = stats['priority_stats'].get(priority, 0) + 1

    # 模块统计
    for case in test_cases:
        module = case.feature_module
        stats['module_stats'][module] = stats['module_stats'].get(module, 0) + 1

    # 质量指标
    cases_with_requirements = sum(1 for case in test_cases if case.related_requirement_id)
    cases_with_notes = sum(1 for case in test_cases if case.notes)
    avg_steps = sum(len(case.test_steps.split('\n')) for case in test_cases) / len(test_cases) if test_cases else 0

    stats['quality_metrics'] = {
        'requirement_coverage': cases_with_requirements / len(test_cases) * 100 if test_cases else 0,
        'documentation_rate': cases_with_notes / len(test_cases) * 100 if test_cases else 0,
        'avg_steps_per_case': round(avg_steps, 1)
    }

    return stats

@app.route('/professional_generate', methods=['GET', 'POST'])
def professional_generate():
    """专业测试用例生成页面"""
    if request.method == 'GET':
        return render_template('professional_generate.html')

    try:
        # 获取表单数据
        requirement_text = request.form.get('requirement_text', '').strip()

        if not requirement_text:
            flash(get_text('flash_requirement_required', g.lang), 'error')
            return redirect(url_for('professional_generate'))

        # 创建专业测试生成器
        ai_config = config_manager.load_config()
        professional_generator = ProfessionalTestGenerator(ai_config)

        # 生成专业测试用例
        print("🚀 开始专业测试用例生成...")
        test_cases = professional_generator.generate_professional_test_cases(requirement_text)

        # 生成文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Excel文件
        excel_filename = f"professional_test_cases_{timestamp}.xlsx"
        excel_path = os.path.join(app.config['OUTPUT_FOLDER'], excel_filename)
        professional_generator.export_to_excel(excel_path)

        # Markdown报告
        md_filename = f"professional_report_{timestamp}.md"
        md_path = os.path.join(app.config['OUTPUT_FOLDER'], md_filename)
        professional_generator.export_to_markdown(md_path)

        # 生成统计信息
        stats = generate_professional_statistics(test_cases)

        flash(get_text('flash_professional_success', g.lang).format(count=len(test_cases)), 'success')

        return render_template('professional_result.html',
                             test_cases=test_cases[:10],  # 只显示前10个
                             stats=stats,
                             total_cases=len(test_cases),
                             excel_file=excel_filename,
                             md_file=md_filename)

    except Exception as e:
        flash(get_text('flash_professional_error', g.lang).format(error=str(e)), 'error')
        return redirect(url_for('professional_generate'))

@app.route('/ai_config')
def ai_config():
    """AI配置页面"""
    cfg = config_manager.load_config()
    current_preset_id = ""
    if cfg:
        for p in AI_MODEL_PRESETS:
            if p.get("provider") == cfg.provider.value and p.get("model") == (cfg.model or ""):
                current_preset_id = p["id"]
                break
    return render_template(
        'ai_config.html',
        model_presets=AI_MODEL_PRESETS,
        current_preset_id=current_preset_id,
        saved_config=cfg,
    )

@app.route('/save_ai_config', methods=['POST'])
def save_ai_config():
    """保存AI配置"""
    try:
        api_key = request.form.get('api_key', '').strip()
        max_tokens = int(request.form.get('max_tokens', 8000))
        temperature = float(request.form.get('temperature', 0.7))
        timeout = int(request.form.get('timeout', 120))

        if not api_key:
            flash(get_text('flash_api_key_required', g.lang), 'error')
            return redirect(url_for('ai_config'))

        raw_preset = request.form.get('model_preset', '').strip()
        if raw_preset == '__custom__':
            preset = None
        else:
            preset = get_preset(raw_preset) if raw_preset else None
            if raw_preset and not preset:
                flash(get_text('flash_invalid_model_preset', g.lang), 'error')
                return redirect(url_for('ai_config'))

        if preset:
            ai_provider = AIProvider(preset['provider'])
            model = preset.get('model')
            bu = preset.get('base_url')
            base_url = (bu.strip() if isinstance(bu, str) and bu.strip() else None)
        else:
            ai_provider = AIProvider(request.form.get('ai_provider', 'openai'))
            base_url = request.form.get('base_url', '').strip() or None
            model = (
                request.form.get('model_name', '').strip()
                or request.form.get('model', '').strip()
                or None
            )
            if not model:
                flash(get_text('flash_model_required_custom', g.lang), 'error')
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

        storage = config_manager.save_config(ai_config)
        if storage == "mysql":
            flash(get_text('flash_config_saved', g.lang), 'success')
        elif storage == "json":
            flash(get_text('flash_config_saved_json_fallback', g.lang), 'warning')
        else:
            flash(get_text('flash_config_save_failed', g.lang), 'error')

    except Exception as e:
        flash(get_text('flash_config_error', g.lang).format(error=str(e)), 'error')

    return redirect(url_for('ai_config'))

@app.route('/test_ai_connection', methods=['POST'])
def test_ai_connection():
    """测试AI连接"""
    try:
        api_key = request.form.get('api_key', '').strip()
        max_tokens = int(request.form.get('max_tokens', 8000))
        temperature = float(request.form.get('temperature', 0.7))
        timeout = int(request.form.get('timeout', 120))

        if not api_key:
            return jsonify({'success': False, 'error': get_text('api_api_key_required', g.lang)})

        raw_preset = request.form.get('model_preset', '').strip()
        if raw_preset == '__custom__':
            preset = None
        else:
            preset = get_preset(raw_preset) if raw_preset else None
        if preset:
            ai_provider = AIProvider(preset['provider'])
            model = preset.get('model')
            bu = preset.get('base_url')
            base_url = (bu.strip() if isinstance(bu, str) and bu.strip() else None)
        else:
            ai_provider = AIProvider(request.form.get('ai_provider', 'openai'))
            base_url = request.form.get('base_url', '').strip() or None
            model = (
                request.form.get('model_name', '').strip()
                or request.form.get('model', '').strip()
                or None
            )
            if not model:
                return jsonify({'success': False, 'error': get_text('flash_model_required_custom', g.lang)})

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
        test_prompt = "Reply with OK if you can read this (connection test)."
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
            return jsonify({'success': True, 'message': get_text('json_config_deleted', g.lang)})
        else:
            return jsonify({'success': False, 'error': get_text('json_delete_failed', g.lang)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/change_language/<lang>')
def change_language(lang):
    """Change language"""
    if lang in SUPPORTED_LANGUAGES:
        session['language'] = lang
        # Redirect back to referrer or home page
        return redirect(request.referrer or url_for('index'))
    return redirect(url_for('index'))

def get_recent_test_cases(limit=10):
    """从MySQL获取最近生成的测试用例数据"""
    try:
        # 从MySQL获取最近会话
        recent_sessions = mysql_db.get_recent_sessions(limit=limit)
        
        # 获取统计数据
        stats = mysql_db.get_session_statistics()
        
        return {
            'total_generated': stats['total_generated'],
            'recent_sessions': recent_sessions,
            'total_sessions': stats['total_sessions'],
            'statistics': stats['statistics']
        }
    except Exception as e:
        print(f"读取历史数据失败: {e}")
        return {
            'total_generated': 0,
            'recent_sessions': [],
            'total_sessions': 0,
            'statistics': {
                'today': 0,
                'this_week': 0,
                'this_month': 0
            }
        }

def save_test_case_session(requirement_text, total_cases, test_type, files, ui_lang='zh'):
    """保存测试用例生成会话到MySQL"""
    try:
        # 生成唯一的session ID
        import uuid
        session_id = str(uuid.uuid4())
        
        # 创建简洁的需求预览
        def create_requirement_preview(text):
            """生成简洁的需求预览"""
            if not text:
                return get_text('preview_text_none', ui_lang)
            
            # 移除多余的空白和换行
            text = ' '.join(text.split())
            
            # 尝试提取关键信息（第一句或标题）
            import re
            # 查找第一个句号或换行符
            sentences = re.split(r'[\n。！？.!?]', text)
            if sentences and sentences[0].strip():
                first_sentence = sentences[0].strip()
                # 如果第一句太短，尝试包括第二句
                if len(first_sentence) < 20 and len(sentences) > 1:
                    sep = '，' if ui_lang == 'zh' else ', '
                    preview = (first_sentence + sep + sentences[1].strip())[:100]
                else:
                    preview = first_sentence[:100]
            else:
                preview = text[:100]
            
            # 如果截断了，添加省略号
            if len(text) > len(preview):
                preview += '...'
            
            return preview
        
        # 生成需求标题
        def create_requirement_title(text):
            """生成需求标题"""
            if not text:
                return get_text('title_unnamed', ui_lang)
            
            # 移除多余的空白和换行
            text = ' '.join(text.split())
            
            # 提取第一句作为标题，限制长度
            import re
            sentences = re.split(r'[\n。！？.!?]', text)
            if sentences and sentences[0].strip():
                title = sentences[0].strip()[:50]
            else:
                title = text[:50]
            
            # 如果截断了，添加省略号
            if len(text) > len(title):
                title += '...'
            
            return title
        
        # 保存到MySQL数据库
        success = mysql_db.save_test_case_session(
            session_id=session_id,
            requirement_title=create_requirement_title(requirement_text),
            requirement_preview=create_requirement_preview(requirement_text),
            requirement_full_text=requirement_text,
            total_cases=total_cases,
            test_type=test_type,
            files=files
        )
        
        if success:
            print(f"✅ 测试用例会话保存成功: {session_id}")
        else:
            print(f"❌ 测试用例会话保存失败: {session_id}")
            
        return session_id
        
    except Exception as e:
        print(f"保存测试用例会话时发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None

@app.route('/update_requirement_title', methods=['POST'])
def update_requirement_title():
    """更新需求标题（使用MySQL）"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        new_title = data.get('title', '').strip()
        
        if not session_id:
            return jsonify({'success': False, 'error': get_text('json_missing_session_id', g.lang)}), 400
        
        if not new_title:
            return jsonify({'success': False, 'error': get_text('json_title_empty', g.lang)}), 400
        
        # 更新MySQL中的标题
        success = mysql_db.update_session_title(session_id, new_title)
        
        if success:
            return jsonify({'success': True, 'message': get_text('json_title_updated', g.lang)})
        else:
            return jsonify({'success': False, 'error': get_text('json_record_not_found', g.lang)}), 404
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/migrate_history', methods=['POST'])
def migrate_history():
    """为旧的会话记录添加ID和标题"""
    try:
        history_file = os.path.join(PROJECT_ROOT, "data", "test_case_history.json")
        if not os.path.exists(history_file):
            return jsonify({'success': False, 'error': get_text('json_history_missing', g.lang)}), 404
        
        with open(history_file, 'r', encoding='utf-8') as f:
            history = json.load(f)
        
        import uuid
        import re
        migrated_count = 0
        
        for session in history.get('sessions', []):
            # 为没有ID的会话添加ID
            if 'id' not in session or not session.get('id'):
                session['id'] = str(uuid.uuid4())
                migrated_count += 1
            
            # 为没有标题的会话生成标题
            if 'requirement_title' not in session or not session.get('requirement_title'):
                preview = session.get('requirement_preview', '')
                none_txt = get_text('preview_text_none', g.lang)
                if preview and preview != none_txt:
                    # 提取第一句作为标题
                    text = ' '.join(preview.split())
                    sentences = re.split(r'[\n。！？.!?]', text)
                    if sentences and sentences[0].strip():
                        title = sentences[0].strip()[:50]
                    else:
                        title = text[:50]
                    if len(text) > len(title):
                        title += '...'
                    session['requirement_title'] = title
                else:
                    session['requirement_title'] = get_text('title_unnamed', g.lang)
        
        # 保存回文件
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True, 
            'message': get_text('json_migrate_done', g.lang).format(count=migrated_count),
            'migrated_count': migrated_count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
