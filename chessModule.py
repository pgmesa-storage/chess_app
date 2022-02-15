
from chessPiece_class import ChessPiece
import copy

# -------------------------------------- CHESS MODULE --------------------------------------------
# Modulo con funciones para realizar movimientos validos sobre un tablero de ajedrez representado
# mediante una matriz donde cada posicion es una casilla del tablero
# ------------------------------------------------------------------------------------------------

if __name__ == "__main__":
    pass

# Realiza el movimiento de una pieza (El movimiento se realiza 100% ya que si si ha invocado a esta funcion es que el 
# movimiento es valido) y se encarga del resto de eventos asociados al movimiento (Comprobar jaques, movimientos especiales
# como enroque y de que se pinten en el tablero)
def makeMove(selectedPiece, finalSquare, board):
    # Realizamos una copia de la pieza para no modificar las propiedades de la pieza que hemos cogido
    piece = copy.deepcopy(selectedPiece)
    captured = False
    castled = False
    
    # Se guarda la posicion inicial antes de mover, se indica que ya no hay pieza en la posicion inicial y 
    # se mira que pieza hay donde nos vamos a mover
    startSquare = piece.square
    board[startSquare[0]][startSquare[1]] = ChessPiece("-",startSquare)
    capturedPiece = board[finalSquare[0]][finalSquare[1]]
    
    # ------------------------------------------------------------------------------------------------------------------------
    # ---- Se mira si ha ocurrido algun movimiento especial (captura al paso o Enroque) ----
    dif = finalSquare[1] - startSquare[1] # dif se usa para ver si el rey ha dado 2 pasos y ha habido enroque
    # Se mira si ha habido captura al paso. Se comprueba si la pieza que deja detras el peon es un peon
    # enemigo a capturar que a dado dos pasos en su anterior jugada atributo isPassing = True
    p = board[startSquare[0]][finalSquare[1]]
    if capturedPiece.char == "-" and piece.char.lower() == "p" and p.char.lower() == 'p' and piece.isEnemy(p.team):
        capturedPiece = board[startSquare[0]][finalSquare[1]]
        board[startSquare[0]][finalSquare[1]] = ChessPiece("-",(startSquare[0],finalSquare[1])) 
        captured = True
    # Se mira si ha habido enroque, es decir si el rey va a dar dos pasos (tiene en sus posibles movimientos)
    # un mov de dos pasos --> Enroque
    elif piece.char.lower() == 'k' and abs(dif) == 2:
        if dif > 0:
            rook = board[finalSquare[0]][7]
            board[finalSquare[0]][7] = ChessPiece("-",(finalSquare[0],7))
            rook.updateState((finalSquare[0],finalSquare[1]-1))
            board[finalSquare[0]][finalSquare[1]-1] = rook
        else:
            rook = board[finalSquare[0]][0]
            board[finalSquare[0]][0] = ChessPiece("-",(finalSquare[0],0))
            rook.updateState((finalSquare[0],finalSquare[1]+1))
            board[finalSquare[0]][finalSquare[1]+1] = rook
        castled = True
# ---------------------------------------------------------------------------------------
# ----- Esto es lo que se jecuta de manera normal si no hay movimientos especiales ------
    else:
    # Se ejecuta cuando se captura una pieza normal (No captura al paso)             
        if isRealPiece(capturedPiece):
            captured = True
    # Se resetea el comer al paso (Tanto si se ha realizado como si no) Solo se puede realizar en ese turno    
    resetInPassing(board) 
    # Se actualiza el estado de la pieza a mover (se actualiza su posicion y se resetean ciertos parametros) y finalmente se mueve
    piece.updateState(finalSquare)
    # Se mira a ver si ha habido coronacion 
    crown, char = piece.checkCrown()
    if crown:
        piece.char = char
    # Finalmente se coloca la pieza y se devuelven dos booleanos que indican si se ha capturado pieza y si se ha enrocado
    board[finalSquare[0]][finalSquare[1]] = piece
    return captured, castled

