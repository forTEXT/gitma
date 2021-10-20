import pandas as pd


def get_spacy_df(text: str) -> pd.DataFrame:
    import spacy
    nlp = spacy.load("de_core_news_sm")

    lemma_list = []
    doc = nlp(text)

    token_counter = 0
    for token in doc:
        if '\n' not in token.text:
            lemma_list.append((
                token_counter,    # Token ID
                token.idx,        # Start Pointer in Document
                token.text,       # Token
            ))
            token_counter += 1

    columns = ['Token_ID', 'Text_Pointer', 'Token']
    return pd.DataFrame(lemma_list, columns=columns)


def to_stanford_tsv(
        ac,
        tags: list,
        file_name: str = None,
        language: str = 'german'):

    lemma_df = get_spacy_df(text=ac.text.plain_text)

    filtered_ac_df = ac.df[ac.df.tag.isin(tags)].copy()

    tsv_tags = []
    for _, row in lemma_df.iterrows():
        l_df = filtered_ac_df[
            (filtered_ac_df['start_point'] <= row['Text_Pointer']) &
            (filtered_ac_df['end_point'] >= row['Text_Pointer'])
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
