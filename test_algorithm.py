#!/usr/bin/env python3
# Copyright © 2023 Anatoliy Poletaev, Ilya Paramonov, Elena Boychuk. All rights reserved.

import json
import os
from copy import deepcopy
from functools import reduce

from dependency_parsing import stanza_json as stanza_parser,\
    spacy_json as spacy_parser, natasha_json as natasha_parser
from constituency_tree_builder.creator import dependency_tree_to_constituency_tree
from constituency_tree_builder.utils import json_to_dependency_tree


def format_constituency_tree(ctree):
    ctree = deepcopy(ctree)
    nodes = [ctree]
    while nodes:
        node = nodes.pop()
        for key in filter(lambda x: not x.startswith("_"), node.keys()):
            nodes.append(node[key])
        node["type"] = node.pop("_type")
        if "_token" in node:
            token = node.pop("_token")
            node["text"] = token["text"]
    return ctree


def calculate_constituents_metrics(parsed_ctree, real_ctree):
    correct_constituents = 0
    parsed_constituents, real_constituents = get_constituents(parsed_ctree), get_constituents(real_ctree)
    constituents_in_parsed, constituents_in_real = len(parsed_constituents), len(real_constituents)
    for real_constituent in real_constituents:
        if real_constituent in parsed_constituents:
            correct_constituents += 1
            parsed_constituents.remove(real_constituent)
    return correct_constituents, constituents_in_parsed, constituents_in_real


def calculate_tagging_metrics(parsed_ctree, real_ctree):
    parsed_words, real_words = get_words(parsed_ctree), get_words(real_ctree)
    correct_tags, total_tags = 0, len(real_words)
    for word in parsed_words:
        if word in real_words:
            correct_tags += 1
            real_words.remove(word)
    return correct_tags, total_tags


def get_constituents(ctree_node):
    if "text" in ctree_node:
        return [(ctree_node["type"], [ctree_node["text"]])]
    ctree_node = deepcopy(ctree_node)
    node_type = ctree_node.pop("type")
    words = [text for label, text in get_words(ctree_node)]
    result = [(node_type, words)]
    for child in ctree_node.values():
        result.extend(get_constituents(child))
    return sorted(result)


def get_words(ctree_node):
    if "text" in ctree_node:
        return [(ctree_node["type"], ctree_node["text"])]
    ctree_node = deepcopy(ctree_node)
    ctree_node.pop("type", None)
    return sorted(reduce(lambda x, y: x + y, map(get_words, ctree_node.values())))


with open(os.path.join("sentences", "opencorpora-sample.json")) as s:
    opencorpora = json.load(s)


parsers = [(stanza_parser, "Stanza"), (spacy_parser, "SpaCy"), (natasha_parser, "Natasha")]


for dependency_parser, parser_name in parsers:
    print(f"Metrics using {parser_name} dependency parser:")
    correct = 0
    correct_structure = 0
    correct_constituents, total_parsed_constituents, total_real_constituents = 0, 0, 0
    correct_words_tagged, total_words = 0, 0
    chain = False
    for sentence in opencorpora:
        text = sentence["text"]
        real = sentence["tree"]
        dependency_tree = json_to_dependency_tree(dependency_parser(text))
        parsed = format_constituency_tree(dependency_tree_to_constituency_tree(dependency_tree))
        correct_const_lalebed, total_pc, total_rc = calculate_constituents_metrics(parsed, real)
        correct_constituents += correct_const_lalebed
        total_parsed_constituents += total_pc
        total_real_constituents += total_rc
        correct_tags_, words_ = calculate_tagging_metrics(parsed, real)
        correct_words_tagged += correct_tags_
        total_words += words_
        if parsed == real:
            correct += 1
    print(f"\nFully correct: {correct}/{len(opencorpora)} ({round(correct / len(opencorpora), 2)})")
    precision, recall = correct_constituents / total_parsed_constituents, correct_constituents / total_real_constituents
    f_1_score = (2 * precision * recall) / (precision + recall)
    print(f"Precision = {round(precision, 2)}, Recall = {round(recall, 2)}, F1-score = {round(f_1_score, 2)}")
    print(f"Tagging accuracy = {round(correct_words_tagged / total_words, 2)}")
    print()