def filterMoves(piece,board):
    # Si es el rey salimos
    if piece.char.lower() == 'k':
        return
    moves = piece.getMoves()
    notLegalMoves = []
    # Miramos si hay jaque al rey aliado para filtrar aquellos que no lo bloqueen
    check, kingPos = teamIsChekingEnemyKing(piece.getEnemyTeam(),board)
    if check:
        validMoves = []
        # Probamos todos los movimientos posibles de la pieza y vemos si se anula el jaque sobre el rey aliado
        for move in moves:
            if not move == None :
                copyBoard = copy.deepcopy(board) 
                makeMove(piece,move,copyBoard)#copyBoard = simulateMoveOn(copyBoard,copyPiece,move)
                # Comprobamos si el movimiento anula el jaque o los jaques que pudiera estar recibiendo el rey aliado
                inCheck, checkPos = teamIsChekingEnemyKing(piece.getEnemyTeam(),copyBoard)
                if not inCheck:
                    validMoves.append(move)
            else:
                validMoves.append(move)         
        piece.moves = validMoves  
    # Miramos si moviendo la pieza a algun lugar provocaría un jaque del enemigo
    moves = piece.getMoves()
    for move in moves:
        if not move == None:
            copyBoard = copy.deepcopy(board) # Las listas son objetos mutables y si los pasamos a una funcion estos se ven modificados (hay que realizar una copia)
            makeMove(piece,move,copyBoard)
            # Una vez simulado el mov, vemos si alguna pieza enemiga da jaque al rey aliado
            inCheck, checkPos = teamIsChekingEnemyKing(piece.getEnemyTeam(),copyBoard)
            if inCheck:
                notLegalMoves.append(move)
    for move in notLegalMoves:
        moves.remove(move)         
    

# Se comprueba si alguna de las piezas del equipo que se le pasa como argumento esta dando jaque al rey enemigo
# Return -- Devuelve 2 valores. Un booleano  con True, si alguna piezada esta dando jaque y una tupla con la posicion
# del rey enemigo (Donde hay que pintar el color rojo del jaque)   
def teamIsChekingEnemyKing(team, board):
    teams = getBoardAsDict(board)
    teamPieces = teams.get(team)
    for piece in teamPieces:
        if not piece.char.lower() == 'k':
            piece.calcLegalMovesOnBoard(board)
            moves = piece.getMoves()
            for move in moves:
                if not move == None:
                    p = board[move[0]][move[1]]
                    if p.char.lower() == 'k' and piece.isEnemy(p.team):
                        kingPos = move
                        return True, kingPos 
    return False, None 

# Funcion creada para optimizar la busqueda de piezas en el tablero
def getBoardAsDict(board):
    teams = {"white": set(), "black": set()}
    pSet = set()
    for i in range(8):
        pSet |= set(board[i])
    for p in pSet:
        if p.char == "-": continue
        else: teams[p.team].add(p)    
    return teams

# Pone a False el atributo inPassing de todos los peones (La utilidad de esta funcion es que una vez realizado un movimiento
# se pierde la oportunidad de comer a peon pasado en caso de que se pudiera en la jugada anterior)
def resetInPassing(board):
    for i in range (8):
        for p in board[i]:
            if p.char.lower() == 'p':
                p.inPassing = False
                
# Comprueba si la pieza que se le pasa como argumento es una pieza real y no una pieza guion "-" o 
# nula (None) (Fuera del tablero)
def isRealPiece(piece):
    if not piece == None and not piece.char == "-":
        return True
    return False

# ------------ Funciones para comprobar el fin de partida por jaque mate, rey ahogado o triple repeticion -----------
# -------------------------------------------------------------------------------------------------------------------

# Se mira si el equipo que se le pasa como argumento tiene alguna pieza que pueda realizar moviminetos legales.    
def movesLeftIn(team,board):
    teams = getBoardAsDict(board)
    teamPieces = teams.get(team)
    piecesWithAvailableMoves = 0
    for piece in teamPieces:
        # Miramos si no se han calculado los mov previamente (lista vacia)
        piece.calcLegalMovesOnBoard(board)
        filterMoves(piece,board)
        moves = piece.getMoves()
        movesWithoutNones = set(moves) # Elimina los objetos repetidos al pasarloa set()
        movesWithoutNones.discard(None)
        if not len(movesWithoutNones) == 0:
            return True
    return False
   
# Miramos si hay empate por repeticion de posicion triple
def tripleRepetition(gameStates):
    numMoves = len(gameStates)
    if numMoves >= 5:
        unique = []
        repeted1 = []
        repeted2 = []
        for board in gameStates:
            if board not in unique:
                unique.append(board)
            elif board not in repeted1:
                repeted1.append(board)
            else:
                return True
    return False


    
        