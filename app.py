import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from datetime import date
import time
import functions
apptitle = 'Ukrainske flyktninger i norske kommuner'


st.set_page_config(
    #page_title='',
    layout='wide'
    )


end_time = date(2024, 4, 22)


with st.sidebar:
    
    st.title(apptitle) 
    
    sperrefrist = """
    {time}
    """.format(time = functions.countdown(end_time))
    st.markdown(sperrefrist.format('%d'))
    
    st.markdown(
        """
        <p style='color:red;font-weight:bold;'>Ikke publiser saker basert på denne researchen før sperrefristen. </p>
        <p style='color:red;font-weight:bold;'>Siden er under utvikling. Bruk den for å undersøke egen kommune, og for å bli kjent med tallgrunnlaget. Feil kan forekomme.</p>
        """,
        unsafe_allow_html=True
    )

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
    return  pd.read_excel('data/'+ file +'.xlsx', dtype={'Kommunenummer':object, 'Fylkenummer': object})

def format_selection(_dict, option):
    return _dict[option]

def check_ano(vec):
        x = vec.str.contains('<5').sum()
        if x > 0:
            return 'Merk at det er {count} celler som er anonymisert (mindre enn fem flyktninger.)'.format(count= x)
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

#folketall = load_data('app_flyktninger_folketall')

# ------------------------------------------------------------------- # 
# Create a dictionary describing the coverage area of each news paper #
# ------------------------------------------------------------------- #

lla = load_data('lla')
coverage = {g: d['kommnr'].values for g, d in lla.groupby('avis')}

# ----------------------------- #
# Municipality selectors #
# ----------------------------- #

# Create a dictionary of unique municipalities, counties, electional districts
kommuner = pd.Series(oppsummert.Kommune.values,index=oppsummert.Kommunenummer).to_dict()
fylker = pd.Series(oppsummert.Fylke.values,index=oppsummert.Fylkenummer).to_dict()
valgdistrikt = pd.Series(oppsummert.Valgdistrikt.values, index = oppsummert.Valgdistriktnummer).to_dict()
kommuner_valgdistrikt = pd.Series(oppsummert.Valgdistrikt.values, index = oppsummert.Kommunenummer).to_dict()
kommuner_sentralitet = pd.Series(oppsummert.sentralitet.values, index = oppsummert.Kommunenummer).to_dict()
kommuner_kostra = pd.Series(oppsummert.kostranavn.values, index = oppsummert.Kommunenummer).to_dict()



# Use tuples to alphabetically sort the municipalities and counties 
kommuner_sorted = sorted(kommuner.items(), key=lambda kv: (kv[1], kv[0]))
fylker_sorted = sorted(fylker.items(), key=lambda kv: (kv[1], kv[0]))
valgdistrikt_sorted = sorted(valgdistrikt.items(), key=lambda kv: (kv[1], kv[0]))


select_fylke = st.sidebar.selectbox(
    'Velg fylke',
    # using lambda in order to get the first element (municipality code) in tuple
    options = map(lambda x: x[0], fylker_sorted), 
    # display the names of the counties, not the codes
    format_func = lambda x: fylker.get(x)
)

select_kommune = st.sidebar.selectbox(
    'Velg kommune (2024)',
    # get the municipalities for the selected county
    options = [j for i in kommuner_sorted for j in i if j[:2] == select_fylke],
    # display the names of the municipalities, not the codes
    format_func = lambda x: kommuner.get(x)
)

if select_kommune == '1508' or select_kommune == '1580':
        st.sidebar.markdown("""
        Merk: Ålesund ble delt i Ålesund og Haram kommuner 01.01.2024. Tallene for 2022 og 2023 er forbundet med 1507-Ålesund.
        """)

select_year = st.sidebar.selectbox(
    'Velg år',
    options = [2022, 2023, 2024]
)

# ------------------------------------------- #
# Filter data and create different dataframes #
# ------------------------------------------- # 

# dataframe with one line per year, per municipality. 
oppsummert_komm = oppsummert[oppsummert['Kommunenummer'].isin([select_kommune])]
oppsummert_komm_year = oppsummert_komm[oppsummert_komm['År'] == select_year] 
oppsummert_komm_2024 = oppsummert_komm[oppsummert_komm['År'] == 2024] 

#oppsummert_year = oppsummert[oppsummert['Kommune'] == 'Aremark'] 
#print(oppsummert_year['ukrainere'])

# Dataframe with 4 lines (gender x age) per year, per municipality
flyktninger_fylke = flyktninger[flyktninger['Fylkenummer'].isin([select_fylke])] 
flyktninger_komm = flyktninger[flyktninger['Kommunenummer'].isin([select_kommune])] 
flyktninger_komm_year = flyktninger_komm[flyktninger_komm['År'] == select_year] 
flyktninger_cols = ['Kommune', 'År', 'Kjønn', 'Aldersgruppe', 'ukrainere', 'ukr_pct', 'ukr_prikket', 'ovrige', 'ovr_pct', 'ovr_prikket', 'pop', 'pop_pct']

# Dataframe with enslige mindreårige. Both ukrainians and other refugees. 
ema_komm = ema[ema['Kommunenummer'].isin([select_kommune])]
ema_komm_year = ema_komm[ema_komm['År'] == select_year] 

# Dataframe with anmodningstall for the selcted kommune.
# Note: Only available for 2024
anmodninger = oppsummert[oppsummert['Kommunenummer'].isin([select_kommune])]
anmodninger = anmodninger[anmodninger['År'] == 2024] 
anmodninger = anmodninger[['Kommune', 'Kommunenummer', 'ema_anmodet_2024', 'ema_vedtak_2024', 'ema_vedtak_2024_string', 'innvandr_anmodet', 'innvandr_vedtak', 'innvandr_vedtak_string', 'innvandr_bosatt', 'ukr_bosatt',  'innvandr_avtalt_bosatt', 'ukr_avtalt_bosatt']]

# dataframe with asylmottak in selected kommune
ukr_mottak_komm = ukr_mottak[ukr_mottak['Kommunenummer'].isin([select_kommune])]
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
tilskudd_komm_year = tilskudd_komm_year[['Tilskuddstype', 'Antall', 'Kommentar']]
tilskudd_string = 'I ' + str(select_year) +' mottok kommunen følgende tilskudd fra IMDi: \n'

tilskudd_komm_total = tilskudd_komm[tilskudd_komm['Tilskuddstype'] == 'Totalt']
tilskudd_komm_total = tilskudd_komm_total['Antall'].sum()


