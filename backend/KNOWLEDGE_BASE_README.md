# 申论小程序知识库功能说明

## 功能概述

本系统已集成智能知识库功能，可以为申论评分和指导提供更准确、专业的参考信息。知识库支持文档存储、向量化检索和智能匹配，即使在没有完整配置的情况下也能正常工作。

## 核心特性

### 🚀 自动回退机制
- **完整模式**: 使用 sentence-transformers + FAISS 进行高精度向量检索
- **轻量模式**: 当依赖库不可用时，自动切换到文本匹配模式
- **零配置启动**: 系统启动时自动创建默认申论知识库

### 📚 默认知识库内容
- 申论考试基础知识
- 评分标准详解
- 题型分类与技巧
- 写作方法指导

### 🔍 智能检索
- 支持语义相似度搜索
- 自动上下文提取
- 相关性评分排序

## API 接口

### 1. 聊天接口（已增强）
```http
POST /api/chat
Content-Type: application/json

{
  "prompt": "如何写好申论开头？",
  "format": "text"
}
```

**响应示例**:
```json
{
  "response": "根据知识库内容，申论写作要注意开头四步法：政治背景句、主题关键词植入、分析意义问题、亮明总论点...",
  "format": "text",
  "content_type": "text/plain"
}
```

### 2. 知识库搜索
```http
POST /api/knowledge/search
Content-Type: application/json

{
  "query": "申论评分标准",
  "top_k": 5,
  "min_score": 0.1
}
```

**响应示例**:
```json
{
  "query": "申论评分标准",
  "results": [
    {
      "id": "shenglun_scoring_1",
      "title": "申论评分标准",
      "content": "申论评分主要从立意、结构、论据、语言、对策五个维度进行评价...",
      "category": "评分标准",
      "tags": ["评分", "标准", "五维度"],
      "score": 0.95
    }
  ],
  "total_found": 1
}
```

### 3. 添加文档
```http
POST /api/knowledge/add
Content-Type: application/json

{
  "content": "新的申论知识内容...",
  "title": "文档标题",
  "category": "分类",
  "tags": ["标签1", "标签2"]
}
```

### 4. 统计信息
```http
GET /api/knowledge/stats
```

**响应示例**:
```json
{
  "total_documents": 4,
  "total_characters": 1250,
  "categories": {
    "基础知识": 1,
    "评分标准": 1,
    "题型分析": 1,
    "写作技巧": 1
  },
  "has_vector_index": true,
  "encoder_type": "sentence-transformers"
}
```

## 部署说明

### 完整部署（推荐）
```bash
# 安装完整依赖
pip install -r requirements.txt

# 启动服务
python app.py
```

### 轻量部署
如果无法安装 sentence-transformers 或 faiss-cpu：
```bash
# 只安装基础依赖
pip install Flask requests flask-cors numpy

# 启动服务（自动使用文本匹配模式）
python app.py
```

## 知识库管理

### 数据存储位置
- 文档数据: `knowledge_base/documents.json`
- 向量数据: `knowledge_base/embeddings.pkl`
- 索引文件: `knowledge_base/faiss.index`

### 添加自定义内容
1. **通过API添加**（推荐）
2. **直接编辑JSON文件**
3. **批量导入脚本**

### 备份与恢复
```bash
# 备份知识库
cp -r knowledge_base knowledge_base_backup

# 恢复知识库
cp -r knowledge_base_backup knowledge_base
```

## 性能优化

### 向量模型选择
- **默认**: `all-MiniLM-L6-v2` (轻量级，384维)
- **高精度**: `all-mpnet-base-v2` (768维，更准确)
- **中文优化**: `paraphrase-multilingual-MiniLM-L12-v2`

### 检索参数调优
- `top_k`: 返回结果数量 (建议 3-10)
- `min_score`: 最小相似度阈值 (建议 0.1-0.3)
- `max_context_length`: 上下文长度限制 (建议 800-1500)

## 故障排除

### 常见问题

1. **依赖安装失败**
   - 使用轻量模式部署
   - 检查Python版本兼容性

2. **知识库为空**
   - 检查 `knowledge_base` 目录权限
   - 重启服务自动创建默认内容

3. **检索结果不准确**
   - 调整 `min_score` 参数
   - 增加相关文档内容
   - 优化查询关键词

4. **内存占用过高**
   - 使用更小的向量模型
   - 限制知识库文档数量
   - 定期清理无用文档

### 日志查看
```bash
# 查看应用日志
tail -f app.log

# 查看知识库操作日志
grep "knowledge" app.log
```

## 扩展开发

### 自定义向量模型
```python
from knowledge_base import KnowledgeBase

# 使用自定义模型
kb = KnowledgeBase(model_name="your-custom-model")
```

### 批量导入脚本
```python
import json
from knowledge_base import get_knowledge_base

def batch_import(file_path):
    kb = get_knowledge_base()
    with open(file_path, 'r', encoding='utf-8') as f:
        docs = json.load(f)
    
    for doc in docs:
        kb.add_document(
            content=doc['content'],
            title=doc.get('title', ''),
            category=doc.get('category', ''),
            tags=doc.get('tags', [])
        )
```

## 最佳实践

1. **内容质量**: 确保添加的文档内容准确、完整
2. **分类管理**: 合理使用 category 和 tags 进行分类
3. **定期维护**: 定期清理过时内容，更新知识库
4. **性能监控**: 关注检索响应时间和准确性
5. **备份策略**: 定期备份知识库数据

## 技术架构

```
申论小程序后端
├── Flask API 服务
├── LLM 集成 (DeepSeek)
├── 知识库系统
│   ├── 文档存储 (JSON)
│   ├── 向量化 (sentence-transformers)
│   ├── 索引构建 (FAISS)
│   └── 相似度检索
└── 自动回退机制
```

通过这个知识库系统，申论小程序能够提供更加准确、专业的评分和指导服务，同时保持了良好的可扩展性和容错性。