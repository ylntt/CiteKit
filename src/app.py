"""网页界面：给非技术成员用的提问页（v0.3）。

运行：
    streamlit run src/app.py
"""

import streamlit as st

from kb import INDEX_DIR, answer_question, build_embeddings, load_index, load_store

st.set_page_config(page_title="CiteKit 文档问答", page_icon="📚", layout="centered")


@st.cache_resource
def get_embeddings():
    """向量模型只建一次，避免每次交互都重新初始化。"""
    return build_embeddings()


@st.cache_resource
def get_vectorstore():
    """索引只读一次；重建索引后需要刷新页面（或点侧边栏的清除缓存）。"""
    return load_index(get_embeddings())


def main():
    st.title("📚 CiteKit · 文档问答")
    st.caption("回答只基于 docs/ 里的资料；资料里没有会直接说不知道。")

    store = load_store()
    files = store.get("files", {})
    chunk_count = sum(len(entry["chunks"]) for entry in files.values())

    with st.sidebar:
        st.subheader("索引状态")
        st.metric("文档数", len(files))
        st.metric("块数", chunk_count)
        params = store.get("params") or {}
        if params:
            st.caption("模型：" + str(params.get("model")))
            st.caption("切块：" + str(params.get("chunk_size")) + " / 重叠 " + str(params.get("chunk_overlap")))
        st.divider()
        st.caption("新增或修改文档后，在终端运行：")
        st.code("python src/ingest.py", language="bash")
        if st.button("清除缓存（重建索引后点这里）"):
            st.cache_resource.clear()
            st.rerun()
        k = st.slider("检索块数 k", 1, 10, 4)

    if not files:
        st.warning("索引是空的（" + str(INDEX_DIR) + "）。先在终端跑一次 python src/ingest.py")
        return

    question = st.text_input("你的问题", placeholder="例：口径变更要怎么走流程？")
    if not st.button("提问", type="primary"):
        return
    if not question.strip():
        st.info("先输入一个问题。")
        return

    with st.spinner("检索 + 生成中…"):
        result = answer_question(get_vectorstore(), question.strip(), k=k)

    st.markdown("### 回答")
    st.write(result.answer)

    st.markdown("### 出处")
    if result.sources:
        for source in result.sources:
            st.markdown("- " + source)
    else:
        st.caption("这次没有给出依据片段 —— 也可能说明资料里确实没有答案。")


main()