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

#folketall = load_data('app_flyktninger_folketall')

# ------------------------------------------------------------------- # 
# Create a dictionary describing the coverage area of each news paper #
# ------------------------------------------------------------------- #

lla = load_data('lla')
coverage = {g: d['kommnr'].values for g, d in lla.groupby('avis')}

#print(pd.isna(coverage['Akers Avis Groruddalen'][0]))


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

#print()

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
oppsummert_year = oppsummert[oppsummert['År'] == 2023] 

# Dataframe with 4 lines (gender x age) per year, per municipality
flyktninger_fylke = flyktninger[flyktninger['Fylkenummer'].isin([select_fylke])] 
flyktninger_komm = flyktninger[flyktninger['Kommunenummer'].isin([select_kommune])] 
flyktninger_komm_year = flyktninger_komm[flyktninger_komm['År'] == select_year] 
flyktninger_cols = ['Kommune', 'År', 'Kjønn', 'Aldersgruppe', 'ukrainere', 'ukr_pct', 'ukr_prikket', 'ovrige', 'ovr_pct', 'ovr_prikket', 'pop', 'pop_pct']

# Dataframe with enslige mindreårige. Both ukrainians and other refugees. 
ema_komm = ema[ema['Kommunenummer'].isin([select_kommune])]
ema_komm_year = ema_komm[ema_komm['År'] == select_year] 

# Dataframe with anmodningstall for the seelcted kommune.
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
                    'Andel av befolkning', format='%.1f %%'
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
                    'Andel av befolkning', format='%.1f %%'
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
                    'Andel av befolkning', format='%.1f %%'
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
                    'Andel av befolkning', format='%.1f %%'
                )}
            )
    
    # If the user wants a top list by SSBs centrality index
    if select_group == 'KOSTRA-gruppe':
        
        #print(kommuner_kostra[select_kommune])
        oppsummert_sidebar = oppsummert[oppsummert['kostranavn'] == kommuner_kostra[select_kommune]]
        oppsummert_sidebar = oppsummert_sidebar[oppsummert_sidebar['År'] == select_year]
        #oppsummert_sidebar = oppsummert_sidebar[oppsummert_sidebar['Fylkenummer'] == select_fylke]
        oppsummert_sidebar = oppsummert_sidebar.sort_values('ukr_pct_pop', ascending = False)
        oppsummert_sidebar = oppsummert_sidebar[['Kommune', 'ukrainere', 'ukr_pct_pop']]
        
        kostra_about_komm = kostra_about[kostra_about['kostragruppe'] == kommuner_kostra[select_kommune]]
        
        print(kostra_about_komm)
        
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
                    'Andel av befolkning', format='%.1f %%'
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
                    'Andel av befolkning', format='%.1f %%'
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
                    'Andel av befolkning', format='%.1f %%'
                )}
            )


use_container_width = False #st.checkbox("Full tabellbredde", value=True)


# ----------------------- #
# Main content of the app #
# ----------------------- # 

# create different tabs for the content
tab1, tab2, tab3, tab4, tab5 = st.tabs(['Dette er saken', 'Slik er det i {kommune}'.format(kommune = kommuner.get(select_kommune)), 'Slik går du fram', 'Tallgrunnlag', 'Ekspertintervju'])

