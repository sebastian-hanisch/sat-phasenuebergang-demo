"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen; Permalink-Begrenzung; jedes Preset zeigt, was seine Hilfe verspricht."""

import pytest

import sph_constants as C
import sph_evaluation as ev
import sph_presets as P
import sph_search as S


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_valid_choices():
    for preset in C.PRESETS.values():
        assert C.N_MIN <= preset["n"] <= C.N_MAX and C.M_MIN <= preset["m"] <= C.M_MAX and 0 <= preset["seed"] <= C.SEED_MAX
        assert preset["units"] in (True, False) and preset["rule"] in C.RULES and preset["budget"] in C.BUDGETS and preset["h"] in C.PIGEON_H and preset["pm"] in C.PER_MILLE


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS["Standardfall (Voreinstellung)"]) == ev.Settings()
    assert next(iter(C.PRESETS)) == "Standardfall (Voreinstellung)"


def test_setting_specs_cover_every_preset_key_and_choices_have_bounds():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)
    for key in ("units_toggle", "rule_select", "budget_select", "h_select", "pm_select"):
        spec = P.SETTING_SPECS[key]
        assert spec.options and spec.lo == spec.options[0] and spec.hi == spec.options[-1], key


def test_rules_match_the_search_module():
    assert C.RULES == S.RULES


def test_coerce_limits_numbers_and_rejects_unknown_choices():
    n, units = P.SETTING_SPECS["n_slider"], P.SETTING_SPECS["units_toggle"]
    assert P._coerce(n, "1") == C.N_MIN and P._coerce(n, "99") == C.N_MAX and P._coerce(n, "7") == 7 and P._coerce(n, "x") is None and P._coerce(n, ["9"]) == 9
    assert P._coerce(units, "true") is True and P._coerce(units, "False") is False and P._coerce(units, "1") is True and P._coerce(units, "vielleicht") is None
    assert P._coerce(P.SETTING_SPECS["rule_select"], "jw") == "jw" and P._coerce(P.SETTING_SPECS["rule_select"], "zufall") is None
    assert P._coerce(P.SETTING_SPECS["pm_select"], "10") == 10 and P._coerce(P.SETTING_SPECS["pm_select"], "7") is None


def test_presets_show_what_their_help_promises():
    r = {name: ev.analyse(ev.Settings(**p)) for name, p in C.PRESETS.items()}
    assert r["Standardfall (Voreinstellung)"].result.satisfiable is True
    teach = r["Lehrbeispiel (6 Variablen)"].result
    assert teach.nodes <= 10 and teach.tree and not teach.tree_truncated
    assert r["Locker (m/n = 3)"].result.satisfiable is True
    near = r["Am Übergang (m/n = 4,5)"]
    assert near.settings.m / near.settings.n == 4.5 and not near.result.aborted
    over = r["Überbestimmt (m/n = 6)"]
    assert over.settings.m / over.settings.n == 6 and over.result.satisfiable is False
    no_units = r["Ohne Einheitspropagation"]
    assert no_units.result.aborted and no_units.result.units == 0 and no_units.settings.units is False
    struct = r["Schubfach, leicht gestört"].settings
    assert (struct.h, struct.pm) == (6, 10)
    assert next(x for x in ev.structure_rows(6) if x["pm"] == 10)["sat"] == 10        # die Störung macht die Formel (meist) erfüllbar
    for a in r.values():
        assert ev.validation_errors(a) == []
