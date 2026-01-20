# CINE-BOT: Ricerca Semantica e Raccomandazioni Film con Qdrant

Questo repository mostra un esempio pratico di motore di raccomandazione per film basato su embedding testuali:

- Database vettoriale persistente con Qdrant (cartella `qdrant_db`)
- Generazione di embedding con Sentence Transformers (modello `paraphrase-multilingual-mpnet-base-v2`, dimensione 768)
- Interfaccia CLI che suggerisce film simili a quello indicato dall’utente

**In breve:** al primo avvio indicizziamo i film da [film_data.json](film_data.json), salviamo i vettori in Qdrant, poi chiediamo all’utente un titolo che gli è piaciuto; prendiamo la trama di quel titolo, creiamo l’embedding e cerchiamo in Qdrant i film più simili (escludendo il titolo stesso) mostrando i primi 3 con punteggio di somiglianza.

## Cosa fa il codice

- Indicizza i film da [film_data.json](film_data.json) in una collezione Qdrant chiamata `film_persistenti`.
- Usa Sentence Transformers (`paraphrase-multilingual-mpnet-base-v2`) per creare embedding di dimensione 768 delle trame.
- Salva i vettori e i metadati in Qdrant su disco nella cartella `qdrant_db`.
- Fornisce una CLI che chiede un titolo e restituisce fino a 3 film consigliati simili per trama, filtrando il titolo indicato per non riproporlo.

## Come funziona (flusso)

1. Avvio: se la collezione non esiste, viene creata e popolata con i film del file JSON.
2. Persistenza: Qdrant scrive su `./qdrant_db` per riutilizzare i dati agli avvii successivi.
3. Raccomandazioni: l’utente inserisce un titolo; si recupera la trama corrispondente, si genera l’embedding e si effettua una `query_points` con filtro `must_not` sul campo `titolo` per escludere il film stesso.

## Requisiti

- Python 3.8+
- sentence-transformers
- qdrant-client

Installazione rapida:

```bash
pip install sentence-transformers qdrant-client
```

## Avvio

```bash
# con Python
python main.py

# oppure con uv (se disponibile)
uv run main.py
```

## Struttura del progetto

- [main.py](main.py): logica principale (indicizzazione, CLI, query a Qdrant)
- [film_data.json](film_data.json): elenco film e metadati (titolo, genere, anno, trama)
- [README.md](README.md): questo documento
- pyproject.toml (se presente): gestione del progetto/ambiente

## Operazioni comuni

- Aggiungere film: modifica [film_data.json](film_data.json) e riavvia. Se la collezione esiste già, elimina la cartella `qdrant_db` per ricrearla da zero.
- Cambiare modello: aggiorna il nome del modello in [main.py](main.py) (variabile `nome_modello`) e crea la collezione con la dimensione corretta.
- Eseguire in RAM: usa `QdrantClient(":memory:")` invece di `path="./qdrant_db"` per test effimeri.

## Esempio di utilizzo (CLI)

```
Scrivi il titolo di un film che ti è piaciuto > Matrix
   🎬 Poiché ti è piaciuto 'Matrix', ti consiglio:
   -> Blade Runner (Score: 0.71)
   -> Star Wars (Score: 0.63)
   -> Il Padrino (Scartato - Troppo diverso, Score: 0.21)
```

## Note

- Il primo avvio scarica il modello (~1GB). Gli avvii successivi riutilizzano i dati salvati.
- I punteggi sono valori di somiglianza (più alti = più simili).
- Per un reset completo, elimina la cartella `qdrant_db` e riavvia.

## Manuale: Logica di Raccomandazione

Questa sezione descrive nel dettaglio come funziona il codice che raccomanda i film, così puoi spiegarlo e dimostrarlo facilmente.

### Obiettivo

- Dato un film che ti è piaciuto (titolo), trovare 3 film con una trama semanticamente simile.
- Escludere dalla risposta il film stesso.

### Flusso dettagliato

