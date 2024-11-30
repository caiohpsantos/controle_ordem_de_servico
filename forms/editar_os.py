import streamlit as st
from datetime import datetime, timedelta
import os
import locale
import mimetypes
from streamlit_pdf_viewer import pdf_viewer
from models.ordem_de_servico import Ordem_Servico, Midia_OS
from controllers import cliente_controller, os_controller
from services import media
from funcionalidades import Valida, Formata, Arquivos

def format_os(item):
    '''
    Recebe o objeto item contendo os dados da ordem de serviço que será exibida.
    Formata a data para o formato dd/mm/aaaa e o valor para R$
    Devolvendo uma string formatada para melhor exibição.
    :param item:Uma lista de listas contendo os dados id, cliente, data, valor e descricao da os fornecida
    :return: String formatada
    '''
    
    id, cliente, data, valor, descricao = item
    data_formatada = data.strftime('%d/%m/%Y')
    valor_formatado = f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    return f'''O.S. {id} | Cliente: {cliente} | Data: {data_formatada} | Valor: {valor_formatado} \n
    {descricao}'''

def localizar_os():
    '''
    Verifica se há um parametro na url, se houver captura o numero e o usa para buscar a ordem de serviço
    e abre o formulário para alterar os dados. Caso não houver abre a pesquisa para escolher qual ordem de serviço
    será editada
    :param id_os:parâmetro na url que é o número da os para edição
    '''

    'locale é a biblioteca responśavel por mostrar o valor em reais na coluna Valor'
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
        
    os_localizadas = None

    '''Este bloco de código monta as formas de pesquisa e chama as funções necessárias para cada uma
    atribuindo o resultado da consulta à variável os_localizadas'''

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
        data = st.date_input("Selecione o intervalo de tempo", [trinta_dias_atras.date(), hoje.date()],
                                help="Inicia com o período de 30 dias contado a partir da data atual. É necessário selecionar duas datas")

    '''Encontra o menor e o maior valor dentre os fechamentos registrados para usar como parâmetro do slider'''
    menor_valor_slider, maior_valor_slider = os_controller.consulta_menor_e_maior_valor_os()
    '''Se o menor valor e o maior forem iguais (não há fechamentos ou só tem 1 ou tem vários do mesmo valor)
    o menor valor é definido como 0 para que o maior sobressaia'''
    if menor_valor_slider == maior_valor_slider:
        menor_valor_slider = 0
    
    if maior_valor_slider < 1:
        maior_valor_slider = 1

    valor = st.select_slider("Escolha a faixa de valores", options=range(menor_valor_slider, maior_valor_slider+1),
                                                value=(menor_valor_slider, maior_valor_slider),
                        help="O menor e o maior valor para selecionar são, respectivamente, os valores dos fechamentos registrados.")
    
    
    os_localizadas = os_controller.consulta_os(cliente_selecionado, data, valor)

    st.divider()
 
    '''Aqui são criadas as abas que serão usadas para mostrar os dados da O.S. que for selecionada'''
    tab_dados, tab_midia = st.tabs(["Dados da O.S", "Mídias da O.S."])
    

    if os_localizadas:
        os_radio = []
        '''O laço de repetição transforma o resultado em uma lista para que o st.radio possa recebê-la'''
        for item in os_localizadas:
            os_radio.append(item)
        
        os_selecionada = st.radio("Ordens de Serviço encontradas", help="Clique na O.S. que deseja editar e depois na aba Dados da O.S. logo acima", 
                                options=os_radio, format_func=format_os, index=None)
        
        '''Caso alguma O.S. seja selecionada o id dela vai para a url do app
        Esta é uma forma de burlar a limitação do streamlit que refaz a página a cada ação que é feita nela.
        Caso coloque um botão, ao clicar no botão para salvar os dados a chamada da função é refeita e perde-se o id,
        por isso optei pela url que permanece mesmo após o rerun da página'''

        if os_selecionada:
                st.query_params.id_os = os_selecionada[0]
    
    with tab_dados:

        id_os = st.query_params.id_os
        if id_os == "None":
            st.caption("É necessário pesquisar a ordem de serviço na aba Consultar O.S. e clicar no botão Editar para que ela apareça aqui.")
        
        if id_os != "None":
            os_para_editar = os_controller.consultar_os_por_id(id_os)
                
            '''Monta o form com os dados salvos para edição'''

            
            st.caption("Use os campos abaixo para alterar os dados da Ordem de Serviço")
            st.caption("Campos com * no nome são obrigatórios")
                    
            st.divider()
            '''consulta todos os clientes por nome_fantasia mas especifica que o selectbox deve estar com o cliente gravado na os'''
            resultado_consulta = cliente_controller.consulta_todos_clientes_e_retorna_os_nomes_fantasia()
            lista_exibicao = [nome[0] for nome in resultado_consulta]
            cliente_atual = cliente_controller.consulta_cliente_por_id(os_para_editar.cliente_id)
            index_cliente_atual = lista_exibicao.index(cliente_atual.nome_fantasia)
            cliente_edit = st.selectbox("Especifique qual cliente solicitou o serviço *", lista_exibicao, index=index_cliente_atual)

            '''Seletor de data, recebendo a data da gravação da os como data padrão.

            Limitar a data do serviço em até 40 dias atrás para o caso de atraso no lançamento,
            em 40 dias ainda está no prazo de lançar as ordens de serviço do dia 01 do mês anterior até o dia 10 do mês posterior'''

            hoje = datetime.today()
            trinta_dias_atras = hoje - timedelta(days=40)
            data_edit = st.date_input("Insira a data que o serviço foi prestado *", os_para_editar.data,trinta_dias_atras,hoje,format="DD/MM/YYYY")

            valor_edit = st.number_input("Valor cobrado (usar ponto e não vírgula para os centavos) *", value=os_para_editar.valor)

            descricao_edit = st.text_area("Descrição *", max_chars=255, key="descricao_geral", value=os_para_editar.descricao).upper()

            solicitante_edit = st.text_input("Nome/departamento de quem solicitou o serviço *", value=os_para_editar.solicitante).upper()

            tel_solicitante_edit = st.text_input("Contato do solicitante", placeholder="Só números. No formato: XX-XXXXX-XXXX", max_chars=11,
                                            value=Formata.limpa_pontuacao(os_para_editar.tel_solicitante))
            
            st.caption('''Os campos abaixo são opcionais. Você pode adicionar mídias em uma ordem de serviço que não possui mídia cadastrada ou adicionar mais.''')

            midias_edit = st.file_uploader("Adicione aqui seus arquivos:", help="Aceita vários arquivos. Aceita fotos, vídeos, áudios, pdfs...", accept_multiple_files=True)
    
            descricao_midia_edit = st.text_area("Descrição dos arquivos de mídia", help="Digite aqui explicações sobre os arquivos. Por exemplo: Áudio da solicitação de serviço, Print da tela do Whatsapp confirmando a solicitação de serviço...")
            
            gravar = st.button("Gravar alterações")
            
            if gravar:
                        #Verifica se nenhum campo obrigatório ficou sem preenchimento
                        if not valor_edit or not descricao_edit or not solicitante_edit:
                            st.error("Algum campo obrigatório ficou em branco. Verifique acima")

                        else:
                            '''inicia as verificações e validações que cada campo precisa ter'''
                            problema=False

                            '''Verificação do cliente'''
                            if cliente_controller.consulta_se_cliente_esta_ativo(cliente_edit) == 0:
                                problema=True
                                st.error(f'''O Cliente {cliente_edit} não está Ativo, portanto não pode ter O.S. registradas.
                                         Para reativá-lo vá até o menu Clientes e Editar, selecione o cliente que deseja, marque a opção Desativado e
                                         depois clique em Gravar.''')

                            '''Verificação do telefone'''
                            if tel_solicitante_edit:
                                if not Valida.telefone(tel_solicitante_edit):
                                    problema = True
                            
                            if midias_edit and not descricao_midia_edit:
                                st.error("Quando um arquivo é anexado à ordem de serviço uma breve descrição deve ser escrita sobre ele no campo acima.")
                                problema = True

                            if not problema:
                                confirmacao = False
                                cliente_escolhido_edit = cliente_controller.consulta_cliente_por_nome_fantasia(cliente_edit)
                                os_editada = Ordem_Servico(cliente_escolhido_edit.id,data_edit,valor_edit,descricao_edit,
                                                        solicitante_edit,tel_solicitante_edit,os_para_editar.id)
                                os_controller.editar_ordem_de_servico(os_editada)
                                if midias_edit:
                                    caminho_arquivos = os_controller.salvar_midia_na_pasta(os_editada.id, os_editada.cliente_id, midias_edit)
                                    for arquivo in caminho_arquivos:
                                        nova_midia = Midia_OS(os_editada.id, arquivo, descricao_midia_edit)
                                        os_controller.salvar_midia_no_bd(nova_midia)
                                st.query_params.id_os = None
                                    
    with tab_midia:
        id_os = st.query_params.id_os
        if id_os == "None":
            st.caption("É necessário pesquisar a ordem de serviço acima e clicar em alguma O.S. para que os arquivos apareçam aqui.")
        
        if id_os != "None":
            with st.spinner('Carregando dados...'):
                os_para_editar = os_controller.consultar_os_por_id(id_os)
                midia_da_os = os_controller.consulta_midia_por_id_os(os_para_editar.id)
                arquivo_para_deletar = {}
                col_1, col_2 = st.columns(2)
                if midia_da_os:
                    for index, arquivo in enumerate(midia_da_os):
                        with col_1:
                            with st.container(border=True):
                                if arquivo.tipo_arquivo == 'Imagem':
                                    st.image(arquivo.arquivo, width=400)
                                if arquivo.tipo_arquivo == 'PDF': 
                                    pdf_viewer(arquivo.arquivo, height=400)
                                
                                arquivo_carregado = Arquivos.ler_arquivo(arquivo.arquivo)
                                tipo_arquivo,_ = mimetypes.guess_type(arquivo.arquivo)

                                st.download_button('Baixar este arquivo ', data=arquivo_carregado, file_name=arquivo.nome_arquivo,
                                                mime=tipo_arquivo, key=f"download_{arquivo.id_midia}")
                                
                                st.caption(f'Descrição: {arquivo.descricao}')
                                remover_arquivo = st.button('Remover este arquivo', key=f"checkbox_{arquivo.id_midia}")
                                if remover_arquivo:
                                    os_controller.deletar_midia_por_id_midia(arquivo.id_midia,arquivo.nome_arquivo,arquivo.arquivo)
                                    
                else:
                    st.write("Não tem arquivos cadastrados. Para adicionar vá a aba 'Dados da O.S.'")

