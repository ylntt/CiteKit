from kb import (
    INDEX_DIR,
    build_embeddings,
    build_index,
    load_documents,
    save_index,
    split_documents,
)

def main():
    documents = load_documents()
    print(f"读取了{len(documents)}个文档")
    if not documents:
        print("docs/ 里没有可读的文档（支持 .md / .txt），先放几个文件进来。")
        return
    chunks = split_documents(documents)
    print("切出的块数",len(chunks))

    embeddings = build_embeddings()
    vectorstore = build_index(chunks,embeddings)
    save_index(vectorstore)
    print("索引已落盘到：", INDEX_DIR)


if __name__ == "__main__":
    main()