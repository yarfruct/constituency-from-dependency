# Copyright © 2023 Anatoliy Poletaev, Ilya Paramonov, Elena Boychuk. All rights reserved.

from morph_analyzer import get_tags, has_same_tense, is_geographical_object,\
    has_same_gender, is_plur_number
import constituency_tree_builder.lists
from constituency_tree_builder.utils import find_conjunction_parts_between, tokens_list,\
    not_included_children, all_children, get_full_text, \
    split_heterogeneous_conjunction_with_adversative,\
    collect_direct_speech_head_parts


def is_punct(dtree):
    return dtree["pos"] in constituency_tree_builder.lists._endpunct_pos


def is_predicate(dtree):
    return is_verb_predicate(dtree) or is_nominative_predicate(dtree)


def is_verb_predicate(dtree):
    return dtree["pos"] in constituency_tree_builder.lists._verb_predicate_pos and dtree["text"] is not None


def is_nominative_predicate(dtree):
    if len(tokens_list(dtree)) == 1 and dtree["pos"] == "PRON":
        return False
    if is_main_part_of_compound_nominative_predicate(dtree):
        return True
    return dtree["pos"] in constituency_tree_builder.lists._nominative_predicate_pos and \
                              any(map(lambda x: (x["pos"], x["deprel"]) in constituency_tree_builder.lists._nominative_subject_pos_deprels,
                                      not_included_children(dtree)))


def is_verb_subject(dtree):
    has_pos = dtree["pos"] in constituency_tree_builder.lists._verb_predicate_pos
    is_infinitive = dtree["text"] == dtree["lemma"]
    has_subject = any(map(lambda x: (x["pos"], x["deprel"]) in constituency_tree_builder.lists._nominative_subject_pos_deprels,
                          not_included_children(dtree)))
    return has_pos and is_infinitive and not has_subject


def is_compound_part(dtree, parent):
    if is_divided_subordinative(dtree, parent):
        return False
    has_deprel = dtree["deprel"] in constituency_tree_builder.lists._compound_part_deprels
    has_subject = False
    for subject_candidate in not_included_children(dtree):
        if is_nominative_subject(subject_candidate, dtree):
            has_subject = True
            break
    return has_deprel and has_subject


def is_divided_subordinative(dtree, main_dtree=None):
    if main_dtree is not None and main_dtree["pos"] == "VERB" \
            and get_tags(dtree["text"], dtree["lemma"], dtree["pos"])["pos"] == "GRND":
        return False
    if is_subordinated_direct_speech(dtree, main_dtree):
        return False
    if any(map(lambda x: ' '.join(x) == get_full_text(tokens_list(dtree)), constituency_tree_builder.lists._sustainable_introductions)):
        return False
    if is_enquoted(dtree):
        return False
    if main_dtree is not None and is_head_of_direct_and_indirect_speech(main_dtree, dtree):
        return False
    has_deprel, has_subordinative_conj, has_subject, has_another_tenses, has_conditional_particles = False, False, False, False, False
    has_deprel = dtree["deprel"] in constituency_tree_builder.lists._divided_subordinative_deprels
    if dtree["deprel"] in constituency_tree_builder.lists._compound_part_deprels or has_deprel:
        conjunction_parts = find_conjunction_parts_between(dtree, main_dtree)
        conjunction_text = get_full_text(conjunction_parts)
        if conjunction_text in constituency_tree_builder.lists._conjunction_types and constituency_tree_builder.lists._conjunction_types[conjunction_text] == "subordinative" \
                or conjunction_text == "—":
            has_subordinative_conj = True
    if main_dtree is not None and (dtree["deprel"] in constituency_tree_builder.lists._compound_part_deprels or has_deprel):
        has_dtree_condition, has_main_part_condition = False, False
        for child in not_included_children(dtree):
            if child["text"].lower() == "бы":
                has_dtree_condition = True
                break
        for child in not_included_children(main_dtree):
            if child["text"].lower() == "бы":
                has_main_part_condition = True
                break
        has_conditional_particles = has_dtree_condition and has_main_part_condition
    for subject_candidate in not_included_children(dtree):
        if (subject_candidate["pos"], subject_candidate["deprel"]) in constituency_tree_builder.lists._nominative_subject_pos_deprels:
            has_subject = True
            break
    if main_dtree is not None and main_dtree["pos"] == "VERB" and dtree["pos"] == "VERB":
        main_tags = get_tags(main_dtree["text"], main_dtree["lemma"], main_dtree["pos"])
        subordinative_tags = get_tags(dtree["text"], dtree["lemma"], dtree["pos"])
        has_another_tenses = not has_same_tense(main_tags, subordinative_tags)
    return has_deprel and (has_subject or has_another_tenses) \
        or has_subordinative_conj \
        or has_conditional_particles


