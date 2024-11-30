import streamlit as st
import locale
import pyperclip
import mimetypes
from streamlit_pdf_viewer import pdf_viewer
from datetime import datetime, timedelta
from pdfminer.high_level import extract_text
from controllers import os_controller, fechamento_controller, cliente_controller, nf_controller
from funcionalidades import Formata, Valida
from models.fechamento import Fechamento
from models.nota_fiscal import Nota_Fiscal
from services.database import conexao
from services.email import envia_email, cria_mensagem_nova_nf
from forms.fechamento import formatar_fechamento
from relatorios.faturamento import emitir_pdf_faturamento_detalhado
from funcionalidades import Arquivos

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

def validar_nf(nf):
    text = extract_text(nf)
    dados_nota = {}
    prefeitura = text[:33]
    if prefeitura == 'PREFEITURA MUNICIPAL DE NERÓPOLIS':    
            dados_nota['num_nota'] = text[395:402] #numero da nota
            dados_nota['timestamp'] = datetime.strptime(text[423:442],'%d/%m/%Y %H:%M:%S') #data e hora da emissão
            dados_nota['cod_verificacao'] = text[464:471] #codigo de verificaçao
            dados_nota['vlr_nota'] = float(text[1886:1892].replace(',','.')) #valor total da nota
            dados_nota['prefeitura'] = True
            documento = text[652:669] #documento do tomador da nota
            if Valida.cnpj(documento, False):
                dados_nota['documento'] = documento
            
            if Valida.cpf(documento):
                dados_nota['documento'] = documento[:14]

            return dados_nota
    else:
        dados_nota['prefeitura'] = False
        return dados_nota

def formatar_nf(nf):
    '''Recebe uma consulta não formatada de nota fiscal e devolve um string formatada para compor um radiobutton

    :param: List, Uma lista de listas contendo os dados do fechamento: numero, data da emissao da nota, 
    valor total da nota e nome fantasia do cliente
    :return: String, Uma string formatada'''

    numero, data_emissao, valor, cliente = nf
    data_formatada = Formata.data(data_emissao)
    valor_formatado = f"R$ {float(valor):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    return f"NF: {numero} | Emissão: {data_formatada} | Valor: {valor_formatado} | Cliente: {cliente}"

