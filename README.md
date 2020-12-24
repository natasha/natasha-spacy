# natasha-spacy

SpaCy official Russian model proposal. Work is heavily inspired and based on <a href="https://github.com/buriy/spacy-ru/">spacy-ru</a> by <a href="http://github.com/buriy/">@buriy</a>. 

Russian model is trained on two resources, both available under MIT license:
1. <a href="https://github.com/natasha/nerus">Nerus</a> — part of <a href="https://github.com/natasha">Natasha project</a>, large silver standard Russian corpus annotated with morphology tags, syntax trees and PER, LOC, ORG NER-tags.
2. <a href="https://github.com/natasha/navec">Navec</a> — also part of Natasha project, pretrained word embeddings for Russian language.

Resulting model is relatively small due to embeddings table pruning (138MB), works fast on CPU. Shows near SOTA performance on tasks of morphology tagging and syntax parsing, beating heavy DeepPavlov BERT on news and wiki domains. On NER task model shows quality comparable to other top Russian systems, beating DeepPavlov, PullEnti, Stanza. See Naeval <a href="https://github.com/natasha/naeval#morphology-taggers">morphology</a>, <a href="https://github.com/natasha/naeval#syntax-parser">syntax</a>, and <a href="https://github.com/natasha/naeval#ner">NER</a> sections.

## Download

<a href="https://storage.yandexcloud.net/natasha-spacy/models/ru_core_news_md-2.3.0.tar.gz">ru_core_news_md-2.3.0.tar.gz</a>, 138MB

## Usage 

First download and install the model.
```bash
wget https://storage.yandexcloud.net/natasha-spacy/models/ru_core_news_md-2.3.0.tar.gz
pip install ru_core_news_md-2.3.0.tar.gz
```

