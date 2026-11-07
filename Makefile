.PHONY: test validate drill mandate

test:
	python3 -m unittest discover -s tests -v

validate:
	python3 tools/validate_vault.py examples/low-oriole-metering --example

drill:
	python3 tools/quickstart_drill.py

mandate:
	python3 tools/init_mandate.py validate-all
