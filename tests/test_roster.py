from ingest.roster import RosterIngestor

INGESTOR = RosterIngestor()


def test_parses_all_roster_entries(roster_path):
    result = INGESTOR.parse(roster_path, "run_test")
    assert len(result.characters) == 3


def test_no_dead_letters_for_clean_source(roster_path):
    result = INGESTOR.parse(roster_path, "run_test")
    assert result.dead_letters == []
    assert result.errors == 0


def test_pc_flag_is_correct_for_player_characters(roster_path):
    result = INGESTOR.parse(roster_path, "run_test")
    pcs = [c for c in result.characters if c.is_pc]
    npcs = [c for c in result.characters if not c.is_pc]
    assert len(pcs) == 2
    assert len(npcs) == 1


def test_original_source_id_is_preserved(roster_path):
    result = INGESTOR.parse(roster_path, "run_test")
    source_ids = {c.source_id for c in result.characters}
    assert "pc_01" in source_ids


def test_new_canonical_ids_are_generated(roster_path):
    result = INGESTOR.parse(roster_path, "run_test")
    for character in result.characters:
        assert character.id != character.source_id, "canonical id should differ from source id"


def test_character_ids_are_unique(roster_path):
    result = INGESTOR.parse(roster_path, "run_test")
    ids = [c.id for c in result.characters]
    assert len(ids) == len(set(ids))


def test_npc_ally_has_attacks_parsed(roster_path):
    result = INGESTOR.parse(roster_path, "run_test")
    el_tigre = next(c for c in result.characters if not c.is_pc)
    assert len(el_tigre.attacks) > 0


def test_attributes_are_integers(roster_path):
    result = INGESTOR.parse(roster_path, "run_test")
    for character in result.characters:
        for stat, value in character.attributes.items():
            assert isinstance(value, int), f"{character.name}.{stat} should be int"


def test_missing_hp_produces_dead_letter(tmp_path):
    bad = tmp_path / "roster.json"
    bad.write_text('[{"id": "x1", "name": "Broken PC", "is_pc": true, "ac": 10}]')
    result = INGESTOR.parse(bad, "run_test")
    assert result.errors == 1
    assert len(result.dead_letters) == 1