# In tab 1: Dette er saken
with tab1:
    
    national_col1, national_col2 = st.columns([5, 4])

    with national_col1:
        national_text = """

        Siden krigen startet i februar 2022 har 60,134 ukrainske flyktninger blitt bosatt i Norge. I samme periode har det kommet 8,465 flyktninger fra andre land. 

        Til sammenligning ble det bosatt i overkant av 15,000 flyktninger i 2015, og i underkant av 10,000 flyktninger i 1993, da mange flyktet fra Bosnia-Hercegovina.
    
        I 2023 ble det bosatt ukrainere i {munn_count} av 357 norske kommuner.
        
        ##### Ikke problemfritt  
        
        Forsker ved NIBR, Vilde Hernes, sier dette ikke er den suksesshistorien som mange hadde ventet (Se her for fullt intervju med sitater, og lenke til forskningsrapporten)
        
        * Kun 10 prosent av ukrainerne snakker engelsk.  
        * Andelen som kommer ut i jobb etter introduksjonsprogrammet ligger helt likt med øvrige flyktninger.  
        * Flyktningene som kom i starten hadde høy utdannelse, men dette har endret seg over tid. Nå er det flere ressurssvake som kommer.  
        * Varierende tilbud til dem over 55 år. 
        
        Flyktninger Norge er vant til å ta i mot er menn i arbeidsdyktig alder. Men 13 prosent av ukrainerne som er bosatt er over 55 år, og 30 prosent er under 18 år. 
        
        ##### Høy andel eldre, få tilbud  
        
        På grunn av det store antallet ukrainske flyktninger utgjør dette en betydelig gruppe med eldre mennesker. Disse skal ha helt andre tjenester i kommunen enn friske flyktninger i arbeidsdyktig alder. Dette var ikke kommunene rigget for, og mange har fortsatt store utfordringer.

        De over 55 år har ikke rett på et introduksjonsprogram. Dette er et program for å raskt komme ut i arbeid eller utdanning. Kommunene kan likevel tilby introduksjonsprogram, ved kapasitet. Det er derfor variasjon i tilbudet til denne gruppen fra kommune til kommune. 

        ##### Sykere enn nordmenn  
        
        Ifølge en rapport fra FHI er ukrainerne sykere enn nordmenn, med særlig dårlig tannhelse. (Se her for fullt intervju med FHI, og lenke til rapport)
        
        Ingen sitter med en oversikt over hvor mange ukrainere som har mottatt behandling via primær- eller spesialisthelsetjenesten, men dette er noe FHI jobber med. Det kan være utfordrende for kommunen å ikke kjenne til helsehistorikken til flyktningene de skal bosette. 

        Overlege ved OUS, xx, forteller at de har evakuert over 350 pasienter fra ukrainske sykehus siden krigen startet. Han sier tallet på ukrainere som har vært innom sykehus i Norge trolig er ti ganger så høyt, og at mange har kreft. (Se her for fullt intervju med sitater)

        Vi har snakket med flyktningtjenesten i xx kommuner. De trekker frem helsetjenesten som en av de største utfordringene i kommunen. Eldreomsorgen og helsetjenesten var presset fra før. I tillegg til ukrainerne som er bosatt, har kommunen også ansvar for helsetjenesten til asylsøkerne som sitter på mottak. (Se oversikt over hvem vi har hatt bakgrunnsamtaler med)

        ##### Midlertidighet fører til usikkerhet
        
        Siden ingen vet om ukrainerne skal være her i tre måneder, tre år eller resten av livet, er det mange kommuner som ikke tør å oppskalere tjenestetilbudet, spesielt innenfor helse, skole, barnehage og NAV. Å ansette sykepleiere og lærere i faste stillinger er risikabelt. De vil tape penger når ukrainerne må dra og de slutter å få tilskudd fra Imdi. 
        
        Noen kommuner sier de skal ri av seg stormen, andre prøver å kjøpe private tjenester som de kan de nedskalere fort. 

        """.format(
            munn_count = str(len(oppsummert_year[oppsummert_year['ukrainere'] > 0]))
        )
        
        st.markdown(
            national_text
        )

    with national_col2:
        with st.expander("Faktaboks"):
            
            st.markdown(
                """
                Ukrainere som kommer til Norge blir gitt kollektiv beskyttelse,  de trenger ingen individuell vurdering eller intervju. Oppholdstillatelsen gir ikke permanent opphold, men for ett år. Tillatelsen kan fornyes dersom situasjonen i Ukraina vedvarer.
    
                Tre steg frem mot bosetting:  
                * Registrering på Råde mottakssenter.  
                * Plassering på mottak. Per 01.02.24 er ventetiden på mottak omtrent 100 dager.
                * Bosetting i kommune - her blir de enten plassert tilfeldig, eller de kan selv søke seg til en kommune hvor de har familie/venner de skal bo sammen med - da er det opp til kommunen om de har kapasitet til å bosette. 
                
                <img src="https://www.imdi.no/globalassets/illustrasjoner/bosettingsprosess---infografikk/bosetting_mottaksbeboere_web_forenklet.jpg" width="100%"><br>
                
                Kommunen mottar automatisk integreringstilskudd. Satsene under er for det første året.  
                * Enslig voksen: 241,100 kroner
                * Voksen i familie: 194,400
                * Tilskudd for enslige mindreåriget: 187,000
                    * blir utbetalt til kommuner som bosetter enslige mindreåriget flyktninger under 18 år. 
                
                
                Engangstilskudd første år:
                * Eldretilskudd: 180,600 kroner 
                    * Utbetalt for personer som har fylt 60 år ved bosetting
                * Barnetilskudd: 27,800
                    * Utbetalt for barn mellom 0 og fem år. Inkluderer også barn som er født inntil seks måneder etter at mor er bosatt i en kommune. 
                
                Tilskudd til opplæring i norsk for voksne personer med kollektiv beskyttelse. Kommunene som har 150 personer eller færre i målgruppen, får også et grunntilskudd.
                * Personstilskudd § 37 d år 1 (2024): 48,400 kroner
                
                Tilskudd for bosetting av personer med nedsatt funksjonsevne og/eller atferdsvansker. 
                Tilskudd 1 er et engangstilskudd og kan tildeles i enten første eller andre bosettingsår. Tilskudd 2 kan tildeles årlig i integreringstilskuddsperioden, det vil si i maksimalt 5 år. 
                * Tilskudd 1: 196,400
                * Tilskudd 2: 1,608,000
                
                Tilskuddet skal dekke de gjennomsnittlige utgiftene kommunen har i bosettingsåret. Kommunen får tilskudd for hver person de bosetter. Tilskuddet skal blant annet dekke innvandrer- og flyktningskontortjenester, bolig, introduksjonsprogram,
                sysselsettingstiltak, yrkeskvalifisering og arbeidstrening, sosialkontor/sosialtjenester, barne- og ungdomsverntenester, tolketjenester, barnehagetjenester, integreringstiltak i grunnskolen, kultur- og ungdomstiltak, 
                utgifter til kommunehelsetjenesten, omsorg for personer med rusproblem.
                
                Det første året blir hele integreringstilskuddet utbetalt når personen er bosatt i kommunen. Påfølgende utbetalinger (år 2-5) blir utbetalt fire ganger i året. 
                
                Dersom en flyktning flytter til en annen kommune, må vedkommende melde endring til folkeregisteret innen åtte dager etter flytting. Tilskuddet i flytteåret blir fordelt mellom de to kommunene. 
                Fraflyttingskommunen mottar tilskuddet inneværende og påfølgende måned.
                """,
                unsafe_allow_html=True
            )


