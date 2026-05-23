import requests
import pandas as pd
from io import StringIO
import json
import geopandas as gpd
import matplotlib.pyplot as plt
import streamlit as st

STATISTIKAAMETI_API_URL = "https://andmed.stat.ee/api/v1/et/stat/RV032"

JSON_PAYLOAD_STR =""" {
  "query": [
    {
      "code": "Aasta",
      "selection": {
        "filter": "item",
        "values": [
          "2014",
          "2015",
          "2016",
          "2017",
          "2018",
          "2019",
          "2020",
          "2021",
          "2022",
          "2023"
        ]
      }
    },
    {
      "code": "Maakond",
      "selection": {
        "filter": "item",
        "values": [
          "39",
          "44",
          "49",
          "51",
          "57",
          "59",
          "65",
          "67",
          "70",
          "74",
          "78",
          "82",
          "84",
          "86",
          "37"
        ]
      }
    },
    {
      "code": "Sugu",
      "selection": {
        "filter": "item",
        "values": [
          "2",
          "3"
        ]
      }
    }
  ],
  "response": {
    "format": "csv"
  }
}
"""
geojson = "maakonnad.geojson"
    

@st.cache_data(ttl=3600)
def import_data():
    headers = {
        'Content-Type': 'application/json'  # or application/x-www-form-urlencoded if needed
    }
    
    parsed_payload = json.loads(JSON_PAYLOAD_STR)

    response = requests.post(
        STATISTIKAAMETI_API_URL,
        json=parsed_payload,
        headers=headers,
        timeout=30,
    )
    
    if response.status_code == 200:
        text = response.content.decode('utf-8-sig')
        df = pd.read_csv(StringIO(text))
    else:
        raise requests.RequestException(
            f"Failed with status code: {response.status_code}: {response.text}"
        )
    return df


@st.cache_data
def import_geojson():
    gdf = gpd.read_file(geojson)
    return gdf


def get_data_for_year(df, year):
    year_data = df[df.Aasta == year]
    return year_data


def plot(df, year):
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    df.plot(
        column='Loomulik iive',
        ax=ax,
        legend=True,
        cmap='viridis',
        legend_kwds={'label': "Loomulik iive"}
    )
    
    plt.title(f'Loomulik iive maakonniti: {year}')
    plt.axis('off')
    plt.tight_layout()
    return fig


def main():
    st.set_page_config(page_title="Loomulik iive maakonniti", layout="wide")
    st.title("Loomulik iive maakonniti")

    try:
        df = import_data()
        gdf = import_geojson()
    except requests.RequestException as exc:
        st.error(f"Andmete laadimine ebaõnnestus: {exc}")
        return

    merged_data = gdf.merge(df, left_on='MNIMI', right_on='Maakond')
    merged_data["Loomulik iive"] = (
        merged_data["Mehed Loomulik iive"] + merged_data["Naised Loomulik iive"]
    )
    merged_data["Aasta"] = merged_data["Aasta"].astype(int)

    years = sorted(merged_data["Aasta"].unique())
    selected_year = st.sidebar.selectbox("Vali aasta", years, index=len(years) - 1)

    data_for_year = get_data_for_year(merged_data, selected_year)
    st.subheader(f"Loomulik iive maakonniti: {selected_year}")
    fig = plot(data_for_year, selected_year)
    st.pyplot(fig)

    st.dataframe(
        data_for_year[
            [
                "Maakond",
                "Mehed Loomulik iive",
                "Naised Loomulik iive",
                "Loomulik iive",
            ]
        ].sort_values("Loomulik iive", ascending=False),
        hide_index=True,
        use_container_width=True,
    )


if __name__ == "__main__":
    main()