def is_head_of_direct_speech(dtree):
    indirect_speech, *_ = collect_direct_speech_head_parts(dtree)
    return indirect_speech is not None


def is_head_of_direct_and_indirect_speech(main_dtree, possible_indirect_speech):
    indirect_speech, *_ = collect_direct_speech_head_parts(main_dtree)
    return indirect_speech == possible_indirect_speech


def is_subordinated_direct_speech(dtree, main_dtree):
    children = not_included_children(dtree, natural_order=True)
    if len(children) < 3 or main_dtree is None:
        return False
    has_quotes, has_connection = False, False
    if dtree["id"] < main_dtree["id"]:
        border_child = children.pop()
        if border_child["text"] == "—":
            has_connection = True
            if children[-1]["text"] == ",":
                children.pop()
    else:
        border_child = children.pop(0)
        if border_child["text"] == ":":
            has_connection = True
    if children[-1]["text"] == "»": # Открывающие кавычки могут относиться к названию: «Цыган» не покупают», сетовал Пушкин
        has_quotes = True
    elif children[0]["text"] == "\"" and children[-1]["text"] == "\"":
        has_quotes = True
    return has_connection and has_quotes


def is_subordinative(dtree, parent):
    if is_subordinated_direct_speech(dtree, parent):
        return False
    tags = get_tags(dtree["text"], dtree["lemma"], dtree["pos"])
    if parent["pos"] in {"NOUN", "VERB"} and tags["pos"] in {"PRTF", "ADJF"}:
        return False
    has_deprel, has_subordinative_conj, has_colon, is_appos, compound_prnoun_part, has_punct_between = False, False, False, False, False, False
    has_deprel = dtree["deprel"] in constituency_tree_builder.lists._subordinative_deprels
    tokens_between = [token["lemma"] for token in find_conjunction_parts_between(dtree, parent)]
    has_punct_between = any(map(lambda x: x in tokens_between, {',', ':'}))
    has_subordinative_conj = has_subordinative_conjunction(dtree)
    is_appos = dtree["deprel"] == "appos"
    for child in not_included_children(dtree):
        if child["lemma"] == ":":
            has_colon = True
            break
    is_parataxis = dtree["deprel"] == "parataxis"
    is_bracketed = is_enclosed_in_brackets(dtree)
    return ((has_deprel or has_subordinative_conj) and has_punct_between) \
        or (has_colon and is_appos) \
        or ((is_bracketed or has_colon) and is_parataxis) \
        and not compound_prnoun_part


def is_compound_geo_proper_noun_part(dtree, parent):
    if is_geographical_object(dtree["text"], dtree["lemma"], dtree["pos"]) \
            and is_geographical_object(parent["text"], parent["lemma"], parent["pos"]):
        if len(not_included_children(dtree)) > 0 and \
                not_included_children(dtree)[0]["lemma"] == "—":
            return True
    return False


def is_compound_name_proper_noun_part(dtree, parent):
    if is_enclosed_in_brackets(dtree):
        return False
    return parent["pos"] == "PROPN" and dtree["pos"] == "PROPN"


def has_subordinative_conjunction(dtree, only_not_included=True):
    children = not_included_children(dtree) if only_not_included else all_children(dtree)
    for conjunction_candidate in children:
        if conjunction_candidate["lemma"] in constituency_tree_builder.lists._subordinative_conjunction_lemmas \
                and conjunction_candidate["pos"] == "SCONJ" or conjunction_candidate["lemma"] == "зачем":
            return True
    return False


def is_adverbial(dtree, parent):
    if dtree["pos"] in constituency_tree_builder.lists._particle_pos:
        return False
    if parent["pos"] == "ADV" and dtree["lemma"] in constituency_tree_builder.lists._particle_by_type:
        return False
    return dtree["deprel"] in constituency_tree_builder.lists._adverbial_deprels or \
        dtree["deprel"] in {"obl", "advcl"} and (dtree["pos"] in {"ADJ", "ADV"} and dtree["lemma"] != "весьма") or \
        is_verbative_target_adverbial(dtree, parent) or \
        has_adverbial_specific_preposition(dtree) or \
        is_adverbial_specific_nominative(dtree, parent)


