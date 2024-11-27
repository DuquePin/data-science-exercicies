# Importando bibliotecas
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

import streamlit as st


@st.cache_data
def load_data(uploaded_file):
    return pd.read_csv(uploaded_file, sep=',')


def main():
    global df
    st.set_page_config(page_title='RFV Table App',
                       layout='wide',
                       initial_sidebar_state='expanded'
                       )

    st.write('# RFV Table App')
    st.markdown('---')

    st.write('## Propósito')
    st.write('Este é um aplicativo útil para criar tabelas RFV com base em novos dados inseridos.')

    st.sidebar.write('## Upload a file')
    uploaded_file = st.sidebar.file_uploader('Input data:', type=['csv'])

    if uploaded_file is not None:
        try:
            df = load_data(uploaded_file)
            st.write('Visualização de dados:')
            st.dataframe(df)
        except ValueError as e:
            st.error(f'Error: {e}')
        finally:
            df['DiaCompra'] = pd.to_datetime(df['DiaCompra'])

            rec = lambda rec: df['DiaCompra'].max() - rec.max()

            df_RFV = (df
                      .groupby(by='ID_cliente')
                      .agg({'DiaCompra': rec, 'CodigoCompra': 'count', 'ValorTotal': 'sum'})
                      .rename(columns={'DiaCompra': 'Recência', 'CodigoCompra': 'Frequência', 'ValorTotal': 'Valor'}))

            st.write('# Tabela RFV')
            st.write(df_RFV.head(5))

            df_RFV['RecênciaScore'] = ''

            df_RFV.loc[df_RFV['Recência'] <= df_RFV['Recência'].quantile(.25), 'RecênciaScore'] = 'A'
            df_RFV.loc[
                (df_RFV['Recência'] > df_RFV['Recência'].quantile(0.25)) &
                (df_RFV['Recência'] <= df_RFV['Recência'].quantile(0.50)),
                'RecênciaScore'
            ] = 'B'
            df_RFV.loc[
                (df_RFV['Recência'] > df_RFV['Recência'].quantile(0.50)) &
                (df_RFV['Recência'] <= df_RFV['Recência'].quantile(0.75)),
                'RecênciaScore'
            ] = 'C'
            df_RFV.loc[df_RFV['Recência'] > df_RFV['Recência'].quantile(.75), 'RecênciaScore'] = 'D'

            st.write('## Classificação de Cliente com Base na Recência')
            st.write(df_RFV[['Recência', 'RecênciaScore']])

            df_RFV['FrequênciaScore'] = ''

            df_RFV.loc[df_RFV['Frequência'] <= df_RFV['Frequência'].quantile(.25), 'FrequênciaScore'] = 'D'
            df_RFV.loc[
                (df_RFV['Frequência'] > df_RFV['Frequência'].quantile(0.25)) &
                (df_RFV['Frequência'] <= df_RFV['Frequência'].quantile(0.50)),
                'FrequênciaScore'
            ] = 'C'
            df_RFV.loc[
                (df_RFV['Frequência'] > df_RFV['Frequência'].quantile(0.50)) &
                (df_RFV['Frequência'] <= df_RFV['Frequência'].quantile(0.75)),
                'FrequênciaScore'
            ] = 'B'
            df_RFV.loc[df_RFV['Frequência'] > df_RFV['Frequência'].quantile(.75), 'FrequênciaScore'] = 'A'

            st.write('## Classificação de Cliente com Base na Frequência')
            st.write(df_RFV[['Frequência', 'FrequênciaScore']])

            df_RFV['ValorScore'] = ''

            df_RFV.loc[df_RFV['Valor'] <= df_RFV['Valor'].quantile(.25), 'ValorScore'] = 'D'
            df_RFV.loc[
                (df_RFV['Valor'] > df_RFV['Valor'].quantile(0.25)) &
                (df_RFV['Valor'] <= df_RFV['Valor'].quantile(0.50)),
                'ValorScore'
            ] = 'C'
            df_RFV.loc[
                (df_RFV['Valor'] > df_RFV['Valor'].quantile(0.50)) &
                (df_RFV['Valor'] <= df_RFV['Valor'].quantile(0.75)),
                'ValorScore'
            ] = 'B'
            df_RFV.loc[df_RFV['Valor'] > df_RFV['Valor'].quantile(.75), 'ValorScore'] = 'A'

            st.write('## Classificação de Cliente com Base no Valor')
            st.write(df_RFV[['Valor', 'ValorScore']])

            df_RFV['RFV'] = df_RFV['RecênciaScore'] + df_RFV['FrequênciaScore'] + df_RFV['ValorScore']

            # Segmentando clientes em grupos
            df_RFV['GrupoCliente'] = ''
            df_RFV.loc[df_RFV['RFV'].str.contains('A'), 'GrupoCliente'] = 'A'
            df_RFV.loc[df_RFV['RFV'].str.contains('B'), 'GrupoCliente'] = 'B'
            df_RFV.loc[df_RFV['RFV'].str.contains('C'), 'GrupoCliente'] = 'C'
            df_RFV.loc[df_RFV['RFV'].str.contains('D'), 'GrupoCliente'] = 'D'

            # Visualizando distribuição percentual dos grupos na base de dados
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.barplot(data=((df_RFV['GrupoCliente'].value_counts() / df_RFV.shape[0]) * 100), palette='viridis', ax=ax)
            ax.set_title('Distribuição de Grupos de Clientes', fontsize=16)
            ax.set_xlabel('Grupo Cliente', fontsize=12)
            ax.set_ylabel('Contagem', fontsize=12)

            # Renderizar o gráfico no Streamlit
            st.write('---')
            st.pyplot(fig)

            # Mapeando ações de marketing de acordo com o perfil do cliente
            dict_acoes = {
                'AAA':
                    'Enviar cupons de desconto, Pedir para indicar nosso produto pra algum amigo, Ao lançar um novo produto enviar amostras grátis pra esses.',
                'DDD':
                    'Churn! clientes que gastaram bem pouco e fizeram poucas compras, fazer nada',
                'DAA':
                    'Churn! clientes que gastaram bastante e fizeram muitas compras, enviar cupons de desconto para tentar recuperar',
                'CAA':
                    'Churn! clientes que gastaram bastante e fizeram muitas compras, enviar cupons de desconto para tentar recuperar'
            }

            df_RFV['Ação de Marketing'] = df_RFV['RFV'].map(dict_acoes)

            st.write('## Tabela RFV final')
            st.write(df_RFV.head(5))


if __name__ == '__main__':
    main()
