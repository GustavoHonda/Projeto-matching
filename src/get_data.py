import pandas as pd
import re
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from src.utils.path import get_project_root
from pathlib import Path
from typing import Any

base_path = get_project_root()

def data_info(df, column)-> None:
    """
    Função auxiliar que mostra os valores únicos, tipo e frequência de uma coluna do DataFrame.

    Args:
        df (pd.DataFrame): DataFrame analisado
        column (str): Nome da coluna analisada
    """
    print(f"Coluna: {column}")
    print(f"Tipo de dado: {df[column].dtype}\n")
    print("Frequência de valores únicos:")
    print(df[column].value_counts())  # inclui NaNs se houver


def extrair_precos(texto)-> list:
    # Remove separador de milhar
    texto = re.sub(r'\.(?=\d{3}(?:,|$))', '', str(texto))
    # Troca vírgula decimal por ponto
    texto = re.sub(r'(?<=\d),(?=\d)', '.', texto)
    # Substitui tudo que não é número ou ponto por espaço
    texto = re.sub(r'[^0-9.]', ' ', texto)
    # Remove espaços duplicados
    texto = re.sub(r'\s+', ' ', texto).strip()
    # Quebra em possíveis preços
    precos = texto.split(' ')
    # Converte os valores válidos para float
    return [float(p) for p in precos if p.replace('.', '', 1).isdigit()]


def preprocess_respostas(df)->pd.DataFrame:
    
    # Rename columns
    name_columns= ['datetime','name_paciente','e-mail','phone_paciente','area','description']
    columns = list(df.columns)
    for i, col in enumerate(name_columns):
        columns[i] = col
    df.columns = columns

    # Clean phone number
    df["phone_paciente"] = df["phone_paciente"].astype(str).str.replace(r"\D", "", regex=True)

    
    
    # Area column
    df.loc[:,"area"] = df["area"].str.split(",")
    df = df.explode('area')
    df.loc[:,'area'] = df['area'].str.replace(":","", regex=True)
    df.loc[:,'area'] = df['area'].str.strip()
    df_paciente_area = df[['phone_paciente','area']].drop_duplicates().reset_index(drop=True)

    # Send pacientes data to google sheets
    df = df.dropna(axis=1,how='all')
    df = df.map(lambda x: np.nan if isinstance(x, str) and x.strip() == "" else x)
    df = df.dropna(axis=0, subset=['name_paciente', 'phone_paciente', 'area'])
    df = df.fillna('').infer_objects(copy=False)
    df.reset_index(inplace=True, drop=True)
    df = df.drop_duplicates(subset=['phone_paciente'], keep='first')
    df_paciente = df[['phone_paciente','name_paciente','e-mail','datetime']].drop_duplicates(subset=['phone_paciente'], keep='first')
    
    update_data(df=df_paciente_area, sheets_name="db-metAMORfose", page="Paciente_area", index="phone_paciente")
    update_data(df=df_paciente, sheets_name="db-metAMORfose", page="Paciente", index="phone_paciente")
    return df


def preprocess_professional(df) -> pd.DataFrame:
    
    # Rename columns
    name_columns = ['name_professional','area','phone_professional',"email_professional","active"]
    columns = list(df.columns)
    for i, col in enumerate(name_columns):
        columns[i] = col
    df.columns = columns

     # Clean phone number
    df.loc[:,'phone_professional'] = df['phone_professional'].apply(lambda x: x.replace("wa.me/","") if type(x) == str else x)
    
    # Professional_area Table
    df.loc[:,"area"] = df["area"].str.split(",")
    df = df.explode('area')
    df.loc[:,'area'] = df['area'].str.replace(":","", regex=True)
    df.loc[:,'area'] = df['area'].str.strip()
    df_professional_area = df[['phone_professional','area']].drop_duplicates().reset_index(drop=True)
    


    # Drop empty data
    df = df.map(lambda x: np.nan if isinstance(x, str) and x.strip() == "" else x)
    df = df.dropna(axis=1,how='all')
    df = df.dropna(axis=0,subset=['name_professional', 'area', 'phone_professional','email_professional'])
    df = df.fillna('').infer_objects(copy=False)
    df.reset_index(inplace=True, drop=True)
    df = df.drop_duplicates(subset=['phone_professional'], keep='first')

    

    update_data(df=df_professional_area, sheets_name="db-metAMORfose", page="Professional_area", index="phone_professional")
    update_data(df=df, sheets_name="db-metAMORfose", page="Professional", index="phone_professional")

    # Remove linhas que tem valor da coluna 'active' como zero
    df = df[df['active'] == 1] 

    return df


