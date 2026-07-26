"""
向量数据库模块
使用 ChromaDB 存储和检索文本向量
使用 sentence-transformers 生成文本嵌入
"""

import os
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Optional


class VectorStore:
    """基于ChromaDB的向量存储"""

    def __init__(
        self,
        collection_name: str = "student_handbook",
        persist_directory: str = "./chroma_db",
        model_name: str = "shibing624/text2vec-base-chinese"
    ):
        """
        初始化向量存储

        Args:
            collection_name: 集合名称
            persist_directory: 持久化目录
            model_name: 嵌入模型名称（中文优化）
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.model_name = model_name

        # 初始化嵌入模型
        print(f"正在加载嵌入模型: {model_name}...")
        self.embedding_model = SentenceTransformer(model_name)
        print("嵌入模型加载完成")

        # 初始化ChromaDB
        os.makedirs(persist_directory, exist_ok=True)
        self.client = chromadb.PersistentClient(path=persist_directory)

        # 获取或创建集合
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # 使用余弦相似度
        )
        print(f"集合 '{collection_name}' 已就绪，当前文档数: {self.collection.count()}")

    def add_documents(self, chunks: List[Dict], batch_size: int = 100) -> int:
        """
        添加文档到向量存储

        Args:
            chunks: 文档块列表，每个块包含 text, page_num, section
            batch_size: 批处理大小

        Returns:
            添加的文档数量
        """
        if not chunks:
            print("没有文档需要添加")
            return 0

        # 检查是否已存在数据
        existing_count = self.collection.count()
        if existing_count > 0:
            print(f"集合中已有 {existing_count} 个文档，跳过添加")
            return existing_count

        total_added = 0

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]

            # 提取文本和元数据
            texts = [chunk["text"] for chunk in batch]
            metadatas = [
                {
                    "page_num": chunk["page_num"],
                    "section": chunk.get("section", "未知"),
                    "chunk_id": i + j
                }
                for j, chunk in enumerate(batch)
            ]
            ids = [f"chunk_{i + j}" for j in range(len(batch))]

            # 生成嵌入向量
            print(f"正在嵌入第 {i+1}-{min(i+batch_size, len(chunks))} 个文档...")
            embeddings = self.embedding_model.encode(texts, show_progress_bar=False)
            embeddings_list = embeddings.tolist()

            # 添加到ChromaDB
            self.collection.add(
                embeddings=embeddings_list,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )

            total_added += len(batch)
            print(f"已添加 {total_added}/{len(chunks)} 个文档")

        print(f"文档添加完成，共添加 {total_added} 个文档")
        return total_added

    def search(
        self,
        query: str,
        top_k: int = 5,
        page_filter: Optional[int] = None
    ) -> List[Dict]:
        """
        语义检索

        Args:
            query: 查询文本
            top_k: 返回结果数量
            page_filter: 页码过滤（可选）

        Returns:
            检索结果列表
        """
        # 生成查询向量
        query_embedding = self.embedding_model.encode([query]).tolist()

        # 构建查询参数
        query_params = {
            "query_embeddings": query_embedding,
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"]
        }

        # 应用页码过滤
        if page_filter is not None:
            query_params["where"] = {"page_num": page_filter}

        # 执行查询
        results = self.collection.query(**query_params)

        # 整理结果
        search_results = []
        if results and results["documents"]:
            for i in range(len(results["documents"][0])):
                # ChromaDB 返回的距离是 1 - 余弦相似度
                distance = results["distances"][0][i]
                similarity = 1 - distance  # 转换为相似度

                search_results.append({
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": distance,
                    "similarity": round(similarity, 4)
                })

        return search_results

    def get_stats(self) -> Dict:
        """获取向量存储统计信息"""
        return {
            "total_documents": self.collection.count(),
            "collection_name": self.collection_name,
            "persist_directory": self.persist_directory,
            "model_name": self.model_name
        }

    def clear(self):
        """清空集合"""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        print("集合已清空")


def test_vector_store():
    """测试向量存储"""
    # 创建测试数据
    test_chunks = [
        {
            "text": '武汉理工大学是教育部直属全国重点大学，是首批列入国家"211工程"和"双一流"建设高校。',
            "page_num": 1,
            "section": "学校简介"
        },
        {
            "text": "学生应当拥护中国共产党的领导，努力学习马克思列宁主义、毛泽东思想、邓小平理论、“三个代表”重要思想、科学发展观、习近平新时代中国特色社会主义思想。",
            "page_num": 10,
            "section": "学生守则"
        },
        {
            "text": "学校实行学分制，学生须修满培养方案规定的学分方可毕业。",
            "page_num": 50,
            "section": "学籍管理"
        }
    ]

    # 初始化向量存储
    store = VectorStore(persist_directory="./test_db")

    # 添加文档
    store.add_documents(test_chunks)

    # 测试检索
    results = store.search("学校的办学层次是什么？", top_k=3)
    print("\n检索结果:")
    for r in results:
        print(f"相似度: {r['similarity']}")
        print(f"内容: {r['text'][:100]}...")
        print(f"页码: {r['metadata']['page_num']}")
        print("---")

    # 清理测试数据
    store.clear()
    print("\n测试完成")


if __name__ == "__main__":
    test_vector_store()
