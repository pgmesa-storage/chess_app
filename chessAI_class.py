from chessModule import *
from random import choice
from chessPiece_class import ChessPiece
import copy

class ChessAI:
    
    team = None
    
    def __init__(self, computerTeam):
        self.team = computerTeam

# --------------------FUNCIONES PARA JUGAR CONTRA EL ORDENADOR----------------------
# ---------------------------------------------------------------------------------- 
    def __removeNones(self,moves):
        setMoves = set(moves)
        setMoves.discard(None)
        return list(setMoves)      
                   
    def generate_move(self,board):
        teamPieces = getBoardAsDict(board).get(self.team)
        piecesWithMoves = {}
        canCaptureIn = ((),None)
        for p in teamPieces:
            p.calcLegalMovesOnBoard(board)
            filterMoves(p,board)
            moves = set(p.getMoves())
            moves.discard(None)
            if not len(moves) == 0:
                piecesWithMoves[p] = set(moves)
                for mov in moves:
                    if board[mov[0]][mov[1]].isEnemy(self.team):
                        canCaptureIn = (mov,p)
                    copyBoard = copy.deepcopy(board) 
                    makeMove(p,mov,copyBoard)
                    inCheck, checkPos = teamIsChekingEnemyKing(p.team,copyBoard)
                    if inCheck:
                        return mov, p
        if not canCaptureIn[1] == None:
            return canCaptureIn
        else:
            # Si ninguno captura pieza o da jaque, se escoge el movimiento de forma aleatoria    
            return self.generate_randomMove(piecesWithMoves)
    
    def generate_randomMove(self, board):
        if type(board) == list:
            teamPieces = getBoardAsDict(board).get(self.team)
            piecesWithMoves = []
            for p in teamPieces:
                p.calcLegalMovesOnBoard(board)
                filterMoves(p,board)
                moves = set(p.getMoves())
                moves.discard(None)
                if not len(moves) == 0:
                    piecesWithMoves.append(p)
            piece = choice(piecesWithMoves)
            m = choice(self.__removeNones(piece.getMoves()))
        else:
            pieces = []
            for p in set(board.keys()):
                pieces.append(p)                 
            piece = choice(pieces)
            m = choice(self.__removeNones(piece.getMoves()))
            #chessB.printAvailableMovementsOf(piece)
        return m,piece
        
        