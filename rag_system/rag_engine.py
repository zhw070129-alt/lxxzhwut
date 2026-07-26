"""
RAG查询引擎
整合PDF解析、向量存储和检索功能
"""

import os
from typing import List, Dict, Optional
from pdf_processor import PDFProcessor
from vector_store import VectorStore


class RAGEngine:
    """RAG查询引擎"""

    def __init__(
        self,
        pdf_path: str,
        persist_directory: str = "./chroma_db",
        collection_name: str = "student_handbook",
        model_name: str = "shibing624/text2vec-base-chinese"
    ):
        """
        初始化RAG引擎

        Args:
            pdf_path: PDF文件路径
            persist_directory: ChromaDB持久化目录
            collection_name: 集合名称
            model_name: 嵌入模型名称
        """
        self.pdf_path = pdf_path
        self.persist_directory = persist_directory
        self.collection_name = collection_name

        # 初始化向量存储
        self.vector_store = VectorStore(
            collection_name=collection_name,
            persist_directory=persist_directory,
            model_name=model_name
        )

        self.is_initialized = False

    def initialize(self, force_rebuild: bool = False):
        """
        初始化引擎，加载PDF并构建向量库

        Args:
            force_rebuild: 是否强制重建向量库
        """
        if force_rebuild:
            self.vector_store.clear()

        # 检查是否已有数据
        stats = self.vector_store.get_stats()
        if stats["total_documents"] > 0:
            print(f"向量库已有 {stats['total_documents']} 个文档，跳过构建")
            self.is_initialized = True
            return

        # 解析PDF
        print("正在解析PDF文件...")
        processor = PDFProcessor(self.pdf_path)
        chunks = processor.process(chunk_size=500, overlap=50)
        print(f"PDF解析完成，共 {len(chunks)} 个文本块")

        # 添加到向量库
        print("正在构建向量库...")
        self.vector_store.add_documents(chunks)
        print("向量库构建完成")

        self.is_initialized = True

    def query(
        self,
        question: str,
        top_k: int = 5,
        page_filter: Optional[int] = None,
        include_context: bool = True
    ) -> Dict:
        """
        执行RAG查询

        Args:
            question: 用户问题
            top_k: 返回结果数量
            page_filter: 页码过滤（可选）
            include_context: 是否包含上下文信息

        Returns:
            查询结果字典
        """
        if not self.is_initialized:
            self.initialize()

        # 语义检索
        search_results = self.vector_store.search(
            query=question,
            top_k=top_k,
            page_filter=page_filter
        )

        # 组装结果
        result = {
            "question": question,
            "results": search_results,
            "total_results": len(search_results)
        }

        if include_context and search_results:
            # 组装上下文
            context_parts = []
            for i, r in enumerate(search_results):
                context_parts.append(
                    f"[来源{i+1}] (页码:{r['metadata']['page_num']}, "
                    f"章节:{r['metadata']['section']})\n{r['text']}"
                )
            result["context"] = "\n\n".join(context_parts)

        return result

    def get_stats(self) -> Dict:
        """获取引擎统计信息"""
        return {
            **self.vector_store.get_stats(),
            "pdf_path": self.pdf_path,
            "is_initialized": self.is_initialized
        }

    def rebuild(self):
        """重建向量库"""
        self.vector_store.clear()
        self.initialize(force_rebuild=True)


def format_results(results: Dict) -> str:
    """格式化查询结果为可读文本"""
    output = []
    output.append(f"问题: {results['question']}")
    output.append(f"找到 {results['total_results']} 条相关结果:\n")

    for i, r in enumerate(results['results']):
        output.append(f"{'='*60}")
        output.append(f"结果 {i+1} (相似度: {r['similarity']:.4f})")
        output.append(f"页码: {r['metadata']['page_num']}")
        output.append(f"章节: {r['metadata']['section']}")
        output.append(f"内容:")
        output.append(r['text'])
        output.append("")

    return "\n".join(output)


def interactive_mode():
    """交互式查询模式"""
    pdf_path = r"D:\zuohaowen\Desktop\大创\images\武汉理工大学学生手册2023.pdf"

    print("正在初始化RAG引擎...")
    engine = RAGEngine(pdf_path)
    engine.initialize()

    print("\n" + "="*60)
    print("武汉理工大学学生手册 RAG 问答系统")
    print("输入问题进行查询，输入 'quit' 退出")
    print("="*60 + "\n")

    while True:
        try:
            question = input("请输入问题: ").strip()
            if question.lower() in ['quit', 'exit', 'q', '退出']:
                print("再见！")
                break

            if not question:
                continue

            results = engine.query(question, top_k=5)
            print("\n" + format_results(results))

        except KeyboardInterrupt:
            print("\n再见！")
            break
        except Exception as e:
            print(f"查询出错: {e}")


if __name__ == "__main__":
    interactive_mode()
