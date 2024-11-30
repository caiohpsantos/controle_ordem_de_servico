import yaml
import os
from yaml.loader import SafeLoader
import streamlit as st
import streamlit_authenticator as stauth
from funcionalidades import Valida, Formata
from services.email import testa_servidor


def dados_empresariais():
    '''carrega o arquivo de configuracao'''
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)

    st.header("Dados empresariais")

    '''cria um formulário que expõe os dados empresariais para edição, atribuindo os dados
    pré-existentes aos seus respectivos campos'''
    with st.form('formulario_dados_empresariais'):
        cnpj = st.text_input('CNPJ', config['dados_empresariais']['cnpj'])
        razao_social = st.text_input('Razão Social', config['dados_empresariais']['razao_social'])
        nome_fantasia = st.text_input('Nome Fantasia', config['dados_empresariais']['nome_fantasia'])
        inscricao_estadual = st.text_input('Inscrição Estadual', config['dados_empresariais']['inscricao_estadual'], max_chars=9)
        endereco = st.text_input('Endereço Completo', config['dados_empresariais']['endereco'])
        telefone_fixo = st.text_input('Telefone Fixo', config['dados_empresariais']['telefone_fixo'])
        telefone_celular = st.text_input('Telefone Celular', config['dados_empresariais']['telefone_celular'])
        email = st.text_input('Email', config['dados_empresariais']['email'])
        gravar = st.form_submit_button("Salvar alterações")

    '''Caso o usuário clique no botão Gravar começam os testes para validar os dados fornecidos
    Caso alguma validação dê errado a variável de controle 'problema' recebe True, o que impede que a gravaçao
    dos dados incorretos ocorra'''
    if gravar:
        problema = False
        '''valida o cnpj fornecido'''
        if not Valida.cnpj(cnpj):
            st.error("Novo CNPJ é inválido")
            problema = True
        '''valida o telefone fixo e o celular fornecido'''
        if not Valida.telefone(telefone_fixo):
            problema = True
            st.error("Telefone fixo é inválido")

        if not Valida.telefone(telefone_celular):
            problema = True
            st.error("Telefone celular é inválido")
        '''valida o email fornecido'''
        if not Valida.email(email):
            st.error("Email fornecido é inválido")
            problema = True
        
        '''caso não haja problemas, inicia a atribuição dos novos valores à instancia do arquivo de configuração
        e salva logo depois'''
        if problema == False:
            '''altera o dicionário com os dados digitados'''
            config['dados_empresariais']['cnpj'] = cnpj
            config['dados_empresariais']['razao_social'] = razao_social
            config['dados_empresariais']['nome_fantasia'] = nome_fantasia
            config['dados_empresariais']['inscricao_estadual'] = inscricao_estadual
            config['dados_empresariais']['endereco'] = endereco
            config['dados_empresariais']['email'] = email
            config['dados_empresariais']['telefone_fixo'] = telefone_fixo
            config['dados_empresariais']['telefone_celular'] = telefone_celular

            with open('config.yaml', 'w') as file:
                config = yaml.dump(config, file, default_flow_style=False)
            st.success("Dados empresariais alterados com sucesso.")

def configurar_email():

    '''carrega o arquivo de configuração'''
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)
    
    '''Gera um formulário e expõe os dados gravados para envio de emails'''
    with st.form('dados_email'):

        st.write("Dados para login")

        email = st.text_input("Email", config['dados_email']['email'])

        senha_email = st.text_input("Senha", config['dados_email']['senha'], type='password')
        
        st.divider()

        st.write("Dados do servidor")
        servidor = st.text_input("Endereço Servidor", config['dados_email']['servidor'])
    
        gravar = st.form_submit_button('Gravar Alterações')
    '''Caso o usuário clique no botão Gravar começam os testes para validar os dados fornecidos
    Caso alguma validação dê errado a variável de controle 'problema' recebe True, o que impede que a gravaçao
    dos dados incorretos ocorra'''
    if gravar:
        problema = False
        '''testa se o servidor está correto'''
        if not testa_servidor(servidor, 587):
            problema = True
        '''testa se todos os campos foram preenchidos'''
        if not email and senha_email and servidor:
            problema = True
            st.error("Todos os dados são obrigatórios. Preencha todos os campos.")
        '''valida se o email fornecido é um email válido'''
        if not Valida.email(email):
            problema = True
            st.error("Email inválido, verifique se não falta algo: um @ ou o domínio (gmail.com, outlook.com.br...)")
        '''caso não haja problemas, inicia a atribuição dos novos valores à instancia do arquivo de configuração
        e salva logo depois'''
        if problema == False:
            config['dados_email']['email'] = email
            config['dados_email']['senha'] = senha_email
            config['dados_email']['servidor'] = servidor


            with open('config.yaml', 'w') as file:
                config = yaml.dump(config, file, default_flow_style=False)
            st.success("Dados para envio de emails alterados com sucesso.")

def pastas_de_midias():
    
    '''carrega o arquivo de configuração'''
    with open('config.yaml') as file:
        config = yaml.load(file, Loader=SafeLoader)
    '''Gera um formulário e expõe os caminhos completos das pastas que recebem os arquivos de midia'''
    with st.form("pastas_midias"):

        st.write("Informe o caminho das pastas de mídias")
        st.caption('''Caso altere as pastas, as mídias já salvas ficarão com o caminho de acesso inválido. Elas ainda vão existir na pasta antiga mas estarão inacessíveis pelo sistema.
         Caso necessário, é possível editar a o.s., apagando o arquivo inválido e acrescentar o arquivo manualmente.''')
         
        pasta_midias = st.text_input("Insira o caminho completo da pasta de midias das ordens de serviço", value=config['pastas_midias']['midias_os'])
        pasta_notas_fiscais = st.text_input("Insira o caminho completo da pasta de midias das notas fiscais", value=config['pastas_midias']['notas_fiscais'])

        gravar = st.form_submit_button("Gravar Alterações")

        '''Caso o usuário clique no botão Gravar começam os testes para validar os dados fornecidos
        Caso alguma validação dê errado a variável de controle 'problema' recebe True, o que impede que a gravaçao
        dos dados incorretos ocorra'''
        if gravar:
            problema = False

            '''verifica se as pastas existem e caso negativo retorna um erro informando e muda a 'problema' para verdadeiro'''
            if not os.path.exists(pasta_midias):
                st.error("Caminho fornecido para a pasta de midias das Ordens de Serviço é inválido. Verifique se foi digitado corretamente ou se as pastas existem")
                problema = True

            if not os.path.exists(pasta_notas_fiscais):
                st.error("Caminho fornecido para a pasta de midias das Notas Fiscais é inválido. Verifique se foir digitado corretamente ou se as pastas existem")
                problema = True

            '''caso não haja problemas, inicia a atribuição dos novos valores à instancia do arquivo de configuração
            e salva logo depois'''
            if problema == False:
                config['pastas_midias']['midias_os'] = pasta_midias
                config['pastas_midias']['notas_fiscais'] = pasta_notas_fiscais

                with open('config.yaml', 'w') as file:
                    config = yaml.dump(config, file, default_flow_style=False)
                
                st.success("Pastas de midias foram alteradas com sucesso.")

            


