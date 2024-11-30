import streamlit as st
import datetime
import os
import io
import locale
import yaml
from yaml import SafeLoader
from streamlit_pdf_viewer import pdf_viewer
from models.ordem_de_servico import Ordem_Servico, Midia_OS
from controllers import cliente_controller, os_controller
from funcionalidades import Formata, Valida
from services import media, email
from relatorios.nova_os import emitir_pdf_nova_os

'''abre o arquivo com os dados da empresa'''
with open('./config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

def nova_os():
    st.query_params.clear()
    with st.form("nova_os"):
                    
        st.caption("Digite abaixo os dados da Ordem de Serviço")
        st.caption("Campos com * no nome são obrigatórios")
        
        st.divider()

        resultado_consulta = cliente_controller.consulta_todos_clientes_ativos_e_retorna_os_nomes_fantasia()
        lista_exibicao = ['']+[nome[0] for nome in resultado_consulta]
        cliente = st.selectbox("Especifique qual cliente solicitou o serviço *", lista_exibicao, 
                               help='''Caso algum cliente não esteja aparecendo aqui é porquê ele está desativado.\n 
                               Vá até o cadastro do cliente em questão e o reative para registrar novas ordens de serviço para ele.''')

        #limitar a data do servico em até 40 dias atrás para o caso de atraso no lançamento
        #em 40 dias ainda está no prazo de lançar as o.s's do dia 01 do mês anterior até o dia 10 do mês posterior
        hoje = datetime.datetime.now()
        trinta_dias_atras = hoje - datetime.timedelta(days=40)
        data = st.date_input("Insira a data que o serviço foi prestado *",'today',trinta_dias_atras,hoje,format="DD/MM/YYYY",)

        valor = st.number_input("Valor cobrado (usar ponto e não vírgula para os centavos) *")

        descricao = st.text_area("Descrição *", max_chars=255, key="descricao_geral").upper()

        solicitante = st.text_input("Nome/departamento de quem solicitou o serviço *").upper()

        tel_solicitante = st.text_input("Contato do solicitante", placeholder="Só números. No formato: XX-XXXXX-XXXX", max_chars=11)

        st.caption("Os campos abaixo são opcionais. Caso queira adicionar o print da conversa do zap ou o áudio da conversa solicitando o serviço como prova da solicitação.")

        midias = st.file_uploader("Adicione aqui seus arquivos:", help="Aceita vários arquivos. Aceita fotos, vídeos, áudios, pdfs...", accept_multiple_files=True)
        
        descricao_midia = st.text_area("Descrição dos arquivos de mídia", placeholder="Se não houver arquivos de mídia pode deixar aqui em branco. Mas se houver, a descrição deve ser preenchida.", help="Digite aqui explicações sobre os arquivos. Por exemplo: Áudio da solicitação de serviço, Print da tela do Whatsapp confirmando a solicitação de serviço...").upper()

        enviar_email = st.checkbox("Enviar email para o cliente sobre esta ordem de serviço.")
        
        gravar = st.form_submit_button("Gravar")

        
        if gravar:
            #Verifica se nenhum campo obrigatório ficou sem preenchimento
            if not valor or not descricao or not solicitante:
                st.error("Algum campo obrigatório ficou em branco. Verifique acima")

            else:
                '''inicia as verificações e validações que cada campo precisa ter'''
                problema=False
                '''Verificação do telefone'''
                if tel_solicitante:
                    if not Valida.telefone(tel_solicitante):
                        problema = True

                if midias and not descricao_midia:
                        st.error("Quando um arquivo é anexado à ordem de serviço uma breve descrição deve ser escrita sobre ele no campo acima.")
                        problema = True
                
                if not problema:
                    cliente_escolhido = cliente_controller.consulta_cliente_por_nome_fantasia(cliente)
                    nova_os = Ordem_Servico(cliente_escolhido.id,data,valor,descricao,solicitante,tel_solicitante)
                    id_cadastrada = os_controller.criar_nova_ordem_servico(nova_os)
                    if midias:
                            for midia in midias:
                                caminho_arquivos = os_controller.salvar_midia_na_pasta(id_cadastrada, nova_os.cliente_id, midias)
                                for arquivo in caminho_arquivos:
                                    nova_midia = Midia_OS(id_cadastrada,arquivo,descricao_midia)
                                
                                os_controller.salvar_midia_no_bd(nova_midia)
                    if enviar_email:
                        'Consulta o nome fantasia do cliente'
                        nome_fantasia_cliente = cliente_controller.consulta_cliente_por_id(nova_os.cliente_id)

                        'Monta o assunto do email, colocando o número da O.S. dinamicamente'
                        assunto = f"Confirmação de Registro de Nova Ordem de Serviço nº {id_cadastrada}"

                        'Monta o corpo do email como uma página html, mudando dinamicante dados necessários'
                        mensagem = email.cria_mensagem_nova_os(id_cadastrada, nome_fantasia_cliente.nome_fantasia, nova_os.data_formatada,
                                                               nova_os.descricao, locale.currency(nova_os.valor, grouping=True))
                        
                        pdf_gerado = emitir_pdf_nova_os(id_cadastrada)
                        
                        with st.spinner("Enviando email"):
                            email.envia_email(cliente_escolhido.email, assunto, mensagem, [pdf_gerado],[f"Discriminacao O.S. - {id_cadastrada}"])
                
                    