def has_adverbial_specific_preposition(dtree):
    for preposition_candidate in not_included_children(dtree):
        if is_adverbial_specific_preposition(preposition_candidate):
            return True
    return False


def is_adverbial_specific_preposition(dtree):
    if get_full_text(tokens_list(dtree)).lower() in constituency_tree_builder.lists._adverbial_specific_preposition_lemmas:
        return True
    return False


def is_adverbial_specific_nominative(dtree, parent):
    tags = get_tags(dtree["text"], dtree["lemma"], dtree["pos"])
    if dtree["lemma"] == "раз":
        for child in not_included_children(dtree):
            if child["lemma"] == "несколько":
                return True
    if get_full_text(tokens_list(dtree)) in {"также", "достаточно", "в одночасье", "из ничего"}:
        return True
    if parent["pos"] == "VERB" and tags["pos"] == "GRND":
        return True
    if dtree["text"] == "втроём":
        return True
    if is_adverbial_head_as_preposition(dtree):
        return True
    if dtree["text"] == "%" and not_included_children(dtree) and not_included_children(dtree, natural_order=True)[0]["lemma"] == "на":
        return True
    has_listed_lemma = dtree["lemma"].lower() in (constituency_tree_builder.lists._adverbial_specific_nominatives_lemmas | constituency_tree_builder.lists._months_names)
    is_ablative_case = tags["case"] == "ablt" # творительный падеж: "ночью"
    is_dat_case = tags["case"] == "datv" # дательный падеж: по утрам, по вечерам
    is_accs_case = tags["case"] in {"accs", "nomn"} # винительный падеж: весь вечер
                                          # именительный падеж, т.к. иногда неотличим от винительного: за год
    is_loct_case = tags["case"] == "loct" # предложный падеж: в случае
    is_loc2_case = tags["case"] == "loc2" # второй предложный падеж: в году
    has_dat_specific_preposition, has_accs_specific_definition, has_accs_specific_preposition, has_loct_specific_preposition, has_loc2_specific_preposition = False, False, False, False, False
    for child in not_included_children(dtree):
        if child["lemma"] in {"по", "с"}:
            has_dat_specific_preposition = True
        if child["lemma"] in {"весь", "всё", "этот"}:
            has_accs_specific_definition = True
        if child["lemma"] in {"в", "за"}:
            has_accs_specific_preposition = True
        if child["lemma"] in {"в"}:
            has_loct_specific_preposition = True
        if dtree["lemma"] in {"год", "месяц", "квартал"} and child["lemma"] in {"в", "за"}:
            has_loc2_specific_preposition = True
    if has_listed_lemma and \
        (is_ablative_case or
         is_dat_case and has_dat_specific_preposition or
         is_accs_case and (has_accs_specific_definition or has_accs_specific_preposition) or
         is_loct_case and has_loct_specific_preposition or
         is_loc2_case and has_loc2_specific_preposition):
        return True
    if is_verb_predicate(parent) or is_aux_part_of_compound_nominative_predicate(parent):
        if dtree["deprel"] == "nummod":
            for child in not_included_children(dtree):
                if child["lemma"].lower() in constituency_tree_builder.lists._months_names:
                    return True
                if child["text"].lower() == "часов":
                    return True
    return False


def is_verbative_target_adverbial(dtree, parent):
    if is_aux_part_of_compound_verb_predicate(parent):
        return False
    has_deprel = dtree["deprel"] == "xcomp"
    parent_is_verb = parent["pos"] == "VERB"
    tags = get_tags(dtree["text"], dtree["lemma"], dtree["pos"])
    dtree_is_infinitive = tags["pos"] == "INFN"
    return has_deprel and parent_is_verb and dtree_is_infinitive


def is_adverbial_head_as_preposition(dtree):
    if dtree["text"].lower() == "случае" \
            and not_included_children(dtree) and not_included_children(dtree)[0]["text"].lower() == "в":
        return True
    if dtree["text"].lower() == "счёт" \
            and not_included_children(dtree) and not_included_children(dtree)[0]["text"].lower() == "за":
        return True
    if get_full_text(tokens_list(dtree)).lower() == "на этот раз":
        return True
    return False


