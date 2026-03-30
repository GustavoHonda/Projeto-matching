import pandas as pd
import random
from faker import Faker

fake = Faker('pt_BR')
random.seed(42)

areas = ["Personal trainer",
         "Nutrição",
         "Psicoterapia",
         "Clínico geral",
         "Terapia",
         "Terapia holística"
         ]

def generate_mock_respostas(num_rows = 50)->pd.DataFrame:
    # Criar mock de respostas
    data = []
    phones = ["11912345678", "11950440023", "11977777777"]
    for i in range(1, num_rows + 1):
        nome = fake.name()
        email = fake.email()
        area = random.choice(areas)
        problema = fake.sentence(nb_words=6)
        row = [
            fake.date_time_this_year().strftime(f"%d/%m/%Y %H:%M:%S"),
            nome,
            email,
            f"55{''.join(str(random.randint(0,9)) for _ in range(8))}",
            area,
        ]
        data.append(row)
    df_respostas = pd.DataFrame(data, columns=["datetime", "name", "email", "phone", "area"])
    return df_respostas

def generate_mock_professionals(n=50, seed=42,dual=False)-> pd.DataFrame:
    fake = Faker()
    random.seed(seed)
    Faker.seed(seed)
    data = []
    if dual:
        n = n//2

    for i in range(1, n + 1):
        user = {
            "name": fake.name(),
            "area": random.choice(areas),
            "phone": f"55{''.join(str(random.randint(0,9)) for _ in range(8))}",
            "email": fake.email(),
            "active": 1
        }
        data.append(user)

    if dual:
        for user in data.copy():
            user_dual = user.copy()
            while True:
                user_dual["area"] = random.choice(areas)
                if user_dual["area"] != user["area"]:
                    break
            data.append(user_dual)
    df = pd.DataFrame(data, columns=user.keys())
    return df

def generate_mock_matches(df_profissionais=None, df_respostas=None)-> pd.DataFrame:
    all_records = set()
    match_records = [[],[],[]]
    data = []
    begin = pd.Timestamp("2025-01-01")
    now = pd.Timestamp.now()
    time = begin
    while time < now:
        for index, profissional in df_profissionais.iterrows():
            for _ in range(4):  # Tenta encontrar um paciente para o profissional
                while True:
                    resposta = df_respostas.sample(1).iloc[0]
                    record = resposta["phone"]
                    tup = profissional["phone"],resposta["phone"]
                    if resposta["phone"] not in match_records[0] and resposta["phone"] not in match_records[1] and resposta["phone"] not in match_records[2]:
                        match_records[2].append(resposta["phone"])
                        all_records.add(tup)
                        break
                fake_date = fake.date_between_dates(
                date_start=begin,
                date_end=pd.Timestamp.now()
                )
                row = {
                    "datetime": resposta["datetime"],
                    "name_paciente": resposta["name"],
                    "name_professional": profissional["name"],
                    "phone_paciente": resposta["phone"],
                    "phone_professional": profissional["phone"],
                    "area": resposta["area"],
                    "email_professional": profissional["email"],
                    "match_time": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                data.append(row)
        time += pd.Timedelta(days=29)
        print(time)
        match_records[0] = match_records[1].copy()
        match_records[1] = match_records[2].copy()
        match_records[2] = []
    df_matches = pd.DataFrame(data, columns=row.keys())
    return df_matches


def mock()-> None:
    professionals = 10
    months = 3
    pacients_per_professional = 4
    df_profissionais = generate_mock_professionals(professionals, seed=42, dual=True)
    df_respostas = generate_mock_respostas(professionals*pacients_per_professional*months)
    df_matches = generate_mock_matches(df_profissionais, df_respostas)
    df_profissionais.to_csv("./csv/mock/mock_professional.csv", index=False)
    df_respostas.to_csv("./csv/mock/mock_respostas.csv", index=False)
    df_matches.to_csv("./csv/mock/mock_matchings.csv", index=False)

def main()->None:
    mock()
    
if __name__ == "__main__":
    main()