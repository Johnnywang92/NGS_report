from flask import Flask, Blueprint, render_template, request, jsonify, url_for, redirect, session, send_from_directory
from flask_cors import CORS
from gene_report_generator import GeneReportGenerator
from config import Config
import os
import time
import json
import mysql.connector
import subprocess
import re
from weasyprint import HTML

app = Flask(__name__, static_folder='static', template_folder='templates')

# 创建蓝图
# 创建独立蓝图
report_bp = Blueprint('report', __name__, template_folder='templates', static_folder='static')
pdf_bp = Blueprint('pdf', __name__)

# =====================
# Flask主应用与蓝图注册
# =====================

# 所有路由和视图函数定义必须在蓝图注册之前
# 在Flask应用初始化处添加
from flask_compress import Compress
Compress(app)

@report_bp.route('/')
def index():
    """
    首页路由，渲染主报告页面。
    解析input_data.json，渲染report_template.html。
    返回：HTML页面
    异常：渲染失败时返回错误页面
    """
    try:
        generator = GeneReportGenerator(base_path=os.path.abspath('report'))
        data = generator.parse_input_data('input_data.json')
        if data is None:
            return render_template('error.html', error_message="Failed to parse input data."), 500

        charts = [{'path': f'/static/{os.path.basename(chart["path"])}', 'title': chart['title']} for chart in data['charts']]
        logo_path = f'/static/{os.path.basename(data["logo_path"])}' if data.get('logo_path') else None
        return render_template('report_template.html', 
                               patient_data=data['patient'], 
                               test_results=data['results'], 
                               charts=charts,
                               logo_path=logo_path,
                               base_path='/static')
    except Exception as e:
        return render_template('error.html', error_message=f"An unexpected error occurred: {e}"), 500

@pdf_bp.route('/save_report', methods=['POST'])
def save_report():
    """
    保存报告API。
    接收前端JSON，写入input_data.json。
    返回：{'status': 'success'} 或 {'status': 'error', 'error': ...}
    """
    try:
        report_data = request.json
        if not report_data:
            return jsonify({'status': 'error', 'error': 'No data provided'}), 400
        # 兼容前端结构，转换为后端期望格式
        if isinstance(report_data, dict) and 'patient_data' in report_data and 'test_results' in report_data:
            patient_id = report_data['patient_data'].get('id', 'unknown')
            data = {
                patient_id: {
                    'name': report_data['patient_data'].get('name', ''),
                    'gender': report_data['patient_data'].get('gender', ''),
                    'age': report_data['patient_data'].get('age', ''),
                    'logo_path': report_data.get('logo_path', ''),
                    **report_data.get('test_results', {}),
                    'charts': report_data.get('charts', []),
                    'approval': report_data.get('approval', {}),
                    'report_date': report_data.get('report_date', ''),
                    'project_type': report_data.get('project_type', ''),
                    'qc': report_data.get('qc', {})
                }
            }
        else:
            data = report_data
        with open('input_data.json', 'w') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500

@pdf_bp.route('/generate_pdf', methods=['POST'])
def generate_pdf():
    """
    生成PDF报告API（所见即所得，使用WeasyPrint）。
    接收HTML内容，生成PDF文件，返回下载URL。
    返回：{'message': 'PDF generated successfully', 'download_url': ...} 或 {'error': ...}
    """
    try:
        if not request.json:
            return jsonify({'error': 'No JSON body provided'}), 400
        html_content = request.json.get('html_content')
        if not html_content:
            return jsonify({'error': 'No HTML content provided'}), 400
        timestamp = int(time.time())
        filename = f'report_{timestamp}.pdf'
        output_path = os.path.join('static', filename)
        # 用WeasyPrint生成PDF
        HTML(string=html_content, base_url=request.host_url).write_pdf(output_path)
        download_url = url_for('static', filename=filename)
        return jsonify({'message': 'PDF generated successfully', 'download_url': download_url})
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {e}'}), 500

