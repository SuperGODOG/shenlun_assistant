# app.py

from flask import Flask, request, jsonify
from services import get_llm_response
from flask_cors import CORS
from knowledge_base import get_knowledge_base
from document_parser import get_document_parser
from werkzeug.utils import secure_filename
import logging
import os
import tempfile
import datetime
from config import MAX_DOCUMENT_SIZE, SUPPORTED_FORMATS, ENABLE_KNOWLEDGE_BASE
from middleware import concurrency_control, get_metrics, clear_cache
from performance_config import LOG_LEVEL, LOG_FORMAT, HEALTH_CHECK_ENABLED, SERVER_ID

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# 配置日志
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format=LOG_FORMAT
)
logger = logging.getLogger(__name__)

@app.route('/', methods=['GET'])
def index():
    """
    Root endpoint that returns a welcome message.
    """
    return jsonify({
        'message': '欢迎使用申论评分系统API',
        'endpoints': {
            '/api/chat': 'POST - 发送提示词获取LLM回复 (支持use_knowledge_base参数控制知识库功能)',
            '/api/knowledge/search': 'POST - 搜索知识库',
            '/api/knowledge/add': 'POST - 添加文档到知识库',
            '/api/knowledge/stats': 'GET - 获取知识库统计信息',
            '/api/documents/upload': 'POST - 上传文档到知识库',
            '/api/documents/batch-import': 'POST - 批量导入目录中的文档'
        },
        'knowledge_base_enabled': ENABLE_KNOWLEDGE_BASE
    })

@app.route('/api/chat', methods=['POST'])
@concurrency_control
def chat():
    """
    API endpoint to interact with the LLM.
    Expects a JSON payload with a "prompt" key and optional "format", "use_knowledge_base" keys.
    """
    try:
        data = request.json
        if not data or 'prompt' not in data:
            return jsonify({'error': 'Invalid input, "prompt" key is required.'}), 400

        prompt = data['prompt']
        format_type = data.get('format', 'text')  # 默认使用text格式
        use_knowledge_base = data.get('use_knowledge_base', None)  # None表示使用全局配置
        
        response = get_llm_response(prompt, format_type, use_knowledge_base)

        if isinstance(response, dict) and 'error' in response:
            return jsonify(response), 500

        return jsonify({
            'response': response,
            'format': format_type,
            'content_type': 'text/markdown' if format_type == 'markdown' else 'text/plain',
            'knowledge_base_used': use_knowledge_base
        })
    except Exception as e:
        logger.error(f'Chat endpoint error: {str(e)}')
        return jsonify({'error': f'处理请求时发生错误: {str(e)}'}), 500

@app.route('/api/beautify-table', methods=['POST'])
def beautify_table_api():
    """
    API endpoint to beautify table text.
    Expects a JSON payload with a "text" key and optional "format" key.
    """
    from services import beautify_table, beautify_table_for_text, detect_and_beautify_tables, detect_and_beautify_tables_for_text
    
    data = request.json
    if not data or 'text' not in data:
        return jsonify({'error': 'Invalid input, "text" key is required.'}), 400

    text = data['text']
    format_type = data.get('format', 'text')  # 默认使用text格式
    auto_detect = data.get('auto_detect', True)  # 是否自动检测表格
    
    try:
        if auto_detect:
            # 自动检测并美化文本中的所有表格
            if format_type == 'markdown':
                beautified_text = detect_and_beautify_tables(text)
            else:
                beautified_text = detect_and_beautify_tables_for_text(text)
        else:
            # 将整个文本作为单个表格处理
            if format_type == 'markdown':
                beautified_text = beautify_table(text)
            else:
                beautified_text = beautify_table_for_text(text)
        
        return jsonify({
            'original_text': text,
            'beautified_text': beautified_text,
            'format': format_type,
            'auto_detect': auto_detect,
            'content_type': 'text/markdown' if format_type == 'markdown' else 'text/plain'
        })
    
    except Exception as e:
        return jsonify({'error': f'Table beautification failed: {str(e)}'}), 500

