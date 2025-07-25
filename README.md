# Installation

	1. python -m venv .venv && pip install -r requirements.txt

# To run using 1Password CLI

	env $(op inject -i ./.env.template | xargs) python ./auth.py