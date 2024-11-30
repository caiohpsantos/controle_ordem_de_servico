import yaml
from yaml.loader import SafeLoader
import streamlit as st
import streamlit_authenticator as stauth
from streamlit_option_menu import option_menu
from forms import cliente, nova_os, editar_os, dados_os, fechamento, configuracoes, faturamento
from services.database import cria_tabelas

st.set_page_config(layout="wide", page_title="Gerenciamento O.S.", menu_items={"Get help":"mailto:caiohpsantos@gmail.com",
                                                                            "Report a bug": "https://forms.gle/44wLD4xNr4qzdmGq6",
                                                                            "About":"Sistema para gerenciamento de ordens de serviço."})

st.header("Sistema de Gerenciamento de Ordem de Serviço - O.S.")


with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

DIR_MIDIA_OS = config['pastas_midias']['midias_os']
DIR_MIDIA_NF = config['pastas_midias']['notas_fiscais']

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

if not st.session_state['authentication_status']:
    authenticator.login(fields = {'Form name':'Login', 'Username':'Usuário', 'Password':'Senha',
                      'Login':'Logar', 'Captcha':'Captcha'})


if st.session_state['authentication_status']:
    with st.sidebar:
            st.write(f'Bem-vindo *{st.session_state["name"]}*')
            authenticator.logout()


    if 'id_os' not in st.session_state:
        st.session_state['id_os'] = None

    with st.sidebar:
        selecionado = option_menu("Menu Principal",["Ordem de Serviço", "Clientes", "Fechamento", "Faturamento", "Relatórios", "Configurações"],
                                icons=['database','person','bi-bar-chart-steps','cash','bi-file-earmark-bar-graph','gear'])
        
    match selecionado:
        case "Clientes":
            acao = option_menu("Gestão de Clientes",["Cadastrar","Editar"], icons=['person-plus','person-gear'], orientation="horizontal")

            match acao:
                case 'Cadastrar':
                    st.query_params.clear()
                    cliente.cadastra_cliente()
                                

                case 'Editar':
                    st.query_params.clear()
                    cliente.edita_cliente()

        case "Ordem de Serviço":
            acao = option_menu("Gestão de Ordem de Serviço",["Dados", "Nova O.S.", "Editar O.S."], orientation="horizontal", 
                            icons=['activity', 'database-add','database-gear' ])
            match acao:
                case "Nova O.S.":
                    st.query_params.clear()
                    nova_os.nova_os()
                case "Editar O.S.":
                    st.query_params.id_os = None
                    editar_os.localizar_os()
                
                case "Dados":
                    st.query_params.clear()
                    dados_os.dados()

        case "Fechamento":
            acao = option_menu("Gestão de Fechamento", options=["Gerar", "Visualizar"], icons=["clipboard-plus-fill", "clipboard-check", "receipt-cutoff"], orientation="horizontal")
            
            match acao:
                case "Gerar":
                    st.query_params.clear()
                    fechamento.criar()

                case "Visualizar":
                    st.query_params.id_fechamento = None
                    fechamento.visualizar()
                
        case "Faturamento":
            acao = option_menu("Gestão de Faturamento", options=["Faturar", "NFs Lançadas"], icons=['receip-cutoff','file-earmark-break'], orientation='horizontal')

            match acao:
                case "Faturar":
                    faturamento.faturar()

                case "NFs Lançadas":
                    faturamento.pesquisa_nf()
        
        case "Relatórios":

            acao = option_menu('Relatórios disponíveis',["Financeiro", "Por Cliente", "Todos os Clientes"], icons=['cash-stack', 'file-earmark-person', ''],
                    orientation="horizontal")
            match acao:
                case "Financeiro":
                    pass
    
        case "Configurações":

            acao = option_menu('Gestão do Sistema', ['Trocar Senha', 'Dados Empresariais', 'Email', 'Pastas de Arquivos'], orientation='horizontal')

            match acao:
                case 'Trocar Senha':

                    # '''se houver usuário logado aciona o método resetar password para criar o formulário de reset de senha'''
                    if st.session_state['authentication_status']:
                        try:
                            if authenticator.reset_password(st.session_state['username'],fields={
                                'Form name':f'Trocar a senha de {st.session_state["name"]}',
                                'Current password':'Senha atual',
                                'New password':'Senha nova',
                                'Repeat password': 'Repita a senha nova',
                                'Reset':'Confirmar'
                            }):
                                with open('config.yaml', 'w') as file:
                                    yaml.dump(config, file, default_flow_style=False)
                                st.success('Senha alterada com sucesso')
                        except Exception as e:
                            st.error(e)
                    elif st.session_state['authentication_status'] is False:
                        st.error('Usuário ou senha incorreta. Tente novamente')
                    elif st.session_state['authentication_status'] is None:
                        st.warning('Faça o login para acessar o sistema')

                case 'Dados Empresariais':
                    configuracoes.dados_empresariais()

                case 'Email':
                    configuracoes.configurar_email()

                case 'Pastas de Arquivos':
                    configuracoes.pastas_de_midias()

elif st.session_state['authentication_status'] is False:
    st.error('Usuário ou senha incorretos')

elif st.session_state['authentication_status'] is None:
    st.warning('Digite seu usuário e senha para entrar')