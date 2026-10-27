if python -c 'import subprocess, sys; from operations.use_cases.cicd.pr_fast_gate import provider_contract_change; files = subprocess.check_output(["git", "diff", "--name-only", sys.argv[1] + "...HEAD"], text=True).splitlines(); sys.exit(0 if provider_contract_change(files) or any(p.startswith(("adversary/", "engine/crates_rs/core_symbol_game/")) for p in files) else 1)' "$BASE_REF"; then
  cargo build --manifest-path engine/crates_rs/Cargo.toml --locked -p core_symbol_game -j1
  echo "CORE_SYMBOL_GAME_HOST=$GITHUB_WORKSPACE/engine/crates_rs/target/debug/core_symbol_game" >> "$GITHUB_ENV"
fi
