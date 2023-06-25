#!/usr/bin/env python3
# Copyright © 2023 Anatoliy Poletaev, Ilya Paramonov, Elena Boychuk. All rights reserved.

from pprint import pprint

from dependency_parsing import stanza_json
from constituency_tree_builder.creator import dependency_tree_to_constituency_tree
from constituency_tree_builder.utils import json_to_dependency_tree


def main():
    while True:
        try:
            sentence = input("Sentence:\n> ")
        except (KeyboardInterrupt, EOFError):
            print("Goodbye.")
            exit(0)
        dependency_tree = json_to_dependency_tree(stanza_json(sentence))
        constituency_tree = dependency_tree_to_constituency_tree(dependency_tree)
        pprint(dependency_tree)
        pprint(constituency_tree)


if __name__ == "__main__":
    main()
