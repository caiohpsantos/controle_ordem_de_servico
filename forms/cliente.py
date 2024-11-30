import streamlit as st
import datetime
from streamlit_option_menu import option_menu
from models.cliente import Cliente
import controllers.cliente_controller as cliente_controller
from funcionalidades import Formata, Valida

def cadastra_cliente():
    st.query_params.clear()
    with st.form("cadastro_cliente"):

        st.caption("Digite nos campos as informações solicitadas")
        
        st.divider()
        
        '''Cria os campos para receber as informaçoes necessárias'''

        st.subheader("Informações fiscais")
        st.caption("Campos com * são obrigatórios, quando for opcional está escrito no campo")
        
        tipo_cliente = st.radio("Escolha o tipo de cliente",["Pessoa Física", "Pessoa Jurídica"], horizontal=True, index=1)
        
        documento = Formata.limpa_pontuacao(st.text_input("CPF/CNPJ *", placeholder="Somente números, sem pontos ( . ) e hífens ( - )", key="documento"))
        
        razao_social = st.text_input("Razão Social/Nome Completo *", key="razao_social").upper()

        nome_fantasia = st.text_input("Nome Fantasia/Apelido/Primeiro Nome   *", key="nome_fantasia").upper()
                            
        inscricao_estadual = st.text_input("Inscrição Estadual *",  key="ie", max_chars=9)
        
        st.divider()

        st.subheader("Informações de contato")

        telefone = st.text_input("Telefone *", placeholder="Só números. No formato: XX-XXXXX-XXXX", max_chars=11)

        email = st.text_input("Email *", placeholder="Não esquecer do @ e o domínio no final (gmail.com, hotmail.com.br, etc...)").lower()

        st.divider()

        st.subheader("Endereço")

        logradouro = st.text_input("Logradouro *", help="Escreva se é rua, avenida, viela, rodovia... e o nome. Exemplo Avenida Anhanguera, Rua C-131").upper()

        col_num, col_complem = st.columns(2)
        with col_num:
            numero = st.text_input("Número *", placeholder="Se não houver número escreva 0")
        
        with col_complem:
            complemento = st.text_input("Complemento", placeholder="opcional").upper()

        col_bairro, col_cidade = st.columns(2)
        with col_bairro:
            bairro = st.text_input("Bairro *").upper()
        with col_cidade:
            cidade = st.text_input("Cidade *").upper()

        cep = st.text_input("CEP *", placeholder="Somente números. Sem ponto (.) ou hífen (-)", key="cep", max_chars=8)

        
        gravar = st.form_submit_button("Cadastrar")
        '''Caso o botão Cadastrar seja apertado começam as verificações dos campos,
        qualquer problema muda o status da variável problema para True, impedindo o andamento
        do código para atribuição de valores na model Cliente e posterior gravação.'''

        if gravar:

            #Verifica se nenhum campo obrigatório ficou vazio

            if not documento or not razao_social or not nome_fantasia or not inscricao_estadual or not telefone or not email or not logradouro or not numero or not bairro or not cidade or not cep:
                st.error("Algum campo obrigatório ficou em branco. Verifique acima")

            else:
                '''Inicia a verificação por cada campo, usa a variável 'problema'   
                para parar a execução do código caso algum seja encontrado,
                impedindo a instanciação da model Cliente'''

                problema = False
                
                '''Verificações do cnpj'''
                if documento and tipo_cliente == "Pessoa Jurídica":
                    cnpj_limpo = Formata.limpa_pontuacao(documento)
                    if not Valida.cnpj(cnpj_limpo):
                        st.error("O CNPJ digitado é inválido.")
                        problema = True
                    if cliente_controller.consulta_se_cliente_existe(Formata.cnpj(cnpj_limpo), razao_social,nome_fantasia):
                        st.error("Este cliente já está cadastrado")
                        problema = True

                '''Verificações do cpf'''
                if documento and tipo_cliente == "Pessoa Física":
                    if not Valida.cpf(documento):
                            st.error("O CPF digitado é inválido.")
                            problema = True
                    if cliente_controller.consulta_se_cliente_existe(Formata.cpf(documento), razao_social, nome_fantasia):
                        st.error("Esse cliente já está cadastrado")
                        problema = True


                '''Verificaçoes da inscrição estadual'''
                if not inscricao_estadual.isdigit():
                    st.error("Inscrição Estadual possui apenas números")
                    problema = True
                    
                if len(inscricao_estadual) != 9:
                    st.error("Inscrição Estadual têm de ter 9 dígitos")
                    problema = True

                '''Verificações do telefone'''
                if not Valida.telefone(telefone):
                    problema = True

                '''Verificações do email'''
                if not Valida.email(email):
                    st.error("Email fornecido é inválido.")
                    problema = True
                
                '''Verificações do número do endereço'''
                if not numero.isdigit():
                    st.error("O número do endereço só pode conter números")
                    problema = True

                '''Verificações do cep'''
                if not Valida.cep(cep):
                    problema = True

                '''Após verificações terminarem e a variável problema continuar False,
                os valores são atribuídos a model Cliente e o controller é chamado para gravar no banco de dados.'''
            
                if not problema:
                    if tipo_cliente == "Pessoa Física":
                        documento = Formata.cpf(documento)
                    
                    if tipo_cliente == "Pessoa Jurídica":
                        documento = Formata.cnpj(documento)

                    cliente_atual = Cliente(1,tipo_cliente, documento,razao_social,nome_fantasia,
                                            inscricao_estadual,Formata.telefone(telefone),email,logradouro,
                                            numero,complemento,bairro,cidade,Formata.cep(cep))

                    cliente_controller.adicionar_cliente(cliente_atual)
                    st.toast(f"Cliente {cliente_atual} foi cadastrado com sucesso")

