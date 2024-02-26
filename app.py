import streamlit as st
import pandas as pd
import streamlit.components.v1 as components


apptitle = 'Ukrainske flyktninger i norske kommuner'


st.set_page_config(
    #page_title='',
    layout='wide'
    )


st.markdown(
    """
    #### Under utvikling
    <p style='color:red;font-weight:bold;'>Applikasjonen er under utvikling. Bruk den for å gjøre case-research, og for å bli kjent tallgrunnlaget. Feil kan forekomme.</p>
    <p style='color:red;font-weight:bold;'>Kjente feil:<p>
    <ul style='color:red;font-weight:bold;'>
    <li>Noe usikker rundt tallgrunnlaget fra IMDi, særlig rundt prikking av i kommuner med mindre enn fem flyktninger per aldersgruppe.</li>
    </ul>
    """,
    unsafe_allow_html=True
)

with st.sidebar:
    
    st.title(apptitle) 

    st.markdown(
        """
        Velg først fylke, deretter kommune og årstall. 
        """
    )

# IMPORT DATA

@st.cache_data
def load_data(file):
    return  pd.read_excel('data/'+ file +'.xlsx', dtype={'Kommunenummer':object, 'Fylkenummer': object})

def format_selection(_dict, option):
    return _dict[option]

flyktninger = load_data('app_flyktninger')
oppsummert = load_data('app_flyktninger_oppsummert')
ema = load_data('ema')
#folketall = load_data('app_flyktninger_folketall')


#CREATE MUNICIPALITY SELECTORS

kommuner = pd.Series(flyktninger.Kommune.values,index=flyktninger.Kommunenummer).to_dict()
fylker = pd.Series(flyktninger.Fylke.values,index=flyktninger.Fylkenummer).to_dict()

unike_kommuner = {key: val for key, val in kommuner.items()}
unike_fylker = {key: val for key, val in fylker.items()}

select_fylke = st.sidebar.selectbox(
    'Velg fylke',
    options = sorted(list(unike_fylker.keys())),
    format_func = lambda x: unike_fylker.get(x)
)

select_kommune = st.sidebar.selectbox(
    'Velg kommune',
    options = sorted(list({k for (k, v) in unike_kommuner.items() if k[:2] ==  select_fylke})),
    format_func = lambda x: unike_kommuner.get(x)
)

select_year = st.sidebar.selectbox(
    'Velg år',
    options = [2022, 2023, 2024]
)

#FILTER DATA FRAME BASED ON SELECTORS

flyktninger_komm = flyktninger[flyktninger['Kommunenummer'].isin([select_kommune])] 
flyktninger_komm_year = flyktninger_komm[flyktninger_komm['År'] == select_year] 
flyktninger_cols = ['Kommune', 'År', 'Kjønn', 'Aldersgruppe', 'ukrainere', 'ukr_pct', 'ukr_prikket', 'ovrige', 'ovr_pct', 'ovr_prikket', 'pop', 'pop_pct']

ema_komm = ema[ema['Kommunenummer'].isin([select_kommune])]
ema_komm_year = ema_komm[ema_komm['År'] == select_year] 

oppsummert_komm = oppsummert[oppsummert['Kommunenummer'].isin([select_kommune])]
oppsummert_komm_year = oppsummert_komm[oppsummert_komm['År'] == select_year] 

