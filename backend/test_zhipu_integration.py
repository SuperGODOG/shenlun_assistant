#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智谱AI嵌入模型集成测试脚本

测试内容：
1. 智谱AI API连接测试
2. 嵌入向量生成测试
3. 知识库集成测试
4. 文档解析和上传测试
"""

import sys
import os
import logging
import json
from typing import List, Dict

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_zhipu_connection():
    """测试智谱AI API连接"""
    logger.info("=== 测试智谱AI API连接 ===")
    
    try:
        from zhipu_embedding import get_zhipu_embedding_service
        
        service = get_zhipu_embedding_service()
        
        # 测试连接
        if service.test_connection():
            logger.info("✅ 智谱AI API连接成功")
            return True
        else:
            logger.error("❌ 智谱AI API连接失败")
            return False
            
    except Exception as e:
        logger.error(f"❌ 智谱AI连接测试异常: {str(e)}")
        return False

def test_embedding_generation():
    """测试嵌入向量生成"""
    logger.info("=== 测试嵌入向量生成 ===")
    
    try:
        from zhipu_embedding import get_text_embedding, get_batch_embeddings
        
        # 测试单个文本嵌入
        test_text = "申论考试是公务员考试的重要组成部分"
        embedding = get_text_embedding(test_text)
        
        if embedding:
            logger.info(f"✅ 单文本嵌入成功，向量维度: {len(embedding)}")
        else:
            logger.error("❌ 单文本嵌入失败")
            return False
        
        # 测试批量文本嵌入
        test_texts = [
            "申论考试基础知识",
            "申论评分标准",
            "申论写作技巧"
        ]
        
        batch_embeddings = get_batch_embeddings(test_texts)
        
        if batch_embeddings and len(batch_embeddings) == len(test_texts):
            logger.info(f"✅ 批量嵌入成功，处理了 {len(batch_embeddings)} 个文本")
            return True
        else:
            logger.error("❌ 批量嵌入失败")
            return False
            
    except Exception as e:
        logger.error(f"❌ 嵌入向量生成测试异常: {str(e)}")
        return False

def test_knowledge_base_integration():
    """测试知识库集成"""
    logger.info("=== 测试知识库集成 ===")
    
    try:
        from knowledge_base import get_knowledge_base
        
        # 获取知识库实例
        kb = get_knowledge_base()
        
        # 测试添加文档
        test_doc_content = "这是一个测试文档，用于验证智谱AI嵌入模型在知识库中的集成效果。申论考试需要掌握材料分析、论点提炼、文章结构等技能。"
        doc_id = kb.add_document(
            content=test_doc_content,
            title="智谱AI集成测试文档",
            category="测试",
            tags=["测试", "智谱AI"]
        )
        
        logger.info(f"✅ 测试文档添加成功，ID: {doc_id}")
        
        # 测试搜索功能
        search_results = kb.search("申论考试技能", top_k=3)
        
        if search_results:
            logger.info(f"✅ 知识库搜索成功，找到 {len(search_results)} 个相关文档")
            for i, result in enumerate(search_results[:2]):
                logger.info(f"  结果 {i+1}: {result['title']} (相似度: {result.get('score', 'N/A')})")
        else:
            logger.warning("⚠️ 知识库搜索未找到相关文档")
        
        # 测试获取上下文
        context = kb.get_context_for_query("申论写作方法")
        
        if context:
            logger.info(f"✅ 上下文获取成功，长度: {len(context)} 字符")
        else:
            logger.warning("⚠️ 未获取到相关上下文")
        
        # 获取知识库统计信息
        stats = kb.get_stats()
        logger.info(f"📊 知识库统计: {json.dumps(stats, ensure_ascii=False, indent=2)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 知识库集成测试异常: {str(e)}")
        return False

def test_document_parsing():
    """测试文档解析功能"""
    logger.info("=== 测试文档解析功能 ===")
    
    try:
        from document_parser import get_document_parser
        
        parser = get_document_parser()
        
        # 测试支持的格式
        supported_formats = parser.get_supported_formats()
        logger.info(f"📄 支持的文档格式: {', '.join(supported_formats)}")
        
        # 测试文本内容解析
        test_content = """申论考试写作指南
        
