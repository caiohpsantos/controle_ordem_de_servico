import streamlit as st
from mysql.connector import Error
from services.database import conexao, cursor
from models.cliente import Cliente


'''Este controller agrega todas as funções relacionadas ao CRUD da tabela cliente'''

'''Criar Registros'''
def adicionar_cliente(cliente):
    """
        Cadastra um novo cliente no banco de dados

        :param cliente: Objeto instanciado da model cliente com todos os dados que um cliente deve ter,
        salvo opcional: complemento do endereço.
        :return: caso ocorra um erro, o retorna. Para sucesso não há confirmação. Incluído no formulário.
        """

    try:
        cursor.execute(
            '''INSERT INTO cliente(ativo, tipo_cliente, documento, razao_social, nome_fantasia, inscricao_estadual, telefone, email, logradouro, 
            numero, complemento, bairro, cidade, cep) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
            (cliente.ativo, cliente.tipo_cliente, cliente.documento, cliente.razao_social, cliente.nome_fantasia, cliente.inscricao_estadual, cliente.telefone, 
            cliente.email, cliente.logradouro, cliente.numero, cliente.complemento, cliente.bairro, cliente.cidade, cliente.cep, 
            ))
        conexao.commit()
        st.toast(f"Cliente {cliente.nome_fantasia} foi cadastrado com sucesso.")
    except Error as e:
        st.error(f"Ocorreu o seguinte erro: {e}")

'''Edita Registros'''
def editar_cliente(cliente):
    """
        Edita um cliente no banco de dados

        :param cliente: Objeto instanciado da model cliente com todos os dados que um cliente deve ter,
        salvo opcional: complemento do endereço.
        :return: não possui, usar try/except junto com a chamada para capturar exceções caso existam
        """
    cursor.execute('''UPDATE cliente SET ativo = %s, tipo_cliente = %s, documento = %s, razao_social = %s, nome_fantasia = %s,inscricao_estadual = %s,
                   telefone = %s, email = %s, logradouro = %s, numero = %s, complemento = %s, bairro = %s, cidade = %s, cep = %s WHERE id = %s''',(
                       cliente.ativo, cliente.tipo_cliente, cliente.documento, cliente.razao_social, cliente.nome_fantasia, cliente.inscricao_estadual, cliente.telefone, 
                        cliente.email, cliente.logradouro, cliente.numero, cliente.complemento, cliente.bairro, cliente.cidade, cliente.cep, cliente.id
                   ))
    conexao.commit()

'''Consulta Registros'''
def consulta_cliente_por_id(cliente_id):
    '''
        Consulta o banco de dados em busca dos dados do cliente usando sua id

        :param id: String contendo o id do cliente que se deseja os dados
        :return: objeto do banco de dados com o resultado da busca
    '''
    
    cursor.execute("SELECT * FROM cliente WHERE id=%s", (cliente_id,))
    resultado = cursor.fetchone()
    id_cliente, ativo, tipo_cliente, documento, razao_social, nome_fantasia, inscricao_estadual, telefone, email, logradouro, numero, complemento, bairro, cidade, cep = resultado
    return Cliente(ativo, tipo_cliente, documento, razao_social, nome_fantasia, inscricao_estadual, telefone, email, logradouro, numero, complemento, bairro, cidade, cep, id_cliente)

def consulta_se_cliente_existe(documento, razao_social, nome_fantasia):
    """
        Consulta o banco de dados em busca dos dados fornecidos: CNPJ, Razão Social e Nome Fantasia

        :param cnpj: String contendo o CNPJ formatado da forma padrão
        :param razao_social e nome_fantasia: String contendo o dado fornecido
        :return: True se o resultado for maior que 0 (encontrou alguma coisa) e
        False se o resultado for = 0 (não encontrou nada)
        """

    cursor.execute(
        "SELECT COUNT(*) FROM cliente WHERE documento = %s OR razao_social = %s OR nome_fantasia = %s", (documento,razao_social,nome_fantasia)
    )
    resultado = cursor.fetchone()[0]
    return True if resultado > 0 else False

def consulta_se_cliente_esta_ativo(nome_fantasia):
    '''
    Consulta o registro do cliente especificado para descobrir se ele está ativo. Caso esteja retorna True, senão False.

    :param nome_fantasia: String, nome fantasia do cliente selecionado para edição
    :return: Boolean, Se o status do cliente for Ativo retorna True, senão retorna False.
    '''

    cursor.execute('''SELECT ativo FROM cliente WHERE nome_fantasia=%s''', (nome_fantasia,))
    resultado = cursor.fetchone()
    return resultado

def consulta_todos_clientes_e_retorna_os_nomes_fantasia():
    """
    Consulta o banco de dados em busca de todos os clientes.

    :return: Uma lista contendo todos os nome fantasia encontrados.
    """
    cursor.execute(
        "SELECT nome_fantasia FROM cliente"
    )
    resultados = cursor.fetchall()
    lista = []
    for resultado in resultados:
         lista.append(resultado)
    lista.sort()
    return lista

def consulta_todos_clientes_ativos_e_retorna_os_nomes_fantasia():
    """
    Consulta o banco de dados em busca de todos os clientes ativos para registrar novas ordens de serviço.

    :return: Uma lista contendo todos os nome fantasia encontrados.
    """
    cursor.execute(
        "SELECT nome_fantasia FROM cliente WHERE ativo=1"
    )
    resultados = cursor.fetchall()
    lista = []
    for resultado in resultados:
         lista.append(resultado)
         lista.sort()
    return lista

def consulta_todos_clientes():
    """
    Consulta o banco de dados em busca de todos os clientes. Independente se estão ou não ativos.

    :return: Um objeto de banco de dados contendo todos os dados de todos os clientes.
    """
    cursor.execute(
        "SELECT * FROM cliente"
    )
    resultado = cursor.fetchall()
    return resultado

def consulta_cliente_por_nome_fantasia(nome_fantasia):
    """
    Consulta o banco de dados em busca de um cliente usando o nome_fantasia como parâmetros.

    :param nome_fantasia: O nome_fantasia selecionado no selectbox da página
    :return: Uma instância da classe Cliente correspondente ao nome_fantasia pesquisado.
    """

    cursor.execute(
        "SELECT * FROM cliente WHERE nome_fantasia = %s",(nome_fantasia,)
    )
    resultado = cursor.fetchone()
    if resultado:
        id, ativo, tipo_cliente, documento, razao_social, nome_fantasia, inscricao_estadual, telefone, email, logradouro, numero, complemento, bairro, cidade, cep = resultado
        return Cliente(ativo, tipo_cliente, documento, razao_social, nome_fantasia, inscricao_estadual, telefone, email, logradouro, numero, complemento, bairro, cidade, cep, id)
    return None

