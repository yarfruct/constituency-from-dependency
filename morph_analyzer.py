# Copyright © 2023 Anatoliy Poletaev, Ilya Paramonov, Elena Boychuk. All rights reserved.

from pymorphy2 import MorphAnalyzer

morph = MorphAnalyzer()


def has_same_tense(first_verb_tags, second_verb_tags):
    return first_verb_tags["tense"] == second_verb_tags["tense"]


def has_same_gender(first_verb_tags, second_verb_tags):
    return first_verb_tags["gender"] == second_verb_tags["gender"]


def has_same_person(first_verb_tags, second_verb_tags):
    return first_verb_tags["person"] == second_verb_tags["person"]


def get_tags(text, lemma, pos):
    parse = parse_word(text, lemma, pos)
    return {
        "pos": parse.tag.POS,
        "gender": parse.tag.gender,
        "person": parse.tag.person,
        "tense": parse.tag.tense,
        "number": parse.tag.number,
        "is_geox": ("Geox" in parse.tag.grammemes),
        "case": parse.tag.case
    }


def is_plur_number(text, lemma, pos):
    return get_tags(text, lemma, pos)["number"] == "plur"


def is_geographical_object(text, lemma, pos):
    tags = get_tags(text, lemma, pos)
    return tags["is_geox"]


def parse_word(text, lemma, pos):
    parse = morph.parse(text)
    if len(parse) == 1:
        return parse[0]
    for candidate in parse:
        if pos == "NUM" and "NUMB" in candidate.tag:
            return candidate
        if candidate.normal_form == lemma and candidate.tag.POS.lower() == pos.lower():
            return candidate
    return parse[0]
