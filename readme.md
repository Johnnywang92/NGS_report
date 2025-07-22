# 基因检测报告自动生成系统

本项目是一个基于 Flask 的基因检测报告自动生成与管理平台，支持前端可视化、报告模板渲染、PDF 导出等功能，适用于医学检验、科研等场景。

## 主要功能

- 解析输入的基因检测数据（JSON 格式）
- 自动渲染美观的 HTML 报告（支持中文字体）
- 支持图表、Logo、患者信息等多种内容展示
- 一键导出 PDF 报告
- 前后端分离，接口友好

## 技术栈

- Python 3
- Flask
- Jinja2 模板
- HTML/CSS
- JavaScript（前端交互）
- [思源黑体](https://github.com/adobe-fonts/source-han-sans/releases) 字体支持

## 快速开始

1. **克隆项目**
   ```bash
   git clone <your-repo-url>
   cd <your-project-folder>
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **准备字体**
   - 下载 [思源黑体](https://github.com/adobe-fonts/source-han-sans/releases) OTF 文件，放入 `report/09_SourceHanSansSC/` 目录下。

4. **准备输入数据**
   - 将你的基因检测数据保存为 `input_data.json`，格式参考示例。

5. **运行服务**
   ```bash
   python app.py
   ```
   - 默认监听 `http://127.0.0.1:5000/`

6. **访问报告页面**
   - 浏览器打开 `http://127.0.0.1:5000/` 查看自动生成的报告。

## 目录结构


mysql -u gene_reports -p -h 127.0.0.1 -P 3307 gene_data < init_db.sql


font:
    https://github.com/adobe-fonts/source-han-sans/releases


python import_samples.py