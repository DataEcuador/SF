import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(layout="wide")  # Configurar diseño de página amplia

# Título principal
st.markdown(
    "<h1 style='text-align: center; font-size: 16px;'>Originación Sistema Financiero Ecuatoriano</h1>",
    unsafe_allow_html=True
)

@st.cache_data
def cargar_datos():
    # Leer los tres archivos de Excel
    archivo1 = pd.read_excel(r'c:\Users\Pablo Torres\Downloads\mestasa.xlsx')
    archivo2 = pd.read_excel(r'c:\Users\Pablo Torres\Downloads\mesmonto.xlsx')
    archivo3 = pd.read_excel(r'c:\Users\Pablo Torres\Downloads\mesop.xlsx')
    
    # Combinar los tres DataFrames
    datos = pd.concat([archivo1, archivo2, archivo3], ignore_index=True)
    
    # Convertir la columna date_field a datetime
    datos['date_field'] = pd.to_datetime(datos['date_field'])

    # Crear una columna para clasificar el tipo de entidad
    datos['tipo_entidad'] = datos['entity_name'].apply(
        lambda x: 'Banco' if x.startswith('B.') else ('Cooperativa' if x.startswith('C.') else 'Otro')
    )
    return datos

# Cargar y preparar los datos
datos = cargar_datos()

# Selector de pestañas
pagina_seleccionada = st.selectbox("Selecciona una página:", ["Gráfico Evolutivo", "Ranking"])

# Página: Gráfico Evolutivo
if pagina_seleccionada == "Gráfico Evolutivo":
    st.markdown(
        "<h2 style='font-size: 16px;'>Gráfico Evolutivo</h2>",
        unsafe_allow_html=True
    )
    
    col1, col2 = st.columns([4, 1])  # 4 partes para el gráfico, 1 parte para los selectores

    # Selectores
    with col2:
        st.write("Selecciona el rango de fechas:")
        min_fecha = datos['date_field'].min()
        max_fecha = datos['date_field'].max()
        fecha_inicio = st.date_input("Desde:", min_fecha, min_value=min_fecha, max_value=max_fecha)
        fecha_fin = st.date_input("Hasta:", max_fecha, min_value=min_fecha, max_value=max_fecha)

        # Selector para tipo de entidad
        tipo_entidades = ['Banco', 'Cooperativa', 'Otro']
        tipos_entidad_seleccionados = st.multiselect("Selecciona uno o más tipos de entidad:", tipo_entidades, default=tipo_entidades)

        # Filtrar entidades por los tipos seleccionados
        entidades_filtradas = datos[datos['tipo_entidad'].isin(tipos_entidad_seleccionados)]['entity_name'].unique()
        entidades_seleccionadas = st.multiselect("Selecciona una o más entidades:", entidades_filtradas)

        productos = datos['product_name'].unique()
        productos_seleccionados = st.multiselect("Selecciona uno o más productos:", productos)
        tipos_valor = datos['p_type'].unique()
        tipo_valor_seleccionado = st.selectbox("Selecciona el tipo de valor:", tipos_valor)

    with col1:
        fecha_inicio = pd.to_datetime(fecha_inicio)
        fecha_fin = pd.to_datetime(fecha_fin)

        if fecha_inicio > fecha_fin:
            st.error("La fecha 'Desde' debe ser menor o igual a la fecha 'Hasta'.")
        elif not entidades_seleccionadas:
            st.write("Selecciona al menos una entidad para ver la gráfica.")
        elif not productos_seleccionados:
            st.write("Selecciona al menos un producto para ver la gráfica.")
        else:
            datos_filtrados = datos[
                (datos['entity_name'].isin(entidades_seleccionadas)) &
                (datos['product_name'].isin(productos_seleccionados)) &
                (datos['p_type'] == tipo_valor_seleccionado) &
                (datos['date_field'] >= fecha_inicio) &
                (datos['date_field'] <= fecha_fin)
            ]
            datos_filtrados = datos_filtrados.dropna(subset=['date_field', 'value']).sort_values(by='date_field')

            if tipo_valor_seleccionado.lower() == "tasa":
                datos_filtrados['value'] = datos_filtrados['value'].round(2)
                label_valor = "Tasa (%)"
            elif tipo_valor_seleccionado.lower() == "monto":
                datos_filtrados['value'] = (datos_filtrados['value'] / 1_000_000).round(2)
                label_valor = "Monto (en millones)"
            elif tipo_valor_seleccionado.lower() == "operaciones":
                datos_filtrados['value'] = datos_filtrados['value'].round(0).astype(int)
                label_valor = "Operaciones (unidades)"
            else:
                label_valor = "Valor"

            # Paleta de colores ampliada
            colores = px.colors.qualitative.Set3 + px.colors.qualitative.Plotly + px.colors.qualitative.Pastel

            # Asignar un color único a cada entidad seleccionada
            color_map = {entidad: colores[i % len(colores)] for i, entidad in enumerate(entidades_seleccionadas)}

            fig = px.line(
                datos_filtrados,
                x='date_field',
                y='value',
                color='entity_name',
                title='Gráfico evolutivo',
                labels={'date_field': 'Fecha', 'value': label_valor, 'entity_name': 'Entidad'},
                markers=True,
                color_discrete_map=color_map  # Aplicar el mapa de colores único
            )
            st.plotly_chart(fig, use_container_width=True)

