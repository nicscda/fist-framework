#!/usr/bin/env bash
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

fn() {
	if ! type -P gh >/dev/null 2>&1; then
		raise "GitHub CLI is not installed."
	fi

	local -A args
	parse_args "$@"
	# Do not modify 'args' after this point!

	local -r pem=$(mktemp)
	trap '{ rm -rf -- '"$pem"'; }' EXIT
	printf '%s\n' "${args[private-key]:-"${PRIVATE_KEY:?}"}" > "$pem"
	dos2unix "$pem" 2>/dev/null || sed -i 's|\r$||' "$pem"

	# 1. Generate JWT
	echo "::notice::Token validity 10min - leave 60s buffer for clock skew, etc."
	local -r now=$(date +%s)
	local -r exp=$((now + 540))
	local -r header_payload="$(
		printf '{"alg":"RS256","typ":"JWT"}' \
		| openssl base64 -A \
		| tr '+/' '-_' \
		| tr -d '='
	).$(
		printf '{"iat":%d,"exp":%d,"iss":"%s"}' "$now" "$exp" "${args[app-id]:-"${APP_ID:?}"}" \
		| openssl base64 -A \
		| tr '+/' '-_' \
		| tr -d '='
	)"
	local -r jwt="${header_payload}.$(
		printf '%s' "$header_payload" \
		| openssl dgst -sha256 -sign "$pem" \
		| openssl base64 -A \
		| tr '+/' '-_' \
		| tr -d '='
	)"

	# 2. Get installation ID
	if ! installation_id=$(
		gh api "app/installations" \
			--header "Authorization: Bearer $jwt" \
			--jq 'first.id // empty'
	) || [[ -z "$installation_id" ]]; then
		raise "Failed to get installation ID. Check your app ID and private key."
	fi

	# 3. Get installation access token
	if ! access_token=$(
		gh api "app/installations/$installation_id/access_tokens" \
			--header "Authorization: Bearer $jwt" \
			--method POST \
			--jq '.token // empty'
	) || [[ -z "$access_token" ]]; then
		raise "Failed to get installation access token."
	fi

	echo "token=$access_token" >> "${GITHUB_OUTPUT:-/dev/null}"
}

fn "$@"