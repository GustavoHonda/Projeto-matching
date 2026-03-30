from src.get_data import open_mock_professional, open_mock_respostas, open_mock_matches
from src.matching import match
from src.create_mock import mock
import pandas as pd

def match_simulation()-> None:  
    
    df_professional = open_mock_professional()
    df_resposta = open_mock_respostas()
    df_matchings = open_mock_matches()
    result = match(df_professional, df_resposta, df_matchings,0)

def main():
    mock()
    match_simulation()

if __name__ == "__main__":
    main()