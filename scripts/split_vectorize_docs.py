import sys

from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import CharacterTextSplitter, MarkdownTextSplitter
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings


def split_vectorize_docs(input_directory, vectordb_path):
    texts = []

    loader = DirectoryLoader(input_directory, glob="**/*.md", show_progress=True)
    documents = loader.load()
    # text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    text_splitter = MarkdownTextSplitter(chunk_size=1024)
    texts.extend(text_splitter.split_documents(documents))

    # embeddings = OpenAIEmbeddings()
    #FIXME: llamacpp embeddings is super slow
    # embeddings = LlamaCppEmbeddings(model_path=MODEL_PATH)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectordb = Chroma.from_documents(texts, embeddings, persist_directory=vectordb_path)
    vectordb.persist()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} input-path output-path")
        sys.exit(1)

    input_directory = sys.argv[1]
    vectordb_path = sys.argv[2]
    split_vectorize_docs(input_directory, vectordb_path)