# Tab 2: Statistical description of the municipality
with tab2:

    summarized = """
    
    I {year} ble det bosatt {sum_total_ukr_year} ukrainere i kommunen, og det utgjorde {ukr_pct_pop_year:.1f} prosent av befolkningen.  

    Siden krigen i Ukraina startet, er det bosatt {sum_total_ukr:,.0f} ukrainere i  {kommune}. Det utgjør {ukr_pct_pop:.1f} prosent av befolkningen, 
    og {ukr_pct_ovr:.1f} av alle bosatte flyktninger i samme periode. 
    
    I en rangering over hvilke kommuner som tar i mot mest ukrainere etter befolkningsstørrelse i {year}, rangeres {kommune} på {fylke_rank:.0f}. plass i fylket og {national_rank:.0f}. plass i hele landet. 
    
    Integrerings- og mangfoldsdirektoratet har anmodet kommunen å bosette {innvandr_anmodet:,.0f} ukrainske flyktninger i  2024. Kommunen {innvandr_vedtak_string}. {kommune} {ema_vedtak_2024_string}

    """.format(
                kommune = kommuner.get(select_kommune), 
                year = select_year, 
                sum_total_ukr = oppsummert_komm['ukrainere'].sum(),
                sum_total_ukr_year = oppsummert_komm_year['ukrainere'].sum(),  
                ukr_pct_pop_year = oppsummert_komm_year['ukr_pct_pop'].sum(),  
                #sum_total_pop = oppsummert_komm['pop'].sum(),
                ukr_pct_pop = (oppsummert_komm['ukrainere'].sum()/oppsummert_komm_year['pop'].sum())*100,
                ukr_pct_ovr = (oppsummert_komm['ukrainere'].sum()/oppsummert_komm['innvandr'].sum())*100,
                fylke_rank = oppsummert_komm_year['fylke_rank'].sum(),
                national_rank = oppsummert_komm_year['national_rank'].sum(),
                innvandr_anmodet = anmodninger['innvandr_anmodet'].iloc[0],
                innvandr_vedtak_string = anmodninger['innvandr_vedtak_string'].iloc[0],
                ema_vedtak_2024_string = anmodninger['ema_vedtak_2024_string'].iloc[0],
                
                )
    
    st.markdown(summarized)
    
    
    if ukr_mottak_bool:
        st.markdown(ukr_mottak_string)
        
    fastlege = """
    ##### Fastlegekapasitet i {kommune} per 2022
        
    I henhold til tall fra SSB, har kommunen {lege_category} når det gjelder fastlegekapasitet.
    
    I {kommune} var det {legeliste_n:,.0f} personer på venteliste i 2022. Det utgjør {legeliste_pct:.1f} prosent av alle som står på fastlegeliste. 

    
    """.format(
        kommune = kommuner.get(select_kommune), 
        legeliste_n = oppsummert_komm_year['legeliste_n'].sum(),
        legeliste_pct = oppsummert_komm_year['legeliste_pct'].sum(),
        lege_category = oppsummert_komm_year['lege_category'].iloc[0]
    )
    
    st.markdown(fastlege)

