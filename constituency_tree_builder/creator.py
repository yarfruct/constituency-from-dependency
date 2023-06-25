# Copyright © 2023 Anatoliy Poletaev, Ilya Paramonov, Elena Boychuk. All rights reserved.

from functools import reduce

from constituency_tree_builder.checks import is_predicate, is_verb_predicate, is_verb_subject, \
    is_compound_part, \
    is_divided_subordinative, is_head_of_direct_speech, \
    is_subordinated_direct_speech, is_subordinative, is_adverbial, \
    has_adverbial_specific_preposition, is_adverbial_specific_nominative, \
    is_adverbial_head_as_preposition, \
    is_indirect_object, is_definition, is_atomic_nominative_part, is_direct_object, \
    is_flat_object_part, \
    is_flat_object_head, is_aux_part_of_compound_verb_predicate, \
    is_main_part_of_compound_verb_predicate, is_main_verb, \
    is_main_part_of_compound_nominative_predicate, \
    is_aux_part_of_compound_nominative_predicate, has_introduction, \
    find_introduction, is_enclosed_in_brackets, is_nominative_subject, \
    has_sustainable_introduction, find_sustainable_introduction, \
    directly_follows, is_particle, is_homogeneous_predicates_part, \
    is_homogeneous_nominative_part, has_preposition, \
    is_preposition, has_indirect_object, has_coordinative_conjunction, is_enquoted, \
    is_heterogeneous_conjunctions_with_adversative, is_punct, \
    is_proper_noun_definition
from constituency_tree_builder.utils import find_conjunction_parts_between, tokens_list,\
    not_included_children, split_heterogeneous_conjunction_with_adversative, clean_constituency_tree,\
    collect_direct_speech_head_parts
import constituency_tree_builder.lists


def dependency_tree_to_constituency_tree(dependency_tree):
    return clean_constituency_tree(create_sentence(dependency_tree))


def create_sentence(dtree):
    children = not_included_children(dtree, natural_order=True)
    end_puncts = []
    for child in reversed(children):
        if not is_punct(child):
            break
        end_puncts.insert(0, child)
        child["~included"] = True
    if not end_puncts:
        return create_core(dtree)
    endpunct = children[-1]
    endpunct["text"] = ''.join([p["text"] for p in end_puncts])
    return {
        "_type": "sentence",
        "core": create_core(dtree),
        "endpunct": {
            "_type": "endpunct",
            "_token": endpunct
        }
    }


def create_core(dtree):
    if is_enclosed_in_brackets(dtree):
        brackets = create_enclosing_brackets(dtree)
        return {
            "_type": "bracketed-group",
            "content": create_core(dtree),
            "brackets": brackets
        }
    if is_head_of_direct_speech(dtree):
        direct_speech = dtree
        indirect_speech, *_, border_tokens = collect_direct_speech_head_parts(dtree)
        indirect_speech["head_id"], direct_speech["head_id"] = direct_speech["head_id"], indirect_speech["head_id"]
        indirect_speech["deprel"], direct_speech["deprel"] = direct_speech["deprel"], indirect_speech["deprel"]
        direct_speech["~children"].remove(indirect_speech)
        indirect_speech["~children"].append(direct_speech)
        if len(border_tokens) > 0:
            for token in border_tokens:
                indirect_speech["~children"].remove(token)
                direct_speech["~children"].append(token)
        return create_core(indirect_speech)
    if has_sustainable_introduction(dtree):
        introduction = find_sustainable_introduction(dtree)
        tokens = tokens_list(dtree)
        main_token = tokens[0]
        for ix, token in enumerate(tokens):
            if ix == len(introduction):
                break
            token["~included"] = True
            if token["id"] < main_token["id"]:
                main_token = token
        dtree_is_in_introduction = dtree["text"].lower() in introduction
        main_token["text"] = ' '.join(introduction).capitalize()
        introduction_node = {
            "_type": "introduction",
            "_token": main_token
        }
        if dtree_is_in_introduction:
            core_node = create_core(not_included_children(dtree)[0])
        else:
            core_node = create_core(dtree)
        return {
            "_type": "core",
            "introduction": introduction_node,
            "core": core_node
        }
    if has_introduction(dtree):
        introduction = find_introduction(dtree)
        introduction["~included"] = True
        return {
            "_type": "core",
            "introduction": create_introduction(introduction, parent=dtree),
            "core": create_core(dtree)
        }
    compound_parts_roots = [dtree]
    for compound_part_candidate in not_included_children(dtree, natural_order=True):
        if is_compound_part(compound_part_candidate, dtree):
            compound_parts_roots.append(compound_part_candidate)
    if len(compound_parts_roots) > 1:
        for compound_part_root in compound_parts_roots:
            compound_part_root["~included"] = True
        result = {
            "_type": "compound-sentence"
        }
        conjunction_parts = find_conjunction_parts_between(*compound_parts_roots)
        if conjunction_parts:
            if is_heterogeneous_conjunctions_with_adversative(conjunction_parts):
                first_coordinative, adversative, second_coordinative = split_heterogeneous_conjunction_with_adversative(conjunction_parts)
                assert len(compound_parts_roots) == 4
                first_coordinative = create_conjunction(*first_coordinative)
                second_coordinative = create_conjunction(*second_coordinative)
                adversative = create_conjunction(*adversative)
                fourth_core = create_core(compound_parts_roots[3])
                third_core = create_core(compound_parts_roots[2])
                second_core = create_core(compound_parts_roots[1])
                first_core = create_core(compound_parts_roots[0])
                return {
                    "_type": "compound-sentence",
                    "first-sentence": {
                        "_type": "compound-sentence",
                        "first-sentence": first_core,
                        "second-sentence": second_core,
                        "joined-by": first_coordinative
                    },
                    "second-sentence": {
                        "_type": "compound-sentence",
                        "first-sentence": third_core,
                        "second-sentence": fourth_core,
                        "joined-by": second_coordinative
                    },
                    "joined-by": adversative
                }
            conjunction = create_conjunction(*conjunction_parts)
            result["joined-by"] = conjunction
        for ix, part in enumerate(compound_parts_roots):
            result[f"{constituency_tree_builder.lists._parts_names[ix]}-sentence"] = create_core(part)
        return result
    for divided_subordinated_candidate in reversed(not_included_children(dtree)):
        if is_divided_subordinative(divided_subordinated_candidate, dtree):
            subordinated_sentence = divided_subordinated_candidate
            subordinated_sentence["~included"] = True
            return create_divided_complex_sentence(dtree, subordinated_sentence)
    if is_predicate(dtree) or is_aux_part_of_compound_verb_predicate(dtree) or is_aux_part_of_compound_nominative_predicate(dtree):
        predicate = dtree
        predicate["~included"] = True
        for subject_candidate in not_included_children(predicate):
            if is_nominative_subject(subject_candidate, dtree):
                if is_subordinative(subject_candidate, dtree):
                    continue
                subject = subject_candidate
                subject["~included"] = True
                return {
                    "_type": "core",
                    "subject": create_subject(subject),
                    "predicate": create_predicate(predicate)
                }
        return create_predicate(predicate)
    if is_nominative_subject(dtree) and not is_verb_subject(dtree):
        subject = dtree
        subject["~included"] = True
        return create_subject(subject)
    if is_verb_subject(dtree):
        subject = dtree
        subject["~included"] = True
        return create_verb_subject(subject)
    return create_verb_subject(dtree)


