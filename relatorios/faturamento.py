import yaml
import streamlit as st
import locale
import io
from yaml import SafeLoader
from fpdf import FPDF
from datetime import datetime
from models.fechamento import Fechamento
from controllers import fechamento_controller, os_controller, cliente_controller
from funcionalidades import Formata

'''locale é responsável por mostrar os valores usando caracteres BR'''
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

'''abre o arquivo com os dados da empresa'''
with open('./config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

'''reescreve a classe FPDF para alterar os métodos header e foooter
criando os cabeçalhos personalizados'''
class PDF(FPDF):
    def header(self):
        
        self.set_font("helvetica", "B", 12,)
        self.set_fill_color(200, 200, 200)
        self.cell(10, 1, f"{config['dados_empresariais']['nome_fantasia']} - {config['dados_empresariais']['razao_social']}",
                  align="l", fill=True)
        self.cell(9, 1, f"Emissão: {datetime.now().strftime("%d/%m/%Y")}", align='r', fill=True,
                   new_x='LMARGIN', new_y='NEXT')
        self.cell(0,1,"Relatório detalhado de Fechamento", fill=True, align="C", new_x='LMARGIN', new_y='NEXT')
        self.ln(1)
        
    def footer(self):
        self.set_y(-1.5)
        self.set_font('helvetica', 'I', 8)
        self.set_fill_color(200, 200, 200)
        self.cell(0,1,f"Página {self.page_no()}/{{nb}}", align='C', fill=True)

'''função responsável por gerar o pdf com os dados do faturamento'''
def emitir_pdf_faturamento_detalhado(num_fechamento):
    '''
    Emite um relatório em pdf constando todas as ordens de serviço que constam em um fechamento

    :param num_fechamento: Integer, id que representa o fechamento no banco de dados
    :return: BytesIO, arquivo pdf formatado com os dados do fechamento
    '''
    fechamento_selecionado = fechamento_controller.consulta_fechamento_por_id(int(num_fechamento))
    cliente_do_fechamento = cliente_controller.consulta_cliente_por_id(fechamento_selecionado.cliente)
    pdf = PDF(unit="cm")
    pdf.add_page()
    '''Monta o início do relatório com os dados do fechamento'''
    pdf.set_font('helvetica', size=16)
    
    'Nome fantasia do cliente'
    pdf.cell(9,1, f"Cliente: {cliente_do_fechamento.nome_fantasia}", align="l")
    
    'Especifica a id do fechamento e a data em que foi registrado'
    pdf.cell(9,1, f"Fechamento nº: {fechamento_selecionado.id} de {fechamento_selecionado.data_formatada}",
             new_x='LMARGIN', new_y="NEXT")
    
    'Mais detalhes do cliente'
    pdf.set_font_size(8)
    pdf.cell(9,0.5,f"Razão Social: {cliente_do_fechamento.razao_social}", new_x='LMARGIN', new_y='NEXT')
    
    if cliente_do_fechamento.tipo_cliente == "Pessoa Jurídica":
        pdf.cell(9,0.5,f"CNPJ: {cliente_do_fechamento.documento}", new_x='LMARGIN', new_y='NEXT')
    
    if cliente_do_fechamento.tipo_cliente == "Pessoa Física":
        pdf.cell(9,0.5,f"CPF: {cliente_do_fechamento.documento}", new_x='LMARGIN', new_y='NEXT')

    pdf.set_font_size(12)
    'Especifica o valor total da soma das o.s. registradas no fechamento'
    pdf.cell(9,1, f"Valor total: {locale.currency(fechamento_selecionado.valor_total, grouping=True)}")
    
    'Especifica quantas o.s. estão registradas no fechamento'
    pdf.cell(9,1, f"Total de O.S. incluídas: {fechamento_selecionado.qtde_os}",
             new_x='LMARGIN', new_y='NEXT')
    
    'Recupera a data mais antiga e a mais recente dentre as o.s. registradas no fechamento e também calcular quantos dias o fechamento abrange'
    data_mais_antiga, data_mais_recente = fechamento_controller.consulta_data_mais_antiga_e_mais_recente(fechamento_selecionado.id)
    diferenca_dias = (data_mais_recente - data_mais_antiga).days
    '''Caso a diferença de dias seja 0 (somente 1 o.s. no fechamento ou várias com a mesma data),
    substitui esse resultado para 1 pois o serviço foi prestado por pelo menos 1 dia'''
    if diferenca_dias == 0:
        diferenca_dias = 1

    pdf.cell(9,1,f"Total dias: {diferenca_dias}")
    if diferenca_dias == 1:
        pdf.cell(9,1,f"Somente no dia: {data_mais_antiga.strftime("%d/%m/%Y")}", new_x='LMARGIN', new_y='NEXT')
    else:
        pdf.cell(9,1,f"De {data_mais_antiga.strftime("%d/%m/%Y")} a {data_mais_recente.strftime("%d/%m/%Y")}",
                 new_x='LMARGIN', new_y='NEXT')
                  
    
    pdf.cell(0,0.1,"",border='B', new_x='LMARGIN', new_y='NEXT')
    
    'Detalha as ordens de serviço cadastradas no fechamento especificado'
    pdf.set_font('helvetica', "", 8)
    pdf.cell(0,1,"Seguem abaixo as Ordens de Serviço incluídas neste fechamento", new_x='LMARGIN', new_y='NEXT')
    
    'consulta todas as ordens de serviço incluídas naquele fechamento'
    os_incluidas = os_controller.consultar_os_por_fechamento(fechamento_selecionado.id)
    
    for os in os_incluidas:
        'Consulta a ordem de serviço específica e usa o objeto para preencher os dados'
        os_da_vez = os_controller.consultar_os_por_id(os[0])
        
        'Define a fonte maior para usar como título e diferenciar aonde a última os acaba e a nova começa'
        pdf.set_font('helvetica', "B", 12)
        
        'Muda a margem para que as ordens de serviço fiquem aninhadas abaixo do texto geral do fechamento'
        pdf.set_margin(1.5)
        pdf.cell(6,1,f"Ordem de Serviço n° {os_da_vez.id}", new_x='LMARGIN', new_y='NEXT')
        
        'Diminui a fonte e deixa o texto sem estilo para delimitar visualmente o resto do texto como pertencente a OS especificada acima'
        pdf.set_font('helvetica', "", 10)
        
        'Muda a margem novamente para aninhar o texto da OS abaixo do título que descreve seu ID'
        pdf.set_margin(2)
        
        'Dados da ordem de servico: data, valor, solicitante (obrigatórios) e telefone de contato do solicitante e imagem caso tenha'
        pdf.cell(6,1,f"Data registro: {os_da_vez.data_formatada}")
        pdf.cell(6,1,f"Valor: {locale.currency(os_da_vez.valor, grouping=True)}", new_x='LMARGIN', new_y='NEXT')
        
        'Trata o telefone do solicitante para mostrar uma mensagem mais amigável caso não tenha sido cadastrado'
        pdf.cell(6,1,f"Solicitante: {os_da_vez.solicitante}")
        tel_solicitante = "Não registrado" if not os_da_vez.tel_solicitante else Formata.telefone(os_da_vez.tel_solicitante)
        pdf.cell(9,1,f"Contato do solicitante: {tel_solicitante}", new_x='LMARGIN', new_y='NEXT')

        '''Se possui imagens anexadas à ordem de serviço vai anexá-las ao relatório,
        caso seja outro tipo de mídia vai informar que existe mídia cadastrada e o tipo,
        se não houver nada o campo não aparece'''
        midia_da_os = os_controller.consulta_midia_por_id_os(os_da_vez.id)
        if midia_da_os:
            for midia in midia_da_os:
                if midia.tipo_arquivo == "Imagem":
                    pdf.cell(0,1,f"Há arquivo(s) anexados, exibindo abaixo arquivo {midia.nome_arquivo}", new_x='LMARGIN', new_y='NEXT')
                    pdf.image(midia.arquivo,w=3, h=4,keep_aspect_ratio=True)
                if midia.tipo_arquivo != "Imagem":
                    pdf.set_font_size(8)
                    pdf.cell(0,1,f"Há arquivo(s) anexados, porém não podem ser exibidos neste relatório pois são do tipo {midia.tipo_arquivo}.",
                             new_x='LMARGIN', new_y='NEXT')
                

    pdf_temporario = io.BytesIO()
    pdf.output(pdf_temporario)
    pdf_temporario.seek(0)
    return pdf_temporario

