class Pagamento:
    def __init__ (self, fechamento_id, data_pagamento, valor_pago, forma_pagamento, observacoes, id=None):
        self.id = id
        self.fechamento_id = fechamento_id
        self.data_pagamento = data_pagamento
        self.valor_pago = valor_pago
        self.forma_pagamento = forma_pagamento
        self.observacoes = observacoes
        