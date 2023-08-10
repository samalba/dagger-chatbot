#!/usr/bin/env python
import os

import langchain
from langchain import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.vectorstores import Chroma
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.llms import LlamaCpp
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler


MODEL_PATH = "./assets/model/llama-2-7b-chat.ggmlv3.q4_0.bin"


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
    )

    if os.environ.get("DEBUG"):
        llm.verbose = True

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
    embeddings = HuggingFaceEmbeddings()
    store = Chroma(embedding_function=embeddings, persist_directory="assets/vectordb")

    # experiments with the memory to handle a conversation
    # from langchain.memory import ConversationBufferMemory
    # memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    qa = RetrievalQA.from_chain_type(llm=init_llama_cpp(),
                                     chain_type="stuff",
                                     retriever=store.as_retriever(),
                                     chain_type_kwargs={"prompt": prompt_template()},
                                    #  memory=memory,
                                    )

    if os.environ.get("DEBUG"):
        langchain.debug = True
        qa.verbose = True

    while True:
        query = input("> ")
        result = qa.run(query)
        print(f"Answer: {result}")
