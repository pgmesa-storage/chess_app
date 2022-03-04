from chessModule import *
import chessModule as chess
from chessGI_class import ChessGI
from chessAI_class import ChessAI
import pygame
import pickle
import socket
import time
from random import choice
import logging
pygame.init()

# ----- Colores para el texto que se muestre en pantalla
WHITE = (226,188,157)
BLACK = (148,96,81)
GRAY = (70, 70, 70)
DARK_GREEN = (100, 140, 0)
LIGHT_GREEN = (141, 182, 0)
YELLOW = (198,206,0)
RED = (178,34,34)
BLUE = (0,191,255)
REAL_BLACK = (0,0,0)

# ------Screen configuration and display-----
# The (0,0)px screenCoord is located in the left-top corner
screenWidth = 1500
screenHeight = 800
screenSize = [screenWidth, screenHeight]
screen = pygame.display.set_mode(screenSize, pygame.RESIZABLE)
pygame.display.set_caption('Chess Game')

myTeam = "white"
enemyTeam = "black"
movingTeam = "white"

#Eliminar
dueTo = None
enemyteam = None

initialPos = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"

gameMoves = []
gameStates = [[[]]]

clock = pygame.time.Clock()
close = False

image = None

END = False
INVERT = False
TURNS = True


# Variables para activar el juego contra el ordenador
IA_ACTIVATED = False
IA2_ACTIVATED = False
SIMULATE = False
ONLINE = False
computerTeam = "black"

# --------------------------------------------------------------------------
# ---- Funcion para configurar la pantalla una vez se reajusta el tamaño ---
def configureScreen(size):
    screen = pygame.display.set_mode(size, pygame.RESIZABLE)
    gi.setScreen(screen)
    gi.updateBoardOnScreen()

# ------------------------------------------------------------
# ---- Funciones para mostrar texto en la interfaz grafica ---

    # Calcula la altura a la que se deben colocar los textos apilados segun el tamaño de la pantalla 
def calcDisplayOfOption(numOptions):
    global screenHeight
    reduc = 200
    button_group_height = screenHeight - reduc
    centralPosOfRect = 0
    for i in range(numOptions):
        centralPosOfRect = button_group_height*((1/2)+i)/numOptions + reduc/2
        yield centralPosOfRect

def showOptions ():
    global gi
    posGenerator = calcDisplayOfOption(4)
    rect1 = gi.showText("Modo Practica", REAL_BLACK,BLUE, screenWidth/2, next(posGenerator),90, True)
    rect2 = gi.showText("Partida 2 Jugadores", REAL_BLACK,BLUE, screenWidth/2, next(posGenerator),90, True)
    rect3 = gi.showText("Partida contra la IA", REAL_BLACK,BLUE, screenWidth/2, next(posGenerator),90, True)
    rect4 = gi.showText("IA vs IA", REAL_BLACK,BLUE, screenWidth/2, next(posGenerator),90, True)
    return [rect1,rect2,rect3,rect4]

def showEndText(endDueto, *byColorTeam): 
    global screenHeight, screenWidth, gi
    if endDueto == "checkMate":
        gi.showText(byColorTeam[0] + " WINS: Check Mate",REAL_BLACK, None, screenWidth/2, screenHeight/2, 60,False)
    elif endDueto == "stalemate":
        gi.showText("Draw: Drowned King",REAL_BLACK, None, screenWidth/2, screenHeight/2, 60, False)
    elif endDueto == "repetition" and TURNS:
        gi.showText("Draw: Triple Repetition",REAL_BLACK, None, screenWidth/2, screenHeight/2, 60, False)         

def showOfficialLastMove():
    global gameMoves
    letters = ["a","b","c","d","e","f","g","h"]
    move = gameMoves[len(gameMoves)-1]
    number = 8-move[1][0]
    letter = letters[move[1][1]]
    char = move[2]
    print("Movement", str(len(gameMoves)) + ":", char+letter+str(number)) 
      
# --------------------------------------------------------
# ---- Funcion para configurar la posicion del tablero ---            
def setPositionOnBoard(strpos,board,invert):
    chars = list(strpos) 
    colum = 0
    row = 0
    for c in chars:
        try:
            spaces = int(c) - 1
            colum += spaces
        except:
            if c == "/":
                colum = 0
                row += 1
            else:
                gi.boardMatrix[row][colum] = ChessPiece(c,(row,colum),invert)
                colum += 1  
    
# ------------------------------------------------------------
# -------- Funciones para el desarrollo de la partida --------

def getTurnOfTeam():
    global gameMoves
    if len(gameMoves)%2 == 0:
        return"white"
    else:
        return "black" 
  
