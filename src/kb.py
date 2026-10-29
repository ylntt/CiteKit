import hashlib
import json
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DOCS_DIR = PROJECT_ROOT / "docs"
INDEX_DIR = PROJECT_ROOT / ".index"
STORE_PATH = INDEX_DIR / "vectors.json"
STORE_VERSION = 2
TEXT_SUFFIXES = [".md", ".txt"]

load_dotenv(PROJECT_ROOT / ".env")


# ---------- 扫描 docs/ ----------

def file_fingerprint(path):
    """算出一个文件的指纹：大小、修改时间、内容哈希。"""
    stat = path.stat()
    return {
        "size": stat.st_size,
        "mtime": stat.st_mtime,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def scan_docs():
    """扫描 docs/，返回 {文件名: 指纹}。"""
    fingerprints = {}
    for path in sorted(DOCS_DIR.glob("*")):
        if path.suffix not in TEXT_SUFFIXES:
            continue
        fingerprints[path.name] = file_fingerprint(path)
    return fingerprints


# ---------- 读取与切块 ----------

def load_one_document(name):
    """读单个文件成 Document 列表。"""
    return TextLoader(str(DOCS_DIR / name), encoding="utf-8-sig").load()


def load_documents():
    """把 docs/ 里的纯文本文件读成 Document 列表。"""
    docs = []
    for name in sorted(scan_docs()):
        docs.extend(load_one_document(name))
    return docs


def split_documents(documents, chunk_size=100, chunk_overlap=20):
    """把整篇文档切成小块，便于检索。"""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return splitter.split_documents(documents)


# ---------- 向量化 ----------

def build_embeddings():
    """创建向量化模型（通义 DashScope，自动读 DASHSCOPE_API_KEY）。"""
    return DashScopeEmbeddings(model="text-embedding-v3")


def embed_chunks(chunks, embeddings, batch_size=10):
    """给一批块调 embedding（DashScope 单次上限 10 条），返回一一对应的向量列表。"""
    vectors = []
    for i in range(0, len(chunks), batch_size):
        batch = [c.page_content for c in chunks[i:i + batch_size]]
        vectors.extend(embeddings.embed_documents(batch))
    return vectors


# ---------- 索引仓库（参数 + 每个文件的指纹与向量，唯一事实来源）----------

def ingest_params(model_name, chunk_size, chunk_overlap):
    """影响向量结果的三个参数：任一变化都必须整体重建。"""
    return {
        "model": model_name,
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap,
    }


def load_store():
    """读回索引仓库；不存在、版本不认识或结构不对，就当空的。"""
    if not STORE_PATH.exists():
        return {"version": STORE_VERSION, "params": {}, "files": {}}
    try:
        store = json.loads(STORE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"version": STORE_VERSION, "params": {}, "files": {}}
    if (
        store.get("version") != STORE_VERSION
        or not isinstance(store.get("params"), dict)
        or not isinstance(store.get("files"), dict)
    ):
        return {"version": STORE_VERSION, "params": {}, "files": {}}
    return store


def save_store(store):
    """把索引仓库写回磁盘（紧凑 JSON，别让向量文件虚胖）。"""
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    STORE_PATH.write_text(
        json.dumps(store, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )


def plan_changes(store, fingerprints, params):
    """对比索引仓库与当前 docs/，分出：要重嵌的、可复用的、已删除的。"""
    if store["params"] != params:
        return {
            "rebuild_all": True,
            "changed": sorted(fingerprints),
            "unchanged": [],
            "deleted": sorted(store["files"]),
        }

    changed, unchanged = [], []
    for name, fingerprint in fingerprints.items():
        cached = store["files"].get(name)
        if cached is None or cached.get("sha256") != fingerprint["sha256"]:
            changed.append(name)
        else:
            unchanged.append(name)

    deleted = [name for name in store["files"] if name not in fingerprints]
    return {
        "rebuild_all": False,
        "changed": sorted(changed),
        "unchanged": sorted(unchanged),
        "deleted": sorted(deleted),
    }


def update_store(store, plan, fingerprints, embeddings, chunk_size, chunk_overlap):
    """只给变更/新增的文件重算向量；已删除的文件从仓库里清掉。"""
    files = store["files"]

    for name in list(files):
        if name not in fingerprints:
            del files[name]

    for name in plan["changed"]:
        chunks = split_documents(load_one_document(name), chunk_size, chunk_overlap)
        vectors = embed_chunks(chunks, embeddings)
        files[name] = {
            "sha256": fingerprints[name]["sha256"],
            "size": fingerprints[name]["size"],
            "mtime": fingerprints[name]["mtime"],
            "chunks": [
                {"text": chunk.page_content, "vector": vector}
                for chunk, vector in zip(chunks, vectors)
            ],
        }
    return store


def count_chunks(store, names):
    """数一数这些文件在仓库里一共有多少块。"""
    return sum(
        len(store["files"][name]["chunks"])
        for name in names
        if name in store["files"]
    )


# ---------- FAISS 索引 ----------

def build_index_from_store(store, embeddings):
    """用索引仓库里的向量重建 FAISS —— 一次 embedding API 都不调。"""
    pairs, metadatas = [], []
    for name, entry in sorted(store["files"].items()):
        for chunk in entry["chunks"]:
            pairs.append((chunk["text"], chunk["vector"]))
            metadatas.append({"source": name})

    if not pairs:
        raise RuntimeError("索引仓库里没有向量，先往 docs/ 放文档再跑 ingest。")

    return FAISS.from_embeddings(pairs, embeddings, metadatas=metadatas)


def save_index(vectorstore):
    """把索引落盘到 .index/ 目录。"""
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(INDEX_DIR))


def load_index(embeddings):
    """从 .index/ 目录读回索引。"""
    return FAISS.load_local(
        str(INDEX_DIR),
        embeddings,
        allow_dangerous_deserialization=True,
    )


# ---------- 提问 ----------

class RAGResult(BaseModel):
    """结构化输出：答案 + 依据片段。"""
    answer: str = Field(description="基于资料的回答")
    sources: List[str] = Field(description="回答所依据的原文片段，每条标明来源文件名")


RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "你是一个严谨的助手，只根据提供的资料回答；资料里没有就回答不知道。"
               "sources 里填你依据的原文片段，并标明来源文件名。"),
    ("user", "资料：\n{context}\n\n问题：{question}"),
])


