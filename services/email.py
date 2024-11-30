import io
import os
import ssl
import yaml
import smtplib
import streamlit as st
from email.message import EmailMessage
from yaml.loader import SafeLoader
from funcionalidades import Formata
from controllers.nf_controller import consulta_nf_por_id
from controllers.fechamento_controller import consulta_data_mais_antiga_e_mais_recente

'Recuperar dados de envio do email do arquivo de configuração'
with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

def testa_servidor(servidor, porta):
    '''Verifica se o servidor fornecido existe tentando uma conexão e enviando um ehlo(assim mesmo que escreve)
    para o servidor
    
    :param servidor: String, endereço web do servidor de email smtp,
    :param porta: Integer, porta de acesso usada para servidores smtp, constante 587
    :return: Boolean, Verdadeiro caso consiga conexão com ehlo ou False caso aconteça algum erro. Além disso 
    retorna mensagem personalizada caso o endereço esteja errado, se ocorrer erro por outro motivo mostra mensagem especificando o erro.'''
    try:
        'inicia conexao'
        with smtplib.SMTP(servidor, porta, timeout=5) as conexao:
            conexao.starttls()
            conexao.ehlo()
        return True

    except smtplib.SMTPConnectError:
        st.error(f"Não foi possível conectar ao servidor {servidor}. Verifique se está correto.")
    except Exception as e:
        st.error(f"Erro ao tentar conectar: {e}")
    return False    

def cria_mensagem_nova_os(id_os, cliente, data, descricao, valor):
    '''Monta dinamicante a mensagem de email quando uma nova ordem de serviço é registrada.
    
    :param id_os: Integer, número da ordem de serviço recém registrada
    :param cliente: String, nome do cliente que receberá o email conforme cadastro no sistema
    :param data: String, data formatada no formato DD/MM/AAAA
    :param descricao: String, texto descritivo do serviço prestado
    :param valor: String, valor formatado em reais para exibição
    '''
    return f'''<!DOCTYPE html>
                            <html lang="pt-br">
                            <head>
                                <meta charset="UTF-8">
                                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                                <title>Nova Ordem de Serviço nº {id_os}</title>
                                <style>
                                    body {{
                                        font-family: Arial, sans-serif;
                                        color: #333;
                                        line-height: 1.6;
                                    }}
                                    .container {{
                                        width: 80%;
                                        margin: 0 auto;
                                    }}
                                    h1 {{
                                        color: #007BFF;
                                    }}
                                    p {{
                                        font-size: 16px;
                                    }}
                                    .order-details {{
                                        background-color: #f9f9f9;
                                        padding: 10px;
                                        border: 1px solid #ddd;
                                        margin-bottom: 20px;
                                    }}
                                    .footer {{
                                        margin-top: 20px;
                                        font-size: 14px;
                                        color: #555;
                                    }}
                                    .footer a {{
                                        color: #007BFF;
                                        text-decoration: none;
                                    }}
                                </style>
                            </head>
                            <body>
                                <div class="container">
                                    <h1>Confirmação de Nova Ordem de Serviço = {id_os}</h1>
                                    
                                    <p>Prezado(a) <strong>{cliente}</strong>,</p>
                                    
                                    <p>Esperamos que esta mensagem o(a) encontre bem.</p>
                                    
                                    <p>Gostaríamos de informá-lo(a) que uma nova Ordem de Serviço foi registrada em nosso sistema com os seguintes detalhes:</p>

                                    <div class="order-details">
                                        <p><strong>Número da O.S.:</strong> {id_os}</p>
                                        <p><strong>Data de Registro:</strong> {data}</p>
                                        <p><strong>Descrição do Serviço:</strong> {descricao}</p>
                                        <p><strong>Valor:</strong> {valor}</p>
                                    </div>

                                    
                                    <p>Se houver qualquer dúvida ou necessidade de ajustes, por favor, entre em contato conosco:</p>
                                    
                                    <p><strong>Telefone Celular:</strong> {config['dados_empresariais']['telefone_celular']} <br>
                                    
                                    <strong>E-mail:</strong> <a href="mailto:{config['dados_empresariais']['email']}">{config['dados_empresariais']['email']}</a></p>

                                    <div class="footer">
                                        <p>Atenciosamente,</p>
                                        <p><strong>{st.session_state["name"]}</strong><br>
                                        {config['dados_empresariais']['nome_fantasia']}</p>
                                    </div>
                                </div>
                            </body>
                            </html>
                            '''

