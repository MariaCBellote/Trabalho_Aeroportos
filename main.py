import streamlit as st
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt


st.set_page_config(
    page_title="Menor Rota entre Aeroportos",
    layout="wide"
)

st.title("Rotas Aeroporto")


# ---------------------------------------------------------------------------
# 1. Leitura da planilha
# ---------------------------------------------------------------------------

arquivo = "aerportos_brasil.xlsx"

xls = pd.ExcelFile(arquivo)

df = pd.read_excel(
    xls,
    sheet_name="Planilha2"
)


# ---------------------------------------------------------------------------
# 2. Visualização dos dados
# ---------------------------------------------------------------------------

st.write("Pré-visualização dos dados:")

st.dataframe(
    df.head(193),
    use_container_width=True
)


# ---------------------------------------------------------------------------
# 3. Construção do grafo
# ---------------------------------------------------------------------------

col_origem = "origem_iata"
col_destino = "destino_iata"

col_cidade_origem = "origem_cidade"
col_cidade_destino = "destino_cidade"

col_peso = "distancia_km"

grafo_dirigido = True


# Seleciona apenas as colunas necessárias

df_validos = df[
    [
        col_origem,
        col_destino,
        col_cidade_origem,
        col_cidade_destino,
        col_peso
    ]
].dropna(
    subset=[
        col_origem,
        col_destino,
        col_cidade_origem,
        col_cidade_destino,
        col_peso
    ]
)


# Verifica se a distância é numérica

df_validos = df_validos[
    pd.to_numeric(
        df_validos[col_peso],
        errors="coerce"
    ).notna()
]


# Converte a distância para número

df_validos[col_peso] = df_validos[col_peso].astype(float)


# Cria o grafo direcionado

G = nx.DiGraph()


# Adiciona os aeroportos e as conexões ao grafo

for _, row in df_validos.iterrows():

    origem = str(row[col_origem]).strip()
    destino = str(row[col_destino]).strip()
    peso = float(row[col_peso])

    G.add_edge(
        origem,
        destino,
        weight=peso
    )


# ---------------------------------------------------------------------------
# 4. Relaciona aeroportos às cidades
# ---------------------------------------------------------------------------

aeroporto_cidade = {}


for _, row in df_validos.iterrows():

    aeroporto_origem = str(row[col_origem]).strip()
    cidade_origem = str(row[col_cidade_origem]).strip()

    aeroporto_destino = str(row[col_destino]).strip()
    cidade_destino = str(row[col_cidade_destino]).strip()

    aeroporto_cidade[aeroporto_origem] = cidade_origem
    aeroporto_cidade[aeroporto_destino] = cidade_destino


# Lista de cidades disponíveis

cidades = sorted(
    set(aeroporto_cidade.values())
)


# ---------------------------------------------------------------------------
# 5. Escolha de origem e destino
# ---------------------------------------------------------------------------

st.header("Escolha Origem e Destino")


col_a, col_b = st.columns(2)


with col_a:

    partida = st.selectbox(
        "Cidade de Origem",
        cidades,
        key="partida"
    )


with col_b:

    destino_default = 1 if len(cidades) > 1 else 0

    chegada = st.selectbox(
        "Cidade de Destino",
        cidades,
        index=destino_default,
        key="chegada"
    )


calcular = st.button(
    "Calcular menor rota",
    type="primary"
)


# ---------------------------------------------------------------------------
# 6. Execução do Dijkstra
# ---------------------------------------------------------------------------

