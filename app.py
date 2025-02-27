import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from datetime import date
# import time
import functions
import io
import math
apptitle = ''


st.set_page_config(
    # page_title='',
    layout='wide'
)


end_time = date(2024, 4, 22)

data_imdi_received_date = '13.11.2024'


with st.sidebar:

    imgcol1, imgcol2, imgcol3 = st.columns([1, 4, 1])

    with imgcol1:
        st.write(' ')

    with imgcol2:
        st.image("img/logo-bok.png")

    with imgcol3:
        st.write(' ')

    st.title(apptitle)

    #st = """
    #{time}
    #""".format(time=functions.countdown(end_time))
    #st.markdown(sperrefrist.format('%d'))

    #st.markdown(
    #    """
    #    <p style='color:red;font-weight:bold;'>Ikke publiser saker før sperrefristen. </p>
    #    """,
    #    unsafe_allow_html=True
    #)

    st.markdown(
        """
        Velg først fylke, deretter kommune og årstall. 
        
        Se fanen 'Tallgrunnlag' for datakilder og detaljert tallgrunnlag.
        """
    )


# --------- #
# Functions #
# --------- #

@st.cache_data
def load_data(file):
    return pd.read_excel('data/' + file + '.xlsx', dtype={'Kommunenummer': object, 'kommnr': object, 'Fylkenummer': object})


def format_selection(_dict, option):
    return _dict[option]


def check_ano(vec):
    x = vec.str.contains('<5').sum()
    if x > 0:
        return 'Merk at det er {count} celler som er anonymisert (mindre enn fem flyktninger.)'.format(count=x)
    else:
        return ''


# ----------- #
# IMPORT DATA #
# ----------- #
flyktninger = load_data('app_flyktninger')
oppsummert = load_data('app_flyktninger_oppsummert')
ema = load_data('ema')
ukr_mottak = load_data('ukrainere_mottak_310124')
kostra_about = load_data('kostra_description')
tilskudd = load_data('tilskudd')

# folketall = load_data('app_flyktninger_folketall')

# ------------------------------------------------------------------- #
# Create a dictionary describing the coverage area of each news paper #
# ------------------------------------------------------------------- #

lla = load_data('lla')
coverage = {g: d['kommnr'].values for g, d in lla.groupby('avis')}

# ----------------------------- #
# Municipality selectors #
# ----------------------------- #

# Create a dictionary of unique municipalities, counties, electional districts
kommuner = pd.Series(oppsummert.Kommune.values,
                     index=oppsummert.Kommunenummer).to_dict()
fylker = pd.Series(oppsummert.Fylke.values,
                   index=oppsummert.Fylkenummer).to_dict()
valgdistrikt = pd.Series(oppsummert.Valgdistrikt.values,
                         index=oppsummert.Valgdistriktnummer).to_dict()
kommuner_valgdistrikt = pd.Series(
    oppsummert.Valgdistrikt.values, index=oppsummert.Kommunenummer).to_dict()
kommuner_sentralitet = pd.Series(
    oppsummert.sentralitet.values, index=oppsummert.Kommunenummer).to_dict()
kommuner_kostra = pd.Series(
    oppsummert.kostranavn.values, index=oppsummert.Kommunenummer).to_dict()


# Use tuples to alphabetically sort the municipalities and counties
kommuner_sorted = sorted(kommuner.items(), key=lambda kv: (kv[1], kv[0]))
fylker_sorted = sorted(fylker.items(), key=lambda kv: (kv[1], kv[0]))
valgdistrikt_sorted = sorted(
    valgdistrikt.items(), key=lambda kv: (kv[1], kv[0]))


select_fylke = st.sidebar.selectbox(
    'Velg fylke',
    # using lambda in order to get the first element (municipality code) in tuple
    options=map(lambda x: x[0], fylker_sorted),
    # display the names of the counties, not the codes
    format_func=lambda x: fylker.get(x)
)

select_kommune = st.sidebar.selectbox(
    'Velg kommune (2024)',
    # get the municipalities for the selected county
    options=[j for i in kommuner_sorted for j in i if j[:2] == select_fylke],
    # display the names of the municipalities, not the codes
    format_func=lambda x: kommuner.get(x)
)

if select_kommune == '1508' or select_kommune == '1580':
    st.sidebar.markdown("""
        Merk: Ålesund ble delt i Ålesund og Haram kommuner 01.01.2024. Tallene for 2022 og 2023 er forbundet med 1507-Ålesund.
        """)

select_year = st.sidebar.selectbox(
    'Velg år',
    options=[2022, 2023, 2024]
)

# ------------------------------------------- #
# Filter data and create different dataframes #
# ------------------------------------------- #

# test

# Downloadable data frame
dfdownload = oppsummert[['Kommunenummer', 'Kommune', 'År', 'ovrige',
                         'ovr_prikket', 'innvandr_pct_pop', 'ukrainere', 'ukr_prikket', 'ukr_pct_pop']]
dfdownload = dfdownload.rename(columns={'ovrige': 'Øvrige innvandrere', 'ovr_pct_pop': 'Øvrige innvandrere som andel av befolkning',
                               'ovr_prikket': 'Øvrige - kommentar', 'ukrainere': 'Ukrainere', 'ukr_prikket': 'Ukrainere - kommentar', 'ukr_pct_pop': 'Ukrainere som andel av befolkning'})
dfdownload = dfdownload.sort_values(['Kommunenummer', 'År'])

# dataframe with one line per year, per municipality.
oppsummert_komm = oppsummert[oppsummert['Kommunenummer'].isin([
                                                              select_kommune])]
oppsummert_komm_year = oppsummert_komm[oppsummert_komm['År'] == select_year]
oppsummert_komm_2024 = oppsummert_komm[oppsummert_komm['År'] == 2024]

# oppsummert_year = oppsummert[oppsummert['Kommune'] == 'Aremark']
# print(oppsummert_year['ukrainere'])

# Dataframe with 4 lines (gender x age) per year, per municipality
flyktninger_fylke = flyktninger[flyktninger['Fylkenummer'].isin([
                                                                select_fylke])]
flyktninger_komm = flyktninger[flyktninger['Kommunenummer'].isin([
                                                                 select_kommune])]
flyktninger_komm_year = flyktninger_komm[flyktninger_komm['År'] == select_year]
flyktninger_cols = ['Kommune', 'År', 'Kjønn', 'Aldersgruppe', 'ukrainere',
                    'ukr_pct', 'ukr_prikket', 'ovrige', 'ovr_pct', 'ovr_prikket', 'pop', 'pop_pct']

# Dataframe with enslige mindreårige. Both ukrainians and other refugees.
ema_komm = ema[ema['Kommunenummer'].isin([select_kommune])]
ema_komm_year = ema_komm[ema_komm['År'] == select_year]

# Dataframe with anmodningstall for the selcted kommune.
# Note: Only available for 2024
anmodninger = oppsummert[oppsummert['Kommunenummer'].isin([select_kommune])]
anmodninger = anmodninger[anmodninger['År'] == 2024]
anmodninger = anmodninger[['Kommune', 'Kommunenummer', 'ema_anmodet_2024', 'ema_vedtak_2024', 'ema_vedtak_2024_string', 'innvandr_anmodet',
                           'innvandr_vedtak', 'innvandr_vedtak_string', 'innvandr_bosatt', 'ukr_bosatt',  'innvandr_avtalt_bosatt', 'ukr_avtalt_bosatt']]

# dataframe with asylmottak in selected kommune
ukr_mottak_komm = ukr_mottak[ukr_mottak['Kommunenummer'].isin([
                                                              select_kommune])]
ukr_mottak_komm = ukr_mottak_komm[['mottak_navn', 'ukr_mottak']]

# Create bullet points of asylmottak in the selected municipality
ukr_mottak_bool = False
ukr_mottak_string = 'Per 31.01.2024 bor det også ukrainere på asylmottak i kommunen. Disse har kommunen også ansvar for mens de venter på å bli bosatt.\n'
for mottak, ukr in ukr_mottak_komm.itertuples(index=False):
    ukr_mottak_bool = True
    ukr_mottak_string += '* ' + mottak + ': ' + str(ukr) + ' ukrainere  \n'


# Dataframe with tilskudd the municipality has received from IMDi
tilskudd_komm = tilskudd[tilskudd['Kommunenummer'].isin([select_kommune])]
tilskudd_komm_year = tilskudd_komm[tilskudd_komm['År'] == select_year]
tilskudd_komm_year = tilskudd_komm_year[[
    'Tilskuddstype', 'Antall', 'Kommentar']]
tilskudd_string = 'I ' + str(select_year) + \
    ' mottok kommunen følgende tilskudd fra Imdi: \n'

tilskudd_komm_total = tilskudd_komm[tilskudd_komm['Tilskuddstype'] == 'Totalt']
tilskudd_komm_total = tilskudd_komm_total['Antall'].sum()


# ------------------------------------------------------ #
# In the sidebar, make a top list for the selected group #
# ------------------------------------------------------ #
with st.sidebar:

    st.markdown('### Last ned ')

    buffer = io.BytesIO()

    downloadcol1, downloadcol2, _ = st.columns([1, 1, 4])

    with downloadcol1:

        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:

            dfdownload.to_excel(writer, sheet_name='Ark1', index=False)
            writer._save()

            download = st.download_button(
                label='Data',
                data=buffer,
                file_name='ukraina.xlsx',
                mime='application/vnd.ms-excel'
            )
    with downloadcol2:
        # with open("img/logo.jpg", "rb") as file:
        #        btn = st.download_button(
        #            label="Logo",
        #            data=file,
        #            file_name="samarbeidsdesken_logo_ukraina.jpg",
        #            mime="image/jpg"
        #        )

        with open("img/logo.zip", "rb") as fp:
            btnzip1 = st.download_button(
                label="Logo",
                data=fp,
                file_name="logo.zip",
                mime="application/zip"
            )

    toplist = """
    ### Lag toppliste for {year}
    
    *Inkluderer ikke anonymiserte grupper. Se fanen Tallgrunnlag. 
    """.format(year=select_year)
    st.markdown(toplist)

    select_group = st.selectbox(
        'Velg gruppering',
        options=[fylker.get(select_fylke), kommuner_valgdistrikt[select_kommune], 'SSBs sentralitetsindeks',
                 'KOSTRA-gruppe', 'Hele landet', 'Lokalavis (dekningsområde)', 'ROBEK']
    )

    if select_group == 'Lokalavis (dekningsområde)':
        select_paper = st.selectbox(
            'Velg lokalavis',
            options=coverage.keys()
        )

    # if select_group == 'SSBs sentralitetsindeks':
    #    select_centrality = st.selectbox(
    # 'Velg indeks',
     #       options=['1 - Mest sentrale', '2', '3', '4', '5', '6 - Minst sentrale']
     #   )

    # If the user wants a top list for the whole country
    if select_group == 'Hele landet':
        oppsummert_sidebar = oppsummert[oppsummert['År'] == select_year]
        oppsummert_sidebar = oppsummert_sidebar.sort_values(
            'ukr_pct_pop', ascending=False)
        oppsummert_sidebar['asterix'] = oppsummert_sidebar.apply(
            functions.make_asterix, axis=1)

        oppsummert_sidebar = oppsummert_sidebar[[
            'Kommune', 'ukrainere', 'ukr_pct_pop', 'asterix']]

        st.dataframe(
            oppsummert_sidebar,
            hide_index=True,
            use_container_width=True,
            column_config={
                'ukrainere': st.column_config.NumberColumn(
                    'Antall ukrainere', format='%.0f'
                ),
                'ukr_pct_pop': st.column_config.NumberColumn(
                    'Andel av befolkning', format='%.2f %%'
                ),
                'asterix': st.column_config.TextColumn(
                    ''
                )}
        )

    # If the user wants a top list by county
    if select_group == kommuner_valgdistrikt[select_kommune]:
        oppsummert_sidebar = oppsummert[oppsummert['År'] == select_year]
        oppsummert_sidebar = oppsummert_sidebar[oppsummert_sidebar['Valgdistrikt']
                                                == kommuner_valgdistrikt[select_kommune]]
        oppsummert_sidebar = oppsummert_sidebar.sort_values(
            'ukr_pct_pop', ascending=False)
        # oppsummert_sidebar = oppsummert_sidebar[['Kommune', 'ukrainere', 'ukr_pct_pop', 'ukr_prikket']]

        oppsummert_sidebar['asterix'] = oppsummert_sidebar.apply(
            functions.make_asterix, axis=1)

        oppsummert_sidebar = oppsummert_sidebar[[
            'Kommune', 'ukrainere', 'ukr_pct_pop', 'asterix']]

        st.sidebar.dataframe(
            oppsummert_sidebar,
            hide_index=True,
            use_container_width=True,
            column_config={
                'ukrainere': st.column_config.NumberColumn(
                    'Antall ukrainere', format='%.0f'
                ),
                'ukr_pct_pop': st.column_config.NumberColumn(
                    'Andel av befolkning', format='%.2f %%'
                ),
                'asterix': st.column_config.TextColumn(
                    ''
                )
            }
        )

    # If the user wants a top list by county
    if select_group == fylker.get(select_fylke):
        oppsummert_sidebar = oppsummert[oppsummert['År'] == select_year]
        oppsummert_sidebar = oppsummert_sidebar[oppsummert_sidebar['Fylkenummer'] == select_fylke]
        oppsummert_sidebar = oppsummert_sidebar.sort_values(
            'ukr_pct_pop', ascending=False)
        oppsummert_sidebar['asterix'] = oppsummert_sidebar.apply(
            functions.make_asterix, axis=1)

        oppsummert_sidebar = oppsummert_sidebar[[
            'Kommune', 'ukrainere', 'ukr_pct_pop', 'asterix']]

        st.sidebar.dataframe(
            oppsummert_sidebar,
            hide_index=True,
            use_container_width=True,
            column_config={
                'ukrainere': st.column_config.NumberColumn(
                    'Antall ukrainere', format='%.0f'
                ),
                'ukr_pct_pop': st.column_config.NumberColumn(
                    'Andel av befolkning', format='%.2f %%'
                ),
                'asterix': st.column_config.TextColumn(
                    ''
                )}
        )

    # If the user wants a top list by SSBs centrality index
    if select_group == 'SSBs sentralitetsindeks':
        oppsummert_sidebar = oppsummert[oppsummert['sentralitet']
                                        == kommuner_sentralitet[select_kommune]]
        oppsummert_sidebar = oppsummert_sidebar[oppsummert_sidebar['År'] == select_year]
        # oppsummert_sidebar = oppsummert_sidebar[oppsummert_sidebar['Fylkenummer'] == select_fylke]
        oppsummert_sidebar = oppsummert_sidebar.sort_values(
            'ukr_pct_pop', ascending=False)
        oppsummert_sidebar['asterix'] = oppsummert_sidebar.apply(
            functions.make_asterix, axis=1)

        oppsummert_sidebar = oppsummert_sidebar[[
            'Kommune', 'ukrainere', 'ukr_pct_pop', 'asterix']]

        sentralitet_description = """
        Sentralitetsindeksen er en måte å måle hvor sentral en kommune er med grunnlag i befolkning, arbeidsplasser og servicetilbud. Indeksen er utviklet av SSB.
        
        Indeksen går fra 1 (mest sentral) til 6 (minst sentral). Kommuner med sentralitet 4, 5 og 5 forstås som distriktskommuner. 
        
        {kommune} har sentralitet {sentralitet}.
        """.format(
            kommune=kommuner.get(select_kommune),
            sentralitet=kommuner_sentralitet[select_kommune]
        )

        st.sidebar.markdown(sentralitet_description)

        st.sidebar.dataframe(
            oppsummert_sidebar,
            hide_index=True,
            use_container_width=True,
            column_config={
                'ukrainere': st.column_config.NumberColumn(
                    'Antall ukrainere', format='%.0f'
                ),
                'ukr_pct_pop': st.column_config.NumberColumn(
                    'Andel av befolkning', format='%.2f %%'
                ),
                'asterix': st.column_config.TextColumn(
                    ''
                )}
        )

    # If the user wants a top list by SSBs centrality index
    if select_group == 'KOSTRA-gruppe':

        oppsummert_sidebar = oppsummert[oppsummert['kostranavn']
                                        == kommuner_kostra[select_kommune]]
        oppsummert_sidebar = oppsummert_sidebar[oppsummert_sidebar['År'] == select_year]
        # oppsummert_sidebar = oppsummert_sidebar[oppsummert_sidebar['Fylkenummer'] == select_fylke]
        oppsummert_sidebar = oppsummert_sidebar.sort_values(
            'ukr_pct_pop', ascending=False)
        oppsummert_sidebar['asterix'] = oppsummert_sidebar.apply(
            functions.make_asterix, axis=1)

        oppsummert_sidebar = oppsummert_sidebar[[
            'Kommune', 'ukrainere', 'ukr_pct_pop', 'asterix']]

        kostra_about_komm = kostra_about[kostra_about['kostragruppe']
                                         == kommuner_kostra[select_kommune]]

        sentralitet_description = """
        KOSTRA-gruppene er utviklet av SSB for å enklere sammenligne like kommuner. Gruppene er satt sammen basert på folkemengde og økonomiske rammebetingelser. 
        
        Les mer om KOSTRA-gruppene [her](https://www.ssb.no/offentlig-sektor/kostra/statistikk/kostra-kommune-stat-rapportering/om-kostra/kostra-gruppene).
        
        {kommune} er i Kostra-gruppe {kostra_gruppe}, som innebærer:  
        * Folkemengde: {folkemengde}  
        * Bundne kostnader: {kostnader}
        * Frie disponible inntekter: {inntekter}
        """.format(
            kommune=kommuner.get(select_kommune),
            kostra_gruppe=kommuner_kostra[select_kommune],
            folkemengde=kostra_about_komm['folkemengde'].iloc[0],
            kostnader=kostra_about_komm['bundekostnader'].iloc[0],
            inntekter=kostra_about_komm['frie_disponible_inntekter'].iloc[0]
        )

        st.sidebar.markdown(sentralitet_description)

        st.sidebar.dataframe(
            oppsummert_sidebar,
            hide_index=True,
            use_container_width=True,
            column_config={
                'ukrainere': st.column_config.NumberColumn(
                    'Antall ukrainere', format='%.0f'
                ),
                'ukr_pct_pop': st.column_config.NumberColumn(
                    'Andel av befolkning', format='%.2f %%'
                ),
                'asterix': st.column_config.TextColumn(
                    ''
                )}
        )

    if select_group == 'Lokalavis (dekningsområde)':
        if pd.isna(coverage[select_paper][0]):
            st.markdown('''
                        Dekningsområdet for denne avisen er ikke klart. Hvis avisen er riksdekkende, velg "Norge" i stedet for "Lokalavis" i velgeren.
                        Hvis avisens dekningsområdet må defineres med postnummer eller andre geografiske kjennetegn (feks kyst), arbeider vi med å sammenstille dette. 
                        ''')

        oppsummert_sidebar = oppsummert[oppsummert['Kommunenummer'].isin(
            coverage[select_paper])]
        oppsummert_sidebar = oppsummert_sidebar[oppsummert_sidebar['År'] == select_year]
        # oppsummert_sidebar = oppsummert_sidebar[oppsummert_sidebar['Fylkenummer'] == select_fylke]
        oppsummert_sidebar = oppsummert_sidebar.sort_values(
            'ukr_pct_pop', ascending=False)
        oppsummert_sidebar['asterix'] = oppsummert_sidebar.apply(
            functions.make_asterix, axis=1)

        oppsummert_sidebar = oppsummert_sidebar[[
            'Kommune', 'ukrainere', 'ukr_pct_pop', 'asterix']]

        st.sidebar.dataframe(
            oppsummert_sidebar,
            hide_index=True,
            use_container_width=True,
            column_config={
                'ukrainere': st.column_config.NumberColumn(
                    'Antall ukrainere', format='%.0f'
                ),
                'ukr_pct_pop': st.column_config.NumberColumn(
                    'Andel av befolkning', format='%.2f %%'
                ),
                'asterix': st.column_config.TextColumn(
                    ''
                )}
        )

    if select_group == 'ROBEK':
        oppsummert_sidebar = oppsummert[oppsummert['År'] == select_year]
        oppsummert_sidebar = oppsummert_sidebar[oppsummert_sidebar['robek'] == 'robek']
        oppsummert_sidebar = oppsummert_sidebar.sort_values(
            'ukr_pct_pop', ascending=False)
        oppsummert_sidebar['asterix'] = oppsummert_sidebar.apply(
            functions.make_asterix, axis=1)

        oppsummert_sidebar = oppsummert_sidebar[[
            'Kommune', 'ukrainere', 'ukr_pct_pop', 'asterix']]

        if oppsummert_komm_year['robek'].str.contains('ikke robek').iloc[0]:
            robek_string = """
            Liste med alle ROBEK-kommuner. {kommune} er ikke en ROBEK-kommune.
            
            """.format(
                kommune=kommuner.get(select_kommune)
            )
        else:
            robek_string = """
            Liste med alle ROBEK-kommuner. {kommune} er en ROBEK-kommune.
            
            """.format(
                kommune=kommuner.get(select_kommune)
            )

        st.markdown(robek_string)

        st.markdown('''
                    ROBEK er et register over kommuner som er i økonomisk ubalanse eller som ikke har vedtatt økonomiplanen, årsbudsjettet eller årsregnskapet innenfor de fristene som gjelder.
                    
                    Kommuner i ROBEK er underlagt statlig kontroll. Les mer om ROBEK [her](https://www.regjeringen.no/no/tema/kommuner-og-regioner/kommuneokonomi/robek-2/id449305/).
                    ''')

        st.dataframe(
            oppsummert_sidebar,
            hide_index=True,
            use_container_width=True,
            column_config={
                'ukrainere': st.column_config.NumberColumn(
                    'Antall ukrainere', format='%.0f'
                ),
                'ukr_pct_pop': st.column_config.NumberColumn(
                    'Andel av befolkning', format='%.2f %%'
                ),
                'asterix': st.column_config.TextColumn(
                    ''
                )}
        )


