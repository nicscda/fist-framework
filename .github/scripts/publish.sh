#!/usr/bin/env bash
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

fn() {
	if ! type -P uv >/dev/null 2>&1; then
		raise "UV is not installed."
	fi

	uv build
	uv publish
	local -r host=$([[ "${UV_PUBLISH_URL:-}" == *test* ]] && echo "test.pypi.org" || echo "pypi.org")
	# uv version format: "<package-name> <version>"
	echo "pkg_url=https://${host}/project/$(uv version | awk '{print $1}')" >> "${GITHUB_OUTPUT:-/dev/null}"
}

fn
