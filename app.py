#!/usr/bin/env python
import os

import langchain
from langchain import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.vectorstores import Chroma
#from langchain.chat_models import ChatOpenAI
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.llms import Ollama
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler


def init_llm():
    debug = bool(os.environ.get("DEBUG"))

    # uncomment to use openai (requires OPENAI_API_KEY env var)
    #llm = ChatOpenAI(verbose=debug)

    llm = Ollama(
        model="llama2",
        temperature=0.7,
        verbose=debug,
        callback_manager=CallbackManager([StreamingStdOutCallbackHandler()])
    )

    return llm


def prompt_template():
    template = """Use the following pieces of context to answer the question at the end. 
If you don't know the answer, just say that you don't know, don't try to make up an answer. 
Use three sentences maximum and keep the answer as concise as possible. 
{context}
Question: {question}
Helpful Answer:"""

    return PromptTemplate(template=template, input_variables=["context", "question"])


if __name__ == "__main__":
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    store = Chroma(embedding_function=embeddings, persist_directory="assets/vectordb")

    # experiments with the memory to handle a conversation
    # from langchain.memory import ConversationBufferMemory
    # memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    qa_chain = RetrievalQA.from_chain_type(llm=init_llm(),
                                     chain_type="stuff",
                                     retriever=store.as_retriever(),
                                     chain_type_kwargs={"prompt": prompt_template()},
                                    #  memory=memory,
                                    )

    debug = bool(os.environ.get("DEBUG"))
    langchain.debug = debug
    qa_chain.verbose = debug

    # Clear screen
    # print("\033c\033[3J", end='')
    q = input("Ask me anything about Dagger: ")

    if debug:
        docs = store.similarity_search(q)
        print(f"# Found {len(docs)} relevant documents")

    qa_chain({"query": q})
    print()