def faturar():
    st.query_params.clear()
    
    st.header("Faturamento")

    confirmacao_2 = None
    tipo_relatorio = None

    opcoes = fechamento_controller.consulta_fechamentos_sem_nota()

    fechamento_selecionado = st.radio("Escolha um fechamento para faturar", options=opcoes, format_func=formatar_fechamento, index=None)

    st.divider()

    if fechamento_selecionado:
        st.write(f"Clique no botão abaixo para iniciar o processo de faturamento do fechamento {fechamento_selecionado[0]}")
        
        st.caption("Caso tenha dúvidas, reveja os valores e ordens de serviço que serão incluídas no menu Visualizar logo acima.")
        confirmacao = st.checkbox("Para confirmar que deseja prosseguir, clique aqui.")
        if confirmacao:
            with st.expander("Dados para emissão da nota fiscal"):
                "Dados do cliente"
                cliente_para_nf = cliente_controller.consulta_cliente_por_nome_fantasia(fechamento_selecionado[1])
                st.write(f"Razão Social/Nome Completo do cliente: {cliente_para_nf.razao_social}")
                if cliente_para_nf.tipo_cliente == "Pessoa Jurídica":
                    tipo_documento = "CNPJ"
                    documento = cliente_para_nf.documento

                if cliente_para_nf.tipo_cliente == "Pessoa Física":
                    tipo_documento = "CPF"
                    documento = Formata.cpf(cliente_para_nf.documento)

                st.write(f"{tipo_documento}: {documento}")

                st.write(f"Endereço: {cliente_para_nf.endereco_completo}")

                st.write(f"Telefone: {cliente_para_nf.telefone} / Email: {cliente_para_nf.email}")

                "Dados do fechamento"
                fechamento_para_nf = fechamento_controller.consulta_fechamento_por_id(fechamento_selecionado[0])
                st.write(f"Fechamento nº: {fechamento_para_nf.id} de {fechamento_para_nf.data_formatada}")
                st.write(f"Valor total: {locale.currency(fechamento_para_nf.valor_total, grouping=True)}")
                data_mais_antiga, data_mais_recente = fechamento_controller.consulta_data_mais_antiga_e_mais_recente(fechamento_para_nf.id)
                diferenca_dias = (data_mais_recente - data_mais_antiga).days
                '''Caso a diferença de dias seja 0 (somente 1 o.s. no fechamento ou várias com a mesma data),
                substitui esse resultado para 1 pois o serviço foi prestado por pelo menos 1 dia'''
                if diferenca_dias == 0:
                    diferenca_dias = 1
                st.write(f"Iniciado em {data_mais_antiga.strftime("%d/%m/%Y")} e finalizado em {data_mais_recente.strftime("%d/%m/%Y")}, totalizando {diferenca_dias} dias.")
                
                os_incluidas_no_fechamento = os_controller.consultar_os_por_fechamento(fechamento_selecionado[0])
                lista_os_para_nf = [os[0] for os in os_incluidas_no_fechamento]
                string_formatada = ', '.join(map(str, lista_os_para_nf))
                st.write(f"Ordens de Serviço incluídas neste fechamento: {string_formatada}")

                texto_sugerido = f'''SERVIÇO PRESTADO DE MENSAGEIRO/COURIER PARA {cliente_para_nf.razao_social},NO PERÍODO DE {Formata.data(data_mais_antiga)} A {Formata.data(data_mais_recente)}, TOTALIZANDO {diferenca_dias} DIAS. SOB O FECHAMENTO Nº: {fechamento_para_nf.id} COM UM TOTAL DE {len(lista_os_para_nf)} ORDENS DE SERVIÇO ABERTAS, NÚMEROS: {string_formatada}.'''.upper()
                
                texto_final = st.text_area('Texto descritivo sugerido', texto_sugerido)
                copiar = st.button("Copiar :clipboard:")
                if copiar:
                    pyperclip.copy(texto_final)

            nota_emitida = st.checkbox("Nota emitida")
            if nota_emitida:
                arquivo_nota = st.file_uploader("Arquivo PDF da nota fiscal", ['pdf'])
                confirma_envio = st.checkbox("Enviar nota e relatório detalhado para o cliente via email.", 
                            help="Essa envio pode ser feito depois no menu XXXXXX")
                salvar_nota = st.button("Salvar nota")    
                if arquivo_nota and salvar_nota:
                    dados_nota = validar_nf(arquivo_nota)
                    if dados_nota['prefeitura'] == False:
                        st.error("O arquivo fornecido não parece ser uma nota fiscal de serviço emitida pela prefeitura de Nerópolis. Caso o arquivo esteja certo contate o suporte.")
                    
                    elif dados_nota['documento'] != cliente_para_nf.documento:
                        st.error(f"Nota fornecida não foi emitida para o cliente {cliente_para_nf.nome_fantasia}. A nota foi emitida para o documento {dados_nota['documento']} e o cliente do fechamento selecionado tem o docmento {cliente_para_nf.documento}.")
                    
                    elif dados_nota['vlr_nota'] != fechamento_para_nf.valor_total:
                        st.error(f"Nota fornecida tem valor {locale.currency(dados_nota['vlr_total'], grouping=True)}, diferente do fechamento escolhido que tem valor {locale.currency(fechamento_para_nf.valor_total)}. Verifique se a nota carregada é a correta ou se o fechamento selecionado é o correto.")
                    
                    else:
                        'Verifica se a nota fiscal já está cadastrada no sistema. Caso não esteja prossegue com o processo, caso esteja retorna um erro'
                        existe_nf = nf_controller.consulta_se_nf_ja_existe(int(dados_nota['num_nota']))
                        
                        if existe_nf:
                            st.error(f"A nota fiscal nº {int(dados_nota['num_nota'])} já está cadastrada no sistema.")
                        
                        else:
                            'Inicia o processo de registro da nota fiscal emitida pelo usuario'
                            'Grava o arquivo na pasta services/media/notas_fiscais'
                            nome_anexos = []
                            caminho_arquivo, nome_arquivo_nf = nf_controller.salvar_nf_na_pasta(int(dados_nota['num_nota']), fechamento_para_nf.id, cliente_para_nf.nome_fantasia, arquivo_nota)
                            nf_para_gravar = Nota_Fiscal(dados_nota['timestamp'],dados_nota['vlr_nota'], caminho_arquivo,
                                        dados_nota["cod_verificacao"], dados_nota['num_nota'])
                            confirma_registro = nf_controller.salvar_nf_no_bd(nf_para_gravar,fechamento_para_nf.id)
                            if confirma_registro and confirma_envio:
                                relatorio = emitir_pdf_faturamento_detalhado(fechamento_para_nf.id)
                                assunto = f"Nota Fiscal de Serviços - Gyn Dourier"
                                mensagem = cria_mensagem_nova_nf(nf_para_gravar,fechamento_para_nf, cliente_para_nf)
                                envia_email(cliente_para_nf.email, assunto, mensagem,[arquivo_nota, relatorio], [nome_arquivo_nf, f'relatorio detalhado fechamento {fechamento_para_nf.id}.pdf'])
                        
                elif not arquivo_nota and salvar_nota:
                    st.error("Não há nenhum arquivo anexado para análise. Insira um no campo acima")
                
                else:
                    pass