def is_indirect_object(dtree, parent):
    if dtree["lemma"] in {"также", "достаточно", "весьма"}:
        return False
    if dtree["lemma"] == "они" and dtree["text"] == "их" \
            and parent is not None and not is_verbal_noun(parent):
        return False
    if parent is not None and is_direct_object_for_verbal_noun(dtree, parent):
        return False
    if parent is not None \
            and is_aux_part_of_compound_nominative_predicate(parent) \
            and is_main_part_of_compound_nominative_predicate(dtree):
        return False
    if is_enclosed_in_brackets(dtree) and dtree["deprel"] == "flat:foreign":
        return True
    if parent is not None and parent["pos"] == "NOUN" and dtree["deprel"] == "flat:foreign":
        return True
    if parent is not None and dtree["deprel"] == "advcl":
        conjunctions_tokens = [t["lemma"] for t in find_conjunction_parts_between(dtree, parent)]
        if conjunctions_tokens == ["как"]:
            return True
    has_deprel, is_numeric_modifier, is_atomic_part, is_target_adverbial = False, False, False, False
    has_deprel = dtree["deprel"] in constituency_tree_builder.lists._indirect_object_deprels or \
                 dtree["deprel"] == "nummod:gov" and has_preposition(dtree) or \
                 dtree["deprel"] == "nsubj" and dtree["lemma"].isupper() and not is_enquoted(dtree)
    if parent is not None:
        if parent["pos"] == "NOUN" and dtree["pos"] == "NUM" \
                and has_same_gender(get_tags(dtree["text"], dtree["lemma"], dtree["pos"]),
                                    get_tags(parent["text"], parent["lemma"], parent["pos"])):
            is_numeric_modifier = True
    if parent is not None:
        is_atomic_part = is_atomic_nominative_part(dtree, parent)
    if parent is not None:
        is_target_adverbial = is_verbative_target_adverbial(dtree, parent)
    return has_deprel \
        and not (is_numeric_modifier or is_atomic_part or is_target_adverbial) \
        and not has_adverbial_specific_preposition(dtree) \
        and not is_adverbial_specific_nominative(dtree, parent) \
        and not is_adverbial_specific_preposition(dtree)


def is_direct_object_for_verbal_noun(dtree, parent):
    dtree_tags = get_tags(dtree["text"], dtree["lemma"], dtree["pos"])
    is_in_gent_case = dtree_tags["case"] == "gent" # родительный падеж
    is_parent_verbal_noun = is_verbal_noun(parent)
    return is_parent_verbal_noun and is_in_gent_case


def is_verbal_noun(dtree):
    return dtree["lemma"] in constituency_tree_builder.lists._verbal_nouns


def is_definition(dtree, parent):
    if dtree["lemma"] == "они" and dtree["text"] == "их" \
            and parent is not None and not is_verbal_noun(parent):
        return True
    if parent is not None and is_compound_name_proper_noun_part(dtree, parent):
        return False
    if dtree["deprel"] in constituency_tree_builder.lists._definition_deprels:
        return True
    tags = get_tags(dtree["text"], dtree["lemma"], dtree["pos"])
    if tags["pos"] in {"PRTF"}:
        return True
    if tags["pos"] == "ADJF" and dtree["deprel"] == "acl":
        return True
    if parent is not None and parent["pos"] == "ADJ" and dtree["lemma"] == "весьма":
        return True
    return False


def is_atomic_nominative_part(dtree, parent):
    if is_compound_geo_proper_noun_part(dtree, parent):
        return True
    if parent["pos"] == "NUM":
        if dtree["lemma"] == "который":
            if len(not_included_children(dtree)) == 1 and not_included_children(dtree)[0]["lemma"] == "из":
                return True
    if parent["pos"] == "PRON" and parent["lemma"] == "кто-то":
        if is_plur_number(dtree["text"], dtree["lemma"], dtree["pos"]):
            if not_included_children(dtree)[0]["lemma"] == "из":
                return True
    if parent["pos"] == "PROPN" and dtree["pos"] == "PROPN":
        return True
    if parent["pos"] == "ADJ":
        if dtree["text"].lower() in {"всё"}:
            return True
    return False


def is_direct_object(dtree, parent):
    if is_enquoted(dtree) and is_verb_predicate(dtree):
        return True
    if dtree["deprel"] in constituency_tree_builder.lists._direct_object_deprels:
        return True
    if dtree["deprel"] == "nummod:gov" and not has_preposition(dtree):
        return True
    if parent is not None and is_direct_object_for_verbal_noun(dtree, parent):
        return True
    return False


def is_flat_object_part(dtree, parent):
    has_deprel = dtree["deprel"] in constituency_tree_builder.lists._flat_object_part_deprels
    is_atomic_part = is_atomic_nominative_part(dtree, parent)
    is_specific_text = (parent["text"] + dtree["text"]).lower() in {"статус-кво"}
    return has_deprel or is_atomic_part or is_specific_text