def get_db_conn():
    return mysql.connector.connect(
        host='localhost',
        port=3307,
        user='gene_reports',
        password='rooT@321',
        database='gene_data'
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    用户登录路由。
    GET渲染登录页，POST校验用户名密码。
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        conn = get_db_conn()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user:
            session['user'] = username
            return redirect('/main')
        else:
            return render_template('login.html', error='用户名或密码错误')
    return render_template('login.html')

@app.route('/logout')
def logout():
    """
    用户登出路由。
    清除session，重定向到登录页。
    """
    session.pop('user', None)
    return redirect('/login')

@app.route('/main')
def main():
    """
    样本管理主页面。
    展示待出报告、已出报告、全部样本。
    """
    if 'user' not in session:
        return redirect('/login')
    conn = get_db_conn()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM samples WHERE status='pending'")
    pending_samples = cursor.fetchall()
    cursor.execute("SELECT * FROM samples WHERE status='finished'")
    finished_samples = cursor.fetchall()
    cursor.execute("SELECT * FROM samples")
    all_samples = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('main.html', pending_samples=pending_samples, finished_samples=finished_samples, all_samples=all_samples)

@app.route('/')
def root():
    """
    根路由，根据登录状态跳转到主页面或登录页。
    """
    if 'user' in session:
        return redirect('/main')
    else:
        return redirect('/login')

@app.route('/import_samples_once')
def import_samples_once():
    """
    单次导入样本数据。
    """
    if 'user' not in session:
        return redirect('/login')
    try:
        result = subprocess.run(['python3', 'import_samples_once.py'], timeout=60, capture_output=True, text=True)
        return f'<pre>{result.stdout or "导入完成"}</pre>'
    except Exception as e:
        return f'导入失败: {e}'

@app.route('/upload_json', methods=['POST'])
def upload_json():
    """
    上传JSON文件并自动导入。
    """
    if 'user' not in session:
        return '未登录，无法上传', 401
    if 'json_file' not in request.files:
        return '未选择文件', 400
    file = request.files['json_file']
    filename = file.filename
    # 文件名校验：只允许字母数字下划线和.json结尾
    if not filename or not re.match(r'^[\w-]+\.json$', filename):
        return '文件名不合法，只允许字母、数字、下划线、短横线和.json结尾', 400
    if not filename.endswith('.json'):
        return '只允许上传JSON文件', 400
    save_dir = os.path.join(os.getcwd(), 'data')
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, filename)
    try:
        file.save(save_path)
    except Exception as e:
        return f'文件保存失败: {e}', 500
    # 上传后自动导入
    try:
        result = subprocess.run(['python3', 'import_samples_once.py'], timeout=60, capture_output=True, text=True)
        import_result = result.stdout or '导入完成'
    except Exception as e:
        import_result = f'导入失败: {e}'
    return f'上传成功\n{import_result}'

@report_bp.route('/report/<sample_id>')
def report_sample(sample_id):
    """
    动态报告页面。
    只允许以S开头的样本ID，渲染对应样本的报告。
    """
    # 只允许以S开头的样本ID，避免与PDF等静态文件冲突
    if not re.match(r'^S\d{3,}$', sample_id):  # 要求至少3位数字
        logging.warning(f'非法样本ID访问尝试: {sample_id}')
        return render_template('error.html', error_message="样本ID格式错误，必须为S开头+至少3位数字"), 400
    try:
        import os, json
        data_path = os.path.join('data', 'processed', f'{sample_id}.json')
        if not os.path.exists(data_path):
            return render_template('error.html', error_message=f"样本 {sample_id} 的报告数据未找到。"), 404
        with open(data_path, encoding='utf-8') as f:
            data = json.load(f)
        patient_id = next(iter(data.keys()))
        patient_data = {
            'id': patient_id,
            'name': data[patient_id].get('name', ''),
            'gender': data[patient_id].get('gender', ''),
            'age': data[patient_id].get('age', ''),
            'logo_path': f"/static/{os.path.basename(data[patient_id].get('logo_path', 'gene_analysis.png'))}" if data[patient_id].get('logo_path') else '/static/gene_analysis.png'
        }
        test_results = {k: v for k, v in data[patient_id].items() if k not in ['name', 'gender', 'age', 'logo_path', 'charts', 'approval', 'report_date', 'project_type', 'qc']}
        charts = []
        for chart in data[patient_id].get('charts', []):
            path = chart.get('path', '')
            if not path.startswith('/static/'):
                path = f"/static/{os.path.basename(path)}"
            charts.append({'path': path, 'title': chart.get('title', '')})
        logo_path = patient_data['logo_path']
        approval = data[patient_id].get('approval', {})
        report_date = data[patient_id].get('report_date', '')
        project_root = os.path.abspath(os.path.dirname(__file__))
        static_dir = os.path.abspath('static')
        font_path = os.path.join(static_dir, '09_SourceHanSansSC', 'SourceHanSansSC-Regular.otf')
        # 判断是否为PDF导出（通过query参数pdf=1）
        is_pdf = request.args.get('pdf') == '1'
        if is_pdf:
            logo_path = f"file://{os.path.join(static_dir, os.path.basename(logo_path))}"
        return render_template('report_template.html',
            patient_data=patient_data,
            test_results=test_results,
            charts=charts,
            logo_path=logo_path,
            font_path=font_path,
            approval=approval,
            report_date=report_date,
            project_root=project_root,
            base_path='/static')
    except Exception as e:
        return render_template('error.html', error_message=f"加载报告时发生错误: {e}"), 500

# 注册蓝图必须在所有路由定义之后
app.register_blueprint(report_bp, url_prefix='/')
app.register_blueprint(pdf_bp, url_prefix='/api')
app.config.from_object(Config)
app.secret_key = 'a-very-secret-key'
CORS(app)

if __name__ == '__main__':
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )