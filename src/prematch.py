import pandas as pd
from pandasql import sqldf

DELAY_TIME = 3

def one_category_match(df_professional: type[pd.DataFrame])-> pd.DataFrame:
    df_professional = df_professional.sample(frac=1).reset_index(drop=True)
    df_professional = df_professional.drop_duplicates(subset=['phone_professional'], keep='first')
    return df_professional

def recent_match(df_resposta: type[pd.DataFrame], df_matchings) -> pd.DataFrame:
    """Filtra os pacientes que tiveram um match nos últimos 3 meses."""
    query = f"""
    SELECT
        paci.phone_paciente,
        paci.area,
        matc.match_time as match_time
        FROM df_resposta as paci
        LEFT JOIN df_matchings as matc
            ON matc.phone_paciente = paci.phone_paciente
            AND matc.area = paci.area
            AND (DATE(matc.match_time) >= DATE('now', '-{DELAY_TIME} months') OR matc.match_time IS NULL)
        WHERE matc.match_time IS NOT NULL
    """
    recent_matches = sqldf(query, locals())

    recent_matches.to_csv("./csv/matching_recent.csv", index = False)

    return recent_matches

def time_match(df_resposta: type[pd.DataFrame], df_matchings)-> pd.DataFrame:
    
    recent_matches = recent_match(df_resposta, df_matchings)

    matches = (
    df_resposta.merge(
        recent_matches[['phone_paciente', 'area']],
        on=['phone_paciente', 'area'],
        how='left',
        indicator=True)
    )
    
    matches = matches[matches['_merge'] == 'left_only']
    matches = matches.drop(columns='_merge')
    
    return matches

def prepare_df(df_professional: pd.DataFrame, df_resposta: pd.DataFrame, df_matchings: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df_resposta = time_match(df_resposta, df_matchings)
    df_resposta.to_csv("./csv/matching_time.csv", index=False)
    return df_professional, df_resposta, df_matchings