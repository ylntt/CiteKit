"""评测脚本：跑 eval/qa_seed.jsonl，输出检索命中率 / 答案命中率 / 拒答率 / 耗时。

用法：
    python src/eval.py        # 默认 k=4
    python src/eval.py 2      # 指定 k，用来对比不同 k 的效果


"""

import json
import sys
import time

from kb import PROJECT_ROOT, answer_question, build_embeddings, load_index

EVAL_PATH = PROJECT_ROOT / "eval" / "qa_seed.jsonl"

# 判定"拒答"的粗规则：答案里出现这些词，认为它承认"资料里没有"。
# 局限：规则粗糙（正经答案里也可能出现"没有"），生产环境通常让另一个模型当裁判。
REFUSAL_MARKERS = ("不知道", "未包含", "未提及", "无法回答", "资料中没有", "没有关于", "没有提到")


def load_cases():
    """读出评测用例（一行一个 JSON）。"""
    cases = []
    for line in EVAL_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            cases.append(json.loads(line))
    return cases


def hit_sources(vectorstore, question, k):
    """检索前 k 块，返回它们的来源文件名列表。"""
    hits = vectorstore.similarity_search(question, k=k)
    return [hit.metadata.get("source", "") for hit in hits]


def main():
    k = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    cases = load_cases()

    embeddings = build_embeddings()
    vectorstore = load_index(embeddings)

    answerable = [case for case in cases if not case.get("expect_refuse")]
    refusable = [case for case in cases if case.get("expect_refuse")]

    retrieved_ok = 0
    answered_ok = 0
    refused_ok = 0
    total_seconds = 0.0

    print(f"用例 {len(cases)} 条（可答 {len(answerable)}｜应拒答 {len(refusable)}），k={k}")
    print("-" * 76)

    for case in cases:
        started = time.perf_counter()
        sources = hit_sources(vectorstore, case["question"], k)
        result = answer_question(vectorstore, case["question"], k=k)
        elapsed = time.perf_counter() - started
        total_seconds += elapsed

        answer_text = result.answer

        if case.get("expect_refuse"):
            refused = any(marker in answer_text for marker in REFUSAL_MARKERS)
            refused_ok += int(refused)
            mark = "✅" if refused else "❌"
            note = "已拒答" if refused else "没拒答（可能编造）"
        else:
            retrieved = case.get("expect_source", "") in sources
            keywords = case.get("expect_contains", [])
            matched = [word for word in keywords if word in answer_text]
            retrieved_ok += int(retrieved)
            answered_ok += 1 if (retrieved and matched) else 0
            mark = "✅" if (retrieved and matched) else "❌"
            note = f"检索{'命中' if retrieved else '未命中'}｜关键词 {len(matched)}/{len(keywords)}"

        print(f"{mark} #{case['id']:>2}  {case['question'][:24]:<24}  {note}  ({elapsed:.1f}s)")

    print("-" * 76)
    if answerable:
        print(f"检索命中率 Recall@{k}：{retrieved_ok}/{len(answerable)} = {retrieved_ok / len(answerable):.0%}")
        print(f"答案正确率（检索命中且关键词命中）：{answered_ok}/{len(answerable)} = {answered_ok / len(answerable):.0%}")
    if refusable:
        print(f"拒答正确率：{refused_ok}/{len(refusable)} = {refused_ok / len(refusable):.0%}")
    print(f"平均耗时：{total_seconds / len(cases):.1f} 秒/条")


if __name__ == "__main__":
    main()