def create_introduction(dtree, parent=None):
    if is_verb_predicate(dtree) and parent is not None:
        conjunction_parts = find_conjunction_parts_between(dtree,
                                                           parent)
        if conjunction_parts and not all(map(is_punct, conjunction_parts)):
            conjunction = create_conjunction(*conjunction_parts)
            result = {
                "_type": "introduction-sentence",
                "sentence": create_sentence(dtree),
                "joined-by": conjunction
            }
            return result
    for child in not_included_children(dtree):
        if is_punct(child):
            child["~included"] = True
    if has_preposition(dtree):
        for preposition_candidate in not_included_children(dtree):
            if is_preposition(preposition_candidate):
                preposition = preposition_candidate
                preposition["~included"] = True
                return {
                    "_type": "introduction",
                    "preposition": create_preposition(preposition),
                    "introduction": create_introduction(dtree)
                }
    if len(not_included_children(dtree)) != 0:
        parts = [dtree] + not_included_children(dtree)
        parts.sort(key=lambda x: x["id"])
        for part in parts:
            part["~included"] = True
        result = {
            "_type": "introduction"
        }
        for ix, part in enumerate(parts):
            result[f"{constituency_tree_builder.lists._parts_names[ix]}-introduction-part"] = create_introduction(part)
        return result
    dtree["~included"] = True
    return {
        "_type": "introduction",
        "_token": dtree
    }


def create_divided_complex_sentence(main_dtree, subordinated_dtree):
    if is_enclosed_in_brackets(subordinated_dtree):
        return {
            "_type": "divided-complex-sentence",
            "main-sentence": create_core(main_dtree),
            "subordinated-sentence": create_core(subordinated_dtree)
        }
    conjunction_parts = find_conjunction_parts_between(main_dtree, subordinated_dtree)
    if conjunction_parts:
        conjunction = create_conjunction(*conjunction_parts)
    if conjunction_parts and conjunction["_token"]["lemma"] == "—":
        if main_dtree["id"] < subordinated_dtree["id"]:
            main_dtree, subordinated_dtree = subordinated_dtree, main_dtree
    result = {
        "_type": "divided-complex-sentence",
        "main-sentence": create_core(main_dtree),
        "subordinated-sentence": create_core(subordinated_dtree)
    }
    if conjunction_parts:
        result["joined-by"] = conjunction
    return result


def create_verb_subject(dtree):
    for indirect_object_candidate in not_included_children(dtree):
        if is_indirect_object(indirect_object_candidate, dtree):
            indirect_object = indirect_object_candidate
            indirect_object["~included"] = True
            return {
                "_type": "subject",
                "subject": create_verb_subject(dtree),
                "object": create_object(indirect_object)
            }
    for adverbial_candidate in not_included_children(dtree):
        if is_adverbial(adverbial_candidate, dtree):
            adverbial = adverbial_candidate
            adverbial["~included"] = True
            return {
                "_type": "subject",
                "subject": create_verb_subject(dtree),
                "adverbial": create_adverbial(adverbial)
            }
    for direct_object_candidate in not_included_children(dtree):
        if direct_object_candidate["deprel"] in constituency_tree_builder.lists._direct_object_deprels:
            direct_object = direct_object_candidate
            direct_object["~included"] = True
            return {
                "_type": "subject",
                "subject": create_verb_subject(dtree),
                "object": create_object(direct_object)
            }
    for particle_candidate in reversed(not_included_children(dtree)):
        if is_particle(particle_candidate):
            particle = particle_candidate
            particle["~included"] = True
            return {
                "_type": "subject",
                "subject": create_verb_subject(dtree),
                "particle": create_particle(particle)
            }
    dtree["~included"] = True
    return {
        "_type": "subject",
        "_token": dtree
    }


