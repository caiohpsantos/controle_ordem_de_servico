import os
import yaml
from yaml.loader import SafeLoader

with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)


DIR_MIDIA_OS = config['pastas_midias']['midias_os']
DIR_MIDIA_NF = config['pastas_midias']['notas_fiscais']  


