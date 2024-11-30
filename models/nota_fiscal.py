class Nota_Fiscal():
    def __init__(self, data_emissao, valor, arquivo, cod_verificacao, numero_nota=None):
        self.numero = numero_nota
        self.data_emissao = data_emissao
        self.valor = valor
        self.arquivo = arquivo
        self.cod_verificacao = cod_verificacao

        def __str__(self):
            return self.numero_nota
        