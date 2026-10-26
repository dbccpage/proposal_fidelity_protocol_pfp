if python -c 'import subprocess, sys; from omega_engine_operations.use_cases.cicd.pr_fast_gate import provider_contract_change; files = subprocess.check_output(["git", "diff", "--name-only", sys.argv[1] + "...HEAD"], text=True).splitlines(); sys.exit(0 if provider_contract_change(files) or any(p.startswith(("omega_engine_woland/", "omega_engine/crates_rs/omega_symbol_game/")) for p in files) else 1)' "$BASE_REF"; then
  cargo build --manifest-path omega_engine/crates_rs/Cargo.toml --locked -p omega_symbol_game -j1
  echo "OMEGA_SYMBOL_GAME_HOST=$GITHUB_WORKSPACE/omega_engine/crates_rs/target/debug/omega_symbol_game" >> "$GITHUB_ENV"
fi
