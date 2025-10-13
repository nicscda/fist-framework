#!/usr/bin/env bash
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

fn() {
	if ! type -P gh >/dev/null 2>&1; then
		raise "GitHub CLI is not installed."
	fi

	local -r command="${1:-}"
	shift

	local -A args
	parse_args "$@"
	# Do not modify 'args' after this point!

	case "$command" in
		title)
			if [[ "$GITHUB_HEAD_REF" =~ ^(release-please|dependabot).* ]]; then
				echo "mode=squash" >> "${GITHUB_OUTPUT:-/dev/null}"
				if [[ "$GITHUB_ACTOR" != *'[bot]' ]]; then
					gh pr edit "${args[pr-number]}" \
						--title "$(gh pr view "${args[pr-number]}" \
						--json commits --jq '.commits | first | .messageHeadline')"
					echo "::warning::Do not change the title of PRs created by a bot."
				fi
			elif ! pattern=$(
				gh api "repos/${args[repository]}/rules/branches/$GITHUB_HEAD_REF" \
					--jq 'first(.[] | select(.type == "commit_message_pattern")) | .parameters.pattern'
			); then
				echo "::warning::Cannot get commit message pattern."
			elif ! grep -Pq "$pattern" <<< "$TITLE"; then
				gh pr edit "${args[pr-number]}" \
					--title "chore: :twisted_rightwards_arrows: merge branch $GITHUB_HEAD_REF into $GITHUB_BASE_REF"
				echo "::warning::PR title should match the pattern: '${pattern%%\(\\n*}$'"
				echo "mode=default" >> "${GITHUB_OUTPUT:-/dev/null}"
			else
				echo "mode=squash" >> "${GITHUB_OUTPUT:-/dev/null}"
			fi
			# Re-enable to trigger auto-merge with new inputs
			if enabled_at=$(
				gh pr view "${args[pr-number]}" \
					--repo "${args[repository]}" \
					--json 'autoMergeRequest' \
					--jq '.autoMergeRequest.enabledAt // empty'
			) && [[ -n "$enabled_at" ]]; then
				gh pr merge "${args[pr-number]}" \
					--repo "${args[repository]}" \
					--disable-auto
			fi
			;;
		body)
			# 0. Fetch current PR body
			local -r body="$(gh api "repos/${args[repository]}/pulls/${args[pr-number]}" --jq '.body')"

			# 1. Fetch language code from template comment
			local -r lang="$(
				awk '/<!--/,/-->/ {
					block = block $0 "\n"
					if (/-->/) {
					if (match(block, /LANG:[[:space:]]*([[:alpha:]_]+)/, m)) {
						print m[1]
						exit
					}
					}
				}' <<< "${body:?}"
			)"
			local -A messages=(
				[title]="Section Review"
				[col1]="Section"
				[col2]="Status"
				[col3]="Note"
				[success]="Passed"
				[error-type-missing]="Missing"
				[error-type-missing-all]="Missing all required sections"
				[error-type-missing-item]="Missing items"
				[error-type-missing-option]="Missing options"
				[error-type-required]="Cannot be empty"
				[error-type-any]="At least one must be selected"
				[error-type-all]="%s item(s) remaining"
			)
			if [[ "$lang" == zh_TW ]]; then
				messages=(
					[title]="驗證結果"
					[col1]="區塊"
					[col2]="狀態"
					[col3]="備註"
					[success]="通過"
					[error-type-missing]="缺少此區塊"
					[error-type-missing-all]="缺少所有必要區塊"
					[error-type-missing-item]="項目遺失"
					[error-type-missing-option]="選項遺失"
					[error-type-required]="不可空白"
					[error-type-any]="至少需選擇 1 項"
					[error-type-all]="尚有 %s 項未完成"
				)
			fi

			# 2. Run a cycle checking
			local -A matrix=(
				[1]="Description|說明"
				[1.type]="required"
				[2]="Type of change|變更類型"
				[2.type]="any"
				[3]="How Has This Been Tested?|驗證測試"
				[3.type]="required"
				[4]="Checklist|自我檢核"
				[4.type]="all"
			)
			local -i errors=0
			local -a rows=()
			local template='{{tablerow "ID" "Node ID" "State" "Context"}}'
			template+='{{tablerow .id .node_id .state .context}}'
			readonly template
			for i in $(seq 1 4); do
				# 2-1. Initialize local variables
				local part="" section="${matrix["${i}"]}" error_msg="" emoji=":white_check_mark:" status="success"
				# 2-2. Get the actual title of the section from the PR body
				if ! section=$(
					awk '/^## / {
						if (match($0, /('"${section/\?/\\?}"')[[:space:]]*$/, m)) {
							print m[1]
							exit
						}
					}' <<< "${body:?}"
				) || [[ -z "$section" ]]; then
					# 2-2-1. Use the default title for the section if not found
					section="${matrix["${i}"]%%|*}"; [[ "$lang" == zh_TW ]] && section="${matrix["${i}"]##*|}"
					error_msg="${messages[error-type-missing]}"
				else
					# 2-2-2. Trim leading/trailing whitespace
					section="${section#"${section%%[![:space:]]*}"}"
					section="${section%"${section##*[![:space:]]}"}"
					# 2-2-3. Remove all HTML comments and just fetch target section without title
					part="$(
						awk '/^## '"${section/\?/\\?}"'/ {flag=1; next} /^## / {flag=0} flag' <<< "${body:?}" \
						| perl -0777 -pe 's/<!--.*?-->//gs'
					)"
					# 2-2-4. Validation by section type
					case "${matrix["${i}".type]}" in
						required)
							if lines=$(
								grep -cvE '^[[:space:]]*$' <<< "$part" || true
							) && (( lines )); then
								echo "::notice::$lines non-blank line(s) in [$section] section."
							else
								error_msg="${messages[error-type-required]}"
							fi
							;;
						any)
							if ! items=$(
								grep -E '^[[:space:]]*[\*\-] +\[[ xX]\]' <<< "$part" || true
							) || [[ -z "$items" ]]; then
								error_msg="${messages[error-type-missing-option]}"
							elif checkeds=$(
								grep -cE '^[[:space:]]*[\*\-] +\[[xX]\]' <<< "$items" || true
							) && (( checkeds )); then
								echo "::notice::$checkeds option(s) made in [$section] section."
							else
								error_msg="${messages[error-type-any]}"
							fi
							;;
						all)
							if ! items=$(
								grep -E '^[[:space:]]*[\*\-] +\[[ xX]\]' <<< "$part" || true
							) || [[ -z "$items" ]]; then
								error_msg="${messages[error-type-missing-item]}"
							elif uncheckeds=$(
								grep -cE '^[[:space:]]*[\*\-] +\[[ ]\]' <<< "$items" || true
							) && (( uncheckeds )); then
								# shellcheck disable=SC2059
								error_msg="$( printf "${messages[error-type-all]}" "$uncheckeds")"
							else
								echo "::notice::All items in [$section] section have been completed."
							fi
							;;
					esac
				fi
				# 2-3. Ensure the emoji matches the status based on errors found
				if [[ -n "$error_msg" ]]; then
					(( errors+=1 ))
					emoji=":x:"
					status="failure"
				fi
				# 2-4. Map job status
				gh api "repos/${args[repository]}/statuses/${args[sha]}" \
					--method POST \
					--field state="${status}" \
					--field target_url="https://github.com/${args[repository]}/actions/runs/${args[run-id]}" \
					--field description="${section}: ${error_msg:-"${messages[success]}"}" \
					--field context="--> Checked: SECTION-${i}" \
					--template "$template"
				# 2-5. Append data row
				rows+=( "$section,$emoji,$error_msg" )
			done

			{
				echo "### :stethoscope: ${messages[title]}"
				echo ""
				if (( ${#rows[@]} )); then
					echo "| ${messages[col1]} | ${messages[col2]} | ${messages[col3]} |"
					echo "| :--- | :---: | :--- |"
					for row in "${rows[@]}"; do
						IFS=, read -ra cells <<< "$row"
						printf '| %s | %s | %s |\n' "${cells[@]}"
					done
				else
					(( errors+=1 ))
					echo "> [!WARNING]"
					echo "> ${messages[error-type-missing-all]}"
				fi
			} >> "${GITHUB_STEP_SUMMARY:-/dev/null}"

			if (( errors )); then
				{
					echo "> [!TIP]"
					case "$lang" in
						zh_TW)
							echo "> - 關於 **說明**:"
							echo ">   請簡要說明此次變更的內容、主要目的，並列出相關的追蹤議題或相依套件。"
							echo "> - 關於 **變更類型**:"
							echo ">   請至少選擇一項相關的變更類型。"
							echo "> - 關於 **驗證測試**:"
							echo ">   請簡要描述此次變更所執行的測試步驟與結果。如不適用，請填寫 _\`N/A\`_。"
							echo "> - 關於 **自我檢核**:"
							echo ">   請確認所有項目皆已完成並勾選後再送交審查。"
							;;
						*)
							echo "> - For **Description**"
							echo ">   Summarize the changes, main purpose, and list any related issues or dependencies."
							echo "> - For **Type of change**:"
							echo ">   Select at least one relevant change type."
							echo "> - For **How Has This Been Tested?**:"
							echo ">   Briefly describe your testing steps and results. If not applicable, write _\`N/A\`_."
							echo "> - For **Checklist**:"
							echo ">   Ensure all required items are checked before submitting."
							;;
					esac
				} >> "${GITHUB_STEP_SUMMARY:-/dev/null}"
				raise "Found errors when checking the sections."
			fi
			;;
		*)
			raise "No such command '$command'."
			;;
	esac
}

fn "$@"