申论考试是公务员考试的重要科目，主要测查考生的文字表达能力、阅读理解能力等。

写作要点：
1. 立意要准确
2. 结构要清晰
3. 论证要充分
4. 语言要规范

通过系统的练习和学习，考生可以有效提高申论写作水平。"""
        
        parsed_result = parser.parse_content_from_text(test_content, "申论写作指南")
        
        if parsed_result:
            logger.info(f"✅ 文本内容解析成功")
            logger.info(f"  标题: {parsed_result['title']}")
            logger.info(f"  内容长度: {len(parsed_result['content'])} 字符")
            logger.info(f"  格式: {parsed_result['format']}")
        else:
            logger.error("❌ 文本内容解析失败")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 文档解析测试异常: {str(e)}")
        return False

def test_api_endpoints():
    """测试API端点（需要启动Flask应用）"""
    logger.info("=== 测试API端点 ===")
    
    try:
        import requests
        
        base_url = "http://localhost:5001"
        
        # 测试根端点
        try:
            response = requests.get(f"{base_url}/", timeout=5)
            if response.status_code == 200:
                logger.info("✅ 根端点访问成功")
            else:
                logger.warning(f"⚠️ 根端点返回状态码: {response.status_code}")
        except requests.exceptions.RequestException:
            logger.warning("⚠️ 无法连接到Flask应用，请确保应用正在运行 (python app.py)")
            return False
        
        # 测试知识库统计端点
        try:
            response = requests.get(f"{base_url}/api/knowledge/stats", timeout=5)
            if response.status_code == 200:
                stats_data = response.json()
                logger.info("✅ 知识库统计API访问成功")
                logger.info(f"  统计信息: {json.dumps(stats_data, ensure_ascii=False, indent=2)}")
            else:
                logger.warning(f"⚠️ 知识库统计API返回状态码: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ 知识库统计API请求失败: {str(e)}")
        
        # 测试知识库搜索端点
        try:
            search_data = {
                "query": "申论考试",
                "top_k": 3
            }
            response = requests.post(
                f"{base_url}/api/knowledge/search",
                json=search_data,
                timeout=5
            )
            if response.status_code == 200:
                search_results = response.json()
                logger.info("✅ 知识库搜索API访问成功")
                logger.info(f"  搜索结果数量: {len(search_results.get('results', []))}")
            else:
                logger.warning(f"⚠️ 知识库搜索API返回状态码: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.warning(f"⚠️ 知识库搜索API请求失败: {str(e)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ API端点测试异常: {str(e)}")
        return False

def main():
    """主测试函数"""
    logger.info("🚀 开始智谱AI嵌入模型集成测试")
    logger.info("=" * 50)
    
    test_results = []
    
    # 执行各项测试
    tests = [
        ("智谱AI连接测试", test_zhipu_connection),
        ("嵌入向量生成测试", test_embedding_generation),
        ("知识库集成测试", test_knowledge_base_integration),
        ("文档解析测试", test_document_parsing),
        ("API端点测试", test_api_endpoints)
    ]
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 执行: {test_name}")
        try:
            result = test_func()
            test_results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ {test_name} 执行异常: {str(e)}")
            test_results.append((test_name, False))
    
    # 输出测试总结
    logger.info("\n" + "=" * 50)
    logger.info("📋 测试结果总结:")
    
    passed_count = 0
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"  {test_name}: {status}")
        if result:
            passed_count += 1
    
    total_tests = len(test_results)
    logger.info(f"\n🎯 总体结果: {passed_count}/{total_tests} 项测试通过")
    
    if passed_count == total_tests:
        logger.info("🎉 所有测试通过！智谱AI嵌入模型集成成功！")
    elif passed_count >= total_tests * 0.8:
        logger.info("⚠️ 大部分测试通过，集成基本成功，但有部分功能需要检查")
    else:
        logger.warning("❌ 多项测试失败，请检查配置和依赖")
    
    return passed_count == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)