import pandas as pd
from pandasql import sqldf
from collections import defaultdict
from src.get_data import data_info, open_matches, save_matches, open_professional, open_respostas, open_mock_professional, open_mock_respostas
from datetime import datetime

MAX_ITERATIONS = 4
NUMBER_OF_PACIENTES_PER_PROFESSIONAL = 4
DELAY_TIME = 3

def one_category_match(df_professional: type[pd.DataFrame])-> pd.DataFrame:
    df_professional = df_professional.sample(frac=1).reset_index(drop=True)
    df_professional = df_professional.drop_duplicates(subset=['phone_professional'], keep='first')
    return df_professional

def time_match(df_resposta: type[pd.DataFrame], df_matchings)-> pd.DataFrame:
    """Filtra os pacientes que já tiveram um match nos últimos 3 meses, para evitar spam para o paciente."""
    query = """
    SELECT
        paci.name_paciente,
        paci.area,
        matc.match_time as match_time
        FROM df_resposta as paci
        LEFT JOIN df_matchings as matc
            ON matc.name_paciente = paci.name_paciente
            AND matc.area = paci.area
            AND DATE(matc.match_time) > DATE('now', '-{DELAY_TIME} months')
        WHERE match_time IS NOT NULL
    """
    recent_matches = sqldf(query, locals())

    matches = (
    df_resposta
    .merge(recent_matches[['name_paciente', 'area']],
           on=['name_paciente', 'area'],
           how='left',
           indicator=True)
    )
    
    matches = matches[matches['_merge'] == 'left_only']
    matches = matches.drop(columns='_merge')
    
    return matches

def all_match(df_professional, df_resposta,df_matchings)-> pd.DataFrame:
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
    all_matches = sqldf(query, locals())
    return all_matches


def select_match(df_matchings, df_all_matches) -> pd.DataFrame:
    """Cada paciente tenha no máximo 1 matching e cada profissional tenha no máximo NUMBER_OF_PACIENTES_PER_PROFESSIONAL matchings."""
    query = """
    SELECT
        all_matches.datetime,
        all_matches.name_paciente,
        all_matches.name_professional,
        all_matches.phone_paciente,
        all_matches.phone_professional,
        all_matches.description,
        all_matches.area,
        all_matches.price_max,
        all_matches.price_min,
        all_matches.email_professional
    FROM df_all_matches all_matches
    LEFT JOIN df_matchings prev
        ON all_matches.phone_paciente = prev.phone_paciente
        AND all_matches.phone_professional = prev.phone_professional
    WHERE prev.phone_paciente IS NULL
    AND prev.phone_professional IS NULL
    """
    
    df_selected_matches = sqldf(query, locals())
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

    result_df = pd.DataFrame(matchings_final, columns=df_all_matches.columns)
    return result_df
       

def match(df_professional, df_resposta, df_matchings, save=False)-> pd.DataFrame:
    # df_professional = one_category_match(df_professional) # Seleciona apenas uma categoria por profissional para garantir envio de apenas 4 mensagens ao tododf_professional.to_csv("./csv/one_category_match.csv", index=False)
    df_resposta = time_match(df_resposta, df_matchings) # Seleciona apenas pacientes que não tiveram match nos últimos 3 meses para evitar spam
    df_resposta.to_csv("./csv/time_match_filter.csv", index=False)
    df_all_matches = all_match(df_professional, df_resposta,df_matchings) # Lista todos o matches possíveis entre profissionais e pacientes.
    df_selected_matches = select_match(df_matchings,df_all_matches)  # Seleciona os matches finais garantindo distribuição equitativa entre profisisonais.
    
    df_selected_matches["match_time"] = datetime.now()   
    if not df_selected_matches.empty:
        print(df_selected_matches)
        save_matches(df_selected_matches,df_all_matches,save)

    return df_selected_matches


def main()-> None:
    df_professional = open_professional()
    df_resposta = open_respostas()
    df_matchings = open_matches()
    
    resultado = match(df_professional,df_resposta,df_matchings,False)


def mock()-> None:
    df_professional = open_mock_professional()
    df_paciente = open_mock_respostas()
    df_paciente = open_respostas()
    df_matches = open_matches()

    print(df_professional.head())
    print(df_paciente.head())
    print(df_matches.head())
    resultado = match(df_professional, df_paciente, df_matches,False)
    resultado = time_match(df_paciente, df_matches)
    print(resultado.head(20))


if __name__ == "__main__":
    main()
    # mock()