import yaml
import streamlit as st
import locale
import io
from yaml import SafeLoader
from fpdf import FPDF
from datetime import datetime
from controllers import os_controller, cliente_controller

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
        self.cell(0,1,"Ordem de Serviço", fill=True, align="C", new_x='LMARGIN', new_y='NEXT')
        self.ln(1)
        
    def footer(self):
        self.set_y(-1.5)
        self.set_font('helvetica', 'I', 8)
        self.set_fill_color(200, 200, 200)
        self.cell(0,1,f"Página {self.page_no()}/{{nb}}", align='C', fill=True)

def emitir_pdf_nova_os(num_os):
    '''Emite um relatório em pdf da nova ordem de serviço registrada
    
    :param num_os: Integer, número da ordem de serviço que foi solicitado o relatorio
    :return: ByteIO, arquivo pdf contendo os dados da ordem de serviço solicitada'''

    os_fornecida = os_controller.consultar_os_por_id(num_os)
    cliente = cliente_controller.consulta_cliente_por_id(os_fornecida.cliente_id)
    pdf = PDF(unit="cm")
    pdf.add_page()
    '''Monta o início do relatório com os dados da ordem de serviço'''
    pdf.set_font('helvetica', size=16)

    'Nome fantasia do cliente'
    pdf.cell(9,1,f"Cliente: {cliente}", align='l')

    'Número da O.S.'
    pdf.cell(9,1,f"Ordem de Serviço: {os_fornecida.id}", align='r', new_x='LMARGIN', new_y="NEXT")

    'Dados do cliente'
    pdf.set_font_size(8)
    pdf.cell(9,0.5,f"Razão Social: {cliente.razao_social}", new_x='LMARGIN', new_y="NEXT")

    'Categoriza o tipo de documento com base se é Pessoa Jurídica (CNPJ) ou Pessoa Física (CPF)'
    if cliente.tipo_cliente == "Pessoa Jurídica":
        tipo_doc = "CNPJ"
    else:
        tipo_doc = "CPF"

    pdf.cell(9,0.5,f"{tipo_doc}: {cliente.documento}")

    'Data de registro da O.S.'
    pdf.set_font_size(16)
    pdf.cell(9,1,f"Registrada em: {os_fornecida.data_formatada}", align='r', new_x='LMARGIN', new_y="NEXT")

    'Valor cobrado'
    pdf.cell(0,1,f"Valor: {locale.currency(os_fornecida.valor, grouping=True)}", new_x='LMARGIN', new_y="NEXT")

    'Descrição do Serviço'
    pdf.cell(0,1,f"Descrição:", new_x='LMARGIN', new_y="NEXT")
    '''Diminui a fonte para que dê a impressão de que o texto está abaixo do título Descrição. 
    Além disso aumenta a margem esquerda para 3cm para alcançar o mesmo efeito'''
    pdf.set_font_size(10)
    # pdf.set_left_margin(3)
    pdf.multi_cell(0,1,f"{os_fornecida.descricao}", new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0,0.1,"", new_x='LMARGIN', new_y='NEXT')
    'Volta a margem e o tamanho da fonte ao normal'
    # pdf.set_left_margin(1)
    pdf.set_font_size(16)
    
    'Dados de quem solicitou a ordem de serviço'
    if os_fornecida.tel_solicitante:
        pdf.cell(9,1,f"Solicitante: {os_fornecida.solicitante}", align='l')
        pdf.cell(9,1,f"Contato: {os_fornecida.tel_solicitante}", align="r", new_x='LMARGIN', new_y='NEXT')
    else:
        pdf.cell(9,1,f"Solicitante: {os_fornecida.solicitante}", align='l', new_x='LMARGIN', new_y='NEXT')
    
    'Separação para área de mídias'
    pdf.cell(0,0.1,"",border='B', new_x='LMARGIN', new_y='NEXT')

    midia_da_os = os_controller.consulta_midia_por_id_os(os_fornecida.id)
    if midia_da_os:
        pdf.cell(0,1,"Há arquivos de mídia relacionados a esta Ordem de Serviço", new_x='lmargin', new_y='next')
        pdf.set_font_size(8)
        pdf.cell(3,1,"Legenda das mídias:",align='l')
        pdf.cell(15,1,f"{midia_da_os[0].descricao}", align='r', new_x='LMARGIN', new_y='NEXT')
        for midia in midia_da_os:
            if midia.tipo_arquivo == "Imagem":
                pdf.cell(0,1,f"Exibindo abaixo arquivo {midia.nome_arquivo}", new_x='LMARGIN', new_y='NEXT')
                pdf.image(midia.arquivo,w=9, keep_aspect_ratio=True)
            if midia.tipo_arquivo != "Imagem":
                pdf.set_font_size(8)
                pdf.cell(0,1,f"Há arquivo(s) anexados, porém não podem ser exibidos neste relatório pois são do tipo {midia.tipo_arquivo}.",
                            new_x='LMARGIN', new_y='NEXT')
    
    pdf_temporario = io.BytesIO()
    pdf.output(pdf_temporario)
    pdf_temporario.seek(0)
    return pdf_temporario