# ------------------------------------------------------ #
# In the sidebar, make a top list for the selected group #
# ------------------------------------------------------ #
with st.sidebar:
    
    toplist = """
    ### Lag toppliste for {year}
    """.format(year = select_year)
    st.markdown(toplist)

    select_group = st.selectbox(
        'Velg gruppering',
        options=[fylker.get(select_fylke), kommuner_valgdistrikt[select_kommune], 'SSBs sentralitetsindeks', 'KOSTRA-gruppe', 'Hele landet', 'Lokalavis (dekningsområde)', 'ROBEK']
    )

    if select_group == 'Lokalavis (dekningsområde)':
        select_paper = st.selectbox(
            'Velg lokalavis',
            options = coverage.keys()
        )
    
    #if select_group == 'SSBs sentralitetsindeks':
    #    select_centrality = st.selectbox(
    ##        'Velg indeks',
     #       options=['1 - Mest sentrale', '2', '3', '4', '5', '6 - Minst sentrale']
     #   )
        
    # If the user wants a top list for the whole country
    if select_group == 'Hele landet':
        oppsummert_sidebar = oppsummert[oppsummert['År'] == select_year]
        oppsummert_sidebar = oppsummert_sidebar.sort_values('ukr_pct_pop', ascending = False)
        oppsummert_sidebar = oppsummert_sidebar[['Kommune', 'ukrainere', 'ukr_pct_pop']]

        st.dataframe(
            oppsummert_sidebar,
            hide_index = True,
            use_container_width = True,
            column_config = {
                'ukrainere': st.column_config.NumberColumn(
                    'Antall ukrainere', format='%.0f'
                ),
                'ukr_pct_pop': st.column_config.NumberColumn(
                    'Andel av befolkning', format='%.2f %%'
                )}
            )
    
    # If the user wants a top list by county
    if select_group == kommuner_valgdistrikt[select_kommune]:
        oppsummert_sidebar = oppsummert[oppsummert['År'] == select_year]
        oppsummert_sidebar = oppsummert_sidebar[oppsummert_sidebar['Valgdistrikt'] == kommuner_valgdistrikt[select_kommune]]
        oppsummert_sidebar = oppsummert_sidebar.sort_values('ukr_pct_pop', ascending = False)
        oppsummert_sidebar = oppsummert_sidebar[['Kommune', 'ukrainere', 'ukr_pct_pop']]

        st.sidebar.dataframe(
            oppsummert_sidebar,
            hide_index = True,
            use_container_width = True,
            column_config = {
                'ukrainere': st.column_config.NumberColumn(
                    'Antall ukrainere', format='%.0f'
                ),
                'ukr_pct_pop': st.column_config.NumberColumn(
                    'Andel av befolkning', format='%.2f %%'
                )}
            )
    
        
    
    # If the user wants a top list by county
    if select_group == fylker.get(select_fylke):
        oppsummert_sidebar = oppsummert[oppsummert['År'] == select_year]
        oppsummert_sidebar = oppsummert_sidebar[oppsummert_sidebar['Fylkenummer'] == select_fylke]
        oppsummert_sidebar = oppsummert_sidebar.sort_values('ukr_pct_pop', ascending = False)
        oppsummert_sidebar = oppsummert_sidebar[['Kommune', 'ukrainere', 'ukr_pct_pop']]

        st.sidebar.dataframe(
            oppsummert_sidebar,
            hide_index = True,
            use_container_width = True,
            column_config = {
                'ukrainere': st.column_config.NumberColumn(
                    'Antall ukrainere', format='%.0f'
                ),
                'ukr_pct_pop': st.column_config.NumberColumn(
                    'Andel av befolkning', format='%.2f %%'
                )}
            )
    
    # If the user wants a top list by SSBs centrality index
    if select_group == 'SSBs sentralitetsindeks':
        oppsummert_sidebar = oppsummert[oppsummert['sentralitet'] == kommuner_sentralitet[select_kommune]]
        oppsummert_sidebar = oppsummert_sidebar[oppsummert_sidebar['År'] == select_year]
        #oppsummert_sidebar = oppsummert_sidebar[oppsummert_sidebar['Fylkenummer'] == select_fylke]
        oppsummert_sidebar = oppsummert_sidebar.sort_values('ukr_pct_pop', ascending = False)
        oppsummert_sidebar = oppsummert_sidebar[['Kommune', 'ukrainere', 'ukr_pct_pop']]
        
        sentralitet_description = """
        Sentralitetsindeksen er en måte å måle hvor sentral en kommune er med grunnlag i befolkning, arbeidsplasser og servicetilbud. Indeksen er utviklet av SSB.
        
        Indeksen går fra 1 (mest sentral) til 6 (minst sentral). Kommuner med sentralitet 4, 5 og 5 forstås som distriktskommuner. 
        
        {kommune} har sentralitet {sentralitet}.
        """.format(
            kommune = kommuner.get(select_kommune),
            sentralitet = kommuner_sentralitet[select_kommune]
        )
        
        st.sidebar.markdown(sentralitet_description)

        st.sidebar.dataframe(
            oppsummert_sidebar,
            hide_index = True,
            use_container_width = True,
            column_config = {
                'ukrainere': st.column_config.NumberColumn(
                    'Antall ukrainere', format='%.0f'
                ),
                'ukr_pct_pop': st.column_config.NumberColumn(
                    'Andel av befolkning', format='%.2f %%'
                )}
            )
    
    # If the user wants a top list by SSBs centrality index
    if select_group == 'KOSTRA-gruppe':
        
        oppsummert_sidebar = oppsummert[oppsummert['kostranavn'] == kommuner_kostra[select_kommune]]
        oppsummert_sidebar = oppsummert_sidebar[oppsummert_sidebar['År'] == select_year]
        #oppsummert_sidebar = oppsummert_sidebar[oppsummert_sidebar['Fylkenummer'] == select_fylke]
        oppsummert_sidebar = oppsummert_sidebar.sort_values('ukr_pct_pop', ascending = False)
        oppsummert_sidebar = oppsummert_sidebar[['Kommune', 'ukrainere', 'ukr_pct_pop']]
        
        kostra_about_komm = kostra_about[kostra_about['kostragruppe'] == kommuner_kostra[select_kommune]]
                
        sentralitet_description = """
        KOSTRA-gruppene er utviklet av SSB for å enklere sammenligne like kommuner. Gruppene er satt sammen basert på folkemengde og økonomiske rammebetingelser. 
        
        Les mer om KOSTRA-gruppene [her](https://www.ssb.no/offentlig-sektor/kostra/statistikk/kostra-kommune-stat-rapportering/om-kostra/kostra-gruppene).
        
        {kommune} er i Kostra-gruppe {kostra_gruppe}, som innebærer:  
        * Folkemengde: {folkemengde}  
        * Bundne kostnader: {kostnader}
        * Frie disponible inntekter: {inntekter}
        """.format(
            kommune = kommuner.get(select_kommune),
            kostra_gruppe = kommuner_kostra[select_kommune],
            folkemengde = kostra_about_komm['folkemengde'].iloc[0],
            kostnader = kostra_about_komm['bundekostnader'].iloc[0],
            inntekter = kostra_about_komm['frie_disponible_inntekter'].iloc[0]
        )
        
        st.sidebar.markdown(sentralitet_description)

        st.sidebar.dataframe(
            oppsummert_sidebar,
            hide_index = True,
            use_container_width = True,
            column_config = {
                'ukrainere': st.column_config.NumberColumn(
                    'Antall ukrainere', format='%.0f'
                ),
                'ukr_pct_pop': st.column_config.NumberColumn(
                    'Andel av befolkning', format='%.2f %%'
                )}
            )
        
    
    if select_group == 'Lokalavis (dekningsområde)':
        if pd.isna(coverage[select_paper][0]):
            st.markdown('''
                        Dekningsområdet for denne avisen er ikke klart. Hvis avisen er riksdekkende, velg "Norge" i stedet for "Lokalavis" i velgeren.
                        Hvis avisens dekningsområdet må defineres med postnummer eller andre geografiske kjennetegn (feks kyst), arbeider vi med å sammenstille dette. 
                        ''')
        
        oppsummert_sidebar = oppsummert[oppsummert['Kommunenummer'].isin(coverage[select_paper])]
        oppsummert_sidebar = oppsummert_sidebar[oppsummert_sidebar['År'] == select_year]
        #oppsummert_sidebar = oppsummert_sidebar[oppsummert_sidebar['Fylkenummer'] == select_fylke]
        oppsummert_sidebar = oppsummert_sidebar.sort_values('ukr_pct_pop', ascending = False)
        oppsummert_sidebar = oppsummert_sidebar[['Kommune', 'ukrainere', 'ukr_pct_pop']]
    
        st.sidebar.dataframe(
            oppsummert_sidebar,
            hide_index = True,
            use_container_width = True,
            column_config = {
                'ukrainere': st.column_config.NumberColumn(
                    'Antall ukrainere', format='%.0f'
                ),
                'ukr_pct_pop': st.column_config.NumberColumn(
                    'Andel av befolkning', format='%.2f %%'
                )}
            )
        
    if select_group == 'ROBEK':
        oppsummert_sidebar = oppsummert[oppsummert['År'] == select_year]
        oppsummert_sidebar = oppsummert_sidebar[oppsummert_sidebar['robek'] == 'robek']
        oppsummert_sidebar = oppsummert_sidebar.sort_values('ukr_pct_pop', ascending = False)
        oppsummert_sidebar = oppsummert_sidebar[['Kommune', 'ukrainere', 'ukr_pct_pop']]
        
        if oppsummert_komm_year['robek'].str.contains('ikke robek').iloc[0]:
            robek_string = """
            Liste med alle ROBEK-kommuner. {kommune} er ikke en ROBEK-kommune.
            
            """.format(
                kommune = kommuner.get(select_kommune)
            )
        else:
            robek_string = """
            Liste med alle ROBEK-kommuner. {kommune} er en ROBEK-kommune.
            
            """.format(
                kommune = kommuner.get(select_kommune)
            )
        
        st.markdown(robek_string)
        
        st.markdown('''
                    ROBEK er et register over kommuner som er i økonomisk ubalanse eller som ikke har vedtatt økonomiplanen, årsbudsjettet eller årsregnskapet innenfor de fristene som gjelder.
                    
                    Kommuner i ROBEK er underlagt statlig kontroll. Les mer om ROBEK [her](https://www.regjeringen.no/no/tema/kommuner-og-regioner/kommuneokonomi/robek-2/id449305/).
                    ''')

        st.dataframe(
            oppsummert_sidebar,
            hide_index = True,
            use_container_width = True,
            column_config = {
                'ukrainere': st.column_config.NumberColumn(
                    'Antall ukrainere', format='%.0f'
                ),
                'ukr_pct_pop': st.column_config.NumberColumn(
                    'Andel av befolkning', format='%.2f %%'
                )}
            )


