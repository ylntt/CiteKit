import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel,Field
from langchain_openai import ChatOpenAI
from typing import List

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DOCS_DIR = PROJECT_ROOT/"docs"          # 文档目录：项目根 / "docs"
INDEX_DIR = PROJECT_ROOT/".index"        # 索引目录：项目根 / ".index"

load_dotenv(PROJECT_ROOT/".env")
TEXT_SUFFIXES = [".md",".txt"]

def load_documents():
    """把docs内的.md文件读成Document列表"""
    docs = []
    for path in DOCS_DIR.glob("*"):
        if path.suffix not in TEXT_SUFFIXES:
            continue
        docs.extend(TextLoader(str(path),encoding="utf-8-sig").load())
    return docs

def split_documents(documents,chunk_size=100,chunk_overlap=20):
    """把整篇文档切成小块，方便检索"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return splitter.split_documents(documents)

def build_embeddings():
    """创建向量化模型（通义，自动读DASHSCOPE_API_KEY）。"""
    return DashScopeEmbeddings(model="text-embedding-v3")

def build_index(chunks,embeddings,batch_size=10):
    """把切块分批向量化，建立FAISS索引"""
    vectorstore = FAISS.from_documents(chunks[:batch_size],embeddings)
    for i in range(batch_size,len(chunks),batch_size):
        vectorstore.add_documents(chunks[i:i+batch_size])
    return vectorstore

def save_index(vectorstore):
    """把索引落盘到.index/ 目录。"""
    INDEX_DIR.mkdir(parents=True,exist_ok=True)
    vectorstore.save_local(str(INDEX_DIR))

def load_index(embeddings):
    """从.index/目录读回索引"""
    return FAISS.load_local(
        str(INDEX_DIR),
        embeddings,
        allow_dangerous_deserialization=True,
    )

class RAGResult(BaseModel):
    """结构化输出：答案+依据片段"""
    answer: str = Field(description="基于资料的回答")
    sources: List[str] = Field(description="回答所依据的原文片段，每条表明来源文件名")

RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system","你是一个严谨的助手，只根据提供的资料回答；资料没有就回答不知道。"
     "sources里填你依据的原文片段，并标注来源文件名。"),
    ("user","资料：{context}\n\n问题：{question}")
])

def build_model():
    """创建对话模型(deepseek，OpenAI兼容接口)"""
    return ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com"
    )

def format_docs(documents):
    """把检索到的Document拼成带来源的上下文文本"""
    return "\n\n".join(
        f"[来源：{d.metadata.get('source')}]\n{d.page_content}"
        for d in documents
    )

def answer_question(vectorstore,question,k=4):
    """检索->拼接上下文->基于资料回答，返回RAGResult"""
    documents = vectorstore.similarity_search(question, k=k)
    model = build_model()
    chain = RAG_PROMPT | model.with_structured_output(RAGResult)
    return chain.invoke({"context":format_docs(documents),"question":question})


if __name__ == "__main__":
    documents = load_documents()
    print("读到的文档数：", len(documents))

    chunks = split_documents(documents)
    print("切出的块数：", len(chunks))

    embeddings = build_embeddings()

    if (INDEX_DIR / "index.faiss").exists():
        vectorstore = load_index(embeddings)
        print("从磁盘读回索引：", type(vectorstore).__name__)
    else:
        vectorstore = build_index(chunks, embeddings)
        save_index(vectorstore)
        print("索引不存在，已新建并落盘到：", INDEX_DIR)

    hits = vectorstore.similarity_search("最小权限是什么", k=3)
    print("检索到", len(hits), "块")
    print("第一块来源：", hits[0].metadata.get("source"))
    print("第一块开头：", hits[0].page_content[:60].replace("\n", " "))


    result = answer_question(vectorstore, "口径变更要怎么走流程？")
    print()
    print("回答：", result.answer)
    print("出处：")
    for s in result.sources:
        print(" -", s[:60].replace("\n", " "))