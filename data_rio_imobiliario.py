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

## Título da página,layout
st.set_page_config(page_title="Informações do mercado imobiliário do Rio de Janeiro",layout="wide")


def variacao_metro_bairro(bairro, tipologia):
    data_metro_quadrado = data[(data['bairro'] == bairro) & (data['principais_tipologias'] == tipologia)].groupby(['ano']).agg(media_metro_quadrado_max=('media_metro_quadrado', 'max'),
                                                            media_metro_quadrado_min=('media_metro_quadrado', 'min'),
                                                            media_metro_quadrado_mean=('media_metro_quadrado', 'mean')).reset_index()

    data_metro_quadrado.iloc[:,3] = round(data_metro_quadrado.iloc[:,3],2)

    return data_metro_quadrado

def main():
    st.write("""
	# Painel de informações do mercado imobiliário na cidade do Rio de Janeiro
	# Dados gerados a partir de transações ocorridas entre 2011 e 2025
	""")
    
    st.sidebar.title('Menu de navegação')
    st.sidebar.selectbox('Esolha a página',sorted(['Página 1', 'Página 2']), index=None, placeholder=' ')
    
    col1,col2 = st.columns(2)
    con1 = col1.container(key='comp_1')
    con2 = col2.container(key='comp_2')
    
    def exibicao_bairro(i):
        st.markdown("""
                    <style>
                    /* Targets the text within the selectbox itself */
                    .stSelectbox > div[data-baseweb="select"] > div {
                        font-size: 20px; 
                    }
                    /* Targets the options in the dropdown menu */
                    div[data-baseweb="popover"] div[role="listbox"] div p {
                        font-size: 18px !important;
                    }
                    /* Targets the label of the selectbox */
                    .stSelectbox > label p {
                        font-size: 22px !important;
                        font-weight: bold;
                    }
                    </style>
                    """, unsafe_allow_html=True)

        bairro_escolhido = st.selectbox('Escolha o bairro',sorted(data['bairro'].unique()), index=None, placeholder='Bairro', key=f'bairro{i}')
        tipologia_escolhida = st.selectbox('Escolha a tipologia',sorted(data['principais_tipologias'].unique()), index=None, placeholder='Tipologia', disabled=bairro_escolhido is None, key=f'tipo{i}')

        if (bairro_escolhido is not None) and (tipologia_escolhida is not None):
            data_metro_quadrado = variacao_metro_bairro(bairro_escolhido, tipologia_escolhida)

            try:
                fig = px.scatter(x=data_metro_quadrado['ano'],y=data_metro_quadrado['media_metro_quadrado_mean'],
                        title=f'Evolução do valor do metro quadro em imóveis do bairro: {bairro_escolhido} <br> Tipologia: {tipologia_escolhida}',
                    )
                fig.update_layout(
                    title_x=0.5,           # Define a posição X como 0.5 (centro)
                    title_xanchor='center', # Garante que o centro do título fique no ponto 0.5
                    title_font_size=24
                )
                fig.update_traces(marker=dict(size=12))
                st.plotly_chart(fig)

                data_metro_quadrado = data_metro_quadrado.rename(columns={'ano': 'Ano', 
                                                                      'media_metro_quadrado_max':'Maior valor de m² (R$/m²)', 
                                                                      'media_metro_quadrado_min':'Menor valor de m² (R$/m²)', 
                                                                      'media_metro_quadrado_mean':'Valor médio de m² (R$/m²)'
                                                                      })

                st.dataframe(data_metro_quadrado, hide_index=True)
            except ValueError:
                st.write('**Não há resultados contemplados por esta busca**')

        else:
            st.write('**Resultados serão exibidos**')        

    with con1:
        exibicao_bairro(1)

    with con2:
        exibicao_bairro(2)


if __name__ == "__main__":
    main()