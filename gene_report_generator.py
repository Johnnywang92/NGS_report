import json
import mysql.connector
import logging
import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# =====================
# 基因报告生成器类
# =====================

class GeneReportGenerator:
    """
    基因报告生成器，负责解析输入数据、生成HTML和PDF报告。
    """
    def __init__(self, template_dir='templates', db_config=None, base_path='static'): 
        """
        初始化生成器。
        参数：
            template_dir: 模板目录
            db_config: 数据库配置
            base_path: 基础路径
        """
        self.env = Environment(loader=FileSystemLoader(template_dir))
        self.db_config = db_config or {
            'host': 'localhost',
            'port': 3307,
            'user': 'gene_reports',
            'password': 'rooT@321',
            'database': 'gene_data',
        }
        self.base_path = base_path
        
    def parse_input_data(self, data_file):
        """
        解析输入JSON数据。
        参数：data_file 输入文件路径
        返回：解析后的数据dict
        异常：文件不存在或JSON格式错误返回None
        """
        try:
            with open(data_file) as f:
                data = json.load(f)
        except FileNotFoundError:
            logging.error(f"Input data file not found: {data_file}")
            return None
        except json.JSONDecodeError:
            logging.error(f"Error decoding JSON from file: {data_file}")
            return None
            
        # Get first patient_id (assuming one patient per file)
        patient_id = next(iter(data.keys()))
        patient_data = {
            'id': patient_id,
            'name': data[patient_id].get('name', ''),
            'gender': data[patient_id].get('gender', ''),
            'age': data[patient_id].get('age', ''),
            'logo_path': data[patient_id].get('logo_path', '')
        }
        
        # Process test results from different modules
        test_results = {}
        for module in ['snp', 'indel', 'sv', 'snv', 'fusion', 'tmb', 'drug']:
            if module in data[patient_id]:
                test_results[module] = []
                for result in data[patient_id][module]:
                    test_results[module].append({
                        'gene': result.get('gene', ''),
                        'status': result.get('status', ''),
                        'description': result.get('description', '')
                    })
        
        # Process charts if any
        charts = data[patient_id].get('charts', [])
        
        # Store raw data in MySQL (optional)
        try:
            if self._store_raw_data(patient_id, data):
                logging.info(f"Successfully stored raw data for patient {patient_id}")
            else:
                logging.warning(f"Failed to store raw data for patient {patient_id}, continuing without database storage")
        except Exception as e:
            logging.warning(f"Database storage skipped: {e}")
        
        return {
            'patient': patient_data,
            'results': test_results,
            'charts': charts,
            'logo_path': data[patient_id].get('logo_path', '')
        }
        
    def _store_raw_data(self, patient_id, raw_data):
        """Store raw JSON data in MySQL database"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Create table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS gene_data (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    patient_id VARCHAR(255) NOT NULL,
                    raw_data JSON NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Insert raw data
            cursor.execute(
                "INSERT INTO gene_data (patient_id, raw_data) VALUES (%s, %s)",
                (patient_id, json.dumps(raw_data))
            )
            
            conn.commit()
            cursor.close()
            conn.close()
        except mysql.connector.Error as err:
            logging.error(f"MySQL error: {err}")
            return False
        except Exception as e:
            logging.error(f"Error storing raw data: {e}")
            return False
        return True
    
    def generate_html_report(self, data, template_name='report_template.html'):
        """Generate HTML report from template"""
        template = self.env.get_template(template_name)
        return template.render(
            patient_data=data['patient'],
            test_results=data['results'],
            charts=data['charts'],
            date=datetime.now().strftime('%Y-%m-%d'),
            base_path=self.base_path
        )
    
    def generate_pdf_report(self, html_content, output_file):
        """
        将HTML内容转为PDF文件。
        参数：html_content HTML字符串
              output_file 输出PDF路径
        返回：True成功，False失败
        """
        import re
        from urllib.parse import urljoin
        def link_callback(uri, rel):
            # 只处理static目录下的资源
            static_dir = os.path.abspath('static')
            if uri.startswith('/static/'):
                path = os.path.join(static_dir, uri.replace('/static/', ''))
                if os.path.exists(path):
                    return path
            # 支持file://绝对路径
            if uri.startswith('file:///'):
                abs_path = uri.replace('file://', '')
                if os.path.exists(abs_path):
                    return abs_path
            # 兼容相对路径
            abs_path = os.path.abspath(uri)
            if os.path.exists(abs_path):
                return abs_path
            return uri
        try:
            with open(output_file, "w+b") as pdf_file:
                pisa_status = pisa.CreatePDF(
                    html_content,
                    dest=pdf_file,
                    link_callback=link_callback
                )
            if pisa_status.err:
                logging.error(f"Error converting to PDF: {pisa_status.err}")
            return not pisa_status.err
        except Exception as e:
            logging.error(f"An unexpected error occurred during PDF generation: {e}")
            return False
    
    def add_approval(self, report_file, reviewer, signature):
        """
        添加电子签章（预留）。
        """
        # Implementation for digital signature
        pass

    def run(self):
        """
        主流程：解析数据、生成HTML、生成PDF。
        """
        data = self.parse_input_data('input_data.json')
        html_report = self.generate_html_report(data)
        pdf_generated = self.generate_pdf_report(html_report, 'output_report.pdf')
        if pdf_generated:
            logging.info("PDF report generated successfully.")
        else:
            logging.error("Failed to generate PDF report.")

if __name__ == '__main__':
    # The base path should be an absolute path for resources to be found correctly
    base_path = os.path.abspath('report')
    generator = GeneReportGenerator(base_path=base_path)
    generator.run()