use_container_width = False #st.checkbox("Full tabellbredde", value=True)


# ----------------------- #
# Main content of the app #
# ----------------------- # 

# create different tabs for the content
tab1, tab2, tab6, tab3, tab4, tab5, tab7 = st.tabs(['Dette er saken', 'Slik er det i din kommune', 'Mulige nyhetssaker', 'Slik kan du gå fram', 'Tallgrunnlag', 'Ekspertkilder og rapporter', 'Fakta og begreper'])

# In tab 1: Dette er saken
with tab1:
    
    national_col1, national_col2 = st.columns([5, 4])

    #with national_col1:
    national_text = """
    355 kommuner har til sammen bosatt 60.134 ukrainske flyktninger siden krigen startet i 2022 (per 19.02.24). I samme periode ble det bosatt 8.465 flyktninger fra andre land.
    
    Til sammenligning ble det under “flyktningbølgen” i 2015-2016 bosatt i overkant av 26.000 personer.
    
    Sist Norge gav en gruppe flyktninger kollektiv beskyttelse var på 1990-tallet. Da kom det 16.000 flyktninger fra Balkan.
    
    #### Hvordan har kommunene møtt det høye antallet ukrainere?
    
    — Det var nokså urealistiske forventninger i starten, sier forsker ved OsloMet, Vilde Hernes.

    — Ukrainerne skulle være som arbeidsinnvandrere som skulle hoppe ut i jobb, helt problemfritt, sier hun. (Forskningsrapport og intervju ligger under "Ekspertkilder og rapporter").

    Hernes er prosjektleder for OsloMets rapport om ukrainske flyktninger som ble publiserte i januar 2024. De har sett på flyktningenes opplevelse av mottak, bosetting og integrering, samt erfaringene til de som har tatt dem imot.
    
    ##### Her er mulige nyhetspoeng fra intervju med Vilde Hernes, basert på hennes forskning:

    - 11 prosent av ukrainerne snakker flytende engelsk, og 60 prosent snakker nesten ikke engelsk i det hele tatt.
    - De ukrainske flyktningene gir helsetjenestene mye dårligere vurdering enn for eksempel skole og barnehage. 
    - 37 prosent oppgir at barna fortsatt følger digital undervisning fra Ukraina.  
    - Andelen ukrainere som kommer ut i jobb etter introduksjonstilbud ligger omtrent likt med øvrige flyktninger.  
    - 75 prosent av ukrainerne har høy utdannelse. Andelen ukrainske flyktninger med høy utdannelse og engelskkunnskaper går ned over tid.

    #### De ensomme eldre
    Norge har bosatt omtrent 3.000 ukrainske flyktninger over 66 år siden krigen startet. De trenger andre tjenester enn det kommunene har vært vant med å tilby flyktninger tidligere. 
    
    — Det er en stor omveltning å skulle ta imot en så stor andel med eldre flyktninger, sier Vilde Hernes ved OsloMet.  
    
    — Ukrainske eldre er ensomme i Norge. Det er utfordrende for denne gruppen som står uten noe særlig tilbud, sier Nataliya Yeremeyeva. Hun er nestleder i Den ukrainske forening i Norge. (Intervju ligger under "Ekspertkilder og rapporter").

    ##### Her er mulige nyhetspoeng om de eldre flyktningene:
    - Hjelpeorganisasjoner peker på de eldre flyktningene som «de glemte», ifølge Vilde Hernes fra OsloMet.  
    - Eldre som kommer alene til Norge er ensomme, og lærer seg ikke språket, sier Yeremeyeva.
    - Tall fra IMDi viser at 13 prosent av de som bosettes er over 55 år. Dette utgjør rundt 7800 mennesker. Disse har ikke rett på introduksjonsprogram.
    
    
    #### Ukrainere er sykere enn nordmenn
    
    — Seks av ti ukrainere rapporterte at de hadde langvarige sykdommer eller plager, sier forsker ved Folkehelseinstituttet (FHI), Angela Susan Labberton. (Forskningsrapport og intervju ligger under "Ekspertkilder og rapporter").
    
    FHI har sett på selvrapportert helse- og helsetjenestebehov i et utvalg voksne flyktninger fra Ukraina, sammenlignet med den norske befolkningen. 

    
    ##### Her er mulige nyhetspoeng om helse:

    - Ukrainere har dårligere helse enn nordmenn og betydelig dårligere tannhelse, sier rapporten til FHI.  
    - Ingen sitter med en oversikt over hvor mange ukrainere som har mottatt behandling via primær- eller spesialisthelsetjenesten, ifølge Angela Susan Labberton ved FHI.  
    - 70 prosent av de ukrainske flyktningene som har ønsket psykisk helsehjelp, har ikke fått det, viser en forskningsrapport fra Nasjonalt kunnskapssenter om vold og traumatisk stress (NKVTS). (Forskningsrapport ligger under "Ekspertkilder og rapporter").
    - Tall fra Verdensbanken viser at forventet levealder for en ukrainer før krigen var 70 år. Nordmenns forventede levealder er 83 år.  
    - Norge har per 8. mars 2024 evakuert 373 syke og skadde ukrainske pasienter.  To tredeler har kreft og en tredel skader. (Intervju med Anders Holtan, overlege ved nasjonalt medevac senter ved Oslo Universitetssykehus, ligger under "Ekspertkilder og rapporter")  


    #### Midlertidighet betyr usikkerhet
    
    Flyktningene fra Ukraina har kollektiv, midlertidig beskyttelse. De er i Norge på ubestemt tid.
    
    Tall fra IMDi viser at 30 prosent av de som er bosatt er under 18 år.  
    
    — Å oppskalere tjenester innenfor skole, barnehage og helsetjenester er en veldig stor risiko for kommunene fordi ukrainere har midlertidig tillatelse, sier Vilde Hernes fra OsloMet.
    
    Dette kan være krevende for private arbeidsgivere som skal ansette, og kommunen som skal skalere opp sine tjenester. 

    — Arbeidsgivere var svært positive til å ansette ukrainere da krigen startet. Nå er de mer skeptiske, sier Vilde Hernes, forsker hos OsloMet. 

    ##### Her er mulige nyhetspoeng om midlertidighet: 
    
    - Det er risikabelt for kommunene å ansette lærere og sykepleiere i faste stillinger. Hvis ukrainerne må hjem, slutter kommunene å få tilskudd fra IMDi og taper penger.  
    - 54 prosent av ukrainere er usikker på om de kommer til å returnere til Ukraina når krigen er over, i følge forskningsrapport fra OsloMet. 

    """
    
    st.markdown(
        national_text
    )

    #with national_col2:
    #    with st.expander("Fakta og begreper om bosetting av ukrainere"):
            
    #        pass


