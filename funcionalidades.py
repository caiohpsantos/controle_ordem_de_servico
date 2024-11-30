import re
import os
import requests
import streamlit as st
import mimetypes
from datetime import datetime

class Arquivos:

    '''Agrega todas as funções que lidam com arquivos do sistema'''
    
    def ler_arquivo(caminho):
        ''' Função para ler arquivos do disco e carregá-los para o ambiente de execução
        :param caminho: string com caminho completo do arquivo
        :return: o arquivo carregado'''
        with open(caminho, 'rb') as f:
            return f.read()
        
    def tipo_arquivo(caminho):
        '''Função para identificar o tipo do arquivo
        :param caminho: string com caminho completo do arquivo
        :return: String, tipo do arquivo padronizado pela biblioteca mimetypes'''
        tipo_mime, _ = mimetypes.guess_type(caminho)

        if tipo_mime:
            return tipo_mime
        else:
            return None
    
    def nome_arquivo(caminho):
        '''
        Identifica o nome do arquivo fornecido
        
        :param caminho: String, string com caminho completo do arquivo
        :return: String, nome do arquivo
        '''
        return os.path.basename(caminho)

class Pesquisa:
    '''Agrega todas as funções que fazem pesquisas externas usando APIs'''
    
    def cep(cep):
        """
        Pesquisa uma API para verificar se o CEP fornecido existe.

        :param cep: String contendo o CEP somente com números
        :return: booleando se o CEP existe ou não
        """
        resposta = requests.get(f"https://api.brasilaberto.com/v1/zipcode/{cep}")
        if resposta.status_code == 200:
                # data = resposta.json()
                # logradouro = data['result']['street']
                # bairro = data['result']['district']
                # cidade = data['result']['city']
                # estado = data['result']['state']
                # return(logradouro,bairro,cidade,estado)
            return True
                
        
        if resposta.status_code == 400:
            return False
        
        if resposta.status_code == 500:
            return True

class Formata:
    '''Agrega todas as funções que formatam as strings que recebem.\n
    Tanto para esterilizar a string(tirar pontuação) ou separar apenas os números'''

    def limpa_pontuacao(string):
        """
        Limpa a string recebida deixando apenas números

        :param string: String que chega com caracteres que não sejam números
        :return: string somente com os números que encontrou
        """
        try:
            numeros = ''.join(filter(str.isdigit,string))
            return numeros
        
        except:
            st.error("Os dados passados são inválidos")
    
    def cnpj(cnpj):
        """
        Formata o CNPJ no padrão ##.###.###/####-##

        :param cnpj: String contendo o cnpj com somente números
        :return: string com o CNPJ formatado
        """
        cnpj_formatado = f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
        return cnpj_formatado
    
    def cpf(cpf):
        '''
        Formata o CPF no padrão ###.###.###-##

        :param cpf: String contendo o cpf sem pontuação, somente números
        :return: string com o cpf formatado
        '''
        cpf_formatado = f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
        return cpf_formatado
    
    def telefone(telefone):
        """
        Formata um número de telefone no formato (xx)xxxxx-xxxx para 11 dígitos
        ou (xx)xxxx-xxxx para 10 dígitos.

        :param numero: String contendo o número de telefone a ser formatado
        :return: String formatada no padrão desejado
        """
        if len(telefone) == 11:
            return f"({telefone[:2]}){telefone[2:7]}-{telefone[7:]}"
        
        if len(telefone) == 10:
            return f"({telefone[:2]}){telefone[2:6]}-{telefone[6:]}"
        
    def cep(cep):
        """
        Formata um número de cep no formato xx.xxx-000.

        :param numero: String contendo o número de cepa ser formatado
        :return: String formatada no padrão desejado
        """
        return f"{cep[:2]}.{cep[2:5]}-{cep[5:]}"
    
    def data(data):
        return data.strftime('%d/%m/%Y')
    