def cria_mensagem_nova_nf(nf, fechamento, cliente):
    '''
    Recebe as models de nota fiscal, fechamento e cliente e usa esses dados para montar o corpo do email de aviso de emissão de nota para o cliente

    Parameters
    ----------
    :param nf: Nota_Fiscal, objeto instanciado da model Nota_Fiscal contendo os dados da nota fiscal fornecida
    :param fechamento: Fechamento, objeto instanciado da model Fechamento contendo os dados do fechamento fornecido
    :param cliente: Cliente, objeto instanciado da model Cliente contendo os dados do cliente fornecido

    Return
    ----------
    :return: String, string formatada para formar um html com os dados da nota
    '''
    data_mais_antiga, data_mais_recente = fechamento.data_mais_antiga_e_mais_recente
    msg = f'''<!DOCTYPE html>
            <html lang="pt-BR">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Nota Fiscal Emitida</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        color: #333;
                        background-color: #f9f9f9;
                        margin: 0;
                        padding: 20px;
                    }}
                    .container {{
                        background-color: #ffffff;
                        border: 1px solid #dddddd;
                        border-radius: 8px;
                        padding: 20px;
                        max-width: 600px;
                        margin: 0 auto;
                    }}
                    .header {{
                        background-color: #4CAF50;
                        padding: 10px;
                        text-align: center;
                        color: white;
                        border-radius: 8px 8px 0 0;
                    }}
                    .content {{
                        margin-top: 20px;
                        line-height: 1.6;
                    }}
                    .footer {{
                        margin-top: 20px;
                        font-size: 12px;
                        color: #666;
                        text-align: center;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>Nota Fiscal Emitida</h2>
                    </div>
                    <div class="content">
                        <p>Prezado(a) <strong>{cliente.nome_fantasia}</strong>,</p>
                        
                        <p>Informamos que sua <strong>Nota Fiscal de Serviço</strong> foi emitida com sucesso referente aos serviços prestados pela nossa empresa
                            no período de {data_mais_antiga} a {data_mais_recente}. Totalizando {fechamento.qtde_dias} dias.</p>

                        <p><strong>Dados da Nota Fiscal:</strong></p>
                        <ul>
                            <li><strong>Número da Nota:</strong> {nf.numero}</li>
                            <li><strong>Data de Emissão:</strong> {Formata.data(nf.data_emissao)}</li>
                            <li><strong>Valor Total:</strong> R$ {nf.valor}</li>
                        </ul>

                        <p>A nota fiscal está disponível em anexo neste email. Caso deseje, pode consultar sua autencidade
                            no site da Prefeitura no link abaixo. O código para validação é: {nf.cod_verificacao}</p>

                        <p><a href="http://gestaopublica.neropolis.bsit-br.com.br/nfse/nfse-validation.jsf" style="color: #4CAF50;">Validar Nota Fiscal</a></p>

                        <p>Se houver qualquer dúvida ou precisar de mais informações, não hesite em nos contatar.</p>

                        <p>Agradecemos pela sua confiança em nossos serviços!</p>

                        <p>Atenciosamente,</p>
                        <p><strong>{config['dados_empresariais']['nome_fantasia']}</strong></p>
                    </div>
                    <div class="footer">
                        <p>{config['dados_empresariais']['razao_social']} - {config['dados_empresariais']['endereco']}</p>
                        <p>Email: {config['dados_empresariais']['email']} | Telefone: {config['dados_empresariais']['telefone_celular']}</p>
                    </div>
                </div>
            </body>
            </html>

            '''
    return msg

def envia_email(destinatario, assunto, mensagem, anexos, nome_arquivos):
    '''Enviar email para o destinatario informado
    
    :param destinatario: String, endereço de email do destinatario
    :param assunto: String, campo assunto do email
    :param mensagem: String, corpo do email contendo o texto que será exibido
    :param anexos: Lista de objetos BytesIO, contendo os arquivos que serão anexados ao email
    :param nome_arquivos: Lista de Strings, contendo o nome dos arquivos que serão anexados
    :return: Toast avisando que o email foi enviado com sucesso ou mensagem de erro especificando o que aconteceu'''

    endereco_email = config['dados_email']['email']
    senha = config['dados_email']['senha']
    servidor = config['dados_email']['servidor']
    
    # Instancia a classe EmailMessage e formata o email com os dados de envio
    email = EmailMessage()
    email['From'] = endereco_email
    email['To'] = destinatario
    email['Subject'] = assunto
    email.set_content(mensagem, subtype='html')

    # Adicionar anexos
    
    for anexo, nome_arquivo in zip(anexos, nome_arquivos):
        
        if isinstance(anexo, io.BytesIO):  # Verifica se é um arquivo gerado em memória
            anexo.seek(0)  # Garante que a leitura do BytesIO comece do início
            email.add_attachment(
                anexo.read(),
                maintype='application',
                subtype='pdf',
                filename=nome_arquivo  # Nome do arquivo anexo
            )

    # Envio do e-mail via servidor SMTP
    try:
        contexto_ssl = ssl.create_default_context()
        with smtplib.SMTP(servidor, 587) as envio:  # Porta 587 para TLS
            envio.starttls(context=contexto_ssl)
            envio.login(endereco_email, senha)
            envio.send_message(email)
            st.toast(f"Email enviado com sucesso para {destinatario}")
    
    except smtplib.SMTPAuthenticationError:
        st.error("Erro de autenticação. Verifique o e-mail e a senha fornecidos.")
    
    except smtplib.SMTPConnectError:
        st.error("Erro ao tentar se conectar ao servidor SMTP. Verifique o servidor e a porta.")
    
    except smtplib.SMTPRecipientsRefused:
        st.error(f"Destinatário {destinatario} recusado. Verifique o endereço de e-mail.")
    
    except FileNotFoundError as e:
        st.error(f"Arquivo anexado não encontrado: {e}")
    
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao enviar o e-mail: {e}")



