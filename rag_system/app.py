"""
Flask Web应用
提供RAG问答系统的Web界面
"""

import os
from flask import Flask, request, jsonify, render_template
from rag_engine import RAGEngine

app = Flask(__name__)

# PDF文件路径
PDF_PATH = r"D:\zuohaowen\Desktop\大创\images\武汉理工大学学生手册2023.pdf"

# 全局RAG引擎实例
rag_engine = None


def get_rag_engine():
    """获取RAG引擎实例（懒加载）"""
    global rag_engine
    if rag_engine is None:
        print("正在初始化RAG引擎...")
        rag_engine = RAGEngine(
            pdf_path=PDF_PATH,
            persist_directory="./chroma_db",
            collection_name="student_handbook"
        )
        rag_engine.initialize()
        print("RAG引擎初始化完成")
    return rag_engine


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/api/query', methods=['POST'])
def query():
    """查询接口"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()

        if not question:
            return jsonify({
                'success': False,
                'error': '请输入问题'
            }), 400

        # 获取RAG引擎
        engine = get_rag_engine()

        # 执行查询
        results = engine.query(
            question=question,
            top_k=data.get('top_k', 5),
            page_filter=data.get('page_filter')
        )

        return jsonify({
            'success': True,
            'data': results
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stats')
def stats():
    """获取系统统计信息"""
    try:
        engine = get_rag_engine()
        return jsonify({
            'success': True,
            'data': engine.get_stats()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/rebuild', methods=['POST'])
def rebuild():
    """重建向量库"""
    try:
        engine = get_rag_engine()
        engine.rebuild()
        return jsonify({
            'success': True,
            'message': '向量库重建完成'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    # 启动时预加载RAG引擎
    get_rag_engine()
    app.run(host='0.0.0.0', port=5000, debug=False)
