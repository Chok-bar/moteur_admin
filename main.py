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

    # Ajout des méthodes pour interagir avec les vues
    def get_all_players(self):
        """
        Récupère les données de la vue ALL_PLAYERS.
        """
        query = "SELECT * FROM ALL_PLAYERS ORDER BY num_parties, first_participation, last_action, player_name;"
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def get_all_players_elapsed_game(self):
        """
        Récupère les données de la vue ALL_PLAYERS_ELAPSED_GAME.
        """
        query = "SELECT * FROM ALL_PLAYERS_ELAPSED_GAME;"
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def get_all_players_elapsed_tour(self):
        """
        Récupère les données de la vue ALL_PLAYERS_ELAPSED_TOUR.
        """
        query = "SELECT * FROM ALL_PLAYERS_ELAPSED_TOUR;"
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def get_all_players_stats(self):
        """
        Récupère les données de la vue ALL_PLAYERS_STATS.
        """
        query = "SELECT * FROM ALL_PLAYERS_STATS;"
        self.cursor.execute(query)
        return self.cursor.fetchall()

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
        # Exemple d'interaction avec les vues
        print("ALL_PLAYERS:")
        for row in admin.get_all_players():
            print(row)

        print("\nALL_PLAYERS_ELAPSED_GAME:")
        for row in admin.get_all_players_elapsed_game():
            print(row)

        print("\nALL_PLAYERS_ELAPSED_TOUR:")
        for row in admin.get_all_players_elapsed_tour():
            print(row)

        print("\nALL_PLAYERS_STATS:")
        for row in admin.get_all_players_stats():
            print(row)
    finally:
        # Fermer la connexion à la base de données
        admin.close()