with st.sidebar:
    
    toplist = """
    ### Lag toppliste for {year}
    """.format(year = select_year)
    st.markdown(toplist)

    select_group = st.selectbox(
        'Velg gruppering',
        options=['Norge', 'Fylke', 'Lokalavis', 'SSBs sentralitetsindeks']
    )

    if select_group == 'Lokalavis':
        select_paper = st.selectbox(
            'Velg lokalavis',
            options=['TBA']
        )
        
    if select_group == 'SSBs sentralitetsindeks':
        select_centrality = st.selectbox(
            'Velg indeks',
            options=['1 - Mest sentrale', '2', '3', '4', '5', '6 - Minst sentrale']
        )
        
    if select_group == 'Norge':
        oppsummert_sidebar = oppsummert[oppsummert['År'] == select_year]
        oppsummert_sidebar = oppsummert_sidebar.sort_values('ukr_pct_pop', ascending = False)
        oppsummert_sidebar = oppsummert_sidebar[['Kommune', 'ukrainere', 'ukr_pct_pop']]

        st.dataframe(
            oppsummert_sidebar.head(50),
            hide_index = True,
            use_container_width = True,
            column_config = {
                'ukrainere': st.column_config.NumberColumn(
                'Antall', format='%.0f'
                ),
            'ukr_pct_pop': st.column_config.NumberColumn(
                'Andel av befolkning', format='%.1f %%'
                )}
            )

    if select_group == 'Fylke':
        oppsummert_sidebar = oppsummert[oppsummert['År'] == select_year]
        oppsummert_sidebar = oppsummert_sidebar[oppsummert_sidebar['Fylkenummer'] == select_fylke]
        oppsummert_sidebar = oppsummert_sidebar.sort_values('ukr_pct_pop', ascending = False)
        oppsummert_sidebar = oppsummert_sidebar[['Kommune', 'ukrainere', 'ukr_pct_pop']]

        st.sidebar.dataframe(
            oppsummert_sidebar.head(50),
            hide_index = True,
            use_container_width = True,
            column_config = {
                'ukrainere': st.column_config.NumberColumn(
                'Antall', format='%.0f'
                ),
            'ukr_pct_pop': st.column_config.NumberColumn(
                'Andel av befolkning', format='%.1f %%'
                )}
            )
        
    if select_group == 'SSBs sentralitetsindeks':
        oppsummert_sidebar = oppsummert[oppsummert['sentralitet'] == int(select_centrality[:1])]
        #oppsummert_sidebar = oppsummert_sidebar[oppsummert_sidebar['Fylkenummer'] == select_fylke]
        oppsummert_sidebar = oppsummert_sidebar.sort_values('ukr_pct_pop', ascending = False)
        oppsummert_sidebar = oppsummert_sidebar[['Kommune', 'ukrainere', 'ukr_pct_pop']]

        st.sidebar.dataframe(
            oppsummert_sidebar.head(50),
            hide_index = True,
            use_container_width = True,
            column_config = {
                'ukrainere': st.column_config.NumberColumn(
                'Antall', format='%.0f'
                ),
            'ukr_pct_pop': st.column_config.NumberColumn(
                'Andel av befolkning', format='%.1f %%'
                )}
            )


use_container_width = False #st.checkbox("Full tabellbredde", value=True)




# PAGE CONTENT

summarized = """
#### Oppsummert

{kommune} har mottatt {sum_total_ukr:,.0f} ukrainske flyktninger i perioden 2022 til starten av 2024. Det utgjør {ukr_pct_pop:.1f} prosent av befolkningen i kommunen, 
og {ukr_pct_ovr:.1f} prosent av alle innvandere som har blitt bosatt i kommunen i samme periode. 

""".format(
            kommune = unike_kommuner.get(select_kommune), 
            year = select_year, 
            sum_total_ukr = oppsummert_komm['ukrainere'].sum(),  
            #sum_total_pop = oppsummert_komm['pop'].sum(),
            ukr_pct_pop = oppsummert_komm_year['ukr_pct_pop'].sum(),
            ukr_pct_ovr = oppsummert_komm_year['ukr_pct_innvandr'].sum()
            )


st.markdown(summarized)

#st.markdown("""
##### Prikking 

#Hvis det står *Prikket (<5)*, betyr det at kommunen mottok mindre enn fem flyktninger det året. IMDi tilbakeholder eksakt antall av personvernhensyn. 
#Summeringer inkluderer bare oppgitte tall, og tar ikke hensyn til prikking. Summeringer må derfor sees på som et minimum antall bosatte flyktninger i kommunen. 
#""")


col1, col2 = st.columns([4, 5])
col3, col4 = st.columns([4, 5])
col5, col6 = st.columns([4, 5])
col7, col8 = st.columns([4, 5])

pop_text = """
        ##### Befolkningen i  {kommune}
        Tabellen viser befolkningen i kommunen, etter kjønn og alder. 
        I {year:.0f} bodde det {sum_year:,.0f} personer i {kommune}. 
        
        """.format(
            kommune = unike_kommuner.get(select_kommune), 
            year = select_year, 
            sum_year = flyktninger_komm_year['pop'].sum(),  
            sum_total = flyktninger_komm['pop'].sum()
            )

with st.container():
    with col1:
        st.markdown(pop_text)
  
    with col2:
        st.dataframe(
        flyktninger_komm_year[['År', 'Kjønn', 'Aldersgruppe', 'pop', 'pop_pct']],
        use_container_width = use_container_width,
        hide_index = True,
        column_config = {
            'År': st.column_config.NumberColumn(format="%.0f"),
            'pop': st.column_config.NumberColumn(
                'Antall', format='%.0f', step=".01"
             ),
            'pop_pct': st.column_config.NumberColumn(
                'Andel', format='%.1f %%'
             )}
        )
        
