import streamlit as st
import os
import calendar
import datetime
from mysql.connector import Error
from services.database import conexao, cursor
from services.media import DIR_MIDIA_OS
from models.ordem_de_servico import Ordem_Servico, Midia_OS
from controllers.cliente_controller import consulta_cliente_por_id


'''Este controller agrega todas as funções relacionadas ao CRUD da tabela ordem_servico e midia_os'''

'''Funções de suporte para os controllers'''

def encontra_primeiro_e_ultimo_dia_mes():
    '''Esta função fornece o primeiro e ultimo dia do mês vigente para as funções que necessitam desses dados

    :return: Objeto Datetime, o primeiro e o ultimo dia do mẽs vigente
    '''
    dia_atual = datetime.date.today()
    primeiro_dia_mes = dia_atual.replace(day=1)
    ultimo_dia_mes = dia_atual.replace(day=calendar.monthrange(dia_atual.year, dia_atual.month)[-1])
    return primeiro_dia_mes, ultimo_dia_mes


'''Funções da tabela ordem_de_servico'''

'''Criar Registros'''
def criar_nova_ordem_servico(nova_os):

    '''
        Cria uma nova ordem de serviço com os dados fornecidos 

        :param nova_os: Objeto, model Ordem Serviço instânciada com os dados passados no formulário
        :return: confirmação da gravação dos dados
    '''
    try:
               
        cursor.execute(
            '''INSERT INTO ordem_de_servico(cliente_id, data, valor, descricao, solicitante, tel_solicitante) 
            VALUES (%s, %s, %s, %s, %s, %s)''', (nova_os.cliente_id, nova_os.data, nova_os.valor, nova_os.descricao,
                                                 nova_os.solicitante, nova_os.tel_solicitante,)
        )
        conexao.commit()
        cliente = consulta_cliente_por_id(nova_os.cliente_id)
        

        cursor.execute('''SELECT MAX(id) FROM ordem_de_servico ''')
        resultado = cursor.fetchone()
        maior_id = resultado[0] if resultado[0] is not None else 0
        st.toast(f"Ordem de serviço número {maior_id} registrada para o cliente {cliente}")
        return maior_id
    
    except Error as e:
        st.error(f"Ocorreu o seguinte erro ao cadastrar uma nova ordem de serviço: {e}")

'''Editar Registros'''
def editar_ordem_de_servico(os_editada):
    '''
    Edita uma ordem de serviço na tabela ordem_de_servico com os dados fornecidos

    :param os_editada: Objeto, instância da model Ordem_Servico com os dados editados de uma O.S.
    :return: confirmação da edição
    '''
    try:
        cursor.execute('''UPDATE ordem_de_servico 
                       SET cliente_id=%s, data=%s, valor=%s, descricao=%s, solicitante=%s, tel_solicitante=%s
                       WHERE id=%s''',(os_editada.cliente_id, os_editada.data, os_editada.valor, os_editada.descricao,
                                       os_editada.solicitante, os_editada.tel_solicitante, os_editada.id))
        conexao.commit()
        st.toast(f"A Ordem de Serviço {os_editada.id} do cliente {consulta_cliente_por_id(os_editada.cliente_id)} foi alterada com sucesso.")
        return True
        
    
    except Error as e:
        st.error(f"Não foi possível editar a ordem de serviço {os_editada.id} pois houve o seguinte erro:{e}")

def adiciona_fechamento_id(os_selecionadas, fechamento_id):
    '''
    Altera as ordens de serviço recebidas, acrescentando a elas o numero do fechamento a que elas pertencem.

    :param os_selecionadas: Lista, lista de ids das ordens de serviço que terão o fechamento_id adicionado no campo de mesmo nome
    :param fechamento_id: Integer, id do fechamento a que a ordem de serviço foi agregada
    :return: Mensagem confirmando a inserção do fechamento
    '''
    os_incluidas = []
    
    for os in os_selecionadas:
        cursor.execute('''UPDATE ordem_de_servico SET fechamento_id = %s WHERE id=%s''',(fechamento_id, os))
        os_incluidas.append(os)

    conexao.commit()
    st.toast(f"A gravação do fechamento número {fechamento_id} foi finalizada com sucesso. Um total de {len(os_incluidas)} ordens de serviço foram acrescentadas a este fechamento.")
    return os_incluidas

