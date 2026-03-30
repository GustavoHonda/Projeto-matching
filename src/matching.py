from itertools import count

import pandas as pd
from pandasql import sqldf
from collections import defaultdict
from src.get_data import data_info, open_matches, save_matches, open_professional, open_respostas, open_mock_professional, open_mock_respostas
from datetime import datetime

MAX_ITERATIONS = 8
NUMBER_OF_PACIENTES_PER_PROFESSIONAL = 4
DELAY_TIME = 1

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
    recent_matches.to_csv("./csv/1-matching_recent.csv", index = False)
    return recent_matches

def time_match(df_resposta: type[pd.DataFrame], recent_matches: pd.DataFrame)-> pd.DataFrame:
    """Remove pacientes que tiveram um match nos últimos 3 meses."""
    matches = (
    df_resposta.merge(
        recent_matches[['phone_paciente', 'area']],
        on=['phone_paciente', 'area'],
        how='left',
        indicator=True)
    )
    
    matches = matches[matches['_merge'] == 'left_only']
    matches = matches.drop(columns='_merge')
    matches.to_csv("./csv/2-matching_time.csv", index=False)
    return matches

def match_all(df_professional, df_resposta,df_matchings)-> pd.DataFrame:
    """Realiza o matching entre profissionais e pacientes, considerando os critérios de área."""
    if df_resposta.empty:
        raise ValueError("df_resposta está vazio. Verifique se os dados foram carregados corretamente.")

    query = """
    SELECT * FROM(SELECT 
        paci.name_paciente,
        paci.area AS area,
        paci.phone_paciente,
        paci.datetime AS datetime,
        prof.name_professional,
        prof.phone_professional,
        prof.email_professional,
        ROW_NUMBER() OVER (PARTITION BY paci.phone_paciente ORDER BY paci.datetime DESC) as rn_paci
    FROM df_resposta paci
    INNER JOIN df_professional prof
        ON paci.area = prof.area 
    ) AS subconsulta
    -- WHERE rn_paci = 1
    """
    match_all = sqldf(query, locals())
    match_all.to_csv("./csv/3-matching_all.csv", index=False)
    return match_all

def match_previous(df_match_all, df_matchings)-> pd.DataFrame:
    """Remove os matches que já foram feitos anteriormente."""
    query = """
    SELECT
        match_all.datetime,
        match_all.name_paciente,
        match_all.name_professional,
        match_all.phone_paciente,
        match_all.phone_professional,
        match_all.area,
        match_all.email_professional
    FROM df_match_all match_all
    LEFT JOIN df_matchings prev
        ON match_all.phone_paciente = prev.phone_paciente
        AND match_all.phone_professional = prev.phone_professional
    WHERE prev.phone_paciente IS NULL
    AND prev.phone_professional IS NULL
    """
    
    df_selected_matches = sqldf(query, locals())
    df_selected_matches.to_csv("./csv/4-match_previous.csv", index=False)
    return df_selected_matches

