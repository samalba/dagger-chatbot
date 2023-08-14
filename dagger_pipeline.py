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


async def split_vectorize_documents(client: dagger.Client):
    docs = sanitize_documents(client)

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

    return directory.export("assets/vectordb")


#FIXME: ollama currently does not support external hosts
# async def fetch_ollama_models(client: dagger.Client):
#     ollama_repository = client.git("https://github.com/jmorganca/ollama.git").branch("main").tree()

#     ollama_binary = (
#         client.container().from_("golang:1.20")
#         .with_workdir("/go/src/github.com/jmorganca/ollama")
#         .with_directory(".", ollama_repository)
#         .with_exec(["sh", "-c", "CGO_ENABLED=1 go build -ldflags '-linkmode external -extldflags \"-static\"' ."])
#         .file("ollama")
#     )

#     ollama_models = client.cache_volume("ollama-models")

#     ollama_models_local_path = os.path.expanduser(os.path.join("~", ".ollama", "models"))
#     ollama_server = (
#         client.container().from_("alpine")
#         .with_file("/bin/ollama", ollama_binary, 0o555)
#         .with_env_variable("OLLAMA_HOST", "0.0.0.0")
#         .with_mounted_cache("/root/.ollama/models", ollama_models)
#         .with_exec(["/bin/ollama", "serve"])
#         .with_exposed_port(11434)
#     )

#     ollama_client = (
#         client.container().from_("alpine")
#         .with_file("/bin/ollama", ollama_binary, 0o555)
#         .with_service_binding("ollama-server", ollama_server)
#         .with_env_variable("OLLAMA_HOST", "ollama-server")
#         .with_exec(["/bin/ollama", "pull", "llama2"])
#     )

#     await ollama_client.sync()

#     return (
#         client.container().from_("alpine")
#         .with_mounted_cache("ollama_models", ollama_models)
#         .directory("ollama_models")
#         .export(ollama_models_local_path)
#     )


async def generate_assets():
    async with dagger.Connection(dagger.Config(log_output=sys.stderr)) as client:
        async with anyio.create_task_group() as tg:
            tg.start_soon(split_vectorize_documents, client)
            #tg.start_soon(fetch_ollama_models, client)


if __name__ == "__main__":
    anyio.run(generate_assets)
