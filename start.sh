#!/bin/bash

# Inject secrets from 1Password, run fetch_posts.py, then start app.py

env $(op inject -i ./.env.template | xargs) \
  python ./fetch_posts.py --write-output --output-file ./top_posters_output.json

python ./app.py
