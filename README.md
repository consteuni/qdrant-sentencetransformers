# CINE-BOT: Motore di Ricerca Semantica per Film con Qdrant e Sentence Transformers

Questo progetto Python dimostra come costruire un motore di ricerca semantica per film utilizzando:
- **Qdrant** come database vettoriale persistente
- **Sentence Transformers** per generare gli embedding delle trame

## Funzionalità
- Indicizzazione di una lista di film con metadati (titolo, genere, anno, trama)
- Salvataggio persistente dei dati su disco (`./qdrant_db`)
- Ricerca semantica: trova i film più simili a una descrizione testuale
- Filtro opzionale per genere (es: "animazione", "fantascienza", "drammatico")
- Interfaccia testuale interattiva

## Come funziona
1. **Primo avvio**: se il database non esiste, viene creato e popolato con alcuni film di esempio. Gli embedding delle trame sono calcolati con il modello `paraphrase-multilingual-mpnet-base-v2` (scarica circa 1GB al primo uso).
2. **Avvii successivi**: i dati e gli embedding vengono letti da disco, senza bisogno di ricalcolare tutto.
3. **Ricerca**: l'utente inserisce una descrizione (es: "spazio e astronavi") e può filtrare per genere. Il sistema restituisce i film più simili.

## Requisiti
- Python 3.8+
- [sentence-transformers](https://www.sbert.net/)
- [qdrant-client](https://qdrant.tech/)

Installa le dipendenze con:
```bash
pip install sentence-transformers qdrant-client
```

## Avvio
Esegui il bot con:
```bash
python main.py
```

## Esempio di utilizzo
```
Cosa vuoi vedere? > spazio e astronavi
Filtro genere (es. 'drammatico' o invio): fantascienza
   🎬 Star Wars (1977) - Score: 0.92
   🎬 Matrix (1999) - Score: 0.75
```

## Note
- I dati sono salvati nella cartella `qdrant_db`.
- Puoi aggiungere altri film modificando la lista `film_list` in `main.py`.
- Il filtro per genere è opzionale: premi invio per cercare su tutti i generi.