ukr_text = """
        ##### Ukrainske flyktninger (kollektiv beskyttelse)
        Tabellen viser antall bosatte ukrainske flyktninger i {kommune}. 
        I {year:.0f} ble det bosatt {sum_year:.0f} ukrainske flyktninger. 
        I hele perioden har kommunen bosatt {sum_total:.0f} ukrainske flyktninger.
        """.format(
            kommune = unike_kommuner.get(select_kommune), 
            year = select_year, 
            sum_year = flyktninger_komm_year['ukrainere'].sum(),  
            sum_total = flyktninger_komm['ukrainere'].sum()
            )

with st.container():
    with col3:
        st.markdown(ukr_text)
  
    with col4:
        st.dataframe(
        flyktninger_komm_year[['År', 'Kjønn', 'Aldersgruppe', 'ukrainere', 'ukr_pct', 'ukr_prikket']],
        use_container_width = use_container_width,
        hide_index = True,
        column_config = {
            'År': st.column_config.NumberColumn(format="%.0f"),
            'ukrainere': st.column_config.NumberColumn(
                'Antall', format='%.0f'
             ),
            'ukr_pct': st.column_config.NumberColumn(
                'Andel', format='%.1f %%'
             ),
            'ukr_prikket': st.column_config.TextColumn(
                'Prikket', 
                help = 'Prikkede data betyr at kommunen har tatt i mot mindre enn fem EMA. Data tilbakeholdes av IMDi av personvernhensyn.'
                )}
        )
        
ema_text = """
        ##### Bosatte enslige mindreårige (EMA) fra Ukraina
        I {year:.0f} bosatte {kommune} {sum_year:.0f} EMA. I hele perioden (2022 til så langt i 2024) har kommunen bosatt {sum_total:.0f} EMA.
                
        Merk at antall EMA ikke kan plusses på antall bosatte ukrainske flyktninger i tabellen over. Tabellen over medregner EMA. 
        
        Les mer om EMA [her](https://www.imdi.no/planlegging-og-bosetting/slik-bosettes-flyktninger/enslige-mindrearige-flyktninger/).
        """.format(
            kommune = unike_kommuner.get(select_kommune), 
            year = select_year, 
            sum_year = ema_komm_year['ema'].sum(),  
            sum_total = ema_komm['ema'].sum()
            )

with st.container():
    with col5:
        st.markdown(ema_text)
  
    with col6:
        st.dataframe(
        ema_komm[['År', 'ema', 'prikket']],
        use_container_width = use_container_width,
        hide_index = True,
         column_config = {
            'År': st.column_config.NumberColumn(format="%.0f"),
            'ema': st.column_config.NumberColumn(
                'Enslige mindreårige (EMA)', 
                ),
            'prikket': st.column_config.TextColumn(
                'Prikket', 
                help = 'Prikkede data betyr at kommunen har tatt i mot mindre enn fem EMA. Data tilbakeholdes av IMDi av personvernhensyn.'
                )}
        )

          
ovr_text = """
        ##### Øvrige flyktninger (ikke kollektiv beskyttelse)
        Tabellen viser antall øvrige flyktninger som også er bosatt i {kommune}, men uten kollektiv beskyttelse (ikke fra Ukraina). 
        I {year:.0f} ble {sum_year:.0f} bosatt flyktninger til kommunen. 
        I hele perioden har kommunen tatt i mot {sum_total:.0f} flyktninger uten kollektiv beskyttelse.
        """.format(
            kommune = unike_kommuner.get(select_kommune), 
            year = select_year, 
            sum_year = flyktninger_komm_year['ovrige'].sum(),  
            sum_total = flyktninger_komm['ovrige'].sum()
            )
        


with st.container():
    with col7:
        
        st.markdown(ovr_text)
  
    with col8:
        st.dataframe(
        flyktninger_komm_year[['År', 'Kjønn', 'Aldersgruppe', 'ovrige', 'ovr_pct', 'ovr_prikket']],
        use_container_width = use_container_width,
        hide_index = True,
        column_config = {
            'År': st.column_config.NumberColumn(format="%.0f"),
            'ovrige': st.column_config.NumberColumn(
                'Antall', format='%.0f'
             ),
            'ovr_pct': st.column_config.NumberColumn(
                'Andel', format='%.1f %%'
             ),
            'ovr_prikket': st.column_config.TextColumn(
                'Prikket', 
                help = 'Prikkede data betyr at kommunen har tatt i mot mindre enn fem EMA. Data tilbakeholdes av IMDi av personvernhensyn.'
                )}
        )