def retira_os_do_fechamento(os_selecionadas, id_fechamento):
    '''
    Retira a ordem de serviço do fechamento em que ela estiver cadastrada apagando o id do fechamento do campo correspondente.
    Caso o fechamento já tenha sido faturado(nota fiscal emitida), a operação não será feita.

    :param os_selecionadas: Lista, uma lista contendo os ids das ordens de serviço que devem ser editadas
    :return: Uma lista com todas as os em que a operação foi bem sucedida.
    '''
    os_incluidas = []
    
    for os in os_selecionadas:
        cursor.execute("UPDATE ordem_de_servico SET fechamento_id = NULL WHERE id=%s", (os,))
        os_incluidas.append(os)
    conexao.commit()
    st.toast(f'''A retirada das ordens de serviço do fechamento {id_fechamento} foi concluída com sucesso.
                Um total de {len(os_incluidas)} foram retiradas.''')
    return os_incluidas

def acrescenta_os_ao_fechamento(os_selecionadas, id_fechamento):
    '''
    Acrescenta as ordens de serviço selecionadas ao fechamento previamente criado.

    :param os_selecionadas: Lista, uma lista contendo os ids das ordens de serviço que devem ser editadas
    :param id_fehchamento: Integer, identificação do fechamento que será acrescentado na edição da o.s.
    :return: Uma lista com todas as o.s. em que a operação foi bem sucedida.
    '''
    os_incluidas = []
    try:
        for os in os_selecionadas:
            cursor.execute("UPDATE ordem_de_servico SET fechamento_id = %s WHERE id=%s", (id_fechamento, os))
            os_incluidas.append(os)
        conexao.commit()
        st.toast(f'''As ordens de serviço selecionadas foram acrescentadas ao fechamento {id_fechamento} com sucesso.
                 Um total de {len(os_incluidas)} ordens de serviço foram acrescentadas''')
        return os_incluidas
    except Error as e:
        st.error(f"Não foi possível acrescentar as ordens de serviço selecionada(s) ao fechamento {id_fechamento}. Erro {e}")

'''Consultar Registros'''

def consulta_os(cliente=None, data=None, valor=None):
    '''
    Consulta as ordens de serviço de acordo com os parâmetros repassados

    :param cliente: Objeto, instância de Cliente
    :param data: objeto datetime, 1 ou 2 datas para determinar o range da busca
    :param valor: inteiro, 2 valores para determinar o range da busca
    :return: resultado da consulta baseado nos filtros recebidos
    '''

    try:
        # Query principal que será acrescida dos parâmetros e condições recebidas
        query = '''
        SELECT os.id, c.nome_fantasia, os.data, os.valor, os.descricao
        FROM ordem_de_servico os
        JOIN cliente c ON os.cliente_id = c.id
        WHERE 1=1 AND os.fechamento_id IS NULL
        '''
        
        parametros = []

        if cliente:
            query += ' AND os.cliente_id = %s'
            parametros.append(cliente.id)
        
        if data:
            data_inicio, data_fim = data
            query += ' AND os.data BETWEEN %s AND %s'
            parametros.append(data_inicio)
            parametros.append(data_fim)
        
        if valor:
            menor_valor, maior_valor = valor
            query += ' AND os.valor BETWEEN %s AND %s'
            parametros.append(menor_valor)
            parametros.append(maior_valor)

        # Executa a consulta
        cursor.execute(query, tuple(parametros))
        resultado = cursor.fetchall()
        if resultado:
            return resultado
        
        else:
            st.warning('''Nenhuma ordem de serviço encontrada. Ou não há ordens de serviço cadastradas ou 
                       todas as ordens de serviço cadastradas já foram registradas em algum fechamento, impedindo sua edição.''')

    except Error as e:
        st.error(f"Não foi possível realizar a consulta sobre os fechamentos. Erro: {e}")

