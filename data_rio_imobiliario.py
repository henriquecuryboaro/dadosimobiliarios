import pandas as pd
from pathlib import Path

#Apontando para arquivo no mesmo diretório do script executado
DF_PATH = Path(__file__).resolve().parent / 'transacoes_imobiliarias.csv'
data = pd.read_csv(DF_PATH)

#Limpeza de dados
##Remoção de vazios na coluna 'bairro'
data['bairro'] = data['bairro'].str.rstrip()

##Ajuste de textos em letras maiúsculas
data.iloc[:,6],data.iloc[:,7],data.iloc[:,12] = data.iloc[:,6].str.capitalize(),data.iloc[:,7].str.capitalize(),data.iloc[:,12].str.capitalize()

##tornar primeira letra de cada termo do endereço maiúscula e demais minúsculas
data.iloc[:,2] = data.iloc[:,2].str.title()

print(data)