def open_respostas()-> pd.DataFrame:
    df = get_data(sheets_name="Respostas-2025",page="Respostas")
    df = preprocess_respostas(df)
    return df


def open_professional()-> pd.DataFrame:
    client = set_credentials()
    df = get_data(sheets_name="Profissionais",page="Página1")
    df = preprocess_professional(df)
    return df


def open_matches()-> pd.DataFrame:
    try:
        df = get_data(sheets_name="db-metAMORfose", page="Matches")
        if df is None or df.empty:
            return pd.DataFrame(columns=["name_paciente", "name_professional" ,"phone_paciente" , "phone_professional", "area", "price_min", "price_max", "datetime","email_professional","match_time"])
        return df
    except Exception as e:
        print(f"Error: {e}")
        print(f"Error in open_matchings function.")
        return pd.DataFrame()
    
    
def save_matches(df_matches, df_match_all,save)->None:
    base_dir = get_project_root()
    df_match_all.to_csv(Path(base_dir, f'./csv/matching_all.csv'), index=False)
    df_matches.to_csv(Path(base_dir, f"./csv/matchings_selected.csv"),index=False)
    
    df = df_matches[["name_paciente", "name_professional", "phone_paciente", "phone_professional","description", "area", "datetime", "price_min", "price_max","email_professional","match_time"]]

    if save:
        df = df.astype(str)
        df = df.fillna('').infer_objects(copy=False)
        append_data(df=df, sheets_name="db-metAMORfose", page="Matches")
        print("Data send!")


def open_mock()->pd.DataFrame:
    mock_path = Path(base_path, "csv", "mock_match.csv")
    df = pd.read_csv(mock_path, sep=",",encoding="utf-8",index_col=0)
    df.reset_index(inplace=True)
    return df


def open_mock_professional()->pd.DataFrame:
    mock_path = Path(base_path, "csv", "mock_professionais.csv")
    df = pd.read_csv(mock_path, sep=",",encoding="utf-8",index_col=0)
    df.reset_index(inplace=True)
    df = preprocess_professional(df)
    return df


def open_mock_respostas()->pd.DataFrame:
    mock_path = Path(base_path, "csv", "mock_respostas.csv")
    df = pd.read_csv(mock_path, sep=",",encoding="utf-8",index_col=0)
    df.reset_index(inplace=True)
    df = preprocess_respostas(df)
    return df


def set_credentials() -> gspread.Client:
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    credentials_path = Path(base_path, "key", "sheets-service-account.json")
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
    client = gspread.authorize(creds)
    return client


def send_data(sheets_name="db-metAMORfose", page = None,df=None)-> None:
    client = set_credentials()
    sheet = client.open(sheets_name)
    sheet = sheet.worksheet(page)
    data = [df.columns.astype(str).tolist()] + df.astype(str).values.tolist()
    sheet.update(values=data, range_name="A1")

    
def get_data(sheets_name = "db-metAMORfose", page = None)-> pd.DataFrame:
    client = set_credentials()
    sheet = client.open(sheets_name)
    sheet = sheet.worksheet(page)
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    return df

def append_data(sheets_name="db-metAMORfose", page = None, df=None)-> None:
    client = set_credentials()
    sheet = client.open(sheets_name)
    sheet = sheet.worksheet(page)
    payload = df.fillna(0).values.tolist()
    sheet.append_rows(payload, value_input_option="USER_ENTERED")

def update_data(sheets_name="db-metAMORfose", page = None, df=None, index = "")-> None:
    df_old = get_data(sheets_name, page)
    if df_old is None or df_old.empty:
        send_data(sheets_name, page, df)
        return
    df_old.set_index(index, inplace=True)
    df_new = df.set_index(index, inplace=False)
    df = df_new.combine_first(df_old).drop_duplicates(keep='first').reset_index()
    client = set_credentials()
    sheet = client.open(sheets_name)
    sheet = sheet.worksheet(page)
    df_payload = df.replace({np.nan: None})
    payload = [df_payload.columns.tolist()] + df_payload.values.tolist()
    sheet.update(values=payload, range_name="A1", value_input_option="USER_ENTERED")

def main()-> None:
    df_resposta = open_respostas()
    df_professional = open_professional()
    df_match = open_matches()
    print(len(df_resposta), len(df_professional), len(df_match))

    df_resposta.to_csv("./csv/respostas.csv")
    df_professional.to_csv("./csv/professional.csv")
    df_match.to_csv("./csv/matchings.csv", index = False)

if __name__ == "__main__":
    main()