import os
from typing import List, Dict, Any
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

class RAGKnowledgeBase:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory
        # 初始化嵌入模型，指向LiteLLM的兼容接口
        self.embeddings = OpenAIEmbeddings(
            base_url=os.getenv("OPENAI_API_BASE", "http://localhost:4000/v1"),
            api_key=os.getenv("OPENAI_API_KEY", "sk-zhu-litellm-2026"),
            model=os.getenv("OPENAI_EMBEDDING_MODEL_NAME", "text-embedding-ada-002") # 假设LiteLLM也兼容OpenAI的embedding模型名
        )
        # 尝试加载已存在的向量数据库，如果不存在则会创建新的
        try:
            self.vectorstore = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings)
            # 检查是否为空，Chroma加载空数据库不会报错
            if self.vectorstore.get()['ids'] == []:
                print(f"ChromaDB initialized at {persist_directory}, but is empty.")
        except Exception as e:
            print(f"Error loading ChromaDB: {e}. Creating a new one.")
            self.vectorstore = Chroma(persist_directory=self.persist_directory, embedding_function=self.embeddings)
            
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            add_start_index=True,
        )
        print(f"RAGKnowledgeBase initialized with ChromaDB at {persist_directory}")

    def upload_pdf_resume(self, pdf_path: str):
        """上传PDF简历并将其内容建立索引"""
        print(f"Loading PDF: {pdf_path}")
        loader = PyPDFLoader(pdf_path)
        docs = loader.load()
        
        if not docs:
            print(f"No content found in PDF: {pdf_path}")
            return

        print(f"Splitting {len(docs)} document(s) into chunks...")
        chunks = self.text_splitter.split_documents(docs)
        print(f"Adding {len(chunks)} chunks to ChromaDB...")
        
        self.vectorstore.add_documents(chunks)
        self.vectorstore.persist()
        print(f"PDF resume {pdf_path} indexed successfully.")

    def search_related_experience(self, query: str, k: int = 5) -> List[str]:
        """根据查询在知识库中搜索相关的经验或信息"""
        if self.vectorstore.get()['ids'] == []:
            print("Vector store is empty, no search performed.")
            return []

        print(f"Searching ChromaDB for query: {query}")
        results = self.vectorstore.similarity_search(query, k=k)
        
        related_texts = [doc.page_content for doc in results]
        print(f"Found {len(related_texts)} related results.")
        return related_texts

# 示例用法 (不会在实际运行时执行，仅为演示)
if __name__ == "__main__":
    # 设置环境变量
    os.environ["OPENAI_API_BASE"] = "http://localhost:4000/v1"
    os.environ["OPENAI_API_KEY"] = "sk-zhu-litellm-2026"
    os.environ["OPENAI_EMBEDDING_MODEL_NAME"] = "text-embedding-ada-002"

    # 创建RAG知识库实例
    rag_kb = RAGKnowledgeBase(persist_directory="./chroma_db_test")

    # 模拟上传简历
    # 注意：这里需要一个实际存在的PDF文件路径来测试
    # 如果没有，可以手动创建一个dummy.pdf文件
    # with open("dummy.pdf", "w") as f:
    #     f.write("This is a dummy PDF file content.") # 实际PDF内容需要更复杂，否则PyPDFLoader会报错
    # try:
    #     rag_kb.upload_pdf_resume("dummy.pdf")
    # except Exception as e:
    #     print(f"Could not upload dummy.pdf: {e}")

    # 模拟搜索
    # results = rag_kb.search_related_experience("项目管理经验")
    # print("\nRelated experiences:")
    # for res in results:
    #     print(f"- {res}")

    print("RAGKnowledgeBase demonstration finished.")
