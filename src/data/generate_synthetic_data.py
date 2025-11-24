from faker import Faker
import random 

import pandas as pd

import argparse

import os

import unicodedata

my_cols = [
    'name',
    'cpf',
    'birth_date',
    'adress_pcode',
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

# ---------------------------------------------------------------------------

def generate_synthetic_data(num_rows=50000):
    """
    gera um dataset de clientes com dados fakes
    """

    random.seed(42)
    rng = random.Random(42)

    Faker.seed(42)
    fake = Faker('pt_BR')

    

    all_cols = list(cat_cols.keys()) + my_cols
    data = []

    for i in range(num_rows):
        acc_creation_date = fake.date_between(start_date='-5y', end_date='today')

        transaction_time = fake.date_time_between(start_date=acc_creation_date, end_date="now")

        amount_type = rng.choices(
            ['small', 'medium', 'large'],
            weights=[0.75, 0.2, 0.05],
            k=1
        )[0]

        if amount_type == 'small':
            transaction_amount = round(rng.uniform(1, 1000), 2)
        elif amount_type == 'medium':
            transaction_amount = round(rng.uniform(1000.01, 2500), 2)
        else:
            transaction_amount = round(rng.uniform(2500.01, 5000), 2)


        row = {
            'name' : remove_acentos(f"{fake.first_name()} {fake.last_name()}"), #o comando padrao inclui titulos como sr, sra, dr...
            'cpf' : fake.cpf(),
            'birth_date' : fake.date_of_birth(minimum_age=18, maximum_age=90),
            'adress_pcode' : fake.postcode(),
            'phone_number' : fake.phone_number(),
            'acc_creation_date' : acc_creation_date,
            'agency' : fake.random_number(digits=4),
            'account': fake.random_number(digits=6),
            'credit_score' : round(rng.uniform(300, 850), 0),
            'sender_id' : fake.bothify(text="sid##??"), # asterisco insere numero, interrogacao insere letra
            'device_id' : fake.bothify(text="dv##??"),
            'device_model' : fake.bothify(text="md##??"),
            'transaction_amount' : round(rng.uniform(0, 50000), 2),
            'transaction_id' : i + 1,
            'transaction_city' : remove_acentos(fake.city()),
            'transaction_time' : transaction_time,
            'receiver_id' : fake.bothify(text="rid##??"),
            'receiver_bank' : fake.bothify(text="bk##"),
            'receiver_agency' : fake.random_number(digits=4),
            'receiver_account' : fake.random_number(digits=6),
        }


        for col, info in cat_cols.items():
            row[col] = rng.choices(
                info['options'],
                weights=info['weight'],
                k=1
                )[0]

        data.append(row)

    df = pd.DataFrame(data)

    return df[all_cols]

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