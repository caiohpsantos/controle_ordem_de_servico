@echo off
REM Caminho para o ambiente virtual
cd /d "C:\Users\Caio\Documents\controle_ordem_de_servico"

REM Ativa o ambiente virtual
call venv\Scripts\activate

REM Inicia a aplicação Streamlit
streamlit run app.py --server.port 80

pause

REM Desativa o ambiente virtual ao encerrar
deactivate