# Tab 3: Suggestions for how the local journalists can proceed
with tab3:
    st.markdown("""
    #### Dette kan du gjøre i din kommune
    
    Flyktninger fra Ukraina er betydelig flere, eldre og sykere enn flyktninger norske kommuner har bosatt tidligere. 
    Forventningen var at de skulle gli inn i samfunnet. De skulle være som arbeidsinnvandrere som hoppet ut i jobb. 
    Erfaringene viser at det har vært flere utfordringer. 
    
    Situasjonsforståelsen vil variere fra kommune til kommune. Noen håndterer det godt, andre opplever situasjonen som utfordrende. 
    
    * Ta kontakt med flyktningkontoret:  
        * Hvordan vedtar kommunen hvor mange flyktninger de skal ta i mot? Hvilke vurderinger blir gjort.  
        * Hvordan har kommunen organisert seg for å ta i mot flyktningene?  
            * Midlertidighet - ukrainere har ikke permanent opphold
            * Tilgang på ressurser (sykepleiere, leger, lærere, mm)  
        * Hva er deres erfaring med å ta imot ukrainske flyktninger?  
            * Hvilke utfordringer møter dere?  
            * Har dere gladhistorier som viser hvordan det har fungert å ta imot ukrainske flyktninger?  
        * Hvordan har det vært å få de i jobb?  
            * Samarbeid med næringsliv  
        * Sykdom og pleie
            * Hvor mange er på sykehjem?  
            * Hvor mange får hjemmesykepleie?  
            * Hvor mange får oppfølging innen spesialisthelsetjenesten?  
        * Hvilket tilbud for de over 55 år?  
        * Hva betyr andelen barn og unge for barnehagene og skolene? 

    * Ta kontakt med kommuneoverlegen:  
        * Hvordan er fastlegesituasjonen i kommunen, og hvordan påvirkes den av ukrainske flyktninger?  
        * FHI sin rapport sier at ukrainere er sykere enn nordmenn. Hva er inntrykket til kommuneoverlegen? Hvordan ser sykdomsbildet ut?  
        * Har dere tall på ukrainere som har benyttet seg av primær - og spesialisthelsetjenesten?  
        * Hvordan vil den ukrainske flyktningbølgen påvirke kommunen fremover?  
    
    * Andre mulige kilder:  
        * Sykepleiere som jobber på sykehjem med ukrainske flyktninger.  
        * Lærer på introduksjonsprogram.  
        * Rektor på skole der de har ukrainske elever.  
        * Asylmottak i de kommunene som har.  

    """)

