import json
import uuid
from pathlib import Path
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)


DATA_PATH = Path(__file__).with_name("film_data.json")


def load_film_data(path: Path = DATA_PATH):
    """Carica i metadati dei film dal file JSON."""
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def trova_trama_da_titolo(titolo_cercato, lista_film):
    """Restituisce la trama del film indicato, None se assente."""
    for film in lista_film:
        if film["titolo"].lower() == titolo_cercato.lower():
            return film["trama"]
    return None

def trova_film_da_titolo(titolo_cercato, lista_film):
    """Restituisce l'oggetto film completo, None se assente."""
    for film in lista_film:
        if film["titolo"].lower() == titolo_cercato.lower():
            return film
    return None


def main():
    print("📂 Connessione al database locale...")
    client = QdrantClient(path="./qdrant_db")

    nome_collezione = "film_persistenti"
    nome_modello = "paraphrase-multilingual-mpnet-base-v2"
    encoder = None

    # Carica i dati dei film dal JSON con gestione errori
    try:
        film_list = load_film_data()
    except FileNotFoundError:
        print("❌ File 'film_data.json' non trovato. Assicurati che esista.")
        return
    except json.JSONDecodeError:
        print("❌ 'film_data.json' non è valido. Controlla la sintassi JSON.")
        return

    if not client.collection_exists(collection_name=nome_collezione):
        print("⚠️ Collezione non trovata. Inizializzazione primo avvio...")
        print(f"📥 Caricamento modello AI: {nome_modello}...")
        encoder = SentenceTransformer(nome_modello)

        client.create_collection(
            collection_name=nome_collezione,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )

        print("🚀 Creazione embeddings e salvataggio...")
        punti = []
        for film in film_list:
            vettore = encoder.encode(film["trama"]).tolist()
            punti.append(PointStruct(id=str(uuid.uuid4()), vector=vettore, payload=film))

        client.upsert(collection_name=nome_collezione, points=punti)
        print("✅ Database creato e salvato su disco!")
    else:
        print("✅ Database trovato su disco! Salto l'indicizzazione.")

    if encoder is None:
        print("📥 Caricamento modello AI per la ricerca...")
        encoder = SentenceTransformer(nome_modello)



    print("\n" + "-" * 50)
    print("🤖 CINE-BOT PERMANENTE")
    print("I tuoi dati sono salvi nella cartella 'qdrant_db'")
    print("-" * 50)

    print("\n" + "-" * 50)
    print("🤖 CINE-MATCH: Dimmi cosa ti piace, ti dirò cosa guardare.")
    print("Film disponibili: Il Padrino, Matrix, Shrek, Toy Story, ecc...")
    print("-" * 50)

    while True:
        titolo_input = input("\nScrivi il titolo di un film che ti è piaciuto > ").strip()

        if titolo_input.lower() in ["q", "exit", "esci"]:
            break

        film_match = trova_film_da_titolo(titolo_input, film_list)

        if film_match is None:
            print(f"❌ Non conosco il film '{titolo_input}'. Prova con un titolo esatto della lista.")
            continue

        print(f"✅ Ho trovato '{titolo_input}'. Analizzo la trama per trovare simili...")

        canonical_title = film_match["titolo"]
        vettore_ricerca = encoder.encode(film_match["trama"]).tolist()

        filtro_no_se_stesso = Filter(
            must_not=[
                FieldCondition(
                    key="titolo",
                    match=MatchValue(value=canonical_title),
                )
            ]
        )

        hits = client.query_points(
            collection_name=nome_collezione,
            query=vettore_ricerca,
            query_filter=filtro_no_se_stesso,
            limit=3,
        ).points

        print(f"   🎬 Poiché ti è piaciuto '{titolo_input}', ti consiglio:")
        for h in hits:
            if h.score > 0.25:
                print(f"   -> {h.payload['titolo']} (Score: {h.score:.3f})")
            else:
                print(f"   -> {h.payload['titolo']} (Scartato - Troppo diverso, Score: {h.score:.3f})")

if __name__ == "__main__":
    main()