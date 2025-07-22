-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(64) NOT NULL UNIQUE,
    password VARCHAR(128) NOT NULL
);

-- 创建样本表
CREATE TABLE IF NOT EXISTS samples (
    id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(64),
    status ENUM('pending', 'finished') NOT NULL
);

-- 插入默认用户
INSERT INTO users (username, password) VALUES ('admin', 'admin123')
    ON DUPLICATE KEY UPDATE password=VALUES(password);

-- 插入样本数据
INSERT INTO samples (id, name, status) VALUES
    ('S001', '张三', 'pending'),
    ('S002', '李四', 'pending'),
    ('S003', '王五', 'finished')
    ON DUPLICATE KEY UPDATE name=VALUES(name), status=VALUES(status); 