SpaCy 2.3.* is required, model won't work with SpaCy 2.1, 2.2. 
```python
>>> import spacy
# Use ipymarkup for NER and syntax visualization
>>> from ipymarkup import show_dep_ascii_markup, show_span_ascii_markup

>>> nlp = spacy.load('ru_core_news_md')
>>> text = 'Посол Израиля на Украине Йоэль Лион признался, что пришел в шок, узнав о решении властей Львовской области объявить 2019 год годом лидера запрещенной в России Организации украинских националистов (ОУН) Степана Бандеры. Свое заявление он разместил в Twitter. «Я не могу понять, как прославление тех, кто непосредственно принимал участие в ужасных антисемитских преступлениях, помогает бороться с антисемитизмом и ксенофобией. Украина не должна забывать о преступлениях, совершенных против украинских евреев, и никоим образом не отмечать их через почитание их исполнителей», — написал дипломат. 11 декабря Львовский областной совет принял решение провозгласить 2019 год в регионе годом Степана Бандеры в связи с празднованием 110-летия со дня рождения лидера ОУН (Бандера родился 1 января 1909 года). В июле аналогичное решение принял Житомирский областной совет. В начале месяца с предложением к президенту страны Петру Порошенко вернуть Бандере звание Героя Украины обратились депутаты Верховной Рады. Парламентарии уверены, что признание Бандеры национальным героем поможет в борьбе с подрывной деятельностью против Украины в информационном поле, а также остановит «распространение мифов, созданных российской пропагандой». Степан Бандера (1909-1959) был одним из лидеров Организации украинских националистов, выступающей за создание независимого государства на территориях с украиноязычным населением. В 2010 году в период президентства Виктора Ющенко Бандера был посмертно признан Героем Украины, однако впоследствии это решение было отменено судом. '
>>> doc = nlp(text)


#######
#
#   NER
#
#######


>>> spans = [
...     (_.start_char, _.end_char, _.label_)
...     for _ in doc.ents
... ]
>>> show_span_ascii_markup(doc.text, spans)
Посол Израиля на Украине Йоэль Лион признался, что пришел в шок, узнав
      LOC────    LOC──── PER───────                                   
 о решении властей Львовской области объявить 2019 год годом лидера 
                   LOC──────────────                                
запрещенной в России Организации украинских националистов (ОУН) 
              LOC─── ORG─────────────────────────────────────── 
Степана Бандеры. Свое заявление он разместил в Twitter. «Я не могу 
PER────────────                                ORG────             
понять, как прославление тех, кто непосредственно принимал участие в 
ужасных антисемитских преступлениях, помогает бороться с 
антисемитизмом и ксенофобией. Украина не должна забывать о 
                              LOC────                      
преступлениях, совершенных против украинских евреев, и никоим образом 
не отмечать их через почитание их исполнителей», — написал дипломат. 
11 декабря Львовский областной совет принял решение провозгласить 2019
           ORG──────────────────────                                  
 год в регионе годом Степана Бандеры в связи с празднованием 110-летия
                     PER────────────                                  
 со дня рождения лидера ОУН (Бандера родился 1 января 1909 года). В 
                        ORG  PER────                                
июле аналогичное решение принял Житомирский областной совет. В начале 
                                ORG────────────────────────           
месяца с предложением к президенту страны Петру Порошенко вернуть 
                                          PER────────────         
Бандере звание Героя Украины обратились депутаты Верховной Рады. 
PER────              LOC────                     ORG───────────  
Парламентарии уверены, что признание Бандеры национальным героем 
                                     PER────                     
поможет в борьбе с подрывной деятельностью против Украины в 
                                                  LOC────   
информационном поле, а также остановит «распространение мифов, 
созданных российской пропагандой». Степан Бандера (1909-1959) был 
                                   PER───────────                 
одним из лидеров Организации украинских националистов, выступающей за 
                 ORG─────────────────────────────────                 
создание независимого государства на территориях с украиноязычным 
населением. В 2010 году в период президентства Виктора Ющенко Бандера 
                                               PER─────────── PER──── 
был посмертно признан Героем Украины, однако впоследствии это решение 
                             LOC────                                  
было отменено судом. 


#######
#
#   MORPH
#
#######


>>> sent = next(doc.sents)
>>> for token in sent:
...     print(token.text.ljust(10), token.lemma_.ljust(10), token.tag_)
Посол      посол      NOUN__Animacy=Anim|Case=Nom|Gender=Masc|Number=Sing
Израиля    израиль    PROPN__Animacy=Inan|Case=Gen|Gender=Masc|Number=Sing
на         на         ADP___
Украине    украина    PROPN__Animacy=Inan|Case=Loc|Gender=Fem|Number=Sing
Йоэль      йоэль      PROPN__Animacy=Anim|Case=Nom|Gender=Masc|Number=Sing
Лион       лион       PROPN__Animacy=Anim|Case=Nom|Gender=Masc|Number=Sing
признался  признаться VERB__Aspect=Perf|Gender=Masc|Mood=Ind|Number=Sing|Tense=Past|VerbForm=Fin|Voice=Mid
,          ,          PUNCT___
что        что        SCONJ___
пришел     прийти     VERB__Aspect=Perf|Gender=Masc|Mood=Ind|Number=Sing|Tense=Past|VerbForm=Fin|Voice=Act
в          в          ADP___
шок        шок        NOUN__Animacy=Inan|Case=Acc|Gender=Masc|Number=Sing
,          ,          PUNCT___
узнав      узнать     VERB__Aspect=Perf|Tense=Past|VerbForm=Conv|Voice=Act
о          о          ADP___
решении    решение    NOUN__Animacy=Inan|Case=Loc|Gender=Neut|Number=Sing
властей    власть     NOUN__Animacy=Inan|Case=Gen|Gender=Fem|Number=Plur
Львовской  львовский  ADJ__Case=Gen|Degree=Pos|Gender=Fem|Number=Sing
области    область    NOUN__Animacy=Inan|Case=Gen|Gender=Fem|Number=Sing
объявить   объявить   VERB__Aspect=Perf|VerbForm=Inf|Voice=Act
2019       2019       ADJ___
год        год        NOUN__Animacy=Inan|Case=Acc|Gender=Masc|Number=Sing
годом      год        NOUN__Animacy=Inan|Case=Ins|Gender=Masc|Number=Sing
лидера     лидер      NOUN__Animacy=Anim|Case=Gen|Gender=Masc|Number=Sing
запрещенной запретить  VERB__Aspect=Perf|Case=Gen|Gender=Fem|Number=Sing|Tense=Past|VerbForm=Part|Voice=Pass
в          в          ADP___
России     россия     PROPN__Animacy=Inan|Case=Loc|Gender=Fem|Number=Sing
Организации организация PROPN__Animacy=Inan|Case=Gen|Gender=Fem|Number=Sing
украинских украинских ADJ__Case=Gen|Degree=Pos|Number=Plur
националистов националист NOUN__Animacy=Anim|Case=Gen|Gender=Masc|Number=Plur
(          (          PUNCT___
ОУН        оун        PROPN__Animacy=Inan|Case=Gen|Gender=Fem|Number=Sing
)          )          PUNCT___
Степана    степан     PROPN__Animacy=Anim|Case=Gen|Gender=Masc|Number=Sing
Бандеры    бандеры    PROPN__Animacy=Anim|Case=Gen|Gender=Masc|Number=Sing
.          .          PUNCT___


########
#
#  SYNTAX
#
######


>>> words = [_.text for _ in sent]
>>> deps = [
...     (_.head.i, _.i, _.dep_)
...     for _ in sent
...     if _.i != _.head.i
... ]
>>> show_dep_ascii_markup(words, deps)
    ┌►┌─┌─┌─ Посол         nsubj
    │ │ │ └► Израиля       nmod
    │ │ │ ┌► на            case
    │ │ └►└─ Украине       nmod
    │ └──►┌─ Йоэль         appos
    │     └► Лион          flat:name
┌───└─┌───── признался     
│     │ ┌──► ,             punct
│     │ │ ┌► что           mark
│   ┌─└►└─└─ пришел        ccomp
│   │ │   ┌► в             case
│   │ └──►└─ шок           obl
│   │     ┌► ,             punct
│   └──►┌─└─ узнав         advcl
│       │ ┌► о             case
│   ┌───└►└─ решении       obl
│   │ ┌─└──► властей       nmod
│   │ │   ┌► Львовской     amod
│   │ └──►└─ области       nmod
│   └►┌─┌─── объявить      nmod
│     │ │ ┌► 2019          amod
│     │ └►└─ год           obj
│     └──►┌─ годом         obl
│ ┌─┌─────└► лидера        nmod
│ │ │ ┌►┌─── запрещенной   amod
│ │ │ │ │ ┌► в             case
│ │ │ │ └►└─ России        obl
│ │ └►└─┌─── Организации   nmod
│ │     │ ┌► украинских    amod
│ │   ┌─└►└─ националистов nmod
│ │   │   ┌► (             punct
│ │   └►┌─└─ ОУН           parataxis
│ │     └──► )             punct
│ └──────►┌─ Степана       appos
│         └► Бандеры       flat:name
└──────────► .             punct
```

