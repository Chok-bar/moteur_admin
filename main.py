import psycopg2
from psycopg2.extras import Json

class GameAdmin:
    def __init__(self, db_config):
        """
        Initialise la connexion à la base de données.
        :param db_config: Dictionnaire contenant les informations de connexion à la base de données.
        """
        self.conn = psycopg2.connect(**db_config)
        self.cursor = self.conn.cursor()

    def create_party(self, rows, cols, max_turn_time, num_turns, num_obstacles, max_players):
        """
        Crée une nouvelle partie avec les paramètres spécifiés et l'enregistre dans la base de données.
        """
        query = """
        INSERT INTO parties (rows, cols, max_turn_time, num_turns, num_obstacles, max_players)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id;
        """
        self.cursor.execute(query, (rows, cols, max_turn_time, num_turns, num_obstacles, max_players))
        party_id = self.cursor.fetchone()[0]
        self.conn.commit()
        return party_id

    def list_parties(self):
        """
        Liste les parties disponibles qui n'ont pas encore commencé.
        """
        query = "SELECT id FROM parties WHERE started = FALSE;"
        self.cursor.execute(query)
        return [row[0] for row in self.cursor.fetchall()]

    def get_party_details(self, party_id):
        """
        Récupère les détails d'une partie spécifique.
        """
        query = "SELECT * FROM parties WHERE id = %s;"
        self.cursor.execute(query, (party_id,))
        party = self.cursor.fetchone()
        if party:
            return {
                "id": party[0],
                "rows": party[1],
                "cols": party[2],
                "max_turn_time": party[3],
                "num_turns": party[4],
                "num_obstacles": party[5],
                "max_players": party[6],
                "players": party[7],
                "started": party[8],
            }
        else:
            raise ValueError(f"Party ID {party_id} does not exist.")

    def start_party(self, party_id):
        """
        Démarre une partie si elle n'a pas encore commencé.
        """
        query = "UPDATE parties SET started = TRUE WHERE id = %s AND started = FALSE;"
        self.cursor.execute(query, (party_id,))
        if self.cursor.rowcount == 0:
            raise ValueError(f"Party ID {party_id} does not exist or has already started.")
        self.conn.commit()
        return True

    def add_player_to_party(self, party_id, player_name):
        """
        Ajoute un joueur à une partie si elle n'a pas encore atteint le nombre maximum de joueurs.
        """
        party = self.get_party_details(party_id)
        if len(party["players"]) < party["max_players"]:
            query = "UPDATE parties SET players = array_append(players, %s) WHERE id = %s;"
            self.cursor.execute(query, (player_name, party_id))
            self.conn.commit()
            return True
        else:
            raise ValueError(f"Party ID {party_id} is full.")

    def close(self):
        """
        Ferme la connexion à la base de données.
        """
        self.cursor.close()
        self.conn.close()


# Exemple d'utilisation
if __name__ == "__main__":
    # Configuration de la base de données
    db_config = {
        "dbname": "your_database_name",
        "user": "your_username",
        "password": "your_password",
        "host": "localhost",
        "port": 5432,
    }

    admin = GameAdmin(db_config)

    try:
        # Création d'une nouvelle partie
        party_id = admin.create_party(rows=5, cols=5, max_turn_time=30, num_turns=10, num_obstacles=3, max_players=4)
        print(f"Nouvelle partie créée avec l'ID : {party_id}")

        # Liste des parties disponibles
        print("Parties disponibles :", admin.list_parties())

        # Ajout de joueurs
        admin.add_player_to_party(party_id, "Player1")
        admin.add_player_to_party(party_id, "Player2")
        print("Détails de la partie :", admin.get_party_details(party_id))

        # Démarrage de la partie
        admin.start_party(party_id)
        print("Partie démarrée :", admin.get_party_details(party_id))
    finally:
        # Fermer la connexion à la base de données
        admin.close()
