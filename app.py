import os

from langchain.document_loaders import DirectoryLoader, UnstructuredHTMLLoader, UnstructuredMarkdownLoader

from langchain import PromptTemplate

from langchain.chains import RetrievalQA
# from langchain.embeddings.openai import OpenAIEmbeddings
# from langchain.llms import OpenAI
# from langchain.chat_models import ChatOpenAI
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma

from langchain.llms import LlamaCpp
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

from langchain.embeddings import HuggingFaceEmbeddings #, SentenceTransformerEmbeddings
# from langchain.embeddings import LlamaCppEmbeddings

import langchain; langchain.debug = True

#NOTE: install: CMAKE_ARGS="-DLLAMA_METAL=on" FORCE_CMAKE=1 pip install llama-cpp-python
MODEL_PATH = "./model/llama-2-7b-chat.ggmlv3.q4_0.bin"

def index():
    #TODO: separate the indexing so it can happen only once if needed
    # daggerize the index via git clone + chromadb + fetch llama2 ggml
    #TODO: sanitize output to properly map code snippet to markdown text (embed code inline)
    #TODO: strip the markdown from useless chars
    #TODO: experiment with LoRa fine-tuning instead of prompt composition (llama, lora_path arg)

    texts = []

    loader = UnstructuredMarkdownLoader("./cookbook.md")
    documents = loader.load()
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts.extend(text_splitter.split_documents(documents))

    def index_documents(path, glob):
        loader = DirectoryLoader(path, glob=glob, show_progress=True)
        # loader = UnstructuredHTMLLoader("/Users/shad/Downloads/Cookbook Dagger.html", mode="single")
        documents = loader.load()
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        texts.extend(text_splitter.split_documents(documents))

    # # loader = DirectoryLoader("/Users/shad/websites/dagger-docs/docs.dagger.io", glob="**/*.html")
    # index_documents("/Users/shad/forks/dagger/docs/current", "**/*.md")
    # index_documents("/Users/shad/forks/dagger/docs/current", "**/*.py")
    # index_documents("/Users/shad/forks/dagger/docs/current", "**/*.go")
    index_documents("/Users/shad/forks/dagger/docs/current", "*-index.md")
    index_documents("/Users/shad/forks/dagger", "CHANGELOG.md")
    index_documents("/Users/shad/forks/dagger/.changes", "v*.md")

    # embeddings = OpenAIEmbeddings()
    #FIXME: llamacpp embeddings is super slow
    # embeddings = LlamaCppEmbeddings(model_path=MODEL_PATH)
    embeddings = HuggingFaceEmbeddings()
    vectore_store = Chroma.from_documents(texts, embeddings)
    return vectore_store


def init_llama_cpp():
    # llm = ChatOpenAI()

    callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
    llm = LlamaCpp(
        model_path=MODEL_PATH,
        n_gpu_layers=1,
        n_batch=512,
        n_ctx=2048,
        use_mlock=False,
        use_mmap=True,
        f16_kv=True,
        temperature=0.8,
        n_threads=os.cpu_count(),
        callback_manager=callback_manager,

#        echo=True,
        verbose=True,
    )

    return llm


def prompt_template():
    #FIXME: improve initial context
    template = """Answer the questions based on the context below. If the question cannot be answered
    using the information provided answer with "I don't know".

    Context: {context}

    Question: {question}

    Answer: """

    return PromptTemplate(template=template, input_variables=["context", "question"])




if __name__ == "__main__":
    store = index()

    qa = RetrievalQA.from_chain_type(llm=init_llama_cpp(),
                                     chain_type="stuff",
                                     retriever=store.as_retriever(),
                                     chain_type_kwargs={"prompt": prompt_template()},
                                     verbose=True)
#                                     return_source_documents=True)

    # out = chain({"query": question})
    # result = out.get("result")

    while True:
        query = input("> ")
        result = qa.run(query)
        print(f"Answer: {result}")

    # import pprint
    # pp = pprint.PrettyPrinter(indent=4)
    # pp.pprint(out)
