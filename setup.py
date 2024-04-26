import os
import dataset
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from dotenv import load_dotenv
from slugify import slugify

def truncate_string(text, max_length):
    if len(text) <= max_length:
        return text
    else:
        return text[:max_length]

load_dotenv() # take environment variables from .env.

path = os.getenv("CSV_FILE_PATH")
df = pd.read_csv(path)

subset_df = df[[
    'ID da resposta',
    'Qual o nome da iniciativa que vocês desenvolvem?',
    'Qual o nome da comunidade onde vocês desenvolvem suas atividades?',
    'Qual a localização do local onde vocês desenvolvem as atividades?',
    'Se sim, qual o nome do grupo, associação, coletivo ou organização que você representa? ',
    'Qual o tipo de atividade que a iniciativa de vocês se encaixa?',
    'Em qual estado vocês atuam?',
    'E qual a cidade?',
    'Qual a localização do local onde vocês desenvolvem as atividades? - Longitude',
    'Qual a localização do local onde vocês desenvolvem as atividades? - Latitude',    
]]

subset_df = subset_df.copy()

rename_dict = {
    'ID da resposta': 'id_resposta',
    'Qual o nome da iniciativa que vocês desenvolvem?': 'nome_acao',
    'Qual o nome da comunidade onde vocês desenvolvem suas atividades?': 'nome_comunidade',
    'Qual a localização do local onde vocês desenvolvem as atividades?': 'localidade',
    'Se sim, qual o nome do grupo, associação, coletivo ou organização que você representa? ': 'organizacao',
    'Qual o tipo de atividade que a iniciativa de vocês se encaixa?': 'categoria',
    'E qual a cidade?': 'municipio',
    'Em qual estado vocês atuam?': 'uf',
    'Qual a localização do local onde vocês desenvolvem as atividades? - Longitude': 'longitude',
    'Qual a localização do local onde vocês desenvolvem as atividades? - Latitude': 'latitude'
}

subset_df.rename(columns=rename_dict, inplace=True)

mapping_categorias = {
    'PLANEJAMENTO URBANO, GESTÃO DE RISCOS E RESPONSABILIDADE CLIMÁTICA: iniciativas em que o território é objeto de reflexão e auto-organização, como processos de planejamento urbano comunitário, auto-urbanização, gestão comunitária de riscos e iniciativas visando combater injustiças socioambientais.': 'Planejamento Urbano, Gestão de Riscos e Responsabilidade Climática',
    'SOBERANIA ALIMENTAR E NUTRICIONAL: iniciativas que coloquem a alimentação como prioridade universal, promovendo formas solidárias de  produção, confecção e distribuição de alimentos e refeições nas periferias.': 'Soberania Alimentar e Nutricional',
    'SAÚDE INTEGRAL E DIGNIDADE HUMANA: iniciativas voltadas para a promoção da saúde e bem estar que envolvam a melhoria das condições de salubridade e segurança da moradia e dos bairros periféricos.': 'Saúde Integral e Dignidade Humana',
    'ECONOMIA SOLIDÁRIA: iniciativas que promovam a produção e circulação solidária de riquezas nas periferias.': 'Economia Solidária',
    'ACESSO À JUSTIÇA E COMBATE ÀS DESIGUALDADES: iniciativas que promovam os direitos humanos e o combate à qualquer forma de violência em territórios periféricos.': 'Acesso à Justiça e Combate às Desigualdades',
    'COMUNICAÇÃO, INCLUSÃO DIGITAL E EDUCAÇÃO POPULAR: iniciativas que promovam a ampliação do alcance das vozes da periferia, possibilitando o desenvolvimento de lideranças e o protagonismo comunitário.': 'Comunicação, Inclusão Digital e Educação Popular',
    'CULTURA E MEMÓRIA: iniciativas que promovam a valorização urbano-cultural do espaço público e do patrimônio material e imaterial.': 'Cultura e Memória'
}
subset_df['categoria'] = subset_df['categoria'].map(mapping_categorias)

subset_df = subset_df.fillna('')

geometry = [Point(lon, lat) for lon, lat in zip(subset_df['longitude'], subset_df['latitude'])]

gdf = gpd.GeoDataFrame(subset_df, geometry=geometry)

db = dataset.connect(os.getenv("DATABASE_URL"))
table_name = os.getenv("TABLE_NAME")
table = db[table_name]
municipio_bbox = db['municipio_bbox']

db.query('CREATE TABLE IF NOT EXISTS ' + table_name + ' ( id serial PRIMARY KEY, geom geometry(Point, 4326), \
    nome_acao varchar, nome_comunidade varchar, localidade varchar, organizacao varchar, organizacao_slug varchar(400), \
    categoria varchar, uf varchar, municipio_cadastro varchar, id_resposta varchar(255), origem varchar(30), ano int, \
    premiado boolean, municipio_bbox_id int);')

for idx, row in gdf.iterrows():
    municipio_bbox_id = municipio_bbox.find_one(slug=slugify(row['municipio']), uf=row['uf'].upper())
    obj = table.find_one(id_resposta=row['id_resposta'], origem='redus')
    if not obj and municipio_bbox_id:
        table.insert(
            dict(
                id_resposta=row['id_resposta'],
                nome_acao=truncate_string(row['nome_acao'], 255),
                nome_comunidade=truncate_string(row['nome_comunidade'], 255),
                localidade=truncate_string(row['localidade'], 255),
                organizacao=truncate_string(row['organizacao'], 255),
                organizacao_slug=slugify(row['organizacao']),
                categoria=row['categoria'],
                uf=row['uf'],
                municipio_cadastro=row['municipio'],
                geom=row['geometry'].wkb,
                origem='redus',
                ano=None,
                premiado=False,
                municipio_bbox_id=municipio_bbox_id['id'],
            )
        )
