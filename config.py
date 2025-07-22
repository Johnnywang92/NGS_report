import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-secret-key'
    DEBUG = os.environ.get('DEBUG', 'True').lower() in ['true', '1', 't']
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5001))
    
    # 数据库配置
    DB_CONFIG = {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'port': os.environ.get('DB_PORT', 3307),
        'user': os.environ.get('DB_USER', 'gene_reports'),
        'password': os.environ.get('DB_PASSWORD', 'rooT@321'),
        'database': os.environ.get('DB_NAME', 'gene_data'),
        'pool_size': 5,
        'pool_name': 'mypool'
    }
    
    # 静态资源配置
    STATIC_COMPRESSION = True
    STATIC_CACHE_AGE = 3600