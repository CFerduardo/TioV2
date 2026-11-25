from dotenv import load_dotenv
load_dotenv()
import os

vad10 = os.getenv('DB_CENTRAL_NAME')
vad20 = os.getenv('bd20')
v10imp = os.getenv('bdimp')

unew = os.getenv('user_new')
uold = os.getenv('user_old')

pwold = os.getenv('psw_old')
pwnew = os.getenv('psw_new')

SERVIDORES_TIENDAS = {       
    'IMPORTADORA':  {'SERVER': '10.100.115.2', 'DATABASE':v10imp, 'USER': uold, 'PASS': pwold},
    'ANACO':        {'SERVER':'10.221.101.10', 'DATABASE':vad20, 'USER':unew,  'PASS':pwnew},
    'APURE':        {'SERVER':'10.24.0.10',    'DATABASE':vad20, 'USER':unew,  'PASS':pwnew},
    'BABILON':      {'SERVER':'10.2.9.10',     'DATABASE':vad20, 'USER':uold,  'PASS':pwold},
    'BARALT':       {'SERVER':'10.201.101.10', 'DATABASE':vad20, 'USER':uold,  'PASS':pwold},
    'BOLIVAR':      {'SERVER':'10.218.101.10', 'DATABASE':vad20, 'USER':unew,  'PASS':pwnew},
    'CABIMAS':      {'SERVER':'10.4.7.10',     'DATABASE':vad20, 'USER':uold,  'PASS':pwold},
    'CABUDARE':     {'SERVER':'10.2.13.10',    'DATABASE':vad20, 'USER':uold,  'PASS':pwold},
    'CAGUA':        {'SERVER':'10.2.5.10',     'DATABASE':vad20, 'USER':uold,  'PASS':pwold},
    'CARORA':       {'SERVER':'10.42.2.10',    'DATABASE':vad20, 'USER':unew,  'PASS':pwnew},
    'CATIA':        {'SERVER':'10.2.15.10',    'DATABASE':vad20, 'USER':uold,  'PASS':pwold},
    'CRUZ VERDE':   {'SERVER':'10.1.2.10',     'DATABASE':vad20, 'USER':uold,  'PASS':pwold},
    'CUMANA':       {'SERVER':'10.23.101.10',  'DATABASE':vad20, 'USER':unew,  'PASS':pwnew},
    'GUACARA':      {'SERVER':'10.2.8.10',     'DATABASE':vad20, 'USER':uold,  'PASS':pwold},
    'GUANARE':      {'SERVER':'10.212.101.10', 'DATABASE':vad20, 'USER':uold,  'PASS':pwold},
    'KAPITANA':     {'SERVER':'10.1.3.10',     'DATABASE':vad20, 'USER':uold,  'PASS':pwold},
    'MARACAIBO':    {'SERVER':'10.46.1.10',    'DATABASE':vad20, 'USER':unew,  'PASS':pwnew},
    'MARACAY':      {'SERVER':'10.15.1.10',    'DATABASE':vad20, 'USER':unew,  'PASS':pwnew},
    'MATURIN':      {'SERVER':'10.3.11.10',    'DATABASE':vad20, 'USER':uold,  'PASS':pwold},
    'PROPATRIA':    {'SERVER':'10.1.4.10',     'DATABASE':vad20, 'USER':uold,  'PASS':pwold},
    'TIGRE':        {'SERVER':'10.10.1.10',    'DATABASE':vad20, 'USER':unew,  'PASS':pwnew},
    'UPATA':        {'SERVER':'10.3.10.10',    'DATABASE':vad20, 'USER':uold,  'PASS':pwold},
    'VALENCIA':     {'SERVER':'10.2.6.10',     'DATABASE':vad20, 'USER':uold,  'PASS':pwold},
    'VALERA':       {'SERVER':'10.2.14.10',    'DATABASE':vad20, 'USER':uold,  'PASS':pwold},
    'VIGIA':        {'SERVER':'10.222.101.10', 'DATABASE':vad20, 'USER':unew,  'PASS':pwnew},
    'VALLES':       {'SERVER':'10.26.1.10',    'DATABASE':vad20, 'USER':unew,  'PASS':pwnew},
    'CASCADA':      {'SERVER':'10.33.101.10',  'DATABASE':vad20, 'USER':uold,  'PASS':pwold},
    'CEMENTERIO':   {'SERVER':'10.32.101.10',  'DATABASE':vad20, 'USER':uold,  'PASS':pwold},
    'CANDELARIA':   {'SERVER':'10.34.101.10',  'DATABASE':vad20, 'USER':uold,  'PASS':pwold},
    'E-COMERCE':    {'SERVER':'10.100.40.37',  'DATABASE':vad20, 'USER':uold,  'PASS':pwold}
}

SQL_SERVER_IMG = {
    'CENTRAL': {'SERVER': '10.21.5.151', 'DATABASE': vad10, 'USER': 'sa', 'PASS': ''}
}

TIENDAS_MAP = {
    '0203': 'BABILON',
    '0301': 'BARALT',
    '0202': 'CABIMAS',
    '0205': 'CABUDARE',
    '0501': 'CAGUA',
    '0207': 'CATIA',
    '0201': 'CRUZ VERDE',
    '0204': 'GUANARE',
    '0103': 'GUACARA',
    '0101': 'KAPITANA',
    '0302': 'MATURIN',
    '0401': 'PROPATRIA',
    '0402': 'UPATA',
    '0102': 'VALENCIA',
    '0206': 'VALERA',
    '0104': 'MARACAY',
    '0208': 'TIGRE',
    '0209': 'MARACAIBO',
    '0210': 'BOLIVAR',
    '0211': 'CARORA',
    '0212': 'ANACO',
    '0213': 'VIGIA',
    '0214': 'CUMANA',
    '0215': 'APURE',
    '0216': 'VALLES',
}