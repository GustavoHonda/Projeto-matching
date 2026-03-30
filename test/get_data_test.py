import pandas as pd
from src.get_data import preprocess_respostas, open_matches, open_professional, open_respostas


def test_preprocess_respostas_minimal(monkeypatch)-> None:
    # Simula um dataframe de entrada
    df = pd.DataFrame([{
        'datetime': '22/12/2024 21:10:00',
        'name_paciente': 'João',
        "email":"pessoa@gmail.com",
        'phone_paciente': '11999999999',
        'area': 'Psicologia',
        'description': 'preciso de atendimento',
        'free_service': 'não',
        'price': '35 150'
    }])

    df = preprocess_respostas(df)
    assert 'datetime' in df.columns
    assert isinstance(df["datetime"], pd.Series)
    assert df['datetime'].iloc[0] == '2024-12-22 21:10:00'
    assert df['area'].iloc[0] == 'Psicologia'

def test_get_professional(monkeypatch)-> None:
    df_professional = open_professional()
    assert not df_professional.empty
    for col in ["name_professional","area","phone_professional","email_professional","active"]:
        assert col in list(df_professional.columns)

def test_get_matches(monkeypatch)-> None:
    df_matches = open_matches()
    assert not df_matches.empty
    for col in ["name_paciente","name_professional","phone_paciente","phone_professional","area","datetime","email_professional","match_time"]:
        assert col in list(df_matches.columns)


def test_get_respostas(monkeypatch)-> None:
    df_respostas = open_respostas()
    assert not df_respostas.empty
    for col in ["name_paciente" ,"phone_paciente", "area", "datetime"]:
        assert col in list(df_respostas.columns)


