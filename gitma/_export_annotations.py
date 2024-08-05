import pandas as pd
import spacy


def get_spacy_df(text: str, spacy_model: str = 'de_core_news_sm') -> pd.DataFrame:
    """Uses spaCy to generate a table with the tokens and their positions in the given text.

    Args:
        text (str): Any text.
        spacy_model (str, optional): A spaCy model as listed at https://spacy.io/usage/models. Defaults to 'de_core_news_sm'.\
            Note that the specified model first needs to be installed, as detailed on the linked page.
        
    Returns:
        pd.DataFrame: `pandas.DataFrame` with 3 columns:\n
            - 'Token_ID': index of token in tokenized text
            - 'Text_Pointer': a text pointer for the start point of the token
            - 'Token': the token
    """
   
    nlp = spacy.load(spacy_model)
    doc = nlp(text)

    lemma_list = []

    for token in doc:
        if '\n' not in token.text:
            lemma_list.append((
                token.i,          # token index
                token.idx,        # start pointer in document
                token.text,       # token
            ))

    columns = ['Token_ID', 'Text_Pointer', 'Token']
    return pd.DataFrame(lemma_list, columns=columns)


def to_stanford_tsv(
        ac,
        tags: list,
        file_name: str = None,
        spacy_model: str = 'de_core_news_sm') -> None:
    """Writes a TSV-file for the supplied `AnnotationCollection` which can be used to train a Stanford NER model.
    Every token in the collection's text gets a tag if it lies within an annotated text segment.

    Args:
        ac (gitma.AnnotationCollection): `AnnotationCollection` object.
        tags (list): List of tags that should be considered.
        file_name (str, optional): Name of the TSV-file. Defaults to `None` (file will be named after the collection).
        spacy_model (str, optional): A spaCy model as listed at https://spacy.io/usage/models. Defaults to 'de_core_news_sm'.\
            Note that the specified model first needs to be installed, as detailed on the linked page.
    """

    filtered_ac_df = ac.df[ac.df.tag.isin(tags)].copy()

    if len(filtered_ac_df) < 1:
        print(
            f"Couldn't find any annotations with given tags in annotation collection {ac.name}")
    else:
        lemma_df = get_spacy_df(text=ac.text.plain_text,
                                spacy_model=spacy_model)
        tsv_tags = []
        for _, row in lemma_df.iterrows():
            l_df = filtered_ac_df[
                (filtered_ac_df['start_point'] <= row['Text_Pointer']) &
                (filtered_ac_df['end_point'] > row['Text_Pointer'])
            ].copy().reset_index(drop=True)

            if len(l_df) > 0:
                tsv_tags.append(l_df.tag[0])
            else:
                tsv_tags.append('O')

        lemma_df['Tag'] = tsv_tags

        lemma_df.to_csv(
            path_or_buf=f'{file_name}.tsv' if file_name else f'{ac.name}.tsv',
            sep='\t',
            index=False
        )
