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
ukr_mottak = load_data('ukrainere_mottak_310124')
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
    'Velg kommune (2024)',
    options = sorted(list({k for (k, v) in unike_kommuner.items() if k[:2] ==  select_fylke})),
    format_func = lambda x: unike_kommuner.get(x)
)

if select_kommune == '1508' or select_kommune == '1580':
        st.sidebar.markdown("""
        Merk: Ålesund ble delt i Ålesund og Haram kommuner 01.01.2024. Tallene for 2022 og 2023 er forbundet med 1507-Ålesund.
        """)

select_year = st.sidebar.selectbox(
    'Velg år',
    options = [2022, 2023, 2024]
)

#FILTER DATA FRAME BASED ON SELECTORS

flyktninger_fylke = flyktninger[flyktninger['Fylkenummer'].isin([select_fylke])] 

flyktninger_komm = flyktninger[flyktninger['Kommunenummer'].isin([select_kommune])] 
flyktninger_komm_year = flyktninger_komm[flyktninger_komm['År'] == select_year] 
flyktninger_cols = ['Kommune', 'År', 'Kjønn', 'Aldersgruppe', 'ukrainere', 'ukr_pct', 'ukr_prikket', 'ovrige', 'ovr_pct', 'ovr_prikket', 'pop', 'pop_pct']

ema_komm = ema[ema['Kommunenummer'].isin([select_kommune])]
ema_komm_year = ema_komm[ema_komm['År'] == select_year] 

oppsummert_komm = oppsummert[oppsummert['Kommunenummer'].isin([select_kommune])]
oppsummert_komm_year = oppsummert_komm[oppsummert_komm['År'] == select_year] 
oppsummert_year = oppsummert[oppsummert['År'] == 2023] 

anmodninger = oppsummert[oppsummert['Kommunenummer'].isin([select_kommune])]
anmodninger = anmodninger[anmodninger['År'] == 2024] 
anmodninger = anmodninger[['Kommune', 'Kommunenummer', 'ema_anmodet_2024', 'ema_vedtak_2024', 'innvandr_anmodet', 'innvandr_vedtak', 'innvandr_vedtak_string', 'innvandr_bosatt', 'ukr_bosatt',  'innvandr_avtalt_bosatt', 'ukr_avtalt_bosatt']]

ukr_mottak_komm = ukr_mottak[ukr_mottak['Kommunenummer'].isin([select_kommune])]
ukr_mottak_komm = ukr_mottak_komm[['mottak_navn', 'ukr_mottak']]


ukr_mottak_bool = False
ukr_mottak_string = 'Per 31.01.2024 bor det også ukrainere på asylmottak i kommunen. Disse har kommunen også ansvar for mens de venter på å bli bosatt.\n'
for mottak, ukr in ukr_mottak_komm.itertuples(index=False):
    ukr_mottak_bool = True
    ukr_mottak_string += '* ' + mottak + ': ' + str(ukr) + ' ukrainere  \n'


