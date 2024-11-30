import streamlit as st
import os
import calendar
import datetime
from mysql.connector import Error
from services.database import conexao, cursor
from models.ordem_de_servico import Ordem_Servico
from models.fechamento import Fechamento
from .cliente_controller import consulta_cliente_por_id

'''Este controller agrega todas as funções relacionadas ao CRUD da tabela fechamento'''

'''Criar Registros'''
def criar_novo_fechamento(novo_fechamento):
    '''
    Cria um novo fechamento no banco de dados

    :param novo_fechamento: Objeto, instância da model Fechamento com os dados passados
    :return: id do novo fechamento para registro nas ordens de serviço
    '''

    try:
        
        cursor.execute('''INSERT INTO fechamento(cliente_id, data_fechamento) VALUES (%s, %s)''',(novo_fechamento.cliente, novo_fechamento.data))
        conexao.commit()

        # nome_cliente = consulta_cliente_por_id(novo_fechamento.cliente_id)

        cursor.execute('''SELECT MAX(id) FROM fechamento''')
        resultado = cursor.fetchone()
        maior_id = resultado[0] if resultado[0] is not None else 0
        return maior_id
    
    except Error as e:
        st.error(f"Não foi possível cadastrar um novo fechamento para o cliente. Erro: {e}")

def add_num_nf_fechamento(fechamento_id, num_nf):
    '''
    Altera o registro do fechameto fornecido, vinculando a ele a nota fiscal emitida com seus dados e já cadastrada no sistema

    :param fechamento_id: Integer, id que representa o fechamento selecionado no banco de dados
    :param num_nf: Integer, id que representa a nota fiscal recém cadastrada no banco de dados
    :return: Boolean, True confirmando o sucesso da operação e False para o fracasso junto a uma mensagem de erro
    '''
    try:
        cursor.execute('''UPDATE fechamento SET numero_nota = %s WHERE id = %s''', (num_nf, fechamento_id))
        conexao.commit()
        return True
    except Error as e:
        st.error(f"Não foi possível adicionar a nota fiscal {num_nf} ao fechamento {fechamento_id}. Erro {e}")
        return False
        
'''Consultar Registros'''

def consulta_valor_total_fechamento(fechamento_id):
    '''
    Soma os valor de todas as ordens de serviço que forem registradas com o fechamento fornecido

    :param fechamento_id: Número que corresponde a um fechamento cadastrado na tabela fechamento
    :return: Float, retorna o valor total da soma das ordens de serviço que pertencem ao fechamento fornecido
    '''
    try:
        cursor.execute('''SELECT SUM(os.valor) AS valor_total_fechamento
                        FROM ordem_de_servico os WHERE os.fechamento_id = %s;''',(fechamento_id,))

        resultado = cursor.fetchone()
        return resultado[0]
    
    except Error as e:
        st.error(f"Não foi possível calcular o valor dos fechamentos. Erro {e}")

def consulta_menor_e_maior_valor_fechamento():
    '''Consulta os valores mínimos e máximos de fechamentos registrados e devolve para o componente slider
    como parâmetro do range mínimo e máximo que ele pode alcançar
    :return: Integer, 2 valores representando, respectivamente o mínimo e o máximo dos valores dos fechamentos no sistema'''
    try:
        cursor.execute('''
            SELECT f.id AS fechamento_id, SUM(os.valor) AS valor_total_fechamento
            FROM fechamento f JOIN ordem_de_servico os ON os.fechamento_id = f.id
            GROUP BY f.id;
        ''')
        resultado = cursor.fetchall()
        if resultado:
            maior_valor = max(valor[1] for valor in list(resultado))
            menor_valor = min(valor[1] for valor in list(resultado))
            return int(menor_valor), int(maior_valor)
        else:
            return 0,1
    except Error as e:
        st.error(f"Não foi possível encontrar o maior valor de fechamento. Erro {e}")

def consulta_fechamento(cliente=None, data=None, valor=None):
    '''Consulta os fechamentos registrados de acordo com os parâmetros recebidos.
    Qualquer parâmetro pode faltar que a pesquisa será realizada sem eles. Caso 
    não receba nenhum retorna todos os valores.
    
    :param cliente: Objeto, instância de Cliente
    :param data: objeto datetime, 1 ou 2 datas para determinar o range da busca
    :param valor: inteiro, 2 valores para determinar o range da busca
    :return: resultado da consulta baseado nos filtros recebidos'''

    try:
        '''query principal que será acrescida dos parametros e condicoes recebidas'''
        query = '''
        SELECT f.id, c.nome_fantasia, f.data_fechamento, SUM(os.valor) AS valor_total
        FROM fechamento f
        JOIN cliente c ON f.cliente_id = c.id
        JOIN ordem_de_servico os ON os.fechamento_id = f.id
        WHERE 1=1
        '''
        
        parametros = []

        if cliente:
            query += 'AND f.cliente_id = %s'
            parametros.append(cliente.id)
        
        if data:
            data_inicio, data_fim = data
            query += ' AND f.data_fechamento BETWEEN %s AND %s '
            parametros.append(data_inicio)
            parametros.append(data_fim)
        
        query += " GROUP BY f.id, c.nome_fantasia, f.data_fechamento"

        if valor:
            menor_valor, maior_valor = valor
            query = f'''
            SELECT fechamento_agrupado.* FROM ({query}) AS fechamento_agrupado 
            WHERE valor_total BETWEEN %s AND %s'''
            parametros.append(menor_valor)
            parametros.append(maior_valor)
        
        cursor.execute(query, tuple(parametros))
        resultado = cursor.fetchall()
        return resultado
    
    except Error as e:
        st.error(f"Não foi possível realizar a consulta sobre os fechamentos. Erro {e}")

