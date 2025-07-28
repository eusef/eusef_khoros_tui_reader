# Installation

	1. python -m venv .venv && pip install -r requirements.txt

# To run using 1Password CLI

If you just want to run individually
	env $(op inject -i ./.env.template | xargs) python ./auth.py

To generate the post data for the viewer
	$(op inject -i ./.env.template | xargs) python ./get_top_posters.py --write-output --output-file=top_posters_output.jso

To run the viewer
	python ./app.py