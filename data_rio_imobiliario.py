import pandas as pd
from pathlib import Path
import plotly.express as px
import streamlit as st

#Apontando para arquivo no mesmo diretório do script executado
DF_PATH = Path(__file__).resolve().parent / 'transacoes_imobiliarias.csv'
data = pd.read_csv(DF_PATH)

#Limpeza de dados
##Remoção de vazios na coluna 'bairro'
data.iloc[:,4] = data.iloc[:,4].str.rstrip()

##Ajuste de textos em letras maiúsculas
data.iloc[:,6],data.iloc[:,7],data.iloc[:,12] = data.iloc[:,6].str.capitalize(),data.iloc[:,7].str.capitalize(),data.iloc[:,12].str.capitalize()

##tornar primeira letra de cada termo do endereço maiúscula e demais minúsculas
data.iloc[:,2] = data.iloc[:,2].str.title()

#Mudança de nomes de colunas:
data = data.rename(columns={'ano_transação': 'ano', 'média_valor_imóvel':'media_valor', 'principal_transação_mercado':'transacao', 'total_transações':'obs','mês_transação':'mes'})

#Manipulação de dados para obtenção de variáveis de interesse
data['media_metro_quadrado'] = round((data.iloc[:,10]/data.iloc[:,9]),2)

#exemplo de transações na rua Siqueira Campos no ano de 2025
# print(data[(data.iloc[:,2] == 'Rua Siqueira Campos') & (data.iloc[:,13] == 2025)])

def variacao_metro_bairro(bairro, tipologia):
    data_metro_quadrado = data[(data['bairro'] == bairro) & (data['principais_tipologias'] == tipologia)].groupby(['ano']).agg(media_metro_quadrado_max=('media_metro_quadrado', 'max'),
                                                            media_metro_quadrado_min=('media_metro_quadrado', 'min'),
                                                            media_metro_quadrado_mean=('media_metro_quadrado', 'mean')).reset_index()

    data_metro_quadrado.iloc[:,3] = round(data_metro_quadrado.iloc[:,3],2)

    return data_metro_quadrado

bairro_escolhido = st.selectbox('Escolha o bairro',data['bairro'].unique())
tipologia_escolhida = st.selectbox('Escolha a tipologia',data['principais_tipologias'].unique())
data_metro_quadrado = variacao_metro_bairro(bairro_escolhido, tipologia_escolhida)

print(data_metro_quadrado)
fig = px.scatter(x=data_metro_quadrado['ano'],y=data_metro_quadrado['media_metro_quadrado_mean'],
                 title=f'Evolução do valor do metro quadro em imóveis do bairro: {bairro_escolhido}. Tipologia: {tipologia_escolhida}')
fig.update_traces(marker=dict(size=12))

st.plotly_chart(fig)
st.write(data_metro_quadrado)