def create_subject(dtree):
    if has_introduction(dtree):
        introduction = find_introduction(dtree)
        introduction["~included"] = True
        return {
            "_type": "subject",
            "introduction": create_introduction(introduction),
            "subject": create_subject(dtree)
        }
    homogeneous_parts = [dtree]
    for homogeneous_candidate in not_included_children(dtree):
        if homogeneous_candidate["deprel"] in constituency_tree_builder.lists._homogeneous_part_deprels:
            homogeneous_parts.append(homogeneous_candidate)
    if len(homogeneous_parts) > 1:
        result = {
            "_type": "homogeneous-subjects"
        }
        for part in homogeneous_parts:
            part["~included"] = True
        conjunction_parts = find_conjunction_parts_between(*homogeneous_parts)
        if conjunction_parts:
            conjunction = create_conjunction(*conjunction_parts)
            result["joined-by"] = conjunction
        for ix, part in enumerate(homogeneous_parts):
            result[f"{constituency_tree_builder.lists._parts_names[ix]}-subject"] = create_subject(part)
        return result
    children = list(reversed(not_included_children(dtree)))
    for proper_noun_definition_candidate in children:
        if is_definition(proper_noun_definition_candidate, dtree) and proper_noun_definition_candidate["pos"] == "PROPN":
            children += not_included_children(proper_noun_definition_candidate)
    for subordinative_candidate in children:
        if is_subordinative(subordinative_candidate, dtree):
            subordinative_candidate["~included"] = True
            subordinative, role = create_subordinative(subordinative_candidate, dtree)
            result = {
                "_type": "subject",
                "subject": create_subject(dtree),
                role: subordinative
            }
            return result
    for indirect_object_candidate in children:
        if is_indirect_object(indirect_object_candidate, dtree):
            object = indirect_object_candidate
            object["~included"] = True
            return {
                "_type": "subject",
                "subject": create_subject(dtree),
                "indirect-object": create_object(object)
            }
    for definition_candidate in children:
        if is_definition(definition_candidate, dtree) and not is_proper_noun_definition(definition_candidate, dtree):
            definition = definition_candidate
            definition["~included"] = True
            return {
                "_type": "subject",
                "subject": create_subject(dtree),
                "definition": create_definition(definition)
            }
    for direct_object_candidate in children:
        if is_direct_object(direct_object_candidate, dtree):
            direct_object = direct_object_candidate
            direct_object["~included"] = True
            return {
                "_type": "subject",
                "subject": create_subject(dtree),
                "direct-object": create_object(direct_object)
            }
    for proper_noun_definition_candidate in children:
        if is_proper_noun_definition(proper_noun_definition_candidate, dtree):
            definition = proper_noun_definition_candidate
            definition["~included"] = True
            return {
                "_type": "subject",
                "subject": create_subject(dtree),
                "definition": create_definition(definition)
            }
    for particle_candidate in reversed(children):
        if is_particle(particle_candidate):
            particle = particle_candidate
            particle["~included"] = True
            return {
                "_type": "subject",
                "subject": create_subject(dtree),
                "particle": create_particle(particle)
            }
    dtree = collect_flat_subject_parts(dtree)
    if is_enquoted(dtree):
        quotes = create_enclosing_quotes(dtree)
        return {
                "_type": "quoted-group",
                "content": create_subject(dtree),
                "quotes": quotes
            }
    return {
            "_type": "subject",
            "_token": dtree
        }


