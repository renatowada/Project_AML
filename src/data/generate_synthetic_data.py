from faker import Faker

import random 

import pandas as pd

import argparse

import os

import unicodedata

from datetime import datetime, timedelta

# ---------------------------------------------

my_cols = [
    'name',
    'cpf',
    'birth_date',
    'address_pcode',
    'phone_number',
    'acc_creation_date',
    'agency',
    'account',
    'credit_score',
    'sender_id',
    'device_id',
    'device_model',
    'transaction_amount',
    'transaction_id',
    'transaction_city',
    'transaction_time',
    'receiver_id',
    'receiver_bank',
    'receiver_agency',
    'receiver_account',
    ]

# ---------------------------------------------
# cria um dicionario com as opcoes e proporcoes para as colunas categoricas
cat_cols = {
    'gender': {
        'options': ['m', 'f'],
        'weight': [0.5, 0.5]
        },
    'account_type': {
        'options': ['corrente', 'poupanca', 'salario', 'pagamento'],
        'weight': [0.4, 0.2, 0.2, 0.2]
        },
    'transaction_type': {
        'options': ['pix', 'ted', 'boleto'],
        'weight': [0.7, 0.1, 0.2]
        },
    'device': {
        'options': ['cellphone', 'desktop'],
        'weight': [0.8, 0.2]
        },
    'receiver_acc_type': {
        'options': ['corrente', 'poupanca', 'salario', 'pagamento'],
        'weight': [0.4, 0.2, 0.2, 0.2]
        },
    'device_os': {
        'options': ['myos', 'bot', 'bluescreen', 'cheeseos', 'penguin'],
        'weight': [0.2, 0.5, 0.1, 0.1, 0.1]
        }
    }

# remove caracteres especiais
def remove_acentos(texto):
    if isinstance(texto, str):
        texto = unicodedata.normalize('NFKD', texto)
        texto = texto.encode('ascii', 'ignore').decode('utf-8')
    return texto


