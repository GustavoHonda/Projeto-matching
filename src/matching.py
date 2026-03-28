import pandas as pd
from pandasql import sqldf
from src.prematch import prepare_df
from collections import defaultdict
from src.get_data import data_info, open_matches, save_matches, open_professional, open_respostas, open_mock_professional, open_mock_respostas
from datetime import datetime

MAX_ITERATIONS = 4
NUMBER_OF_PACIENTES_PER_PROFESSIONAL = 4

def match_all(df_professional, df_resposta,df_matchings)-> pd.DataFrame:
    if df_resposta.empty:
        raise ValueError("df_resposta está vazio. Verifique se os dados foram carregados corretamente.")

    """Realiza o matching entre profissionais e pacientes, considerando os critérios de área."""
    query = """
    SELECT 
        paci.name_paciente,
        paci.area AS area,
        paci.phone_paciente,
        paci.price_max AS price_max,
        paci.price_min AS price_min,
        paci.datetime AS datetime,
        paci.description AS description,
        prof.name_professional,
        prof.area AS area_professional,
        prof.phone_professional,
        prof.email_professional,
        ROW_NUMBER() OVER (PARTITION BY paci.phone_paciente ORDER BY paci.datetime DESC) as rn_paci
    FROM df_professional prof
    JOIN df_resposta paci
        ON paci.area = prof.area
    """
    match_all = sqldf(query, locals())
    return match_all

def match_previous(df_match_all, df_matchings)-> pd.DataFrame:
    """Cada paciente tenha no máximo 1 matching e cada profissional tenha no máximo NUMBER_OF_PACIENTES_PER_PROFESSIONAL matchings."""
    query = """
    SELECT
        match_all.datetime,
        match_all.name_paciente,
        match_all.name_professional,
        match_all.phone_paciente,
        match_all.phone_professional,
        match_all.description,
        match_all.area,
        match_all.price_max,
        match_all.price_min,
        match_all.email_professional
    FROM df_match_all match_all
    LEFT JOIN df_matchings prev
        ON match_all.phone_paciente = prev.phone_paciente
        AND match_all.phone_professional = prev.phone_professional
    WHERE prev.phone_paciente IS NULL
    AND prev.phone_professional IS NULL
    """
    
    df_selected_matches = sqldf(query, locals())
    return df_selected_matches


def select_match(df_matchings, df_match_all) -> pd.DataFrame:
    df_selected_matches = match_previous(df_match_all,df_matchings)
    df_selected_matches = df_selected_matches.sample(frac=1, random_state=42).reset_index(drop=True)

    # contadores
    matchings_arquivados = set()
    if not df_matchings.empty:
        for row in df_matchings[['phone_paciente', 'phone_professional']].values:
            matchings_arquivados.add(tuple(row))
    matchings_existentes = defaultdict(int)
    professional_counts = defaultdict(int)
    paciente_counts = defaultdict(int)
    
    matchings_final = []
    condition = 1
    
    while(condition):
        print(f"Iteração: {condition}")
        # Loop guloso para selecionar matchings
        for _, row in df_selected_matches.iterrows():
            paciente = row['phone_paciente']
            professional = row['phone_professional']
            chave = (paciente, professional)

            if chave in matchings_arquivados: # verifica se o matching já foi feito antes
                if condition > 2:
                    pass
                else:
                    continue
            if paciente_counts[paciente] >= 1: # garante que cada paciente tenha no máximo 1 matching
                continue
            if professional_counts[professional] >= NUMBER_OF_PACIENTES_PER_PROFESSIONAL: # garante que cada profissional tenha no máximo NUMBER_OF_PACIENTES_PER_PROFESSIONAL matchings
                continue
            if chave in matchings_existentes: # verifica se o matching já foi selecionado nessa iteração
                continue

            # garante homogeneidade:
            min_count = min(professional_counts.values(), default=0)
            if professional_counts[professional] > min_count:
                continue  # pula se esse profissional já está acima da mínima

            # adiciona o matching
            matchings_final.append(row)
            paciente_counts[paciente] += 1
            professional_counts[professional] += 1
            matchings_existentes[chave] = matchings_existentes.get(chave,0) + 1  # marca como existente

        # Verificar se todos os profissionais têm pelo menos 4 pacientes
        if all(count >= NUMBER_OF_PACIENTES_PER_PROFESSIONAL for count in professional_counts.values()):
            condition = 0  # todos os profissionais têm pelo menos 4 pacientes
        elif(condition < MAX_ITERATIONS):
            condition += 1
        else:
            condition = 0  # evita loop infinito, sai após 3 tentativas
            
            print("🔹 Pacientes Atribuidos por profissional")
            for key in professional_counts.keys():
                print(f"    Profissional {key}: {professional_counts[key]} pacientes")

            print(" ⚠️ Limite de iterações atingido, saindo do loop. Nem todos os profissionais atingiram 4 pacientes.")

    result_df = pd.DataFrame(matchings_final, columns=df_match_all.columns)
    return result_df
       

def match(df_professional, df_resposta, df_matchings, save=False)-> pd.DataFrame:
    df_professional, df_resposta, df_matchings = prepare_df(df_professional, df_resposta, df_matchings) # Filtra os pacientes que tiveram um match nos últimos 3 meses e remove profissionais duplicados.
    df_match_all = match_all(df_professional, df_resposta,df_matchings) # Lista todos o matches possíveis entre profissionais e pacientes.
    df_selected_matches = select_match(df_matchings,df_match_all)  # Seleciona os matches finais garantindo distribuição equitativa entre profisisonais.
    
    df_selected_matches["match_time"] = datetime.now()   
    if not df_selected_matches.empty:
        print(df_selected_matches)
        save_matches(df_selected_matches,df_match_all,save)

    return df_selected_matches


def main()-> None:
    df_professional = open_professional()
    df_resposta = open_respostas()
    df_matchings = open_matches()

    df_resposta.to_csv("./csv/respostas.csv", index=False)
    df_professional.to_csv("./csv/professional.csv", index=False)
    df_matchings.to_csv("./csv/matchings.csv", index = False)

    result = match(df_professional,df_resposta,df_matchings,False)


def mock()-> None:
    df_professional = open_mock_professional()
    df_paciente = open_mock_respostas()
    df_paciente = open_respostas()
    df_matches = open_matches()

    print(df_professional.head())
    print(df_paciente.head())
    print(df_matches.head())
    resultado = match(df_professional, df_paciente, df_matches,False)
    print(resultado.head(20))


if __name__ == "__main__":
    main()
    # mock()