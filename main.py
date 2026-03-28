import pandas as pd
from pathlib import Path
import plotly.express as px
import streamlit as st
import sidrapy
import datetime

## Título da página,layout
st.set_page_config(page_title="Informações do mercado imobiliário do Rio de Janeiro",layout="wide")

#Apontando para arquivos no mesmo diretório do script executado
##Base Data.Rio
DF_PATH = Path(__file__).resolve().parent / 'transacoes_imobiliarias.csv'
@st.cache_data
def load_data():
    return pd.read_csv(DF_PATH)

data = load_data()

##Bases de CDI baixadas localmente a partir de acesso pela biblioteca python-bcb (via Google Colab)
DF_CDI = Path(__file__).resolve().parent / 'CDI.parquet'
@st.cache_data
def load_cdiparquet():
    return pd.read_parquet(DF_CDI)

CDI = load_cdiparquet()

DF_CDI2 = Path(__file__).resolve().parent / 'CDI2.parquet'
@st.cache_data
def load_cdi2parquet():
    return pd.read_parquet(DF_CDI2)

CDI2 = load_cdi2parquet()


#Limpeza de dados
##Remoção de vazios na coluna 'bairro'
data.iloc[:,4] = data.iloc[:,4].str.rstrip()

##Ajuste de textos em letras maiúsculas
data.iloc[:,6],data.iloc[:,7],data.iloc[:,12] = data.iloc[:,6].str.capitalize(),data.iloc[:,7].str.capitalize(),data.iloc[:,12].str.capitalize()

##tornar primeira letra de cada termo do endereço maiúscula e demais minúsculas e fazer alterações em abreviações de identificações de logradouros
data.iloc[:,2] = data.iloc[:,2].str.title()

data.iloc[:,2] = data.iloc[:,2].str.replace('Avn', 'Av.', regex=False)
data.iloc[:,2] = data.iloc[:,2].str.replace('Prc', 'Praça', regex=False)
data.iloc[:,2] = data.iloc[:,2].str.replace('Lrg', 'Largo', regex=False)
data.iloc[:,2] = data.iloc[:,2].str.replace('Trv', 'Travessa', regex=False)

#Mudança de nomes de colunas:
data = data.rename(columns={'ano_transação': 'ano', 'média_valor_imóvel':'media_valor', 'principal_transação_mercado':'transacao', 'total_transações':'obs','mês_transação':'mes'})


#Manipulação de dados para obtenção de variáveis de interesse
data['media_metro_quadrado'] = round((data.iloc[:,10]/data.iloc[:,9]),2)

@st.cache_data
def variacao_metro_bairro(bairro, tipologia):
    data_metro_quadrado = data[(data['bairro'] == bairro) & (data['principais_tipologias'] == tipologia)].groupby(['ano']).agg(media_metro_quadrado_max=('media_metro_quadrado', 'max'),
                                                            media_metro_quadrado_min=('media_metro_quadrado', 'min'),
                                                            media_metro_quadrado_med=('media_metro_quadrado', 'median'),
                                                            transacoes=('obs','count')).reset_index()

    data_metro_quadrado.iloc[:,3] = round(data_metro_quadrado.iloc[:,3],2)

    return data_metro_quadrado

@st.cache_data
def ranking_bairro(tipologia,inicio,fim):
    lista_bairro_var = []
                
    for bairro in (data['bairro'].unique()):    
        resumo = variacao_metro_bairro(bairro,tipologia)
                        
        if resumo.empty or len(resumo) < 2:
            continue
                        
        resumo = resumo[(resumo['ano'] >= inicio.year) & (resumo['ano'] <= fim.year)]

        if len(resumo) < 2:
            continue

        variacao = ((resumo.iloc[-1]['media_metro_quadrado_med'] - resumo.iloc[0]['media_metro_quadrado_med'])/resumo.iloc[0]['media_metro_quadrado_med'])*100

        lista_bairro_var.append([bairro,round(variacao,2)])

    
    return (
        pd.DataFrame(lista_bairro_var, columns=['Bairro', 'Variação (%)'])
        .sort_values('Variação (%)', ascending=False)
        .head(10)
    )

@st.cache_data
def variacao_metro_logradouro(logradouro, tipologia,inicio,fim):
    data_metro_quadrado_lgd = data[(data['logradouro'] == logradouro) & 
                                   (data['principais_tipologias'] == tipologia) &
                                   (data['ano'] >= inicio.year) &
                                   (data['ano'] <= fim.year)].groupby(['ano']).agg(media_metro_quadrado_max=('media_metro_quadrado', 'max'),
                                                            media_metro_quadrado_min=('media_metro_quadrado', 'min'),
                                                            media_metro_quadrado_med=('media_metro_quadrado', 'median'),
                                                            transacoes=('obs','count')).reset_index()

    data_metro_quadrado_lgd.iloc[:,3] = round(data_metro_quadrado_lgd.iloc[:,3],2)

    return data_metro_quadrado_lgd

