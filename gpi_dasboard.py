import pandas as pd
import altair as alt
import jsonschema
import geopandas as gpd

import re
import math
from dateutil.relativedelta import *
# exclude max rows limit
alt.data_transformers.enable('default', max_rows=None)

csvName = 'all_countries_xgb_results.csv'
dataFile = pd.read_csv(csvName)
dataGPI = dataFile.iloc[:, 0:5]
dataGPI = dataGPI.rename(
    columns={"GPI_score": "Real GPI", "gpi_predicted": "Predicted GPI"}
)
dataGPI['date'] = pd.to_datetime(dataGPI['MonthYear'], format='%Y%m')
dataGPI['year'] = dataGPI['MonthYear'].apply(str).str[:4]
dataGPI['month'] = dataGPI['MonthYear'].apply(str).str[-2:]
dataGPI['month_str'] = dataGPI['date'].dt.month_name()
dataGPI['Real GPI'] = dataGPI['Real GPI'].round(3)
dataGPI['Predicted GPI'] = dataGPI['Predicted GPI'].round(3)
dataGPI['delta_perc'] = ((dataGPI['Predicted GPI'] -
                          dataGPI['Real GPI']) / dataGPI['Real GPI'] * 100).round(4)

# Shapefile of the world (enriched)
geoLayer = gpd.read_file('world_countries_geo.json')

# Calculate list of dates
dates = dataGPI.groupby(by=['MonthYear']).first().reset_index()[
    ['MonthYear', 'date', 'year', 'month']
]

# FEATURE IMPORTANCE DATA (from wide form to long form)
featuresI = pd.read_csv(csvName)
features = list(featuresI.columns)[6:]  # get list of features
featuresI_m = featuresI.melt(
    ['MonthYear', 'country_code'], value_vars=features)
featuresI_m = featuresI_m.sort_values(['country_code', 'MonthYear', 'value'], ascending=[
    True, True, False]).reset_index(drop=True)
featuresI_m.head()

featuresI_m['ranking'] = featuresI_m.groupby(['MonthYear', 'country_code'])[
    'value'].rank(method='first', ascending=False)
featuresI_m = featuresI_m[featuresI_m['ranking'] <= 10]
featuresI_m.head()

# GPI dates 'months=-6'
date = dataGPI['date'].max()
date_back = date + relativedelta(months=-6)

predictedTimeFrame = [{
    "start": date_back,
    "end": date,
    "event": "Only Predicted Data"
}]

timeSpan = alt.pd.DataFrame(predictedTimeFrame)
timeSpan['start'] = pd.to_datetime(timeSpan['start'])
timeSpan['end'] = pd.to_datetime(timeSpan['end'])

# COUNTRY SELECTOR OUTSIDE THE MAP ######################
codes = dataGPI['country_code'].unique()
names = dataGPI['country_name'].unique()
zip_iterator = zip(codes, names)
code_dicts = dict(zip_iterator)

# Prepare data for selector below the map
dataLegend = geoLayer.sort_values(by=['Sub-region Name', 'FIPS']).dropna()
dataLegend = dataLegend[
    ['name', 'FIPS', 'Sub-region Name', 'Region Name']
].sort_values(['Region Name', 'Sub-region Name', 'FIPS'])

# Filtering data: remove labels for countries not in the GDELT dataset
dataLegend = dataLegend[dataLegend['FIPS'].isin(list(codes))]
dataLegend['RN'] = dataLegend.groupby('Sub-region Name').cumcount() + 1
dataLegend.rename(columns={'name': 'country_name',
                           'FIPS': 'country_code'}, inplace=True)

dataLegend['Sub-region Name ordered'] = ""

# Choose max column to visualize on Selector Chart
c = 24
for index, row in dataLegend.iterrows():
    r = math.floor(row['RN'] / c)
    dataLegend.at[index,
                  'Sub-region Name ordered'] = row[
        'Sub-region Name'] if r == 0 else f"{row['Sub-region Name']} -{str(r + 1)}"

