.PHONY: help install serve clean

help: ## Show this help message
	@echo "Football API Service"
	@echo "==================="
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip3 install -r requirements.txt --break-system-packages

serve: ## Start the API server
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

clean: ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

# Development commands
format: ## Format code with black
	black backend/ app/

lint: ## Lint code with flake8
	flake8 backend/ app/