use_container_width = False  # st.checkbox("Full tabellbredde", value=True)


# ----------------------- #
# Main content of the app #
# ----------------------- #

# create different tabs for the content
tab1, tab2, tab6, tab3, tab4, tab5, tab7, tab8 = st.tabs(['Dette er saken', 'Slik er det i din kommune', 'Mulige nyhetssaker',
                                                         'Slik kan du gå fram', 'Tallgrunnlag', 'Ekspertkilder og rapporter', 'Fakta og begreper', 'Publisering'])

# In tab 1: Dette er saken
with tab1:

    national_col1, national_col2 = st.columns([5, 4])

    # with national_col1:
    national_text = """

Researchpakken blir jevnlig oppdatert ettersom asylfeltet stadig er i bevegelse.

**Logg:**

- April 24: Først publisert. 
- 28.11.24: Oppdaterte tall fra Imdi og intervju med direktør i Imdi. 
- 03.02.25: Ny rapport fra OsloMet, og intervju med forsker Vilde Hernes. 

--------


355 kommuner har til sammen bosatt **76.126** ukrainske flyktninger siden krigen startet i 2022 (per. 13.11.2024). I samme periode ble det bosatt 10.965 flyktninger fra andre land. 

**Etter å ha bosatt rundt 30.000 i året, forventes det nå en klar nedgang.**

De siste to årene har nesten samtlige kommuner rustet opp tjenesteapparatet for å ta imot rekordhøye antall som skal bosettes. Med UDIs prognoser om færre ankomster fra Ukraina i 2025 er det mange kommuner som nå må nedskalere flyktningtjenestene sine. Hva skal de da gjøre med alle de nylig har ansatt? Lærere for eksempel? 

Andre kommuner har fortsatt sprengt kapasitet.


Imdi har bedt kommunen bosette 18.900 flyktninger i løpet av 2025. Av dem er 15 500 fra Ukraina.

Nå er det opp til hver enkelt kommune å avgjøre hvor mange og hvilke flyktninger de klarer å bosette. 

Sjekk hvor mange Imdi har [anmodet din kommune om å bosette.](https://www.imdi.no/planlegging-og-bosetting/bosettingstall/) Og - hva sier kommunestyret?

-------

**Store kapasitetsutfordringer i kommunene**

– Det er klart at etter tre år med historisk høy bosetting, opplever kommunene kapasitetsutfordringer på ulike områder, sier Libe Rieber-Mohn, direktør i Integrerings- og mangfoldsdirektoratet (Imdi, [klikk her](https://kommunikasjon.ntb.no/presserom/89626/imdi/mi?item=image-17983499) for pressebilde). 

– Vi ser at flere kommuner nå sliter med å oppdrive boliger som ligger nær kollektivtransport og kommunale tilbud. Helsesektoren, skoler og barnehager har også store kapasitetsutfordringer.  

**En økning av barn og unge som kommer alene**

Mens det totale antallet flyktninger går ned neste år, forventes det en 20 prosent økning i bosetting av enslige mindreårige flyktninger, ifølge Imdi. I overkant av halvparten av disse kommer fra Ukraina. 

– Vi anmoder nå en rekke kommuner om å ta imot barn og unge som kommer hit uten foreldre eller andre omsorgspersoner. De er i en spesielt sårbar situasjon, men vi skal ikke glemme at det er mange ressurssterke ungdommer blant dem, sier Rieber-Mohn. 

– Blant de under 18 år, ser vi en dobling av andelen 16-17-åringer fra 2022 til 2024, og det er hovedsakelig en økning i unge gutter, sier Vilde Hernes, forsker ved OsloMet. 
 
– Vi antar at disse ungdommene reiser eller blir sendt fra Ukraina mens det fortsatt er lovlig, med tanke på reiseforbudet for ukrainske menn mellom 18-60 år, sier hun. 

Mange av barna som kommer alene er også 15 år eller yngre. Det er en gruppe som er ressurskrevende for en kommune å bosette. 

– Noen kommuner har lang erfaring med å bosette enslige mindreårige og har god kompetanse på det. Men siden det nå er en såpass kraftig økning, må vi spørre noen flere kommuner som ikke har bosatt enslige mindreårige de siste årene. Disse må også spesifisere hva slags boløsninger kommunene har tilgjengelig, sier Rieber-Mohn.

**Flere eldre legger mer press på kommunene**

Cirka fire prosent av de bosatte flyktningene fra Ukraina  er over 66 år. Dette er en annen gruppe enn Norge vanligvis bosetter, og de trenger gjerne andre tjenester enn det kommunene har vært vant med å tilby tidligere. 
   
– Det er en stor omveltning å skulle ta imot en så stor andel med eldre flyktninger, sier Vilde Hernes ved OsloMet.  

– Det er flere 80- og 90-åringer som har kommet fra Ukraina. Som alle andre eldre vil behovene variere, det gjelder også eldre flyktningers behov for helsetjenester, omsorgstilbud og andre typer tiltak, sier Rieber-Mohn.  

**Midlertidighet gjør det vanskelig å skalere opp** 
    
I to og et halvt år har flyktningene fra Ukraina fått midlertidig kollektiv beskyttelse i Norge. 

Men i september 2024 endret regjeringen på dette. De som kommer fra områder i Ukraina som UDI vurderer som trygge, får ikke lenger kollektiv beskyttelse, men kan søke om asyl på lik linje med andre asylsøkere. 

De som har fått kollektiv beskyttelse, er fortsatt i landet på ubestemt tid, noe som fører til flere utfordringer for ukrainerne: 

— Ukrainere opplever at den midlertidige oppholdstillatelsen gjør at arbeidsgivere er mer skeptiske til å ansette dem i faste stillinger, sier Vilde Hernes ved OsloMet. 
 
— Mange ønsker en fast fulltidsjobb, og sier at midlertidige stillinger gjør den generelle usikkerheten de lever med enda større, sier hun. 
 
— Usikkerheten rundt om og hvor lenge de vil får bli i Norge gjør det vanskelig å planlegge livet og tenke langsiktig. 

For kommunen er det også problematisk: 

— Å oppskalere tjenester innenfor skole, barnehage og helsetjenester er en veldig stor risiko for kommunene fordi ukrainere har midlertidig tillatelse, sier Hernes. 
    
— Hvis ukrainerne må hjem, slutter kommunene å få tilskudd fra Imdi, og de taper dermed penger. 


**En av tre ukrainere i jobb**

– Sammenlignet med andre grupper av flyktninger blir ukrainerne raskere sysselsatt, viser ny [forskning fra SSB.](https://www.ssb.no/arbeid-og-lonn/sysselsetting/artikler/en-av-tre-ukrainere-er-i-jobb) 

– Andelen ukrainere i jobb er omtrent 38 prosent for dem som har bodd i Norge ett år, og omtrent 48 prosent for dem som kom for to år siden, ifølge rapporten. 

– Manglende norskferdigheter er fortsatt den klart største barrieren for å få jobb i Norge, sier Vilde Hernes fra OsloMet. 
 
– Ukrainere har et kortere introduksjonsprogram enn flyktninger fra andre land. Hvis de ikke kommer seg ut i jobb, innebærer det økte sosialhjelpeutgifter, sier Libe Rieber-Mohn fra Imdi. 

Kommunen mottar integreringstilskudd fra Imdi i fem år. Hvis flyktningen kommer ut i jobb etter introduksjonsprogrammet, kan kommunen selv benytte store deler av dette tilskuddet til andre ting. 

– Det er en vinn-vinn-situasjon, både for dem som kommer ut i arbeid og for kommunens økonomi, sier Rieber-Mohn. 

**De over 55 år får ikke introduksjonsprogram**

Siden krigen startet, har Norge bosatt 9500 ukrainske flyktninger over 55 år.  Denne gruppen har ikke rett på introduksjonsprogram. 

– Regjeringen har nå et forslag ute til høring om å øke aldersgrensen til 60 år, sier Rieber-Mohn. 

– Det vil være mer kostnadseffektivt å la denne gruppen delta på et introduksjonsprogram, slik at de kommer seg ut i jobb, fremfor å bli sosialstønadsmottakere, sier hun. 


    """.format(
        data_imdi_received_date=data_imdi_received_date
    )

    
    
    st.markdown(
        national_text
    )

    # with national_col2:
    #    with st.expander("Fakta og begreper om bosetting av ukrainere"):

    #        pass


