import pandas as pd
from src.get_data import extrair_precos, preprocess_respostas, open_matches, open_professional, open_respostas

def test_extrair_precos_simples()-> None:
    assert extrair_precos("R$ 200,00") == [200.0]

def test_extrair_precos_multiplos()-> None:
    assert extrair_precos("R$ 1.200,50 ou R$ 999,99") == [1200.5, 999.99]

def test_extrair_precos_sem_valor()-> None:
    assert extrair_precos("Sem valor") == []

def test_extrair_precos_valor_bruto()-> None:
    assert extrair_precos("300") == [300.0]

def test_extrair_precos_com_ponto_milhar()-> None:
    assert extrair_precos("1.000") == [1000.0]


def test_preprocess_respostas_minimal(monkeypatch)-> None:
    # Simula um dataframe de entrada
    df = pd.DataFrame([{
        'time': '22/12/2024 21:10:00',
        'name_paciente': 'João',
        "email":"pessoa@gmail.com",
        'phone_paciente': '11999999999',
        'area': 'Psicologia',
        'description': 'preciso de atendimento',
        'free_service': 'não',
        'price': '35 150'
    }])

    df = preprocess_respostas(df)
    assert df['datetime'].dtype == "datetime64[ns]"
    assert df['datetime'].iloc[0] == pd.to_datetime('2024-12-22 21:10:00')
    assert df['price_min'].iloc[0] == 150.0
    assert df['price_max'].iloc[0] == 35.0
    assert df['area'].iloc[0] == 'Psicologia'
    assert 'datetime' in df.columns

def test_get_professional(monkeypatch)-> None:
    df_professional = open_professional()
    assert not df_professional.empty
    for col in ["id_professional","name_professional","area","phone_professional","email_professional","active"]:
        assert col in list(df_professional.columns)

def test_get_matches(monkeypatch)-> None:
    df_matches = open_matches()
    assert not df_matches.empty
    for col in ["name_paciente","name_professional","phone_paciente","phone_professional","area","datetime","min_price","max_price","email_professional","match_time"]:
        assert col in list(df_matches.columns)


def test_get_respostas(monkeypatch)-> None:
    df_respostas = open_respostas()
    assert not df_respostas.empty
    for col in ["name_paciente" ,"phone_paciente", "area", "price_min", "price_max", "datetime"]:
        assert col in list(df_respostas.columns)


