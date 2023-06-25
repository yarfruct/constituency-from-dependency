# Copyright © 2023 Anatoliy Poletaev, Ilya Paramonov, Elena Boychuk. All rights reserved.

import os.path
from collections import defaultdict

_endpunct_pos = {
    "PUNCT",
}

_verb_predicate_pos = {
    "VERB",
}

_nominative_predicate_pos = {
    "NOUN",
    "ADJ",
}

_main_verb_deprels = {
    "xcomp",
    "csubj",
}

_aux_verb_for_nominative_deprels = {
    "cop",
    "aux:pass"
}

_nominative_subject_pos_deprels = {
    ("ADJ", "nsubj"),
    ("DET", "nsubj"),
    ("NOUN", "nsubj"),
    ("NOUN", "nsubj:pass"),
    ("PRON", "nsubj:pass"),
    ("NUM", "nsubj"),
    ("PROPN", "nsubj"),
    ("PRON", "nsubj"),
    ("VERB", "nsubj"),
    ("VERB", "csubj"),
    ("VERB", "csubj:pass"),
    ("CCONJ", "csubj"),
    ("X", "csubj"),
}

_indirect_object_deprels = {
    "nmod",
    "obl",
    "iobj",
    "xcomp",
}

_flat_object_part_deprels = {
    "nummod",
    "nummod:gov",
    "flat",
    "flat:name",
}

_direct_object_deprels = {
    "obj",
}

_opening_quotes = {
    "«",
    "\"",
    "„",
}

_closing_quotes = {
    "»",
    "\"",
    "“",
}

_opening_brackets = {
    "(",
}

_closing_brackets = {
    ")",
}

_direct_speech_border_tokens = {
    "—",
    ",",
}

_adverbial_deprels = {
    "advmod",
}

_preposition_deprels = {
    "case"
}

_preposition_specific_lemmas = {
    "о"
}

_adverbial_specific_preposition_lemmas = {
    "назло",
    "несмотря на",
    "вопреки",
    "после",
    "в случае",
    "с помощью",
    "целых",
    "вплоть до",
    "в качестве",
    "при",
    "в связи с",
    "за счёт",
    "из-за",
}

_adverbial_specific_nominatives_lemmas = {
    "ночь",
    "утро",
    "день",
    "вечер",
    "зима",
    "весна",
    "лето",
    "осень",
    "полдень",
    "время",
    "год",
    "случай",
}

_months_names = {
    "январь",
    "февраль",
    "март",
    "апрель",
    "май",
    "июнь",
    "июль",
    "август",
    "сентябрь",
    "октябрь",
    "ноябрь",
    "декабрь"
}

_introduction_deprels = {
    "parataxis",
}

_definition_deprels = {
    "amod",
    "det",
    "appos",
}

_homogeneous_part_deprels = {
    "conj",
}

_conjunction_deprels = {
    "cc",
    "mark",
}

_conjunction_types = {
    "но": "adversative",
    "; но": "adversative",
    ", но": "adversative",
    ", , но": "adversative",
    ", а": "adversative",
    "не , а": "adversative",
    ", а не то": "adversative",
    "не только , но и": "adversative",
    "как": "comparative",
    "и": "coordinative",
    ", и": "coordinative",
    "и ,": "coordinative",
    "и , и": "coordinative",
    ", , и": "coordinative",
    ", и , и": "coordinative",
    ", а также": "coordinative",
    "как , так и": "coordinative",
    "или": "divisive",
    ", или": "divisive",
    "или , или": "divisive",
    "то ли , то ли": "divisive",
    ", когда": "subordinative",
    "когда ,": "subordinative",
    ", поэтому": "subordinative",
    ", потому что": "subordinative",
    ", откуда": "subordinative",
    ", как будто": "subordinative",
    ", если": "subordinative",
    "если —": "subordinative",
    "если ,": "subordinative",
    "хотя ,": "subordinative",
    ", пусть": "subordinative",
    ", хотя": "subordinative",
    "хотя и ,": "subordinative",
    ", чтобы": "subordinative",
    ", что": "subordinative",
    ", на что": "subordinative",
    ", кто": "subordinative",
    ", почему": "subordinative",
    ", которая": "subordinative",
    ", которое": "subordinative",
    ", которой": "subordinative",
    ", которые": "subordinative",
    "которые": "subordinative",
    ", который": "subordinative",
    ", которым": "subordinative",
    ", которых": "subordinative",
    ", в которых": "subordinative",
    ", как": "subordinative",
    "как ,": "subordinative",
    ", чем": "subordinative",
    ", зачем": "subordinative",
    ", где": "subordinative",
    ", пока": "subordinative",
    "так как ,": "subordinative",
    ", тогда как": "subordinative",
    ", словно": "subordinative",
}