# Tab 2: Statistical description of the municipality
with tab2:

    summarized = """
    
    ##### Bosatte
    
    {kommune} har bosatt {sum_total_ukr:,.0f} ukrainske flyktninger siden krigen brøt ut. De utgjør {ukr_pct_pop:.2f} prosent av befolkningen, og {ukr_pct_ovr:.2f} prosent av alle bosatte flyktninger i samme periode. 
    
    I **{year}** {erble} bosatt {sum_total_ukr_year} ukrainere i kommunen, noe som utgjør {ukr_pct_pop_year:.2f} prosent av befolkningen.  {anonym}
    
    """.format(
        kommune=kommuner.get(select_kommune),
        year=select_year,
        sum_total_ukr=oppsummert_komm['ukrainere'].sum(),
        sum_total_ukr_year=oppsummert_komm_year['ukrainere'].sum(),
        ukr_pct_pop_year=oppsummert_komm_year['ukr_pct_pop'].sum(),
        # sum_total_pop = oppsummert_komm['pop'].sum(),
        ukr_pct_pop=(oppsummert_komm['ukrainere'].sum(
        )/oppsummert_komm_2024['pop'].sum())*100,
        ukr_pct_ovr=(oppsummert_komm['ukrainere'].sum(
        )/oppsummert_komm['innvandr'].sum())*100,
        erble='ble det' if select_year != 2024 else 'er det så langt',
        anonym='' if oppsummert_komm_year['ukr_prikket'].isnull(
        ).iloc[0] else 'Merk at vi ikke vet eksakt antall på grunn av anonymisering. Se fanen Tallgrunnlag.',
        data_imdi_received_date=data_imdi_received_date
    )
    summarized_anmodning = """
    
    ##### Anmodninger
    Integrerings- og mangfoldsdirektoratet (Imdi) har anmodet kommunen om å bosette {innvandr_anmodet:,.0f} flyktninger i  2024. Det inkluderer både ukrainske og øvrige flyktninger. Kommunen {innvandr_vedtak_string}. 
     
     {kommune} {ema_vedtak_2024_string}
    """.format(
        kommune=kommuner.get(select_kommune),
        innvandr_anmodet=anmodninger['innvandr_anmodet'].iloc[0],
        innvandr_vedtak_string=anmodninger['innvandr_vedtak_string'].iloc[0],
        ema_vedtak_2024_string=anmodninger['ema_vedtak_2024_string'].iloc[0],
    )

    summarized_rank = """
    
    I **{year}** {erkom} {kommune} på {fylke_rank:}plass i fylket, og {national_rank}plass i hele landet i en rangering over hvilke kommuner som tar imot flest ukrainske flyktninger etter befolkningsstørrelse. 
    
    Tall mottatt fra Imdi {data_imdi_received_date}.
    """.format(
        kommune=kommuner.get(select_kommune),
        year=select_year,
        fylke_rank='jumbo' if math.isnan(oppsummert_komm_year['fylke_rank'].iloc[0]) else str(
            '{:.0f}'.format(oppsummert_komm_year['fylke_rank'].iloc[0])) + '. ',
        national_rank='jumbo' if math.isnan(oppsummert_komm_year['national_rank'].iloc[0]) else str(
            '{:.0f}'.format(oppsummert_komm_year['national_rank'].iloc[0])) + '. ',
        erkom='kom' if select_year != 2024 else 'er',
        data_imdi_received_date=data_imdi_received_date
    )

    if select_year == 2024:
        st.markdown(summarized_anmodning)

    st.markdown(summarized)
    st.markdown(summarized_rank)
    if ukr_mottak_bool:
        st.markdown(ukr_mottak_string)

    if select_year == 2024:
        fastlege = """
        ##### Fastlegekapasitet
        
        Det er ikke tilgjengelig tall for 2024. Derfor gjengis tall fra 2023.
        
        {lege_category}.

        """.format(
            year=select_year,
            kommune=kommuner.get(select_kommune),
            legeliste_n=oppsummert_komm_year['legeliste_n'].iloc[0],
            legeliste_pct=oppsummert_komm_year['legeliste_pct'].iloc[0],
            lege_category=oppsummert_komm_year['lege_category'].iloc[0]
        )

    else:

        fastlege = """
        ##### Fastlegekapasitet
            
        {lege_category}.
        
        """.format(
            year=select_year,
            kommune=kommuner.get(select_kommune),
            # legeliste_n = oppsummert komm_year['legeliste_n'].iloc[0],
            # legeliste_pct = oppsummert_komm_year['legeliste_pct'].iloc[0],
            lege_category=oppsummert_komm_year['lege_category'].iloc[0]
        )

    st.markdown(fastlege)

    st.markdown('''
            ##### Tilskudd fra Imdi
            
            Kommunene mottar tilskudd for flyktninger de fem første årene de er bosatt i kommunen. 
            
            I 2022 og 2023 har kommunen mottatt totalt {sum_tilskudd:,.0f} millioner kroner i tilskudd fra Imdi.  
            
            Beløpet skal dekke utgifter til bosetting og integrering av ukrainske flyktninger, i tillegg til flyktninger fra andre land.
            
            Merk at enkelte verdier kan være tilbakeholdt av Imdi av anonymiseringshensyn.
            
            {tabellen}
            
            '''.format(
                year=select_year,
                sum_tilskudd=tilskudd_komm_total/1000000,
                tabellen='Tabellen viser tilskudd gitt i **' +
                str(select_year) + '** for alle flyktninger bosatt i kommunen de siste fem årene.' if select_year != 2024 else 'Vi vet ennå ikke hvor mye tilskuddspenger kommunen får i 2024.'
                )
                )

    st.dataframe(
        tilskudd_komm_year.style.format(thousands=" ", precision=0),
        hide_index=True,
        column_config={
            'Antall': st.column_config.NumberColumn(
                'Sum',
                # format="kr %:,f",
                # format = None,
                # min_value = 0,
                # max_value = tilskudd_komm_total
            ),
            'Kommentar': st.column_config.TextColumn(
                'Kommentar'
            )
        },
        use_container_width=True
    )

with tab6:
    st.markdown("""
    

#### Nye forslag saker: 

1. Hvor mange flyktninger er din kommune anmodet om å bosette? Hva sier kommunestyret - klarer kommunen å bosette så mange? Hvor ligger utfordringene? 
2. Er din kommune anmodet om å bosette noen barn eller unge som kommer alene? Er dette en gruppe kommunen er rustet til å bosette? 
3. Er det mange eldre ukrainere bosatt i din kommune? Hvordan opplever kommunen presset på helsesektoren og andre omsorgstjenester som følge av dette? 
4. Er det flere flyktninger over 55 år i din kommune som ikke får delta på introduksjonsprogram? Hvilke konsekvenser får dette? 
5. Hvor mange i din kommune har kommet ut i jobb etter introduksjonsprogrammet? Sammenlign med resten av landet. Hvilke jobber har de fått? 
6. Hvordan har flyktningstrømmen påvirket kommuneøkonomien? Sitter de igjen med overskudd, eller underskudd? 
7. Har kommunen bosatt like mange flyktninger som de sa de skulle i 2024?  

*Oppdatert 28.11.24, Samarbeidsdesken*

-------
#### Tidligere forslag: 

##### Vil bosette færre flyktninger enn kommunen er anmodet om
    
**Mulig sak**: Kommunen ble anmodet om å bosette x antall flykninger, men har bare sagt ja til y.  
    
**Mulig historie**: 
- En ukrainsk flyktning som sitter på asylmottak og venter på å få tildelt en kommune. 
- En som er bosatt og blitt en ressurs for kommunen. 
- En rektor, sykepleier o.l. som sier at kapasiteten er sprengt. 
    
**Høre med kommunedirektøren:** 
- Hva er grunnen til at kommunen ikke ønsker å bosette antallet flyktninger de er bedt om? 
- Burde de ikke ta imot flere? 
- Hva er erfaringen deres med de ukrainske flyktningene som allerede er bosatt?

Burde kommunen vært i stand til å bosette flere? Se på kommunens fastlegekapasitet, økonomi etc.  
    
#####  Vil bosette flere flyktninger enn kommunen er anmodet om
   
**Mulig sak**: Kommunen ble anmodet om å bosette x antall flyktninger, men har selv bedt om å ta imot y.
    
**Høre med kommunedirektøren:**

- Horfor ønsker kommunen å ta imot flere flyktninger enn de har blitt anmodet om?  
    
- Kommer flyktningene raskt ut i jobb eller utdanning i kommunen? Hvor mange er i jobb?
- Hvorfor vurderer dere kapasiteten deres til å være bedre enn hva Imdi legger til grunn?
- Er penger et insentiv for å ta imot flere?  
       

#### Hvor mange flyktninger har kommunen bosatt sammenlignet med nabokommunene?
    
**Mulig sak**: Kommunen tar imot mange flyktninger i forhold til befolkningstallet.  Kommunen er på x. plass i fylket.  
    
Sammenlign din kommune med sammenlignbare kommuner (folketall, økonomi og sentralitet). Velg relevante grupperinger i venstre marg på nettsiden.  
       
    
#### De over 55 har ikke rett på introduksjonsprogram

Ukrainske flyktninger over 55 år får ikke tilbud om introduksjonsprogram.
    
**Mulig sak**: Ukrainske flyktninger over 55 år kommer seg ikke ut i jobb.   

**Mulig historie**: En ukrainsk flyktning over 55 år som står uten tilbud om introduksjonstilbud. Hvilke konsekvenser får dette?  
    
**Undersøke**:  
- Hvorfor gir ikke kommunen dem over 55 år tilbud om deltagelse på introduksjonsprogram? 
    
- Hva gjør kommunen for å integrere de eldre ukrainerne i samfunnet?  Hva gjør frivillige organisasjoner?
    
- Hva er den langsiktige planen for denne gruppen?  
    
####  Kommunen gir tilbud til ukrainske flyktninger over 55 år, selv om de ikke må
    
**Mulig sak**: I denne kommunen får ukrainske flyktninger tilbud om introduksjonsprogram, selv om kommunen ikke er pliktig til å gi dem dette.  
    
**Mulig historie**: En ukrainsk flyktning over 55 år som går på introduksjonsprogram, eller har kommet ut i jobb. Eller en lærer på introduksjonsprogram som underviser flyktninger over 55 år.
    
**Undersøke**: 
- Hvorfor har kommunen valgt å gi tilbud til dem over 55 år? 
    
 - Kommer de over 55 år ut i jobb etter endt introduksjonsprogram? 
    
- Hvor mange av de over 55 år benytter seg av introduksjonsprogrammet?  
 
#### Så mange ukrainere har kommet ut i jobb i kommunen
    
**Mulig sak**: x antall i kommunen har fått seg arbeid etter fullført introduksjonsprogram.
    
**Mulig historie**: En ukrainsk flyktning som har kommet ut i arbeid, eller en arbeidsgiver som har ansatt en.
    
**Undersøke:** 
- Hvilke bransjer og bedrifter har ansatt ukrainske flyktninger? 
- Hvor mange har fullført introduksjonsprogrammet, men ikke kommet i jobb? Hva er grunnen til det?    
- Hvilken tilrettelegging kreves ved ansettelse, og hvilken kunnskap tilfører de eventuelt bedriften?  
      

#### Hvor blir det av pengene?
    
**Mulig sak**: Kommunen har totalt mottatt xxx millioner kroner i 2022 og 2023. Hva har de brukt tilskuddspengene på?
    
**Mulig historie**: En ukrainsk flyktning som ikke har fått tjenestene hen har rett på.  
    
    
Tilskuddspengene er ikke øremerket og ikke rapporteringspliktig. 

**Undersøke:**
    
- Sitter kommunen igjen med økonomisk overskudd, og hva gjør de eventuelt med pengene? 
    
- Se pengebruken opp mot hvilke tjenester flyktningene faktisk har fått i kommunen. Er flyktningene misfornøyd med tjenestene? Har Statsforvalteren avdekket avvik?  
       
    
    """)