def checkEndOfGameFor(team, board):
    global gi, gameStates
    t0 = time.time()
    if not movesLeftIn(team,board):
        if gi.check:
            if team == "white":
                enemy = "black"
            else:
                enemy = "white"
            return True, "checkMate"
        else:
            return True, "stalemate"
    elif tripleRepetition(gameStates) and TURNS:
        return True, "repetition"
    logger.debug(" checkEnd time: %f ",time.time() - t0) 
    return False, None  
    
# Evalua si donde se ha pinchado con el raton para mover una pieza es una casilla valida o no, para saber si mover la pieza
# o no hacer nada. Se han tenido que calcular sus movimientos en el tablero
# Return -- Devuelve True si es una casilla valida
def evalMove(piece, square):
    possibleMoves = piece.getMoves()
    if square in possibleMoves:
        return True
    return False

# Encapsula las actualizaciones de variables y checkeos necesarios tras realizar un movimiento
def move(clickedSquare):
    global gi, gameMoves, gameStates,dueTo,enemyteam, END, dueTo, movingTeam
    t0 = time.time()
    gameMoves.append((gi.selectedPiece.square, clickedSquare,gi.selectedPiece.char))
    movingTeam = gi.selectedPiece.team
    enemyteam = gi.selectedPiece.getEnemyTeam()
    gi.moveSelectedPiece(clickedSquare)
    gameStates.append(gi.getCharBoard())
    logger.debug(" Turn of: " + getTurnOfTeam())
    END, dueTo = checkEndOfGameFor(enemyteam, gi.boardMatrix) 
    logger.debug(" Move time: %f \n",time.time() - t0) 
    
def waitRemainingTime (t0, seconds):
    tf = time.time()
    dif = tf-t0
    
    if dif >= seconds: return
    else: time.sleep(seconds-dif)

# ---- Funcion para el traspaso de info entre sockets (modo online 2 jugadores ------
# -----------------------------------------------------------------------------------
def sendMove(piece,move):
    global sock
    info = (piece,move)
    content = pickle.dumps(info)
    sock.sendall(content)
    
def recieveMove():
    global sock
    content = sock.recv(40960)
    return pickle.loads(content)

def invertMove(move):
    newMove = (7 - move[0],7 - move[1])
    return newMove
        
        


def practiceMode(gi):
    END = False
    close = False
    GRAY = (70, 70, 70)
    initialPos = initialPos = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"
    setPositionOnBoard(initialPos,gi.boardMatrix, False)
    while not close:
        # Actualizacion de tablero
        screen.fill(GRAY)
        gi.updateBoardOnScreen()
        if END:
            showEndText(dueTo,movingTeam)
        else:
            # If a piece is selected the image will follow the mouse (it's printed in the screenCoord of the mouse in every frame)
            if isRealPiece(gi.selectedPiece) and not END:
                image = gi.getPieceImage(gi.selectedPiece.char)
                mousePos = pygame.mouse.get_pos()
                screen.blit(image, (mousePos[0]-gi.squareSide/2, mousePos[1]-gi.squareSide/2)) 
        pygame.display.update()
        
        #--- Bucle principal de eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                close = True
            if event.type == pygame.VIDEORESIZE:
                size = (event.w, event.h)
                screenHeight = event.h
                screenWidth = event.w
                configureScreen(size)
            if event.type == pygame.MOUSEBUTTONDOWN and not END:
                clickedSquare = gi.getSquare(pygame.mouse.get_pos())
                # Miro a ver si he pinchado dentro del tablero
                if clickedSquare == None: 
                    continue
                # Si no tengo una pieza seleccionada la selecciono 
                if gi.selectedPiece == None:
                    t0 = time.time()
                    gi.takePieceAt(clickedSquare)
                    logger.debug(" takePiece time: %f",time.time() - t0)       
                # Tengo ya una pieza seleccionada, miro si como, la dejo en su sitio o la muevo a otra casilla valida
                else:
                    if gi.selectedPiece.square == clickedSquare:
                        gi.dontMoveSelectedPice()
                    else:
                        if evalMove(gi.selectedPiece,clickedSquare):
                            logger.debug(f" {gi.selectedPiece.team} Movement: [ {gi.selectedPiece.char} , {clickedSquare} ]")
                            move(clickedSquare)                                                                                          
        # Se establecen el frame rate (fps) 
        clock.tick(60)
    # Se cierra el Juego
    logger.info(" Closing Game")
    pygame.quit()          
            
# -------------------------------------------------------------------   
# -------------Inicio de la Ejecución del Programa-------------------    

logging.basicConfig(level = logging.DEBUG)
logger = logging.getLogger(__name__)

gi = ChessGI(screen)