with st.sidebar:
    
    toplist = """
    ### Lag toppliste for {year}
    """.format(year = select_year)
    st.markdown(toplist)

    select_group = st.selectbox(
        'Velg gruppering',
        options=[unike_fylker.get(select_fylke), 'Norge', 'Lokalavis', 'SSBs sentralitetsindeks']
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

    if select_group == unike_fylker.get(select_fylke):
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
        
    if select_group == 'SSBs sentralitetsindeks':
        oppsummert_sidebar = oppsummert[oppsummert['sentralitet'] == int(select_centrality[:1])]
        oppsummert_sidebar = oppsummert_sidebar[oppsummert_sidebar['År'] == select_year]
        #oppsummert_sidebar = oppsummert_sidebar[oppsummert_sidebar['Fylkenummer'] == select_fylke]
        oppsummert_sidebar = oppsummert_sidebar.sort_values('ukr_pct_pop', ascending = False)
        oppsummert_sidebar = oppsummert_sidebar[['Kommune', 'ukrainere', 'ukr_pct_pop']]
        
        st.sidebar.markdown("""
        Sentralitetsindeksen er en måte å måle hvor sentral en kommune er med grunnlag i befolkning, arbeidsplasser og servicetilbud. Indeksen er utviklet av SSB.
        
        Mest sentrale kommuner er Oslo og omkringliggende kommuner. Større byer som Bergen, Trondheim  og Tromsø har verdien 2. De minst sentrale kommunene i Norge, er blant annet Eidfjord, Frøya, Folldal, Gratangen, mfl.        
        """)

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


use_container_width = False #st.checkbox("Full tabellbredde", value=True)


# PAGE CONTENT




underdev_col1, underdev_col2 = st.columns([5, 4])
national_col1, national_col2 = st.columns([5, 4])
munn_col1, munn_col2 = st.columns([5, 4])
recipe_col1, recipe_col2 = st.columns([5, 4])

with underdev_col1:
    pass    
    st.markdown(
        """
        #### Under utvikling
        <p style='color:red;font-weight:bold;'>Sperrefrist: 22. april 2024.</p>
        <p style='color:red;font-weight:bold;'>Applikasjonen er under utvikling. Bruk den for å gjøre case-research, og for å bli kjent tallgrunnlaget. Mindre feil kan forekomme.</p>
        """,
        unsafe_allow_html=True
    )
    
with underdev_col2:
    pass


with national_col1:
    national_text = """
    #### Dette er saken
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
    
    #with st.expander("Kilder"):
    #    st.markdown("""
    #    Kilder:  
    #    * [Regjeringen, 08.01.2024](https://www.regjeringen.no/no/aktuelt/rekordmange-flykninger-bosatt-i-2023/id3021169/) - hentet 27.02.2024
    #    * [OsloMet, 17.04.2023](https://www.oslomet.no/om/nyheter/undersoker-ukraineres-liv-norge) - hentet 27.02.2024
    #    """)

with national_col2:
    with st.expander("Faktaboks"):
        
        st.markdown(
            """
            Ukrainere som kommer til Norge blir gitt kollektiv beskyttelse,  de trenger ingen individuell vurdering eller intervju. Oppholdstillatelsen gir ikke permanent opphold, men for ett år. Tillatelsen kan fornyes dersom situasjonen i Ukraina vedvarer.
 
            Tre steg frem mot bosetting:  
            * Registrering på Råde mottakssenter.  
            * Plassering på mottak. Her venter de i snitt xxx måneder.
            * Bosetting i kommune - her blir de enten plassert tilfeldig, eller de kan selv søke seg til en kommune hvor de har familie/venner de skal bo sammen med - da er det opp til kommunen om de har kapasitet til å bosette. 
            
            Tilskudd til kommunen: 
 
            Introduksjonsstønad: 
            Enslig mindreårig asylsøker: 
            Tilskudd for eldre:
            Tilskudd for flyktninger med funksjonsnedsetting:
            
            <img src="https://www.imdi.no/globalassets/illustrasjoner/bosettingsprosess---infografikk/bosetting_mottaksbeboere_web_forenklet.jpg" width="100%">
            
            """,
            unsafe_allow_html=True
        )


with munn_col1:

    summarized = """
    #### Slik er det i {kommune}
    
    I {year} ble det bosatt {sum_total_ukr_year} ukrainere i kommunen. I {year} utgjorde det {ukr_pct_pop_year:.1f} prosent av befolkningen.  

    Fra 2022 til starten av 2024 har {kommune} bosatt {sum_total_ukr:,.0f} ukrainske flyktninger. Det utgjør {ukr_pct_pop:.1f} prosent av befolkningen i kommunen, 
    og {ukr_pct_ovr:.1f} prosent av alle flyktninger bosatt i kommunen i samme periode. 
    
    I en rangering over hvilke kommuner som tar i mot mest ukrainere etter befolkningsstørrelse i {year}, rangeres {kommune} på {fylke_rank:.0f}. plass i fylket og {national_rank:.0f}. plass i hele landet. 
    
    I 2024 er {kommune} anmodet av Integrerings- og mangfoldsdirektoratet (IMDi) å bosette {innvandr_anmodet:,.0f} flyktninger. Kommunen {innvandr_vedtak_string} i 2024.

    """.format(
                kommune = unike_kommuner.get(select_kommune), 
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
                innvandr_vedtak_string = anmodninger['innvandr_vedtak_string'].iloc[0]
                )
    
    st.markdown(summarized)
    
    
    if ukr_mottak_bool:
        st.markdown(ukr_mottak_string)
        
    fastlege = """
    ##### Fastlegekapasitet i {kommune} per 2022
    
    Merk: 2022 er siste publiserte tall fra SSB. SSB publiserer foreløpige 2023-tall 15. mars.
    
    I {kommune} var det {legeliste_n:,.0f} personer på venteliste i 2022. Det utgjør {legeliste_pct:.1f} prosent av antall pasienter på fastlegeliste totalt (les mer om indikatoren hos [SSB](https://www.ssb.no/kompis/statbank/?id=a1b62e7f-aaf5-4db5-9e46-ef70a93c695f&ver=75680&val=KOSandelpasiente0000&lang=no)). 
    Tallene er hentet fra [SSBs tabell 12005](https://www.ssb.no/statbank/table/12005).
    
    Ved å samtidig se på personer på ventelise og SSBs mål på [reservekapasitet](https://www.ssb.no/kompis/statbank/?id=a1b62e7f-aaf5-4db5-9e46-ef70a93c695f&ver=75680&val=KOSreservekapasi0000&lang=no) blant fastlegene, har kommunen {lege_category} når det gjelder fastlegekapasitet.
    """.format(
        kommune = unike_kommuner.get(select_kommune), 
        legeliste_n = oppsummert_komm_year['legeliste_n'].sum(),
        legeliste_pct = oppsummert_komm_year['legeliste_pct'].sum(),
        lege_category = oppsummert_komm_year['lege_category'].iloc[0]
    )
    
    st.markdown(fastlege)

with recipe_col1:
    st.markdown("""
    #### Dette kan du gjøre i din kommune
    
    Flyktninger fra Ukraina er betydelig flere, aldre og sykere enn flyktninger norske kommuner har bosatt tidligere. Forventningen var at de skulle gli inn i samfunnet. De skulle være som arbeidsinnvandrere som hoppet ut i jobb. Erfaringene viser at det har vært flere utfordringer. 
    
    * Ta kontakt med flyktningkontoret:  
        * Hva er deres erfaring med å ta imot ukrainske flyktninger?  
        * Hvilke utfordringer møter dere?  
        * Hvordan har det vært å få de i jobb?  
        * Hvor mange er på sykehjem?  
        * Hvor mange får hjemmesykepleie?  
        * Hvor mange får oppfølging innen spesialisthelsetjenesten?  
        * Hvilket tilbud for de over 55 år?  
        * Har dere gladhistorier som viser hvordan dette har fungert godt å ta imot ukrainske flyktninger?  
        * Hva betyr andelen barn og unge for barnehagene og skolene?  
        * Hvordan vedtar kommunen hvor mange flyktninger de skal ta i mot? Hvilke vurderinger blir gjort.  
        * Hvordan har kommunen organisert seg for å ta i mot flyktningene?  
        
    * Ta kontakt med kommuneoverlegen:  
        * Hvordan er fastlegesituasjonen i kommunene?  
        * Hva betyr de ukrainske flyktningene for denne situasjonen?  
        * FHI sin rapport sier at ukrainere er sykere enn nordmenn. Hva er ditt inntrykk? Hvordan ser sykdomsbildet ut?  
        * Har dere tall på ukrainere som har benyttet seg av primær - og spesialisthelsetjenesten?  
        * Hvordan vil den ukrainske flyktningbølgen påvirke kommunen fremover?  
    
    * Andre mulige kilder:  
        * Sykepleiere som jobber på sykehjem med ukrainske flyktninger.  
        * Lærer på introduksjonsprogram.  
        * Rektor på skole der de har ukrainske elever.  
        * Asylmottak i de kommunene som har.  

    """)


with st.expander("Se tallgrunnlag"):

    st.markdown("""
    ##### Prikking 

    Hvis det står *Prikket (<5)*, betyr det at antallet er mindre enn fem. IMDi tilbakeholder eksakt antall av personvernhensyn. 
    Summeringer inkluderer bare oppgitte tall, og tar ikke hensyn til prikking. Summeringer må derfor sees på som et minimum antall bosatte flyktninger i kommunen. 
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
                kommune = unike_kommuner.get(select_kommune), 
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
            I hele perioden har kommunen bosatt {sum_total:.0f} ukrainske flyktninger.
            """.format(
                kommune = unike_kommuner.get(select_kommune), 
                year = select_year, 
                sum_year = flyktninger_komm_year['ukrainere'].sum(),  
                sum_total = flyktninger_komm['ukrainere'].sum()
                )

    with st.container():
        with tablecol3:
            st.markdown(ukr_text)
    
        with tablecol4:
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
                kommune = unike_kommuner.get(select_kommune), 
                year = select_year, 
                sum_year = flyktninger_komm_year['ovrige'].sum(),  
                sum_total = flyktninger_komm['ovrige'].sum()
                )
            


    with st.container():
        with tablecol7:
            
            st.markdown(ovr_text)
    
        with tablecol8:
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



