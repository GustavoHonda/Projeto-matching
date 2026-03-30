import pandas as pd
from datetime import datetime
from src.matching import match, match_all

df_professional = pd.DataFrame([
        {"name_professional": "Prof A", "area": "psicologia", "phone_professional": "111", "price": 200, "freq": 0, "email_professional":"abc@gmail.com"},
        {"name_professional": "Prof X", "area": "psicoterapia", "phone_professional": "222", "price": 200, "freq": 0, "email_professional":"abc@gmail.com"}
    ])
df_resposta = pd.DataFrame([
    {"name_paciente": "Paciente A", "area": "psicologia", "datetime": "31/08/2024 21:33:09", "phone_paciente": "(11)111111111"},
    {"name_paciente": "Paciente B", "area": "psicologia", "datetime": "31/08/2024 21:33:08", "phone_paciente": "(11)222222222"},
    {"name_paciente": "Paciente C", "area": "psicoterapia", "datetime": "31/08/2024 21:33:08", "phone_paciente": "(11)333333333"},
])

now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

df_matchings = pd.DataFrame([
    {"name_paciente":"Paciente A","name_professional":"Prof 4","phone_paciente":"(11)111111111","phone_professional":"1234567890","area":"psicologia","datetime":"31/08/2024 21:33:09","price_min":"35","price_max":"150", "email_professional":"abc@gmail.com", "match_time":now},
    {"name_paciente":"Paciente B","name_professional":"Prof 4","phone_paciente":"(11)222222222","phone_professional":"1234567890","area":"psicologia","datetime":"31/08/2024 21:33:09","price_min":"35","price_max":"150", "email_professional":"abc@gmail.com", "match_time":now},
    {"name_paciente":"Paciente B","name_professional":"Prof 4","phone_paciente":"(11)222222222","phone_professional":"1234567890","area":"psicologia","datetime":"19/02/2025 21:33:09","price_min":"35","price_max":"150", "email_professional":"abc@gmail.com", "match_time":"2024-08-31 21:33:09"},
])

result = match(df_professional, df_resposta, df_matchings)

def test_match()-> None:  
    assert not result.empty
    
def test_match2()-> None:
    assert len(result) == 1

def test_match_values()-> None:
    assert "222" in result['phone_professional'].values

def test_match_values2()-> None:
    assert "(11)333333333" in result['phone_paciente'].values

def test_match_values3()-> None:
    assert "111" not in result['phone_professional'].values
    assert "(11)111111111" not in result['phone_paciente'].values
    assert "(11)222222222" not in result['phone_paciente'].values

# def test_recent_match() -> None:
#     recent = recent_match(df_resposta, df_matchings)
#     assert not recent.empty
#     assert len(recent) == 2