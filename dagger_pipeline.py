#!/usr/bin/env python
import sys
import anyio

import dagger


def sanitize_documents(client: dagger.Client) -> dagger.Directory:
    # Dagger git repository
    dagger_repository = client.git("https://github.com/dagger/dagger.git").branch("main").tree()

    # Create a new directory with only the files we need from the repository
    dir = client.directory()
    dir = dir.with_directory(".", dagger_repository,
                                    include=[
                                        ".changes/v*.md",
                                        "CHANGELOG.md",
                                        ]
                                    )
    dir = dir.with_directory(".", dagger_repository.directory("docs/current"), exclude=["sdk/cue"])

    docs = (
        client.container()
        .from_("python:3.11-slim-bookworm")
        .with_mounted_file("/app/app.py", client.host().file("./scripts/sanitize_markdown.py"))
        # dagger docs
        .with_mounted_directory("/docs", dir)
        .with_workdir("/docs")
        .with_exec(["sh", "-c", "find /docs \\( -name '*.md' \\) -exec python /app/app.py {} \\;"])
        .directory("/docs")
    )

    return docs


def split_vectorize_documents(client: dagger.Client):
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


async def generate_assets():
    async with dagger.Connection(dagger.Config(log_output=sys.stderr)) as client:
        await split_vectorize_documents(client)


if __name__ == "__main__":
    anyio.run(generate_assets)