## Training

Both Nerus and Navec are adapted to fit SpaCy utilities. Training procedure uses only standart `spacy convert`, `spacy init-model`, `spacy train`.

Initialize the environment. We use SpaCy 2.3 for training, Russian language in SpaCy requires PyMorphy for morphology.
```bash
pip install spacy==2.3.5 pymorphy2==0.8
mkdir -p data train/data train/base train/model
```

650MB embeddings table. Navec is precomputed on fiction texts, has 500 000 words in vocabulary.
```bash
wget https://storage.yandexcloud.net/natasha-spacy/data/navec.12B.300d.txt.gz -P data
```

1.5GB training data. We use 10% slice of original Nerus, it contains 100 000 documents, 1 000 000 sentences.
```bash
wget https://storage.yandexcloud.net/natasha-spacy/data/nerus-dev.conllu.gz -P data
wget https://storage.yandexcloud.net/natasha-spacy/data/nerus-train.conllu.gz -P data
gunzip data/nerus-*.conllu.gz
```

WARNING! Conversion requires 32GB of RAM, resulting in JSON that is 4.5GB in size. 
```bash
# --n-sents explanation: on average there are 10 sentences per document in Nerus
spacy convert --n-sents 10 --morphology data/nerus-train.conllu train/data
spacy convert --n-sents 10 --morphology data/nerus-dev.conllu train/data
```

Original Navec embeddings have 500 000 words in vocabulary. Pruning to 125 000 words we lose just 0.5 percentage points in accuracy.
```bash
spacy init-model ru train/base --vectors-loc data/navec.12B.300d.txt.gz --prune-vectors 125000
```

Training takes ~2 hours per iteration on CPU (~5 times faster on GPU).
```bash
spacy train --base-model train/base --n-iter 10 ru train/model train/data/nerus-train.json train/data/nerus-dev.json
```

## Package

Update `meta.json` with description, authors, sources. On model name `core_news_md`:
- `core` — provides all three: tagger, parser and ner;
- `news` — trained on Nerus that is large automatically annotated news corpus;
- `md` — in SpaCy small models are 10-50MB in size, `md` - 50-200MB, `lg` - 200-600MB, out model is ~140MB.

```javascript
{
  "name": "core_news_md",
  "lang": "ru",
  "version": "2.3.0",
  "spacy_version": ">=2.3.0,<2.4.0",
  "description": "Russian multitask CNN initialized with Navec embeddings trained on Nerus dataset. Assigns context-specific token vectors, POS tags, dependency parse and named entities.",
  "author": "Yuri Baburov, Alexander Kukushkin",
  "email": "burchik@gmail.com, alex@alexkuk.ru",
  "url": "https://github.com/natasha/natasha-spacy",
  "license": "MIT",
  "sources": [
    {
      "name": "Nerus",
      "url": "https://github.com/natasha/nerus"
    },
    {
      "name": "Navec",
      "url": "https://github.com/natasha/navec"
    }
  ]
}
```

Use `spacy package` and `python sdist` to produce tar.gz archive.
```bash
mkdir package
spacy package {dir} package
cd package/*; python setup.py sdist
mv package/*/dist/*.tar.gz .
rm -r package
```
