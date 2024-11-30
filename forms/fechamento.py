import streamlit as st
import pandas as pd
import locale
from streamlit_pdf_viewer import pdf_viewer
from datetime import datetime, timedelta
from controllers import os_controller, fechamento_controller, cliente_controller, nf_controller
from funcionalidades import Formata, Valida
from models.fechamento import Fechamento
from models.nota_fiscal import Nota_Fiscal
from services.database import conexao
from services.email import envia_email, cria_mensagem_nova_nf
from relatorios.faturamento import emitir_pdf_faturamento_detalhado



def formatar_fechamento(fechamento):
    '''Recebe um fechamento e devolve um string formatada para compor um radiobutton

    :param: List, Uma lista de listas contendo os dados do fechamento: id, nome fantasia do cliente relacionado, 
    data de registro do fechamento e o valor total dele (soma de todo as ordens de serviço que estão nele)
    :return: String, Uma string formatada'''
    id, nome_cliente, data, valor = fechamento
    data_formatada = Formata.data(data)
    valor_formatado = f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    return f"Fechamento nº {id} | Cliente: {nome_cliente} | Data: {data_formatada} | Valor: {valor_formatado}"

        
def criar():
    st.query_params.clear()
    
    st.header("Fechamento Mensal por Cliente")

    '''Cria o selecbox com os todos os clientes'''
    resultado_consulta = cliente_controller.consulta_todos_clientes_e_retorna_os_nomes_fantasia()
    lista_exibicao = ['']+[nome[0] for nome in resultado_consulta]
    col1, col2 = st.columns(2)
    nome_selecionado = col1.selectbox("Escolha o cliente para realizar o fechamento", lista_exibicao, placeholder="Clique aqui para escolher")

    '''Se o selectbox não estiver no index vazio (0) executa o bloco de código abaixo'''
    if nome_selecionado != '':
        'Consulta o cliente selecionado no banco de dados e o instancia na model Cliente'
        cliente_selecionado = cliente_controller.consulta_cliente_por_nome_fantasia(nome_selecionado)
        'Consulta todas as ordens de serviço no bd que sejam do cliente selecionado e que não estejam em nenhum fechamento ainda'
        resultado = os_controller.consultar_os_por_cliente_sem_fechamento(cliente_selecionado.id)
        'variável de controle para autorizar o processo a seguir'
        confirmar_fechamento = False

        'Se não houver nenhuma os disponível'
        if not resultado:
            st.write("Não há ordens de serviço fora de fechamentos para esse cliente.")
        else:
            'Tendo os disponível'
            'Avisos importantes para o usuário'
            with st.expander("Ajuda"):
                st.info("Para retirar alguma O.S. do fechamento clique sobre a Ordem de Serviço e desmarque a opção 'Adicionar'.")
                st.info("Se este símbolo: :material/file_open: estiver em uma ordem de serviço ela possui arquivos de mídia. Clique sobre ela para vê-los.")
                st.info("Atenção! Ordens de Serviço que forem incluídas no fechamento não poderão ser editadas posteriormente.")
            
            'Laço de repetição que vai gerar um expander para cada o.s. retornada'
            os_selecionadas = []
            for registro in resultado:
                '''Verifica o index 4 (coluna que guarda a informação se a os possui mídia registrada),
                se verdadeiro determina um ícone para diferenciar das que não possuem'''
                if registro[4] == 0:
                    icone = None
                elif registro[4] == 1:
                    icone = ":material/file_open:"
                else:
                    icone = None
                
                with st.expander(f"O.S. {registro[0]}", expanded=False, icon=icone):
                    'Checkbox que determina se a o.s. vai ser contada ou não no fechamento'
                    selecionada = st.checkbox("Adicionar", key=registro[0], value=True) 
                    'Dados da o.s. para o usuário verificar se estão corretos'
                    st.text_input("Data de registro", Formata.data(registro[1]), disabled=True, key=f"data{registro[0]}")
                    st.text_input("Valor", locale.currency(registro[2],grouping=True), disabled=True, key=f"valor{registro[0]}")
                    st.text_area("Descrição", registro[3], disabled=True, key=f"descricao{registro[0]}")
                    st.divider()

                    'Verifica novamente se há mídias na o.s. Caso tenha pesquisa no bd pelos registros e monta um visualizar dependendo do tipo'
                    if registro[4] == 1:
                        midias = os_controller.consulta_midia_por_id_os(registro[0])
                        qtde_midias = len(midias) if midias else '0'
                        if midias:
                            st.write(f"Há um total de {qtde_midias} arquivos para esta ordem de serviço")
                            for midia in midias:
                                if midia.tipo_arquivo == 'Imagem':
                                    with st.spinner("Carregando arquivo"):
                                        try:
                                            st.write("Imagem")
                                            st.image(midia.arquivo, width=400, caption=midia.descricao)
                                        except Exception as e:
                                            st.error(f"Não foi possível carregar a imagem {midia.nome_arquivo}. Erro: {e}")

                                if midia.tipo_arquivo == 'PDF':
                                    with st.spinner("Carregando arquivo"):
                                        try:
                                            st.write("PDF")
                                            st.caption("Caso o PDF não apareça, recarregue a página. Estou trabalhando numa solução.")
                                            pdf_viewer(midia.arquivo, height=400, key='viewer'+midia.tipo_arquivo+str(midia.id_midia))
                                            

                                        except Exception as e:
                                            st.error(f"Não foi possível carregar o arquivo {midia.nome_arquivo}. Erro: {e}")
                    else:
                        st.write('Nâo existem mídias cadastradas para esta ordem de serviço')

                    'Verifica se o checkbox está selecionado, caso esteja adiciona o id da o.s. na lista para gravação'
                    if selecionada:
                        os_selecionadas.append(registro[0])

            'Cria um dataframe com os dados da consulta de todas as o.s. do clientes sem fechamento. Para facilitar o manejo de datas.'
            dataframe = pd.DataFrame(resultado, columns=['ID', 'Data', 'Valor', 'Descrição', 'Mídia'])
            dataframe['Data'] = pd.to_datetime(dataframe['Data'])
            menor_data = dataframe['Data'].min()
            maior_data = dataframe['Data'].max()
            diferenca_dias = (maior_data - menor_data).days
            
            
            '''Container contendo dados diversos do fechamento: qtde de o.s., quais são, período de tempo, valor total'''
            with st.container(border=True):
                st.write(f"Há um total de {len(os_selecionadas)} ordens de serviço selecionadas.")
                string_os_selecionadas = ', '.join(map(str, os_selecionadas))        
                st.write(f"As ordens de serviços que serão adicionadas a este fechamento são: {string_os_selecionadas}")
                st.write(f"Este fechamento cobre {diferenca_dias} dias. De {menor_data.strftime('%d/%m/%Y')} até {maior_data.strftime('%d/%m/%Y')}")
                st.write(f"O valor total deste fechamento é {locale.currency(dataframe['Valor'].sum(),grouping=True)}")

            st.write(f"Para realizar o fechamento do cliente {cliente_selecionado} confirme abaixo.")
            
            confirmar_fechamento = st.button("Confirmar")

        if confirmar_fechamento:
            novo_fechamento = Fechamento(cliente_selecionado.id, datetime.today())
            fechamento_id = fechamento_controller.criar_novo_fechamento(novo_fechamento)
            
            os_incluidas = []

            with st.spinner(f"Gravando dados do fechamento {fechamento_id} para o cliente {cliente_selecionado}"):
                os_incluidas = os_controller.adiciona_fechamento_id(os_selecionadas, fechamento_id)

            if os_selecionadas == os_incluidas:
                st.toast(f"Gravação do fechamento número {fechamento_id} finalizada.")
            
            else:
                conexao.rollback()
                st.error(f"Houve um erro na gravação do fechamento número {fechamento_id} do cliente {cliente_selecionado}. A operação foi desfeita.")

