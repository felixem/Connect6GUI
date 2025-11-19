from engine import *

class MoveExceptionType:
    TIMEOUT = -1
    INVALID_MOVE = -2
    DUPLICATED_MOVE = -3

class MoveException(Exception):
    def __init__(self, type, message):
        super().__init__(message)
        self.type = type

class TimeoutMoveException(MoveException):
    def __init__(self):
        super().__init__(MoveExceptionType.TIMEOUT, "Timeout")

class InvalidMoveException(MoveException):
    def __init__(self, move):
        super().__init__(MoveExceptionType.INVALID_MOVE, "Try impossible move " + str(move))

class DuplicatedMoveException(MoveException):
    def __init__(self, move):
        super().__init__(MoveExceptionType.DUPLICATED_MOVE, "Try duplicated move " + str(move))

class GameState:

    Exit = -1;

    Idle = 0;
    AI2AI = 1;
    AI2Human = 2
    Human2Human = 3;

    WaitForEngine = 1;
    WaitForHumanFirst = 2;
    WaitForHumanSecond = 3;

    Win = 4;
    Draw = 5;

class Player:
    HUMAN = 0
    BOT = 1
    
    def __init__(self):
        self.type = None
        self.id = -1
        
    def get_name(self):
        return ""
        
    def start_player(self, move, level, vcf):
        return
        
    def is_ready(self):
        return False
        
    def release(self):
        return;
        
class HumanPlayer(Player):
    def __init__(self):
        super().__init__()
        self.type = Player.HUMAN
        
    def is_ready(self):
        return True
        
class BotPlayer(Player):
    def __init__(self):
        super().__init__()
        self.path = ""
        self.type = Player.BOT
        self.engine = GameEngine()
        
    def has_correct_name(self):
        return self.path is not None and len(self.path) > 0
        
    def release(self):
        if self.engine is not None:
            self.engine.release()
            self.engine = GameEngine()
            
    def init_engine(self, level, vcf, move):
        self.engine.init(self.path, level, vcf);
    
    def get_short_name(self):
        return self.engine.shortName;
        
    def get_name(self):
        return self.engine.name;
        
    def start_player(self, move, level, vcf):
        self.init_engine(level,vcf,move)
        return
        
    def is_ready(self):
        return self.path is not None and len(self.path) > 0
        
class Game:
    def __init__(self, black, white):
        self.black = black
        self.white = white
        self.result = -1
        self.moves = []
        self.times = []
        self.feedback = ""
        self.error = None
        
    def release(self):
        self.black.release()
        self.white.release()
        self.result = -1
        self.moves = []
        self.times = []
        self.feedback = ""
        self.error = None
        
    def is_ready(self):
        return self.black.is_ready(), self.white.is_ready()
        
    def start_players(self, level, vcf):
        self.black.start_player(Move.BLACK, level, vcf)
        self.white.start_player(Move.WHITE, level, vcf)
        
        #Return mode and next state
    def get_game_state(self):
        black_t = self.black.type
        white_t = self.white.type
        
        if black_t == Player.HUMAN and white_t == Player.HUMAN:
            return GameState.Human2Human, GameState.WaitForHumanFirst
        elif black_t == Player.BOT and white_t == Player.BOT:
            return GameState.AI2AI, GameState.WaitForEngine
        else:
            if black_t == Player.BOT:
                return GameState.AI2Human, GameState.WaitForEngine
            else:
                return GameState.AI2Human, GameState.WaitForHumanFirst

