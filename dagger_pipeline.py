#!/usr/bin/env python
import sys
import anyio

import dagger


def sanitize_documents(client: dagger.Client) -> dagger.Directory:
    # Dagger git repository
    dagger_repository = client.git("https://github.com/dagger/dagger.git").branch("main").tree()

    directory = (
        client.container()
        .from_("python:3.11-slim-buster")
        .with_directory("/out", client.directory())
        .with_mounted_file("/app/app.py", client.host().file("./scripts/sanitize_markdown.py"))
        # dagger docs
        .with_mounted_directory("/src", dagger_repository.directory("docs/current"))
        .with_workdir("/src")
        .with_exec(["python", "/app/app.py", "742989-cookbook.md", "/out/cookbook_clean.md"])
        .directory("/out")
    )

    # Add the changelog files to the sanitized docs
    docs = directory.with_directory(".", dagger_repository,
                                      include=[".changes/v*.md", "CHANGELOG.md"])

    return docs


def split_vectorize_documents(client: dagger.Client, docs: dagger.Directory) -> dagger.Directory:
    directory = (
        client.container()
        .from_("python:3.11-slim-buster")
        .with_directory("/out", client.directory())
        .with_mounted_file("/app/app.py", client.host().file("./scripts/split_vectorize_docs.py"))
        .with_mounted_file("/app/requirements.txt", client.host().file("./scripts/requirements.txt"))
        .with_directory("/docs", docs)
        .with_exec(["pip", "install", "--no-cache-dir", "-r", "/app/requirements.txt"])
        .with_workdir("/docs")
        .with_exec(["python", "/app/app.py", ".", "/out"])
        .directory("/out")
    )

    return directory


async def index_documents():
    async with dagger.Connection(dagger.Config(log_output=sys.stderr)) as client:
        documents = sanitize_documents(client)
        vectordb = split_vectorize_documents(client, documents)
        await vectordb.export("assets/vectordb")

        #TODO: download model weights from within a container + copy it to assets/model

if __name__ == "__main__":
    anyio.run(index_documents)