def visualizar():
    st.header("Visualização/Edição de Fechamentos")

    col_cliente, col_data = st.columns(2)

    with col_cliente:
        cliente_selecionado = None
        resultado_consulta = cliente_controller.consulta_todos_clientes_e_retorna_os_nomes_fantasia()
        lista_exibicao = ['']+[nome[0] for nome in resultado_consulta]
        nome_selecionado = st.selectbox("Escolha o cliente", lista_exibicao)
        if nome_selecionado != '':
            cliente_selecionado = cliente_controller.consulta_cliente_por_nome_fantasia(nome_selecionado)
    
    with col_data:
        hoje = datetime.today()
        trinta_dias_atras = hoje - timedelta(days=30)
        data = st.date_input("Selecione o intervalo de tempo",(trinta_dias_atras.date(), hoje.date()),
                                help="Inicia com o período de 30 dias contado a partir da data atual. É necessário selecionar duas datas")

    '''Encontra o menor e o maior valor dentre os fechamentos registrados para usar como parâmetro do slider'''
    menor_valor_slider, maior_valor_slider = fechamento_controller.consulta_menor_e_maior_valor_fechamento() 
    '''Se o menor valor e o maior forem iguais (não há fechamentos ou só tem 1 ou tem vários do mesmo valor)
    o menor valor é definido como 0 para que o maior sobressaia'''
    if menor_valor_slider == maior_valor_slider:
        menor_valor_slider = 0
    
    if maior_valor_slider < 1:
        maior_valor_slider = 1

    valor = st.select_slider("Escolha a faixa de valores", options=range(menor_valor_slider, maior_valor_slider+1),
                                                value=(menor_valor_slider, maior_valor_slider),
                        help="O menor e o maior valor para selecionar são, respectivamente, os valores dos fechamentos registrados.")
    
    fechamentos_localizados = fechamento_controller.consulta_fechamento(cliente_selecionado, data, valor)
        

    opcoes = []

    for fechamento in fechamentos_localizados:
        opcoes.append(fechamento)

    fechamento_selecionado = st.radio("Selecione o fechamento para visualizar", options=opcoes, index= None, format_func=formatar_fechamento)

    if fechamento_selecionado:
        st.query_params.id_fechamento = fechamento_selecionado[0]

    st.divider()

    tab_dados, tab_os_registrada, tab_os_fora_fechamento = st.tabs(["Dados do Fechamento", "Ordens de Serviço Registradas", "Ordens de Serviço sem Fechamanento"])
    
    with tab_dados:
        id_fechamento = st.query_params.id_fechamento
    
        if id_fechamento == 'None':
            st.write("Escolha um fechamento acima para visualizar os dados")
        
        if id_fechamento != 'None':
            fechamento_para_editar = fechamento_controller.consulta_fechamento_por_id(id_fechamento)
            
            st.header(f"Fechamento nº: {fechamento_para_editar.id}")

            st.text_input("Registrado para o cliente", value=fechamento_para_editar.cliente, disabled=True, 
                        key=f"{fechamento_para_editar.id}_cliente_{fechamento_para_editar.cliente}")
            st.text_input("Registrado no dia ", value=Formata.data(fechamento_para_editar.data), disabled=True, 
                        key=f"{fechamento_para_editar.id}_data_{fechamento_para_editar.data_formatada}")
            st.text_input("Valor total das Ordens de Serviço anexadas", value=locale.currency(fechamento_para_editar.valor_total, grouping=True),
                        key=f"{fechamento_para_editar.id}_valor_{fechamento_para_editar.valor_total}", disabled=True)
            
            hoje = datetime.now().date()
            diferenca_dias = hoje - fechamento_para_editar.data
            dias_passados = diferenca_dias.days
            st.text(f"Este fechamento foi registrado há {dias_passados} dias.")

            if fechamento_controller.consulta_se_fechamento_possui_nf(id_fechamento):
                numero_nota = fechamento_controller.consulta_nf_por_fechamento(id_fechamento)
                st.write(f"Este fechamento possui a nota fiscal nº {numero_nota} associada.")
            else:
                st.write("Este fechamento ainda não possui nota fiscal associada.")

    with tab_os_registrada:
        confirmado = None
        id_fechamento = st.query_params.id_fechamento

        if id_fechamento == "None":
            st.write("Escolha um fechamento acima para visualizar as ordens de serviço que pertencem a ele.")
        
        if id_fechamento != "None":
            with st.expander("Ajuda"):
                st.info('''É possível retirar uma ordem de serviço de um fechamento que ainda não tenha sido faturado(nota emitida).
                        Basta abrir a ordem de serviço desejada e marcar a opção Retirar. Depois no botão Confirmar abaixo na página.''')
                st.info('''Caso não consiga clicar na opção Retirar, é porque o fechamento selecionado já possui uma nota fiscal associada.
                        Portanto, não é mais possível retirar ordens de serviço deste fechamento.''')
            os_localizadas = os_controller.consultar_os_por_fechamento(id_fechamento)
            os_selecionadas = []
            for registro in os_localizadas:
                '''Verifica o index 5 (coluna que guarda a informação se a os possui mídia registrada),
                se verdadeiro determina um ícone para diferenciar das que não possuem'''
                if registro[5] == 0:
                    icone = None
                elif registro[5] == 1:
                    icone = ":material/file_open:"
                else:
                    icone = None
    
                with st.expander(f"O.S. {registro[0]}", expanded=False, icon=icone):
                    '''Consulta se o fechamento já possui uma nf registrada, se possuir desabilita o checkbox
                    para retirar a ordem de serviço já que o fechamento não pode ser editado'''
                    habilita_edicao = fechamento_controller.consulta_se_fechamento_possui_nf(id_fechamento)
                    'Checkbox que determina se a o.s. vai ser retirada do fechamento'
                    selecionada = st.checkbox("Retirar", key=f'checkbox_{registro[0]}', value=False, disabled=habilita_edicao) 
                    'Dados da o.s. para o usuário verificar se estão corretos'
                    st.text_input("Data de registro", value=Formata.data(registro[2]), disabled=True, key=f"data{registro[0]}")
                    st.text_input("Valor", locale.currency(registro[3],grouping=True), disabled=True, key=f"valor{registro[0]}")
                    st.text_area("Descrição", registro[4], disabled=True, key=f"descricao{registro[0]}")
                    st.divider()

                    if selecionada:
                        os_selecionadas.append(registro[0])

            if len(os_selecionadas) != 0:
                st.warning(f"Aviso: as seguintes ordens de serviço serão retiradas do fechamento {id_fechamento}: {os_selecionadas}")
                st.write("Para confirmar a exclusão, clique no botão abaixo")
                confirmado = st.button("Confirmar", key="retirar")
            
        if confirmado:
            with st.spinner(f"Gravando dados do fechamento {id_fechamento} para o cliente {cliente_selecionado}"):
                os_incluidas = os_controller.retira_os_do_fechamento(os_selecionadas, id_fechamento)

            if os_selecionadas == os_incluidas:
                    st.toast(f"Gravação do fechamento número {id_fechamento} finalizada.")
                
            else:
                conexao.rollback()
                st.error(f"Houve um erro na gravação do fechamento número {id_fechamento} do cliente {cliente_selecionado}. A operação foi desfeita.")

    with tab_os_fora_fechamento:
        id_fechamento = st.query_params.id_fechamento

        if id_fechamento == "None":
            st.write("Escolha um fechamento acima para visualizar as ordens de serviço que podems er adicionadas a ele.")
        
        if id_fechamento != "None":
            with st.expander("Ajuda"):
                st.info('''É possível acrescentar uma ordem de serviço em um fechamento já aberto desde que ela já não esteja registrada
                        em um fechamento diferente do que está aberto e que o fechamento ainda não tenha sido faturado(nota emitida).
                        Basta abrir a ordem de serviço desejada e marcar a opção Acrescentar. Depois no botão Confirmar abaixo na página.''')
                st.info('''Caso não consiga clicar na opção Acrescentar, é porque o fechamento selecionado já possui uma nota fiscal associada.
                        Portanto, não é mais possível acrescentar ordens de serviço a este fechamento.''')
            fechamento = fechamento_controller.consulta_fechamento_por_id(id_fechamento)
            os_localizadas = os_controller.consultar_os_por_cliente_sem_fechamento(fechamento.cliente)

            for registro in os_localizadas:
                '''Verifica o index 5 (coluna que guarda a informação se a os possui mídia registrada),
                se verdadeiro determina um ícone para diferenciar das que não possuem'''
                if registro[4] == 0:
                    icone = None
                elif registro[4] == 1:
                    icone = ":material/file_open:"
                else:
                    icone = None
                with st.expander(f"O.S. {registro[0]}", expanded=False, icon=icone):
                    '''Consulta se o fechamento selecionado possui uma nota fiscal associada.
                    Caso possua desabilita a opção Acrescentar, já que o fechamento não pode mais sofrer alterações'''
                    habilita_edicao = fechamento_controller.consulta_se_fechamento_possui_nf(id_fechamento)
                    'Checkbox que determina se a o.s. vai ser retirada do fechamento'
                    selecionada = st.checkbox("Acrescentar", key=f'checkbox_add_{registro[0]}', value=False, disabled=habilita_edicao) 
                    'Dados da o.s. para o usuário verificar se estão corretos'
                    st.text_input("Data de registro", value=Formata.data(registro[1]), disabled=True, key=f"data_add_{registro[0]}")
                    st.text_input("Valor", locale.currency(registro[2],grouping=True), disabled=True, key=f"valor_add_{registro[0]}")
                    st.text_area("Descrição", registro[3], disabled=True, key=f"descricao_add_{registro[0]}")
                    st.divider()

                    if selecionada:
                        os_selecionadas.append(registro[0])

            if len(os_selecionadas) != 0:
                st.warning(f"Aviso: as seguintes ordens de serviço serão acrescentadas ao fechamento {id_fechamento}: {os_selecionadas}")
                st.write("Para confirmar a adição, clique no botão abaixo")
                confirmado = st.button("Confirmar", key="acrescentar")
            
        if confirmado:
            with st.spinner(f"Gravando dados do fechamento {id_fechamento} para o cliente {cliente_selecionado}"):
                os_incluidas = os_controller.acrescenta_os_ao_fechamento(os_selecionadas, id_fechamento)

            if os_selecionadas == os_incluidas:
                    st.toast(f"Gravação do fechamento número {id_fechamento} finalizada.")
                
            else:
                conexao.rollback()
                st.error(f"Houve um erro na gravação do fechamento número {id_fechamento} do cliente {cliente_selecionado}. A operação foi desfeita.")

