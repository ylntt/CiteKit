"""建索引：扫描 docs/ → 只对变更文件重新向量化 → 重建索引并落盘。"""

from kb import (
    INDEX_DIR,
    build_embeddings,
    build_index_from_store,
    count_chunks,
    ingest_params,
    load_store,
    plan_changes,
    save_index,
    save_store,
    scan_docs,
    update_store,
)

MODEL_NAME = "text-embedding-v3"
CHUNK_SIZE = 100
CHUNK_OVERLAP = 20


def main():
    params = ingest_params(MODEL_NAME, CHUNK_SIZE, CHUNK_OVERLAP)

    fingerprints = scan_docs()
    print(f"扫描到 {len(fingerprints)} 个文档")
    if not fingerprints:
        print("docs/ 里没有可读的文档（支持 .md / .txt），先放几个文件进来。")
        return

    store = load_store()
    plan = plan_changes(store, fingerprints, params)
    print("需要重新嵌入：", plan["changed"] or "（无）")
    print("复用已有向量：", plan["unchanged"] or "（无）")
    if plan["deleted"]:
        print("已删除：", plan["deleted"])

    reused = count_chunks(store, plan["unchanged"])

    embeddings = build_embeddings()
    store = update_store(store, plan, fingerprints, embeddings, CHUNK_SIZE, CHUNK_OVERLAP)
    embedded = count_chunks(store, plan["changed"])

    store["params"] = params
    save_store(store)
    print(f"本次嵌入 {embedded} 块，复用 {reused} 块")

    vectorstore = build_index_from_store(store, embeddings)
    save_index(vectorstore)
    print("索引已落盘到：", INDEX_DIR)


if __name__ == "__main__":
    main()