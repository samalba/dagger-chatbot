# dagger-chatbot

Chatbot that understands Dagger pipelines

## Generate assets

Several assets are needed for the chatbot to run:

- Split and tokenize the dagger docs from the git repository
- Vectorize them in a vector db (Chroma)
- Fetch the llama-2 model file

How to generate the assets:

```shell
./dagger_pipeline.py
```

## Install the local python dependencies

Run the following commands in a shell:

```shell
python3 -m venv
CMAKE_ARGS="-DLLAMA_METAL=on" FORCE_CMAKE=1 pip install llama-cpp-python
pip install -r requirements.txt
```

## Run the chatbot

```shell
./app.py
```
