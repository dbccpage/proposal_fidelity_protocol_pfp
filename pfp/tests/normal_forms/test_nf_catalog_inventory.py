"""The education catalogue's contract register is generated from the contracts and cannot drift."""

from pfp.infrastructure.normal_forms import catalog_inventory as inventory


def test_the_catalogue_register_matches_the_contracts():
    catalog = inventory._catalog_path()
    text = catalog.read_text(encoding="utf-8")
    assert inventory._replace(text, inventory.render(catalog)) == text
    assert "`nf.classical.3nf`" in text and "`nf.experimental.qm_classical`" in text


def test_a_hand_edited_register_is_reported_as_drift(tmp_path, monkeypatch):
    catalog = inventory._catalog_path()
    copy = tmp_path / "014_normal_forms" / "catalog.md"
    copy.parent.mkdir()
    copy.write_text(catalog.read_text(encoding="utf-8").replace("`active`", "`draft`", 1), encoding="utf-8")
    monkeypatch.setattr(inventory, "_catalog_path", lambda: copy)
    assert inventory.main(["--check"]) == 1
    assert inventory.main(["--write"]) == 0 and inventory.main(["--check"]) == 0
