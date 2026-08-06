import os
import requests
from datetime import datetime
from supabase import create_client, Client
from groq import Groq

# ---------------------------------------------------------
# 1. LE TUE CREDENZIALI (Supporta GitHub Actions e Locale)
# ---------------------------------------------------------
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID", "77x4gb6at2mn13mrf2y0r011kkh2t8")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET", "is234sflairunj58nqtbg5w2r9tt1a")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")

SUPABASE_URL = "https://jxayyftyhkweruvjfsch.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "sb_publishable_n9M6xB7gVICsm4R9MavFrw_rxyeHsOZ")

# ---------------------------------------------------------
# 2. INIZIALIZZAZIONE CLIENTI
# ---------------------------------------------------------
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

# ---------------------------------------------------------
# 3. FUNZIONE PER OTTENERE TOKEN DA TWITCH
# ---------------------------------------------------------
def get_twitch_token():
    auth_url = "https://id.twitch.tv/oauth2/token"
    auth_params = {
        'client_id': TWITCH_CLIENT_ID,
        'client_secret': TWITCH_CLIENT_SECRET,
        'grant_type': 'client_credentials'
    }
    res = requests.post(auth_url, params=auth_params)
    return res.json()['access_token']

# ---------------------------------------------------------
# 4. FUNZIONE IA PER RIASSUMERE/TRADURRE CON GROQ
# ---------------------------------------------------------
def elabora_descrizione_ia(testo_originale):
    if not testo_originale:
        return "Nessuna descrizione disponibile."
    
    prompt = f"Traduci e riassumi la seguente descrizione di un videogioco in italiano in max 2 frasi accattivanti:\n\n{testo_originale}"
    
    chat_completion = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )
    return chat_completion.choices[0].message.content

# ---------------------------------------------------------
# 5. RECUPERO GIOCHI DA IGDB ED ESECUZIONE
# ---------------------------------------------------------
def recupera_e_salva_giochi():
    print("🚀 Script avviato correttamente!")
    
    print("Ottenimento token da Twitch...")
    access_token = get_twitch_token()
    
    headers = {
        'Client-ID': TWITCH_CLIENT_ID,
        'Authorization': f'Bearer {access_token}',
    }
    
    # Data di oggi in timestamp UNIX (inizio e fine giornata)
    oggi = datetime.now()
    timestamp_inizio = int(datetime(oggi.year, oggi.month, oggi.day, 0, 0, 0).timestamp())
    timestamp_fine = int(datetime(oggi.year, oggi.month, oggi.day, 23, 59, 59).timestamp())

    # Query IGDB: Piattaforme (167=PS5, 169=Xbox Series X, 130=Switch, 6=PC)
    query = f'''
    fields name, summary, platforms.name, cover.url, first_release_date;
    where release_dates.date >= {timestamp_inizio} & release_dates.date <= {timestamp_fine} & platforms = (167, 169, 130, 6);
    limit 50;
    '''

    print("Ricerca giochi in uscita oggi...")
    response = requests.post('https://api.igdb.com/v4/games', headers=headers, data=query)
    giochi = response.json()

    print(f"Trovati {len(giochi)} giochi in uscita oggi!")

    for gioco in giochi:
        titolo = gioco.get('name')
        summary = gioco.get('summary', '')
        
        # Estrai piattaforme
        piattaforme = ", ".join([p['name'] for p in gioco.get('platforms', [])])
        
        # Estrai URL Immagine (convertito ad alta risoluzione)
        immagine_url = ""
        if 'cover' in gioco:
            immagine_url = "https:" + gioco['cover']['url'].replace("t_thumb", "t_cover_big")
            
        print(f"Elaborazione IA per: {titolo}...")
        descrizione_italiano = elabora_descrizione_ia(summary)
        
        # Salva su Supabase
        dati_gioco = {
            "titolo": titolo,
            "piattaforme": piattaforme,
            "data_uscita": oggi.strftime('%Y-%m-%d'),
            "descrizione": descrizione_italiano,
            "immagine_url": immagine_url
        }
        
        supabase.table("giochi").insert(dati_gioco).execute()
        print(f"✅ Salvato con successo nel Database: {titolo}")

# Avvio diretto della funzione senza condizioni
recupera_e_salva_giochi()