# Tab 4: Source data for the municipality
with tab4: 
    
    st.markdown("""
    ##### Om tallene
    Befolkningstall er hentet fra[ SSB-tabell 07459](https://www.ssb.no/statbank/table/07459).
    
    Fakta om venteliste hos fastlege og reservekapasitet er hentet fra [SSB-tabell 12005](https://www.ssb.no/statbank/table/12005). Merk: 2022 er siste publiserte tall fra SSB. SSB publiserer foreløpige 2023-tall 15. mars.
    
    Flyktningtall er hentet fra Integrerings- og mangfolksdirektaret (IMDi).
                
    ###### Anonymisering 
    Hvis det står *<5* i en eller flere celler, betyr det at antall bosatte flyktninger er mindre enn fem. IMDi tilbakeholder eksakt antall for å unngå identifisering. 
    Summeringer tar ikke hensyn til anonymisering. Summeringer må derfor sees på som et minimum antall bosatte flyktninger, hvis det står <5 i en eller flere celler. 
    """)


    tablecol1, tablecol2 = st.columns([4, 5])
    tablecol3, tablecol4 = st.columns([4, 5])
    tablecol5, tablecol6 = st.columns([4, 5])
    tablecol7, tablecol8 = st.columns([4, 5])

    pop_text = """
            ##### Befolkningen i  {kommune}
            Tabellen viser befolkningen i kommunen, etter kjønn og alder. 
            I {year:.0f} bodde det {sum_year:,.0f} personer i {kommune}. 
            
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
            Tabellen viser antall bosatte ukrainske flyktninger i {kommune}. 
            I {year:.0f} ble det bosatt {sum_year:.0f} ukrainske flyktninger. 
            
            {prikking}
            
            I hele perioden har kommunen bosatt {sum_total:.0f} ukrainske flyktninger.
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
            ##### Bosatte enslige mindreårige (EMA) fra Ukraina
            I {year:.0f} bosatte {kommune} {sum_year:.0f} EMA. I hele perioden (2022 til så langt i 2024) har kommunen bosatt {sum_total:.0f} EMA.
                    
            Merk at antall EMA ikke kan plusses på antall bosatte ukrainske flyktninger i tabellen over. Tabellen over medregner EMA. 
            
            Les mer om EMA [her](https://www.imdi.no/planlegging-og-bosetting/slik-bosettes-flyktninger/enslige-mindrearige-flyktninger/).
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

# Tab 5: Expert interviews
with tab5:
    fhi_string = """
    Intervju med FHI. 
    """
    
    with st.expander('Intervju med Folkehelseinstituttet'):
        st.markdown(fhi_string)
    
    nibr_string = """
    Hvem er ukrainerne som kommer? 
    * Tilstrømningen er veldig forskjellig fra 2015. Da var det en klar overvekt av menn som kom. Med ukrainerne var det i starten en stor overvekt kvinner, men etter de første månedene har andelen menn og kvinner vært mer lik, og holdt seg stabil.  
    * I stor grad har ukrainerne høy utdannelse. 75 prosent har høyere utdannelse. Men her ser vi litt utvikling over tid. Større andel av de som kom i den første fasen hadde høyere utdannelse enn dem som har kommet i senere tid. Det samme gjelder engelskkunnskapene.  
    * **Dette er vanlig dynamikk. At de som kommer i første fase ofte er ressurssterke, mens etter hvert så kommer det mindre ressurssterke.**  
    
    En stor andel av de ukrainske flyktningene er eldre. Hvilke utfordringer byr dette på?
    * 5 prosent av de som kommer er over 66 år. Dette er mye høyere enn tidligere år når tallet har lagt på 1-2 prosent. Men de prosentene høres jo ikke så mye ut. Det viktige er at det totale antallet er utrolig mye høyere enn tidligere, og integreringsapparatet trenger helt annen kompetanse og et helt annet tilbud enn man har for folk i arbeidsdyktig alder som skal ut i et introduksjonsprogram.  
    * Det er en stor omveltning å skulle ta imot en så stor andel med eldre flyktninger.  Det trengs andre tjenester enn det man har vært vant til tidligere.  
    
    Hvordan har dette vært for kommunene?
    * Generelt har kommunene press på eldreomsorg og helsetjenester, og når det over natten kommer veldig mange flere, så blir det naturlig nok enda større press.  
    * Flyktningtjenesten og introduksjonsprogrammet er ikke de eneste som skal ta imot flyktninger. Hele kommunen bosetter med hele tjenesteapparatet. Å skulle oppskalere alle tjenester er krevende.  
    * Veldig mange har 2015 i tankene. De husker at de oppskalerte, men så stoppet det å komme folk. Da taper kommunene penger, for de slutter å få tilskudd for personer. Veldig mange kommuner har akkurat rukket å nedskalere etter 2015 når ukrainerne begynte å komme i 2022. 
    * Normalt når vi tar imot flyktninger, tar vi for gitt at de skal bli. Man tror ikke at de skal returnere. Men denne gruppen har bare midlertidig opphold.  
    * Å oppskalere tjenester innenfor skole, barnehage og helsetjenester er en veldig stor risiko for kommunene fordi ukrainere har midlertidig tillatelse.  Hadde kommunene visst at disse skulle bli i all overskuelig framtid kunne de ansatt mye leger, sykepleiere og lærere i faste stillinger fordi de hadde fått en større befolkning. Men siden man ikke vet om de skal være her i tre måneder, tre år eller resten av livet, så er det mange kommuner som ikke tør å oppskalere. I tillegg er det mangel på folk til å fylle slike stillinger som sykepleiere, lærere, leger etc. 

    På hvilke tjenester er det størst press i kommunen? 
    * Helsevesenet og Nav er veldig presset. Lokalt NAV-personell sier at de ikke har kapasitet til å følge opp denne gruppen. De er rett og slett ikke nok ansatte til å følge opp en så stor økning av mennesker på kort tid.  
    * Mitt inntrykk har vært at skole og barnehage har gått bra hittil, mens helse er et generelt problem fra før av.  
    
    Hvordan løser kommunene dette?  
    * Det er veldig forskjellig hvordan kommunene løser det. Noen har unntak for midlertidige stillinger, noen tenker at de skal ri av seg stormen og håper at det skal fungere, men tør ikke å ansette. Andre prøver å bruke private tjenester i større grad, da kan de eventuelt nedskalere fort. Men det er et helt reelt dilemma som kommunene uttrykker veldig sterkt, at det er krevende. 

    Har bosettingen av ukrainere vært forskjellig fra bosetting av andre flyktninger?
    
    * Det har kanskje vært flere likhetstrekk enn forskjeller i arbeidet med å ta imot ukrainere og andre flyktninger. Det var nok nokså urealistiske forventinger om i starten at dette skulle være helt annerledes.  
    * Ukrainerne skulle bare gli inn, dette skulle bare være som arbeidsinnvandrere som skulle hoppe ut i jobb, helt problemfritt. Det har vist seg at denne gruppen også trenger støtte og hjelp for å komme seg ut i jobb og arbeid. Selv om de har høy utdanning får de ikke nødvendigvis brukt det i Norge når de ikke kan engelsk, og ikke norsk.
    * Ukrainere har generelt ikke gode engelskkunnskaper. Det er en myte som må avkreftes gang på gang, på gang.  
    * Kun 11 prosent snakker flytende engelsk, og rundt 60 prosent kan nesten ikke engelsk i det hele tatt. Av de som kommer nå, er det en enda lavere andel som snakker engelsk.  
    
    Så det har ikke vært enklere å få en ukrainer ut i jobb enn øvrige flyktninger? 
    * Ukrainere som har gått introduksjonstilbudet har cirka samme resultater som andre flyktninggrupper har hatt når det kommer til å komme seg ut i arbeid.  
    * Når du ikke kan språket og har et annet alfabet så er det ikke nødvendigvis enkelt å få dem ut i jobb. Det er en helt urealistisk forventning.  
    * I vår rapport finner vi at flere arbeidsgivere i utgangspunktet var mer positivt innstilt til å ansette ukrainske flyktninger enn øvrige flyktninger da krigen startet, men at de på en annen side sier at den midlertidig tillatelse gjør at de er mer skeptiske til å ansette dem. Det å ansette noen, og lære dem opp, tar tid og koster penger.  
    * Det er en stor vilje for å lære seg norsk og komme ut i arbeidslivet, men det er veldig mange som møter på utfordringer. Språk trekkes frem som den største barrieren.
    
    Hvilke tilbud gir kommunene til de over 55 år?
    
    * Det er veldig forskjellig om kommunen tilbyr norskopplæring og introduksjonsprogram til denne gruppen. Det handler om kapasitet. Små kommuner tilbyr i større grad. Det handler nok om at når de først har opprettet en klasse, kan de like gjerne fylle den opp. I større kommuner er det færre som tilbyr norskopplæring til denne gruppen som de ikke har plikt til å tilby.  
    * Halvparten av kommunene opplyser at de ukrainske flyktningene har fått mindre norskundervisning og introduksjonsprogram enn hva de har hatt rett til. De har ikke hatt klasserom, de har ikke hatt nok lærere, de har ikke hatt mulighet til å oppskalere så raskt som behovet var.  
    * Mange påpeker at dette er en gruppe vi ikke har vært vant til å ha en så høy andel av. Dette er en gruppe som blir litt glemt med at man ikke har så mye tilbud.  
    * En del av de frivillige organisasjonene sier at de eldre er glemt, det er ikke noe tilbud for dem.
    
    Hva vet dere om helsesituasjonen til de som kommer? 
    * Ukrainerne gir helsetjenesten mye dårligere score enn for eksempel skole og barnehage.  
    * Det er en kulturkræsj på hva man er vant til i helsevesenet.  
    * I Ukraina er de mye mer vant til å bli sendt til en spesialist direkte, de har ingen fastlegeordning. Det er også mye mer vanlig å få utskrevet medisiner for ting vi her i Norge er mer restriktive på.  
    * Det var noen som ble sjokkert da de ble bedt om å drikke Cola fordi de hadde feber og vondt i magen. De ville ha medisin.  


    """
    
    with st.expander('Intervju med Vilde Hernes, forsker ved NIBR.'):
        st.markdown(nibr_string)
    
    ous_string = """
    Intervju med OUS. 
    """
    
    with st.expander('Intervju med Oslo universitetssykehus'):
        st.markdown(ous_string)
