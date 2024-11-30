from controllers import fechamento_controller, cliente_controller
from funcionalidades import Formata
from datetime import timedelta

class Fechamento:
    def __init__(self, cliente, data, id=None, numero_nota=None):
        self.id = id
        self.cliente = cliente
        self.data = data
        self.numero_nota = numero_nota

    
    @property
    def valor_total(self):
        valor_bruto = fechamento_controller.consulta_valor_total_fechamento(self.id)
        if valor_bruto is None:
            return 0
        else:
            valor_formatado = round(valor_bruto,2)
            return valor_bruto
    
    @property
    def data_formatada(self):
        data = self.data
        return data.strftime('%d/%m/%Y')
    
    @property
    def qtde_os(self):
        return fechamento_controller.consulta_qtde_os_no_fechamento(self.id)
    
    @property
    def nome_cliente(self):
        cliente_pesquisado = cliente_controller.consulta_cliente_por_id(self.cliente)
        return cliente_pesquisado.nome_fantasia

    @property
    def data_mais_antiga_e_mais_recente(self):
        data_mais_antiga, data_mais_recente = fechamento_controller.consulta_data_mais_antiga_e_mais_recente(self.id)
        data_mais_antiga_formatada = Formata.data(data_mais_antiga)
        data_mais_recente_formatada = Formata.data(data_mais_recente)
        return data_mais_antiga_formatada, data_mais_recente_formatada
    
    @property
    def qtde_dias(self):
        data_mais_antiga, data_mais_recente = fechamento_controller.consulta_data_mais_antiga_e_mais_recente(self.id)
        qtde_dias = (data_mais_antiga - data_mais_recente).days
        return qtde_dias
    
