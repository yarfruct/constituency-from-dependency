# Copyright © 2023 Anatoliy Poletaev, Ilya Paramonov, Elena Boychuk. All rights reserved.

import stanza
import ru_core_news_lg

from natasha import Segmenter, MorphVocab, NewsEmbedding, NewsMorphTagger, \
        NewsSyntaxParser, NewsNERTagger, Doc
from stanza.pipeline.core import DownloadMethod

stanza_model = stanza.Pipeline("ru", model_dir="./stanza_models",
                               download_method=DownloadMethod.REUSE_RESOURCES)

spacy_model = ru_core_news_lg.load()

natasha_segmenter = Segmenter()
natasha_morph_vocab = MorphVocab()
natasha_emb = NewsEmbedding()
natasha_morph_tagger = NewsMorphTagger(natasha_emb)
natasha_syntax_parser = NewsSyntaxParser(natasha_emb)
natasha_ner_tagger = NewsNERTagger(natasha_emb)


def stanza_tree_repr(word, words):
    spaces = 2
    children = [w for w in words if w.head == word.id]
    result = f"{word.deprel} - {word.text}"
    if not children:
        return result
    for child in children:
        child_tree_repr = stanza_tree_repr(child, words).strip().split('\n')
        result += '\n'
        result += '\n'.join(' ' * spaces + line for line in child_tree_repr)
    return result


def stanza_parse(sentence):
    words = stanza_model(sentence).sentences[0].words
    root = next(filter(lambda x: x.deprel == "root", words))
    return stanza_tree_repr(root, words)


def stanza_json(sentence):
    words = stanza_model(sentence).sentences[0].words
    return [{"id": word.id - 1,
             "text": word.text,
             "lemma": word.lemma,
             "pos": word.upos.upper(),
             "head_id": word.head - 1,
             "deprel": word.deprel.lower()}
            for word in words]


def spacy_tree_repr(token):
    spaces = 2
    result = f"{token.dep_.lower()} - {token.text}"
    if not token.children:
        return result
    for child in token.children:
        child_tree_repr = spacy_tree_repr(child).strip().split('\n')
        result += '\n'
        result += '\n'.join(' ' * spaces + line for line in child_tree_repr)
    return result


def spacy_parse(sentence):
    doc = spacy_model(sentence)
    root = next(filter(lambda x: x.dep_ == "ROOT", doc))
    return spacy_tree_repr(root)


def spacy_json(sentence):
    doc = spacy_model(sentence)
    return [{"id": word.i,
             "text": word.text,
             "lemma": word.lemma_,
             "pos": word.pos_.upper(),
             "head_id": word.head.i,
             "deprel": word.dep_.lower()}
            for word in doc]


def natasha_tree_repr(token, doc):
    spaces = 2
    children = [t for t in doc.tokens if t.head_id == token.id]
    result = f"{token.rel} - {token.text}"
    if not children:
        return result
    for child in children:
        child_tree_repr = natasha_tree_repr(child, doc).strip().split('\n')
        result += '\n'
        result += '\n'.join(' ' * spaces + line for line in child_tree_repr)
    return result


def natasha_parse(sentence):
    doc = Doc(sentence)
    doc.segment(natasha_segmenter)
    doc.tag_morph(natasha_morph_tagger)
    for token in doc.tokens:
        token.lemmatize(natasha_morph_vocab)
    doc.parse_syntax(natasha_syntax_parser)
    try:
        root = next(filter(lambda x: x.rel == "root", doc.tokens))
    except StopIteration:
        return '\n'.join([f"{t.id}, {t.text}, {t.head_id}, {t.rel}" for t in doc.tokens])
    return natasha_tree_repr(root, doc)


def natasha_json(sentence):
    doc = Doc(sentence)
    doc.segment(natasha_segmenter)
    doc.tag_morph(natasha_morph_tagger)
    for token in doc.tokens:
        token.lemmatize(natasha_morph_vocab)
    doc.parse_syntax(natasha_syntax_parser)
    return [{"id": int(word.id.split('_')[1]) - 1,
             "text": word.text,
             "lemma": word.lemma,
             "pos": word.pos.upper(),
             "head_id": int(word.head_id.split('_')[1]) - 1,
             "deprel": word.rel.lower()}
            for word in doc.tokens]