def edita_cliente():

    col1, col2 = st.columns(2)
    resultado_consulta = cliente_controller.consulta_todos_clientes_e_retorna_os_nomes_fantasia()
    lista_exibicao = ['']+[nome[0] for nome in resultado_consulta]
    nome_selecionado = col1.selectbox("Escolha o cliente para editar", lista_exibicao)
    if nome_selecionado:
                    cliente_selecionado = cliente_controller.consulta_cliente_por_nome_fantasia(nome_selecionado)
                    
                    with st.form("cadastro_cliente"):

                        st.caption("Digite nos campos as informações que deseja alterar")
                        
                        st.divider()

                        
                        '''Cria os campos para receber as informaçoes necessárias'''
                        opcao = "Ativo" if cliente_selecionado.ativo == 1 else "Desativado"
                        marcacao = True if cliente_selecionado.ativo == 1 else False
                        cliente_selecionado.ativo = st.checkbox(opcao, marcacao, help="Ao deixar a caixa desmarcada esse cliente não aparecerá na tela para Criar O.S.")

                        st.subheader("Informações fiscais")
                        st.caption("Campos com * são obrigatórios, quando for opcional está escrito no campo")
                        
                        index_tipo = 0 if cliente_selecionado.tipo_cliente == "Pessoa Física" else 1
                        cliente_selecionado.tipo_cliente = st.radio("Tipo do cliente", ["Pessoa Física", "Pessoa Jurídica"], index=index_tipo)

                        cliente_selecionado.documento = st.text_input("CPF/CNPJ *", placeholder="Somente números, sem pontos ( . ), barras ( / ) e hífens ( - )",
                                            key="cnpj", max_chars=14, value=cliente_selecionado.documento)
                        
                        cliente_selecionado.razao_social = st.text_input("Razão Social *", key="razao_social", value=cliente_selecionado.razao_social).upper()

                        cliente_selecionado.nome_fantasia = st.text_input("Nome Fantasia *", key="nome_fantasia", value=cliente_selecionado.nome_fantasia).upper()
                                        
                        cliente_selecionado.inscricao_estadual = st.text_input("Inscrição Estadual *",  key="ie", max_chars=9, value=cliente_selecionado.inscricao_estadual)
                        

                        st.divider()

                        st.subheader("Informações de contato")

                        cliente_selecionado.telefone = st.text_input("Telefone *", placeholder="Só números. No formato: XX-XXXXX-XXXX", max_chars=11, value=cliente_selecionado.telefone)

                        cliente_selecionado.email = st.text_input("Email *", placeholder="Não esquecer do @ e o domínio no final (gmail.com, hotmail.com.br, etc...)",
                                              value=cliente_selecionado.email).lower()

                        st.divider()

                        st.subheader("Endereço")

                        cliente_selecionado.logradouro = st.text_input("Logradouro *", help="Escreva se é rua, avenida, viela, rodovia... e o nome. Exemplo Avenida Anhanguera, Rua C-131",
                                                   value=cliente_selecionado.logradouro).upper()

                        col_num, col_complem = st.columns(2)
                        with col_num:
                            cliente_selecionado.numero = st.text_input("Número *", placeholder="Se não houver número escreva 0", value=cliente_selecionado.numero)
                        
                        with col_complem:
                            cliente_selecionado.complemento = st.text_input("Complemento", placeholder="opcional", value=cliente_selecionado.complemento).upper()

                        col_bairro, col_cidade = st.columns(2)
                        
                        with col_bairro:
                            cliente_selecionado.bairro = st.text_input("Bairro *", value=cliente_selecionado.bairro).upper()
                        
                        with col_cidade:
                            cliente_selecionado.cidade = st.text_input("Cidade *", value=cliente_selecionado.cidade).upper()

                        cliente_selecionado.cep = st.text_input("CEP *", placeholder="Somente números. Sem ponto (.) ou hífen (-)", key="cep", max_chars=8, value=cliente_selecionado.cep)

                        gravar = st.form_submit_button("Gravar Alterações")

                        if gravar:
                            #Verifica se nenhum campo obrigatório ficou vazio

                            if not cliente_selecionado.documento or not cliente_selecionado.razao_social or not cliente_selecionado.nome_fantasia or not cliente_selecionado.inscricao_estadual or not cliente_selecionado.telefone or not cliente_selecionado.email or not cliente_selecionado.logradouro or not cliente_selecionado.numero or not cliente_selecionado.bairro or not cliente_selecionado.cidade or not cliente_selecionado.cep:
                                st.error("Algum campo obrigatório ficou em branco. Verifique acima")
                            
                            else:

                                '''Inicia a verificação por cada campo, usa a variável 'problema'   
                                    para parar a execução do código caso algum seja encontrado,
                                    impedindo a instanciação da model Cliente'''
                                    
                                problema = False
                                '''Verificações do cnpj'''
                                if cliente_selecionado.documento and cliente_selecionado.tipo_cliente == "Pessoa Jurídica":
                                    cnpj_limpo = Formata.limpa_pontuacao(cliente_selecionado.cnpj)
                                    if not Valida.cnpj(cnpj_limpo):
                                        st.error("Novo CNPJ não é válido.")
                                        problema = True
                                
                                if cliente_selecionado.documento and cliente_selecionado.tipo_cliente == "Pessoa Física":
                                    if not Valida.cpf(cliente_selecionado.documento):
                                        st.error("Novo CPF digitado é inválido.")
                                        problema = True
                                    
                        
                                '''Verificaçoes da inscrição estadual'''
                                if not cliente_selecionado.inscricao_estadual.isdigit():
                                    st.error("Inscrição Estadual possui apenas números")
                                    problema = True
                                    
                                if len(cliente_selecionado.inscricao_estadual) != 9:
                                    st.error("Inscrição Estadual têm de ter 9 dígitos")
                                    problema = True

                                '''Verificações do telefone'''
                                if not Valida.telefone(cliente_selecionado.telefone):
                                    problema = True

                                '''Verificações do email'''
                                if not Valida.email(cliente_selecionado.email):
                                    st.error("Email fornecido é inválido.")
                                    problema = True
                                
                                '''Verificações do número do endereço'''
                                if not cliente_selecionado.numero.isdigit():
                                    st.error("O número do endereço só pode conter números")
                                    problema = True

                                '''Verificações do cep'''
                                if not Valida.cep(cliente_selecionado.cep):
                                    problema = True

                                '''Após verificações terminarem e a variável problema continuar False,
                                os valores são atribuídos a model Cliente e o controller é chamado para gravar no banco de dados.'''
                            
                                if not problema:
                                
                                    cliente_controller.editar_cliente(cliente_selecionado)
                                    st.toast(f"Cliente {cliente_selecionado} foi alterado com sucesso")                              