if calcular:

    if partida != chegada:

        # -------------------------------------------------------------------
        # Encontra todos os aeroportos das cidades escolhidas
        # -------------------------------------------------------------------

        aeroportos_origem = [
            aeroporto
            for aeroporto, cidade in aeroporto_cidade.items()
            if cidade == partida
        ]


        aeroportos_destino = [
            aeroporto
            for aeroporto, cidade in aeroporto_cidade.items()
            if cidade == chegada
        ]


        # -------------------------------------------------------------------
        # Procura a menor rota entre todos os aeroportos possíveis
        # -------------------------------------------------------------------

        melhor_caminho = None
        menor_custo = float("inf")


        for aeroporto_origem in aeroportos_origem:

            for aeroporto_destino in aeroportos_destino:

                try:

                    caminho = nx.dijkstra_path(
                        G,
                        aeroporto_origem,
                        aeroporto_destino,
                        weight="weight"
                    )


                    custo = nx.dijkstra_path_length(
                        G,
                        aeroporto_origem,
                        aeroporto_destino,
                        weight="weight"
                    )


                    if custo < menor_custo:

                        menor_custo = custo
                        melhor_caminho = caminho


                except nx.NetworkXNoPath:

                    continue


        # -------------------------------------------------------------------
        # Resultado
        # -------------------------------------------------------------------

        if melhor_caminho is not None:

            st.subheader("Resultado")


            # Mostra a rota com cidade + aeroporto

            rota_detalhada = []


            for aeroporto in melhor_caminho:

                cidade = aeroporto_cidade[aeroporto]

                rota_detalhada.append(
                    f"{cidade} ({aeroporto})"
                )


            st.markdown(
                f"**Rota de menor custo:** "
                f"{' → '.join(rota_detalhada)}"
            )


            st.markdown(
                f"**Custo total:** {menor_custo:.2f}"
            )


            # Mostra os aeroportos utilizados

            st.markdown(
                f"**Aeroportos utilizados:** "
                f"{' → '.join(melhor_caminho)}"
            )


            # ----------------------------------------------------------------
            # Detalhamento dos trechos
            # ----------------------------------------------------------------

            trechos = []


            for i in range(len(melhor_caminho) - 1):

                aeroporto_origem = melhor_caminho[i]
                aeroporto_destino = melhor_caminho[i + 1]

                cidade_origem = aeroporto_cidade[aeroporto_origem]
                cidade_destino = aeroporto_cidade[aeroporto_destino]


                peso_trecho = G[
                    aeroporto_origem
                ][
                    aeroporto_destino
                ]["weight"]


                trechos.append({
                    "De": f"{cidade_origem} ({aeroporto_origem})",
                    "Para": f"{cidade_destino} ({aeroporto_destino})",
                    "Custo": peso_trecho
                })


            st.table(
                pd.DataFrame(trechos)
            )


            # ----------------------------------------------------------------
            # Visualização do grafo
            # ----------------------------------------------------------------

            st.subheader("Visualização do grafo")


            fig, ax = plt.subplots(
                figsize=(10, 7)
            )


            # Cria a posição dos nós

            pos = nx.spring_layout(
                G,
                seed=42,
                k=0.7
            )


            # Arestas da menor rota

            arestas_caminho = list(
                zip(
                    melhor_caminho[:-1],
                    melhor_caminho[1:]
                )
            )


            arestas_caminho_set = set(
                arestas_caminho
            )


            # Outras arestas

            outras_arestas = [
                e
                for e in G.edges()
                if e not in arestas_caminho_set
            ]


            # ----------------------------------------------------------------
            # Nós do grafo
            # ----------------------------------------------------------------

            nx.draw_networkx_nodes(
                G,
                pos,
                ax=ax,
                node_size=550,
                node_color="#cfe2f3",
                edgecolors="#333333"
            )


            # Destaca os aeroportos utilizados

            nx.draw_networkx_nodes(
                G,
                pos,
                nodelist=melhor_caminho,
                ax=ax,
                node_size=650,
                node_color="#ff9999",
                edgecolors="#990000"
            )


            # Nomes dos aeroportos

            nx.draw_networkx_labels(
                G,
                pos,
                ax=ax,
                font_size=8,
                font_weight="bold"
            )


            # ----------------------------------------------------------------
            # Arestas que não fazem parte da rota
            # ----------------------------------------------------------------

            nx.draw_networkx_edges(
                G,
                pos,
                edgelist=outras_arestas,
                ax=ax,
                edge_color="#cccccc",
                width=0.8,
                arrows=grafo_dirigido,
                arrowsize=8
            )


            # ----------------------------------------------------------------
            # Arestas da menor rota
            # ----------------------------------------------------------------

            nx.draw_networkx_edges(
                G,
                pos,
                edgelist=arestas_caminho,
                ax=ax,
                edge_color="#cc0000",
                width=3,
                arrows=grafo_dirigido,
                arrowsize=15
            )


            # ----------------------------------------------------------------
            # Pesos das arestas
            # ----------------------------------------------------------------

            pesos_caminho = {
                e: G[e[0]][e[1]]["weight"]
                for e in arestas_caminho
            }


            nx.draw_networkx_edge_labels(
                G,
                pos,
                edge_labels=pesos_caminho,
                ax=ax,
                font_size=8,
                font_color="#990000"
            )


            # ----------------------------------------------------------------
            # Título
            # ----------------------------------------------------------------

            ax.set_title(
                f"Menor rota: {partida} → {chegada} "
                f"(custo total: {menor_custo:.2f})"
            )


            ax.axis("off")


            st.pyplot(fig)

            plt.close(fig)


            # ----------------------------------------------------------------
            # Grafo completo
            # ----------------------------------------------------------------

            with st.expander(
                "Ver grafo completo (todos os aeroportos e conexões)"
            ):

                fig2, ax2 = plt.subplots(
                    figsize=(10, 7)
                )


                # Posição dos nós

                pos2 = nx.spring_layout(
                    G,
                    seed=42,
                    k=0.7
                )


                # Nós

                nx.draw_networkx_nodes(
                    G,
                    pos2,
                    ax=ax2,
                    node_size=450,
                    node_color="#cfe2f3",
                    edgecolors="#333333"
                )


                # Nomes

                nx.draw_networkx_labels(
                    G,
                    pos2,
                    ax=ax2,
                    font_size=7
                )


                # Arestas

                nx.draw_networkx_edges(
                    G,
                    pos2,
                    ax=ax2,
                    edge_color="#999999",
                    width=0.8,
                    arrows=grafo_dirigido,
                    arrowsize=6
                )


                # Pesos de todas as arestas

                edge_labels_all = nx.get_edge_attributes(
                    G,
                    "weight"
                )


                nx.draw_networkx_edge_labels(
                    G,
                    pos2,
                    edge_labels=edge_labels_all,
                    ax=ax2,
                    font_size=6
                )


                ax2.axis("off")


                st.pyplot(fig2)

                plt.close(fig2)