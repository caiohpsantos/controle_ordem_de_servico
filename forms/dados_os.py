import streamlit as st
import pandas as pd
import locale
import calendar
import datetime
import matplotlib.pyplot as plt
from controllers import os_controller

'''Define a localidade para o Brasil, podendo ser usado para definir a moeda e nome de dias, meses e dias da semana'''
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

def dados():
    rerun = st.button('Mostrar menus')
    if rerun:
        st.rerun()
    st.query_params.clear()
    resultados = os_controller.consultar_todas_os_retorna_qtde_e_soma_por_mes()
    col_qtde_os, col_valor_os = st.columns(2)
    with col_qtde_os:
        st.write(f"Lançamentos no mês")
        st.header(resultados[0])
    with col_valor_os:
        st.write("Total valores no mês")
        if resultados[1] == None:
            st.header("R$ 0,00")
        else:
            st.header(locale.currency(resultados[1],grouping=True))

    st.divider()
    col_top_clientes, col_recentes = st.columns(2)

    with col_top_clientes:
        consulta = os_controller.consultar_5_melhores_clientes_mes()
        clientes = []
        valores = []
        for cliente, valor in consulta:
            clientes.append(cliente)
            valores.append(valor)
        fig, ax = plt.subplots()
        ax.bar(clientes, valores)
        ax.set_xlabel("Clientes")
        ax.set_ylabel("Valor Total - R$")
        ax.set_title("Top 5 Clientes - Valores Acumulados")
        plt.xticks(rotation=45, ha='right')
        st.pyplot(fig)
        
        # pd.options.plotting.backend = 'plotly'
        # colunas = ['Cliente', "Valor Total"]
        # df_top_clientes = pd.DataFrame(os_controller.consultar_5_melhores_clientes_mes(), columns=colunas)
        # st.write("Top 5 clientes / soma dos valores no mês atual")
        # label_clientes = 
        # st.write(df_top_clientes.set_index('Cliente').plot(kind='pie', y='Valor Total', autopct='%1.1f%%', figsize=(8, 8), startangle=90))
        # st.write(df_top_clientes.plot(kind='hist', x='Cliente', y='Valor Total'))
        
    with col_recentes:
        colunas = ['Número O.S.', 'Cliente', 'Data', 'Valor', 'Descrição']
        df_recentes = pd.DataFrame(os_controller.consultar_todas_os(5), columns=colunas)
        df_recentes['Data'] = pd.to_datetime(df_recentes["Data"])
        df_recentes['Data'] = df_recentes['Data'].dt.strftime('%d/%m/%Y')
        df_recentes['Valor'] = df_recentes['Valor'].apply(lambda x: locale.currency(x, grouping=True))
        st.write("Últimas cinco O.S. cadastradas")
        st.write(df_recentes)