def consulta_fechamento_por_id(id):
    '''
    Consulta o banco de dados em busca dos dados do fechamento usando o id como parâmetro
    
    :param id: Integer, número que representa um fechamento no banco de dados
    :return: Instancia de Fechamento, retorna uma instancia de Fechamento com base no id fornecido
    '''

    try:
        cursor.execute('''SELECT f.id, f.cliente_id, f.data_fechamento FROM fechamento f
                       WHERE f.id = %s ''', (id,))
        resultado = cursor.fetchone()
        fechamento = Fechamento(resultado[1], resultado[2], resultado[0])
        return fechamento
    
    except Error as e:
        st.error(f"Não foi possível encontrar o fechamento solicitado. Erro:{e}")

def consulta_fechamentos_sem_nota():
    '''
    Consulta todos os fechamentos que não têm o campo nota fiscal preenchido

    :return: resultado da consulta
    '''

    try:
        cursor.execute('''SELECT f.id, c.nome_fantasia, f.data_fechamento, SUM(os.valor) FROM fechamento f
                       JOIN cliente c ON f.cliente_id = c.id
                       JOIN ordem_de_servico os ON os.fechamento_id = f.id
                       WHERE f.numero_nota IS NULL
                       GROUP BY f.id, c.nome_fantasia, f.data_fechamento''')
        resultado = cursor.fetchall()
        return resultado
    
    except Error as e:
        st.error(f"Não foi possível encontrar os fechamentos disponíveis para faturamento. Erro {e}")

def consulta_qtde_os_no_fechamento(fechamento_id):
    '''Consulta no banco de dados todas as ordens de serviços que estão incluídas no fechamento fornecido e retorna a qtde
    
    :param fechamento_id: Número que corresponde a um fechamento cadastrado na tabela fechamento
    :return: Integer, contagem total de ordens de serviço encontradas'''

    try:
        cursor.execute('''SELECT COUNT(*) FROM ordem_de_servico o WHERE o.fechamento_id = %s''', (fechamento_id,))
        resultado = cursor.fetchone()
        return resultado[0]
    
    except Error as e:
        st.error(f"Não foi possível calcular a quantidade de ordens de serviço registradas neste faturamento. Erro {e}")

def consulta_data_mais_antiga_e_mais_recente(fechamento_id):
    '''Consulta no banco de dados quais são as datas mais antiga e mais nova 
    registradas para o fechamento fornecido
    
    :param fechamento_id: Número que corresponde a um fechamento cadastrado na tabela fechamento
    :return: Object Datetime, retorna a data mais antiga seguida da data mais recente.'''

    try:
        cursor.execute('''SELECT MIN(o.data) AS mais_antiga, MAX(o.data) AS mais_recente FROM 
                       ordem_de_servico o WHERE o.fechamento_id = %s''', (fechamento_id,))
        resultado = cursor.fetchone()
        data_mais_antiga = resultado[0]
        data_mais_recente = resultado[1]

        return data_mais_antiga, data_mais_recente

    except Error as e:
        st.error(f"Não foi possível encontrar as datas mais antiga e mais nova do fechamento fornecido. Erro {e}")

def consulta_se_fechamento_possui_nf(fechamento_id):
    '''Consulta na base de dados se o fechamento fornecido possui uma nota fiscal associada
    
    :param fechamento_id: Integer, Número que corresponde a um fechamento cadastrado na tabela fechamento
    :return: Boolean, verdadeiro caso tenha uma nota fiscal ou falso caso não tenha'''

    try:
        cursor.execute('''SELECT COUNT(*) FROM fechamento WHERE id=%s AND numero_nota IS NOT NULL''',(fechamento_id,))
        resultado = cursor.fetchone()
        return resultado[0] > 0
    
    except Error as e:
        st.error(f"Não foi possível verificar se o fechamento {fechamento_id} possui nota fiscal associada. Erro {e}")
        return None

def consulta_nf_por_fechamento(fechamento_id):
    '''Consulta se o fechamento fornecido possui uma nota fiscal associada
    
    :param fechamento_id:Integer, Número que corresponde a um fechamento cadastrado na tabela fechamento
    :return: Integer, número da nota fiscal encontrada, caso não haja nenhuma retorna 0'''

    try:
        cursor.execute('''SELECT numero_nota FROM fechamento WHERE id=%s''', (fechamento_id,))
        resultado = cursor.fetchone()
        return resultado[0] if resultado and resultado[0] is not None else 0
    
    except Error as e:
        st.error(f"Não foi possível verificar se o fechamento {fechamento_id} possui uma nota fiscal associada. Erro {e}")

def consulta_fechamento_por_nf(num_nf):
    '''
    Consulta o fechamento associado a uma nota fiscal registrada
    
    :param num_nf: Integer, Numero que identifica a nota fiscal no banco de dados
    :return: Objeto, instância do fechamento encontrado ou mensagem de erro
    '''
    try:
        cursor.execute('''SELECT * FROM fechamento WHERE numero_nota = %s''', (num_nf,))
        resultado = cursor.fetchone()
        return Fechamento(resultado[1], resultado[2], resultado[0], resultado[3])

    except Error as e:
        st.error(f"Não foi possível encontrar o fechamento associado á nota {num_nf}. Erro {e}")