# 智谱AI嵌入模型服务
import requests
import json
import logging
import os
from typing import List, Optional
from config import ZHIPU_API_URL, ZHIPU_API_KEY, ZHIPU_EMBEDDING_MODEL

logger = logging.getLogger(__name__)

class ZhipuEmbeddingService:
    """智谱AI嵌入模型服务类"""
    
    def __init__(self):
        self.api_url = ZHIPU_API_URL
        self.api_key = ZHIPU_API_KEY
        self.model = ZHIPU_EMBEDDING_MODEL
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def get_embeddings(self, texts: List[str]) -> Optional[List[List[float]]]:
        """获取文本嵌入向量
        
        Args:
            texts: 文本列表
            
        Returns:
            嵌入向量列表，如果失败返回None
        """
        try:
            # 智谱AI嵌入API端点
            url = f"{self.api_url.rstrip('/')}/embeddings"
            
            payload = {
                "model": self.model,
                "input": texts
            }
            
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                embeddings = [item['embedding'] for item in result.get('data', [])]
                logger.info(f"成功获取 {len(embeddings)} 个文本的嵌入向量")
                return embeddings
            else:
                logger.error(f"智谱AI嵌入API调用失败: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"智谱AI嵌入API请求异常: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"智谱AI嵌入服务异常: {str(e)}")
            return None
    
    def get_single_embedding(self, text: str) -> Optional[List[float]]:
        """获取单个文本的嵌入向量
        
        Args:
            text: 输入文本
            
        Returns:
            嵌入向量，如果失败返回None
        """
        embeddings = self.get_embeddings([text])
        return embeddings[0] if embeddings else None
    
    def test_connection(self) -> bool:
        """测试API连接
        
        Returns:
            连接是否成功
        """
        try:
            test_embedding = self.get_single_embedding("测试文本")
            return test_embedding is not None
        except Exception as e:
            logger.error(f"智谱AI连接测试失败: {str(e)}")
            return False

# 全局智谱AI嵌入服务实例
_zhipu_service = None

def get_zhipu_embedding_service() -> ZhipuEmbeddingService:
    """获取智谱AI嵌入服务实例"""
    global _zhipu_service
    if _zhipu_service is None:
        _zhipu_service = ZhipuEmbeddingService()
    return _zhipu_service

def get_text_embedding(text: str) -> Optional[List[float]]:
    """便捷函数：获取文本嵌入向量"""
    service = get_zhipu_embedding_service()
    return service.get_single_embedding(text)

def get_batch_embeddings(texts: List[str]) -> Optional[List[List[float]]]:
    """便捷函数：批量获取文本嵌入向量"""
    service = get_zhipu_embedding_service()
    return service.get_embeddings(texts)