def consultar_os_por_id(id):
    '''
        Consulta o banco de dados em busca dos dados da ordem de serviço usando o id como parâmetro

        :param id: Integer, número que representa uma ordem de serviço específica no banco de dados
        :return: Instância da model Ordem_Servico que corresponde a id pesquisada ou None caso não haja nenhuma
    '''
    try:
        cursor.execute("SELECT * FROM ordem_de_servico WHERE id=%s", (id,))
        resultado = cursor.fetchone()
        
        if resultado:
            instancia_os = Ordem_Servico(resultado[1],resultado[2],resultado[3],resultado[4],resultado[5],
                                          resultado[6], resultado[0])
            return instancia_os
        else:
             return None
    except Error as e:
        st.error(f"Não foi possível consulta a ordem de serviço pelo id fornecido. Erro: {e}")

def consultar_todas_os(limite=None):
    '''
        Consulta na tabela ordem_de_servico todas as ordens de serviço cadastradas, 
        com a opção de limitar o número de resultados.
        
        :param limite: Integer opcional que define o número máximo de resultados a serem retornados.
        :return: Objeto do banco de dados com os dados solicitados (id da os, nome fantasia associado ao
        id do cliente, data da os, valor da os e descricao da os)
    '''
    try:
          consulta_sql = '''SELECT os.id, c.nome_fantasia, os.data, os.valor, os.descricao FROM ordem_de_servico os 
                          JOIN cliente c ON os.cliente_id = c.id  WHERE os.fechamento_id IS NULL
                         ORDER BY os.id DESC'''
          if limite:
              consulta_sql += f' LIMIT {limite}'
          
          cursor.execute(consulta_sql)
          resultado = cursor.fetchall()
          return resultado
    except Error as e:
          st.error(f"Não foi possível consultar todas as O.S. disponíveis. Erro:{e}")

def consultar_todas_os_retorna_qtde_e_soma_por_mes():
    '''
        Consulta todas as ordens de serviços lançadas no mês vigente

        :return: Integer, qtde de registros no banco de dados que tenham sido registrados durante o mês
        vigente e a soma do valor das ordens de serviços retornadadas
    '''
    primeiro_dia, ultimo_dia = encontra_primeiro_e_ultimo_dia_mes()
    try:
        cursor.execute('''SELECT 
                            COUNT(*) AS quantidade_os,
                            SUM(valor) AS valor_total_os
                            FROM ordem_de_servico
                            WHERE data BETWEEN %s AND %s;
                            ''', (primeiro_dia, ultimo_dia))
        resultado = cursor.fetchone()

        return resultado
    
    except Error as e:
         st.error(f"Não foi possível encontrar a quantidade de registros do último mês. Erro:{e}")

def consultar_5_melhores_clientes_mes():
    '''
        Soma os valores das ordens de serviço que cada cliente tem lançado dentro do mês vigente,
        ordenando pelo maior valor e retornando os 5 maiores

        :return: Objeto do banco de dados, retorna 5 registros do banco de dados contendo os dados:
        Nome Fantasia e soma do valor das ordens de serviço do mês (dentro ou fora de qualquer fechamento)
    '''
    primeiro_dia, ultimo_dia = encontra_primeiro_e_ultimo_dia_mes()
    try:
        cursor.execute('''
                        SELECT c.nome_fantasia, SUM(os.valor) AS valor_total
                        FROM ordem_de_servico os
                        JOIN cliente c ON os.cliente_id = c.id
                        WHERE os.data BETWEEN %s AND %s
                        GROUP BY c.nome_fantasia
                        ORDER BY valor_total DESC
                        LIMIT 5;
                        ''', (primeiro_dia, ultimo_dia))
        resultado = cursor.fetchall()
        return resultado 
    except Error as e:
        st.error(f"Não foi possível encontrar os 5 melhores clientes. Erro: {e}")

