import streamlit as st
import pandas as pd
import numpy as np

# Carrega os dados
dados = pd.read_csv('data_export_20241007.csv', sep = ',')
max = '2021-06-01'
dados = dados[dados['dtBase'] == max]

# Função MelhoresEscolhas
def MelhoresEscolhas(data, positivo, negativo, empresas):
    df = data.drop(columns=[empresas])
    
    # Seleciona as colunas positivas e negativas
    positivos = df[list(positivo)]
    negativos = df[list(negativo)]

    def ahp_positivos(tabela):
        table = []
        for i in tabela.columns:
            total = sum(tabela[i])  # Calcula o total da coluna
            a = np.where(total == 0, 0, tabela[i] / total)  # Normalização da coluna
            table.append(a)
        table = pd.DataFrame(table).T
        table.columns = tabela.columns
        return table

    positivos = ahp_positivos(positivos)

    def numeros_negativos(tabela):
        table = []
        for i in tabela.columns:
            a = np.where(tabela[i] == 0, 0, 1 / tabela[i])  # Inversão dos valores
            table.append(a)
        table = pd.DataFrame(table).T
        tab_final = []
        for i in table.columns:
            total = table[i].sum()
            b = np.where(total == 0, 0, table[i] / total)  # Normalização pelo total da coluna
            tab_final.append(b)
        tab_final = pd.DataFrame(tab_final).T
        tab_final.columns = tabela.columns
        return tab_final

    negativos = numeros_negativos(negativos)
    tabela_ahp = pd.concat([positivos, negativos], axis=1)

    medias = pd.DataFrame(tabela_ahp.mean(), columns=['media'])
    desvio = pd.DataFrame(tabela_ahp.std(), columns=['desvio'])
    fator_ahp = pd.concat([medias, desvio], axis=1)
    fator_ahp['desvio'] = fator_ahp['desvio'].fillna(np.mean(fator_ahp['desvio']))
    fator_ahp['desvio/media'] = fator_ahp['desvio'] / fator_ahp['media']
    fator_ahp['Fator'] = fator_ahp['desvio/media'] / sum(fator_ahp['desvio/media'])

    fator = pd.DataFrame(fator_ahp['Fator']).T
    colunas_para_calculo = fator.columns

    def matriz_de_decisao(tabela, fator):
        table = []
        for i in colunas_para_calculo:
            a = tabela[i] * fator[i][0]
            table.append(a)
        table = pd.DataFrame(table).T
        return table

    resultado_ahp = matriz_de_decisao(tabela_ahp, fator)
    soma = resultado_ahp.sum(axis=1)
    soma = pd.DataFrame(soma, columns=['Resultado'])

    # Redefinir o índice após a soma para garantir que ele não se desalinhe
    soma = soma.reset_index(drop=True)

    # Mesclar com a coluna de empresas, redefinindo o índice
    melhores_escolhas = pd.concat([soma, data[[empresas]].reset_index(drop=True)], axis=1)

    # Ordenar os resultados pelo valor do resultado e redefinir o índice novamente
    melhores_escolhas = melhores_escolhas.sort_values(by='Resultado', ascending=False).reset_index(drop=True)

    # Renomeia a coluna de empresas, se necessário
    melhores_escolhas.rename(columns={empresas: 'Empresa'}, inplace=True)

    return melhores_escolhas, fator.T

# Aplicação Streamlit
st.title('Seleção de Colunas Positivas e Negativas para Análise AHP')

# Lista de colunas disponíveis
colunas_disponiveis = list(dados.columns)

# Adicionar os filtros na barra lateral (sidebar)
st.sidebar.header('Filtros')

# Selecionar a coluna de empresas
coluna_empresas = 'strNomeAdministradora'  # Coluna fixa de empresas

# Selecionar tipo adm
tipo_administradora = st.sidebar.selectbox('Selecione o Tipo de Administradora:', dados['NomeTipoAdministradora'].unique())

# Selecionar tipo segmento
segmento = st.sidebar.selectbox('Selecione o Segmento:', dados['strNomeSegmento'].unique())

# Aplicar os dois filtros principais de tipo administradora e segmento
dados_filtrados = dados[
    (dados['NomeTipoAdministradora'] == tipo_administradora) &
    (dados['strNomeSegmento'] == segmento)
]

# Selecionar colunas positivas
colunas_positivas = st.sidebar.multiselect('Selecione as colunas positivas:', colunas_disponiveis)

# Selecionar colunas negativas
colunas_negativas = st.sidebar.multiselect('Selecione as colunas negativas:', colunas_disponiveis)

# Número de filtros a serem aplicados
num_filtros = st.sidebar.number_input('Quantos filtros deseja aplicar?', min_value=1, max_value=10, step=1)

filtros = []
# Criar a interface para múltiplos filtros
for i in range(int(num_filtros)):
    st.sidebar.write(f"Filtro {i+1}")
    coluna_filtro = st.sidebar.selectbox(f'Selecione a coluna para o Filtro {i+1}:', colunas_disponiveis, key=f"coluna_filtro_{i}")
    
    # Selecionar o tipo de condição
    condicao = st.sidebar.selectbox(f'Selecione a condição para o Filtro {i+1}:', ['Igual a', 'Maior ou igual a', 'Menor ou igual a'], key=f"condicao_{i}")
    
    # Selecionar o valor do filtro
    valor_filtro = st.sidebar.text_input(f'Digite o valor para o Filtro {i+1}:', key=f"valor_filtro_{i}")
    
    filtros.append((coluna_filtro, condicao, valor_filtro))

# Aplicar os filtros selecionados
for coluna_filtro, condicao, valor_filtro in filtros:
    if valor_filtro:
        try:
            valor_filtro = float(valor_filtro)
        except ValueError:
            pass  # Mantém o valor como string se não for conversível para float

        if condicao == 'Igual a':
            dados_filtrados = dados_filtrados[dados_filtrados[coluna_filtro] == valor_filtro]
        elif condicao == 'Maior ou igual a':
            dados_filtrados = dados_filtrados[dados_filtrados[coluna_filtro] >= valor_filtro]
        elif condicao == 'Menor ou igual a':
            dados_filtrados = dados_filtrados[dados_filtrados[coluna_filtro] <= valor_filtro]

# Exibir os dados filtrados
st.write("Dados após aplicação dos filtros:")
st.dataframe(dados_filtrados)

# Verifica se o usuário selecionou colunas suficientes
if len(colunas_positivas) > 0 and len(colunas_negativas) > 0 and coluna_empresas:
    st.write("Executando a análise AHP com os dados filtrados...")
    resultado, fator = MelhoresEscolhas(dados_filtrados, colunas_positivas, colunas_negativas, coluna_empresas)

    # Exibe o resultado
    st.write("Melhores escolhas baseadas na análise AHP:")
    st.dataframe(resultado)

    # Exibe o fator calculado
    st.write("Fatores calculados:")
    st.dataframe(fator)
else:
    st.write("Por favor, selecione pelo menos uma coluna positiva, uma negativa e a coluna de empresas.")