def is_flat_object_head(dtree):
    return dtree["lemma"].lower() in {"множество", "большинство", "кто-то"}


def is_aux_part_of_compound_verb_predicate(dtree):
    has_lemma = is_aux_verb_text(dtree)
    has_main_part = False
    for main_part_candidate in not_included_children(dtree):
        if is_main_verb(main_part_candidate):
            has_main_part = True
    return has_lemma and has_main_part


def is_main_part_of_compound_verb_predicate(dtree):
    has_aux_part, has_pos, is_infinitive = False, False, False
    has_pos = dtree["pos"] == "VERB"
    is_infinitive = dtree["text"] == dtree["lemma"]
    for aux_part_candidate in not_included_children(dtree):
        if is_aux_verb_text(aux_part_candidate):
            has_aux_part = True
            break
    return has_aux_part and has_pos and is_infinitive


def is_aux_verb_text(dtree):
    if dtree["lemma"].lower() in constituency_tree_builder.lists._aux_verb_specific_lemmas:
        return True
    if dtree["text"] == "смела":
        return True
    return False


def is_main_verb(dtree):
    has_deprel = dtree["deprel"] in constituency_tree_builder.lists._main_verb_deprels
    return has_deprel


def is_main_part_of_compound_nominative_predicate(dtree, parent=None):
    if parent is not None and is_direct_object(dtree, parent):
        return False
    if parent is not None and dtree["deprel"] == "conj":
        return is_main_part_of_compound_nominative_predicate(parent)
    tags = get_tags(dtree["text"], dtree["lemma"], dtree["pos"])
    has_pos = dtree["pos"] in constituency_tree_builder.lists._nominative_pos or tags["pos"] == "PRTS"
    is_specific_word = dtree["text"].lower() in {
        "запрещено",
        "нужный",
        "можно",
        "разрешено",
        "добротно",
        "красиво",
        "примитивно",
        "лень",
        "непрост",
        "пора",
    }
    is_short_adj = tags['pos'] == 'ADJS'
    if not is_specific_word:
        if parent is not None and parent["lemma"] == "быть":
            is_specific_word = dtree["text"].lower() == "так"
    has_subject = False
    for subject_candidate in all_children(dtree):
        if is_nominative_subject(subject_candidate, dtree):
            has_subject = True
            break
    has_aux_part = False
    for aux_part_candidate in not_included_children(dtree):
        if is_aux_part_of_compound_nominative_predicate(aux_part_candidate):
            has_aux_part = True
    in_subordinative = has_subordinative_conjunction(dtree, only_not_included=False) or \
                       (parent is not None and has_subordinative_conjunction(parent, only_not_included=False))
    return has_pos or is_short_adj or is_specific_word


def is_aux_part_of_compound_nominative_predicate(dtree):
    has_deprel = dtree["deprel"] in constituency_tree_builder.lists._aux_verb_for_nominative_deprels
    has_special_lemma = dtree["lemma"].lower() in {"становиться", "являться", "стать", "оказаться", "счесть", "быть"}
    is_a_word = dtree["text"] not in {"—"}
    return (has_deprel or has_special_lemma) and is_a_word


def has_introduction(dtree):
    return find_introduction(dtree) is not None


def find_introduction(core_dtree):
    candidates = not_included_children(core_dtree, natural_order=True)
    if len(candidates) == 0:
        return None
    if is_subordinated_direct_speech(candidates[0], core_dtree):
        return None
    if is_enquoted(candidates[0]) or is_enclosed_in_brackets(candidates[0]):
        return None
    if candidates[0]["deprel"] in constituency_tree_builder.lists._introduction_deprels \
            and not has_subordinative_conjunction(candidates[0]) \
            and not is_enclosed_in_brackets(candidates[0]):
        conjunctions_between = find_conjunction_parts_between(core_dtree, candidates[0])
        if not (len(conjunctions_between) == 1 and conjunctions_between[0]["text"] == ":"):
            return candidates[0]
    if candidates[0]["deprel"] in constituency_tree_builder.lists._divided_subordinative_deprels and len(not_included_children(candidates[0])) > 0:
        possible_root = candidates[0]
        possible_conjunction = not_included_children(possible_root, natural_order=True)[0]
        has_lemma, has_comma = False, False
        has_lemma = possible_conjunction["lemma"].lower() in constituency_tree_builder.lists._introduction_conjunction_specific_lemmas
        has_comma = "," in {token["lemma"] for token in find_conjunction_parts_between(core_dtree, possible_root)}
        if has_lemma and has_comma:
            return possible_root
    if candidates[0]["id"] == 0 and candidates[0]["lemma"] in {"и", "а", "или", "но"}:
        lemmas = [t["lemma"] for t in tokens_list(core_dtree)]
        if lemmas.count(candidates[0]["lemma"]) == 1:
            return candidates[0]
    return None