def consultar_todas_os_por_cliente_sem_fechamento(id_cliente):
    '''
        Consulta na tabela ordem_de_servico todas as ordens de servico cadastradas

        :param id_cliente: Integer, id do cliente selecionado usando o nome fantasia em um menu drop down
        :return: Objeto do banco de dados com os dados solicitados (id da os, nome fantasia associado ao
        id do cliente, data da os, valor da os e descricao da os) filtrados pelo id do cliente
    '''
    try:
          cursor.execute('''SELECT os.id, c.nome_fantasia, os.data, os.valor, os.descricao FROM ordem_de_servico os 
                         JOIN cliente c ON os.cliente_id = c.id WHERE c.id = %s AND os.fechamento_id IS NULL
                         ORDER BY os.id DESC''', (id_cliente,))
          resultado = cursor.fetchall()
          return resultado
    except Error as e:
          st.error(f"Não foi possível consultar todas as O.S. disponíveis para o cliente selecionado. Erro:{e}")

def consultar_os_por_cliente_sem_fechamento(id_cliente):
    '''
        Consulta na tabela ordem_de_servico todas as ordens de servico cadastradas que foram registradas
        para o cliente fornecido e que ainda não pertençam a um fechamento.

        :param id_cliente: Integer, id do cliente selecionado usando o nome fantasia em um menu drop down
        :return: Objeto do banco de dados com os dados solicitados (id da os, nome fantasia associado ao
        id do cliente, data da os, valor da os e descricao da os) filtrados pelo id do cliente e a falta de um valor
        na coluna fechamento_id
    '''
    try:
        cursor.execute('''SELECT os.id, os.data, os.valor, os.descricao, 
                            CASE 
                                WHEN COUNT(m.idmidia_os) > 0 THEN TRUE 
                                ELSE FALSE 
                            END AS has_midia
                        FROM ordem_de_servico os
                        LEFT JOIN midia_os m ON m.id_os = os.id
                        WHERE os.cliente_id = %s 
                        AND os.fechamento_id IS NULL
                        GROUP BY os.id, os.data, os.valor, os.descricao

                        ''',(id_cliente,))
        resultado = cursor.fetchall()
        return resultado
    except Error as e:
        st.error(f"Não foi possível consultas todas as O.S. do cliente selecionado e que ainda não pertençam a um fechamento. Erro:{e}")
        
def consultar_os_por_data(data):
    '''
        Consulta na tabela ordem_de_servico as ordens de servicos cadastradas que correspondam à data informada

        :param data: objeto do tipo date que será usado na consulta
        :return: Objeto do banco de dados com os dados solicitados (id da os, nome fantasia associado ao
        id do cliente, data da os, valor da os e descricao da os) filtrados pela data fornecida
    '''
    data_formatada = datetime.strftime(data,'%Y/%m/%d')
    try:
        cursor.execute("""
            SELECT os.id, c.nome_fantasia, os.data, os.valor, os.descricao 
            FROM ordem_de_servico os 
            JOIN cliente c ON os.cliente_id = c.id 
            WHERE os.data = %s ORDER BY os.id DESC
        """, (data_formatada,))
        resultado = cursor.fetchall()
        return resultado
    except Error as e:
        st.error(f"Não foi possível consultar todas as O.S. disponíveis para a data selecionada. Erro: {e}")

def consultar_os_por_cliente_e_por_data(id_cliente=None, data= None):
    '''
    Realiza a consulta na tabela ordem_de_servico podendo usar 2 parâmetros ao mesmo tempo: o id do cliente e a data
    Verifica se o parâmetro foi fornecido e concatena ele à query de consulta

    :param id_cliente: Integer, número da id do cliente recebido após consulta na tabela clientes pelo nome_fantasia. Pode ser nulo
    :param data: Date, data selecionada para pesquisa na tabela. Também pode ser nulo
    :return: Objeto do banco de dados, Resultado da consulta com os campos id, nome fantasia, data, valor e descricao
    ordenados de forma decrescente pela data e depois pelo id da ordem de serviço
    '''
    try:
        query = """
            SELECT os.id, c.nome_fantasia, os.data, os.valor, os.descricao 
            FROM ordem_de_servico os 
            JOIN cliente c ON os.cliente_id = c.id
        """
        condicoes = []
        parametros = []

        if id_cliente is not None:
            condicoes.append("os.cliente_id = %s")
            parametros.append(id_cliente)
        
        if data is not None:
            condicoes.append("os.data = %s")
            parametros.append(data)
        
        if condicoes:
            query += " WHERE " + " AND ".join(condicoes)

        query += " ORDER BY os.data, os.id DESC "

        cursor.execute(query, tuple(parametros))
        resultado = cursor.fetchall()
        return resultado
    except Error as e:
        st.error(f"Não foi possível consultar as O.S. para o cliente e/ou data selecionados. Erro: {e}")

