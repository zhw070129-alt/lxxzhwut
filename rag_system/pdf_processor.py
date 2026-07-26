"""
PDF解析和文本分块模块
负责从学生手册PDF中提取文本，并进行智能分块
"""

import re
import fitz  # PyMuPDF
from typing import List, Dict, Tuple


class PDFProcessor:
    """PDF文本提取与分块处理器"""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = None

    def open(self):
        """打开PDF文件"""
        self.doc = fitz.open(self.pdf_path)
        print(f"已打开PDF: {self.pdf_path}, 共{len(self.doc)}页")

    def close(self):
        """关闭PDF文件"""
        if self.doc:
            self.doc.close()

    def extract_text_by_page(self) -> List[Dict]:
        """
        按页提取文本
        返回: [{"page_num": 页码, "text": 文本内容}, ...]
        """
        if not self.doc:
            self.open()

        pages = []
        for i, page in enumerate(self.doc):
            text = page.get_text("text")
            if text.strip():
                pages.append({
                    "page_num": i + 1,
                    "text": text.strip()
                })
        return pages

    def clean_text(self, text: str) -> str:
        """清理文本，去除多余空白和特殊字符"""
        # 合并连续换行
        text = re.sub(r'\n{3,}', '\n\n', text)
        # 去除行首行尾空白
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        # 去除连续空格
        text = re.sub(r' {2,}', ' ', text)
        return text.strip()

    def split_into_sections(self, text: str, page_num: int) -> List[Dict]:
        """
        基于标题和章节结构进行分块
        识别常见的章节标题模式
        """
        # 匹配章节标题模式
        # 例如: "第一章", "第二章", "一、", "1.", "1.1", "（一）" 等
        section_patterns = [
            r'^(第[一二三四五六七八九十百千万]+章\s*.+)',  # 第X章
            r'^(第[一二三四五六七八九十百千万]+节\s*.+)',  # 第X节
            r'^([一二三四五六七八九十]+、.+)',  # 一、xxx
            r'^(\d+\.\s*.+)',  # 1. xxx
            r'^(\d+\.\d+\s*.+)',  # 1.1 xxx
            r'^(（[一二三四五六七八九十]+）.+)',  # （一）xxx
            r'^(\([一二三四五六七八九十]+\)\s*.+)',  # （一）xxx
            r'^(【.+】)',  # 【xxx】
            r'^(◆.+)',  # ◆xxx
            r'^(●.+)',  # ●xxx
            r'^(◎.+)',  # ◎xxx
            r'^(■.+)',  # ■xxx
        ]

        combined_pattern = '|'.join(f'({p})' for p in section_patterns)

        # 按行分析
        lines = text.split('\n')
        sections = []
        current_section = {"title": "", "content": "", "page_num": page_num}

        for line in lines:
            if not line.strip():
                current_section["content"] += '\n'
                continue

            # 检查是否是标题行
            match = re.match(combined_pattern, line.strip())
            if match:
                # 保存当前章节
                if current_section["content"].strip():
                    sections.append(current_section.copy())
                # 开始新章节
                current_section = {
                    "title": line.strip(),
                    "content": "",
                    "page_num": page_num
                }
            else:
                current_section["content"] += line + '\n'

        # 保存最后一个章节
        if current_section["content"].strip():
            sections.append(current_section)

        return sections

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        将文本切分为固定大小的块，支持重叠
        """
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        # 按段落分割
        paragraphs = text.split('\n\n')

        current_chunk = ""
        for para in paragraphs:
            if len(current_chunk) + len(para) <= chunk_size:
                current_chunk += para + '\n\n'
            else:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = para + '\n\n'

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        # 如果有超长块，进一步切分
        final_chunks = []
        for chunk in chunks:
            if len(chunk) > chunk_size:
                # 按句号分割
                sentences = re.split(r'([。！？])', chunk)
                temp = ""
                for i in range(0, len(sentences), 2):
                    sent = sentences[i]
                    if i + 1 < len(sentences):
                        sent += sentences[i + 1]

                    if len(temp) + len(sent) <= chunk_size:
                        temp += sent
                    else:
                        if temp.strip():
                            final_chunks.append(temp.strip())
                        temp = sent
                if temp.strip():
                    final_chunks.append(temp.strip())
            else:
                final_chunks.append(chunk)

        return final_chunks

    def process(self, chunk_size: int = 500, overlap: int = 50) -> List[Dict]:
        """
        完整处理流程：提取文本 → 分块
        返回: [{"text": 文本块, "page_num": 页码, "section": 章节标题}, ...]
        """
        if not self.doc:
            self.open()

        all_chunks = []

        # 按页提取
        pages = self.extract_text_by_page()
        print(f"共提取 {len(pages)} 页文本")

        for page in pages:
            text = self.clean_text(page["text"])
            if not text:
                continue

            # 尝试按章节分割
            sections = self.split_into_sections(text, page["page_num"])

            if sections:
                for section in sections:
                    content = section["content"].strip()
                    if not content:
                        continue

                    # 对内容进行分块
                    text_chunks = self.chunk_text(content, chunk_size, overlap)

                    for chunk in text_chunks:
                        all_chunks.append({
                            "text": chunk,
                            "page_num": page["page_num"],
                            "section": section.get("title", "未知章节")
                        })
            else:
                # 没有识别到章节结构，直接分块
                text_chunks = self.chunk_text(text, chunk_size, overlap)
                for chunk in text_chunks:
                    all_chunks.append({
                        "text": chunk,
                        "page_num": page["page_num"],
                        "section": "第{}页".format(page["page_num"])
                    })

        self.close()
        print(f"共生成 {len(all_chunks)} 个文本块")
        return all_chunks


def test_processor():
    """测试PDF处理器"""
    pdf_path = r"D:\zuohaowen\Desktop\大创\images\武汉理工大学学生手册2023.pdf"

    processor = PDFProcessor(pdf_path)
    chunks = processor.process(chunk_size=500, overlap=50)

    # 显示前5个块
    for i, chunk in enumerate(chunks[:5]):
        print(f"\n=== 块 {i+1} ===")
        print(f"页码: {chunk['page_num']}")
        print(f"章节: {chunk['section']}")
        print(f"内容: {chunk['text'][:200]}...")

    return chunks


if __name__ == "__main__":
    test_processor()
