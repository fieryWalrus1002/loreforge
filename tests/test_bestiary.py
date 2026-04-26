from ingest.bestiary import BestiaryIngestor

INGESTOR = BestiaryIngestor()


def test_parses_all_creatures(bestiary_path):
    result = INGESTOR.parse(bestiary_path, "run_test")
    assert len(result.creatures) == 4


def test_no_dead_letters_for_clean_source(bestiary_path):
    result = INGESTOR.parse(bestiary_path, "run_test")
    assert result.dead_letters == []
    assert result.errors == 0


def test_hd_coerced_from_string_to_int(bestiary_path):
    result = INGESTOR.parse(bestiary_path, "run_test")
    for creature in result.creatures:
        assert isinstance(creature.hd, int), f"{creature.name} hd should be int"


def test_hp_is_floor_4point5_times_hd(bestiary_path):
    import math
    result = INGESTOR.parse(bestiary_path, "run_test")
    for creature in result.creatures:
        assert creature.hp == math.floor(4.5 * creature.hd)


def test_ac_coerced_from_string_to_int(bestiary_path):
    result = INGESTOR.parse(bestiary_path, "run_test")
    for creature in result.creatures:
        assert isinstance(creature.ac, int)


def test_clanker_t_die_remapped_to_tr_die(bestiary_path):
    result = INGESTOR.parse(bestiary_path, "run_test")
    clanker = next(c for c in result.creatures if "Clanker" in c.name)
    laser = next(a for a in clanker.attacks if "Laser" in a.name)
    assert laser.tr_die is not None, "tr_die should be populated after remapping t_die"


def test_clanker_t_rate_remapped_to_tr_mult(bestiary_path):
    result = INGESTOR.parse(bestiary_path, "run_test")
    clanker = next(c for c in result.creatures if "Clanker" in c.name)
    laser = next(a for a in clanker.attacks if "Laser" in a.name)
    assert laser.tr_mult is not None, "tr_mult should be populated after remapping t_rate"


def test_creature_ids_are_unique(bestiary_path):
    result = INGESTOR.parse(bestiary_path, "run_test")
    ids = [c.id for c in result.creatures]
    assert len(ids) == len(set(ids))


def test_source_file_recorded_on_each_creature(bestiary_path):
    result = INGESTOR.parse(bestiary_path, "run_test")
    for creature in result.creatures:
        assert creature.source_file == str(bestiary_path)


def test_missing_required_field_produces_dead_letter(tmp_path):
    bad = tmp_path / "bestiary.json"
    bad.write_text('[{"name": "Broken Beast"}]')  # missing hd and ac
    result = INGESTOR.parse(bad, "run_test")
    assert result.errors == 1
    assert len(result.dead_letters) == 1
    assert "hd" in result.dead_letters[0].reason or "ac" in result.dead_letters[0].reason
