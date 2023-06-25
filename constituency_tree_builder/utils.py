# Copyright © 2023 Anatoliy Poletaev, Ilya Paramonov, Elena Boychuk. All rights reserved.

from copy import deepcopy
from functools import reduce

from constituency_tree_builder.lists import _conjunction_deprels,\
    _subordinative_conjunction_lemmas, _opening_brackets, _closing_brackets, \
    _opening_quotes, _closing_quotes, _conjunction_types,\
    _direct_speech_border_tokens


def find_conjunction_parts_between(*tokens):
    tokens = list(tokens)
    tokens.sort(key=lambda x: x["id"])
    start, end = tokens[0]["id"], tokens[-1]["id"]
    result = []
    children = reduce(list.__add__, map(not_included_children, tokens))
    children.sort(key=lambda x: x["id"])
    has_conjunctive_word = False
    for child in children:
        if child["text"] in (_opening_brackets | _closing_brackets):
            continue
        if child["deprel"] in _conjunction_deprels:
            result.append(child)
            if child["text"].lower() == "если":
                has_conjunctive_word = True
            for part in not_included_children(child):
                if part["deprel"] == "fixed":
                    result.append(part)
                elif part["pos"] in {"PART", "ADP"}:
                    result.append(part)
            continue
        if child["lemma"] in _subordinative_conjunction_lemmas and not has_conjunctive_word:
            result.append(child)
            for part in not_included_children(child):
                if part["deprel"] == "fixed":
                    result.append(part)
                elif part["pos"] in {"PART", "ADP"}:
                    result.append(part)
            continue
        if child["deprel"] == "punct" and start < child["id"] < end \
                and child["lemma"] not in (_opening_quotes | _closing_quotes):
            result.append(child)
            continue
        if get_full_text(tokens_list(child)).lower() in {"не только"}:
            result.extend(tokens_list(child))
            continue
    if get_full_text(result) == ", а":
        negative_particle_candidate = tokens_list(tokens[0])[0]
        if negative_particle_candidate["lemma"] == "не":
            negative_particle = negative_particle_candidate
            result.insert(0, negative_particle)
    return result


def tokens_list(dtree):
    result = []
    nodes = [dtree]
    while nodes:
        node = nodes.pop(0)
        nodes.extend(not_included_children(node))
        result.append(node)
    result.sort(key=lambda x: x["id"])
    return result


def not_included_children(dtree, natural_order=False):
    children = [c for c in dtree["~children"] if not c["~included"]]
    key = (lambda x: x["id"]) if natural_order else \
        (lambda x: [abs(x["id"] - dtree["id"]), x["id"]])
    return sorted(children, key=key)


def all_children(dtree, natural_order=False):
    children = [c for c in dtree["~children"]]
    key = (lambda x: x["id"]) if natural_order else \
        (lambda x: [abs(x["id"] - dtree["id"]), x["id"]])
    return sorted(children, key=key)


def get_full_text(tokens):
    return ' '.join([t["text"] for t in sorted(tokens, key=lambda x: x["id"])])


def json_to_dependency_tree(json_):

    def find_children(word):
        return list(filter(lambda x: x["head_id"] == word["id"] and x != word, json_))
    try:
        root = next(filter(lambda x: x["deprel"] == "root", json_))
    except StopIteration:
        root = json_[0]
        root["~included"] = False
        root["~children"] = []
        return root
    words_to_process = [root]
    while words_to_process:
        word = words_to_process.pop()
        children = find_children(word)
        words_to_process.extend(children)
        word["~children"] = children
        word["~included"] = False
    return root


def clean_constituency_tree(ctree):
    ctree = deepcopy(ctree)
    nodes = [ctree]
    tokens = []
    while nodes:
        node = nodes.pop()
        for key in filter(lambda x: not (x.startswith("_") or x.startswith("~")), node.keys()):
            nodes.append(node[key])
        if "_token" in node:
            tokens.append(node["_token"])
    for token in tokens:
        token.pop("~included")
        token.pop("~children")
        token.pop("head_id")
        token.pop("id")
    return ctree


def split_heterogeneous_conjunction_with_adversative(parts):
    first_coordinative, adversative, second_coordinative = [], [], []
    found_first_coordinative, found_adversative, found_second_coordinative = False, False, False
    for part in parts:
        if part["lemma"] == ",":
            if len(first_coordinative) == 0:
                first_coordinative.append(part)
            elif len(adversative) == 0:
                adversative.append(part)
            elif len(second_coordinative) == 0:
                second_coordinative.append(part)
            else:
                return None, None, None
        elif part["lemma"] == ";":
            if found_first_coordinative and len(adversative) == 0:
                adversative.append(part)
            else:
                return None, None, None
        elif part["lemma"] in _conjunction_types:
            type_ = _conjunction_types[part["lemma"]]
            if type_ == "coordinative":
                if not found_first_coordinative:
                    first_coordinative.append(part)
                    found_first_coordinative = True
                elif found_first_coordinative and not found_adversative:
                    return None, None, None
                elif found_adversative and not found_second_coordinative:
                    second_coordinative.append(part)
                    found_second_coordinative = True
                else:
                    return None, None, None
            elif type_ == "adversative":
                if found_first_coordinative and not found_adversative:
                    adversative.append(part)
                    found_adversative = True
                else:
                    return None, None, None
        else:
            return None, None, None
    if len(first_coordinative) == 0 or len(second_coordinative) == 0 or len(adversative) == 0:
        return None, None, None
    return first_coordinative, adversative, second_coordinative


def collect_direct_speech_head_parts(dtree):
    opening_quote, closing_quote, border_tokens, indirect_speech = None, None, [], None
    for child in not_included_children(dtree, natural_order=True):
        if child["text"] in _opening_quotes:
            if opening_quote is None:
                opening_quote = child
            else:
                return None, None, [], None
        elif child["text"] in _closing_quotes:
            if closing_quote is None:
                closing_quote = child
            else:
                return None, None, [], None
        elif child["deprel"] in {"parataxis"}:
            if closing_quote is not None:
                if indirect_speech is not None:
                    return None, None, [], None
                indirect_speech = child
                for border_candidate in not_included_children(indirect_speech, natural_order=True):
                    if border_candidate["pos"] != "PUNCT":
                        break
                    if border_candidate["lemma"] in _direct_speech_border_tokens:
                        border_tokens.append(border_candidate)
    return indirect_speech, opening_quote, closing_quote, border_tokens