def pesquisa_nf():
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

    col_cliente_valor, col_data_numero = st.columns(2)

    with col_cliente_valor:
        'consulta por cliente'
        cliente_selecionado = None
        resultado_consulta = cliente_controller.consulta_todos_clientes_e_retorna_os_nomes_fantasia()
        lista_exibicao = ['']+[nome[0] for nome in resultado_consulta]
        nome_selecionado = st.selectbox("Escolha o cliente", lista_exibicao)
        if nome_selecionado != '':
            cliente_selecionado = cliente_controller.consulta_cliente_por_nome_fantasia(nome_selecionado)
        
        'consulta por range de valores'
        '''Encontra o menor e o maior valor dentre os fechamentos registrados para usar como parâmetro do slider'''
        menor_valor_slider, maior_valor_slider = nf_controller.consulta_nf_maior_e_menor_valor()
        '''Se o menor valor e o maior forem iguais (não há fechamentos ou só tem 1 ou tem vários do mesmo valor)
        o menor valor é definido como 0 para que o maior sobressaia'''
        if menor_valor_slider == maior_valor_slider:
            menor_valor_slider = 0
        
        if maior_valor_slider < 1:
            maior_valor_slider = 1

        valor = st.select_slider("Escolha a faixa de valores", options=range(menor_valor_slider, maior_valor_slider+1),
                                                    value=(menor_valor_slider, maior_valor_slider),
                        help="O menor e o maior valor para selecionar são, respectivamente, os valores das notas fiscais registradas.")


    
    with col_data_numero:
        'pesquisa por range de data'
        hoje = datetime.today()
        trinta_dias_atras = hoje - timedelta(days=30)
        data = st.date_input("Selecione o intervalo de tempo", [trinta_dias_atras.date(), hoje.date()],
                                help="Inicia com o período de 30 dias contado a partir da data atual. É necessário selecionar duas datas")

        'pesquisa por numero da nf'
        numero = st.number_input("Número da NF",step=1)

    nfs_localizadas = nf_controller.consulta_nf(cliente_selecionado, data, valor, numero)

    st.divider()    

    if nfs_localizadas:
        nf_radio = []
        '''O laço de repetição transforma o resultado em uma lista para que o st.radio possa recebê-la'''
        for item in nfs_localizadas:
            nf_radio.append(item)
        
        
        nf_selecionada = st.radio("Notas Fiscais encontradas", help="Clique na NF que deseja visualizar", 
                                options=nf_radio, format_func=formatar_nf, index=None)
        
        '''Caso alguma NF. seja selecionada o NUMERO dela vai para a url do app
        Esta é uma forma de burlar a limitação do streamlit que refaz a página a cada ação que é feita nela.
        Caso coloque um botão, ao clicar no botão para salvar os dados a chamada da função é refeita e perde-se o numero,
        por isso optei pela url que permanece mesmo após o rerun da página'''

        if nf_selecionada:
            nf = nf_controller.consulta_nf_por_id(nf_selecionada[0])
            
            fechamento = fechamento_controller.consulta_fechamento_por_nf(nf.numero)
            
            cliente = cliente_controller.consulta_cliente_por_id(fechamento.cliente)
            

            with st.container(border=True):
                st.header(f"Dados da nota fiscal nº {nf.numero}")
                st.write(f"Valor: {locale.currency(float(nf.valor), grouping=True)}")
                st.write(f"Data de emissão: {Formata.data(nf.data_emissao)}")
                st.write(f"Código de Verificação: {nf.cod_verificacao}")
                st.write(f"Fechamento de origem: Nº{fechamento.id} de {fechamento.data_formatada}")
                st.write(f"Cliente: {cliente.nome_fantasia} ({cliente.razao_social})")
                st.write(f"{cliente.tipo_cliente}: {cliente.documento}")
                
                st.divider()

                st.header("Downloads")
                col_nf, col_relatorio = st.columns(2)
                with col_nf:
                    arquivo_carregado = Arquivos.ler_arquivo(nf.arquivo)
                    tipo_arquivo,_ = mimetypes.guess_type(nf.arquivo)
                    nome_nf = Arquivos.nome_arquivo(nf.arquivo)
                    pdf_viewer(arquivo_carregado, 300)
                    st.download_button("Nota Fiscal", arquivo_carregado, nome_nf,
                                        mime=tipo_arquivo, key=f"download_{nome_nf}")
                
                with col_relatorio:
                    relatorio_detalhado = emitir_pdf_faturamento_detalhado(fechamento.id)
                    nome_relatorio = f'relatorio detalhado fechamento {fechamento.id}.pdf'
                    pdf_viewer(relatorio_detalhado.getvalue(), 300)
                    st.download_button("Relatório Detalhado", relatorio_detalhado, nome_relatorio,
                                        mime='application/pdf', key=f"download_{nome_relatorio}")
                    
              
            