from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import uuid
import os

def main():
    # --- 1. SETUP DEL CLIENT SU DISCO ---
    # Invece di ":memory:", diamo un percorso. 
    # Qdrant creerà una cartella "qdrant_db" nel tuo progetto e salverà tutto lì.
    print("📂 Connessione al database locale...")
    client = QdrantClient(path="./qdrant_db") 
    
    nome_collezione = "film_persistenti"
    nome_modello = 'paraphrase-multilingual-mpnet-base-v2'

    # --- 2. CONTROLLO ESISTENZA ---
    # Verifichiamo se la collezione esiste già su disco.
    if not client.collection_exists(collection_name=nome_collezione):
        print("⚠️ Collezione non trovata. Inizializzazione primo avvio...")
        
        # Carichiamo il modello SOLO se dobbiamo inserire dati
        print(f"📥 Caricamento modello AI: {nome_modello}...")
        encoder = SentenceTransformer(nome_modello)

        # Creiamo la collezione
        client.create_collection(
            collection_name=nome_collezione,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )

        # I dati
        film_list = [
            {"titolo": "Matrix", "genere": "fantascienza", "anno": 1999, "trama": "Un hacker scopre che il mondo è una simulazione virtuale gestita dalle macchine. Pillola rossa o pillola blu? Distopia tecnologica."},
            {"titolo": "Alla ricerca di Nemo", "genere": "animazione", "anno": 2003, "trama": "Un pesce pagliaccio sfida i pericoli del vasto mare aperto e dell'oceano per ritrovare suo figlio. Nuota attraverso l'acqua profonda incontrando squali."},
            {"titolo": "Star Wars", "genere": "fantascienza", "anno": 1977, "trama": "Guerre stellari ambientate in una galassia lontana. Astronavi combattono nello spazio profondo usando spade laser e la forza contro l'impero."},
            {"titolo": "Toy Story", "genere": "animazione", "anno": 1995, "trama": "I giocattoli prendono vita quando nessuno guarda. Un cowboy geloso cerca di liberarsi di uno spaceman tecnologico."},
            {"titolo": "Il Padrino", "genere": "drammatico", "anno": 1972, "trama": "La storia di una potente famiglia mafiosa italo-americana. Crimine organizzato, onore e tradimenti a New York."}
        ]

        print("🚀 Creazione embeddings e salvataggio...")
        punti = []
        for film in film_list:
            vettore = encoder.encode(film["trama"]).tolist()
            punti.append(PointStruct(id=str(uuid.uuid4()), vector=vettore, payload=film))

        client.upsert(collection_name=nome_collezione, points=punti)
        print("✅ Database creato e salvato su disco!")
    
    else:
        print("✅ Database trovato su disco! Salto l'indicizzazione.")
        # Dobbiamo comunque caricare l'encoder per trasformare le domande dell'utente
        print(f"📥 Caricamento modello AI per la ricerca...")
        encoder = SentenceTransformer(nome_modello)

    # --- 3. LOOP DI RICERCA ---
    print("\n" + "-" * 50)
    print("🤖 CINE-BOT PERMANENTE")
    print("I tuoi dati sono salvi nella cartella 'qdrant_db'")
    print("-" * 50)

    while True:
        domanda_utente = input("\nCosa vuoi vedere? > ")
        if domanda_utente.lower() in ["q", "exit"]: break
        
        filtro_genere = input("Filtro genere (es. 'drammatico' o invio): ").lower().strip()

        # Encoding domanda
        vettore_domanda = encoder.encode(domanda_utente).tolist()

        # Costruzione filtro
        filtro = None
        if filtro_genere:
            filtro = Filter(must=[FieldCondition(key="genere", match=MatchValue(value=filtro_genere))])

        # Ricerca
        hits = client.query_points(
            collection_name=nome_collezione,
            query=vettore_domanda,
            query_filter=filtro,
            limit=3
        ).points

        if not hits: print("❌ Nessun risultato.")
        for h in hits:
            print(f"   🎬 {h.payload['titolo']} ({h.payload['anno']}) - Score: {h.score:.3f}")

if __name__ == "__main__":
    main()