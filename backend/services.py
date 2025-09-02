# services.py

import requests
import json
import re
from config import LLM_API_URL, LLM_API_KEY, SYSTEM_PROMPT, ENABLE_KNOWLEDGE_BASE
from knowledge_base import get_knowledge_base
import logging

def beautify_table_for_text(table_text):
    """
    为纯文本格式美化表格
    """
    lines = table_text.strip().split('\n')
    if len(lines) < 2:
        return table_text
    
    # 检测表格分隔符
    separators = ['|', '\t', '  ', '，', '、']
    best_separator = None
    max_columns = 0
    
    for sep in separators:
        test_columns = len(lines[0].split(sep))
        if test_columns > max_columns and test_columns > 1:
            max_columns = test_columns
            best_separator = sep
    
    if not best_separator or max_columns < 2:
        return table_text
    
    # 解析表格数据
    table_data = []
    for line in lines:
        if line.strip():
            cells = [cell.strip() for cell in line.split(best_separator)]
            # 确保每行都有相同数量的列
            while len(cells) < max_columns:
                cells.append('')
            table_data.append(cells[:max_columns])
    
    if len(table_data) < 2:
        return table_text
    
    # 计算每列的最大宽度
    col_widths = [0] * max_columns
    for row in table_data:
        for i, cell in enumerate(row):
            # 计算中文字符宽度（中文字符占2个位置）
            width = sum(2 if ord(char) > 127 else 1 for char in cell)
            col_widths[i] = max(col_widths[i], width)
    
    # 设置最小列宽
    col_widths = [max(width, 4) for width in col_widths]
    
    # 生成美化的表格（纯文本风格）
    result = []
    
    # 生成分隔线
    def make_separator():
        parts = []
        for width in col_widths:
            parts.append('─' * (width + 2))
        return '┌' + '┬'.join(parts) + '┐' if not result else '├' + '┼'.join(parts) + '┤'
    
    # 格式化行
    def format_row(row, is_header=False):
        parts = []
        for i, cell in enumerate(row):
            # 计算需要的填充
            cell_width = sum(2 if ord(char) > 127 else 1 for char in cell)
            padding = col_widths[i] - cell_width
            if is_header:
                parts.append(f' 【{cell}】{" " * (padding-2)} ' if padding >= 2 else f' 【{cell}】 ')
            else:
                parts.append(f' {cell}{" " * padding} ')
        return '│' + '│'.join(parts) + '│'
    
    # 添加顶部分隔线
    result.append(make_separator())
    
    # 添加表头
    if table_data:
        result.append(format_row(table_data[0], is_header=True))
        # 添加表头分隔线
        parts = []
        for width in col_widths:
            parts.append('─' * (width + 2))
        result.append('├' + '┼'.join(parts) + '┤')
        
        # 添加数据行
        for row in table_data[1:]:
            result.append(format_row(row))
    
    # 添加底部分隔线
    parts = []
    for width in col_widths:
        parts.append('─' * (width + 2))
    result.append('└' + '┴'.join(parts) + '┘')
    
    return '\n'.join(result)

def detect_and_beautify_tables_for_text(content):
    """
    检测并美化文本中的表格（纯文本格式）
    """
    lines = content.split('\n')
    result_lines = []
    current_table = []
    in_table = False
    
    for line in lines:
        # 检测是否是表格行（包含多个分隔符）
        separators_count = sum(1 for sep in ['|', '\t'] if sep in line)
        has_multiple_items = len([item for item in re.split(r'[|\t，、]', line) if item.strip()]) > 2
        
        if (separators_count > 0 or has_multiple_items) and line.strip():
            if not in_table:
                in_table = True
            current_table.append(line)
        else:
            if in_table and current_table:
                # 处理当前表格
                table_text = '\n'.join(current_table)
                beautified_table = beautify_table_for_text(table_text)
                result_lines.append(beautified_table)
                current_table = []
                in_table = False
            
            result_lines.append(line)
    
    # 处理最后一个表格
    if in_table and current_table:
        table_text = '\n'.join(current_table)
        beautified_table = beautify_table_for_text(table_text)
        result_lines.append(beautified_table)
    
    return '\n'.join(result_lines)