class Tournament:

    def __init__(self):
        self.players = []
        self.games = []
        
    def add_player(self, player):
        self.players.append(player)
        
    def reset_players(self):
        self.players = []
        
    def reset_games(self):
        self.games = []
        
    def generate_games(self):
        self.games = []
        return;
                        
    def next_game(self):
        for game in self.games:
            if game.result == -1:
                return game
        
        return None
        
    def load_from_file(self, f):
        reader = PlayerReader()
        self.players = reader.read_from_file(f)
        
        #Calculate scores for every player
    def calculate_scores(self):
        scores = [0] * len(self.players)
        timeouts = [0] * len(self.players)
        incorrect_moves = [0] * len(self.players)
        cross_table = [[0 for i in range(len(self.players))] for j in range(len(self.players))]
        
        for game in self.games:
            idb = game.black.id
            idw = game.white.id
            
            if game.result == Move.NONE:
                scores[idb] += 1
                scores[idw] += 1
                cross_table[idb][idw] += 1
                cross_table[idw][idb] += 1
            elif game.result == Move.BLACK:
                scores[idb] += 2
                cross_table[idb][idw] += 2
                if game.error is not None:
                    if game.error.type == MoveExceptionType.TIMEOUT:
                        timeouts[idw] += 1
                    else:
                        incorrect_moves[idw] += 1
            elif game.result == Move.WHITE:
                scores[idw] += 2
                cross_table[idw][idb] += 2
                if game.error is not None:
                    if game.error.type == MoveExceptionType.TIMEOUT:
                        timeouts[idb] += 1
                    else:
                        incorrect_moves[idb] += 1
        
        return scores, timeouts, incorrect_moves, cross_table
        
    #Calculate tie-breaker
    def calculate_bucholtz(self, scores):
        bucholtz = [0] * len(self.players)
        
        for game in self.games:
            idb = game.black.id
            idw = game.white.id
            
            if game.result == Move.NONE:
                bucholtz[idb] += scores[idw]
                bucholtz[idw] += scores[idb]
            elif game.result == Move.BLACK:
                bucholtz[idb] += scores[idw]*2
            elif game.result == Move.WHITE:
                bucholtz[idw] += scores[idb]*2
                
        return bucholtz
    
    #Get final clasification   
    def get_classification(self):
        scores, timeouts, incorrect_moves, cross_table = self.calculate_scores()
        bucholtz = self.calculate_bucholtz(scores)
        
        tuples = []
        for i in range(0, len(scores)):
            tuples.append((self.players[i], scores[i], bucholtz[i], timeouts[i], incorrect_moves[i]))
        
        #Sort by score and bucholtz as tie-breaker
        sorted_list = sorted(tuples, key=lambda x: (x[1], x[2]), reverse=True)

        #Sort cross table by position in sorted list
        sorted_cross_table = self.order_cross_table(cross_table, sorted_list)
        
        return sorted_list, sorted_cross_table
    
    #Order cross table by position in sorted list
    def order_cross_table(self, cross_table, classification):
        ordered = [[0 for i in range(len(self.players))] for j in range(len(self.players))]
        
        for i in range(0, len(classification)):
            player, _, _, _, _ = classification[i]
            for j in range(i, len(classification)):
                player2, _, _, _, _ = classification[j]
                ordered[i][j] = cross_table[player.id][player2.id]
                ordered[j][i] = cross_table[player2.id][player.id]
                
        return ordered
        
    def save_results(self, f):
        #Print players
        f.write('Players:\n')
        for player in self.players:
            f.write(str(player.id))
            f.write(",")
            f.write(player.name)
            f.write(";")
        f.write("\n")
        
        #Print classification
        f.write('Classification:\n')
        classification, cross_table = self.get_classification()
        for i in range(0, len(classification)):
            player, score, bucholtz, timeouts, incorrect_moves = classification[i]
            f.write(str(i+1))
            f.write(",")
            f.write(str(player.id))
            f.write(",")
            f.write(player.name)
            f.write(",")
            f.write(str(score))
            f.write(",")
            f.write(str(bucholtz))
            f.write(",")
            f.write(str(timeouts))
            f.write(",")
            f.write(str(incorrect_moves))
            f.write(",")
            f.write("\n")

        #Print cross table results
        f.write('Cross table results:\n')
        f.write("RK,PLAYER,")
        for i in range(0, len(cross_table)):
            f.write(str(i+1))
            f.write(",")
        f.write('PTS,')
        f.write('TIEBREAK,')
        f.write('TIMEOUTS,')
        f.write('INCORRECT')
        f.write("\n")
        for i in range(0, len(cross_table)):
            f.write(str(i+1))
            f.write(",")
            f.write(classification[i][0].name)
            f.write(",")
            for j in range(0, len(cross_table[i])):
                f.write(str(cross_table[i][j]))
                f.write(",")
            f.write(str(classification[i][1]))
            f.write(",")
            f.write(str(classification[i][2]))
            f.write(",")
            f.write(str(classification[i][3]))
            f.write(",")
            f.write(str(classification[i][4]))
            f.write("\n")
        
        #Print games
        f.write('Games:\n')
        for game in self.games:
            black = game.black
            white = game.white
            f.write(str(black.id))
            f.write(",")
            f.write(black.name)
            f.write(",")
            f.write(str(white.id))
            f.write(",")
            f.write(white.name)
            f.write(",")
            f.write(str(game.result))
            f.write(",")
            f.write(str(game.feedback))
            f.write(",")
            
            #Write moves
            for move in game.moves:
                move = move.toPlaceCmd().strip()+" "
                f.write(move)
                
            f.write(",")
            #Write times
            for t in game.times:
                f.write(str(t))
                f.write(" ")
            
            f.write('\n') 
        
class RoundRobinTournament(Tournament):
    def __init__(self, repetitions = 1):
        super().__init__()
        self.repetitions = repetitions
        
    def generate_games(self):
        self.games = []
        for p1 in self.players:
            for p2 in self.players:
                if p1 != p2:
                    for i in range(0, self.repetitions):
                        game = Game(p1,p2)
                        self.games.append(game)
        
        return None
        
class PlayerReader:

    def __init__(self):
        return
        
    def read_from_file(self, path):
        # Using readline()
        file1 = open(path, 'r')
        players = []
        idx = 0
         
        while True:
         
            # Get next line from file
            line = file1.readline()
         
            # if line is empty
            # end of file is reached
            if not line:
                break
            
            #Create player from file
            player = BotPlayer()
            player.path = line.strip()
            
            try:
                print('Loading engine: ' + player.path);
                player.start_player(Move.BLACK, 1, True);
                player.release()
                players.append(player)
                player.id = idx
                idx = idx+1
                print('Engine loaded successfully: ' + player.path);
            except Exception as e:
                print("Error to load the engine: " + player.path + ", errors: " + str(e));
             
        file1.close()
        return players
        
            
    
                        
                    
            
