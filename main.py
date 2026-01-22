import pandas as pd
from pathlib import Path
import plotly.express as px
import streamlit as st
import sidrapy
import datetime

## Título da página,layout
st.set_page_config(page_title="Informações do mercado imobiliário do Rio de Janeiro",layout="wide")

#Apontando para arquivo no mesmo diretório do script executado
DF_PATH = Path(__file__).resolve().parent / 'transacoes_imobiliarias.csv'

@st.cache_data
def load_data():
    return pd.read_csv(DF_PATH)

data = load_data()

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

@st.cache_data
def variacao_metro_bairro(bairro, tipologia):
    data_metro_quadrado = data[(data['bairro'] == bairro) & (data['principais_tipologias'] == tipologia)].groupby(['ano']).agg(media_metro_quadrado_max=('media_metro_quadrado', 'max'),
                                                            media_metro_quadrado_min=('media_metro_quadrado', 'min'),
                                                            media_metro_quadrado_mean=('media_metro_quadrado', 'mean')).reset_index()

    data_metro_quadrado.iloc[:,3] = round(data_metro_quadrado.iloc[:,3],2)

    return data_metro_quadrado

# def maiores_variacoes(tipologia_escolhida):
# tipologia_escolhida = 'Apartamento'

def main():
    st.write('# Painel de informações do mercado imobiliário na cidade do Rio de Janeiro')
    
    st.sidebar.title('Menu de navegação')
    pagina = st.sidebar.selectbox('Esolha a página',['Início','Evolução de transações em bairros', 'Comparação de indicadores'])
    
    if pagina == 'Início':
        st.write('### Este painel exibe informações referentes a transações reais de imóveis na cidade do Rio de Janeiro, ocorridas entre os anos de 2011 e 2025')
        st.write('### Os registros analisados provêm de dados públicos que podem ser encontrados no portal da prefeitura do Rio de Janeiro (Data.Rio), além de dados econômicos do IBGE.')
        st.write('### \n')
        st.write('\n ')
        st.markdown('### **As seguintes consultas podem ser realizadas:**')
        st.markdown('###   **1. Evolução de transações em bairros**')
        st.write('### Avalia o perfil das transações realizadas ao longo do tempo em um determinado bairro, considerando uma tipologia escolhida.')
        st.write('### É possível analisar estes dados selecionando dois bairros ou duas tipologias ao mesmo  tempo')
        st.write('\n')
        st.markdown('###  **2. Comparação de indicadores**')
        st.write('### Compara as variações observadas nas transações realizadas com o valor de IPCA para um dado período.')
        st.write('### Esta comparação fornece um indicativo de quais bairros proporcionaram um investimento em imóveis que pode ter oferecido ganho real aos compradores no período avaliado')



    if pagina == 'Evolução de transações em bairros':

        st.write('### Registros de negociações de imóveis ocorridas entre 2011 e 2025 no município')
        st.write('### Fonte dos dados - Portal Data.Rio')

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
                        title_font_size=24,
                        yaxis=dict(title='Valor médio do metro quadrado por transação (R$/m²)'),
                        xaxis=dict(title='Ano')


                    )
                    fig.update_traces(marker=dict(size=12))
                    st.plotly_chart(fig)

                    data_metro_quadrado['variacao_anual'] = '-'
                    for i in range(1,len(data_metro_quadrado)):
                        data_metro_quadrado.iloc[i,4] = round(100*((data_metro_quadrado.iloc[i,3] - data_metro_quadrado.iloc[i-1,3])/data_metro_quadrado.iloc[i-1,3]),2)

                    data_metro_quadrado = data_metro_quadrado.rename(columns={'ano': 'Ano', 
                                                                        'media_metro_quadrado_max':'Maior valor de m² (R$/m²)', 
                                                                        'media_metro_quadrado_min':'Menor valor de m² (R$/m²)', 
                                                                        'media_metro_quadrado_mean':'Valor médio de m² (R$/m²)',
                                                                        'variacao_anual':'Variação anual (%)'
                                                                        })

                    ultima_obs = len(data_metro_quadrado)-1
                    variacao = round(100*((data_metro_quadrado.iloc[ultima_obs,3] - data_metro_quadrado.iloc[0,3])/data_metro_quadrado.iloc[0,3]),2)
                    st.write(f'### Variação total observada no período para imóveis no bairo para a tipologia escolhida: {variacao}%')
                    st.dataframe(data_metro_quadrado, hide_index=True)
                except ValueError:
                    st.write('### Não há resultados contemplados por esta busca')

            else:
                st.write('### Selecione as opções acima')        

        with con1:
            exibicao_bairro(1)

        with con2:
            exibicao_bairro(2)
    
    if pagina == 'Comparação de indicadores':
        
        def ipca_acumulado(inicio,fim):

            inicio = str(inicio)[0:4]+str(inicio)[5:7]
            fim = str(fim)[0:4]+str(fim)[5:7]

            # monta o período no formato exigido pelo SIDRA
            period = f'{inicio}-{fim}'
            

            ipca = sidrapy.get_table(
                table_code='1737',
                territorial_level='1',     # Brasil
                ibge_territorial_code='1',
                variable='63',             # Variação mensal
                period=period,
                header='n'
            )

            df_ipca = pd.DataFrame(ipca)

            df_ipca['V'] = df_ipca['V'].astype(float)
            df_ipca['decimal'] = (df_ipca['V'])/100
            ipca_acumulado_periodo = 1

            for i in range(len(df_ipca)):
                ipca_acumulado_periodo = ipca_acumulado_periodo*(1+(df_ipca.iloc[i,11]))

            return (ipca_acumulado_periodo-1)

        col3,col4 = st.columns(2)
        con3 = col3.container(key='comp_3')
        con4 = col4.container(key='comp_4')

        with con3:

            inicio = st.date_input('### Início da série', min_value=datetime.date(1900, 1, 1), max_value=None)
            fim = st.date_input('### Fim da série', min_value=datetime.date(1900, 1, 1), max_value=None)

            try:
                inflacao_acumulada = ipca_acumulado(inicio,fim)
                st.write(f'# IPCA acumulado entre {inicio} e {fim}: {round(100*(inflacao_acumulada),2)}%')
            except KeyError:
                st.write('### Selecione um intervalo de datas para verificar indicadores financeiros. Caso nenhum valor de IPCA acumulado seja exibido, não há dados históricos para este período')

        with con4:
            tipologia_var = st.selectbox('Escolha a tipologia',sorted(data['principais_tipologias'].unique()), index=None, placeholder='Tipologia', key=f'tipo_var')

            if (tipologia_var is not None):
                lista_bairro_var = []
                try:
                    for bairro in (data['bairro'].unique()):
                        resumobairro = variacao_metro_bairro(bairro,tipologia_var)
                        
                        if resumobairro.empty or len(resumobairro) < 2:
                            continue
                        
                        resumobairro = resumobairro[(resumobairro['ano'] >= inicio.year) & (resumobairro['ano'] <= fim.year)]

                        if resumobairro.empty or len(resumobairro) < 2:
                            continue

                        ultima_obs = len(resumobairro)-1
                        variacao = round(100*((resumobairro.iloc[ultima_obs,3] - resumobairro.iloc[0,3])/resumobairro.iloc[0,3]),2)
                        lista_bairro_var.append([bairro,variacao])

                        tabela_resumo = pd.DataFrame(lista_bairro_var, columns=['Bairro','Variação (%)'])
                        maiores_var = tabela_resumo.sort_values(by='Variação (%)', ascending=False).head(10)

                    st.dataframe(maiores_var, hide_index=True)
                except:
                    st.write('')

            else:
                st.write('### Selecione uma opção de tipologia acima')

if __name__ == "__main__":
    main()