def markdown_to_text(markdown_content):
    """
    将markdown文本转换为美化的纯文本，包含表格美化
    """
    # 首先检测并美化表格
    text = detect_and_beautify_tables_for_text(markdown_content)
    
    # 处理标题 - 转换为带前缀的文本
    text = re.sub(r'^#{6}\s+(.+)$', r'      • \1', text, flags=re.MULTILINE)
    text = re.sub(r'^#{5}\s+(.+)$', r'    ▪ \1', text, flags=re.MULTILINE)
    text = re.sub(r'^#{4}\s+(.+)$', r'  ◦ \1', text, flags=re.MULTILINE)
    text = re.sub(r'^#{3}\s+(.+)$', r'▶ \1', text, flags=re.MULTILINE)
    text = re.sub(r'^#{2}\s+(.+)$', r'■ \1', text, flags=re.MULTILINE)
    text = re.sub(r'^#{1}\s+(.+)$', r'【\1】', text, flags=re.MULTILINE)
    
    # 处理加粗文本
    text = re.sub(r'\*\*(.+?)\*\*', r'【\1】', text)
    text = re.sub(r'__(.+?)__', r'【\1】', text)
    
    # 处理斜体
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    
    # 处理代码块
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`(.+?)`', r'\1', text)
    
    # 处理链接
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # 处理列表 - 保持缩进结构
    text = re.sub(r'^\s*[-*+]\s+', '• ', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*(\d+)\.\s+', r'\1. ', text, flags=re.MULTILINE)
    
    # 处理分割线
    text = re.sub(r'^\s*[-*_]{3,}\s*$', '────────────────────', text, flags=re.MULTILINE)
    
    # 清理多余的空行，但保留段落结构
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # 清理首尾空白
    text = text.strip()
    
    return text

def beautify_table(table_text):
    """
    美化表格文本，将混乱的表格重新格式化
    """
    lines = table_text.strip().split('\n')
    if len(lines) < 2:
        return table_text
    
    # 检测表格分隔符
    separators = ['|', '\t', '  ', '，', '、']
    best_separator = None
    max_columns = 0
    
    for sep in separators:
        test_columns = len(lines[0].split(sep))
        if test_columns > max_columns and test_columns > 1:
            max_columns = test_columns
            best_separator = sep
    
    if not best_separator or max_columns < 2:
        return table_text
    
    # 解析表格数据
    table_data = []
    for line in lines:
        if line.strip():
            cells = [cell.strip() for cell in line.split(best_separator)]
            # 确保每行都有相同数量的列
            while len(cells) < max_columns:
                cells.append('')
            table_data.append(cells[:max_columns])
    
    if len(table_data) < 2:
        return table_text
    
    # 计算每列的最大宽度
    col_widths = [0] * max_columns
    for row in table_data:
        for i, cell in enumerate(row):
            # 计算中文字符宽度（中文字符占2个位置）
            width = sum(2 if ord(char) > 127 else 1 for char in cell)
            col_widths[i] = max(col_widths[i], width)
    
    # 设置最小列宽
    col_widths = [max(width, 4) for width in col_widths]
    
    # 生成美化的表格
    result = []
    
    # 生成分隔线
    def make_separator():
        parts = []
        for width in col_widths:
            parts.append('-' * (width + 2))
        return '+' + '+'.join(parts) + '+'
    
    # 格式化行
    def format_row(row):
        parts = []
        for i, cell in enumerate(row):
            # 计算需要的填充
            cell_width = sum(2 if ord(char) > 127 else 1 for char in cell)
            padding = col_widths[i] - cell_width
            parts.append(f' {cell}{" " * padding} ')
        return '|' + '|'.join(parts) + '|'
    
    # 添加顶部分隔线
    result.append(make_separator())
    
    # 添加表头
    if table_data:
        result.append(format_row(table_data[0]))
        result.append(make_separator())
        
        # 添加数据行
        for row in table_data[1:]:
            result.append(format_row(row))
    
    # 添加底部分隔线
    result.append(make_separator())
    
    return '\n'.join(result)

def detect_and_beautify_tables(content):
    """
    检测并美化文本中的表格
    """
    lines = content.split('\n')
    result_lines = []
    current_table = []
    in_table = False
    
    for line in lines:
        # 检测是否是表格行（包含多个分隔符）
        separators_count = sum(1 for sep in ['|', '\t'] if sep in line)
        has_multiple_items = len([item for item in re.split(r'[|\t，、]', line) if item.strip()]) > 2
        
        if (separators_count > 0 or has_multiple_items) and line.strip():
            if not in_table:
                in_table = True
            current_table.append(line)
        else:
            if in_table and current_table:
                # 处理当前表格
                table_text = '\n'.join(current_table)
                beautified_table = beautify_table(table_text)
                result_lines.append(beautified_table)
                current_table = []
                in_table = False
            
            result_lines.append(line)
    
    # 处理最后一个表格
    if in_table and current_table:
        table_text = '\n'.join(current_table)
        beautified_table = beautify_table(table_text)
        result_lines.append(beautified_table)
    
    return '\n'.join(result_lines)

def beautify_markdown(content):
    """
    美化markdown文本，添加更好的格式化和表格美化
    """
    # 首先检测并美化表格
    content = detect_and_beautify_tables(content)
    
    # 确保标题前后有空行
    content = re.sub(r'\n(#{1,6}\s+[^\n]+)', r'\n\n\1\n', content)
    
    # 确保列表项格式正确
    content = re.sub(r'\n([*+-]\s+)', r'\n\1', content)
    content = re.sub(r'\n(\d+\.\s+)', r'\n\1', content)
    
    # 添加代码块的语言标识（如果缺失）
    content = re.sub(r'```\n', '```\n', content)
    
    # 确保段落之间有适当的空行
    content = re.sub(r'\n\n\n+', '\n\n', content)
    
    # 清理开头和结尾的多余空行
    content = content.strip()
    
    return content

def get_llm_response(prompt, format_type="text", use_knowledge_base=None):
    """
    Sends a prompt to the LLM and gets a response with optional knowledge base enhancement.

    :param prompt: The input text to send to the LLM. Could be a JSON string.
    :param format_type: The desired output format ("markdown" or "text")
    :param use_knowledge_base: Whether to use knowledge base for context enhancement
    :return: The response text from the LLM or an error message.
    """
    # 如果prompt是JSON字符串，尝试解析它
    original_prompt = prompt
    try:
        # 检查是否是JSON字符串
        if isinstance(prompt, str) and (prompt.startswith('{') or prompt.startswith('[')):
            parsed_prompt = json.loads(prompt)
            # 将解析后的JSON转换为字符串表示，以便LLM理解
            prompt = json.dumps(parsed_prompt, ensure_ascii=False, indent=2)
    except json.JSONDecodeError:
        # 如果解析失败，保持原样
        pass
    
    # 知识库增强 - 受全局配置和参数控制
    knowledge_context = ""
    # 如果没有明确指定use_knowledge_base，则使用全局配置
    if use_knowledge_base is None:
        use_knowledge_base = ENABLE_KNOWLEDGE_BASE
    
    if use_knowledge_base and ENABLE_KNOWLEDGE_BASE:
        try:
            kb = get_knowledge_base()
            knowledge_context = kb.get_context_for_query(prompt, max_context_length=800)
            if knowledge_context:
                logging.info(f"Retrieved knowledge context: {len(knowledge_context)} characters")
        except Exception as e:
            logging.warning(f"Knowledge base query failed: {e}")
            knowledge_context = ""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLM_API_KEY}"
    }

    # 根据格式类型调整系统提示词
    system_prompt = SYSTEM_PROMPT
    
    # 添加知识库上下文
    if knowledge_context:
        system_prompt += f"\n\n【相关知识库内容】\n{knowledge_context}\n\n请结合上述知识库内容回答用户问题，确保答案准确、专业。如果知识库内容与问题相关，请优先使用知识库中的信息。"
    
    if format_type == "markdown":
        system_prompt += "\n\n请使用Markdown格式输出回答，包括适当的标题、列表、加粗等格式化元素，使内容更易读。"
    elif format_type == "text":
        system_prompt += "\n\n请输出结构清晰的文本，使用适当的标题和列表格式。"
    
    data = {
        "model": "deepseek-chat",  # 使用正确的模型名称
        "stream": False,  # 设置为False以获取完整响应
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.6,
        "top_p": 0.95
    }

    try:
        response = requests.post(LLM_API_URL, headers=headers, data=json.dumps(data))
        print(f"API Response Status: {response.status_code}")
        response.raise_for_status()  # Raise an exception for bad status codes
        
        result = response.json()
        content = result['choices'][0]['message']['content']
        print(f"原始LLM响应长度: {len(content)} 字符")
        
        # 根据格式类型处理内容
        if format_type == "markdown":
            content = beautify_markdown(content)
        elif format_type == "text":
            content = markdown_to_text(content)
        
        print(f"处理后响应长度: {len(content)} 字符")
        print(f"响应前100字符: {content[:100]}")
        print(f"响应后100字符: {content[-100:]}")
        
        return content
    except requests.exceptions.RequestException as e:
        print(f"Error calling LLM API: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Error response content: {e.response.text}")
        return {"error": str(e)}