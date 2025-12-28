.PHONY: test lint ci

test:
	@if command -v bats >/dev/null 2>&1; then \
		bats test/feature-install.bats; \
	else \
		echo "bats not found; running test/run.sh instead."; \
		bash test/run.sh; \
	fi

lint:
	@command -v shellcheck >/dev/null 2>&1 || { \
		echo "shellcheck not found. Install shellcheck to run lint."; \
		exit 127; \
	}
	shellcheck feature-install install-feature-cli.sh \
		test/run.sh test/test_helper.bash \
		test/fixtures/*/install.sh

ci: lint test
