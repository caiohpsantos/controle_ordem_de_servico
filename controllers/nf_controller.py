import streamlit as st
import os
import calendar
import datetime
from mysql.connector import Error
from services.database import conexao, cursor
from services.media import DIR_MIDIA_NF
from models.nota_fiscal import Nota_Fiscal
from controllers.cliente_controller import consulta_cliente_por_id
from controllers.fechamento_controller import add_num_nf_fechamento

'Consultas relacionadas à notas fiscais'
def consulta_nf_por_id(num_nf):
    '''
    Consulta o banco de dados para recuperar os dados da nota fiscal solicitada.

    :param num_nf: Número da nota fiscal que será pesquisada
    return
    '''

    try:
        cursor.execute('''SELECT * FROM nota_fiscal nf  WHERE nf.numero = %s''', (num_nf,))
        resultado = cursor.fetchone()
        nf_encontrada = Nota_Fiscal(resultado[1], resultado[2], resultado[3], resultado[4], resultado[0])
        return nf_encontrada
    
    except Error as e:
        st.error(f"Não foi possível encontrar os dados da nota fiscal {num_nf}. Erro: {e} ")
        return False

def consulta_nf_maior_e_menor_valor():
    '''
    Consulta no banco de dados e maior e o menor valor dentre as notas fiscais cadastradas
    :return: Integer, 2 valores inteiros
    '''
    try:
        cursor.execute('''SELECT MIN(valor) AS menor_valor, MAX(valor) AS maior_valor FROM nota_fiscal''')
        resultado = cursor.fetchone()
        maior_valor = int(float(resultado[1])) if resultado[1] is not None else 1
        menor_valor = int(float(resultado[0])) if resultado[0] is not None else 0
        return menor_valor, maior_valor

    except Error as e:
        st.error(f"Não foi possível extrair o menor e o maior valor dentre as notas fiscais cadastradas. Erro{e}")
        return False

def consulta_nf(cliente=None, data=None, valor=None, numero=None):
    '''Consulta as notas fiscais de acordo com os parâmetros recebidos.
    Qualquer parâmetro pode faltar que a pesquisa será realizada sem eles. Caso 
    não receba nenhum, retorna todos os valores.
    
    :param cliente: Objeto, instância de Cliente
    :param data: objeto datetime, 1 ou 2 datas para determinar o range da busca
    :param valor: tuple, 2 valores para determinar o range da busca
    :param numero: inteiro, número da nota fiscal
    :return: resultado da consulta baseado nos filtros recebidos'''

    try:
        # Query base sem filtros adicionais
        query = '''
        SELECT nf.numero, nf.data_emissao, nf.valor, c.nome_fantasia AS nome_cliente
        FROM nota_fiscal nf
        JOIN fechamento f ON nf.numero = f.numero_nota
        JOIN cliente c ON f.cliente_id = c.id
        WHERE 1 = 1
        '''

        parametros = []

        # Filtro por número da nota fiscal
        if numero < 0:
            query += ' AND nf.numero = %s'
            parametros.append(numero)
        
        # Filtro por cliente (nome do cliente)
        if cliente:
            query += ' AND c.id = %s'
            parametros.append(cliente.id)

        # Filtro por data de emissão (faixa de datas)
        if data:
            data_inicio, data_fim = data
            query += ' AND nf.data_emissao BETWEEN %s AND %s'
            parametros.append(data_inicio)
            parametros.append(data_fim)

        # Filtro por valor da nota fiscal (faixa de valores)
        if valor:
            menor_valor, maior_valor = valor
            query += ' AND nf.valor BETWEEN %s AND %s'
            parametros.append(menor_valor)
            parametros.append(maior_valor)
        
        # Agrupamento dos resultados, pode ajustar conforme necessidade
        query += " GROUP BY nf.numero, nf.data_emissao, nf.valor, c.nome_fantasia"

        # Executa a consulta
        cursor.execute(query, tuple(parametros))
        resultado = cursor.fetchall()
        return resultado
    
    except Error as e:
        st.error(f"Não foi possível realizar a consulta sobre as notas fiscais. Erro: {e}")

def consulta_se_nf_ja_existe(num_nf):
    '''
    Consulta o banco de dados em busca de um registro de nota fiscal que tenha o mesmo número fornecido.
    
    :param num_nf: Número da nota fiscal que será pesquisada
    :return: True se o já existe um registro e False caso não exista
    '''

    try:
        cursor.execute('''SELECT COUNT(*) FROM nota_fiscal nf WHERE nf.numero = %s''', (num_nf,))
        resultado = cursor.fetchone()
        existe_nf = False if resultado[0] == 0 else True
        return existe_nf
    except Error as e:
        st.error(f"Não foi possível pesquisar se a nota fiscal número {num_nf} já está cadastrada.")

'Criar Registros'
def salvar_nf_na_pasta(num_nf, fechamento_id, cliente, arquivo_nf):
    '''
    Salva o pdf da nota fiscal recebida na pasta correspondente. Troca o nome do arquivo seguindo a ordem de:
    Letras NF, número da nf, letras FC, número do fechamento que a gerou e nome fantasia do cliente pagador.
    Exemplo: NF 752 - FC 1 - ELO AGRONEGOCIOS.pdf

    :param num_nf: Número da nota fiscal, retirado do próprio arquivo após validação.
    :param fechamento_id: Número do fechamento que gerou a nota fiscal.
    :param cliente: Número de cadastro do cliente relacionado ao fechamento e nota recebidos acima.
    :param arquivo_nf: Arquivo binário que será salvo na pasta correspondente.
    :return: Confirmação de gravação do arquivo com mensagem flutuante e caminho completo do arquivo na pasta gravada
    '''
    
    try:
        nome_arquivo = f"NF {num_nf} - FC {fechamento_id} - {cliente}.pdf"
        caminho_destino = os.path.join(DIR_MIDIA_NF, nome_arquivo)
        try:
            with open(caminho_destino, 'wb') as nf:
                nf.write(arquivo_nf.getbuffer() if hasattr(arquivo_nf, 'getbuffer') else arquivo_nf)
                st.toast(f"O arquivo da nota fiscal nº {num_nf} foi salvo com sucesso.")
                return caminho_destino, nome_arquivo
        except Error as e:
            st.error(f"Não foi possível salvar o arquivo da nota fiscal {num_nf}. Erro {e}")
    except:
        st.error(f"Não foi possível gravar o arquivo da nota fiscal nº {num_nf}.")

def salvar_nf_no_bd(nf_instanciada,fechamento_id):
    '''
    Grava o registro da nota fiscal no banco de dados

    :param nf_instanciada: Objeto, instancia da classe Nota Fiscal com os dados da nf para gravaçaõ no bd
    :return: Boolean, True ou False para registro finalizado e mensagem flutuante confirmando a transação ou mensagem de erro
    '''

    try:
        cursor.execute('''INSERT INTO nota_fiscal(numero, data_emissao, valor, arquivo, cod_verificacao)
                   VALUES (%s, %s, %s, %s, %s)''', (int(nf_instanciada.numero), nf_instanciada.data_emissao, nf_instanciada.valor,
                                                    nf_instanciada.arquivo, nf_instanciada.cod_verificacao))
        confirmacao = add_num_nf_fechamento(fechamento_id, nf_instanciada.numero)
        conexao.commit()
        if confirmacao:
            st.toast(f"A nota fiscal nº {nf_instanciada.numero} foi gravada com sucesso.")
            return True
    except Error as e:
        st.error(f"Não foi possível gravar a nota fiscal nº {nf_instanciada.numero}. Erro: {e}")
        return False