# Tab 3: Suggestions for how the local journalists can proceed
with tab3:
    st.markdown("""
    Flyktninger fra Ukraina er betydelig flere og er eldre enn flyktninger Norge har bosatt tidligere. Forskning viser at de er sykere enn nordmenn. 
    Forventningen var at de skulle gli inn i samfunnet. De skulle være som arbeidsinnvandrere, som kom raskt ut i jobb. Men erfaringene viser at det har vært flere utfordringer.
    
    Noen kommuner mener de håndterer flyktningstrømmen godt, andre opplever situasjonen som utfordrende.
    
    ##### Det ukrainske miljøet
    * Den ukrainske forening i Norge har Facebook-grupper knyttet til forskjellige kommuner. 
    * Hør med ditt eget nettverk. Er det noen som kjenner ukrainere?
    * Kontakt frivillige organisasjoner (Røde kors, SEIF), kirken, flyktningkontoret.
    * Du kan bruke tolk via telefon (se Nasjonalt tolkeregister). I noen tilfeller kan flyktningkontoret bistå.
    
    ##### Politikere/kommuneadministrasjon
    * Hvorfor tar kommunen imot færre/flere enn Imdi har anmodet? (sjekk tall for din kommune i talloversikten).
    * Hvor mange enkeltpersoner har kommunen ikke villet bosette?
    * Har kommunen vært nødt til å ansette flere (lærere, sykepleiere, saksbehandlere) for å opprettholde et godt tjenestetilbud? Er det utfordrende å ansette folk i faste stillinger siden det er uvisst hvor lenge ukrainere blir i Norge?
    * Be kommunen om en oversikt om hvordan tilskuddene fra Imdi er brukt.
    
    ##### Flyktningtjenesten i kommunen
    * Hva er kommunens erfaring med å ta imot ukrainske flyktninger?
        * Er det forskjell på ukrainere som ankom rett etter krigen brøt ut, sammenlignet med de som kommer nå?
        * Er det økt press på noen av tjenestene i kommunen som følge av pågangen av ukrainske flyktninger? Hvordan løser dere dette? 
        * Hvor høy andel av ukrainere har kommet ut i jobb eller utdanning? Hvordan er andelen sammenlignet med øvrige flyktninger?
    * Kan kommunen si noe om sykdomsbildet blant ukrainere?
        * Hvor mange er på sykehjem eller mottar hjemmesykepleie?
        * Hvor mange får oppfølging innen spesialisthelsetjenesten?
        * Hvordan skiller dette seg fra erfaringene dere har fra øvrige flyktninger?
        * Hvilken oppfølging får de som har tjenestegjort i krigen?
    * Hvilket tilbud gir kommunen de over 55 år?
    * Hva betyr andelen barn og unge for barnehagene og skolene? Har kommunen ansatt flere lærere? Hvordan blir tolkebehovet dekket?
    
    ##### Kommuneoverlege
    * Si noe om sykdomsbildet blant ukrainere i din kommune:
        * Hvor mange er på sykehjem eller mottar hjemmesykepleie?
        * Hvor mange får oppfølging innen spesialisthelsetjenesten?
        * Hvordan skiller dette seg fra erfaringene dere har fra øvrige flyktninger?
        * Hvilken oppfølging får de som har tjenestegjort i krigen?
    * Hvordan er fastlegesituasjonen i kommunen, og hvordan påvirkes den av ukrainske flyktninger? Hvilke tiltak har dere satt inn?
    * En rapport fra OsloMet viser at ukrainere har en lavere terskel for å oppsøke fastlege, enn nordmenn. Er dette noe dere opplever? 
    * Hvilke konsekvenser vil pågangen av ukrainske flyktninger få for helsetjenestene fremover? 
    
    ##### Hvis din kommune har asylmottak
    * Hvordan har antallet ukrainere påvirket deres arbeid?
    * Hvilke utfordringer møter dere?
    * Opplever øvrige asylsøkere lenger ventetid på mottak på grunn av ukrainere?
    
    ##### Tips til historier
    * Finner dere løsningsorienterte historier som viser hvordan kommunen har løst sine utfordringer? Jobber det ukrainere på sykehjem, på den lokale matbutikken, i barnehager/skoler? Er det noen ukrainere som selv hjelper til med å få hjulene til å gå rundt i kommunen? 
    * Har det kommet noen som har tjenestegjort i krigen? Hvilken historie har de å fortelle? Hvem er hen? Hvordan ble hen rekruttert? Hvorfor endte hen opp i din kommune?
    * Er det noen eldre som bor på sykehjem, sammen med nordmenn med erfaring fra andre verdenskrig?
    * Snakk med sykepleiere som kjenner på det økte presset i kommunen. 
    * Eller en rektor/lærer som har fått en ukrainsk elev i klasserommet. 
    * Lærer på introduksjonsprogram.
    * Oppsøk et asylmottak hvis det finnes i din kommune. 

    """)

    st.markdown(
        """
        #### Slik gjorde vi det i Sortland
        
        Epost til Nav i Sortland kommune fra Samarbeidsdesken 23.02.2024
        
        <div style='border:1px solid;margin:10px;padding:20px;'>
        
        Hei, 
        
        Takk for hyggelig samtale i går.
        
        Vi jobber som sagt med et prosjekt om ukrainske flyktninger. Vi ser at de er eldre og sykere enn de flyktningene Norge har tatt imot 
        tidligere. Vi lurer på hvilke konsekvenser dette får for den enkelte kommune, og da særlig mtp trykket på helsesektoren. 
        
        Vi lurer derfor på: 
        1. Kan dere si noe om sykdomsbildet til ukrainerne som kommer til kommunene deres?  
        2. Hvordan skiller dette seg fra erfaringen dere har fra tidligere flyktninger? 
        3. Hvordan opplever dere situasjonen i helsesektoren? Er det økt trykk? Hvilke utfordringer har dere? Har dere nok bemanning til å takle 
            situasjonen? 
        4. Hvor mange ukrainere bor på sykehjem? Hvor mange mottar hjemmesykepleie? Hvor mange mottar behandling - både psykisk og somatisk? 
        5. Er det andre sektorer som påvirkes av at flyktningene er eldre og sykere? 
        6. Hvordan ser dere for dere situasjonen fremover - kan dere ta imot flere syke og eldre? 
        
        Er det andre utfordringer dere tenker vi burde se på i forbindelse med flyktningstrømmen fra Ukraina?   
        </div>
        Svar fra Sortland kommune 07.03.2024
        
        <div style='border:1px solid;margin:10px;padding:20px;'>

        <p>Her er svar på spørsmålene du sendte- de er svart ut fra helsestasjonen og legetjenestene og representerer situasjonen i kommunen knyttet til de 
        punktene du ønsket besvart.</p>
        
        Sortland kommunes erfaringer med flyktninger fra Ukraina

        ##### 1. Kan dere si noe om sykdomsbildet til ukrainerne som kommer til kommunene deres?

        Svar: 
        <p style='background-color:yellow'>Sykdomsbildet blant ukrainske flyktninger i Sortland kommune viser et høyt antall barn og unge med dårlig tannhelse. Kommunen har også bosatt 
        flere familier med barn som har autisme.</p>
        
        <p>Observert sykdomsbilde i kommunen knyttet mot denne gruppen samsvarer med nasjonale rapporter peker også på <span style='background-color:yellow;'>utfordringer knyttet til hiv, syfilis, 
        hepatitt B og C blant ukrainske flyktninger.</span></p>

        <p>Ukrainske flyktninger: Dårligere helse og betydelig dårligere tannhelse - FHI
        https://www.imdi.no/contentassets/91a28cb4be194aeda357a1e64d5132c0/isf_rapport_3_24_uuweb.pdf</p>
        
        <p style='background-color:yellow'>Det er erfart kulturelle og sosiale forskjeller knyttet til medisinbruk og behandling gjennom spesialisthelsetjenester i Ukraina i forhold til Norge.</p>
        
        <p>I Ukraina er det kortere ventetid på behandling til ulike spesialisttjenester, samtidig som det er forskjeller på utdanning til spesialisttjenester i Norge i forhold til Ukraina. Det er derfor fokus på god veiledning på norsk helsesystem og at det er kvalitetsmessig trygt å forholde seg til helsetjenestene når de ankommer kommunen.</p>
        
        <p>Vi ser også at ukrainske barn ofte har fulgt vaksinasjonsprogrammet mens det er lavere trend blant foresatte å ta vaksiner, for eksempel covid vaksiner.</p>

        ##### 2. Hvordan skiller dette seg fra erfaringen dere har fra tidligere flyktninger?

        <p>Svar:</br>
        Sammenlignet med tidligere flyktninger, har ukrainske flyktninger generelt bedre fysisk og psykisk helse. De har generelt mindre oppfølgingsbehov enn 
        kvoteflyktninger, og har høyere helsemessig tilstand ved ankomst sammenlignet med kvoteflyktninger som har bodd lenge i leir.</p>
        
        ##### 3. Hvordan opplever dere situasjonen i helsesektoren? Er det økt trykk? Hvilke utfordringer har dere? Har dere nok bemanning til å takle situasjonen?

        <p>Svar:</br>
        Vi opplever et økt trykk i helsesektoren, spesielt med hensyn til helsekartleggingssamtaler i regi av helsestasjonen og oppfølging i skolehelsetjenesten.
        Mangelen på personell har også ført til utfordringer med å gjennomføre nødvendige blodprøver i henhold til veilederen. For å møte utfordringene 
        etableres det blant annet i år et ekstra legekontor i kommunen.</br>
        
        ##### 4. Hvor mange ukrainere bor på sykehjem? Hvor mange mottar hjemmesykepleie? Hvor mange mottar behandling - både psykisk og somatisk?

        <p>Svar:</br>
        Per nå er det ingen økning i behov for sykehjemsplasser eller hjemmesykepleietjenester siden 2022, da det ikke har vært en betydelig tilstrømning 
        av eldre fra Imdi.</p>
        
        ##### 5. Er det andre sektorer som påvirkes av at flyktningene er eldre og sykere?

        <p>Svar:</br>
        I forhold til eldre er det ingen erfart belastning mot denne gruppen enn øvrige befolkning.</p>

        <p><span style='background-color:yellow;'>Politiet som har økt fokus på forebygging av ungdomskriminalitet og rusmisbruk blant unge i kommunen, hvor også ukrainske ungdommer er vektlagt.</span> Det har 
        blitt gitt tilbakemelding på at det er tendens til økning av ungdomskriminalitet i kommunen de siste årene.  Det er også økt fokus på forebygging 
        nasjonalt for barn og unge nasjonalt som også øker bevisstheten til dette arbeidet. <span style='background-color:yellow;'>I forhold til rusmisbruk er det også flere foresatte fra Ukraina som 
        har en lavere terskel for rusmisbruk enn hva som er erfart av andre bosatte flyktninger.</span></p>
        
        ##### 6. Hvordan ser dere for dere situasjonen fremover - kan dere ta imot flere syke og eldre?

        <p>Svar: </br>
        Sortland kommune vurderer kapasiteten kontinuerlig for å kunne imøtekomme behovene til bosatte med ulike behov, uavhengig av alder eller opprinnelsesland.</p>
        
        ##### 7. Er det andre utfordringer dere tenker vi burde se på i forbindelse med flyktningstrømmen fra Ukraina?
        
        <p>Svar: </br>
        Det gis tilbakemelding på fra helsesektoren at det bør være økt fokus på forebyggede arbeid knyttet til hjerte/kar sykdommer, røykavvenning, tannhelse, 
        alkohol- og medisinbruk for bosatte flyktninger fra Ukraina. <span style='background-color:yellow;'>Det dras paralleller mot de statlige og kommunale forebyggingsarbeidet som ble utført på 
        80 og 90 tallet i Norge hvor vi per i dag kan vise til signifikant bedre helse på disse områdene og høyere gjennomsnittlig levealder i Norge sammenlignet 
        med Ukraina, hvor gjennomsnittlig levealder på menn før krigen var 67 år.</span></sp>
        
        <p>Det er også behov for mer fokus på traumekartlegging og oppfølging herunder de siste år for denne gruppen, ettersom vi nå <span style='background-color:yellow;'>bosetter flere menn som har hatt 
        tjenestetid i krigsbelastede soner</p> i Ukraina fra krigens oppstart i 2022.</p>
        
        <p>Vi ønsker avslutningsvis gjerne en oppfølging fra dere,  hvor dere ser på hvordan Sortland kommune har tilpasset tjenestetilbudet for å håndtere en 
        <span style='background-color:yellow;'>befolkningsvekst på 6 % over tre år</span>, med over 200 bosatte flyktninger årlig. <span style='background-color:yellow;'>Sortland kommune har vært en foregangskommune</span> ved å håndtere økt bosetting 
        på en innovativ og kvalitetsmessig god måte, med fokus på individuell oppfølging og samarbeid med næringslivet for arbeidsformidling til bosatte flyktninger. </p>
        
        <p>Kontakt oss gjerne for ytterligere informasjon eller oppfølging.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# Tab 4: Source data for the municipality
with tab4:

    tablecol1, tablecol2 = st.columns([4, 5])
    tablecol3, tablecol4 = st.columns([4, 5])
    tablecol5, tablecol6 = st.columns([4, 5])
    tablecol7, tablecol8 = st.columns([4, 5])

    pop_text = """
            ##### Befolkningen i  {kommune}
            """.format(
        kommune=kommuner.get(select_kommune),
        year=select_year,
        sum_year=flyktninger_komm_year['pop'].sum(),
        sum_total=flyktninger_komm['pop'].sum()
    )

    with st.container():
        with tablecol1:
            st.markdown(pop_text)

        with tablecol2:
            st.dataframe(
                flyktninger_komm_year[['År', 'Kjønn',
                                       'Aldersgruppe', 'pop', 'pop_pct']],
                use_container_width=use_container_width,
                hide_index=True,
                column_config={
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
            """.format(
        kommune=kommuner.get(select_kommune),
        year=select_year,
        sum_year=flyktninger_komm_year['ukrainere'].sum(),
        sum_total=flyktninger_komm['ukrainere'].sum(),
        prikking=check_ano(flyktninger_komm_year['ukrainere_string'].astype(str))
    )
   
    with st.container():
        with tablecol3:
            st.markdown(ukr_text)

        with tablecol4:
            st.dataframe(
                flyktninger_komm_year[[
                    'År', 'Kjønn', 'Aldersgruppe', 'ukrainere_string', 'ukr_pct']],
                use_container_width=use_container_width,
                hide_index=True,
                column_config={
                    'År': st.column_config.NumberColumn(format="%.0f"),
                    'ukrainere_string': st.column_config.TextColumn(
                        'Antall'
                    ),
                    'ukr_pct': st.column_config.NumberColumn(
                        'Andel', format='%.1f %%'
                    )  # ,
                    # 'ukr_prikket': st.column_config.TextColumn(
                    #    'Prikket',
                    #    help = 'Prikkede data betyr at kommunen har tatt i mot mindre enn fem EMA. Data tilbakeholdes av IMDi av personvernhensyn.'
                    #   )
                }
            )

    ema_text = """
            ##### Bosatte enslige mindreårige fra Ukraina
            """.format(
        kommune=kommuner.get(select_kommune),
        year=select_year,
        sum_year=ema_komm_year['ema'].sum(),
        sum_total=ema_komm['ema'].sum()
    )

    with st.container():
        with tablecol5:
            st.markdown(ema_text)

        with tablecol6:
            st.dataframe(
                ema_komm_year[['År', 'ema_string']],
                use_container_width=use_container_width,
                hide_index=True,
                column_config={
                    'År': st.column_config.NumberColumn(format="%.0f"),
                    'ema_string': st.column_config.TextColumn(
                        'Enslige mindreårige',
                    )}
            )

    ovr_text = """
            ##### Øvrige flyktninger (ikke kollektiv beskyttelse)
            """.format(
        kommune=kommuner.get(select_kommune),
        year=select_year,
        sum_year=flyktninger_komm_year['ovrige'].sum(),
        sum_total=flyktninger_komm['ovrige'].sum()
    )

    with st.container():
        with tablecol7:

            st.markdown(ovr_text)

        with tablecol8:
            st.dataframe(
                flyktninger_komm_year[[
                    'År', 'Kjønn', 'Aldersgruppe', 'ovrige_string', 'ovr_pct']],
                use_container_width=use_container_width,
                hide_index=True,
                column_config={
                    'År': st.column_config.NumberColumn(format="%.0f"),
                    'ovrige_string': st.column_config.TextColumn(
                        'Antall'
                    ),
                    'ovr_pct': st.column_config.NumberColumn(
                        'Andel', format='%.1f %%'
                    )}
            )

    anon_numbers_source = """
                
    ###### Anonymisering 
    Hvis det står *<5* i en eller flere tabeller, betyr det at antallet er mellom èn og fem. Imdi tilbakeholder eksakt antall for å unngå identifisering.            
    
    ##### Tallkilder
    Befolkningstall er hentet fra[ SSB-tabell 07459](https://www.ssb.no/statbank/table/07459). Tall hentet 22.02.2024.
    
    Fakta om venteliste hos fastlege og reservekapasitet er hentet fra [SSB-tabell 12005](https://www.ssb.no/statbank/table/12005). Tall hentet 18.03.2024.
    
    Tall som beskriver antall ukrainere og antall øvrige flyktninger er sammenstilt av fra Integrerings- og mangfolksdirektaret. Tall mottatt {data_imdi_received_date}.
    
    Tall som beskriver enslige mindreårige er sammenstilt av Integrerings- og mangfolksdirektaret. Tall mottatt 09.02.2024.
    
    Anmodningstall er hentet fra [Imdis nettsider](https://www.imdi.no/planlegging-og-bosetting/bosettingstall/). Tall hentet 08.03.2024 kl. 12:20.
    
    Tilskuddstall er hentet fra [Imdis nettsider](https://www.imdi.no/om-integrering-i-norge/statistikk/F00/tilskudd). Tall hentet 11.03.2024.
    
    Bosettingstall fra 2015-2016 er hentet fra Imdis årsrapporter fra hhv. [2015](https://www.imdi.no/globalassets/dokumenter/arsrapporter-og-styrende-dokumenter/arsrapport-2015/imdis-arsrapport-2015.pdf) (side 4) og [2016](https://www.regjeringen.no/contentassets/59f5becfc2384dacb88e9ef4fcccba33/arsrapport-2016-imdi.pdf) (side 2).
    
    Tall på antall flyktninger fra Balkan på 1990-tallet er hentet fra [Store norske leksikon](https://snl.no/kollektiv_beskyttelse).
    """.format(
        data_imdi_received_date=data_imdi_received_date
    )

    st.markdown(anon_numbers_source)

# Tab 5: Expert interviews
with tab5:

    st.markdown(
        """
        Rapporter: 
        - Angela Labberton  mfl. (FHI) - [Helsetjenestebehov blant flyktninger fra Ukraina som kom til Norge i 2022](https://www.fhi.no/nyheter/2023/ukrainske-flyktninger-darligere-helse-og-betydelig-darligere-tannhelse/).  
        - Intervju med forsker ved OsloMet, Vilde Hernes, som kommenterer på funn i [ny rapport](https://oda.oslomet.no/oda-xmlui/handle/11250/3172723). Rapporten er skrevet på oppdrag fra Imdi. 
        - Institutt for samfunnsforskning - [Tilrettelegging for integrering av flyktninger i Norge](https://samfunnsforskning.brage.unit.no/samfunnsforskning-xmlui/bitstream/handle/11250/3116715/ISF_Rapport_3_24_UUweb.pdf).  
        
        Samarbeidsdesken har gjennomført intervjuer og sitatsjekk med ekspertkilder. Sitatene kan brukes fritt. 
        """
    )
    fhi_string = """
    
    Angela Labberton med flere har undersøkt selv-rapportert helse og helsetjenestebehov blant voksne ukrainere fra Ukraina. 
    
    Det er viktig at nyansene og forbehold kommer frem og at ikke svarene klippes ut på en måte som gjør at meningen blir endret. Også skillet mellom det som er funnet i undersøkelsen versus andre vurderinger.
    
    Du finne rapporten i punktlisten øverst på siden. 
    
    ##### Hva viser deres studie om helsesituasjonen til de ukrainske flyktningene? 
    — <span style='background-color:yellow;'>Seks av ti rapporterte at de hadde langvarig sykdommer eller plager. Omtrent en tredjedel rapporterte symptomer den siste uken som indikerer psykiske plager.</span>  
    
    — Folkehelseinstituttet gjennomførte en spørreundersøkelse blant voksne flyktninger fra Ukraina som kom til Norge i 2022 der deltakerne vurderte sin egen helse. Det kom 731 svar, hvorav flesteparten var kvinner. Omtrent halvparten vurderte sin helse alt i alt som god eller svært god mens seks av ti rapporterte at de hadde langvarig sykdommer eller plager. Omtrent en tredjedel rapporterte symptomer den siste uken som indikerer psykiske plager. Funnene viser den selvurderte helsen til dem som har valgt å svare på undersøkelsen, og må tolkes noe forsiktig.
    
    ##### Hva viser deres studie om helsesituasjonen til ukrainske flyktninger sammenlignet med den norske befolkningen?
    — <span style='background-color:yellow;'>Det overordnete bildet viser at flyktningene rapporterte dårligere helse og betydelig dårligere tannhelse sammenlignet med den øvrige befolkningen.</span> 


    Svarene fra undersøkelsen ble sammenlignet med svar fra fem befolkningsundersøkelser i Norge. Sammenligningen viser at flyktningene vurderte sin generelle helse og tannhelse som dårligere, og at en høyere andel rapportere om psykiske plager og langvarig sykdommer eller plager, enn blant den norske befolkningen.
    
    ##### Hvordan er tannhelsen? 
    — <span style='background-color:yellow;'>Tannhelsetjenester kan være et stort helsebehov blant flyktningene.</span>

    Undersøkelsen viser at flere enn åtte av ti av flyktningene, like mange som blant den norske befolkningen, oppga at de hadde vært til tannlege i løpet av de siste to årene. 
    Likevel oppga under en tredjedel at de vurderte sin tannhelse som god eller veldig god, sammenlignet med tre fjerdedeler av den norske befolkningen. 

    
    ##### Hvorfor er helsen til ukrainere dårligere enn helsen til den norske befolkningen?
    — Undersøkelsen kan ikke si noe om årsaken til dårligere helse, men det kan være flere årsaker til at helsen til flyktningene kan være dårligere enn den norske befolkningen, og bildet er sammensatt. Fra før vet vi at flyktninger er en gruppe med dårligere helse sammenlignet med personer som har innvandret av andre grunner. Situasjonen i hjemlandet, samt hendelser før og under migrasjonen, kan påvirke en persons helse, i tillegg til levekår, livstils- og miljøfaktorer, og bruk av helsetjenester.
    I Europa sammenheng skårer Ukraina dårligere på flere helseindikatorer, også før fullskala invasjonen. Det er rapportert om regionale forskjeller i tilgang og kvaliteten på helsetjenester i Ukraina og pågående reformer har mål om å forbedre helsetjenesten. <span style='background-color:yellow;'>Fullskala invasjonen i Ukraina har i tillegg ført til redusert tilgang til helsehjelp og medisiner som kan ha resultert i behandlingsavbrudd.</span>
    Til slutt har geografiske og juridiske faktorer noe å si om helsen til de som ankommer. <span style='background-color:yellow;'>De som flykter ofte er friskere og yngre enn den øvrige befolkningen i opprinnelseslandet. Imidlertid kan den korte reiseveien fra Ukraina og færre juridiske hindringer bidra til at flere ukrainske flyktninger med dårligere helse ankommer, sammenlignet med flyktninger fra andre land.</span>
    
    ##### Hvilke utfordringer byr dette på?
    — Vi har ikke undersøkt dette spesifikt. Det har kommet særlig mange kvinner og barn fra Ukraina og de kan ha ulike behov enn andre flyktninggrupper Norge tidligere har erfaring med å motta. Så det har nok vært en bratt læringskurve bare på grunn av den annerledes demografien. <span style='background-color:yellow;'>Undersøkelsen vår, samt erfaringer fra mottaksapparat og kommunen, viser at en andel av flyktningene har behov for oppfølging av ulike typer helseplager, inkludert langvarige sykdommer, tannhelse og psykiske plager. Så det kan være behov for ulike type helsetjenester. I tillegg er det et stort behov for oversettelser og tolk fordi kun en mindre del av ukrainere kan engelsk (eller norsk) ved ankomst.</p>
    
    ##### Hvilke sykdommer/plager er de mest utbredte hos ukrainerne? 
    — Når det gjelder spesifikke sykdommer eller tilstander, har vi kun undersøkt noen utvalgte tilstander som også ble spurt om i tidligere befolkningsundersøkelser i Norge. Blant disse var de meste hyppigste rapporterte tilstander rygglidelser, depresjon, høyt blodtrykk og allergi. Mellom 18-23% av respondenter - cirka en av fem - rapporterte å ha vært plaget av en eller flere av disse tilstandene i løpte av det siste året. Sammenlignet med de norske svarerne rapporterte en større andel av flyktningene om høyt blodtrykk og hjertekramper, og kronisk bronkitt, kols eller emfysem. På den andre siden rapporterte en lavere andel av flyktningene astma, allergi og artrose/slitasjegikt enn den norske befolkningen.
    
    ##### Hva betyr dette for kommunehelsetjenesten? Hva betyr dette for spesialisthelsetjenesten? 
    — Kommunehelsetjenesten og fastlegen har en nøkkelrolle i helsetjenesten i Norge og håndterer den største andelen av helsehjelpen som gis. <span style='background-color:yellow;'>En grov modellering gjort av FHI tidlig i 2022 viser at det vil være en større økning i allmennlegebruk enn liggedøgn på sykehus. Samtidig vil noen av flyktningene har behov for vurdering, behandling og/eller oppfølging i spesialisthelsetjenesten. Som nevnte over vil det også være økt behov for bruk av tolk.</span>
    
    ##### Er norske kommuner rigget for dette? 
    — Det er andre etater i helseforvaltningen som har bedre oversikt på dette enn FHI. Hvordan situasjonen er vil nok variere fra kommune til kommune og kan avhenge av faktorer som hvor robust tjenestetilbudet var fra før, antall nye innbyggere i kommunen og hvor godt tjenestene har lyktes med å bli stryket som følge av økt behov. <span style='background-color:yellow;'>Flere kommuner melder om at deres tjenester er under press.</span>
    
    ##### Finnes det en oversikt over trykket Ukrainske flyktninger legger på helsevesenet?
    — <span style='background-color:yellow;'>Det finnes ingen samlet nasjonal oversikt over faktisk helsetjenestebruk blant ukrainske flyktninger. Folkehelseinstitutt jobber med å skaffe kunnskap om dette ved bruk av registerkoblinger, men dette er arbeid som tar lengre tid.</span>
    
    ##### Andre funn du tenker er viktig å få frem? 
    — Det er veldig viktig å formidle god informasjon om helsetjenesten i Norge på en forståelig måte til de nyankomne flyktningene. Særlig de mest nyankomne flyktningene rapporterte i større grad at de ikke hadde fått forståelig informasjon om helsetjenester, visste hvordan de skulle kontakte helsevesenet, eller hadde fått den helsehjelpen de følte de hadde hatt behov for i Norge. Det norske helsevesenet er organisert noe annerledes enn i mange andre land og dette kan føre til at tilgang, bruk og/eller forventningene blant flyktninger er nokså annerledes.

    """

    with st.expander('Intervju med Angela Labberton ved Folkehelseinstituttet.'):
        _, imgcol = st.columns([5, 1])
        with imgcol:
            with open("img/Angela Labberton kredittering Simen Gald.jpg", "rb") as file:
                btn = st.download_button(
                    label="Last ned pressebilde",
                    data=file,
                    file_name="Angela Labberton kredittering Simen Gald.jpg",
                    mime="image/jpg"
                )

            st.markdown('Foto: Simen Gald')

        st.markdown(fhi_string, unsafe_allow_html=True)

    nibr_string = """
    
         
    **Nedskalering i kommunene**

    – Manglende norskferdigheter er fortsatt den klart største barrieren for å få jobb i Norge. 

    – En bekymring for kommunene nå er hvordan de skal få til en god nedskaleringsprosess, der f.eks. ansatte i flyktningtjenester og norskopplæring må omplasseres eller sies opp.

    

    **Ukrainere i jobb**

    – Én av tre ukrainere oppgir at de er økonomisk selvstendige og klarer seg selv.

    – 30 prosent av ukrainerne oppgir at de er i arbeid, mens 70 prosent mottar en eller annen form for offentlig, økonomisk støtte. 

    – Manglende norskferdigheter er fortsatt den klart største barrieren for å få jobb i Norge. 


    **Jobbmatch og kvalifisering**

    – Majoriteten av ukrainerne har høyere utdanning eller tidligere arbeidserfaring. Cirka halvparten får, ikke eller i liten grad, brukt dette i jobben i Norge.

    – 43% er villig til å ta «hvilken som helst jobb», mens 45% er villig til å ta arbeid som ikke matcher tidligere erfaring eller utdanning, men det avhenger av type arbeid.

    – Mange planlegger videre utdanning eller kompetanseheving i Norge, ofte med mål om å kvalifisere seg til yrker som trengs på det norske arbeidsmarkedet.
                

    **Varierende erfaring med arbeidspraksis**

    Med regjeringens krav om mer arbeidsrettede introduksjonsprogram er arbeidspraksis blitt et mye brukt tiltak.

    – En bekymring blant noen ukrainere er at visse arbeidsgivere utnytter situasjonen med arbeidspraksis for å få gratis arbeidskraft.


    **Midlertidig jobb**

    – Ukrainere opplever at den midlertidige oppholdstillatelsen gjør at arbeidsgivere er mer skeptiske til å ansette dem i faste stillinger. 
    
    – Mange ønsker en fast fulltidsjobb, og sier at midlertidige stillinger gjør den generelle usikkerheten de lever med enda større. 
    
    
    – Usikkerheten rundt om og hvor lenge de vil får bli i Norge gjør det vanskelig å planlegge livet og tenke langsiktig.

    
    **Vil bli i Norge**

    – Bare 10 % av ukrainerne ønsker å dra tilbake. Det er en klar økning i andelen som sier at de ikke ønsker å returnere når krigen er over.
    
    – Flere forsøker nå å finne strategier for å bli i Norge, f.eks. å søke om arbeidstillatelse i stedet for midlertidig beskyttelse hvis de oppfyller betingelsene.

    
    **Derfor vil de ikke tilbake til Ukraina**

    – En åpenbar grunn til at man ikke vil returnere er rett og slett at noen ikke har noe å returnere til.


    – Et ønske om et stabilt og trygt liv for barna trekkes ofte frem av foreldre som bakgrunnen for at de ikke ønsker å returnere etter krigen.


    – En ny tendens er at vi ser en større splittelse blant ukrainerne. Flere som har flyktet fra Ukraina er engstelige for hvordan de vil bli tatt imot av ukrainere som ble igjen hvis de returnerer.

    
    **Flere enslige mindreårige gutter på 16-17 år**

    – Blant de under 18 år, ser vi en dobling av andelen 16-17-åringer fra 2022 til 2024, og det er hovedsakelig en økning i unge gutter.
    
    – Vi antar at disse ungdommene reiser eller blir sendt fra Ukraina mens det fortsatt er lovlig, med tanke på reiseforbudet for ukrainske menn mellom 18-60 år.
    
    – En økning i andelen ungdommer påvirker hvilke tjenester kommunene må ha tilgjengelig, spesielt siden en del av disse kommer som enslige mindreårige.


    **Barn og skolegang**

    – Så og si alle barn fra Ukraina deltar på norske skoler
    
    – Spesielt de yngre barna trives og integreres godt, men at det er mer variasjon og utfordringer for ungdommen.
    
    – Selv om nesten alle går på norsk skole, deltar også 58% på en eller annen form for ukrainsk skolegang eller undervisning i tillegg.
    
    
    – Foreldrenes dilemma er frykten for at barna skal falle mellom to skoleløp hvis de må returnere til Ukraina opp mot belastningen det kan være for barna med doble løp når de samtidig skal følge norsk skole, lære et nytt språk og få nye venner.


    **Sekundærflytting**

    – Når vi spør om de har planer om å flytte til en annen norsk kommune er det store forskjeller mellom de som bor sentralt og ruralt.
    
    – Blant de som er bosatt i rurale strøk svarer én av tre at de har planer om å flytte til en annen kommune.
    
    – De som ønsker å flytte peker ofte på dårlige muligheter på arbeidsmarkedet i kommunen som årsak.
    """

    with st.expander('Intervju med Vilde Hernes, forsker ved NIBR.'):

        _, imgcol = st.columns([5, 1])
        with imgcol:
            with open("img/Vilde Hernes kredittering Sonja Balci.jpg", "rb") as file:
                btn = st.download_button(
                    label="Last ned pressebilde",
                    data=file,
                    file_name="Vilde Hernes kredittering Sonja Balci.jpg",
                    mime="image/jpg"
                )
            st.markdown('Foto: Sonja Balci')

        st.markdown(nibr_string)

    ous_string = """
    Anders Holtan, overlege og leder for koordineringssenter for medisinsk evakuering ved Oslo Universitetssykehus.
          
    — Norge har per 8. mars 2024 evakuert 373 syke og skadde ukrainske pasienter til Norge. Medevac pasienter utgjør en liten andel ift det totale antallet ukrainske flyktninger som har kommet til Norge, men dette er mennesker vi vet er syke og som er mer krevende for helsevesenet enn en gjennomsnittlig asylsøker.    
    
    — Av de 373 ukrainerne som har kommet via medisinsk evakuering har to tredeler kreft og en tredel skader.
    
    ##### Pasientene bosettes i de forskjellige kommunene:     
    — Arbeidsbyrden for helsevesenet, både for kommunehelsetjenesten og spesialisthelsetjenesten, er vesentlig større for medevac pasienter enn for de andre ukrainerne som kommer.  
    
    — Dette er som andre kreftpasienter og skadde som bor i kommunen; de kan være i behov av legetjenester, hjemmesykepleie, fysioterapi, pasientreiser, behov resepter, attester etc.  
    """

    with st.expander('Intervju med Anders Holtan, Oslo universitetssykehus.'):
        _, imgcol = st.columns([5, 1])
        with imgcol:
            with open("img/Anders Holtan.jpg", "rb") as file:
                btn = st.download_button(
                    label="Last ned pressebilde",
                    data=file,
                    file_name="Anders Holtan.jpg",
                    mime="image/jpg"
                )
        st.markdown(ous_string)

    with st.expander('Intervju med Nataliya Yeremeyeva, sosiolog og medlem i ukrainsk forening.'):

        natyer_string = """
        
        ##### Eldre er ensomme: 
        — Eldre flyktninger er en spesielt sårbar gruppe som består av mange med relativt lave norskkunnskaper og et begrenset sosialt nettverk.  
        
        — Det er ikke uvanlig at eldre innvandrere opplever ensomhet i enda større grad enn den øvrige befolkningen i Norge, men eldre fra Ukraina som har kommet til Norge på grunn av krigen befinner seg i en enda vanskeligere situasjon. De fleste måtte forlate hjemmet mot sin vilje.  
        
        — Det å vite at hjemlandet er i krig, og at det kanskje aldri blir mulig for dem å komme tilbake til der de hører til, er vanskelig.  
        
        — Det å starte et nytt liv, og bygge opp et sosiale nettverket er ikke lett når man blir eldre.  
        
        — Det er vanskelig å lære et nytt språk og bli godt integrert i det nye samfunnet for mange eldre innvandrere, men det er enda vanskeligere å håndtere psykiske lidelser forårsaket av ensomhet og ekskludering. Eldre innvandrere kan være en viktig ressurs for det norske samfunnet. For å ivareta deres psykiske helse betyr det også å investere i mangfoldige Norge.

       ##### Aktiviteter for dem over 55 år: 

        — Ukrainske eldre i Norge, som alle andre, trenger å føle seg som en del av felleskapet. De som bor i kommuner som har mulighet til å tilby dem introduksjonsprogrammet er heldige. Da får de sjansen til å være sammen med andre og delta i aktiviteter. 

        — Noen prøver å skape disse mulighetene selv ved å etablere sosiale arenaer der de kan være sammen med andre. De har for eksempel et ukrainsk kor i Oslo organisert av og for de eldre, og en annen gruppe eldre ukrainere deltar daglig i pro-ukrainske demonstrasjoner i Oslo sentrum. 

        ##### Tilbud til de eldre: 
        — Hvis de eldre ikke går på introduksjonsprogram, så lærer de ikke om det norske samfunnet, og hvis de ikke kan språket kan de ikke snakke med naboen eller med folk på butikken. 

        — Det er alltid en fordel hvis kommuner kan tilby et tilpasset introduksjonsprogram til alle uansett alder som kan åpne flere muligheter for sosial deltakelse

        — Introduksjonsprogrammet er en mulighet til å lære om det norske samfunnet og bli integrert i samfunnet.  Der en viktig investering Norge gjør i den framtidige gjenoppbyggingen av Ukraina. Dette er viktig kunnskap som ukrainere kan ta med seg tilbake til hjemlandet når krigen er slutt. 

        — Det er også en måte å forebygge psykisk uhelse og gjøre hverdagen mer meningsfull. 

        — Frivillige organisasjoner bør fått mer tilskudd slik at de kan arrangere sosiale aktiviteter der eldre ukrainere de kan lære seg språket, ha et fellesskap og føle seg som en del av samfunnet. 

        — Det er kjempeviktig at både donorer og frivillige organisasjoner er oppmerksomme på at ensomhet og ekskludering kan være et stort problem for eldre innvandrere, ukrainere er ingen unntak. 

        — Sosiale aktiviteter for folk med dårlige norskkunnskaper og et begrenset sosiale nettverk, er utrolig viktig for både mental og fysisk helse. Aktiviteter som tilbys må selvfølgelig tilpasses målgruppes behov, men må skape en integreringsarena som eldre innvandrere ikke kan organisere selv. 

        — Sosiale aktiviteter kan hjelpe eldre innvandrere å lære norsk, få nye venner og føle seg en del av det norske samfunnet. Det er ikke minst en mulighet til å dele sin kultur med andre.

        ##### Verst for de eldre som ikke har familie: 
        — Noen eldre kommer med familien sin, de blir ikke nødvendigvis integrert i det norske samfunnet, men de har det trolig bedre psykisk enn de som har kommet alene. 

        — Mange ukrainere fortsatt husker tiden da det var ganske vanlig for flere generasjoner å bo under samme tak som resultatet av den sovjetiske boligpolitikken. Selv om situasjonen har begynt å endre seg ila siste 20 år, er mange ukrainske eldre likevel i stor grad involvert i livene til sine barn og barnebarn. Det er ikke uvanlig at de hjelper å lage mat, passe på huset og oppdra barnebarn. 

        — De som kom til Norge med eller til sin familie har i hvert fall en mulighet til å kompensere mangel på det sosiale livet med familieaktiviteter. De som kom alene, har dessverre ikke det, og er i stor grad avhengig av eksterne tilbud.  

        ##### Pensjon og helse: 
        — Før 2018 var pensjonsalderen i Ukraina 55 år for kvinner og 60 år for menn. Pensjonssystemet har endret seg siden da, og nå kan man tidligst pensjonere seg etter fylte 60 år uavhengig kjønn. Så pensjonsalderen i Ukraina er likevel lavere enn i Norge. 

        — Det å forlate arbeidsmarkedet såpass tidlig påvirker luten tvil livstilen.  Ukrainske eldre er mer aktive nå enn i min barndom for cirka 30 år siden, men likevel er det fortsatt mange fordommer og barrierer som forhindrer aktiv aldring. 

        — Helse er selvfølgelig en viktig faktor her. La oss ikke glemme at gjennomsnittlig levealder i Ukraina har lenge vært en av de laveste i Europa, og Russlands fullskala krig har gjort situasjonen betydelig verre. 

        — Allerede før krigen viste forskning at alderdom i Ukraina begynte allerede ved 57 års-alderen, hvis man ser på sykdomsutvikling. 

        """

        _, imgcol = st.columns([5, 1])
        with imgcol:
            with open("img/Nataliya Yeremeyeva.jpg", "rb") as file:
                btn = st.download_button(
                    label="Last ned pressebilde",
                    data=file,
                    file_name="Nataliya Yeremeyeva kredittering privat.jpg",
                    mime="image/jpg"
                )

        st.markdown(natyer_string)
        # st.markdown("Intervjuet publiseres 03.04.24")

with tab7:
    st.markdown(
        """
                
                Kilde: Imdi
                ##### Kommunene kan selv velge hvem og hvor mange flyktninger de vil bosette: 
                
                Hvert år får kommunene en forespørsel fra Imdi om å bosette et antall flyktninger i kommunen. De kan selv velge hvor mange de ønsker å ta imot.  
                
                Majoriteten av ukrainske asylsøkere bor på asylmottak spredt rundt i landet, mens de venter på å bli bosatt i en kommune og få innvilget flyktningstatus. Gjennomsnittlig ventetid for personer som bodde på mottak var per 31.01.24 omtrent 72 dager.
                
                På mottaket blir asylsøkerne kartlagt. Hvilken oppfølging vil de trenge i kommunen? Basert på denne informasjonen kan kommunen velge å si ja eller nei til å bosette personen. 

                ##### Norskopplæring og introduksjonsprogram for ukrainske flyktninger
                Alle mellom 18 og 67 år har rett på norskopplæring i kommunen de bor i. Ukrainske flyktninger mellom 18 og 55 år har i tillegg rett på introduksjonsprogram. Det har ikke de mellom 55 og 67 år, men kommunen kan likevel velge å tilby introduksjonsprogram dersom kommunen har kapasitet til det. 
                
                Introduksjonsprogrammet er et opplæringsprogram over seks måneder (maks ett år) som skal forberede flyktningen til deltakelse i arbeid eller utdanning.
                
                Foreldre med barn under 18 år får også foreldreveiledning. 
                
                ##### Integreringstilskudd ved bosetting av ukrainere
                Kommunene har rett på integreringstilskudd når de bosetter ukrainske flyktninger. I tillegg kommer tilskuddene i årene etter bosettingsåret, i inntil fem år totalt. 
                
                Det skal dekke kommunens utgifter til bosetting og integrering, inkludert introduksjonsprogrammet. 
                
                Jo raskere flyktningene kommer ut i arbeid eller utdanning, jo større andel av tilskuddene går rett til kommunene. 
                
                I bosettingsåret mottar kommunen følgende satser, alt etter hvem de bosetter:
                - Enslig voksen: 241 000 kroner
                - Voksen i familie 187 000 kroner
                - Barn (0-18 år): 194 400
                - Enslige mindreårige: 187 000 kroner
                I tillegg kommer det enkelttilskudd, for:
                - De over 60 år: 180 000 kroner
                - Barn mellom 0-5 år: 27 800 kroner. 
                - Bosetting av personer med nedsatt funksjonsevne eller atferdsvansker:
                    - Engangstilskudd: 196 400 kroner
                    - Årlig tilskudd: inntil 1 608 000 kroner
                    
                Kommunene mottar de samme satsene for ukrainere som for andre flyktninger kommunen bosetter etter avtale med Imdi. 
                    
                ##### Tilskudd for opplæring i norsk og samfunnskunnskap for ukrainske voksne
                Kommunene mottar også persontilskudd på 39 700 kroner for voksne ukrainere (18-67 år) som får opplæring i norsk og samfunnskunnskap.  Hvis det er færre enn 150 personer i denne målgruppen, får kommunen et ekstra tilskudd opp mot 694 600 kroner.  
                
                ##### Økonomisk støtte til ukrainere
                Full deltakelse i introduksjonsprogrammet gir økonomisk støtte på omtrent 237 000 kroner i året. Det må skattes av støtten. Eventuell annen økonomisk støtte eller inntekt fra jobb, kan gjøre at flyktningen får mindre utbetalt.

                Kilde: Imdi
                """
    )

with tab8:

    #sperrefrist2 = """
    #{time}
    #""".format(time=functions.countdown(end_time))
    #st.markdown(sperrefrist2.format('%d'))

    st.markdown("""
                ##### Forslag til kreditering av Samarbeidsdesken
                """)

    st.markdown("""
                Fakta og tallgrunnlag i denne saken er utarbeidet av Samarbeidsdesken, et journalistisk fellesprosjekt mellom Landslaget for lokalaviser (LLA), Senter for undersøkende journalistikk (SUJO) og NRK.
                """)

    with open("img/logo2.zip", "rb") as zip2:
        btnzip2 = st.download_button(
            label="Last ned logo",
            data=zip2,
            file_name="logo2.zip",
            mime="application/zip"
        )

    st.markdown("""
                ##### Ting å være obs på
                Ukraina-nettsiden inneholder research dere alle kan bruke, men som vi ikke ønsker å dele med andre uten redaksjonell bearbeiding. Del derfor ikke lenken til nettsiden, verken i sakene dere skriver eller i kildehenvisningen i Datawrapper.
                
                
                """)
