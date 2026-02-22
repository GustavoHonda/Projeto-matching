import pandas as pd
from datetime import datetime
from src.matching import match, time_match

df_professional = pd.DataFrame([
        {"name_professional": "Prof A", "area": "psicologia", "phone_professional": "111", "price": 200, "freq": 0, "email_professional":"abc@gmail.com"},
        {"name_professional": "Prof X", "area": "psicoterapia", "phone_professional": "111", "price": 200, "freq": 0, "email_professional":"abc@gmail.com"}
    ])
df_resposta = pd.DataFrame([
    {"name_paciente": "Paciente A","description":"description1", "area": "psicologia", "datetime": "31/08/2024 21:33:09", "phone_paciente": "(11)912345678", "price_min": 35,"price_max": 150},
    {"name_paciente": "Paciente B","description":"description2", "area": "psicologia", "datetime": "31/08/2024 21:33:08", "phone_paciente": "(11)912345678", "price_min": 35,"price_max": 150},
    {"name_paciente": "Paciente C","description":"description2", "area": "psicoterapia", "datetime": "31/08/2024 21:33:08", "phone_paciente": "(11)912345678", "price_min": 35,"price_max": 150},

])


df_matchings = pd.DataFrame([
    {"name_paciente":"Gustavo Akio Honda","name_professional":"Gustavo Akio Honda2","phone_paciente":"11950440023","phone_professional":"11950440023","area":"psicologia","datetime":"31/08/2024 21:33:09","price_min":"35","price_max":"150", "email_professional":"abc@gmail.com", "match_time":"31/08/2024 21:33:09"},
    {"name_paciente":"Gustavo Akio Honda3","name_professional":"Gustavo Akio Honda4","phone_paciente":"11950440023","phone_professional":"11950440023","area":"psicologia","datetime":"31/08/2024 21:33:09","price_min":"35","price_max":"150", "email_professional":"abc@gmail.com", "match_time":"31/08/2024 21:33:09"},
    {"name_paciente":"Paciente A","name_professional":"Gustavo Akio Honda4","phone_paciente":"11950440023","phone_professional":"11950440023","area":"psicologia","datetime":"19/02/2025 21:33:09","price_min":"35","price_max":"150", "email_professional":"abc@gmail.com", "match_time":"31/08/2024 21:33:09"}
])

result = match(df_professional, df_resposta, df_matchings,False)

def test_match()-> None:  
    assert not result.empty
    
def test_match2()-> None:
    assert len(result) == 1
    
def test_match3()-> None:
    assert result.iloc[0]["phone_paciente"] == "(11)912345678"

# def test_time_match()-> None:
#     assert pd.DataFrame() == time_match(df_resposta, df_matchings)

def test_match_types()-> None:
    check = "Prof X" in result['name_professional'].values
    assert check