def create_predicate(dtree, parent=None):
    if has_sustainable_introduction(dtree):
        introduction = find_sustainable_introduction(dtree)
        tokens = tokens_list(dtree)
        main_token = tokens[0]
        for ix, token in enumerate(tokens):
            if ix == len(introduction):
                break
            token["~included"] = True
            if token["id"] < main_token["id"]:
                main_token = token
        main_token["text"] = ' '.join(introduction).capitalize()
        introduction_node = {
            "_type": "introduction",
            "_token": main_token
        }
        core_node = create_predicate(dtree)
        return {
            "_type": "predicate",
            "introduction": introduction_node,
            "predicate": core_node
        }
    children = not_included_children(dtree)
    if is_aux_part_of_compound_verb_predicate(dtree):
        main_part = None
        for main_part_candidate in not_included_children(dtree):
            if is_main_verb(main_part_candidate):
                main_part = main_part_candidate
                children += not_included_children(main_part)
                break
    elif is_aux_part_of_compound_nominative_predicate(dtree):
        main_part = None
        for main_part_candidate in not_included_children(dtree):
            if is_main_part_of_compound_nominative_predicate(main_part_candidate, dtree):
                main_part = main_part_candidate
                children += not_included_children(main_part)
                break
    elif is_main_part_of_compound_nominative_predicate(dtree, parent):
        for aux_part_candidate in not_included_children(dtree):
            if is_aux_part_of_compound_nominative_predicate(aux_part_candidate):
                aux_part = aux_part_candidate
                children += not_included_children(aux_part)
                break
    if has_introduction(dtree):
        introduction = find_introduction(dtree)
        introduction["~included"] = True
        return {
            "_type": "predicate",
            "introduction": create_introduction(introduction),
            "predicate": create_predicate(dtree)
        }
    for subordinative_candidate in children:
        if is_subordinative(subordinative_candidate, dtree):
            subordinative_candidate["~included"] = True
            subordinative, role = create_subordinative(subordinative_candidate, dtree)
            result = {
                "_type": "predicate",
                "predicate": create_predicate(dtree),
                role: subordinative
            }
            return result
    for direct_speech_candidate in children:
        if is_subordinated_direct_speech(direct_speech_candidate, dtree):
            direct_speech_candidate["~included"] = True
            direct_speech = create_subordinated_direct_speech(direct_speech_candidate, dtree)
            result = {
                "_type": "predicate",
                "predicate": create_predicate(dtree),
                "indirect-object": direct_speech
            }
            return result
    homogeneous_parts = [dtree]
    for homogeneous_candidate in not_included_children(dtree):
        if is_homogeneous_predicates_part(homogeneous_candidate, dtree):
            homogeneous_parts.append(homogeneous_candidate)
    if len(homogeneous_parts) > 1:
        if has_indirect_object(homogeneous_parts[1]):
            for indirect_object_candidate in reversed(not_included_children(homogeneous_parts[1])):
                if is_indirect_object(indirect_object_candidate, homogeneous_parts[1]) and has_coordinative_conjunction(homogeneous_parts[1]) \
                        and not (
                        is_aux_part_of_compound_verb_predicate(dtree) and is_main_verb(indirect_object_candidate)) \
                        and not (is_aux_part_of_compound_verb_predicate(homogeneous_parts[1]) and is_main_verb(indirect_object_candidate)) \
                        and directly_follows(homogeneous_parts[-1], indirect_object_candidate):
                    indirect_object = indirect_object_candidate
                    indirect_object["~included"] = True
                    return {
                        "_type": "predicate",
                        "predicate": create_predicate(dtree),
                        "indirect-object": create_object(indirect_object)
                    }
        for adverbial_candidate in reduce(list.__add__, map(not_included_children, homogeneous_parts)):
            if is_adverbial(adverbial_candidate, dtree) and is_adverbial_specific_nominative(adverbial_candidate, dtree) and has_coordinative_conjunction(homogeneous_parts[1]) \
                    and not (is_aux_part_of_compound_verb_predicate(dtree) and is_main_verb(adverbial_candidate)) \
                    and not (
                    is_aux_part_of_compound_verb_predicate(homogeneous_parts[1]) and is_main_verb(adverbial_candidate)):
                adverbial = adverbial_candidate
                adverbial["~included"] = True
                return {
                    "_type": "predicate",
                    "predicate": create_predicate(dtree),
                    "adverbial": create_adverbial(adverbial)
                }
        result = {
            "_type": "homogeneous-predicates"
        }
        for part in homogeneous_parts:
            part["~included"] = True
        conjunction_parts = find_conjunction_parts_between(*homogeneous_parts)
        if conjunction_parts:
            conjunction = create_conjunction(*conjunction_parts)
            result["joined-by"] = conjunction
        for ix, part in enumerate(homogeneous_parts):
            result[f"{constituency_tree_builder.lists._parts_names[ix]}-predicate"] = create_predicate(part, dtree)
        return result
    for indirect_object_candidate in reversed(children):
        if (is_indirect_object(indirect_object_candidate, dtree)
                or (is_aux_part_of_compound_nominative_predicate(dtree)
                    and main_part is not None
                    and is_main_part_of_compound_nominative_predicate(main_part, dtree)
                    and is_indirect_object(indirect_object_candidate, main_part)
                    and not is_atomic_nominative_part(indirect_object_candidate, main_part)))\
            and not (is_aux_part_of_compound_verb_predicate(dtree) and is_main_verb(indirect_object_candidate)) \
            and not (is_aux_part_of_compound_nominative_predicate(dtree) and indirect_object_candidate == main_part) \
            and not indirect_object_candidate["pos"] == "ADJ":
            indirect_object = indirect_object_candidate
            indirect_object["~included"] = True
            return {
                "_type": "predicate",
                "predicate": create_predicate(dtree),
                "indirect-object": create_object(indirect_object)
            }
    adverbial_candidates = list(reversed(children))
    for ix, adverbial_candidate in enumerate(adverbial_candidates):
        if (is_adverbial(adverbial_candidate, dtree) and not is_aux_part_of_compound_nominative_predicate(dtree) \
            or is_adverbial_specific_nominative(adverbial_candidate, dtree) or has_adverbial_specific_preposition(adverbial_candidate) \
            or adverbial_candidate["pos"] == "ADV") \
                and not (is_aux_part_of_compound_nominative_predicate(dtree) and adverbial_candidate["lemma"] == "так"):
            if not is_adverbial_specific_nominative(adverbial_candidate, dtree) \
                    and ix != len(adverbial_candidates) - 1 \
                    and is_adverbial_specific_nominative(adverbial_candidates[ix + 1], dtree):
                continue
            adverbial = adverbial_candidate
            adverbial["~included"] = True
            return {
                "_type": "predicate",
                "predicate": create_predicate(dtree),
                "adverbial": create_adverbial(adverbial)
            }
    if is_main_part_of_compound_nominative_predicate(dtree):
        for definition_candidate in reversed(not_included_children(dtree)):
            if is_definition(definition_candidate, dtree):
                definition = definition_candidate
                definition["~included"] = True
                return {
                    "_type": "predicate",
                    "predicate": create_predicate(dtree),
                    "definition": create_definition(definition)
                }
    if is_aux_part_of_compound_nominative_predicate(dtree):
        for definition_candidate in reversed(children):
            if is_definition(definition_candidate, main_part):
                definition = definition_candidate
                definition["~included"] = True
                return {
                    "_type": "predicate",
                    "predicate": create_predicate(dtree),
                    "definition": create_definition(definition)
                }
    for direct_object_candidate in reversed(children):
        if is_direct_object(direct_object_candidate, dtree):
            direct_object = direct_object_candidate
            direct_object["~included"] = True
            return {
                "_type": "predicate",
                "predicate": create_predicate(dtree),
                "direct-object": create_object(direct_object)
            }
    for particle_candidate in reversed(children):
        if is_particle(particle_candidate):
            particle = particle_candidate
            particle["~included"] = True
            return {
                "_type": "predicate",
                "predicate": create_predicate(dtree),
                "particle": create_particle(particle)
            }
    if is_aux_part_of_compound_verb_predicate(dtree):
        for main_part in not_included_children(dtree):
            if is_main_verb(main_part):
                main_part["~included"] = True
                dtree["~included"] = True
                return {
                    "_type": "compound-predicate",
                    "main-verb": create_predicate(main_part),
                    "aux-verb": create_predicate(dtree)
                }
    if is_main_part_of_compound_verb_predicate(dtree):
        for aux_part_candidate in not_included_children(dtree):
            if aux_part_candidate["lemma"].lower() in constituency_tree_builder.lists._aux_verb_specific_lemmas:
                aux_part = aux_part_candidate
                aux_part["~included"] = True
                dtree["~included"] = True
                return {
                    "_type": "compound-predicate",
                    "main-verb": create_predicate(dtree),
                    "aux-verb": create_predicate(aux_part)
                }
    elif is_main_part_of_compound_nominative_predicate(dtree, parent):
        for aux_part_candidate in not_included_children(dtree):
            if is_aux_part_of_compound_nominative_predicate(aux_part_candidate):
                aux_part_candidate["~included"] = True
                dtree["~included"] = True
                return {
                    "_type": "compound-predicate",
                    "main-nominative": create_main_nominative(dtree),
                    "aux-verb": create_predicate(aux_part_candidate)
                }
        return {
            "_type": "compound-predicate",
            "main-nominative": create_main_nominative(dtree)
        }
    elif is_aux_part_of_compound_nominative_predicate(dtree):
        for main_part in not_included_children(dtree):
            if is_main_part_of_compound_nominative_predicate(main_part, dtree):
                main_part["~included"] = True
                return {
                    "_type": "compound-predicate",
                    "main-nominative": create_main_nominative(main_part),
                    "aux-verb": create_predicate(dtree)
                }
    dtree["~included"] = True
    return {
        "_type": "predicate",
        "_token": dtree
    }