@app.route('/api/knowledge/search', methods=['POST'])
def search_knowledge():
    """
    Search the knowledge base for relevant documents.
    """
    data = request.json
    if not data or 'query' not in data:
        return jsonify({'error': 'Invalid input, "query" key is required.'}), 400
    
    query = data['query']
    top_k = data.get('top_k', 5)
    min_score = data.get('min_score', 0.1)
    
    try:
        kb = get_knowledge_base()
        results = kb.search(query, top_k=top_k, min_score=min_score)
        
        return jsonify({
            'query': query,
            'results': results,
            'total_found': len(results)
        })
    except Exception as e:
        logging.error(f"Knowledge search error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/knowledge/add', methods=['POST'])
def add_knowledge():
    """
    Add a new document to the knowledge base.
    """
    data = request.json
    if not data or 'content' not in data:
        return jsonify({'error': 'Invalid input, "content" key is required.'}), 400
    
    content = data['content']
    title = data.get('title', '')
    category = data.get('category', '')
    tags = data.get('tags', [])
    
    try:
        kb = get_knowledge_base()
        doc_id = kb.add_document(content, title, category, tags)
        
        return jsonify({
            'message': 'Document added successfully',
            'document_id': doc_id
        })
    except Exception as e:
        logging.error(f"Knowledge add error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/knowledge/stats', methods=['GET'])
def knowledge_stats():
    """
    Get knowledge base statistics.
    """
    try:
        kb = get_knowledge_base()
        stats = kb.get_stats()
        
        return jsonify(stats)
    except Exception as e:
        logging.error(f"Knowledge stats error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents/upload', methods=['POST'])
def upload_document():
    """上传文档到知识库"""
    try:
        # 检查是否有文件上传
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': '没有上传文件'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': '没有选择文件'
            }), 400
        
        # 检查文件格式
        filename = secure_filename(file.filename)
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext not in SUPPORTED_FORMATS:
            return jsonify({
                'success': False,
                'error': f'不支持的文件格式: {file_ext}，支持的格式: {", ".join(SUPPORTED_FORMATS)}'
            }), 400
        
        # 检查文件大小
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_DOCUMENT_SIZE:
            return jsonify({
                'success': False,
                'error': f'文件过大，最大支持 {MAX_DOCUMENT_SIZE / 1024 / 1024:.1f}MB'
            }), 400
        
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            file.save(temp_file.name)
            temp_path = temp_file.name
        
        try:
            # 解析文档
            parser = get_document_parser()
            parsed_doc = parser.parse_file(temp_path)
            
            if not parsed_doc:
                return jsonify({
                    'success': False,
                    'error': '文档解析失败'
                }), 400
            
            # 添加到知识库
            kb = get_knowledge_base()
            
            # 获取可选的分类和标签
            category = request.form.get('category', '用户上传')
            tags_str = request.form.get('tags', '')
            tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()] if tags_str else []
            
            doc_id = kb.add_document(
                content=parsed_doc['content'],
                title=parsed_doc['title'],
                category=category,
                tags=tags
            )
            
            return jsonify({
                'success': True,
                'message': '文档上传成功',
                'document_id': doc_id,
                'title': parsed_doc['title'],
                'format': parsed_doc['format']
            })
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)
        
    except Exception as e:
        logging.error(f"文档上传失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'上传失败: {str(e)}'
        }), 500

@app.route('/api/documents/batch-import', methods=['POST'])
def batch_import_documents():
    """批量导入目录中的文档"""
    try:
        data = request.json
        if not data or 'directory' not in data:
            return jsonify({
                'success': False,
                'error': '请提供目录路径'
            }), 400
        
        directory = data['directory']
        recursive = data.get('recursive', True)
        category = data.get('category', '批量导入')
        
        # 检查目录是否存在
        if not os.path.exists(directory) or not os.path.isdir(directory):
            return jsonify({
                'success': False,
                'error': '目录不存在或不是有效目录'
            }), 400
        
        # 批量解析文档
        parser = get_document_parser()
        parsed_docs = parser.batch_parse_directory(directory, recursive)
        
        if not parsed_docs:
            return jsonify({
                'success': False,
                'error': '目录中没有找到支持的文档'
            }), 400
        
        # 添加到知识库
        kb = get_knowledge_base()
        imported_docs = []
        failed_docs = []
        
        for doc in parsed_docs:
            try:
                doc_id = kb.add_document(
                    content=doc['content'],
                    title=doc['title'],
                    category=category,
                    tags=[doc['format'], '批量导入']
                )
                
                imported_docs.append({
                    'id': doc_id,
                    'title': doc['title'],
                    'source': doc.get('source_path', ''),
                    'format': doc['format']
                })
                
            except Exception as e:
                failed_docs.append({
                    'title': doc['title'],
                    'source': doc.get('source_path', ''),
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'message': f'批量导入完成，成功导入 {len(imported_docs)} 个文档',
            'imported_count': len(imported_docs),
            'failed_count': len(failed_docs),
            'imported_documents': imported_docs,
            'failed_documents': failed_docs
        })
        
    except Exception as e:
        logging.error(f"批量导入失败: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'批量导入失败: {str(e)}'
        }), 500

@app.route('/api/metrics', methods=['GET'])
def metrics():
    """
    Get performance metrics.
    """
    try:
        metrics_data = get_metrics()
        return jsonify(metrics_data)
    except Exception as e:
        logger.error(f'Metrics endpoint error: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache_endpoint():
    """
    Clear application cache.
    """
    try:
        clear_cache()
        return jsonify({'message': 'Cache cleared successfully'})
    except Exception as e:
        logger.error(f'Clear cache endpoint error: {str(e)}')
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    """
    if not HEALTH_CHECK_ENABLED:
        return jsonify({'error': 'Health check disabled'}), 404
    
    try:
        # 基本健康检查
        health_status = {
            'status': 'healthy',
            'server_id': SERVER_ID,
            'timestamp': datetime.datetime.now().isoformat(),
            'services': {
                'llm': 'available',
                'knowledge_base': 'available' if ENABLE_KNOWLEDGE_BASE else 'disabled'
            }
        }
        
        # 检查知识库状态
        if ENABLE_KNOWLEDGE_BASE:
            try:
                kb = get_knowledge_base()
                stats = kb.get_stats()
                health_status['services']['knowledge_base'] = 'healthy'
                health_status['knowledge_base_stats'] = stats
            except Exception as e:
                health_status['services']['knowledge_base'] = 'unhealthy'
                health_status['knowledge_base_error'] = str(e)
        
        return jsonify(health_status)
    except Exception as e:
        logger.error(f'Health check error: {str(e)}')
        return jsonify({
            'status': 'unhealthy',
            'server_id': SERVER_ID,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # 配置日志
    logging.basicConfig(level=logging.INFO)
    app.run(debug=True, port=5001)