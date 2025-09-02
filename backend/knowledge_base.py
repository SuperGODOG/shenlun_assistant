# knowledge_base.py

import os
import json
import pickle
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logging.warning("FAISS not available, using fallback similarity search")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("sentence-transformers not available, using fallback embedding")

# 导入智谱AI嵌入服务
try:
    from zhipu_embedding import get_zhipu_embedding_service, get_batch_embeddings
    ZHIPU_EMBEDDING_AVAILABLE = True
except ImportError:
    ZHIPU_EMBEDDING_AVAILABLE = False
    logging.warning("Zhipu embedding service not available, using fallback embedding")

class KnowledgeBase:
    """
    轻量级知识库系统，支持文档存储、向量化和相似性检索
    即使没有依赖库也能正常工作（使用简单的文本匹配）
    """
    
    def __init__(self, kb_dir: str = "knowledge_base", model_name: str = "all-MiniLM-L6-v2", use_zhipu: bool = True):
        self.kb_dir = kb_dir
        self.model_name = model_name
        self.use_zhipu = use_zhipu
        self.documents = []
        self.embeddings = None
        self.index = None
        self.encoder = None
        self.zhipu_service = None
        
        # 创建知识库目录
        os.makedirs(self.kb_dir, exist_ok=True)
        
        # 初始化编码器
        self._init_encoder()
        
        # 加载现有知识库
        self._load_knowledge_base()
        
        # 如果没有数据，创建默认知识库
        if not self.documents:
            self._create_default_knowledge_base()
    
    def _init_encoder(self):
        """初始化文本编码器"""
        # 优先使用智谱AI嵌入服务
        if self.use_zhipu and ZHIPU_EMBEDDING_AVAILABLE:
            try:
                self.zhipu_service = get_zhipu_embedding_service()
                # 测试连接
                if self.zhipu_service.test_connection():
                    logging.info("Successfully initialized Zhipu embedding service")
                    return
                else:
                    logging.warning("Zhipu embedding service connection failed, falling back to local models")
            except Exception as e:
                logging.warning(f"Failed to initialize Zhipu embedding service: {e}")
        
        # 回退到本地sentence-transformers
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.encoder = SentenceTransformer(self.model_name)
                logging.info(f"Loaded SentenceTransformer model: {self.model_name}")
            except Exception as e:
                logging.warning(f"Failed to load SentenceTransformer: {e}")
                self.encoder = None
        else:
            self.encoder = None
            logging.info("Using fallback text matching (no embedding models available)")
    
    def _create_default_knowledge_base(self):
        """创建默认的申论知识库"""
        default_docs = [
            {
                "id": "shenglun_basics_1",
                "title": "申论考试基础知识",
                "content": "申论考试是公务员考试的重要组成部分，主要测查考生的阅读理解能力、综合分析能力、提出和解决问题能力、文字表达能力。考试时间通常为180分钟，满分100分。",
                "category": "基础知识",
                "tags": ["申论", "公务员考试", "基础"]
            },
            {
                "id": "shenglun_scoring_1",
                "title": "申论评分标准",
                "content": "申论评分主要从立意、结构、论据、语言、对策五个维度进行评价。立意要准确深刻，结构要清晰完整，论据要充分有力，语言要规范流畅，对策要可行有效。",
                "category": "评分标准",
                "tags": ["评分", "标准", "五维度"]
            },
            {
                "id": "shenglun_types_1",
                "title": "申论题型分类",
                "content": "申论主要包括概括论述题、对策建议题、综合分析题、应用文写作题、文章写作题五大题型。每种题型都有其特定的答题要求和评分标准。",
                "category": "题型分析",
                "tags": ["题型", "分类", "答题技巧"]
            },
            {
                "id": "shenglun_writing_1",
                "title": "申论写作技巧",
                "content": "申论写作要注意开头四步法：政治背景句、主题关键词植入、分析意义问题、亮明总论点。文章结构要合理，论证要充分，语言要规范。",
                "category": "写作技巧",
                "tags": ["写作", "技巧", "结构"]
            }
        ]
        
        for doc in default_docs:
            self.add_document(doc["content"], doc["title"], doc.get("category", ""), doc.get("tags", []))
        
        logging.info(f"Created default knowledge base with {len(default_docs)} documents")
    
    def add_document(self, content: str, title: str = "", category: str = "", tags: List[str] = None) -> str:
        """添加文档到知识库"""
        doc_id = f"doc_{len(self.documents)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        document = {
            "id": doc_id,
            "title": title,
            "content": content,
            "category": category,
            "tags": tags or [],
            "created_at": datetime.now().isoformat()
        }
        
        self.documents.append(document)
        
        # 重新构建索引
        self._build_index()
        
        # 保存知识库
        self._save_knowledge_base()
        
        return doc_id
    
    def _encode_texts(self, texts: List[str]) -> np.ndarray:
        """文本编码"""
        # 优先使用智谱AI嵌入服务
        if self.zhipu_service:
            try:
                embeddings = get_batch_embeddings(texts)
                if embeddings:
                    logging.info(f"Successfully encoded {len(texts)} texts using Zhipu embedding")
                    return np.array(embeddings)
                else:
                    logging.warning("Zhipu embedding failed, falling back to local models")
            except Exception as e:
                logging.warning(f"Zhipu encoding failed: {e}, using fallback")
        
        # 回退到本地sentence-transformers
        if self.encoder and SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                embeddings = self.encoder.encode(texts)
                return np.array(embeddings)
            except Exception as e:
                logging.warning(f"Local encoding failed: {e}, using fallback")
        
        # 最终回退方案：使用简单的词频向量
        return self._simple_text_encoding(texts)
    
    def _simple_text_encoding(self, texts: List[str]) -> np.ndarray:
        """简单的文本编码（回退方案）"""
        # 构建词汇表
        vocab = set()
        for text in texts:
            words = text.lower().split()
            vocab.update(words)
        
        vocab = list(vocab)
        vocab_size = len(vocab)
        
        # 创建词频向量
        embeddings = []
        for text in texts:
            words = text.lower().split()
            vector = np.zeros(vocab_size)
            for word in words:
                if word in vocab:
                    vector[vocab.index(word)] += 1
            embeddings.append(vector)
        
        return np.array(embeddings)
    
    def _build_index(self):
        """构建向量索引"""
        if not self.documents:
            return
        
        # 提取文档内容
        texts = [doc["content"] for doc in self.documents]
        
        # 编码文本
        self.embeddings = self._encode_texts(texts)
        
        # 构建FAISS索引
        if FAISS_AVAILABLE and self.embeddings.shape[1] > 0:
            try:
                dimension = self.embeddings.shape[1]
                self.index = faiss.IndexFlatIP(dimension)  # 内积相似度
                # 归一化向量
                faiss.normalize_L2(self.embeddings)
                self.index.add(self.embeddings)
                logging.info(f"Built FAISS index with {len(self.documents)} documents")
            except Exception as e:
                logging.warning(f"FAISS indexing failed: {e}, using fallback search")
                self.index = None
        else:
            self.index = None
    
    def search(self, query: str, top_k: int = 5, min_score: float = 0.01) -> List[Dict]:
        """搜索相关文档"""
        if not self.documents:
            return []
        
        if self.index and self.embeddings is not None:
            # 使用向量搜索
            return self._vector_search(query, top_k, min_score)
        else:
            # 使用文本匹配搜索
            results = self._text_search(query, top_k)
            # 应用最小分数过滤
            return [r for r in results if r.get('score', 0) >= min_score]
    
    def _vector_search(self, query: str, top_k: int, min_score: float) -> List[Dict]:
        """向量搜索"""
        try:
            # 编码查询
            query_embedding = self._encode_texts([query])
            faiss.normalize_L2(query_embedding)
            
            # 搜索
            scores, indices = self.index.search(query_embedding, min(top_k, len(self.documents)))
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if score >= min_score:
                    doc = self.documents[idx].copy()
                    doc["score"] = float(score)
                    results.append(doc)
            
            return results
        except Exception as e:
            logging.warning(f"Vector search failed: {e}, using text search")
            return self._text_search(query, top_k)
    
    def _text_search(self, query: str, top_k: int) -> List[Dict]:
        """文本匹配搜索（回退方案）"""
        query_lower = query.lower()
        
        # 提取中文关键词（简单方法：按常见词分割）
        import re
        # 移除标点符号和常见停用词
        query_clean = re.sub(r'[什么是的？！。，、；：]', ' ', query_lower)
        query_words = [w.strip() for w in query_clean.split() if len(w.strip()) > 0]
        
        results = []
        for doc in self.documents:
            content_lower = doc["content"].lower()
            title_lower = doc["title"].lower()
            
            # 计算匹配分数
            content_score = 0
            title_score = 0
            
            # 1. 直接包含检查
            if query_lower in content_lower:
                content_score += 1.0
            if query_lower in title_lower:
                title_score += 1.0
            
            # 2. 关键词匹配
            for word in query_words:
                if len(word) >= 2:  # 只考虑长度>=2的词
                    if word in content_lower:
                        content_score += 0.5
                    if word in title_lower:
                        title_score += 0.5
            
            # 3. 字符级相似度（针对中文）
            query_chars = set(query_lower)
            content_chars = set(content_lower)
            title_chars = set(title_lower)
            
            if len(query_chars) > 0:
                content_char_overlap = len(query_chars & content_chars) / len(query_chars)
                title_char_overlap = len(query_chars & title_chars) / len(query_chars)
                
                content_score += content_char_overlap * 0.3
                title_score += title_char_overlap * 0.3
            
            # 综合评分
            final_score = content_score * 0.7 + title_score * 0.3
            
            if final_score > 0:
                doc_copy = doc.copy()
                doc_copy["score"] = final_score
                results.append(doc_copy)
        
        # 按分数排序
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results[:top_k]
    
    def get_context_for_query(self, query: str, max_context_length: int = 1000) -> str:
        """获取查询相关的上下文"""
        results = self.search(query, top_k=3)
        
        if not results:
            return ""
        
        context_parts = []
        current_length = 0
        
        for result in results:
            content = result["content"]
            title = result["title"]
            
            # 格式化内容
            formatted_content = f"【{title}】\n{content}"
            
            if current_length + len(formatted_content) <= max_context_length:
                context_parts.append(formatted_content)
                current_length += len(formatted_content)
            else:
                # 截断最后一个文档
                remaining_length = max_context_length - current_length
                if remaining_length > 100:  # 至少保留100字符
                    truncated_content = content[:remaining_length-len(title)-10] + "..."
                    context_parts.append(f"【{title}】\n{truncated_content}")
                break
        
        return "\n\n".join(context_parts)
    
    def _save_knowledge_base(self):
        """保存知识库"""
        try:
            # 保存文档数据
            docs_file = os.path.join(self.kb_dir, "documents.json")
            with open(docs_file, "w", encoding="utf-8") as f:
                json.dump(self.documents, f, ensure_ascii=False, indent=2)
            
            # 保存向量数据
            if self.embeddings is not None:
                embeddings_file = os.path.join(self.kb_dir, "embeddings.pkl")
                with open(embeddings_file, "wb") as f:
                    pickle.dump(self.embeddings, f)
            
            # 保存FAISS索引
            if self.index is not None:
                index_file = os.path.join(self.kb_dir, "faiss.index")
                faiss.write_index(self.index, index_file)
            
            logging.info("Knowledge base saved successfully")
        except Exception as e:
            logging.error(f"Failed to save knowledge base: {e}")
    
    def _load_knowledge_base(self):
        """加载知识库"""
        try:
            # 加载文档数据
            docs_file = os.path.join(self.kb_dir, "documents.json")
            if os.path.exists(docs_file):
                with open(docs_file, "r", encoding="utf-8") as f:
                    self.documents = json.load(f)
            
            # 加载向量数据
            embeddings_file = os.path.join(self.kb_dir, "embeddings.pkl")
            if os.path.exists(embeddings_file):
                with open(embeddings_file, "rb") as f:
                    self.embeddings = pickle.load(f)
            
            # 加载FAISS索引
            index_file = os.path.join(self.kb_dir, "faiss.index")
            if os.path.exists(index_file) and FAISS_AVAILABLE:
                try:
                    self.index = faiss.read_index(index_file)
                except Exception as e:
                    logging.warning(f"Failed to load FAISS index: {e}")
                    self.index = None
            
            if self.documents:
                logging.info(f"Loaded knowledge base with {len(self.documents)} documents")
            
        except Exception as e:
            logging.error(f"Failed to load knowledge base: {e}")
            self.documents = []
    
    def get_stats(self) -> Dict:
        """获取知识库统计信息"""
        categories = {}
        total_chars = 0
        
        for doc in self.documents:
            category = doc.get("category", "未分类")
            categories[category] = categories.get(category, 0) + 1
            total_chars += len(doc["content"])
        
        return {
            "total_documents": len(self.documents),
            "total_characters": total_chars,
            "categories": categories,
            "has_vector_index": self.index is not None,
            "encoder_type": "sentence-transformers" if self.encoder else "simple_text"
        }

# 全局知识库实例
_knowledge_base = None

def get_knowledge_base() -> KnowledgeBase:
    """获取全局知识库实例"""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = KnowledgeBase()
    return _knowledge_base