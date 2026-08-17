#!/usr/bin/env bash
# Bash Boilerplate: https://github.com/xwmx/bash-boilerplate
set -euo pipefail # strict mode

raise() {
	# shellcheck disable=SC2059
	printf "::error::${1:-"Unexpected error occurred."}\n" "${@:2}" >&2
	exit 1
}

parse_args() {
	if ! [[ "$(declare -p args 2>/dev/null)" =~ "declare -A" ]]; then
		raise "Please declare 'local -A args' before calling parser."
	else
		local -r pattern="^--[a-zA-Z](-?[a-zA-Z0-9]+)*$"
		while (( $# ))
		do
			if ! [[ "$1" =~ $pattern ]]; then
				raise "Option '$1' does not match the format '$pattern'."
			else
				local key="${1#--}"
				shift
				if ! (( $# )) || [[ "$1" =~ $pattern ]]; then
					raise "Option '--$key' requires an argument."
				else
					local value="$1"
					shift
					# Trim leading/trailing whitespace
					value="${value#"${value%%[![:space:]]*}"}"
					value="${value%"${value##*[![:space:]]}"}"
					case "$key" in
						include|exclude)
							args["$key"]="$(tr , '\n' <<< "$value" \
								| sed 's|^[[:space:]]*||;s|[[:space:]]*$||;s|^\(\./\)\?|\./|' \
								| grep -v '^$' \
								|| true)"
							;;
						co-authors|any|all|required)
							args["$key"]="$(tr , '\n' <<< "$value" \
								| sed 's|^[[:space:]]*||;s|[[:space:]]*$||' \
								| grep -v '^$' \
								|| true)"
							;;
						*-folder)
							if [[ "$value" =~ ((^|/)/|(/|\.)\.+(/|$)) ]]; then
								raise "Refusing to operate on root path or parent directory reference."
							elif [[ "${value:-.}" =~ ^./?$ ]]; then
								args["$key"]="."
							elif [[ "$value" != ./* ]]; then
								args["$key"]="./${value%/}"
							else
								args["$key"]="${value%/}"
							fi
							;;
						*)
							args["$key"]="${value:?}"
							;;
					esac
				fi
			fi
		done
	fi
}

generate_files() {
	if ! type -P uv >/dev/null 2>&1; then
		raise "UV is not installed."
	else
		sudo apt-get install -y -qq -o=Dpkg::Use-Pty=0 gettext
		uv sync --frozen --no-dev --no-editable
	fi

	{
		local label; label="$(uv run --no-sync python --version | tr ' ' '-')"
		echo "### :technologist: Logging"
		echo ""
		echo "![${label}](https://img.shields.io/badge/${label}-blue?logo=python&logoColor=FFDD54)"
		if [[ -n "${TAG_NAME:-}" ]] && url=$(
			gh release view "${TAG_NAME}" --json url --jq '.url' 2>/dev/null
		); then
			label="release-${TAG_NAME#v}"
			echo "[![${label}](https://img.shields.io/badge/${label}-green?logo=github&logoColor=FFFFFF)]($url)"
		else
			label="$(uv version --bump patch --bump beta --dry-run)"
			label="${label%% *}-${label##* }"
			echo "![${label}](https://img.shields.io/badge/${label}-red?logo=pypi&logoColor=FFFFFF)"
		fi
		echo "\`\`\`"
		make ENV=prod locale build | sed $'s/\033\\[[0-9;]*m//g'
		echo "\`\`\`"
	} >> "${GITHUB_STEP_SUMMARY:-/dev/null}"
}
