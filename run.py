import argparse
from datetime import datetime, timedelta
from stock_analyzer.main import StockAnalyzer
import io
import os
import subprocess
import logging
import time
import tempfile
import shutil
from pathlib import Path
import re

# 尝试导入reportlab库
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.units import inch
    reportlab_available = True
except ImportError:
    reportlab_available = False

# 尝试导入markdown库
try:
    import markdown
    markdown_available = True
except ImportError:
    markdown_available = False

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='股票量化分析工具')
    
    # 必需参数
    parser.add_argument('symbols', nargs='+', help='股票代码列表，例如：AAPL MSFT GOOG')
    
    # 可选参数
    parser.add_argument(
        '--days', 
        type=int, 
        default=365,
        help='分析历史数据的天数，默认365天'
    )
    
    parser.add_argument(
        '--output', 
        type=str,
        default='./reports',
        help='报告输出目录，默认为./reports'
    )
    
    parser.add_argument(
        '--format',
        choices=['excel', 'csv', 'json'],
        default='excel',
        help='报告输出格式，默认为excel'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='是否显示详细日志'
    )
    
    parser.add_argument(
        '--export-md',
        action='store_true',
        help='是否导出Markdown格式的报告'
    )
    
    parser.add_argument(
        '--export-log-md',
        action='store_true',
        default=True,  # 修改为默认为True，自动导出日志文件
        help='是否将分析日志导出为Markdown文件'
    )
    
    parser.add_argument(
        '--export-pdf',
        action='store_true',
        default=True,  # 默认为True，自动导出PDF文件
        help='是否将分析日志导出为PDF文件'
    )
    
    return parser.parse_args()

def validate_symbol(symbol):
    """验证股票代码格式"""
    if not symbol:
        return False
    # 统一转换为大写
    symbol = symbol.upper()
    if len(symbol) < 1 or len(symbol) > 6:
        return False
    return symbol  # 返回标准化的股票代码

class LogCapture:
    """捕获标准输出的类"""
    def __init__(self):
        self.log_buffer = io.StringIO()
        self.terminal = None
        self.log_content = ""
    
    def start(self):
        """开始捕获"""
        import sys
        self.terminal = sys.stdout
        sys.stdout = self
    
    def stop(self):
        """停止捕获"""
        import sys
        sys.stdout = self.terminal
        self.log_content = self.log_buffer.getvalue()
        return self.log_content
    
    def write(self, message):
        """写入消息到终端和缓冲区"""
        self.terminal.write(message)
        self.log_buffer.write(message)
    
    def flush(self):
        """刷新缓冲区"""
        self.terminal.flush()
        self.log_buffer.flush()

def analyze_stocks(args):
    """分析多个股票"""
    analyzer = StockAnalyzer()
    results = {}
    log_captures = {}
    
    for symbol in args.symbols:
        valid_symbol = validate_symbol(symbol)
        if not valid_symbol:
            print(f"无效的股票代码: {symbol}")
            continue
            
        try:
            if args.verbose:
                print(f"正在分析 {symbol}...")
            
            # 如果需要导出日志，开始捕获输出
            log_capture = None
            if args.export_log_md:
                log_capture = LogCapture()
                log_capture.start()
            
            # 分析股票
            report_path = analyzer.analyze_stock(valid_symbol, args.days, args.export_md)
            
            # 如果需要导出日志，停止捕获并保存
            if args.export_log_md and log_capture:
                log_content = log_capture.stop()
                log_captures[valid_symbol] = log_content
            
            if report_path:
                results[valid_symbol] = {
                    'status': 'success',
                    'report_path': report_path
                }
                if args.verbose:
                    print(f"成功生成 {valid_symbol} 的分析报告: {report_path}")
            else:
                results[valid_symbol] = {
                    'status': 'failed',
                    'error': '分析失败'
                }
                print(f"分析 {valid_symbol} 失败")
                
        except Exception as e:
            # 如果捕获了日志，需要停止捕获
            if args.export_log_md and 'log_capture' in locals() and log_capture:
                log_capture.stop()
                
            results[valid_symbol] = {
                'status': 'error',
                'error': str(e)
            }
            print(f"分析 {valid_symbol} 时发生错误: {str(e)}")
    
    # 导出日志为Markdown文件
    if args.export_log_md:
        for symbol, log_content in log_captures.items():
            md_file = export_log_to_markdown(symbol, log_content, args.output)
            
            # 如果需要导出PDF，将Markdown转换为PDF
            if args.export_pdf and md_file:
                convert_markdown_to_pdf(md_file)
    
    return results

def export_log_to_markdown(symbol, log_content, output_dir):
    """将日志导出为Markdown文件"""
    timestamp = datetime.now().strftime('%Y-%m-%d')
    filename = f"{output_dir}/{symbol}_analysis_log_{timestamp}.md"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"# {symbol} 股票分析日志 ({timestamp})\n\n")
        # 不使用代码块标记，直接写入内容
        f.write(log_content)
    
    print(f"成功导出 {symbol} 的分析日志: {filename}")
    return filename

