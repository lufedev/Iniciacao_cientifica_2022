import pandas.io.sql as sqlio
import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
import functools as ft
import os
from ydata_profiling import ProfileReport

# COISAS IMPORTANTES
diretorio = "./dados/Filtered/"
conn = psycopg2.connect(
    # 192.168.15.45
    "dbname = 'postgres' user = 'postgres' host = '192.168.15.45' port = '7777' password = 'ic_2023'"
)

anos = ["2013", "2014", "2015", "2016", "2017", "2018", "2019", "2020", "2021"]
df_ufs = {}
df_analfabetismo = {}
df_renda = {}
dfs_comparativos = {}
UF = {}


# QUERIES
def getUF(year):
    query = 'select * from "uf_' + year + '";'
    return sqlio.read_sql_query(query, conn)


def getAnalfabetismo(year):
    query = 'select "UF","' + year + '" from "analfabetismo";'
    return sqlio.read_sql_query(query, conn)


def getRenda(year):
    query = 'select "UF","' + year + '" from "rendapercapita";'
    return sqlio.read_sql_query(query, conn)


# Coleta a cv anual
for ano in anos:
    df_ufs[ano] = getUF(ano)
    df_analfabetismo[ano] = getAnalfabetismo(ano)
    df_renda[ano] = getRenda(ano)

# Mescla a tabela de analfabetismo com a tabela de CV, renomeia a coluna que contém o ano para Analfabetismo
for ano in anos:
    dfs = [
        df_ufs[ano],
        df_analfabetismo[ano].rename(columns={ano: "Analfabetismo"}),
        df_renda[ano].rename(columns={ano: "Renda_per_capita"}),
    ]

    dfs_comparativos[ano] = ft.reduce(
        lambda left, right: pd.merge(left, right, on="UF"), dfs
    )
# Exporta individualmente cada estado brasileiro, separando por ano.
for ano, df_comparativo in dfs_comparativos.items():
    UF_grouped = df_comparativo.groupby("UF")
    for uf, grupo in UF_grouped:
        tabela_uf = grupo.copy()
        tabela_uf["UF"] = tabela_uf["UF"].apply(lambda x: f"{x} {ano}")
        tabela_uf.to_csv(f"./dados/Filtered/{ano}/{uf}-{ano}.csv", index=False)

# Agrupa todos os resultados por Estado.
for subdir, _, files in os.walk(diretorio):
    for file in files:
        if file.endswith(".csv"):
            caminho_arquivo = os.path.join(subdir, file)
            # obter o nome do estado a partir do nome do arquivo
            estado = file.split("-")[0]
            # ler a tabela
            tabela = pd.read_csv(caminho_arquivo)
            # adicionar a coluna "UF" com o nome do estado
            tabela["UF"] = estado
            # adicionar a tabela no dicionário de UF
            if estado in UF:
                UF[estado] = pd.concat([UF[estado], tabela])
            else:
                UF[estado] = tabela
# Remove a coluna UF
for estado, tabela in UF.items():
    tabela = tabela.fillna(0)
    tabela = tabela.drop(columns=["UF"])
    UF[estado] = tabela

print(UF["Sao Paulo"]["Renda_per_capita"])
print(UF["Sao Paulo"]["BCG"].corr(UF["Sao Paulo"]["Analfabetismo"]))