def is_enclosed_in_brackets(dtree):
    lemmas = [token["lemma"] for token in tokens_list(dtree)]
    if len(lemmas) < 2:
        return False
    return lemmas[0] in constituency_tree_builder.lists._opening_brackets and lemmas[-1] in constituency_tree_builder.lists._closing_brackets


def is_enclosed_in_commas(dtree):
    tokens = sorted(tokens_list(dtree), key=lambda x: x["id"])
    lemmas = [token["lemma"] for token in tokens]
    if len(lemmas) < 2:
        return False
    opened_with_comma = lemmas[0] == ','
    closed_with_comma = lemmas[-1] == ','
    return closed_with_comma and (opened_with_comma or tokens[0]["id"] == 0)


def is_nominative_subject(dtree, predicate=None):
    if predicate is None:
        return dtree["pos"] in {pos for pos, deprel in constituency_tree_builder.lists._nominative_subject_pos_deprels}
    return (dtree["pos"], dtree["deprel"]) in constituency_tree_builder.lists._nominative_subject_pos_deprels


def is_proper_noun(dtree):
    return dtree["pos"] == "PROPN"


def is_proper_noun_definition(dtree, parent):
    return is_definition(dtree, parent) and is_proper_noun(dtree)


def has_sustainable_introduction(dtree):
    return find_sustainable_introduction(dtree) is not None


def find_sustainable_introduction(dtree):
    texts = [t["text"].lower() for t in tokens_list(dtree)]
    for sustainable_introduction_candidate in constituency_tree_builder.lists._sustainable_introductions:
        if texts[:len(sustainable_introduction_candidate)] == list(sustainable_introduction_candidate):
            return sustainable_introduction_candidate
    return None


def directly_follows(first, second):
    second_ids = [token["id"] for token in tokens_list(second)]
    return second_ids[0] - first["id"] == 1


def is_particle(dtree):
    if dtree["pos"] in constituency_tree_builder.lists._particle_pos or dtree["text"].lower() in {"бы", "даже", "уже"}:
        return True
    return False


def is_homogeneous_predicates_part(dtree, parent):
    has_deprel = dtree["deprel"] in constituency_tree_builder.lists._homogeneous_part_deprels
    forms_compound_noun = is_main_part_of_compound_nominative_predicate(parent) and is_main_part_of_compound_nominative_predicate(dtree)
    return has_deprel and not forms_compound_noun


def is_homogeneous_nominative_part(dtree, parent=None):
    has_deprel = dtree["deprel"] in constituency_tree_builder.lists._homogeneous_part_deprels
    return has_deprel


def has_preposition(dtree):
    for preposition_candidate in not_included_children(dtree):
        if is_preposition(preposition_candidate):
            return True
    return False


def is_preposition(dtree):
    if dtree["deprel"] in constituency_tree_builder.lists._preposition_deprels:
        return True
    if dtree["lemma"].lower() in constituency_tree_builder.lists._preposition_specific_lemmas:
        return True
    return False


def has_indirect_object(dtree):
    for indirect_object_candidate in reversed(not_included_children(dtree)):
        if is_indirect_object(indirect_object_candidate, dtree):
            return True
    return False


def has_coordinative_conjunction(dtree):
    for coordination_candidate in not_included_children(dtree):
        if coordination_candidate["deprel"] in constituency_tree_builder.lists._conjunction_deprels \
                and constituency_tree_builder.lists._conjunction_types[coordination_candidate["text"]] == "coordinative":
            return True
    return False


def is_enquoted(dtree):
    children = not_included_children(dtree, natural_order=True)
    if len(children) < 2:
        return False
    return children[0]["text"] in constituency_tree_builder.lists._opening_quotes and children[-1]["text"] in constituency_tree_builder.lists._closing_quotes


def is_heterogeneous_conjunctions_with_adversative(parts):
    first_coordinative, adversative, second_coordinative = split_heterogeneous_conjunction_with_adversative(parts)
    return first_coordinative is not None and second_coordinative is not None and adversative is not None
