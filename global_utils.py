import json
import pandas as pd
import numpy as np
import os

def update_geojson(df, date):
        
    columns_list = ['median_age', 'population_density', 'location', 'new_cases_smoothed_per_million']
    df = df.loc[df['date'] == date, columns_list]
    countries_list = list(set([location for location in list(df['location'])]))
    quantiles_list = [np.ceil(np.nanpercentile(np.array(df['new_cases_smoothed_per_million']), q)) for q in list(np.arange(0, 100, 12.5))]

    f = open('assets/geo_world.json')
    geojson = json.load(f)
    
    for feature in geojson['features']:
        property = feature['properties']
        
        country = property['name']

        if country in countries_list:
            median_age = df.loc[df['location'] == country, 'median_age'].values[0]
            population_density = df.loc[df['location'] == country, 'population_density'].values[0]
            new_cases_smoothed_per_million = df.loc[df['location'] == country, 'new_cases_smoothed_per_million'].values[0]

            if not np.isnan(median_age):
                property['median_age'] = median_age
            else:
                property['median_age'] = None
            
            if not np.isnan(population_density):
                property['population_density'] = population_density
            else:
                property['population_density'] = None
            
            if not np.isnan(new_cases_smoothed_per_million):
                if new_cases_smoothed_per_million == 0:
                    property['new_cases_smoothed_per_million'] = 0.1
                else:
                    property['new_cases_smoothed_per_million'] = new_cases_smoothed_per_million
            else:
                property['new_cases_smoothed_per_million'] = 0.1

    f.close()

    with open('assets/updated_geo_world.json', 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False)
        f.close()

    print(f'GEOJSON zaktualizowany o wartości z dnia {date}.')

    return quantiles_list



def get_variables_dict():
    assets_path = os.path.join(os.getcwd(), 'assets')
    data_path = os.path.join(assets_path, 'variables_dict.csv')

    df = pd.read_csv(data_path, sep=';')
    df = df.drop('definition_eng', axis=1)

    variables_dict = {}
    for row in range(df.shape[0]):
        variable_name = df.loc[row, 'variable_name']
        definition_pl = df.loc[row, 'definition_pl']
        variables_dict[variable_name] = definition_pl

    return variables_dict



def transform_df_wide_long(df):
    
    variables_dict = get_variables_dict()
    df_wide = df
    columns_to_drop = ['iso_code', 'tests_units']
    df_wide = df_wide.drop(columns_to_drop, axis=1, inplace=False)
    df_long = pd.melt(df_wide,id_vars=['continent', 'location', 'date'],var_name='metrics', value_name='values')
    df_long = df_long[~pd.isna(df_long['continent'])]
    df_long['metrics'] = [variables_dict[value] for value in list(df_long['metrics'])]

    return df_long



def fix_countries_names(df):

    countries_to_replace_dict = {
        'Czechia': 'Czech Rep.',
        'South Korea': 'Korea',
        'Northern Cyprus': 'N. Cyprus',
        'Solomon Islands': 'Solomon Is.',
        'Falklan Islands': 'Falklan Is.',
        'North Macedonia': 'Macedonia'
        }
    df = df.replace({"location": countries_to_replace_dict}, inplace=False)

    return df