def select_match(df_matchings, df_selected_matches) -> pd.DataFrame:
    df_selected_matches = df_selected_matches.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # contadores
    matchings_arquivados = set()
    if not df_matchings.empty:
        for row in df_matchings[['phone_paciente', 'phone_professional']].values:
            matchings_arquivados.add(tuple(row))
    matchings_existentes = defaultdict(int)
    
    # Inicializa o contador para pacientes, garantindo que cada paciente tenha no máximo 1 matching
    paciente_counts = defaultdict(int)
    paciente_counts.update({phone: 0 for phone in df_selected_matches['phone_paciente'].unique()})

    # Inicializa os contadores para profissionais e pacientes que aparecem nos matchings selecionados
    professional_counts = defaultdict(lambda: defaultdict(int))
    for row in df_selected_matches.drop_duplicates(subset=['phone_professional','area']).drop_duplicates(subset=['phone_paciente','area']).itertuples():
        professional_counts[row.phone_professional][row.area] = 0
    
    
    matchings_final = []
    condition = 1
    while(condition):
        print(f"Iteração: {condition}")
        # Loop guloso para selecionar matchings
        for _, row in df_selected_matches.iterrows():
            paciente = row['phone_paciente']
            professional = row['phone_professional']
            area = row['area']
            chave = (paciente, professional)
            
            if paciente_counts[paciente] >= 1: # garante que cada paciente tenha no máximo 1 matching
                # print("pass by paciente")
                continue
            if sum(professional_counts[professional].values()) >= NUMBER_OF_PACIENTES_PER_PROFESSIONAL: # garante que cada profissional tenha no máximo NUMBER_OF_PACIENTES_PER_PROFESSIONAL matchings
                # print("pass by profissional")
                continue
            if chave in matchings_existentes: # verifica se o matching já foi selecionado nessa iteração
                # print("pass by existente")
                continue

            # garante homogeneidade:
            # min_count = min(paciente_per_professional, default=0)
            # if sum(professional_counts[professional].values())> min_count:
            #     print("pass by homogeneidade")
            #     continue  # pula se esse profissional já está acima da mínima

            # adiciona o matching
            matchings_final.append(row)
            # print("hit!")
            paciente_counts[paciente] += 1
            professional_counts[professional][area] += 1
            matchings_existentes[chave] = matchings_existentes.get(chave,0) + 1  # marca como existente

        # Verificar se todos os profissionais têm pelo menos 4 pacientes
        
        if all(sum(area.values()) >= NUMBER_OF_PACIENTES_PER_PROFESSIONAL for area in professional_counts.values() ):
            condition = 0  # todos os profissionais têm pelo menos 4 pacientes
        elif(condition < MAX_ITERATIONS):
            condition += 1
        else:
            condition = 0  # evita loop infinito, sai após 3 tentativas
            
            print("🔹 Pacientes Atribuidos por profissional")
            total_por_profissional = defaultdict(int)

            # 2. Percorre seu dicionário aninhado e soma tudo
            for profissional, phones in professional_counts.items():
                    count = sum(phones.values())
                    total_por_profissional[profissional] += count

            # 3. Agora você imprime o resultado consolidado
            print("Relatório Geral de Atendimentos:")
            for phone, total in total_por_profissional.items():
                print(f"    Profissional {phone}: {total} pacientes no total")

            print(" ⚠️ Limite de iterações atingido, saindo do loop. Nem todos os profissionais atingiram 4 pacientes.")

    result_df = pd.DataFrame(matchings_final, columns=df_selected_matches.columns)
    result_df.to_csv("./csv/5-matchings_selected.csv", index=False)
    return result_df

def match(df_professional, df_resposta, df_matchings, save=False)-> pd.DataFrame:
    recent_matches = recent_match(df_resposta, df_matchings) # Filtra os pacientes que tiveram um match nos últimos 3 meses.
    df_non_recent_pacients = time_match(df_resposta, recent_matches) # Remove pacientes que tiveram um match nos últimos 3 meses.
    df_match_all = match_all(df_professional, df_non_recent_pacients,df_matchings) # Lista todos o matches possíveis entre profissionais e pacientes.
    df_selected_matches = match_previous(df_match_all,df_matchings) # Seleciona os matches que ainda não foram feitos, garantindo que cada paciente tenha no máximo 1 matching e cada profissional tenha no máximo NUMBER_OF_PACIENTES_PER_PROFISSIONAL matchings.
    df_result = select_match(df_matchings,df_selected_matches)  # Seleciona os matches finais garantindo distribuição equitativa entre profisisonais.
    
    df_result["match_time"] = datetime.now()
    if not df_result.empty:
        print(df_result)
        save_matches(df_result,save)

    return df_result

def main()-> None:
    df_professional, df_professional_area = open_professional()
    df_resposta, df_resposta_area = open_respostas()
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