#!/usr/bin/env python
import os
import sys
import anyio

import dagger


def sanitize_documents(client: dagger.Client) -> dagger.Directory:
    # Dagger git repository
    dagger_repository = client.git("https://github.com/dagger/dagger.git").branch("main").tree()

    directory = (
        client.container()
        .from_("python:3.11-slim-bookworm")
        .with_directory("/out", client.directory())
        .with_mounted_file("/app/app.py", client.host().file("./scripts/sanitize_markdown.py"))
        # dagger docs
        .with_mounted_directory("/src", dagger_repository.directory("docs/current"))
        .with_workdir("/src")
        .with_exec(["python", "/app/app.py", "cookbook.md", "/out/cookbook_clean.md"])
        .directory("/out")
    )

    # Add other files we want to index
    docs = directory.with_directory(".", dagger_repository,
                                    include=[
                                        ".changes/v*.md",
                                        "CHANGELOG.md",
                                        "docs/current/index.md",
                                        "docs/current/faq.md",
                                        ])

    return docs


def split_vectorize_documents(client: dagger.Client, docs: dagger.Directory) -> dagger.Directory:
    directory = (
        client.container()
        .from_("python:3.11-slim-bookworm")
        .with_directory("/out", client.directory())
        .with_mounted_file("/app/app.py", client.host().file("./scripts/split_vectorize_docs.py"))
        .with_mounted_file("/app/requirements.txt", client.host().file("./scripts/requirements.txt"))
        # mount docs from the dagger repository fetched previously
        .with_directory("/docs", docs)
        # configure cache volume for transformers and pip
        .with_mounted_cache("/cache", client.cache_volume("python3-pip"))
        .with_env_variable("TRANSFORMERS_CACHE", "/cache/hub")
        .with_env_variable("XDG_CACHE_HOME", "/cache")
        # install system dependencies for building python libraries
        .with_exec(["sh", "-c", "apt-get update && apt-get install -y build-essential sqlite3 && rm -rf /var/lib/apt/lists/*"])
        # install python dependencies
        .with_exec(["pip", "install", "-r", "/app/requirements.txt"])
        .with_exec(["python", "/app/app.py", "/docs", "/out"])
        .directory("/out")
    )

    return directory


# def fetch_model(client: dagger.Client) -> dagger.Directory:
#     filename = "llama-2-7b-chat.ggmlv3.q4_0.bin"
#     model_file = client.http(f"https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGML/resolve/main/{filename}")
#     model_filepath = os.path.join(f"assets/model/{filename}")

#     if os.path.exists(model_filepath):
#         print(f"Skipping model file download, use the one found at: {model_filepath}")
#         return client.directory()

#     directory = (
#         client.directory()
#         .with_file(path=filename, source=model_file)
#     )

#     return directory


def initialize_ollama(client: dagger.Client):
    ollama_repository = client.git("https://github.com/jmorganca/ollama.git").branch("main").tree()
    ollama = ollama_repository.docker_build()
    ollama.with_exec(["pull", "llama2"])


async def generate_assets():
    async with dagger.Connection(dagger.Config(log_output=sys.stderr)) as client:
        documents = sanitize_documents(client)
        vectordb = split_vectorize_documents(client, documents)

        async with anyio.create_task_group() as tg:
            tg.start_soon(vectordb.export, "assets/vectordb")
            #tg.start_soon(model_file.export, "assets/model")


if __name__ == "__main__":
    anyio.run(generate_assets)
