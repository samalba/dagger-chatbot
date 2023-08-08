#!/usr/bin/env python
import sys
import anyio

import dagger


async def index_documents():
    async with dagger.Connection(dagger.Config(log_output=sys.stderr)) as client:
        # Dagger Docs from the git repository
       dagger_docs = client.git("https://github.com/dagger/dagger.git").branch("main").tree().directory("docs/current")

       sanitizer = (
           client.container()
           .from_("python:3.11-slim-buster")
           .with_directory("/out", client.directory())
           .with_mounted_file("/app/app.py", client.host().file("./assets/sanitize_markdown.py"))
           .with_mounted_directory("/src", dagger_docs)
           .with_workdir("/src")
           .with_exec(["python", "/app/app.py", "742989-cookbook.md", "/out/cookbook_clean.md"])
           .directory("/out")
       )

       #TODO: add changelogs files
       # - dagger/CHANGELOG.md
       # - dagger/.changes/v*.md

       await sanitizer.export("assets/docs")


if __name__ == "__main__":
    anyio.run(index_documents)
