
from os.path import join
from itertools import islice as head
from collections import Counter
import unicodedata

from tqdm.auto import tqdm as log_progress

from nerus import load_nerus
from navec import Navec


DATA_DIR = 'data'

NATASHA_DIR = join(DATA_DIR, 'natasha')
NERUS = join(NATASHA_DIR, 'nerus_lenta.conllu.gz')
NAVEC = join(NATASHA_DIR, 'navec_hudlit_v1_12B_500K_300d_100q.tar')

ADAPT_DIR = join(DATA_DIR, 'adapt')
TRAIN = join(ADAPT_DIR, 'nerus-train.conllu')
TEST = join(ADAPT_DIR, 'nerus-test.conllu')
EMB = join(ADAPT_DIR, 'navec.12B.300d.txt')


########
#
#   NERUS
#
######


ROOT_SOURCE = -1
SHIFT = 'shift'
LEFT = 'left'
RIGHT = 'right'


class BadDeps(Exception):
    pass


def token_deps(tokens):
    for token in tokens:
        source = int(token.head_id) - 1
        target = int(token.id) - 1
        yield source, target


def dep_actions(deps):
    index = set()
    refs = Counter()
    for source, target in deps:
        index.add((source, target))
        refs[source] += 1

    yield SHIFT
    stack = [ROOT_SOURCE, 0]
    pointer = 1

    for _ in range(2 * len(deps) - 1):
        if len(stack) < 2:
            raise BadDeps

        source, target = stack[-2:]
        if (source, target) in index and not refs[target]:
            yield RIGHT
            stack.pop(-1)
            refs[source] -= 1
        elif (target, source) in index and not refs[source]:
            yield LEFT
            stack.pop(-2)
            refs[target] -= 1
        else:
            yield SHIFT
            stack.append(pointer)
            pointer += 1

    if stack != [ROOT_SOURCE]:
        raise BadDeps


def deps_projective(deps):
    # check that deps are projective. auto detect multiple roots,
    # cycles, check all nodes are reachable

    try:
        list(dep_actions(deps))
        return True
    except BadDeps:
        return False


def match_pos_rel(pos, rel):
    if rel == 'det':
        pos = 'DET'

    if rel == 'nummod' and pos not in ['NUM', 'NOUN', 'SYM']:
        pos = 'NUM'

    if rel == 'advmod' and pos not in ['ADV', 'ADJ', 'CCONJ', 'DET', 'PART', 'SYM']:
        pos = 'ADV'

    if rel == 'expl' and pos not in ['PRON', 'DET', 'PART']:
        pos = 'PRON'

    if rel == 'aux':
        pos = 'AUX'

    if rel == 'cop' and pos not in ['AUX', 'PRON', 'DET', 'SYM']:
        pos = 'PRON'

    if rel == 'case' and pos in ['PROPN', 'ADJ', 'PRON', 'DET', 'NUM', 'AUX']:
        pos = 'ADP'

    if rel == 'mark' and pos in ['NOUN', 'PROPN', 'ADJ', 'PRON', 'DET', 'NUM', 'VERB', 'AUX', 'INTJ']:
        pos = 'SCONJ'

    if rel == 'cc' and pos in ['NOUN', 'PROPN', 'ADJ', 'PRON', 'DET', 'NUM', 'VERB', 'AUX', 'INTJ']:
        pos = 'CCONJ'

    if rel == 'punct':
        pos = 'PUNCT'

    if pos == 'PUNCT' and rel not in ['punct', 'root']:
        rel = 'punct'

    return pos, rel


def norm_unicode(text):
    # и'̆  -> й
    # Актер Владимир Долинский
    # поддержала и Энн Хэтэуэй

    return unicodedata.normalize('NFC', text)


def projective_sent(sent):
    deps = list(token_deps(sent.tokens))
    return deps_projective(deps)


def find_token_bounds(text, tokens):
    offset = 0
    for token in tokens:
        start = text.find(token.text, offset)
        stop = start + len(token.text)
        offset = stop
        token.start, token.stop = start, stop


def token_misc(text, token):
    misc = {'Tag': token.tag}
    if token.stop < len(text) and not text[token.stop].isspace():
        misc['SpacyAfter'] = 'No'
    return misc


def rename_feat(key, value):
    if key == 'Variant':
        key = 'StyleVariant'
    if value == '1':
        value = 'First'
    if value == '2':
        value = 'Second'
    if value == '3':
        value = 'Third'
    return key, value


def rename_feats(feats):
    # Degree=Pos|Number=Plur|Variant=Short
    # Case=Acc|Number=Sing|Person=1

    return dict(
        rename_feat(key, value)
        for key, value in feats.items()
    )


def adapt_nerus(docs):
    for doc in docs:
        # ~13% gets removed
        doc.sents = [
            _ for _ in doc.sents
            if projective_sent(_)
        ]

        for sent in doc.sents:

            sent.text = norm_unicode(sent.text)
            for token in sent.tokens:
                token.text = norm_unicode(token.text)
            find_token_bounds(sent.text, sent.tokens)

            for token in sent.tokens:
                token.feats = rename_feats(token.feats)
                # 3% sents change match pos rel, 0.3% tokens
                token.pos, token.rel = match_pos_rel(token.pos, token.rel)
                token.misc = token_misc(sent.text, token)

        yield doc


def format_feats(feats):
    if not feats:
        return '_'

    return '|'.join(
        '%s=%s' % (_, feats[_])
        for _ in sorted(feats)
    )


def format_conll(docs):
    # https://universaldependencies.org/format.html

    # ID, FORM, LEMMA,
    # UPOS, XPOS, FEATS
    # HEAD, DEPREL, DEPS
    # MISC    

    for doc in docs:
        yield f'# newdoc id = {doc.id}'
        for sent in doc.sents:
            yield f'# sent_id = {sent.id}'
            yield f'# text = {sent.text}'
            for token in sent.tokens:
                feats = format_feats(token.feats)
                misc = format_feats(token.misc)
                yield (
                    f'{token.id}\t{token.text}\t_'  # no lemma
                    f'\t{token.pos}\t_\t{feats}'  # just pos, no xpos
                    f'\t{token.head_id}\t{token.rel}\t_'  # just deprel, no deps
                    f'\t{misc}'
                )
            yield ''


def dump_lines(lines, path):
    with open(path, 'w') as file:
        for line in lines:
            file.write(line + '\n')
