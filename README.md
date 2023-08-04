# dagger-chatbot

Chatbot that understands Dagger pipelines

## How to

The code is not ready to run outside of my dev env...

Few notes:

- Download the llamma-2 weights (optimized for chat, quantized on 4 bits) - I guess it works as well with the base model, store it under `model/llama-2-7b-chat.ggmlv3.q4_0.bin`
- Grab [the cookbook from the dagger repo](https://github.com/dagger/dagger/blob/main/docs/current/742989-cookbook.md)
- Sanitize it with `python ./sanitize_cookbook.py > cookbook.md`
- Run the chat: `python ./app.py`
- Some indexing is done on the dagger repo (change the fs path to the proper cloned location), in particular the changelog

Next:

- Everything will be portable and init with a dagger pipeline