def create_main_nominative(dtree):
    homogeneous_parts = [dtree]
    for homogeneous_candidate in not_included_children(dtree):
        if is_homogeneous_nominative_part(homogeneous_candidate, dtree):
            homogeneous_parts.append(homogeneous_candidate)
    if len(homogeneous_parts) > 1:
        result = {
            "_type": "homogeneous-main-nominatives"
        }
        for part in homogeneous_parts:
            part["~included"] = True
        conjunction_parts = find_conjunction_parts_between(*homogeneous_parts)
        if conjunction_parts:
            conjunction = create_conjunction(*conjunction_parts)
            result["joined-by"] = conjunction
        for ix, part in enumerate(homogeneous_parts):
            result[f"{constituency_tree_builder.lists._parts_names[ix]}-main-nominative"] = create_main_nominative(part)
        return result
    for indirect_object_candidate in reversed(not_included_children(dtree)):
        if is_indirect_object(indirect_object_candidate, dtree) \
                and not is_flat_object_part(indirect_object_candidate, dtree) \
                and not is_flat_object_head(dtree):
            indirect_object = indirect_object_candidate
            indirect_object["~included"] = True
            return {
                "_type": "main-nominative",
                "main-nominative": create_main_nominative(dtree),
                "indirect-object": create_object(indirect_object)
            }
    for particle_candidate in reversed(not_included_children(dtree)):
        if is_particle(particle_candidate) and particle_candidate["lemma"].lower() != "все":
            particle = particle_candidate
            particle["~included"] = True
            return {
                "_type": "main-nominative",
                "main-nominative": create_main_nominative(dtree),
                "particle": create_particle(particle)
            }
    for preposition_candidate in not_included_children(dtree):
        if preposition_candidate["deprel"] in constituency_tree_builder.lists._preposition_deprels:
            preposition = preposition_candidate
            preposition["~included"] = True
            return {
                "_type": "main-nominative",
                "main-nominative": create_main_nominative(dtree),
                "preposition": create_preposition(preposition)
            }
    flat_parts = [dtree]
    for flat_part in filter(lambda x: is_atomic_nominative_part(x, dtree), not_included_children(dtree)):
        flat_part["~included"] = True
        flat_parts.append(flat_part)
    if len(flat_parts) > 1:
        flat_parts.sort(key=lambda x: x["id"])
        dtree["text"] = ' '.join([part["text"] for part in flat_parts])
    if is_enquoted(dtree):
        quotes = create_enclosing_quotes(dtree)
        return {
            "_type": "quoted-group",
            "content": create_main_nominative(dtree),
            "quotes": quotes
        }
    return {
        "_type": "predicate",
        "_token": dtree
    }


