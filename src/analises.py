import pandas as pd

def analise():

    pac = pd.read_csv("./csv/mock/mock_respostas.csv")
    mat = pd.read_csv("./csv/mock/mock_matchings.csv")
    now = pd.Timestamp.now()
    delay = pd.Timedelta(days=60)
    time =  now - delay
    print(time)
    print(delay)   
    print(now) 
    mat["match_time"] = pd.to_datetime(mat["match_time"])
    mat_recent = mat[mat["match_time"] > time].copy()
    mat_recent.to_csv("./csv/simulation/1-recent.csv", index=False)
    pac_phones = set(mat_recent["phone_paciente"])
    pac = pac[~pac["phone"].isin(pac_phones)].copy()
    pac.to_csv("./csv/simulation/2-nao-match.csv", index=False)

analise()