def generate_synthetic_data(num_rows=100000):
    
    random.seed(42)
    rng = random.Random(42)
    Faker.seed(42)
    fake = Faker('pt_BR')

    # -------------------------------------------------------------------------------
    # Gerando Base de Clientes (Consistência de Identidade)

    num_unique_accounts = int(num_rows * 0.3)
    
    accounts_db = {}
    
    # Geramos os dados estáticos de cada conta UMA ÚNICA VEZ
    for i in range(num_unique_accounts):
        acc_id = fake.unique.bothify(text="acc######") # ID único garantido
        creation_date = fake.date_between(start_date='-5y', end_date='today')
        
        accounts_db[acc_id] = {
            'name': remove_acentos(f"{fake.first_name()} {fake.last_name()}"),
            'cpf': fake.cpf(),
            'birth_date': fake.date_of_birth(minimum_age=18, maximum_age=90),
            'address_pcode': fake.postcode(),
            'phone_number': fake.phone_number(),
            'acc_creation_date': creation_date,
            'agency': fake.random_number(digits=4),
            'account': fake.random_number(digits=6),
            'credit_score': round(rng.uniform(300, 850), 0),
            'device_id': fake.bothify(text="dv##"),
            'device_model': fake.bothify(text="md##"),
        }

    # Converter as chaves (IDs) em lista para poder sortear e definir papéis
    all_account_ids = list(accounts_db.keys())
    rng.shuffle(all_account_ids)


    # Definir Papéis (Topologia) AGORA, antes de gerar transações
    n_mules = int(len(all_account_ids) * 0.05)
    n_bosses = int(len(all_account_ids) * 0.01)
    
    mules_pool = all_account_ids[:n_mules]
    bosses_pool = all_account_ids[n_mules : n_mules + n_bosses]
    honest_pool = all_account_ids[n_mules + n_bosses:]

    print(f"Base de clientes criada: {len(all_account_ids)} contas únicas.")
    print(f"Perfis: {len(mules_pool)} Laranjas, {len(bosses_pool)} Chefes, {len(honest_pool)} Honestos.")


    # ---------------------------------------------------------------------------
    # Gerando Transações

    data = []
    
    # Configuração de Datas
    today = datetime.now()
    cutoff_date = today - timedelta(days=10)
    fraud_entry_end_global = cutoff_date - timedelta(days=1)
    fraud_exit_start_global = cutoff_date

    mule_balances = {m_id: 0.0 for m_id in mules_pool}
    
    # Loop para gerar as LINHAS de transação
    for i in range(num_rows):
        
        # 1. Escolher Cenário
        scenario = rng.choices(['normal', 'fraud_cycle'], weights=[0.85, 0.15], k=1)[0]
        
        rows_to_add = [] # Lista temporária para guardar as linhas deste ciclo

        # --- Lógica de Definição de IDs ---
        
        # Cenário Normal
        # Honesto -> Honesto
        if scenario == 'normal':
            sender_id = rng.choice(honest_pool)
            receiver_id = rng.choice(honest_pool)
            while receiver_id == sender_id: receiver_id = rng.choice(honest_pool)
            
            trans_date = fake.date_time_between(start_date='-60d', end_date="now")
            amount = round(rng.uniform(50, 2000), 2)
            trans_type = 'pix'

            sender_profile = accounts_db[sender_id]
            receiver_profile = accounts_db[receiver_id]

            # Montar linha
            row_normal = {
                'transaction_id': i,
                'transaction_amount': amount,
                'transaction_time': trans_date,
                'sender_id': sender_id,
                'receiver_id': receiver_id,
                'transaction_type': trans_type,
                'transaction_city': remove_acentos(fake.city()),
                
                # Dados do Sender
                'name': sender_profile['name'],
                'cpf': sender_profile['cpf'],
                'birth_date': sender_profile['birth_date'],
                'address_pcode': sender_profile['address_pcode'],
                'phone_number': sender_profile['phone_number'],
                'acc_creation_date': sender_profile['acc_creation_date'],
                'agency': sender_profile['agency'],
                'account': sender_profile['account'],
                'credit_score': sender_profile['credit_score'],
                'device_id': sender_profile['device_id'],
                'device_model': sender_profile['device_model'],

                # Dados do Receiver
                'receiver_name': receiver_profile['name'],
                'receiver_bank': fake.bothify(text="bk##"),
                'receiver_agency': receiver_profile['agency'],
                'receiver_account': receiver_profile['account']
            }
            rows_to_add.append(row_normal)

        # Cenário Fraudulento
        elif scenario == 'fraud_cycle':
            sender_honest = rng.choice(honest_pool) # Origem
            mule = rng.choice(mules_pool)           # Laranja
            boss = rng.choice(bosses_pool)          # Chefe

            # Honesto -> Laranja
            sender_id = sender_honest
            receiver_id = mule
            
            sender_profile = accounts_db[sender_id]
            receiver_profile = accounts_db[receiver_id]

            base_amount = round(rng.uniform(2000, 15000), 2)
            entry_date = fake.date_time_between(start_date='-30d', end_date="-2d")

            row_in = {
                'transaction_id': i,
                'transaction_amount': base_amount,
                'transaction_time': entry_date,
                'sender_id': sender_id,
                'receiver_id': receiver_id,
                'transaction_type': 'pix',
                'transaction_city': remove_acentos(fake.city()),

                # Dados do Sender (Honesto)
                'name': sender_profile['name'],
                'cpf': sender_profile['cpf'],
                'birth_date': sender_profile['birth_date'],
                'address_pcode': sender_profile['address_pcode'],
                'phone_number': sender_profile['phone_number'],
                'acc_creation_date': sender_profile['acc_creation_date'],
                'agency': sender_profile['agency'],
                'account': sender_profile['account'],
                'credit_score': sender_profile['credit_score'],
                'device_id': sender_profile['device_id'],
                'device_model': sender_profile['device_model'],

                # Dados do Receiver (Laranja)
                'receiver_name': receiver_profile['name'],
                'receiver_bank': fake.bothify(text="bk##"),
                'receiver_agency': receiver_profile['agency'],
                'receiver_account': receiver_profile['account']
            }
            rows_to_add.append(row_in)

            # Laranja -> Chefe
            sender_id_out = mule
            receiver_id_out = boss
            
            sender_profile_out = accounts_db[sender_id_out]
            receiver_profile_out = accounts_db[receiver_id_out]

            # Transfere rapidamente para outra conta (de 1 a 6 horas)
            delay = timedelta(hours=rng.randint(1, 6), minutes=rng.randint(0, 59))
            exit_date = entry_date + delay

            # O Laranja fica com uma comissão
            fee_percent = rng.uniform(0.02, 0.05)
            exit_amount = round(base_amount * (1 - fee_percent), 2)

            row_out = {
                'transaction_id': i + 1000000, # ID offset
                'transaction_amount': exit_amount,
                'transaction_time': exit_date,
                'sender_id': sender_id_out,
                'receiver_id': receiver_id_out,
                'transaction_type': 'pix',
                'transaction_city': remove_acentos(fake.city()),

                # Dados do Sender (Laranja)
                'name': sender_profile_out['name'],
                'cpf': sender_profile_out['cpf'],
                'birth_date': sender_profile_out['birth_date'],
                'address_pcode': sender_profile_out['address_pcode'],
                'phone_number': sender_profile_out['phone_number'],
                'acc_creation_date': sender_profile_out['acc_creation_date'],
                'agency': sender_profile_out['agency'],
                'account': sender_profile_out['account'],
                'credit_score': sender_profile_out['credit_score'],
                'device_id': sender_profile_out['device_id'],
                'device_model': sender_profile_out['device_model'],

                # Dados do Receiver (Chefe)
                'receiver_name': receiver_profile_out['name'],
                'receiver_bank': fake.bothify(text="bk##"),
                'receiver_agency': receiver_profile_out['agency'],
                'receiver_account': receiver_profile_out['account']
            }
            rows_to_add.append(row_out)

        # Preenche colunas categóricas aleatórias e adiciona à lista final
        for row in rows_to_add:
            for col, info in cat_cols.items():
                # Verifica se já não foi preenchido
                if col not in row: 
                    row[col] = rng.choices(info['options'], weights=info['weight'], k=1)[0]
            
            data.append(row)

    df = pd.DataFrame(data)
    
    cols_order = ['transaction_id', 'transaction_time', 'transaction_amount', 
                  'sender_id', 'name', 'cpf', 'receiver_id', 'receiver_name'] + \
                 [c for c in df.columns if c not in ['transaction_id', 'transaction_time', 'transaction_amount', 'sender_id', 'name', 'cpf', 'receiver_id', 'receiver_name']]
    
    return df[cols_order]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Gera dados sintéticos.")
    parser.add_argument("--rows", type=int, default=10000, help="Número de linhas a gerar")
    args = parser.parse_args()

    df = generate_synthetic_data(num_rows=args.rows)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.dirname(script_dir)
    project_root = os.path.dirname(src_dir)
    output_path = os.path.join(project_root, 'data', '01_raw', 'synthetic_dataset.csv')
    
    output_dir = os.path.dirname(output_path)
    os.makedirs(output_dir, exist_ok=True)

    df.to_csv(output_path, index=False)

    print(f"Dataset salvo em {output_path}")





