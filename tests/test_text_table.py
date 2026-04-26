import math

from ingest.text_table import TextTableIngestor

INGESTOR = TextTableIngestor()

MINIMAL_TABLE = """\
Creatures HD AC Atk Dmg TR Shock MV ML Skill Save
Test Beast 3 14 +4 1d6 bite 1d8/x2 - 15m 8 +2 14+
"""


def test_parses_all_mutated_animals(mutated_animals_path):
    result = INGESTOR.parse(mutated_animals_path, "run_test")
    assert len(result.creatures) == 10


def test_parses_all_robots(robots_path):
    result = INGESTOR.parse(robots_path, "run_test")
    assert len(result.creatures) == 10


def test_heritor_bug_fixed_hp_is_one(mutated_animals_path):
    result = INGESTOR.parse(mutated_animals_path, "run_test")
    heritor = next(c for c in result.creatures if "Heritor" in c.name)
    assert heritor.hp == 1
    assert heritor.hd == 1


def test_standard_hp_is_floor_4point5_times_hd(mutated_animals_path):
    result = INGESTOR.parse(mutated_animals_path, "run_test")
    for creature in result.creatures:
        if "Heritor" not in creature.name:
            assert creature.hp == math.floor(4.5 * creature.hd)


def test_multi_attack_parsed_from_x_notation(mutated_animals_path):
    result = INGESTOR.parse(mutated_animals_path, "run_test")
    ghoul_bear = next(c for c in result.creatures if "Ghoul Bear" in c.name)
    assert ghoul_bear.attacks[0].num_attacks == 2


def test_shock_dash_produces_null_shock(mutated_animals_path):
    result = INGESTOR.parse(mutated_animals_path, "run_test")
    blinder = next(c for c in result.creatures if "Blinder" in c.name)
    assert blinder.attacks[0].shock_dmg is None


def test_shock_value_parsed_from_n_dash_format(mutated_animals_path):
    result = INGESTOR.parse(mutated_animals_path, "run_test")
    ghoul_bear = next(c for c in result.creatures if "Ghoul Bear" in c.name)
    assert ghoul_bear.attacks[0].shock_dmg == 3


def test_two_token_shock_n_ac_m_parsed(robots_path):
    result = INGESTOR.parse(robots_path, "run_test")
    janglesnake = next(c for c in result.creatures if "Janglesnake" in c.name)
    assert janglesnake.attacks[0].shock_dmg == 5
    assert janglesnake.attacks[0].shock_ac == 15


def test_bare_die_tr_normalized(robots_path):
    result = INGESTOR.parse(robots_path, "run_test")
    brainbot = next(c for c in result.creatures if "Brainbot" in c.name)
    assert brainbot.attacks[0].tr_die == "1d8"


def test_asterisk_annotation_stripped_from_atk(robots_path):
    result = INGESTOR.parse(robots_path, "run_test")
    janglesnake = next(c for c in result.creatures if "Janglesnake" in c.name)
    assert "*" not in janglesnake.attacks[0].atk


def test_poison_flag_set_for_flaysnake(mutated_animals_path):
    result = INGESTOR.parse(mutated_animals_path, "run_test")
    flaysnake = next(c for c in result.creatures if "Flaysnake" in c.name)
    assert flaysnake.attacks[0].poison is True


def test_trailing_plus_artifact_stripped_from_dmg(mutated_animals_path):
    result = INGESTOR.parse(mutated_animals_path, "run_test")
    gorehound = next(c for c in result.creatures if "Gorehound" in c.name)
    assert not gorehound.attacks[0].dmg.endswith("+")


def test_prose_description_extracted(mutated_animals_path):
    result = INGESTOR.parse(mutated_animals_path, "run_test")
    for creature in result.creatures:
        assert creature.description, f"{creature.name} should have a prose description"


def test_special_abilities_extracted(mutated_animals_path):
    result = INGESTOR.parse(mutated_animals_path, "run_test")
    blinder = next(c for c in result.creatures if "Blinder" in c.name)
    assert len(blinder.special_abilities) > 0
    assert blinder.special_abilities[0]["name"] == "Silent Strike"


def test_comment_lines_are_ignored(tmp_txt):
    content = "# this is a comment\n" + MINIMAL_TABLE
    result = INGESTOR.parse(tmp_txt(content), "run_test")
    assert len(result.creatures) == 1


def test_missing_table_produces_dead_letter(tmp_txt):
    result = INGESTOR.parse(tmp_txt("Just some prose with no table.\n"), "run_test")
    assert result.errors == 1
    assert "No stat table" in result.dead_letters[0].reason


def test_unparseable_row_goes_to_dead_letter(tmp_txt):
    # Row ends with a save target so it's recognised as a data row, but has too few
    # tokens to parse all fields — should land in dead letters
    content = "Creatures HD AC Atk Dmg TR Shock MV ML Skill Save\nBadRow 14+\n"
    result = INGESTOR.parse(tmp_txt(content), "run_test")
    assert len(result.dead_letters) == 1
    assert result.errors == 1