_conjunction_types = defaultdict(lambda: "coordinative", **_conjunction_types)

_introduction_conjunction_specific_lemmas = {
    "как",
}

_sustainable_introductions = {
    ("хочешь", "не", "хочешь", ",", "а"),
    ("так", ",", "может", ","),
    ("так", "сказать"),
    ("опять", "же"),
    ("отметим", ",", "что"),
    ("отметим", "также", ",", "что"),
    ("как", "известно", ","),
    ("более", "того", ","),
    ("вообще", "-", "то"),
}

_particle_pos = {
    "PART",
}

_particle_by_type = {
    "бы": "particle",
    "все": "amplifying-particle",
    "всего": "particle",
    "все-таки": "particle",
    "всё-таки": "particle",
    "даже": "amplifying-particle",
    "едва": "particle",
    "же": "amplifying-particle",
    "и": "amplifying-particle",
    "именно": "amplifying-particle",
    "не": "negative-particle",
    "ни": "amplifying-particle",
    "просто": "amplifying-particle",
    "таки": "particle",
    "тоже": "particle",
    "только": "restrictive-particle",
    "уже": "amplifying-particle",
}

_particle_by_type = defaultdict(lambda: "particle", **_particle_by_type)

_compound_part_deprels = {
    "conj",
}

_nominative_pos = {
    "ADJ",
    "DET",
    "NOUN",
    "PRON",
}

_divided_subordinative_deprels = {
    "advcl",
    "parataxis",
}

_subordinative_deprels = {
    "acl",
    "acl:relcl",
    "ccomp",
}

_subordinative_conjunction_lemmas = {
    "если",
    "поэтому",
    "потому",
    "откуда",
    "почему",
    "который",
    "что",
    "кто",
    "так",
    "—",
    "зачем",
    "где",
    "пусть",
    "словно",
    "чтобы",
}

_definitive_subordinative_conjunctions = {
    ", которая",
    ", которое",
    ", которой",
    ", которые",
    "которые",
    ", который",
    ", которым",
    ", которых",
    ", кто",
    ", где",
}

_direct_object_subordinative_conjunctions = {
    ", зачем",
}

_adverbial_subordinative_conjunctions = {
    ", словно"
}

_action_verb_specific_lemmas = {
    "начать",
    "продолжать",
    "хотеть",
    "устать",
    "мочь",
    "сметь",
    "позволять",
    "быть",
    "стать",
    "являться",
    "пытаться",
}

_perceptional_verb_specific_lemmas = {
    "полюбить",
    "видеть",
    "смотреть",
    "слышать",
    "слушать",
    "чувствовать",
    "нюхать",
    "пробовать",
    "трогать",
    "желать",
    "счесть",
}

_actional_adjectives_specific_lemmas = {
    "должен",
    "пора",
    "можно",
}

_aux_verb_specific_lemmas = _action_verb_specific_lemmas | _perceptional_verb_specific_lemmas | _actional_adjectives_specific_lemmas

with open(os.path.join("resources", "verbal-nouns.txt"), encoding="utf-8") as f:
    _verbal_nouns = {word.strip() for word in f.readlines() if len(word.strip()) > 0}

_parts_names = ["first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth"]
