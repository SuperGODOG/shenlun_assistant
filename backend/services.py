# services.py

import requests
import json
import re
from config import LLM_API_URL, LLM_API_KEY, SYSTEM_PROMPT

def markdown_to_text(markdown_content):
    """
    将markdown文本转换为美化的纯文本
    """
    # 移除markdown标记但保留结构
    text = markdown_content
    
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

def beautify_markdown(content):
    """
    美化markdown文本，添加更好的格式化
    """
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

def get_llm_response(prompt, format_type="text"):
    """
    Sends a prompt to the LLM and gets a response.

    :param prompt: The input text to send to the LLM. Could be a JSON string.
    :param format_type: The desired output format ("markdown" or "text")
    :return: The response text from the LLM or an error message.
    """
    # 如果prompt是JSON字符串，尝试解析它
    try:
        # 检查是否是JSON字符串
        if isinstance(prompt, str) and (prompt.startswith('{') or prompt.startswith('[')):
            parsed_prompt = json.loads(prompt)
            # 将解析后的JSON转换为字符串表示，以便LLM理解
            prompt = json.dumps(parsed_prompt, ensure_ascii=False, indent=2)
    except json.JSONDecodeError:
        # 如果解析失败，保持原样
        pass
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LLM_API_KEY}"
    }

    # 根据格式类型调整系统提示词
    system_prompt = SYSTEM_PROMPT
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