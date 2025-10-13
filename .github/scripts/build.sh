#!/usr/bin/env bash
source "$(dirname "${BASH_SOURCE[0]}")/common.sh"

fn() {
	generate_files "${TARGET_DIRECTORY:?}"
}

fn