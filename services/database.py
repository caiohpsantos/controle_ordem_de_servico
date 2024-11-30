import mysql.connector
from mysql.connector import Error

def cria_conexao():
    try:
        conexao = mysql.connector.connect(
            host='localhost',  
            user='root',  
            password='S3gur4m35**',  
            database='machado_santos_courier'  
        )
        if conexao.is_connected():
            return conexao
    except Error as e:
        print(f"Erro ao conectar ao MySQL: {e}")
        return None
    
def fecha_conexao(conexao):
    if conexao.is_connected():
        conexao.close()
        
def cria_tabelas():
    'Cria tabela de clientes se ela não existir'
    cursor.execute('''CREATE TABLE IF NOT EXISTS `cliente` (
                    `id` int NOT NULL AUTO_INCREMENT,
                    `ativo` tinyint(1) NOT NULL DEFAULT '1',
                    `tipo_cliente` varchar(18) NOT NULL,
                    `documento` varchar(18) NOT NULL,
                    `razao_social` varchar(255) NOT NULL,
                    `nome_fantasia` varchar(255) NOT NULL,
                    `inscricao_estadual` varchar(9) NOT NULL,
                    `telefone` varchar(20) NOT NULL,
                    `email` varchar(255) NOT NULL,
                    `logradouro` varchar(255) NOT NULL,
                    `numero` varchar(6) NOT NULL,
                    `complemento` varchar(255) DEFAULT NULL,
                    `bairro` varchar(100) NOT NULL,
                    `cidade` varchar(100) NOT NULL,
                    `cep` varchar(10) NOT NULL,
                    PRIMARY KEY (`id`)
                    )''')
    
    'Cria tabela de ordem de serviço se ela não existir'
    cursor.execute('''CREATE TABLE IF NOT EXISTS `ordem_de_servico` (
                    `id` int NOT NULL AUTO_INCREMENT,
                    `cliente_id` int NOT NULL,
                    `data` datetime NOT NULL,
                    `valor` float NOT NULL,
                    `descricao` varchar(255) NOT NULL,
                    `solicitante` varchar(100) DEFAULT NULL,
                    `tel_solicitante` varchar(20) DEFAULT NULL,
                    `fechamento_id` int DEFAULT NULL,
                    PRIMARY KEY (`id`)
                    )''')
    
    'Cria tabela de midias se ela não existir'
    cursor.execute('''CREATE TABLE IF NOT EXISTS `midia_os` (
                    `idmidia_os` int NOT NULL AUTO_INCREMENT,
                    `id_os` int NOT NULL,
                    `arquivo` varchar(255) NOT NULL,
                    `descricao` varchar(255) DEFAULT NULL,
                    PRIMARY KEY (`idmidia_os`))
                   ''')
    
    'Cria tabela de notas fiscais se ela não existir'
    cursor.execute('''CREATE TABLE IF NOT EXISTS `nota_fiscal` (
                    `numero` INT NOT NULL,
                    `data_emissao` DATE NULL,
                    `valor` VARCHAR(45) NULL,
                    `arquivo` VARCHAR(255) NULL,
                    `cod_verificacao` VARCHAR(45) NULL,
                    PRIMARY KEY (`numero`));''')
    
    'Cria tabela de fechamentos se ela não existir'
    cursor.execute('''CREATE TABLE IF NOT EXISTS `fechamento` (
                    `id` int NOT NULL AUTO_INCREMENT,
                    `cliente_id` int DEFAULT NULL,
                    `data_fechamento` date DEFAULT NULL,
                    `numero_nota` int DEFAULT NULL,
                    PRIMARY KEY (`id`)
                    )''')
    
    'Cria tabela de pagamentos se ela não existir'
    cursor.execute('''CREATE TABLE IF NOT EXISTS `pagamento` (
                   `id` int NOT NULL AUTO_INCREMENT,
                   `fechamento_id` int NOT NULL,
                   `data_pgto` date NOT NULL,
                   `valor_pgto` decimal(10,2) NOT NULL,
                   `forma_pgto` varchar(8) NOT NULL,
                   `observacoes` varchar(55) DEFAULT NULL,
                   PRIMARY KEY (`id`)
                   )''')

    'Cria chave estrangeira da tabela ordem_de_servico em midia_os'
    cursor.execute(''' ALTER TABLE `midia_os` 
                    ADD INDEX `fk_midia_os_1_idx` (`id_os` ASC) VISIBLE;
                    ;
                    ALTER TABLE `database`.`midia_os` 
                    ADD CONSTRAINT `fk_midia_os_1`
                    FOREIGN KEY (`id_os`)
                    REFERENCES `ordem_de_servico` (`id`)
                    ON DELETE NO ACTION
                    ON UPDATE NO ACTION;
                   ''')
    
    'Cria chave estrangeira da tabela cliente e fechamento em ordem_de_servico'
    cursor.execute('''
                   ALTER TABLE `ordem_de_servico` 
                   ADD INDEX `fk_ordem_de_servico_1_idx` (`cliente_id` ASC) VISIBLE,
                   ADD INDEX `fk_ordem_de_servico_2_idx` (`fechamento_id` ASC) VISIBLE;
                   ;
                   ALTER TABLE `ordem_de_servico` 
                   ADD CONSTRAINT `fk_ordem_de_servico_1`
                   FOREIGN KEY (`cliente_id`)
                   REFERENCES `database`.`cliente` (`id`)
                   ON DELETE NO ACTION
                   ON UPDATE NO ACTION,
                   ADD CONSTRAINT `fk_ordem_de_servico_2`
                   FOREIGN KEY (`fechamento_id`)
                   REFERENCES `fechamento` (`id`)
                   ON DELETE NO ACTION
                   ON UPDATE NO ACTION;
                   ''')

    'Cria a chave estrangeira da tabela cliente em fechamento'
    cursor.execute('''
                    ALTER TABLE `fechamento` 
                    ADD INDEX `fk_fechamento_1_idx` (`cliente_id` ASC) VISIBLE;
                    ;
                    ALTER TABLE `fechamento` 
                    ADD CONSTRAINT `fk_fechamento_1`
                    FOREIGN KEY (`cliente_id`)
                    REFERENCES `cliente` (`id`)
                    ON DELETE NO ACTION
                    ON UPDATE NO ACTION;
                    ''')

    'Cria a chave estrangeira da tabela nota fiscal em fechamento'
    cursor.execute('''ALTER TABLE `fechamento` 
                    ADD INDEX `fk_fechamento_1_idx` (`numero_nota` ASC) VISIBLE;
                    ;
                    ALTER TABLE `machado_santos_courier`.`fechamento` 
                    ADD CONSTRAINT `fk_fechamento_1`
                    FOREIGN KEY (`numero_nota`)
                    REFERENCES `machado_santos_courier`.`nota_fiscal` (`numero`)
                    ON DELETE NO ACTION
                    ON UPDATE NO ACTION;''')
    conexao.commit()


conexao = cria_conexao()
cursor = conexao.cursor()