# Página: Ranking
elif pagina_seleccionada == "Ranking":
    st.markdown(
        "<h2 style='font-size: 16px;'>Ranking</h2>",
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([4, 1])

    with col2:
        # Selector de fecha
        st.write("Selecciona una fecha:")
        min_fecha = datos['date_field'].min()
        max_fecha = datos['date_field'].max()
        fecha_seleccionada = st.date_input("Fecha:", max_fecha, min_value=min_fecha, max_value=max_fecha)

        # Selector de producto
        productos = datos['product_name'].unique()
        producto_seleccionado = st.selectbox("Selecciona un producto:", productos)

        # Selector de tipo de entidad
        tipo_entidades = ['Banco', 'Cooperativa', 'Otro']
        tipos_entidad_seleccionados = st.multiselect("Selecciona uno o más tipos de entidad:", tipo_entidades, default=tipo_entidades)

        # Selector de orden
        columna_orden = st.selectbox(
            "Selecciona la columna para ordenar el ranking:",
            ["Tasa", "Monto", "Operaciones"]
        )

    with col1:
        datos_filtrados = datos[
            (datos['date_field'] == pd.to_datetime(fecha_seleccionada)) &
            (datos['product_name'] == producto_seleccionado) &
            (datos['tipo_entidad'].isin(tipos_entidad_seleccionados))
        ]

        if datos_filtrados.empty:
            st.write(f"No hay datos disponibles para la fecha {fecha_seleccionada} y el producto seleccionado.")
        else:
            ranking = datos_filtrados.pivot_table(
                index='entity_name',
                columns='p_type',
                values='value',
                aggfunc='first'
            ).reset_index()

            ranking = ranking.rename(columns={
                'entity_name': 'Entidad',
                'tasa': 'Tasa',
                'monto': 'Monto',
                'operaciones': 'Operaciones'
            })

            ranking['Monto'] = (ranking['Monto'] / 1_000_000).round(2)
            ranking['Operaciones'] = ranking['Operaciones'].fillna(0).astype(int)
            ranking['Tasa'] = ranking['Tasa'].fillna(0).round(2)

            ranking = ranking.sort_values(by=columna_orden, ascending=False).reset_index(drop=True)
            ranking['Ranking'] = range(1, len(ranking) + 1)

            ranking = ranking[['Ranking', 'Entidad', 'Tasa', 'Monto', 'Operaciones']]

            st.dataframe(
                ranking.style.format({
                    'Tasa': '{:.2f}',
                    'Monto': '{:.2f}',
                    'Operaciones': '{:,.0f}'
                }),
                use_container_width=True
            )