# Tab 2: Statistical description of the municipality
with tab2:
    
    print(oppsummert_komm)
    
    summarized = """
    
    {kommune} har bosatt {sum_total_ukr:,.0f} ukrainske flyktninger siden krigen brøt ut. De utgjør {ukr_pct_pop:.2f} prosent av befolkningen, og {ukr_pct_ovr:.2f} prosent av alle bosatte flyktninger i samme periode. 
    
    I **{year}** ble det bosatt {sum_total_ukr_year} ukrainere i kommunen, noe som utgjør {ukr_pct_pop_year:.2f} prosent av befolkningen.  
    
    """.format(
                kommune = kommuner.get(select_kommune), 
                year = select_year, 
                sum_total_ukr = oppsummert_komm['ukrainere'].sum(),
                sum_total_ukr_year = oppsummert_komm_year['ukrainere'].sum(),  
                ukr_pct_pop_year = oppsummert_komm_year['ukr_pct_pop'].sum(),  
                #sum_total_pop = oppsummert_komm['pop'].sum(),
                ukr_pct_pop = (oppsummert_komm['ukrainere'].sum()/oppsummert_komm_2024['pop'].sum())*100,
                ukr_pct_ovr = (oppsummert_komm['ukrainere'].sum()/oppsummert_komm['innvandr'].sum())*100
                )
    summarized_anmodning = """
    
    ##### Anmodninger
     Integrerings- og mangfoldsdirektoratet (IMDi) har anmodet kommunen om å bosette {innvandr_anmodet:,.0f} flyktninger i  2024. Det inkluderer både ukrainske og øvrige flyktninger. Kommunen {innvandr_vedtak_string}. 
     
     {kommune} {ema_vedtak_2024_string}
    """.format(
        kommune = kommuner.get(select_kommune), 
        innvandr_anmodet = anmodninger['innvandr_anmodet'].iloc[0],
        innvandr_vedtak_string = anmodninger['innvandr_vedtak_string'].iloc[0],
        ema_vedtak_2024_string = anmodninger['ema_vedtak_2024_string'].iloc[0],
    )
    
    summarized_rank = """
    
    I **{year}** kom {kommune} på {fylke_rank:.0f}. plass i fylket, og {national_rank:.0f}. plass i hele landet i en rangering over hvilke kommuner som tar imot flest ukrainske flyktninger etter befolkningsstørrelse. 
    """.format(
                kommune = kommuner.get(select_kommune), 
                year = select_year, 
                fylke_rank = oppsummert_komm_year['fylke_rank'].sum(),
                national_rank = oppsummert_komm_year['national_rank'].sum(),                
                )
    
    st.markdown(summarized)
    st.markdown(summarized_rank)
    if ukr_mottak_bool:
        st.markdown(ukr_mottak_string)
    st.markdown(summarized_anmodning)
    
        
    if select_year == 2024:
        fastlege = """
        ##### Fastlegekapasitet
        
        Det er ikke tilgjengelig tall for 2024. Derfor gjengis tall fra 2023.
        
        {lege_category}.

        """.format(
            year = select_year,
            kommune = kommuner.get(select_kommune), 
            legeliste_n = oppsummert_komm_year['legeliste_n'].iloc[0],
            legeliste_pct = oppsummert_komm_year['legeliste_pct'].iloc[0],
            lege_category = oppsummert_komm_year['lege_category'].iloc[0]
            )
    
    else:
        
        fastlege = """
        ##### Fastlegekapasitet
            
        {lege_category}.
        
        """.format(
            year = select_year,
            kommune = kommuner.get(select_kommune),
            #legeliste_n = oppsummert komm_year['legeliste_n'].iloc[0],
            #legeliste_pct = oppsummert_komm_year['legeliste_pct'].iloc[0],
            lege_category = oppsummert_komm_year['lege_category'].iloc[0]
        )
        
    st.markdown(fastlege)
    
    st.markdown('''
            ##### Tilskudd fra IMDi
            
            Kommunene mottar tilskudd for flyktninger de fem første årene de er bosatt i kommunen. 
            
            I 2022 og 2023 har kommunen mottatt totalt {sum_tilskudd:,.0f} millioner kroner i tilskudd fra IMDi.  
            
            Beløpet skal dekke utgifter til bosetting og integrering av ukrainske flyktninger, i tillegg til flyktninger fra andre land.
            
            Merk at enkelte verdier kan være tilbakeholdt av IMDi av anonymiseringshensyn.
            
            Tabellen viser tilskudd gitt i **{year}** for alle flyktninger bosatt i kommunen de siste fem årene.
            '''.format( 
                year = select_year,
                sum_tilskudd = tilskudd_komm_total/1000000
                )
            )
    
    st.dataframe(
        tilskudd_komm_year.style.format(thousands=" ", precision=0),
        hide_index=True,
        column_config={
            'Antall': st.column_config.NumberColumn(
                'Sum',
                #format="kr %:,f",
                #format = None,
                #min_value = 0,
                #max_value = tilskudd_komm_total
                ),
            'Kommentar': st.column_config.TextColumn(
                'Kommentar'
            )
        },
        use_container_width= True
    )

