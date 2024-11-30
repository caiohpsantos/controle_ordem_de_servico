import os
import mimetypes
from controllers.cliente_controller import consulta_cliente_por_id


class Ordem_Servico:
    def __init__(self, cliente_id,data, valor, descricao, solicitante, tel_solicitante, id=None, fechamento=None):
        self.id = id
        self.cliente_id = cliente_id
        self.data = data
        self.valor = valor
        self.descricao = descricao
        self.solicitante = solicitante
        self.tel_solicitante = tel_solicitante
        self.fechamento_id = fechamento

        def __str__(self):
            nome_fantasia_cliente = consulta_cliente_por_id(self.cliente_id)
            return f'O.S. {self.id} da(o) {nome_fantasia_cliente}'
        
    @property
    def data_formatada(self):
            data = self.data
            return data.strftime('%d/%m/%Y')
        
class Midia_OS:
    def __init__(self,id_os,arquivo,descricao, id_midia=None):
        self.id_midia = id_midia
        self.id_os = id_os
        self.arquivo = arquivo
        self.descricao = descricao
        self.nome_arquivo = os.path.basename(self.arquivo)

    @property    
    def tipo_arquivo(self):
            tipo_mime, _ = mimetypes.guess_type(self.arquivo)

            if tipo_mime:
                if tipo_mime.startswith('image/'):
                    return "Imagem"
                elif tipo_mime == 'application/pdf':
                    return "PDF"
                elif tipo_mime.startswith('video/'):
                    return "Vídeo"
                else:
                    return "Outro"
            else:
                return None
        