def create_object(dtree):
    if is_enquoted(dtree) and is_verb_predicate(dtree):
        quotes = create_enclosing_quotes(dtree)
        return {
            "_type": "quoted-group",
            "content": create_core(dtree),
            "quotes": quotes
        }
    homogeneous_parts = [dtree]
    for homogeneous_candidate in not_included_children(dtree):
        if homogeneous_candidate["deprel"] in constituency_tree_builder.lists._homogeneous_part_deprels:
            homogeneous_parts.append(homogeneous_candidate)
    if len(homogeneous_parts) > 1:
        if has_preposition(homogeneous_parts[0]) and not any(map(has_preposition, homogeneous_parts[1:])):
            for preposition_candidate in not_included_children(homogeneous_parts[0]):
                if is_preposition(preposition_candidate):
                    preposition = preposition_candidate
                    preposition["~included"] = True
                    return {
                        "_type": "object",
                        "object": create_object(dtree),
                        "preposition": create_preposition(preposition)
                    }
        result = {
            "_type": "homogeneous-objects"
        }
        for part in homogeneous_parts:
            part["~included"] = True
        conjunction_parts = find_conjunction_parts_between(*homogeneous_parts)
        if conjunction_parts:
            conjunction = create_conjunction(*conjunction_parts)
            result["joined-by"] = conjunction
        for ix, part in enumerate(homogeneous_parts):
            result[f"{constituency_tree_builder.lists._parts_names[ix]}-object"] = create_object(part)
        return result
    if has_introduction(dtree):
        introduction = find_introduction(dtree)
        introduction["~included"] = True
        return {
            "_type": "object",
            "introduction": create_introduction(introduction),
            "object": create_object(dtree)
        }
    if len(not_included_children(dtree)) > 0 and not_included_children(dtree, natural_order=True)[0]["lemma"] == "как":
        comparative_conjunction = not_included_children(dtree, natural_order=True)[0]
        comparative_conjunction["~included"] = True
        return {
            "_type": "comparative-clause",
            "object": create_object(dtree),
            "joined-by": create_conjunction(comparative_conjunction)
        }
    children = list(reversed(not_included_children(dtree)))
    if dtree["pos"] == "SYM":
        for child in children:
            if child["pos"] == "NUM":
                children.extend(not_included_children(child))
    for subordinative_candidate in children:
        if is_subordinative(subordinative_candidate, dtree):
            subordinative_candidate["~included"] = True
            subordinative, role = create_subordinative(subordinative_candidate, dtree)
            result = {
                "_type": "object",
                "object": create_object(dtree),
                role: subordinative
            }
            return result
    for indirect_object_candidate in children:
        if is_indirect_object(indirect_object_candidate, dtree) \
                and not is_flat_object_part(indirect_object_candidate, dtree) \
                and not is_flat_object_head(dtree):
            indirect_object = indirect_object_candidate
            indirect_object["~included"] = True
            return {
                "_type": "object",
                "object": create_object(dtree),
                "indirect-object": create_object(indirect_object)
            }
    for adverbial_candidate in children:
        if is_adverbial(adverbial_candidate, dtree):
            adverbial = adverbial_candidate
            adverbial["~included"] = True
            return {
                "_type": "object",
                "object": create_object(dtree),
                "adverbial": create_adverbial(adverbial)
            }
    for direct_object_candidate in children:
        if is_direct_object(direct_object_candidate, dtree) \
                and not is_flat_object_part(direct_object_candidate, dtree):
            direct_object = direct_object_candidate
            direct_object["~included"] = True
            return {
                "_type": "object",
                "object": create_object(dtree),
                "direct-object": create_object(direct_object)
            }
    for particle_candidate in children:
        if is_particle(particle_candidate):
            particle = particle_candidate
            particle["~included"] = True
            return {
                "_type": "object",
                "object": create_object(dtree),
                "particle": create_particle(particle)
            }
    for preposition_candidate in children:
        if preposition_candidate["deprel"] in constituency_tree_builder.lists._preposition_deprels:
            preposition = preposition_candidate
            preposition["~included"] = True
            return {
                "_type": "object",
                "object": create_object(dtree),
                "preposition": create_preposition(preposition)
            }
    for definition_candidate in children:
        if is_definition(definition_candidate, dtree):
            definition = definition_candidate
            definition["~included"] = True
            return {
                "_type": "object",
                "object": create_object(dtree),
                "definition": create_definition(definition)
            }
    dtree = collect_flat_object_parts(dtree)
    if is_enquoted(dtree):
        quotes = create_enclosing_quotes(dtree)
        return {
            "_type": "quoted-group",
            "content": create_object(dtree),
            "quotes": quotes
        }
    if is_enclosed_in_brackets(dtree):
        brackets = create_enclosing_brackets(dtree)
        return {
            "_type": "bracketed-group",
            "content": create_object(dtree),
            "brackets": brackets
        }
    return {
        "_type": "object",
        "_token": dtree
    }


