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

    def create_party(self, title_party):
        """
        Crée une nouvelle partie avec le titre spécifié et l'enregistre dans la base de données.
        """
        query = """
        INSERT INTO parties (title_party)
        VALUES (%s)
        RETURNING id_party;
        """
        self.cursor.execute(query, (title_party,))
        party_id = self.cursor.fetchone()[0]
        self.conn.commit()
        return party_id

    def list_parties(self):
        """
        Liste les parties disponibles.
        """
        query = "SELECT id_party, title_party FROM parties;"
        self.cursor.execute(query)
        return [{"id_party": row[0], "title_party": row[1]} for row in self.cursor.fetchall()]

    def add_player(self, pseudo):
        """
        Ajoute un joueur à la base de données.
        """
        query = """
        INSERT INTO players (pseudo)
        VALUES (%s)
        RETURNING id_player;
        """
        self.cursor.execute(query, (pseudo,))
        player_id = self.cursor.fetchone()[0]
        self.conn.commit()
        return player_id

    def assign_player_to_party(self, id_party, id_player, id_role, is_alive=True):
        """
        Assigne un joueur à une partie avec un rôle spécifique.
        """
        query = """
        INSERT INTO players_in_parties (id_party, id_player, id_role, is_alive)
        VALUES (%s, %s, %s, %s);
        """
        self.cursor.execute(query, (id_party, id_player, id_role, is_alive))
        self.conn.commit()

    def start_turn(self, id_party):
        """
        Démarre un nouveau tour pour une partie.
        """
        query = """
        INSERT INTO turns (id_party, start_time)
        VALUES (%s, NOW())
        RETURNING id_turn;
        """
        self.cursor.execute(query, (id_party,))
        turn_id = self.cursor.fetchone()[0]
        self.conn.commit()
        return turn_id

    def end_turn(self, id_turn):
        """
        Termine un tour en mettant à jour l'heure de fin.
        """
        query = """
        UPDATE turns
        SET end_time = NOW()
        WHERE id_turn = %s;
        """
        self.cursor.execute(query, (id_turn,))
        self.conn.commit()

    def record_player_action(self, id_player, id_turn, action, origin_position, target_position):
        """
        Enregistre une action effectuée par un joueur pendant un tour.
        """
        query = """
        INSERT INTO players_play (
            id_player, id_turn, start_time, end_time, action,
            origin_position_col, origin_position_row,
            target_position_col, target_position_row
        )
        VALUES (%s, %s, NOW(), NOW(), %s, %s, %s, %s, %s);
        """
        self.cursor.execute(query, (
            id_player, id_turn, action,
            origin_position[0], origin_position[1],
            target_position[0], target_position[1]
        ))
        self.conn.commit()

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
        party_id = admin.create_party("Partie 1")
        print(f"Nouvelle partie créée avec l'ID : {party_id}")

        # Ajout de joueurs
        player1_id = admin.add_player("Player1")
        player2_id = admin.add_player("Player2")
        print(f"Joueurs ajoutés : {player1_id}, {player2_id}")

        # Assigner des joueurs à la partie
        admin.assign_player_to_party(party_id, player1_id, id_role=1, is_alive=True)  # Rôle 1 : Villageois
        admin.assign_player_to_party(party_id, player2_id, id_role=2, is_alive=True)  # Rôle 2 : Loup
        print(f"Joueurs assignés à la partie {party_id}")

        # Démarrer un tour
        turn_id = admin.start_turn(party_id)
        print(f"Tour démarré avec l'ID : {turn_id}")

        # Enregistrer une action
        admin.record_player_action(
            id_player=player1_id,
            id_turn=turn_id,
            action="up",
            origin_position=(0, 0),
            target_position=(0, 1)
        )
        print("Action enregistrée pour Player1")

        # Terminer le tour
        admin.end_turn(turn_id)
        print(f"Tour {turn_id} terminé")
    finally:
        # Fermer la connexion à la base de données
        admin.close()