.PHONY: test lint ci

test:
\tbats test/feature-install.bats

lint:
\tshellcheck feature-install install-feature-cli.sh \\
\t\ttest/run.sh test/test_helper.bash \\
\t\ttest/fixtures/*/install.sh

ci: lint test
