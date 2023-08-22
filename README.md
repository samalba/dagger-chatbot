# dagger-chatbot

Chatbot that understands Dagger pipelines

## Install dependencies

First, install the local python dependencies.

Run the following commands in a shell:

```shell
python3 -m venv venv && source ./venv/bin/activate
pip install -r requirements.txt
```

Then you need to make sure you have [Ollama](https://ollama.ai/) up and running.

If you're not using the MacOS app and you built from the binary, open a shell and run the following command:

```shell
ollama serve
```

## Generate assets

Several assets are needed for the chatbot to run:

- Fetch the documentation markdown files from the Dagger git repository
- Sanitize them (strip useless characters), split them into documents
- Tokenize the documents using an embedding model
- Store the tokenized documents into vector db (Chroma)

How to generate the assets:

```shell
dagger run ./dagger_pipeline.py
```

## Run the chatbot

Example:

```shell
./app.py
Ask me anything about Dagger: How to integrate Dagger with Github actions?
```
