import sys
from kb import answer_question,build_embeddings,load_index


def main():
    """取问题并转化为向量进行比对后回答"""
    if len(sys.argv) < 2:
        print("未传入问题")
        return
    question = sys.argv[1]
    embeddings = build_embeddings()
    vectorstore = load_index(embeddings)
    result = answer_question(vectorstore,question)
    print(result.answer)
    for i in result.sources:
        print(i)


if __name__ == "__main__":
    main()

