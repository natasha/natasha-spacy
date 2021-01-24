
import re
import gzip
import json
import unicodedata
from os.path import join, exists, expanduser
from itertools import islice as head
from collections import defaultdict, Counter

import boto3
import pandas as pd
from tqdm.auto import tqdm as log_progress
from matplotlib import pyplot as plt

from nerus import load_nerus
from navec import Navec


#######
#
#   IO
#
#####


def load_json(path):
    with open(path) as file:
        return json.load(file)


def dump_json(data, path):
    with open(path, 'w') as file:
        json.dump(data, file)


def dump_gz_lines(lines, path):
    with gzip.open(path, 'wt') as file:
        for line in lines:
            file.write(line + '\n')


def load_lines(path):
    with open(path) as file:
        for line in file:
            yield line.rstrip('\n')


#########
#
#   CONST
#
#####


config = {}
path = expanduser('~/.natasha-spacy.json')
if exists(path):
    config = load_json(path)


DATA_DIR = 'data'

NATASHA_DIR = join(DATA_DIR, 'natasha')
NERUS = join(NATASHA_DIR, 'nerus_lenta.conllu.gz')
NAVEC = join(NATASHA_DIR, 'navec_hudlit_v1_12B_500K_300d_100q.tar')

ADAPT_DIR = join(DATA_DIR, 'adapt')
TRAIN = join(ADAPT_DIR, 'nerus-train.conllu.gz')
DEV = join(ADAPT_DIR, 'nerus-dev.conllu.gz')
EMB = join(ADAPT_DIR, 'navec.12B.300d.txt')

S3_TRAIN = join(DATA_DIR, 'nerus-train.conllu.gz')
S3_DEV = join(DATA_DIR, 'nerus-dev.conllu.gz')
S3_EMB = join(DATA_DIR, 'navec.12B.300d.txt.gz')

TRAIN_DIR = 'train'
LOGS_DIR = join(TRAIN_DIR, 'logs')
MODELS_DIR = join(TRAIN_DIR, 'models')
META = 'meta'

GZ = '.gz'
JSON = '.json'

S3_KEY_ID = config.get('s3_key_id')
S3_KEY = config.get('s3_key')
S3_BUCKET = 'natasha-spacy'
S3_REGION = 'us-east-1'
S3_ENDPOINT = 'https://storage.yandexcloud.net'


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


def rename_feat(key, value):
    # @buriy оно ломается внутри без переименовывания.
    # 1) фича может быть только текстовой, или цифры кто-то зарезервировал.
    # 2) почему-то слово "Variant" зарезервировано кем-то.
    # там такой геморрой из-за его внутреннего словаря Vocab, где слова меняются на их хеши в открытом хеше.

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
        # ~13% nonprojective
        doc.sents = [
            _ for _ in doc.sents
            if projective_sent(_)
        ]

        for sent in doc.sents:
            sent.text = norm_unicode(sent.text)
            for token in sent.tokens:
                token.text = norm_unicode(token.text)
                # 3% sents change match pos rel, 0.3% tokens
                token.pos, token.rel = match_pos_rel(token.pos, token.rel)
                token.feats = rename_feats(token.feats)

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
                yield (
                    f'{token.id}\t{token.text}\t_'  # no lemma
                    f'\t{token.pos}\t_\t{feats}'  # just pos, no xpos
                    f'\t{token.head_id}\t{token.rel}\t_'  # just deprel, no deps
                    f'\t{token.tag}'  # Tag=O -> O
                )
            yield ''


########
#
#   S3
#
#######


class S3:
    __attributes__ = ['key_id', 'key', 'bucket', 'endpoint', 'region']

    def __init__(self, key_id=S3_KEY_ID, key=S3_KEY, bucket=S3_BUCKET,
                 endpoint=S3_ENDPOINT, region=S3_REGION):
        self.key_id = key_id
        self.key = key
        self.bucket = bucket
        self.endpoint = endpoint
        self.region = region

        self.client = boto3.client(
            's3',
            aws_access_key_id=key_id,
            aws_secret_access_key=key,
            region_name=region,
            endpoint_url=endpoint,
        )

    def upload(self, path, key):
        self.client.upload_file(path, self.bucket, key)

    def download(self, key, path):
        self.client.download_file(self.bucket, key, path)


##########
#
#   LOGS
#
#####


def parse_log(lines):
    for line in lines:
        if not re.match('^[\s\d\.]+$', line):
            continue

        parts = [float(_) for _ in line.split()]
        _, _, morph, _, uas, las, _, _, _, ner, _, _ = parts
        yield morph, uas, las, ner

        

def load_log(path):
    lines = load_lines(path)
    items = parse_log(lines)
    return pd.DataFrame(
        items,
        columns=['morph', 'uas', 'las', 'ner']
    )
    

########
#
#   GRID
#
######


METRICS = ['morph', 'las', 'ner']


def load_scores(paths, metrics=METRICS):
    scores = defaultdict(list)
    for path in paths:
        table = load_log(path)
        for metric in metrics:
            score = table[metric].max()
            scores[metric].append(score)
    return dict(scores)


def show_scores(scores, sizes, metrics=METRICS):
    fig, axes = plt.subplots(1, len(metrics))
    fig.set_size_inches(5 * len(metrics), 4)

    for metric, ax in zip(metrics, axes):
        ax.set_title(metric)
        ax.plot(sizes, scores[metric])
        ax.scatter(sizes, scores[metric])