1. Caricamento dati: si leggono i metadati dei film da [film_data.json](film_data.json) tramite `load_film_data()`.
2. Inizializzazione Qdrant: si crea (se manca) la collezione `film_persistenti` con vettori di dimensione 768 e distanza `COSINE`.
3. Indicizzazione: per ogni voce del JSON si calcola l’embedding della `trama` e si inserisce un `PointStruct` con:
   - `id`: UUID univoco
   - `vector`: l’embedding (lista di 768 float)
   - `payload`: l’intero oggetto film (titolo, genere, anno, trama)
4. Predisposizione modello: si assicura che l’`encoder` (`paraphrase-multilingual-mpnet-base-v2`) sia caricato per le query.
5. Input utente: l’utente inserisce un `titolo`. Si recupera la `trama` corrispondente (funzione `trova_trama_da_titolo`).
6. Query semantica: si calcola l’embedding della trama del titolo scelto e si invoca `client.query_points()` con:
   - `query`: embedding della trama
   - `query_filter`: filtro `must_not` sul campo `titolo` per escludere il film stesso
   - `limit`: 3 risultati
7. Presentazione: si mostrano i risultati ordinati per `score` (somiglianza). In esempio, si filtra a video con soglia 0.25.

### Schema dei dati (Qdrant)

- Collezione: `film_persistenti`
- `VectorParams`: `size=768`, `distance=COSINE`
- `payload` per ogni punto: `{titolo, genere, anno, trama}`
- `id`: UUID4 generato a runtime

### API principali usate

- Modello: `SentenceTransformer(nome_modello)` per calcolare gli embedding
- Indicizzazione: `client.upsert(collection_name, points=[PointStruct(...)])`
- Ricerca: `client.query_points(collection_name, query=embedding, query_filter=Filter(...), limit=3)`
- Filtro-esclusione: `Filter(must_not=[FieldCondition(key="titolo", match=MatchValue(value=titolo_input))])`

### Considerazioni su `score` e distanza

- Distanza `COSINE`: la somiglianza è maggiore quanto più i vettori puntano nella stessa direzione.
- `score` più alto ⇒ maggiore somiglianza tematica. La soglia (ad es. 0.25) è regolabile.

### Persistenza e reset

- Qdrant salva i dati su disco in `./qdrant_db`. Se la collezione esiste, non si ricalcolano gli embedding.
- Per ricostruire da zero: elimina `qdrant_db` e rilancia l’app.

### Estensioni possibili

- Aggiungere filtri (es. `genere`) direttamente in `query_filter` con `must`.
- Cambiare modello e adeguare la dimensione del vettore (`size`).
- Integrare una query testuale libera (embedding della frase inserita dall’utente) oltre al titolo.
- Arricchire `payload` con altri campi (regista, cast, durata) per filtri più ricchi.

### Pseudocodice riassuntivo

```
film_list = load_film_data()
if collection not exists:
   encoder = load_model()
   create_collection(size=768, distance=COSINE)
   upsert(embedding(trama) + payload)
else:
   encoder = load_model()

title = input()
trama = trova_trama_da_titolo(title, film_list)
emb = encoder.encode(trama)
filter = must_not(titolo == title)
hits = query_points(query=emb, filter=filter, limit=3)
print(hits by score)
```

### Troubleshooting

- Primo avvio lento: il modello scarica ~1GB; attende il completamento.
- Nessun risultato: verifica che il titolo esatto esista in [film_data.json](film_data.json).
- Errore dimensione vettore: se cambi modello, aggiorna `size` in `VectorParams`.

## Talking Points (per colloqui/demo)

- Ho costruito un piccolo motore di raccomandazione basato su embedding testuali usando Sentence Transformers e Qdrant.
- I dati dei film sono separati in `film_data.json`, li indicizzo con vettori da 768 dimensioni (MPNet multilingua) e li salvo in `qdrant_db`.
- La raccomandazione parte da un titolo inserito: prendo la trama, genero l’embedding e cerco i “vicini” in Qdrant con `query_points`.
- Escludo il film stesso con un filtro `must_not` sul campo `titolo`, poi mostro i 3 risultati più simili per `score`.
- Il progetto dimostra persistenza, filtro sui payload e best practice nel separare dati, modello e storage.