cNames = list(dataLegend['Sub-region Name ordered'].unique())
labelsList = []
for el in cNames:
    if len(re.findall(r"\b -\d", el)) > 0:
        el = ''
    labelsList.append(el)

for i, row in dataLegend.iterrows():
    if row['country_code'] in code_dicts.keys():
        dataLegend.at[i, 'country_name'] = code_dicts[row['country_code']]


def create_final_chart():
    colors_gpi = alt.Scale(
        domain=['Real GPI', 'Predicted GPI'],
        range=['#4f4f4f', '#72a35a']
    )

    # Selectors:
    click_time = alt.selection_single(empty='none', init={'MonthYear': 201909}, on='mouseover', nearest=True,
                                      fields=['MonthYear'])
    click_country = alt.selection_single(empty='none', init={'country_code': 'US', 'country_name': 'United States'},
                                         fields=['country_code', 'country_name'])

    timeline = alt.Chart(dates).mark_square(
        cursor='pointer'
    ).encode(
        x=alt.X('date:T', axis=alt.Axis(grid=False, title=None)),
        color=alt.condition(click_time, alt.value('#4f4f4f'), alt.value('lightgray')),
        size=alt.condition(click_time, alt.value(120), alt.value(80)),
        opacity=alt.condition(click_time, alt.value(1), alt.value(0.8)),
        tooltip=[alt.Tooltip('date:T', format='%b, %Y')]
    ).properties().add_selection(
        click_time
    )

    base = alt.Chart(geoLayer).mark_geoshape(
        fill='lightgrey', stroke='white', strokeWidth=.5  # lightgrey
    ).project(
        type='mercator',
        scale=100,
        translate=[300, 220]
    )

    world_map = alt.Chart(dataGPI).transform_filter(
        click_time
    ).transform_lookup(
        lookup='country_code',
        from_=alt.LookupData(geoLayer, key='FIPS', fields=['FIPS', 'geometry', 'type', 'name'])
    ).mark_geoshape(
        stroke='gray',
        strokeWidth=0.5,
        cursor='pointer'
    ).encode(
        color=alt.condition(click_country,
                            alt.value('#4f4f4f'),
                            alt.Color(
                                'Predicted GPI:Q',
                                scale=alt.Scale(
                                    scheme='purpleorange',
                                    reverse=True,
                                    type='threshold',
                                    domain=[1.47, 1.9, 2.35, 2.9]
                                ), legend=alt.Legend(
                                    orient='none',
                                    direction='horizontal',
                                    title='← More Peace         GPI         Less Peace →',
                                    titleAnchor='middle',
                                    titleLimit=250,
                                    gradientLength=250,
                                    legendX=300,
                                    legendY=320
                                )
                            )
                            ),
        tooltip=[
            alt.Text('name:N', title='Country'),
            alt.Text('Predicted GPI:Q', format=',.3f', title='Predicted GPI'),
            alt.Text('Real GPI:Q', format=',.3f', title='Real GPI'),
        ]
    ).add_selection(
        click_country
    )

    zero_line = alt.Chart(pd.DataFrame({'y': [0]})).mark_rule(
        strokeDash=[10, 3],
        size=1,
    ).encode(
        y='y:Q'
    )

    text_country = alt.Chart(dataGPI).mark_text(
        align='center', baseline='bottom', dx=+5, dy=20, fontSize=14, fontWeight="bold"
    ).encode(
        x=alt.value(175),
        y=alt.value(0),
        text='caption:N',
    ).transform_filter(
        click_country
    ).transform_filter(
        click_time
    ).transform_calculate(
        caption="datum.country_name"
    )

    gpi_error = alt.Chart(dataGPI).mark_line(
        interpolate='monotone',
        color='#72a35a'
    ).transform_filter(
        click_country
    ).encode(
        x=alt.X('date:T', title=None),
        y=alt.Y('delta_perc:Q', title=None, scale=alt.Scale(zero=False))
    ).properties(
        title=alt.TitleParams(text='GPI Prediction error (%)', fontWeight="normal")
    )

    gpi_score = alt.Chart(dataGPI).mark_line(
        interpolate='monotone'
    ).transform_filter(
        click_country
    ).transform_fold(
        fold=['Predicted GPI', 'Real GPI'],
        as_=['GPI', 'value']
    ).encode(
        x=alt.X('date:T', title=None),
        y=alt.Y('value:Q', title=None, scale=alt.Scale(zero=False)),
        color=alt.Color('GPI:N',
                        legend=alt.Legend(direction='horizontal', orient='top', symbolSize=200, symbolStrokeWidth=5,
                                          title=None), scale=colors_gpi)
    )

    gpi_area = alt.Chart(dataGPI).mark_area(
        interpolate='monotone',
        color='lightgray',
        opacity=0.5
    ).transform_filter(
        click_country
    ).encode(
        x=alt.X('date:T', title=None),
        y=alt.Y('Real GPI:Q', title=None, scale=alt.Scale(zero=False)),
        y2=alt.Y2('Predicted GPI:Q')
    )

    mark_line = alt.Chart(
        dataGPI
    ).transform_filter(
        click_country
    ).transform_filter(
        click_time
    ).mark_rule(
        strokeDash=[2, 4]
    ).encode(
        x=alt.X('date:T', title=None),
    )

    #########

    timeline = timeline.properties(
        width=1050,
        height=30
    )

    # Draw text labels near the ruler
    text_ruler = mark_line.mark_text(
        align='left', dx=5, dy=-5
    ).encode(
        text=alt.Text('date:T', format='%b, %Y')
    )

    gpi_score = gpi_score.properties(
        title='GPI Real and Predicted',
        height=100,
        width=350
    )

    gpi_area = gpi_area.properties(
        title=alt.TitleParams(text='Real VS Predicted GPI', fontWeight="normal"),
        height=100,
        width=350
    )

    gpi_score_dots = alt.Chart(dataGPI).mark_circle(
        color='#4f4f4f', size=100
    ).transform_filter(
        click_country
    ).transform_filter(
        'datum.month=="03"'
    ).encode(
        x=alt.X('date:T', title=None),
        y=alt.Y('Real GPI:Q', title=None, scale=alt.Scale(zero=False)),
    )

    rect = alt.Chart(timeSpan).mark_rect(
        color="beige",
        opacity=0.9
    ).encode(
        x='start:T',
        x2='end:T'
    )

    gpi_chart = rect + gpi_area + gpi_score + gpi_score_dots + mark_line + text_ruler

    gpi_time = (gpi_error + zero_line + mark_line + text_ruler).properties(
        height=100,
        width=350
    )

    world_map = world_map.properties(
        width=600,
        height=380,
    ).project(
        type='mercator',
        scale=100,
        # center=[-130,75]
        translate=[300, 220]
    )

    ranking = alt.Chart(featuresI_m).mark_bar(
        color='#5a8246',
        tooltip=True
    ).encode(
        x=alt.X('value:Q', title=None),
        y=alt.X('variable:N', title=None, sort='-x', axis=alt.Axis(orient='right')),
        tooltip=[
            alt.Text('variable:N', title='Variable')
        ]
    ).transform_filter(
        f"datum.country_code == {click_country.country_code}"
    ).transform_filter(
        click_time
    ).properties(
        width=180,
        height=130,
        title=alt.TitleParams(text='Variable importance*', fontWeight="normal")
    ).interactive()

    prediction_chart = alt.Chart(dataGPI, title=alt.TitleParams(text='🔎  Predicted GPI for the last six months',
                                                                fontWeight="normal")).mark_line(
        interpolate='monotone',
        color='#72a35a',
        point=True
    ).transform_filter(
        click_country
    ).transform_filter(
        alt.datum.MonthYear >= '201909'
    ).encode(
        x=alt.X('date:T', title=None),
        y=alt.Y('Predicted GPI:Q', title=None, scale=alt.Scale(zero=False), axis=alt.Axis(gridColor='white'))
    ).properties(
        height=100,
        width=350
    )

    mark_line_y = alt.Chart(
        dataGPI
    ).transform_filter(
        click_country
    ).transform_filter(
        alt.datum.MonthYear >= '201909'
    ).transform_filter(
        click_time
    ).mark_rule(
        strokeDash=[2, 4]
    ).encode(
        x=alt.X('date:T', title=None),
    )

    # Draw text labels near the ruler
    text_ruler_y = mark_line.mark_text(
        align='left', dx=5, dy=-5
    ).transform_filter(
        alt.datum.MonthYear >= '201909'
    ).encode(
        text=alt.Text('date:T', format='%b, %Y')
    )

    prediction_chart_y = (rect + prediction_chart + mark_line_y + text_ruler_y)

    # SELECTOR SECTION
    base_legend = alt.Chart(
        dataLegend
    ).transform_window(
        id='rank()',
        groupby=['Sub-region Name ordered']
    )

    rect_legend = base_legend.mark_rect(
        stroke='white',
        color='lightgray',
        height=14
    ).encode(
        x=alt.X('id:O', title=None, axis=None),
        y=alt.Y('Sub-region Name ordered:N', title=None,
                sort=alt.EncodingSortField(field='Region Name', order='ascending')),
        color=alt.condition(click_country, alt.value('black'), alt.value('lightgray'))
        # legend=alt.Legend(orient='bottom')

    ).properties(width={"step": 18}, height={"step": 15}).add_selection(
        click_country
    )

    text_legend = base_legend.mark_text(
        fontSize=8,
        cursor='pointer'
    ).transform_calculate(
        label='substring(datum.country_code, 0, 2)'
    ).encode(
        x=alt.X('id:O', title=None, axis=None),
        y=alt.Y('Sub-region Name ordered:N', title=None,
                sort=alt.EncodingSortField(field='Region Name', order='ascending'),
                axis=alt.Axis(values=labelsList, domain=False)),
        text='label:N',
        color=alt.condition(click_country, alt.value('white'), alt.value('#484848')),
        tooltip=[alt.Tooltip('country_name:N', title='Country')]
    ).properties(width={"step": 18}).add_selection(
        alt.selection_single())  # selection used as a workaround for a bug on tooltips

    country_selector = (rect_legend + text_legend).facet(
        row=alt.Row(
            'Region Name:N',
            header=alt.Header(labelOrient='left'),
            # title=None,

            title="Select a Country to visualize GPI over time",
        )
    ).resolve_scale(
        y='independent'
    ).properties(
        spacing=5
    )

    # Selector Left Line:
    selectors_text = pd.DataFrame({
        'x': [0],
        'y': [0],
        'text': 'Select a country'
    })

    left_line = alt.Chart(
        selectors_text,
        height=350,
        width=3
    ).mark_rule(
        color='white'
    ).encode(
        x=alt.value(0)
    )

    # CREATE COMPOUND CHART
    entire_dashboard = (
            (rect + timeline) &
            (
                    (base + world_map) & (left_line | country_selector) |
                    (text_country & gpi_chart & prediction_chart_y & gpi_time & ranking)
            )

    ).configure(
        concat=alt.CompositionConfig(spacing=30), padding={"left": 35, "top": 5, "right": 35, "bottom": 10}
    ).configure_view(
        stroke=None
    )

    return entire_dashboard


final_chart = create_final_chart()

# Uncomment to visualize only vega-lite chart
# alt.renderers.enable('altair_viewer')
# final_chart.show()

# EXPORT TO HTML

final_chart.save('web/Dashboard_GPI_prediction.html', embed_options={'actions': False})

a_file = open('web/Dashboard_GPI_prediction.html')

jsPart = list(range(15, 32))  # JS part
jsFile = []

with open('web/Dashboard_GPI_prediction.html', 'rt') as f:
    for position, line in enumerate(f):
        if position in jsPart:
            jsFile.append(line)

with open('web/chart.js', 'w') as f:
    f.writelines(jsFile)
