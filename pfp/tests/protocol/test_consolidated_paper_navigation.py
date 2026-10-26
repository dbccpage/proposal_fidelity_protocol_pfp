from pathlib import Path


def test_paper_consolidation_navigation():
    root = Path(__file__).resolve().parents[4]
    docs = root / "omega_engine_education/documentation"
    consolidated = root / "omega_engine_atlas/coda_atlas/F004_papers/001_finite_obstruction_calculus/000_pre_genesis_to_mssn/paper.md"
    assert consolidated.is_file()
    sn_dir = (docs / "002_oesn") if (docs / "002_oesn").is_dir() else (docs / "002_s_n")
    sn = sn_dir / "papers"
    mssn_dir = (docs / "003_oemssn") if (docs / "003_oemssn").is_dir() else (docs / "003_minimal_symbol_system_n_mssn")
    mssn = mssn_dir / "papers"
    for directory in (sn, mssn):
        assert directory.is_dir()
        assert (directory / "README.md").is_file()
    for retired in (sn / "000_sn", mssn / "000_mssn", mssn / "001_pregenesis_through_mssn"):
        assert not retired.exists()