def consultar_os_por_fechamento(id_fechamento):
    '''
    Realiza uma consulta na tabela ordem_de_servico em busca de todas as ordens de serviço registradas sob o fechamento fornecido.

    :param id_fechamento: Integer, número que representa o id do fechamento fornecido
    :return: resultado da consulta contendo todas as ordens de serviço que possuam o id fornecido no campo fechamento na tabela ordem_de_servico
    '''

    try:
        cursor.execute(''' SELECT os.id, c.nome_fantasia, os.data, os.valor, os.descricao,
                        CASE 
                        WHEN COUNT(m.idmidia_os) > 0 THEN TRUE 
                        ELSE FALSE 
                        END AS has_midia
                        FROM ordem_de_servico os
                        LEFT JOIN midia_os m ON m.id_os = os.id
                        JOIN cliente c ON os.cliente_id = c.id
                        WHERE os.fechamento_id = %s
                        GROUP BY os.id, c.nome_fantasia, os.data, os.valor, os.descricao;''', (id_fechamento,))
        resultado = cursor.fetchall()
        return resultado
    
    except Error as e:
        st.error(f"Não foi possível encontrar as ordens de serviço relacionadas ao fechamento {id_fechamento}. Erro: {e}")

def consulta_menor_e_maior_valor_os():
    '''
    Consulta na tabela ordem_de_servico todos os registros que não pertençam a um fechamento. Depois encontra o menor e o maior valor de os cadastrada.

    :return Float: retorna 2 números que representam o menor e o maior valor encontrada nas ordens de serviço consultadas.
    '''

    try:
        cursor.execute('''SELECT MIN(os.valor) AS menor_valor, MAX(os.valor) as maior_valor FROM ordem_de_servico os
                       WHERE fechamento_id IS NULL;''')
        resultado = cursor.fetchone()
        if resultado[0] != None and resultado[1] != None:
            menor_valor = resultado[0]
            maior_valor = resultado[1]+1
            return int(menor_valor), int(maior_valor)
        else:
            menor_valor = 0
            maior_valor = 1
            return menor_valor, maior_valor
    
    except Error as e:
        st.error(f"Não foi possível encontrar o menor e o maior valor entre as ordens de serviço cadastradas. Erro {e}")


'''Funções da tabela midia_os'''

'''Criar Registros'''
def salvar_midia_na_pasta(id_os, id_cliente, arquivos):

    '''
        Salva os arquivos fornecidos na pasta correspondente, troca o nome dele
        usando o id da os, o id do cliente, a palavra arquivo e o número de arquivos que 
        estão gravados pra aquela OS. 
        Exemplo: 48_7_arquivo_0.pdf
        48 é o número da O.S.
        7 é o id do cliente que solicitou a O.S.
        0 é a qtde de arquivos que já estavam cadastrados pra aquela O.S.

        :param id_os: Integer, número de id da os a qual o(s) arquivo(s) se refere(m)
        :param id_cliente: Integer, número de id do cliente ao qual a os foi registrada
        :param arquivos: Objeto, arquivos fornecidos no formulário de registro da O.S. como foram upados
        :return: Lista de String, o caminho completo de cada arquivo fornecido para registro no bd
    '''
    caminho_arquivos = []

    '''Consulta no banco de dados se já existem arquivos cadastrados para a O.S.,
    caso existam retorna a qtde de registros encontrados, caso não existam retorna 0
    '''
    cursor.execute("SELECT COUNT(*) FROM midia_os WHERE id_os = %s", (id_os,))
    resultado = cursor.fetchone()
    num_arquivos_existentes = resultado[0] if resultado else 0


    for index, arquivo in enumerate(arquivos):
        extensao = os.path.splitext(arquivo.name)[1]  # Obtém a extensão do arquivo, incluindo o ponto
        '''O nome do arquivo usa o número de resultados para somar à qtde de arquivos que já existem 
        para impedir que seja sobreescritos'''
        nome_arquivo = f"{id_os}_{id_cliente}_arquivo_{index + num_arquivos_existentes}{extensao}"
        caminho_destino = os.path.join(DIR_MIDIA_OS, nome_arquivo)
        try:
            with open(caminho_destino, "wb") as f:
                    f.write(arquivo.getbuffer() if hasattr(arquivo, 'getbuffer') else arquivo)
                    caminho_arquivos.append(caminho_destino)
        except Exception as e:
                print(f"Erro ao salvar o arquivo {arquivo}: {e}")
    return caminho_arquivos
    