@st.cache_data
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


@st.cache_data
def var_logradouro(lgd_escolhido, tipologia_lgd,inicio,fim):
    data_logradouro = variacao_metro_logradouro(lgd_escolhido, tipologia_lgd,inicio,fim)

    if data_logradouro.empty:
        return pd.DataFrame(data_logradouro)

    else:
        return pd.DataFrame(data_logradouro)


@st.cache_data
def cdi_acumulado(inicio,fim):
    df_cdi = pd.concat([CDI,CDI2], ignore_index=True)
    df_cdi['CDI'] = df_cdi['CDI']/100

    inicio = pd.to_datetime(inicio)
    fim = pd.to_datetime(fim)

    df_cdi = df_cdi[(df_cdi['Date'] >= inicio) & (df_cdi['Date'] <= fim)]
    
    acumulado=1
    for i in range(len(df_cdi)):
        acumulado=acumulado*(1+df_cdi.iloc[i,1])

    return round(100*(acumulado-1),2)



def main():
    st.write('# Painel de informações do mercado imobiliário na cidade do Rio de Janeiro')

    st.sidebar.title('Menu de navegação')
    pagina = st.sidebar.selectbox('Esolha a página',['Início','Evolução de transações em bairros', 'Comparação de indicadores'])
    
    if pagina == 'Início':
        col1,col2 = st.columns(2)
        con1=col1.container(key='inicio_texto')
        con2=col2.container(key='inicio_imagem')

        with con1:
            st.write('### Este painel exibe informações referentes a transações reais de imóveis na cidade do Rio de Janeiro, ocorridas entre os anos de 2011 e 2025')
            st.write('### Os registros analisados provêm de dados públicos que podem ser encontrados no portal da prefeitura do Rio de Janeiro (Data.Rio), além de dados econômicos do IBGE e do BCB.')
            st.write('### \n')
            st.write('\n ')
            st.markdown('### **As seguintes consultas podem ser realizadas:**')
            st.markdown('###   **1. Evolução de transações em bairros**')
            st.write('### Avalia o perfil das transações realizadas ao longo do tempo em um determinado bairro, considerando uma tipologia escolhida.')
            st.write('### É possível analisar estes dados selecionando dois bairros ou duas tipologias ao mesmo  tempo')
            st.write('\n')
            st.markdown('###  **2. Comparação de indicadores**')
            st.write('### Exibe as variações nas negociações de imóveis para um dado logradouro, bem como compara as variações observadas nas transações realizadas com o valor de IPCA para um dado período.')
            st.write('### Esta comparação fornece um indicativo de quais bairros proporcionaram um investimento em imóveis que pode ter oferecido ganho real aos compradores no período avaliado')

        with con2:
            st.image('CentroRJ.jpg')

    if pagina == 'Evolução de transações em bairros':

        st.write('### Registros de negociações de imóveis ocorridas entre 2011 e 2025 no município')
        st.write('### Fonte dos dados - Portal Data.Rio')

        col1,col2 = st.columns(2)
        con1 = col1.container(key='comp_1')
        con2 = col2.container(key='comp_2')
        
        def exibicao_bairro(i):
            st.markdown("""
                        <style>
                        /* texto na 'selectbox' */
                        .stSelectbox > div[data-baseweb="select"] > div {
                            font-size: 20px; 
                        }
                        /* texto no menu */
                        div[data-baseweb="popover"] div[role="listbox"] div p {
                            font-size: 18px !important;
                        }
                        /* texto do rótulo da 'selectbox */
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
                    fig = px.scatter(x=data_metro_quadrado['ano'],y=data_metro_quadrado['media_metro_quadrado_med'],
                            title=f'Evolução do valor do metro quadro em imóveis do bairro: {bairro_escolhido} <br> Tipologia: {tipologia_escolhida}',
                        )
                    fig.update_layout(
                        title_x=0.5,           # Define a posição X como 0.5 (centro)
                        title_xanchor='center', # Garante que o centro do título fique no ponto 0.5
                        title_font_size=18,
                        yaxis=dict(title='Mediana dos valores de metro quadrado por transação (R$/m²)'),
                        xaxis=dict(title='Ano')


                    )
                    fig.update_traces(marker=dict(size=16))
                    st.plotly_chart(fig)

                    data_metro_quadrado['variacao_anual'] = '-'
                    for i in range(1,len(data_metro_quadrado)):
                        data_metro_quadrado.iloc[i,5] = round(100*((data_metro_quadrado.iloc[i,3] - data_metro_quadrado.iloc[i-1,3])/data_metro_quadrado.iloc[i-1,3]),2)

                    data_metro_quadrado = data_metro_quadrado.rename(columns={'ano': 'Ano', 
                                                                        'media_metro_quadrado_max':'Maior valor de m² (R$/m²)', 
                                                                        'media_metro_quadrado_min':'Menor valor de m² (R$/m²)', 
                                                                        'media_metro_quadrado_med':'Mediana dos valores de m² (R$/m²)',
                                                                        'transacoes':'Transações realizadas',
                                                                        'variacao_anual':'Variação anual (%)'
                                                                        })

                    ultima_obs = len(data_metro_quadrado)-1
                    variacao = round(100*((data_metro_quadrado.iloc[ultima_obs,3] - data_metro_quadrado.iloc[0,3])/data_metro_quadrado.iloc[0,3]),2)
                    st.write(f'### Variação total observada no período para imóveis no bairro para a tipologia escolhida: {variacao}%')
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
        
        col3,col4 = st.columns(2)
        con3 = col3.container(key='comp_3')
        con4 = col4.container(key='comp_4')

        with con3:

            inicio = st.date_input('### Início da série', min_value=datetime.date(1900, 1, 1), max_value=None)
            fim = st.date_input('### Fim da série', min_value=datetime.date(1900, 1, 1), max_value=None)

            try:
                inflacao_acumulada = ipca_acumulado(inicio,fim)
                st.write(f'### IPCA acumulado entre {inicio} e {fim}: {round(100*(inflacao_acumulada),2)}%')
                cdi_acumulado_result = cdi_acumulado(inicio,fim)
                st.write(f'### CDI acumulado entre {inicio} e {fim}: {cdi_acumulado_result}%')
            except KeyError:
                st.write('### Selecione um intervalo de datas para verificar indicadores financeiros. ')
                st.write('### Caso nenhum valor de IPCA ou CDI acumulado seja exibido, não há dados históricos para este período')

            st.write(' ')
            st.write('### Selecione abaixo um bairro e endereço para acompanhar a evolução de valores de transações neste local')
            bairro_lgd = st.selectbox('Escolha o bairro',sorted(data['bairro'].unique()), index=None, placeholder='Bairros', key=f'bairro_lgd')
            lgd_bairro_escolhido = data[data['bairro'] == bairro_lgd]
            lgd_escolhido = st.selectbox('Escolha o logradouro',sorted(lgd_bairro_escolhido['logradouro'].unique()), index=None, placeholder='Logradouros', key=f'lgd_escolhido')
            tipologia_lgd = st.selectbox('Escolha a tipologia',sorted(lgd_bairro_escolhido['principais_tipologias'].unique()), index=None, placeholder='Tipologia', key=f'tipo_escolhida')

            var_logradouro_df = var_logradouro(lgd_escolhido, tipologia_lgd,inicio,fim)
            var_logradouro_df = var_logradouro_df.rename(columns={'ano': 'Ano', 
                                                                        'media_metro_quadrado_max':'Maior valor de m² (R$/m²)', 
                                                                        'media_metro_quadrado_min':'Menor valor de m² (R$/m²)', 
                                                                        'media_metro_quadrado_med':'Mediana dos valores de m² (R$/m²)',
                                                                        'transacoes':'Transações realizadas'
                                                                        })
            if (bairro_lgd is not None) and (lgd_escolhido is not None) and (tipologia_lgd is not None):
                if var_logradouro_df.empty:
                    st.write('### Se nenhum dado é exibido, nenhuma transação atende os critérios da busca realizada')
                else:
                    st.dataframe(var_logradouro_df, hide_index=True)

            else:
                pass

        with con4:
            tipologia_var = st.selectbox('Escolha a tipologia',sorted(data['principais_tipologias'].unique()), index=None, placeholder='Tipologia', key=f'tipo_var')

            try:
                if tipologia_var and inicio and fim:
                    maiores_var = ranking_bairro(
                    tipologia_var,
                    inicio,
                    fim
                )
                st.dataframe(maiores_var, hide_index=True)
                st.write('### Analise criticamente os dados acima : bairros com variações nos valores de transações muito altas entre diferentes anos podem indicar uma região com poucas negociações, e não uma tendência real de valorização.')
            except:
                st.write('### Selecione uma opção de tipologia acima para verificar quais foram os bairros com maior variação nos valores do metro quadrado em negociações durante o período escolhido')
                

if __name__ == "__main__":
    main()