with tab6:
    st.markdown("""
    ##### Ukrainske flyktninger får sjelden psykisk helsehjelp 

    **Mulig sak**: 70 prosent av de ukrainske flyktningene som har ønsket psykologhjelp har ikke fått det, viser forskningsrapport fra Nasjonalt kunnskapssenter om vold og traumatisk stress (NKVTS). (Forskningsrapport ligger under "Ekspertkilder og rapporter") 

    **Mulig historie**: Ukrainske flyktninger som har tjenestegjort i krigen. Eller ukrainske flyktninger som har traumer etter krigen.
    
    Hvilken psykisk helsehjelp har de fått i Norge? 

    Hvordan er dette sammenlignet med asylsøkerne som kommer fra for eksempel Gaza?  
       
       
      
    ##### Hvor blir det av pengene?
    
    **Mulig sak**: Kommunen har totalt mottatt xxx millioner kroner i 2022 og 2023. Hva har de brukt tilskuddspengene på?
    
    **Mulig historie**: En ukrainsk flyktning som ikke har fått tjenestene hen har rett på.  
    
    Tilskuddspengene er ikke øremerket og ikke rapporteringspliktig. 
    
    Sitter kommunen igjen med økonomisk overskudd, og hva gjør de eventuelt med pengene? 
    
    Se pengebruken opp mot hvilke tjenester flyktningene faktisk har fått i kommunen. Er flyktningene misfornøyd med tjenestene? Har Statsforvalter avdekket avvik?  
       
       
    
    ##### Vil bosette færre flyktninger enn kommunen er anmodet om
    
    **Mulig sak**: Kommunen ble anmodet om å bosette x antall flykninger, men har bare sagt ja til x.  
    
    **Mulig historie**: En ukrainsk flyktning som sitter på asylmottak og venter på å få tildelt en kommune. Eventuelt en som er bosatt, men som ventet lenge på mottak.
    
    Hva er grunnen til at kommunen ikke ønsker å bosette antallet flyktninger de er bedt om? Burde de ta imot flere? Se på kommunens fastlegekapasitet, økonomi etc.  
       
       
    
    ##### Vil bosette flere flyktninger enn kommunen er anmodet om 
    **Mulig sak**: Kommunen ble anmodet om å bosette x antall flyktninger, men har selv bedt om å ta imot x.
    
    Hvorfor ønsker kommunen å ta imot flere flyktninger enn de har blitt anmodet om?  
    
    Kommer flyktningene raskt ut i jobb eller utdanning? 
    
    Hvor mange flyktninger har flyttet fra kommunen?  
    
    Er penger et insentiv for å ta imot flere?  
       
       

    ##### Hvor mange flyktninger har kommunen bosatt sammenlignet med nabokommunene? 
    
    **Mulig sak**: Kommunen tar imot mange flyktninger i forhold til befolkningstallet.  Kommunen er på x plass i fylket.  
    
    Sammenlign din kommune med sammenlignbare kommuner (folketall, økonomi og sentralitet). Velg relevante grupperinger i venstre marg på nettsiden.  
       
       
    
    ##### Ukrainske flyktninger over 55 år får ikke tilbud om introduksjonsprogram
    
    **Mulig sak**: Ukrainske flyktninger over 55 år blir ensomme og ikke integrert i det norske samfunnet.  
    
    **Mulig historie**: En ukrainsk flyktning over 55 år som står uten tilbud.  
    
    Hvorfor gir ikke kommunen dem over 55 år tilbud om deltagelse på introduksjonsprogram? 
    
    Hva gjør kommunen for å integrere dem i samfunnet?  Hva gjør frivillige organisasjoner?
    
    Hva er den langsiktige planen for denne gruppen?  
       
       
    
    ##### Kommunen gir tilbud til ukrainske flyktninger over 55 år, selv om de ikke må
    
    **Mulig sak**: I denne kommunen får ukrainske flyktninger tilbud om introduksjonsprogram, selv om kommunen ikke er pliktig til å gi dem dette.  
    
    **Mulig historie**: En ukrainsk flyktning over 55 år som går på introduksjonsprogram, eller har kommet ut i jobb. Eller en lærer på introduksjonsprogram som underviser flyktninger over 55 år.
    
    Hvorfor har kommunen valgt å gi tilbud til dem over 55 år? 
    
    Kommer de over 55 år ut i jobb etter endt introduksjonsprogram? 
    
    Hvor mange av de over 55 år benytter seg av introduksjonsprogrammet?  
       
       

    ##### Så mange ukrainere har kommet ut i jobb 
    
    **Mulig sak**: x antall i kommunen har fått seg arbeid etter fullført introduksjonsprogram.
    
    **Mulig historie**: En ukrainsk flyktning som har kommet ut i arbeid, eller en arbeidsgiver som har ansatt en.
    
    Hvilke bransjer og bedrifter har ansatt ukrainske flyktninger?
    
    Hvor mange har fullført introduksjonsprogrammet, men ikke kommet i jobb? Hva er grunnen til det? 
    
    Hvilken tilrettelegging kreves ved ansettelse, og hvilken kunnskap tilfører de eventuelt bedriften?  
       
       
    
    ##### Ukrainerne har dårligere helse enn nordmenn 
    
    **Mulig sak**: Ukrainere har dårligere helse enn nordmenn, viser FHI-rapport. Forventet levealder for ukrainere var 70 år. Forventet levealder for nordmenn er 83 år. 
    
    **Mulig historie**: En ukrainsk flyktning som er syk/skadet. 
    
    Hvordan er sykdomsbildet til ukrainerne som kommunen har bosatt? Har ukrainerne fått den helseoppfølgingen de trenger? 
    
    Har det påvirket kommunehelsetjenestene? Hvordan har kommunen løst et eventuelt økt press? 
    
    I denne kommunen får de x kroner ekstra i tilskudd for pleietrengende. Hva har pengene gått til?  
       
       

    ##### Økt ventetid på mottak for andre asylsøkere  
    
    **Mulig sak**: Ventetiden på mottak har økt for øvrige flyktninger som et resultat av de ukrainske flyktningene.  
    
    **Mulig historie**: En asylsøkere fra et annet land som har sittet lenge på mottak og ventet på svar på asylsøknaden sin. 
    
    Hva er gjennomsnittlig ventetid på mottok for øvrige flyktninger? 
    
    Hva tenker øvrige flyktninger om at ukrainere bosettes raskt, mens de selv må vente lenger? 
    
    Hva tenker ukrainske flyktninger om at de får prioritet? 
    
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
    * Hvorfor tar kommunen imot færre/flere enn IMDi har anmodet? (sjekk tall for din kommune i talloversikten).
    * Hvor mange enkeltpersoner har kommunen ikke villet bosette?
    * Har kommunen vært nødt til å ansette flere (lærere, sykepleiere, saksbehandlere) for å opprettholde et godt tjenestetilbud? Er det utfordrende å ansette folk i faste stillinger siden det er uvisst hvor lenge ukrainere blir i Norge?
    * Be kommunen om en oversikt om hvordan tilskuddene fra IMDi er brukt.
    
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
        
        Epost til NAV i Sortland kommune fra Samarbeidsdesken 23.02.2024
        
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
        av eldre fra IMDi.</p>
        
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
                kommune = kommuner.get(select_kommune), 
                year = select_year, 
                sum_year = flyktninger_komm_year['pop'].sum(),  
                sum_total = flyktninger_komm['pop'].sum()
                )

    with st.container():
        with tablecol1:
            st.markdown(pop_text)
    
        with tablecol2:
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
            """.format(
                kommune = kommuner.get(select_kommune), 
                year = select_year, 
                sum_year = flyktninger_komm_year['ukrainere'].sum(),  
                sum_total = flyktninger_komm['ukrainere'].sum(),
                prikking = check_ano(flyktninger_komm_year['ukrainere_string'])
                )

    with st.container():
        with tablecol3:
            st.markdown(ukr_text)
    
        with tablecol4:
            st.dataframe(
            flyktninger_komm_year[['År', 'Kjønn', 'Aldersgruppe', 'ukrainere_string', 'ukr_pct']],
            use_container_width = use_container_width,
            hide_index = True,
            column_config = {
                'År': st.column_config.NumberColumn(format="%.0f"),
                'ukrainere_string': st.column_config.TextColumn(
                    'Antall'
                ),
                'ukr_pct': st.column_config.NumberColumn(
                    'Andel', format='%.1f %%'
                )#,
                #'ukr_prikket': st.column_config.TextColumn(
                #    'Prikket', 
                #    help = 'Prikkede data betyr at kommunen har tatt i mot mindre enn fem EMA. Data tilbakeholdes av IMDi av personvernhensyn.'
                #   )
            }
            )
            
    ema_text = """
            ##### Bosatte enslige mindreårige fra Ukraina
            """.format(
                kommune = kommuner.get(select_kommune), 
                year = select_year, 
                sum_year = ema_komm_year['ema'].sum(),  
                sum_total = ema_komm['ema'].sum()
                )

    with st.container():
        with tablecol5:
            st.markdown(ema_text)
    
        with tablecol6:
            st.dataframe(
            ema_komm_year[['År', 'ema_string']],
            use_container_width = use_container_width,
            hide_index = True,
            column_config = {
                'År': st.column_config.NumberColumn(format="%.0f"),
                'ema_string': st.column_config.TextColumn(
                    'Enslige mindreårige', 
                    )}
            )

            
    ovr_text = """
            ##### Øvrige flyktninger (ikke kollektiv beskyttelse)
            """.format(
                kommune = kommuner.get(select_kommune), 
                year = select_year, 
                sum_year = flyktninger_komm_year['ovrige'].sum(),  
                sum_total = flyktninger_komm['ovrige'].sum()
                )
            


    with st.container():
        with tablecol7:
            
            st.markdown(ovr_text)
    
        with tablecol8:
            st.dataframe(
            flyktninger_komm_year[['År', 'Kjønn', 'Aldersgruppe', 'ovrige_string', 'ovr_pct']],
            use_container_width = use_container_width,
            hide_index = True,
            column_config = {
                'År': st.column_config.NumberColumn(format="%.0f"),
                'ovrige_string': st.column_config.TextColumn(
                    'Antall'
                ),
                'ovr_pct': st.column_config.NumberColumn(
                    'Andel', format='%.1f %%'
                )}
            )
    
    st.markdown("""
                
    ###### Anonymisering 
    Hvis det står *<5* i en eller flere tabeller, betyr det at antallet er mellom èn og fem. IMDi tilbakeholder eksakt antall for å unngå identifisering.            
    
    ##### Tallkilder
    Befolkningstall er hentet fra[ SSB-tabell 07459](https://www.ssb.no/statbank/table/07459). Tall hentet 22.02.2024.
    
    Fakta om venteliste hos fastlege og reservekapasitet er hentet fra [SSB-tabell 12005](https://www.ssb.no/statbank/table/12005). Tall hentet 18.03.2024.
    
    Tall som beskriver antall ukrainere og antall øvrige flyktninger er sammenstilt av fra Integrerings- og mangfolksdirektaret. Tall mottatt 19.02.2024.
    
    Tall som beskriver enslige mindreårige er sammenstilt av Integrerings- og mangfolksdirektaret. Tall mottatt 09.02.2024.
    
    Anmodningstall er hentet fra [IMDis nettsider](https://www.imdi.no/planlegging-og-bosetting/bosettingstall/). Tall hentet 08.03.2024 kl. 12:20.
    
    Tilskuddstall er hentet fra [IMDis nettsider](https://www.imdi.no/om-integrering-i-norge/statistikk/F00/tilskudd). Tall hentet 11.03.2024.
    
    Bosettingstall fra 2015-2016 er hentet fra IMDis årsrapporter fra hhv. [2015](https://www.imdi.no/globalassets/dokumenter/arsrapporter-og-styrende-dokumenter/arsrapport-2015/imdis-arsrapport-2015.pdf) (side 4) og [2016](https://www.regjeringen.no/contentassets/59f5becfc2384dacb88e9ef4fcccba33/arsrapport-2016-imdi.pdf) (side 2).
    
    Tall på antall flyktninger fra Balkan på 1990-tallet er hentet fra [Store norske leksikon](https://snl.no/kollektiv_beskyttelse).
    """)

# Tab 5: Expert interviews
with tab5:
    
    st.markdown(
        """
        Samarbeidsdesken har gjennomført intervjuer og sitatsjekk med ekspertkilder. Sitatene kan brukes fritt. 
        """
    )
    fhi_string = """
    
    Angela Labberton med flere har undersøkt selv-rapportert helse og helsetjenestebehov blant voksne ukrainere fra Ukraina. 
    
    Det er viktig at nyansene og forbehold kommer frem og at ikke svarene klippes ut på en måte som gjør at meningen blir endret. Også skillet mellom det som er funnet i undersøkelsen versus andre vurderinger.
    
    Rapporten er tilgjengelig [her](https://www.fhi.no/nyheter/2023/ukrainske-flyktninger-darligere-helse-og-betydelig-darligere-tannhelse/).
    
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
    
    with st.expander('Intervju med Angela S. Labberton ved Folkehelseinstituttet'):
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
    
    Vilde Hernes med flere har undersøkt erfaringene til ukrainske flyktninger som har kommet til Norge etter Russlands invasjon i 2022. 
    
    Rapporten er tilgjengelig [her](https://oda.oslomet.no/oda-xmlui/handle/11250/3029151).
    
    ##### Hvem er ukrainerne som kommer? 
    — Tilstrømningen er veldig forskjellig fra 2015. Da var det en klar overvekt av menn som kom. Med ukrainerne var det i starten en stor overvekt kvinner, men etter de første månedene har andelen menn og kvinner vært mer lik, og holdt seg stabil.  
    
    — I stor grad har ukrainerne høy utdannelse. 75 prosent har høyere utdannelse. Men her ser vi litt utvikling over tid. Større andel av de som kom i den første fasen hadde høyere utdannelse enn dem som har kommet i senere tid. Det samme gjelder engelskkunnskapene.  
    
    — Dette er vanlig dynamikk. At de som kommer i første fase ofte er ressurssterke, mens etter hvert så kommer det mindre ressurssterke.  
    
    ##### En stor andel av de ukrainske flyktningene er eldre. Hvilke utfordringer byr dette på?
    — 5 prosent av de som kommer er over 66 år. Dette er mye høyere enn tidligere år når tallet har lagt på 1-2 prosent. Men de prosentene høres jo ikke så mye ut. Det viktige er at det totale antallet er utrolig mye høyere enn tidligere, og integreringsapparatet trenger helt annen kompetanse og et helt annet tilbud enn man har for folk i arbeidsdyktig alder som skal ut i et introduksjonsprogram.  
    
    — Det er en stor omveltning å skulle ta imot en så stor andel med eldre flyktninger.  Det trengs andre tjenester enn det man har vært vant til tidligere.  
    
    ##### Hvordan har dette vært for kommunene?
    — Generelt har kommunene press på eldreomsorg og helsetjenester, og når det over natten kommer veldig mange flere, så blir det naturlig nok enda større press.  
    
    — Flyktningtjenesten og introduksjonsprogrammet er ikke de eneste som skal ta imot flyktninger. Hele kommunen bosetter med hele tjenesteapparatet. Å skulle oppskalere alle tjenester er krevende.  
    
    — Veldig mange har 2015 i tankene. De husker at de oppskalerte, men så stoppet det å komme folk. Da taper kommunene penger, for de slutter å få tilskudd for personer. Veldig mange kommuner har akkurat rukket å nedskalere etter 2015 når ukrainerne begynte å komme i 2022. 
    
    — Normalt når vi tar imot flyktninger, tar vi for gitt at de skal bli. Man tror ikke at de skal returnere. Men denne gruppen har bare midlertidig opphold.  
    
    — Å oppskalere tjenester innenfor skole, barnehage og helsetjenester er en veldig stor risiko for kommunene fordi ukrainere har midlertidig tillatelse.  Hadde kommunene visst at disse skulle bli i all overskuelig framtid kunne de ansatt mye leger, sykepleiere og lærere i faste stillinger fordi de hadde fått en større befolkning. Men siden man ikke vet om de skal være her i tre måneder, tre år eller resten av livet, så er det mange kommuner som ikke tør å oppskalere. I tillegg er det mangel på folk til å fylle slike stillinger som sykepleiere, lærere, leger etc. 

    ##### På hvilke tjenester er det størst press i kommunen? 
    — Helsevesenet og Nav er veldig presset. Lokalt NAV-personell sier at de ikke har kapasitet til å følge opp denne gruppen. De er rett og slett ikke nok ansatte til å følge opp en så stor økning av mennesker på kort tid.  
    
    — Mitt inntrykk har vært at skole og barnehage har gått bra hittil, mens helse er et generelt problem fra før av.  
    
    ##### Hvordan løser kommunene dette?  
    — Det er veldig forskjellig hvordan kommunene løser det. Noen har unntak for midlertidige stillinger, noen tenker at de skal ri av seg stormen og håper at det skal fungere, men tør ikke å ansette. Andre prøver å bruke private tjenester i større grad, da kan de eventuelt nedskalere fort. Men det er et helt reelt dilemma som kommunene uttrykker veldig sterkt, at det er krevende. 

    ##### Har bosettingen av ukrainere vært forskjellig fra bosetting av andre flyktninger?
    
    — Det har kanskje vært flere likhetstrekk enn forskjeller i arbeidet med å ta imot ukrainere og andre flyktninger. Det var nok nokså urealistiske forventinger om i starten at dette skulle være helt annerledes.      
    
    — Ukrainerne skulle bare gli inn, dette skulle bare være som arbeidsinnvandrere som skulle hoppe ut i jobb, helt problemfritt. Det har vist seg at denne gruppen også trenger støtte og hjelp for å komme seg ut i jobb og arbeid. Selv om de har høy utdanning får de ikke nødvendigvis brukt det i Norge når de ikke kan engelsk, og ikke norsk.    
    
    — Ukrainere har generelt ikke gode engelskkunnskaper. Det er en myte som må avkreftes gang på gang, på gang.    
    
    — Kun 11 prosent snakker flytende engelsk, og rundt 60 prosent kan nesten ikke engelsk i det hele tatt. Av de som kommer nå, er det en enda lavere andel som snakker engelsk.  
    
    ##### Skole
    
    — Usikkerheten for framtiden er framtredende for denne gruppen. 37 prosent svarer at barna fortsatt følger online ukrainsk skole. Oftest i tillegg til å følge norsk skole.
    
    ##### Så det har ikke vært enklere å få en ukrainer ut i jobb enn øvrige flyktninger? 
    — Ukrainere som har gått introduksjonstilbudet har cirka samme resultater som andre flyktninggrupper har hatt når det kommer til å komme seg ut i arbeid.  
    
    — Når du ikke kan språket og har et annet alfabet så er det ikke nødvendigvis enkelt å få dem ut i jobb. Det er en helt urealistisk forventning.  
    
    — I vår rapport finner vi at flere arbeidsgivere i utgangspunktet var mer positivt innstilt til å ansette ukrainske flyktninger enn øvrige flyktninger da krigen startet, men at de på en annen side sier at den midlertidig tillatelse gjør at de er mer skeptiske til å ansette dem. Det å ansette noen, og lære dem opp, tar tid og koster penger.  
    
    — Det er en stor vilje for å lære seg norsk og komme ut i arbeidslivet, men det er veldig mange som møter på utfordringer. Språk trekkes frem som den største barrieren.
    
    ##### Hvilke tilbud gir kommunene til de over 55 år?
    
    — Det er veldig forskjellig om kommunen tilbyr norskopplæring og introduksjonsprogram til denne gruppen. Det handler om kapasitet. Små kommuner tilbyr i større grad. Det handler nok om at når de først har opprettet en klasse, kan de like gjerne fylle den opp. I større kommuner er det færre som tilbyr norskopplæring til denne gruppen som de ikke har plikt til å tilby.  
    
    — Halvparten av kommunene opplyser at de ukrainske flyktningene har fått mindre norskundervisning og introduksjonsprogram enn hva de har hatt rett til. De har ikke hatt klasserom, de har ikke hatt nok lærere, de har ikke hatt mulighet til å oppskalere så raskt som behovet var.  
    
    — Mange påpeker at dette er en gruppe vi ikke har vært vant til å ha en så høy andel av. Dette er en gruppe som blir litt glemt med at man ikke har så mye tilbud.  
    
    — En del av de frivillige organisasjonene sier at de eldre er glemt, det er ikke noe tilbud for dem.
    
    ##### Hva vet dere om helsesituasjonen til de som kommer? 
    — Ukrainerne gir helsetjenesten mye dårligere score enn for eksempel skole og barnehage.  
    
    — Det er en kulturkræsj på hva man er vant til i helsevesenet.  
    
    — I Ukraina er de mye mer vant til å bli sendt til en spesialist direkte, de har ingen fastlegeordning. Det er også mye mer vanlig å få utskrevet medisiner for ting vi her i Norge er mer restriktive på.  
    
    — Det var noen som ble sjokkert da de ble bedt om å drikke Cola fordi de hadde feber og vondt i magen. De ville ha medisin.  
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
    
    with st.expander('Intervju med Anders Holtan, Oslo universitetssykehus'):
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
        
    with st.expander('Intervju med Nataliya Yeremeyeva, nestleder i ukrainsk forening'):
        
        natyer_string = """
        
        Nataliya Yeremeyeva, nestleder i ukrainsk forening.
        
        ##### Hva vet du om de eldre ukrainerne som kommer til Norge?
        — Eldre mennesker er en spesielt sårbar gruppe. Det er utfordrende for denne gruppen uten noe særlig tilbud. Ukrainske eldre er ensomme i Norge.  
        
        — Noen eldre kommer med familien sin, de blir ikke nødvendigvis integrert i Norge, men de har det nok psykisk bedre enn de som kom alene. De som kom alene det ganske vanskelig.  
        
        — Om de har eller ikke har mulighet til å lære språket er det likevel alltid vanskeligere for eldre å lære seg et nytt språk.  
        
        — Folk pensjonerer seg tidligere i Ukraina, og de har dårligere helse enn nordmenn.  

        ##### Løsning? 

        — Frivillige organisasjoner burde fått mer tilskudd slik at de kunne arrangert sosiale aktiviteter der eldre ukrainere de kan lære seg språket, ha et fellesskap og føle seg som en del av samfunnet.  
        
        — Hvis de ikke går på introduksjonsprogram lærer de ikke om det norske samfunnet, og hvis de ikke kan språket kan de ikke snakke med naboen eller med folk på butikken. Det begrenser alle muligheter for deltakelse i samfunnet dramatisk.  
        
        — Alle kommuner burde tilby introduksjonsprogram til de som ønsker det som en integreringsstrategi. 


        ##### Ekstra: tannlege.
        — Folk forteller at det tar lang tid å komme til tannlegen.  Når det for eksempel er snakk om tannregulering, drar flere tilbake til Ukraina for å gå til tannlege.  
        
        — De få akuttbehandling i Norge, men behandlinger som kan vente blir ikke dekket - som for eksempel implantat eller krone. Flere velger derfor å dra på turer hjem til Ukraina å fikse dette.     
        """

        st.markdown(natyer_string)
        
with tab7: 
    st.markdown(
                """
                
                Kilde: IMDi
                ##### Kommunene kan selv velge hvem og hvor mange flyktninger de vil bosette: 
                
                Hvert år får kommunene en forespørsel fra IMDi om å bosette et antall flyktninger i kommunen. De kan selv velge hvor mange de ønsker å ta imot.  
                
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
                    
                Kommunene mottar de samme satsene for ukrainere som for andre flyktninger kommunen bosetter etter avtale med IMDi. 
                    
                ##### Tilskudd for opplæring i norsk og samfunnskunnskap for ukrainske voksne
                Kommunene mottar også persontilskudd på 39 700 kroner for voksne ukrainere (18-67 år) som får opplæring i norsk og samfunnskunnskap.  Hvis det er færre enn 150 personer i denne målgruppen, får kommunen et ekstra tilskudd opp mot 694 600 kroner.  
                
                ##### Økonomisk støtte til ukrainere
                Full deltakelse i introduksjonsprogrammet gir økonomisk støtte på omtrent 237 000 kroner i året. Det må skattes av støtten. Eventuell annen økonomisk støtte eller inntekt fra jobb, kan gjøre at flyktningen får mindre utbetalt.

                Kilde: IMDi
                """
            )