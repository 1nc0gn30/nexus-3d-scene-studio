.PHONY: help install test test-mcp test-cli test-ui test-engine serve mcp clean format lint

PYTHON ?= python3
PYTEST ?= pytest

help:
	@echo "Nexus 3D Scene Studio - Makefile commands:"
	@echo "  make install      Install package in editable development mode"
	@echo "  make test         Run all unit test suites"
	@echo "  make test-mcp     Run MCP server unit tests"
	@echo "  make test-cli     Run CLI unit tests"
	@echo "  make test-ui      Run UI server unit tests"
	@echo "  make serve        Start Studio Web UI server on port 8092"
	@echo "  make mcp          Run Stdio MCP JSON-RPC server"
	@echo "  make clean        Remove build artifacts and cached files"

install:
	$(PYTHON) -m pip install -e .

test:
	PYTHONPATH=src $(PYTHON) -m pytest tests/ -v

test-mcp:
	PYTHONPATH=src $(PYTHON) -m pytest tests/test_mcp.py -v

test-cli:
	PYTHONPATH=src $(PYTHON) -m pytest tests/test_cli.py -v

test-ui:
	PYTHONPATH=src $(PYTHON) -m pytest tests/test_ui_server.py -v

serve:
	PYTHONPATH=src $(PYTHON) -m nexus_3d_scene_studio.ui_server --port 8092 --host 0.0.0.0

mcp:
	PYTHONPATH=src $(PYTHON) -m nexus_3d_scene_studio.mcp_server

clean:
	rm -rf build/ dist/ *.egg-info .pytest_cache .coverage htmlcov/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
