class Cliente:
    def __init__(self, ativo, tipo_cliente, documento, razao_social, nome_fantasia, inscricao_estadual,
                 telefone, email, logradouro, numero, complemento, bairro, cidade, cep, id=None):
        self.id = id
        self.ativo = ativo
        #dados fiscais
        self.tipo_cliente = tipo_cliente
        self.documento = documento
        self.razao_social = razao_social
        self.nome_fantasia = nome_fantasia
        self.inscricao_estadual = inscricao_estadual
        #dados contato
        self.telefone = telefone
        self.email = email
        #dados endereço
        self.cep = cep
        self.logradouro = logradouro
        self.numero = numero
        self.complemento = complemento
        self.bairro = bairro
        self.cidade = cidade

    def __str__(self):
        return f'{self.nome_fantasia}'
    
    @property
    def endereco_completo(self):
        return f"{self.logradouro}, {self.numero}, {self.complemento}, {self.bairro}, {self.cidade}, CEP: {self.cep}"