def convert_markdown_to_pdf(markdown_file, pdf_file=None):
    """
    将Markdown文件转换为PDF文件，保留所有原始内容和格式，包括中文字符和段落格式
    
    Args:
        markdown_file: Markdown文件路径
        pdf_file: 输出PDF文件路径，如果为None则自动生成
    
    Returns:
        生成的PDF文件路径
    """
    if pdf_file is None:
        pdf_file = os.path.splitext(markdown_file)[0] + '.pdf'
    
    if not reportlab_available or not markdown_available:
        print("需要安装reportlab和markdown库才能转换PDF")
        print("请运行: pip install reportlab markdown")
        return None
    
    try:
        # 读取Markdown文件内容
        with open(markdown_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # 提取代码块内容（保留原始格式）
        code_blocks = []
        code_block_pattern = r'```(.*?)```'
        for i, match in enumerate(re.finditer(code_block_pattern, md_content, re.DOTALL)):
            code_blocks.append(match.group(1))
            # 替换为标记，以便后续处理
            md_content = md_content.replace(match.group(0), f"__CODE_BLOCK_{i}__")
        
        # 将Markdown转换为HTML
        html_content = markdown.markdown(md_content)
        
        # 提取纯文本内容（简单处理，实际应用可能需要更复杂的HTML解析）
        text_content = re.sub(r'<[^>]+>', '\n', html_content)
        
        # 恢复代码块
        for i, code_block in enumerate(code_blocks):
            text_content = text_content.replace(f"__CODE_BLOCK_{i}__", code_block)
        
        # 创建PDF文档
        doc = SimpleDocTemplate(
            pdf_file,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # 注册中文字体（使用系统字体）
        try:
            pdfmetrics.registerFont(TTFont('SimSun', '/System/Library/Fonts/PingFang.ttc'))
            chinese_font = 'SimSun'
        except:
            try:
                pdfmetrics.registerFont(TTFont('SimSun', '/System/Library/Fonts/STHeiti Light.ttc'))
                chinese_font = 'SimSun'
            except:
                chinese_font = 'Helvetica'  # 如果找不到中文字体，使用默认字体
                print("警告：未找到中文字体，PDF中的中文可能无法正确显示")
        
        # 创建样式
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            name='Chinese',
            fontName=chinese_font,
            fontSize=12,
            leading=14,
            firstLineIndent=0  # 移除首行缩进
        ))
        
        styles.add(ParagraphStyle(
            name='ChineseHeading',
            fontName=chinese_font,
            fontSize=16,
            leading=20,
            spaceAfter=12,
            spaceBefore=12,
            alignment=0  # 左对齐
        ))
        
        styles.add(ParagraphStyle(
            name='CodeBlock',
            fontName='Courier',
            fontSize=10,
            leading=12,
            leftIndent=20,
            rightIndent=20,
            spaceAfter=12,
            spaceBefore=12,
            backColor='#f5f5f5'
        ))
        
        # 处理内容
        story = []
        
        # 分割文本为行，保留原始格式
        lines = text_content.split('\n')
        
        # 处理标题和内容
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # 处理标题
            if line.startswith('#'):
                heading_level = len(re.match(r'^#+', line).group())
                heading_text = line[heading_level:].strip()
                
                if heading_level == 1:
                    story.append(Paragraph(heading_text, styles['Title']))
                elif heading_level == 2:
                    story.append(Paragraph(heading_text, styles['ChineseHeading']))
                else:
                    story.append(Paragraph(heading_text, styles['Heading3']))
                
                story.append(Spacer(1, 0.2 * inch))
                i += 1
                continue
            
            # 检查是否在代码块内
            if i < len(lines) - 1 and lines[i+1].strip() == '```':
                # 找到代码块的结束位置
                start_idx = i + 2
                end_idx = start_idx
                while end_idx < len(lines) and lines[end_idx].strip() != '```':
                    end_idx += 1
                
                # 提取代码块内容
                code_content = '\n'.join(lines[start_idx:end_idx])
                story.append(Paragraph(code_content, styles['CodeBlock']))
                
                i = end_idx + 1 if end_idx < len(lines) else len(lines)
                continue
            
            # 处理普通段落，保留原始格式
            # 收集连续的非空行作为一个段落
            paragraph_lines = []
            while i < len(lines) and lines[i].strip():
                paragraph_lines.append(lines[i])
                i += 1
            
            if paragraph_lines:
                # 保留原始格式，不合并行
                for para_line in paragraph_lines:
                    if para_line.strip():  # 跳过空行
                        # 使用XML转义字符，确保特殊字符正确显示
                        para_line = para_line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                        story.append(Paragraph(para_line, styles['Chinese']))
            
            # 跳过连续的空行
            while i < len(lines) and not lines[i].strip():
                i += 1
                
            # 在段落之间添加间距
            if paragraph_lines:
                story.append(Spacer(1, 0.1 * inch))
        
        # 生成PDF
        doc.build(story)
        
        print(f"成功将 {markdown_file} 转换为 {pdf_file}")
        return pdf_file
    
    except Exception as e:
        print(f"转换PDF时发生错误: {str(e)}")
        return None

def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()
    
    # 创建输出目录
    os.makedirs(args.output, exist_ok=True)
    
    # 设置详细日志
    if args.verbose:
        print("开始分析...")
        print(f"分析周期: {args.days}天")
        print(f"输出目录: {args.output}")
        print(f"输出格式: {args.format}")
        
    # 分析股票
    start_time = datetime.now()
    results = analyze_stocks(args)
    end_time = datetime.now()
    
    # 输出汇总信息
    success_count = sum(1 for r in results.values() if r['status'] == 'success')
    total_count = len(results)
    
    print("\n分析完成!")
    print(f"总用时: {end_time - start_time}")
    print(f"成功: {success_count}/{total_count}")
    
    # 如果有失败的情况，显示详细信息
    failed = {s: r for s, r in results.items() if r['status'] != 'success'}
    if failed:
        print("\n失败详情:")
        for symbol, result in failed.items():
            print(f"{symbol}: {result.get('error', '未知错误')}")

if __name__ == "__main__":
    main() 