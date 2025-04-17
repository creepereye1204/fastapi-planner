.PHONY: run
run:
	poetry run uvicorn src.main:app --reload