def create_adverbial(dtree):
    homogeneous_parts = [dtree]
    for homogeneous_candidate in not_included_children(dtree):
        if homogeneous_candidate["deprel"] in constituency_tree_builder.lists._homogeneous_part_deprels:
            homogeneous_parts.append(homogeneous_candidate)
    if len(homogeneous_parts) > 1:
        if has_preposition(homogeneous_parts[0]) and not any(map(has_preposition, homogeneous_parts[1:])):
            for preposition_candidate in not_included_children(homogeneous_parts[0]):
                if is_preposition(preposition_candidate):
                    preposition = preposition_candidate
                    preposition["~included"] = True
                    return {
                        "_type": "adverbial",
                        "adverbial": create_adverbial(dtree),
                        "preposition": create_preposition(preposition)
                    }
        result = {
            "_type": "homogeneous-adverbials"
        }
        for part in homogeneous_parts:
            part["~included"] = True
        conjunction_parts = find_conjunction_parts_between(*homogeneous_parts)
        if conjunction_parts:
            conjunction = create_conjunction(*conjunction_parts)
            result["joined-by"] = conjunction
        for ix, part in enumerate(homogeneous_parts):
            result[f"{constituency_tree_builder.lists._parts_names[ix]}-adverbial"] = create_adverbial(part)
        return result
    for subordinative_candidate in reversed(not_included_children(dtree)):
        if is_subordinative(subordinative_candidate, dtree):
            subordinative_candidate["~included"] = True
            subordinative, role = create_subordinative(subordinative_candidate, dtree)
            if role == "adverbial":
                role = "sub-adverbial"
            result = {
                "_type": "adverbial",
                "adverbial": create_adverbial(dtree),
                role: subordinative
            }
            return result
    for indirect_object_candidate in reversed(not_included_children(dtree)):
        if is_indirect_object(indirect_object_candidate, dtree):
            indirect_object = indirect_object_candidate
            indirect_object["~included"] = True
            if is_adverbial_head_as_preposition(dtree):
                return {
                    "_type": "adverbial",
                    "adverbial": create_adverbial(indirect_object),
                    "preposition": create_preposition(dtree)
                }
            return {
                "_type": "adverbial",
                "adverbial": create_adverbial(dtree),
                "indirect-object": create_object(indirect_object)
            }
    for adverbial_candidate in reversed(not_included_children(dtree)):
        if is_adverbial(adverbial_candidate, dtree):
            adverbial = adverbial_candidate
            adverbial["~included"] = True
            return {
                "_type": "adverbial",
                "adverbial": create_adverbial(dtree),
                "sub-adverbial": create_adverbial(adverbial)
            }
    for direct_object_candidate in reversed(not_included_children(dtree)):
        if is_direct_object(direct_object_candidate, dtree) \
                and not is_flat_object_part(direct_object_candidate, dtree):
            direct_object = direct_object_candidate
            direct_object["~included"] = True
            return {
                "_type": "adverbial",
                "adverbial": create_adverbial(dtree),
                "direct-object": create_object(direct_object)
            }
    for particle_candidate in reversed(not_included_children(dtree)):
        if is_particle(particle_candidate):
            particle = particle_candidate
            particle["~included"] = True
            return {
                "_type": "adverbial",
                "adverbial": create_adverbial(dtree),
                "particle": create_particle(particle)
            }
    for preposition_candidate in not_included_children(dtree):
        if preposition_candidate["deprel"] in constituency_tree_builder.lists._preposition_deprels:
            preposition = preposition_candidate
            preposition["~included"] = True
            return {
                "_type": "adverbial",
                "adverbial": create_adverbial(dtree),
                "preposition": create_preposition(preposition)
            }
    for definition_candidate in reversed(not_included_children(dtree)):
        if is_definition(definition_candidate, dtree):
            definition = definition_candidate
            definition["~included"] = True
            return {
                "_type": "adverbial",
                "adverbial": create_adverbial(dtree),
                "definition": create_definition(definition)
            }
    dtree = collect_flat_adverbial_parts(dtree)
    return {
        "_type": "adverbial",
        "_token": dtree
    }


def create_definition(dtree):
    homogeneous_parts = [dtree]
    for homogeneous_candidate in not_included_children(dtree):
        if homogeneous_candidate["deprel"] in constituency_tree_builder.lists._homogeneous_part_deprels:
            homogeneous_candidate["~included"] = True
            homogeneous_parts.append(homogeneous_candidate)
    if len(homogeneous_parts) > 1:
        result = {
            "_type": "homogeneous-definitions"
        }
        for ix, part in enumerate(homogeneous_parts):
            result[f"{constituency_tree_builder.lists._parts_names[ix]}-definition"] = create_definition(part)
        conjunction_parts = find_conjunction_parts_between(*homogeneous_parts)
        if conjunction_parts:
            conjunction = create_conjunction(*conjunction_parts)
            result["joined-by"] = conjunction
        return result
    for indirect_object_candidate in reversed(not_included_children(dtree)):
        if is_indirect_object(indirect_object_candidate, dtree):
            indirect_object = indirect_object_candidate
            indirect_object["~included"] = True
            return {
                "_type": "definition",
                "definition": create_definition(dtree),
                "indirect-object": create_object(indirect_object)
            }
    for adverbial_candidate in reversed(not_included_children(dtree)):
        if is_adverbial(adverbial_candidate, dtree):
            adverbial = adverbial_candidate
            adverbial["~included"] = True
            return {
                "_type": "definition",
                "definition": create_definition(dtree),
                "adverbial": create_adverbial(adverbial)
            }
    for definition_candidate in reversed(not_included_children(dtree)):
        if is_definition(definition_candidate, dtree):
            definition = definition_candidate
            definition["~included"] = True
            return {
                "_type": "definition",
                "definition": create_definition(dtree),
                "sub-definition": create_definition(definition)
            }
    for particle_candidate in reversed(not_included_children(dtree)):
        if is_particle(particle_candidate):
            particle = particle_candidate
            particle["~included"] = True
            return {
                "_type": "definition",
                "definition": create_definition(dtree),
                "particle": create_particle(particle)
            }
    dtree = collect_flat_definition_parts(dtree)
    if is_enquoted(dtree):
        quotes = create_enclosing_quotes(dtree)
        return {
            "_type": "quoted-group",
            "content": create_definition(dtree),
            "quotes": quotes
        }
    return {
        "_type": "definition",
        "_token": dtree
    }


def create_enclosing_quotes(dtree):
    children = not_included_children(dtree, natural_order=True)
    left, right = None, None
    for child in children:
        if child["text"] in constituency_tree_builder.lists._opening_quotes:
            child["~included"] = True
            left = child
    for child in reversed(children):
        if child["text"] in constituency_tree_builder.lists._closing_quotes:
            child["~included"] = True
            right = child
    assert left is not None and right is not None
    left["text"] = f"{left['text']} {right['text']}"
    return {
        "_type": "punct",
        "_token": left
    }