def build_model():
    """创建对话模型（DeepSeek，OpenAI 兼容接口）。"""
    return ChatOpenAI(
        model="deepseek-chat",
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        base_url="https://api.deepseek.com",
    )


def format_docs(documents):
    """把检索到的 Document 拼成带来源的上下文文本。"""
    return "\n\n".join(
        f"[来源：{d.metadata.get('source')}]\n{d.page_content}"
        for d in documents
    )


def answer_question(vectorstore, question, k=4):
    """检索 → 拼上下文 → 基于资料回答，返回 RAGResult。"""
    documents = vectorstore.similarity_search(question, k=k)
    model = build_model()
    chain = RAG_PROMPT | model.with_structured_output(RAGResult)
    return chain.invoke({"context": format_docs(documents), "question": question})


# ---------- 自检：跑两次，看"本次嵌入了几块" ----------

if __name__ == "__main__":
    MODEL_NAME, CHUNK_SIZE, CHUNK_OVERLAP = "text-embedding-v3", 100, 20
    params = ingest_params(MODEL_NAME, CHUNK_SIZE, CHUNK_OVERLAP)

    fingerprints = scan_docs()
    store = load_store()
    plan = plan_changes(store, fingerprints, params)

    print("需要重新嵌入：", plan["changed"] or "（无）")
    print("未变、可复用：", plan["unchanged"] or "（无）")
    print("已删除：", plan["deleted"] or "（无）")

    reused = count_chunks(store, plan["unchanged"])

    embeddings = build_embeddings()
    store = update_store(store, plan, fingerprints, embeddings, CHUNK_SIZE, CHUNK_OVERLAP)
    embedded = count_chunks(store, plan["changed"])

    store["params"] = params
    save_store(store)
    print("本次嵌入块数：", embedded, "| 复用已有向量块数：", reused)

    vectorstore = build_index_from_store(store, embeddings)
    save_index(vectorstore)
    print("索引已重建，总块数：", len(vectorstore.index_to_docstore_id))