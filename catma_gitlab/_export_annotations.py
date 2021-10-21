import pandas as pd
import spacy


def get_spacy_df(text: str, language: str = 'german', tokenizer: spacy.Tokenizer = None) -> pd.DataFrame:
    """Generates a table with the token and their position in the given text by using `spacy`.

    Args:
        text (str): Any text.
        language (str, optional): The text's language. Defaults to 'german'.
        tokenizer (spacy.Tokenizer, optional): A Spacy tokenizer. Should be used if the text is neither German nor English.
            See https://spacy.io/api/tokenizer for further informations. Defaults to None.

    Returns:
        pd.DataFrame: `pandas.DataFrame` with three columns
            - 'Token_ID': index of token in tokenized text
            - 'Token_Index': a text pointer for the start point of the token
            - 'Token': the token
    """
    from spacy.tokenizer import Tokenizer

    if tokenizer:
        tokenizer = tokenizer
    elif language == 'german':
        from spacy.lang.de import German
        nlp = German()
        tokenizer = Tokenizer(nlp.vocab)
    else:
        from spacy.lang.en import English
        nlp = English()
        tokenizer = Tokenizer(nlp.vocab)

    lemma_list = []
    doc = tokenizer(text)

    for token in doc:
        if '\n' not in token.text:
            lemma_list.append((
                token.id,    # Token ID
                token.idx,        # Start Pointer in Document
                token.text,       # Token
            ))

    columns = ['Token_ID', 'Text_Pointer', 'Token']
    return pd.DataFrame(lemma_list, columns=columns)


def to_stanford_tsv(
        ac,
        tags: list,
        file_name: str = None,
        language: str = 'german',
        tokenizer=None) -> None:
    """Takes a CATMA `AnnotationCollection` and writes a tsv-file which can be used to train a stanford NER model.
    Every token in the collection's text gets a tag if it lays in an annotated text segment. 

    Args:
        ac (catma_gitlab.AnnotationCollection): `AnnotationCollection` object
        tags (list): List of tags, that should be considered.
        file_name (str, optional): name of the tsv-file. Defaults to None.
        language (str, optional): the text's language. Defaults to 'german'.
        tokenizer (spacy.Tokenizer, optional): A Spacy tokenizer. Should be used if the text is neither German nor English.
            See https://spacy.io/api/tokenizer for further informations. Defaults to None.
    """

    filtered_ac_df = ac.df[ac.df.tag.isin(tags)].copy()

    if len(filtered_ac_df) < 1:
        print(
            f"Couldn't find any annotations with given tags in AnnotationCollection {ac.name}")
    else:
        lemma_df = get_spacy_df(text=ac.text.plain_text, language=language)
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


if __name__ == "__main__":
    from catma_gitlab.project import CatmaProject
    project_directory = '../../HESSENBOX-DA/EvENT/catma_backup/'
    project_uuid = 'CATMA_DD5E9DF1-0F5C-4FBD-B333-D507976CA3C7_EvENT_root'

    project = CatmaProject(
        project_directory,
        project_uuid,
        included_acs=['Krambambuli_MW', 'Krambambuli_GS',
                      'gold_annotation_event_krambambuli']
    )

    tags = ['non_event', 'stative_event', 'process', 'change_of_state']
    project.ac_dict['Krambambuli_MW'].to_stanford_tsv(tags=tags)