class Valida:
    '''Agrega todas as funções que validam dados'''

    def calcular_digito(cnpj, posicoes):
        """
        Calcula o dígito verificador do CNPJ fornecido junto com uma lista de posições que devem ser usadas para o cálculo.

        :param cnpj: String contendo o CNPJ somente com números
        :param posicoes: Objeto iterável que contém as posições que devem ser usadas para o cálculo
        :return: 0 se o resto for menor que 2 senão o resultado da subtração entre 11 e o resto da soma usando o cnpj e as posições
        """
        soma = sum([int(cnpj[i]) * posicoes[i] for i in range(len(posicoes))])
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto
    
    def cnpj(cnpj, emite_msg_erro = True):
        """
        Valida o cnpj recebido para saber se possui a qtde correta de dígitos e se é válido

        :param cnpj: String, CNPJ que precisa ser validado, pode ou nao vir com pontuação
        :param emite_msg_erro: Boolean, flag que habilita mensagens de erro da função. Padrão: True
        :return: mensagem de erro caso o cnpj fornecido seja muito curto ou muito longo e 
        booleano indicando se o CNPJ fornecido é válido
        """
        try:
            cnpj_limpo = Formata.limpa_pontuacao(cnpj)
            if len(str(cnpj_limpo)) > 0 and len(str(cnpj_limpo)) < 14 and emite_msg_erro == True:
                st.error("O CNPJ possui menos de 14 dígitos.")
                return False
            if len(str(cnpj_limpo)) > 14 and emite_msg_erro == True:
                st.error("O CNPJ possui mais de 14 dígitos.")
                return False
            # Posições para o cálculo dos dígitos verificadores
            posicoes_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
            posicoes_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

            # Calcula os dígitos verificadores
            digito1 = Valida.calcular_digito(str(cnpj_limpo)[:12], posicoes_1)
            digito2 = Valida.calcular_digito(str(cnpj_limpo)[:12] + str(digito1), posicoes_2)

            # Verifica se os dígitos calculados conferem com os dígitos fornecidos
            return str(cnpj_limpo)[-2:] == f'{digito1}{digito2}'
        except:
            return False
    
    def cpf(cpf):
        '''
        Valida um CPF. O CPF deve ser uma string com 11 dígitos ou formatado como ###.###.###-XX.

        :param cpf: CPF a ser validado
        :return: True se o CPF for válido, False caso contrário
        '''
        # Remover pontuação (se houver)
        cpf_fornecido = Formata.limpa_pontuacao(cpf)

        # Verificar se o CPF tem 11 dígitos ou se é uma sequência repetida
        if len(cpf_fornecido) != 11 or cpf_fornecido == cpf_fornecido[0] * 11:
            return False

        # Função auxiliar para calcular o dígito verificador
        def calcula_digito(cpf_parcial):
            soma = 0
            for i, j in enumerate(range(len(cpf_parcial) + 1, 1, -1)):
                soma += int(cpf_parcial[i]) * j
            resto = soma % 11
            return '0' if resto < 2 else str(11 - resto)

        # Validar o primeiro dígito verificador
        primeiro_digito = calcula_digito(cpf_fornecido[:9])
        if cpf_fornecido[9] != primeiro_digito:
            return False

        # Validar o segundo dígito verificador
        segundo_digito = calcula_digito(cpf_fornecido[:10])
        if cpf_fornecido[10] != segundo_digito:
            return False

        return True

    def telefone(telefone):
        """
        Verifica se o telefone fornecido tem a qtde correta de caracteres

        :param telefone: String contendo o telefone pode ou não vir com pontuação
        :return: Boolean + mensagem especificando o erro encontrado caso haja algum
        """
        telefone_limpo = Formata.limpa_pontuacao(telefone)

        if str(telefone_limpo)[0] == '0':
            st.error("O código de área deve ter apenas 2 dígitos. Retire o 0.")
            return False

        if len(str(telefone_limpo)) < 10:
            st.error("Telefone fornecido está muito curto. Lembre-se de adicionar o código de área com 2 dígitos.")
            return False
        
        if len(str(telefone_limpo)) > 11:
            st.error("Telefone fornecido está muito longo. Lembre-se que o código de área deve ter apenas 2 dígitos.")
            return False
        
        if len(str(telefone_limpo)) == 10 and str(telefone_limpo)[2] == '9':
            st.error("Telefones fixos não começam com 9, verifique se digitou corretamente  ")
            return False
        
        if len(str(telefone_limpo)) == 11 and str(telefone_limpo)[2] != '9':
            st.error("Telefones celulares começam com 9, verifique se digitou corretamente")
            return False
        else:
            return True
    
    def email(email):
        """
        Valida um endereço de e-mail.

        :param email: String contendo o e-mail a ser validado
        :return: Booleano indicando se o e-mail é válido
        """
        # Expressão regular para validar e-mails
        regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        
        # Usar a expressão regular para verificar o e-mail
        if re.match(regex, email):
            return True
        else:
            return False
        
    def cep(cep):
        """
        Valida um cep fornecido conferindo se a qtde se caracteres está correta.
        Depois pesquisa o cep na API para verificar se ele existe.
        Por limitação do streamlit, não foi implementada a atribuição dos dados diretamente nos campos.

        :param email: String contendo o cdp a ser validado
        :return: Booleano indicando se o cep é válido
        """
        cep_limpo = Formata.limpa_pontuacao(cep)
        if len(cep_limpo) < 8:
            st.error("CEP digitado é muito curto")
            return False

        if len(cep_limpo) > 8:
            st.error("CEP digitado é muito longo.")
            return False

        # if not Pesquisa.cep(cep_limpo):
        #     st.error("O CEP digitado não existe")
        #     return False
        else:
            return True
        