logging.info(" Openning First Screen") 
if __name__ == "__main__": 
    # ----- Pantalla para elegir el modo que se va a jugar ------
    modeSelected = False
    buttons = []
    while not modeSelected and not close:
        screen.fill(GRAY)
        buttons = showOptions()  
        pygame.display.update()        
        clock.tick(60)
        
        mouseCoords = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                close = True
            if event.type == pygame.VIDEORESIZE:
                size = (event.w, event.h)
                configureScreen(size)
            if event.type == pygame.MOUSEBUTTONDOWN:
                for but in buttons:
                    if but.collidepoint(pygame.mouse.get_pos()):
                        if buttons.index(but) == 0:
                            logger.info(" Practice Mode")
                            TURNS = False
                        elif buttons.index(but) == 1:
                            logger.info(" Online Mode")
                            ONLINE = True
                        elif buttons.index(but) == 2:
                            logger.info(" vs IA Mode")
                            IA_ACTIVATED = True
                            teams = ["white", "black"]
                            computerTeam = choice(teams)
                            logger.debug(" Computer team = %s", computerTeam)
                            if computerTeam == "white":
                                INVERT = True
                                myTeam = "black"
                                initialPos = "RNBKQBNR/PPPPPPPP/8/8/8/8/pppppppp/rnbkqbnr"
                            TURNS = True
                        elif buttons.index(but) == 3:
                            logger.info(" IA vs IA Mode")
                            IA_ACTIVATED = True
                            IA2_ACTIVATED = True
                            SIMULATE = True
                        modeSelected = True   
    print("")
    logger.info(" Opening Game\n")
    logger.debug(initialPos + " Invert: %s  turn of " + getTurnOfTeam() +"\n", INVERT)
    setPositionOnBoard(initialPos,gi.boardMatrix, INVERT)
    if IA_ACTIVATED:
        ai = ChessAI(computerTeam)
        t = 0.5
    if IA2_ACTIVATED:
        ai2 = ChessAI("white")
        t = 0.2
    ti = time.time()
    while not close:
        # Actualizacion de tablero
        screen.fill(GRAY)
        gi.updateBoardOnScreen()
        if END:
            showEndText(dueTo,movingTeam)
        else:
            # If a piece is selected the image will follow the mouse (it's printed in the screenCoord of the mouse in every frame)
            if isRealPiece(gi.selectedPiece) and not END:
                image = gi.getPieceImage(gi.selectedPiece.char)
                mousePos = pygame.mouse.get_pos()
                screen.blit(image, (mousePos[0]-gi.squareSide/2, mousePos[1]-gi.squareSide/2)) 
        pygame.display.update()
        
        if IA_ACTIVATED and not END:          
            if IA2_ACTIVATED and "white" == getTurnOfTeam():
                computerTeam = getTurnOfTeam()
                ti = time.time()
                square, piece = ai2.generate_move(gi.boardMatrix)
                logger.debug(f" Computer Movement: [ {piece.char} , {square} ]")
                logger.debug(f" Tiempo en generar el movimiento {time.time()-ti}")
                waitRemainingTime(ti,t) 
                gi.eraseLastMove() 
                gi.selectedPiece = piece
                gi.eraseLastMove()
                move(square)  
            if computerTeam == getTurnOfTeam():
                ti = time.time()
                square, piece = ai.generate_move(gi.boardMatrix)
                logger.debug(f" Computer Movement: [ {piece} , {square} ]")
                logger.debug(f" Tiempo en generar el movimiento {time.time()-ti}")
                waitRemainingTime(ti,t) 
                gi.eraseLastMove() 
                gi.selectedPiece = piece
                gi.eraseLastMove()
                move(square) 
            
        #--- Bucle principal de eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                close = True
            if event.type == pygame.VIDEORESIZE:
                size = (event.w, event.h)
                screenHeight = event.h
                screenWidth = event.w
                configureScreen(size)
            if event.type == pygame.MOUSEBUTTONDOWN and not END:
                clickedSquare = gi.getSquare(pygame.mouse.get_pos())
                # Miro a ver si he pinchado dentro del tablero
                if clickedSquare == None: 
                    continue
                # Si no tengo una pieza seleccionada la selecciono 
                if gi.selectedPiece == None: # and getTurnOfTeam() == myteam
                    t0 = time.time()
                    gi.takePieceAt(clickedSquare)
                    # if not gi.selectedPiece == getTurnOfTeam() and TURNS:
                    #     gi.dontMoveSelectedPice()
                    logger.debug(" takePiece time: %f",time.time() - t0) 
                            
                # Tengo ya una pieza seleccionada, miro si como, la dejo en su sitio o la muevo a otra casilla valida
                else:
                    if gi.selectedPiece.square == clickedSquare:
                        gi.dontMoveSelectedPice()
                    else:
                        if evalMove(gi.selectedPiece,clickedSquare):
                            logger.debug(f" {gi.selectedPiece.team} Movement: [ {gi.selectedPiece.char} , {clickedSquare} ]")
                            move(clickedSquare)     
                                                                                                   
        # Se establecen el frame rate (fps) 
        clock.tick(60)
    # Se cierra el Juego
    logger.info(" Closing Game")
    pygame.quit()
# ---------------Fin de la Ejecución del Programa--------------------
# -------------------------------------------------------------------