def create_enclosing_brackets(dtree):
    children = tokens_list(dtree)
    left, right = None, None
    for child in children:
        if child["text"] in constituency_tree_builder.lists._opening_brackets:
            child["~included"] = True
            left = child
    for child in reversed(children):
        if child["text"] in constituency_tree_builder.lists._closing_brackets:
            child["~included"] = True
            right = child
    assert left is not None and right is not None
    left["text"] = f"{left['text']} {right['text']}"
    return {
        "_type": "punct",
        "_token": left
    }


def create_subordinative(dtree, main_word):
    if is_enclosed_in_brackets(dtree):
        brackets = create_enclosing_brackets(dtree)
        subordinative, role = create_subordinative(dtree, main_word)
        return {
            "_type": "bracketed-group",
            "content": subordinative,
            "brackets": brackets
        }, role
    conjunction_parts = find_conjunction_parts_between(dtree, main_word)
    if conjunction_parts:
        conjunction = create_conjunction(*conjunction_parts)
    core = create_core(dtree)
    node = {
        "_type": "subordinative",
        "sentence": core,
    }
    if conjunction_parts:
        node["joined-by"] = conjunction
        conjunction_text = conjunction["_token"]["text"]
        if conjunction_text in constituency_tree_builder.lists._definitive_subordinative_conjunctions:
            type_ = "definition"
        elif conjunction_text in constituency_tree_builder.lists._direct_object_subordinative_conjunctions:
            type_ = "direct-object"
        elif conjunction_text in constituency_tree_builder.lists._adverbial_subordinative_conjunctions:
            type_ = "adverbial"
        else:
            type_ = "indirect-object"
    else:
        type_ = "indirect-object"
    return node, type_


def create_subordinated_direct_speech(dtree, main_word):
    children = not_included_children(dtree, natural_order=True)
    joinings = []
    if dtree["id"] < main_word["id"]:
        joining = children.pop()
        joinings.append(joining)
        if joining["text"] == "—":
            if children[-1]["text"] == ",":
                joinings.append(children.pop())
    else:
        joinings.append(children.pop(0))
    if children[0]["text"] in constituency_tree_builder.lists._opening_quotes:
        joinings.append(children[0])
    if children[-1]["text"] in constituency_tree_builder.lists._closing_quotes:
        joinings.append(children[-1])
    for joining in joinings:
        joining["~included"] = True
    joinings[0]["text"] = ' '.join([j["text"] for j in sorted(joinings, key=lambda x: x["id"])])
    joined_by = {
        "_type": "punct",
        "_token": joinings[0]
    }
    return {
        "_type": "direct-speech",
        "content": create_sentence(dtree),
        "joined-by": joined_by
    }


def create_conjunction(*parts):
    for part in parts:
        part["~included"] = True
    text = ' '.join([part['text'] for part in sorted(parts, key=lambda x: x["id"])])
    base_token = parts[0]
    base_token['text'] = text
    if all(map(lambda x: x["deprel"] == "punct", parts)):
        return {
            "_type": "punct",
            "_token": base_token
        }
    return {
        "_type": f"{constituency_tree_builder.lists._conjunction_types[text.lower()]}-conjunction",
        "_token": base_token
    }


def create_punct(dtree):
    return {
        "_type": "punct",
        "_token": dtree
    }


def create_preposition(dtree):
    parts = not_included_children(dtree)
    if not parts:
        return {
            "_type": "preposition",
            "_token": dtree
        }
    parts.append(dtree)
    for part in parts:
        part["~included"] = True
    parts.sort(key=lambda x: x["id"])
    return {
        "_type": "preposition",
        **{f"{constituency_tree_builder.lists._parts_names[ix]}-part": create_preposition(part) for ix, part in enumerate(parts)}
    }


def create_particle(dtree):
    text = dtree["lemma"].lower()
    type_ = constituency_tree_builder.lists._particle_by_type[text]
    return {
        "_type": type_,
        "_token": dtree
    }


def collect_flat_subject_parts(dtree):
    flats = [dtree]
    children = not_included_children(dtree)
    for child in children:
        is_flat_part = child["deprel"].startswith("flat") or is_atomic_nominative_part(child, dtree)
        if not is_flat_part:
            continue
        nodes = [child]
        while nodes:
            node = nodes.pop()
            nodes.extend(not_included_children(node))
            flats.append(node)
    for flat in flats:
        flat["~included"] = True
    dtree["text"] = ' '.join([f["text"] for f in sorted(flats, key=lambda x: x["id"])])
    return dtree


def collect_flat_object_parts(dtree):
    flats = [dtree]
    if is_flat_object_head(dtree):
        flats.extend(not_included_children(dtree))
    else:
        nodes = not_included_children(dtree)
        while nodes:
            node = nodes.pop()
            if is_flat_object_part(node, dtree):
                flats.append(node)
                for child in not_included_children(node):
                    if child["lemma"] in {"—", "-"}:
                        ids = [token["id"] for token in flats]
                        if min(ids) < child["id"] < max(ids):
                            flats.append(child)
                nodes.extend(not_included_children(node))
    for flat in flats:
        flat["~included"] = True
    dtree["text"] = ' '.join(map(lambda x: x["text"], sorted(flats, key=lambda x: x["id"])))
    dtree["text"] = dtree["text"].replace(' - ', '-')
    dtree["text"] = dtree["text"].replace(' -', '-')
    return dtree


def collect_flat_adverbial_parts(dtree):
    return collect_flat_object_parts(dtree)


def collect_flat_definition_parts(dtree):
    return collect_flat_object_parts(dtree)
