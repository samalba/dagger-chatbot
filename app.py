#!/usr/bin/env python
import os

import langchain
from langchain import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.vectorstores import Chroma
#from langchain.chat_models import ChatOpenAI
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.llms import LlamaCpp
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler


MODEL_PATH = "./assets/model/llama-2-7b-chat.ggmlv3.q4_0.bin"

#MODEL_PATH = "./assets/model/luna-ai-llama2-uncensored.ggmlv3.q4_0.bin"
#MODEL_PATH = "./assets/model/stable-platypus2-13b.ggmlv3.q4_0.bin"

#MODEL_PATH = "./assets/model/codeup-llama-2-13b-chat-hf.ggmlv3.q4_0.bin" # meh
#MODEL_PATH = "./assets/model/llama-2-13b-chat.ggmlv3.q4_0.bin"
#MODEL_PATH= "./assets/model/llama2_7b_chat_uncensored.ggmlv3.q4_0.bin" # meh



def init_llama_cpp():
    # llm = ChatOpenAI(verbose=bool(os.environ.get("DEBUG")))

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
    llm.client.verbose = bool(os.environ.get("DEBUG"))

    return llm


def prompt_template():
    #FIXME: improve initial context
    template = """Answer the questions based on the context below. If the question cannot be answered
    using the information provided answer with "I don't know". Don't include new questions in your answers.

    Context: {context}

    Question: {question}

    Answer: """

    return PromptTemplate(template=template, input_variables=["context", "question"])


if __name__ == "__main__":
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
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

    debug = bool(os.environ.get("DEBUG"))
    langchain.debug = debug
    qa.verbose = debug

    print("\033c\033[3J", end='')
    print(f"Using model: {MODEL_PATH}")
    query = input("Ask me anything about Dagger: ")
    result = qa.run(query)