def salvar_midia_no_bd(midia_os):
    '''
        Salva no banco de dados os caminhos absolutos de cada arquivo fornecido pelo usuário para o registro da ordem de serviço

        :param midia_os: model instanciada da tabela Midia_Os contendo os dados necessários para registro
        :return: janela flutuante confirmando a gravação dos dados ou mensagem de erro
    '''

    try:
         cursor.execute('''INSERT INTO midia_os(id_os, arquivo, descricao) VALUES (%s, %s, %s)''', (midia_os.id_os, midia_os.arquivo, midia_os.descricao))
         conexao.commit()
         st.toast(f"A mídia {os.path.basename(midia_os.arquivo)} foi cadastrada com sucesso junto a ordem de serviço {midia_os.id_os}")

    except Error as e:
         st.error(f"Ocorreu o seguinte erro ao cadastrar a mídia para a os {midia_os.id_os}:{e}")

'''Consultar Registros'''
def consulta_midia_por_id_os(id_os):

    '''
        Consulta na tabela midia_os todos os arquivos de mídia salvos correspondentes ao id da ordem de serviço fornecida

        :param id_os: Integer, número correspondente à id da ordem de serviço que deseja pesquisar
        :return: Lista, lista contendo o(s) id(s) das mídias encontradas ou None caso não tenha nenhuma.
        Os dados vêm com os seguintes índices:
            0=id da mídia
            1=id da ordem de serviço
            2=caminho do arquivo cadastrado no banco de dados
            3=descrição do arquivo
    '''
    try:
        cursor.execute("SELECT * FROM midia_os WHERE id_os = %s", (id_os,))
        resultado = cursor.fetchall()
        if not resultado:
             return None
        else:
            midias_instanciadas = [Midia_OS(res[1], res[2], res[3], res[0]) for res in resultado]
            return midias_instanciadas
    except Error as e:
        st.error(f"Não foi possivel encontrar nenhuma midia salva. Erro:{e}")

'''Deletar Registros'''
def deletar_midia_por_id_midia(id_midia, nome_arquivo, caminho):
    '''Exclui arquivos de mídia salvos. Excluindo tanto o arquivo no diretório quanto o registro no banco de dados
    Caso haja algum erro na remoção do arquivo do disco o registro no banco de dados não será apagado

    :param id_midia: Integer, número que corresponde ao registro no banco de dados da mídia em questão
    :param nome_arquivo: String, nome do arquivo conforme registro no banco de dados
    :param caminho: String, caminho absoluto do arquivo
    :return: mensagem especificando o sucesso ou falha no procedimento'''
    
    '''Exclui o arquivo do disco'''
    continuar = False
    try:
        if os.path.exists(caminho):
            os.remove(caminho)
        else:
            st.toast(f"Arquivo {nome_arquivo} não foi encontrado para remoção.")
        
        continuar = True
        
    except Exception as e:
            st.error(f"Erro ao tentar excluir o arquivo {nome_arquivo}. Ocorreu um erro: {e}")
        
    '''Exclui o registro do arquivo do banco de dados'''
    if continuar:
        try:
            cursor.execute("DELETE FROM midia_os WHERE idmidia_os = %s", (id_midia,))
            conexao.commit()
            st.toast(f"O arquivo {nome_arquivo} foi deletado com sucesso.")
        
        except Error as e:
            st.error(f"Não foi possível deletar o arquivo {nome_arquivo}, ocorreu um erro: {e}")