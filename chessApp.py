       
import os
import json
import time
import pygame
import logging
from pathlib import Path
from random import choice

from chessModule import *
from client import FAIL, SUCCESS, ChessClient
from classes.chessGI_class import ChessGI
from classes.chessAI_class import ChessAI
from classes.inputs import InputBox

dir_ = Path(__file__).parent.resolve()
env_path = dir_/'.env.json'

def config(key) -> any:
    if not os.path.exists(env_path):
        raise Exception(f"Not '.env.json' file in '{dir_}'")
    with open(env_path, 'r') as file:
        env_dict = json.load(file)
    return env_dict[key]

# Environment variables
try:
    HOST_ADDRESS = config('HOST_ADDRESS')
    HOST_PORT = config('HOST_PORT')
    SERVER_PASSWORD = config('SERVER_PASSWORD')
    NAME = config('USER_NAME')
except Exception as err:
    print(err)
    exit(1)

pygame.init()
# ------------- Variables globales para las funciones definidas fuera del main ---------------
# --------------------------------------------------------------------------------------------

# ----- Colores para el texto que se muestre en pantalla
GRAY = (70, 70, 70)
REAL_BLACK = (0,0,0)
BLUE = (0,191,255)
WHITE = (255,255,255)
# --- Online Game vars
HOSTS_IP = ""
PORT = 9999

# --------------------------------------------------------------------------
# ---- Funcion para configurar la pantalla una vez se reajusta el tamaño ---
def configureScreen(gi,size, update_board=True):
    screen = pygame.display.set_mode(size, pygame.RESIZABLE)
    if update_board:
        gi.setScreen(screen)
        gi.updateBoardOnScreen()
# ------------------------------------------------------------
# ---- Funciones para mostrar texto en la interfaz grafica ---

    # Calcula la altura a la que se deben colocar los textos apilados segun el tamaño de la pantalla 
def calcDisplayOfOption(numOptions, screenHeight):
    reduc = 200
    button_group_height = screenHeight - reduc
    centralPosOfRect = 0
    for i in range(numOptions):
        centralPosOfRect = button_group_height*((1/2)+i)/numOptions + reduc/2
        yield centralPosOfRect
        
def showInput(screen, order:int, width=140, height=32) -> InputBox:
    posGenerator = calcDisplayOfOption(order, gi.screen.get_height())
    for _ in range(order-1):
        next(posGenerator) # Queremos el ultimo solo
    
    box = InputBox((screenWidth/2) - width, next(posGenerator), width, height)
    box.draw(screen)
    
    return box

def showOptions (gi):
    screenHeight = gi.screen.get_height()
    screenWidth = gi.screen.get_width()
    posGenerator = calcDisplayOfOption(5, screenHeight)
    rect1 = gi.showText("Practice Mode", REAL_BLACK,BLUE, screenWidth/2, next(posGenerator),90, True)
    rect2 = gi.showText("2 players (local)", REAL_BLACK,BLUE, screenWidth/2, next(posGenerator),90, True)
    rect3 = gi.showText("Online Game", REAL_BLACK,BLUE, screenWidth/2, next(posGenerator),90, True)
    rect4 = gi.showText("Game against AI", REAL_BLACK,BLUE, screenWidth/2, next(posGenerator),90, True)
    rect5 = gi.showText("AI vs AI", REAL_BLACK,BLUE, screenWidth/2, next(posGenerator),90, True)
    return [rect1,rect2,rect3,rect4,rect5]

def showEndText(endDueto, gi, *byColorTeam): 
    screenHeight = gi.screen.get_height()
    screenWidth = gi.screen.get_width()
    if endDueto == "checkMate":
        gi.showText(byColorTeam[0] + " WINS: Check Mate",REAL_BLACK, None, screenWidth/2, screenHeight/2, 60,False)
    elif endDueto == "stalemate":
        gi.showText("Draw: Drowned King",REAL_BLACK, None, screenWidth/2, screenHeight/2, 60, False)
    elif endDueto == "repetition":
        gi.showText("Draw: Triple Repetition",REAL_BLACK, None, screenWidth/2, screenHeight/2, 60, False)         

def showOfficialLastMove(gameMoves):
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

def invert_move(move) -> tuple[int,int]:
    newMove = (7 - move[0],7 - move[1])
    return newMove
# ------------------------------------------------------------
# -------- Funciones para el desarrollo de la partida --------
def getTurnOfTeam(gameMoves):
    if len(gameMoves)%2 == 0:
        return"white"
    else:
        return "black" 
  
def checkEndOfGameFor(team, board, gameStates, TURNS):
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
    elif TURNS and tripleRepetition(gameStates):
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

def waitRemainingTime(t0, seconds):
    if seconds == 0: return
    tf = time.time()
    dif = tf-t0
    if dif >= seconds: return
    else: time.sleep(seconds-dif)
  
# ----- Funciones para definir los ciclos de ejecucion de cada modo de juego ------  
# ---------------------------------------------------------------------------------      
def practice_mode(gi,logger):
    logger.info(" Practice Mode")
    gi.reset()
    END = False
    close = False
    gameMoves = []
    gameStates = [[[]]]
    initialPos = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"
    
    # Encapsula las actualizaciones de variables y checkeos necesarios tras realizar un movimiento
    def move(clickedSquare):
        t0 = time.time()
        gameMoves.append((gi.selectedPiece.square, clickedSquare, gi.selectedPiece.char))
        enemyteam = gi.selectedPiece.getEnemyTeam()
        gi.moveSelectedPiece(clickedSquare)
        gameStates.append(gi.getCharBoard())
        logger.debug(" Turn of: " + getTurnOfTeam(gameMoves))
        END, dueTo = checkEndOfGameFor(enemyteam, gi.boardMatrix, gameStates, True) 
        logger.debug(" Move time: %f \n",time.time() - t0) 
        return END, dueTo
        
    setPositionOnBoard(initialPos,gi.boardMatrix, False)
    while not close:
        # Actualizacion de tablero
        screen.fill(GRAY)
        gi.updateBoardOnScreen()
        if END:
            showEndText(dueTo,gi,movingTeam)
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
                configureScreen(gi,size)
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
                            movingTeam = gi.selectedPiece.team
                            END, dueTo = move(clickedSquare)                                                                                          
        # Se establecen el frame rate (fps) 
        clock.tick(60)

def local_mode_2players(gi, logger):
    logger.info(" 2 players (local)")
    gi.reset()
    END = False
    close = False
    gameMoves = []
    gameStates = [[[]]]
    initialPos = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"
    
    # Encapsula las actualizaciones de variables y checkeos necesarios tras realizar un movimiento
    def move(clickedSquare):
        t0 = time.time()
        gameMoves.append((gi.selectedPiece.square, clickedSquare, gi.selectedPiece.char))
        enemyteam = gi.selectedPiece.getEnemyTeam()
        gi.moveSelectedPiece(clickedSquare)
        gameStates.append(gi.getCharBoard())
        logger.debug(" Turn of: " + getTurnOfTeam(gameMoves))
        END, dueTo = checkEndOfGameFor(enemyteam, gi.boardMatrix, gameStates, True) 
        logger.debug(" Move time: %f \n",time.time() - t0) 
        return END, dueTo
        
    setPositionOnBoard(initialPos, gi.boardMatrix, False)
    while not close:
        # Actualizacion de tablero
        screen.fill(GRAY)
        gi.updateBoardOnScreen()
        if END:
            showEndText(dueTo,gi,movingTeam)
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
                configureScreen(gi,size)
            if event.type == pygame.MOUSEBUTTONDOWN and not END:
                clickedSquare = gi.getSquare(pygame.mouse.get_pos())
                # Miro a ver si he pinchado dentro del tablero
                if clickedSquare == None: 
                    continue
                # Si no tengo una pieza seleccionada la selecciono 
                if gi.selectedPiece == None:
                    p = gi.boardMatrix[clickedSquare[0]][clickedSquare[1]]
                    if getTurnOfTeam(gameMoves) == p.team:
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
                            inverted = gi.selectedPiece.inverted
                            movingTeam = gi.selectedPiece.team
                            END, dueTo = move(clickedSquare)
                            gi.invert(not inverted) 
                                                                                                                     
        # Se establecen el frame rate (fps) 
        clock.tick(60)

def online_mode(gi, logger):
    logger.info(" Online Game")
    gi.reset()
    END = False
    close = False
    gameMoves = []
    gameStates = [[[]]]
    initialPos = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"
    myTeam = None
    # We try to connect to the server
    client = ChessClient()
    client.init(NAME, HOST_ADDRESS, HOST_PORT, SERVER_PASSWORD)
    client.start()
    connection_outcome = False
    while not connection_outcome:
        screenWidth = gi.screen.get_width()
        screenHeight = gi.screen.get_height()
        screen.fill(GRAY)
        gi.showText("Connecting to the server...", WHITE, GRAY, screenWidth/2, screenHeight/2,40, True)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                client.close()
                return
            if event.type == pygame.VIDEORESIZE:
                size = (event.w, event.h)
                configureScreen(gi,size, update_board=False)
        if not client.is_connected() and client.is_alive():
            pass
        else:
            if client.is_connected():
                connection_outcome = True
            else:
                screen.fill(GRAY)
                gi.showText("[!] Client failed to connect to the server", WHITE, GRAY, screenWidth/2, screenHeight/2,40, True)
        clock.tick(60)
        pygame.display.update()
    # ------ Elegir entre crear o unirse a partida
    game = False; chosen = False; room_id = None; outcome_decided = False; last_msg = None
    while not game:
        # Actualizacion grafica
        screenWidth = gi.screen.get_width()
        screenHeight = gi.screen.get_height()
        if not chosen:
            screen.fill(GRAY)
            posGenerator = calcDisplayOfOption(2, gi.screen.get_height())
            rect1 = gi.showText("Create Room", REAL_BLACK,BLUE, screenWidth/2, next(posGenerator),90, True)
            rect2 = gi.showText("Join an exisiting Room", REAL_BLACK,BLUE, screenWidth/2, next(posGenerator),90, True)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                client.close()
                return
            if event.type == pygame.VIDEORESIZE:
                size = (event.w, event.h)
                configureScreen(gi,size, update_board=False)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and 'text_box' in locals():
                room_id = text_box.text
                client.set_room_id(room_id)
                screen.fill(GRAY)
                params = (f"Joining room with id '{room_id}'...",
                            WHITE, GRAY, screenWidth/2, screenHeight/2 , 40, True)
                gi.showText(*params)
                last_msg = (gi.showText, params)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if rect1.collidepoint(pygame.mouse.get_pos()):
                    chosen = True
                    client.set_action(0)
                    # Wait until the room_id variable is loaded
                    while client.room_id is None: pass
                    screen.fill(GRAY)
                    params = (f"Waiting for a player to join the room... (ID: '{client.room_id}')",
                            WHITE, GRAY, screenWidth/2, screenHeight/2 , 40, True)
                    gi.showText(*params)
                    last_msg = (gi.showText, params)
                elif rect2.collidepoint(pygame.mouse.get_pos()):
                    chosen = True
                    client.set_action(1)
                    # Input del ID
                    text_box = showInput(screen, 2)
            # Vemos si han escrito en el input
            if "text_box" in locals():
                text_box.handle_event(event)
        if last_msg is not None:
            screen.fill(GRAY)
            last_msg[0](*last_msg[1])
        # Vemos si han escrito en el input
        if "text_box" in locals() and room_id is None:
            screen.fill(GRAY)
            posGenerator = calcDisplayOfOption(1, gi.screen.get_height())
            gi.showText(f"Introduce the id of the room you want to join",WHITE, GRAY, screenWidth/2, next(posGenerator), 40, True)
            # Vemos si hay que actualizar el tamaño
            text_box.update()
            # Refrescamos el render del inputbox
            text_box.draw(screen)
        if client.game_status == SUCCESS:
            if not outcome_decided:
                print("[%] Iniciando partida")
            game = True
            outcome_decided = True
        elif client.game_status == FAIL:
            if not outcome_decided:
                print("[!] Fallo al iniciar la partida")
            msg = "[!] Connection with client failed, could not start the game"
            screen.fill(GRAY)
            gi.showText(msg,WHITE, GRAY, screenWidth/2, screenHeight/2,40, True)
            outcome_decided = True
        clock.tick(60)
        pygame.display.update()
                
    # -------------------------------------
    # Encapsula las actualizaciones de variables y checkeos necesarios tras realizar un movimiento
    def move(clickedSquare):
        t0 = time.time()
        gameMoves.append((gi.selectedPiece.square, clickedSquare, gi.selectedPiece.char))
        possibleWinner = gi.selectedPiece.team
        enemyteam = gi.selectedPiece.getEnemyTeam()
        gi.moveSelectedPiece(clickedSquare)
        gameStates.append(gi.getCharBoard())
        logger.debug(" Turn of: " + getTurnOfTeam(gameMoves))
        END, dueTo = checkEndOfGameFor(enemyteam, gi.boardMatrix, gameStates, True) 
        logger.debug(" Move time: %f \n",time.time() - t0)
        if END:
            logger.info(f" Fin de la partida, ganador -> {possibleWinner}")
            logger.info(" Conexion Terminada")
            client.close()
        return END, dueTo
    myTeam = client.team
    if myTeam == "black":
        initialPos = "RNBKQBNR/PPPPPPPP/8/8/8/8/pppppppp/rnbkqbnr"
        setPositionOnBoard(initialPos, gi.boardMatrix, True)
    else:
        setPositionOnBoard(initialPos, gi.boardMatrix, False)
    while not close:
        if not client.connection:
            client.close()
            print("[!] The other player cancelled the game")
            return
        # Actualizacion de tablero
        screen.fill(GRAY)
        gi.updateBoardOnScreen()
        if END:
            if getTurnOfTeam(gameMoves) == "white":
                winner = "black"
            else:
                winner = "white"
            showEndText(dueTo,gi,winner)
        else:
            # If a piece is selected the image will follow the mouse (it's printed in the screenCoord of the mouse in every frame)
            if isRealPiece(gi.selectedPiece) and not END:
                image = gi.getPieceImage(gi.selectedPiece.char)
                mousePos = pygame.mouse.get_pos()
                screen.blit(image, (mousePos[0]-gi.squareSide/2, mousePos[1]-gi.squareSide/2)) 
        
        if not myTeam == getTurnOfTeam(gameMoves) and not END:
            gi.showText(f"Waiting '{client.enemy_team}'s response", REAL_BLACK, None, screenWidth/2, screenHeight/2, 20, False)
            enemy_move = client.read_enemy_move()
            if enemy_move is not None:
                gi.selectedPiece = enemy_move[0]
                END, dueTo = move(enemy_move[1])       
                logger.info(" Jugada recibida")
       
        #--- Bucle principal de eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                client.close()
                close = True
            if event.type == pygame.VIDEORESIZE:
                size = (event.w, event.h)
                configureScreen(gi,size)
            if event.type == pygame.MOUSEBUTTONDOWN and not END and myTeam == getTurnOfTeam(gameMoves):
                clickedSquare = gi.getSquare(pygame.mouse.get_pos())
                # Miro a ver si he pinchado dentro del tablero
                if clickedSquare == None: 
                    continue
                # Si no tengo una pieza seleccionada la selecciono 
                if gi.selectedPiece == None:
                    p = gi.boardMatrix[clickedSquare[0]][clickedSquare[1]]
                    teamTurn = getTurnOfTeam(gameMoves)
                    if teamTurn == myTeam and p.team == myTeam:
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
                            logger.info(" Enviando info del mov...")
                            mov = invert_move(clickedSquare)
                            copySP = copy.deepcopy(gi.selectedPiece)
                            copySP.square = invert_move(copySP.square)        
                            client.send_move((copySP,mov))
                            END, dueTo = move(clickedSquare)     
        pygame.display.update()                                                                                                         
        # Se establecen el frame rate (fps) 
        clock.tick(60)

def playerVsIA_mode(gi, logger):
    logger.info(" Player vs AI")
    gi.reset()
    END = False
    close = False
    gameMoves = []
    gameStates = [[[]]]
    initialPos = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"
    teams = ["black", "white"]
    ai = ChessAI(choice(teams))
    
    # Encapsula las actualizaciones de variables y checkeos necesarios tras realizar un movimiento
    def move(clickedSquare):
        t0 = time.time()
        gameMoves.append((gi.selectedPiece.square, clickedSquare, gi.selectedPiece.char))
        enemyteam = gi.selectedPiece.getEnemyTeam()
        gi.moveSelectedPiece(clickedSquare)
        gameStates.append(gi.getCharBoard())
        logger.debug(" Turn of: " + getTurnOfTeam(gameMoves))
        END, dueTo = checkEndOfGameFor(enemyteam, gi.boardMatrix, gameStates, True) 
        logger.debug(" Move time: %f \n",time.time() - t0) 
        return END, dueTo
    t = 0.0  
    if ai.team == "white":
        initialPos = "RNBKQBNR/PPPPPPPP/8/8/8/8/pppppppp/rnbkqbnr"
        setPositionOnBoard(initialPos, gi.boardMatrix, True)
    else:
        setPositionOnBoard(initialPos, gi.boardMatrix, False)
    while not close:
        # Actualizacion de tablero
        screen.fill(GRAY)
        gi.updateBoardOnScreen()
        if END:
            showEndText(dueTo,gi,movingTeam)
        else:
            # If a piece is selected the image will follow the mouse (it's printed in the screenCoord of the mouse in every frame)
            if isRealPiece(gi.selectedPiece) and not END:
                image = gi.getPieceImage(gi.selectedPiece.char)
                mousePos = pygame.mouse.get_pos()
                screen.blit(image, (mousePos[0]-gi.squareSide/2, mousePos[1]-gi.squareSide/2)) 
        pygame.display.update()
        
        # Generamos movimiento de la IA
        if not END and ai.team == getTurnOfTeam(gameMoves):
            ti = time.time()
            square, piece = ai.generate_move(gi.boardMatrix)
            logger.debug(f" Computer Movement: [ {piece.char} , {square} ]")
            logger.debug(f" Tiempo en generar el movimiento {time.time()-ti}")
            waitRemainingTime(ti,t) 
            gi.eraseLastMove() 
            gi.selectedPiece = piece
            movingTeam = gi.selectedPiece.team
            gi.eraseLastMove()
            END, dueTo = move(square)  
        
        #--- Bucle principal de eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                close = True
            if event.type == pygame.VIDEORESIZE:
                size = (event.w, event.h)
                configureScreen(gi,size)
            if event.type == pygame.MOUSEBUTTONDOWN and not END:
                clickedSquare = gi.getSquare(pygame.mouse.get_pos())
                # Miro a ver si he pinchado dentro del tablero
                if clickedSquare == None: 
                    continue
                # Si no tengo una pieza seleccionada la selecciono 
                if gi.selectedPiece == None:
                    p = gi.boardMatrix[clickedSquare[0]][clickedSquare[1]]
                    teamTurn = getTurnOfTeam(gameMoves)
                    if not teamTurn == ai.team and p.team == teamTurn:
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
                            movingTeam = gi.selectedPiece.team
                            END, dueTo = move(clickedSquare)
                                                                                                                     
        # Se establecen el frame rate (fps) 
        clock.tick(60)
            
def IAvsIA_mode(gi, logger): 
    logger.info(" AI vs AI Mode")       
    gi.reset()
    END = False
    close = False
    gameMoves = []
    gameStates = [[[]]]
    initialPos = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"
    ai = ChessAI("white")
    
    def move(clickedSquare):
        t0 = time.time()
        gameMoves.append((gi.selectedPiece.square, clickedSquare, gi.selectedPiece.char))
        movingTeam = gi.selectedPiece.team
        enemyteam = gi.selectedPiece.getEnemyTeam()
        gi.moveSelectedPiece(clickedSquare)
        gameStates.append(gi.getCharBoard())
        logger.debug(" Turn of: " + getTurnOfTeam(gameMoves))
        END, dueTo = checkEndOfGameFor(enemyteam, gi.boardMatrix, gameStates, True) 
        logger.debug(" Move time: %f \n",time.time() - t0) 
        return END, dueTo
    
    t = 0.2
    setPositionOnBoard(initialPos,gi.boardMatrix, False) 
    while not close:
        # Actualizacion de tablero
        screen.fill(GRAY)
        gi.updateBoardOnScreen()
        if END:
            showEndText(dueTo,gi,movingTeam)
        pygame.display.update()
        
        # Generamos movimiento de la IA
        if not END:
            ti = time.time()
            square, piece = ai.generate_move(gi.boardMatrix)
            logger.debug(f" Computer Movement: [ {piece.char} , {square} ]")
            logger.debug(f" Tiempo en generar el movimiento {time.time()-ti}")
            waitRemainingTime(ti,t) 
            gi.eraseLastMove() 
            gi.selectedPiece = piece
            movingTeam = gi.selectedPiece.team
            gi.eraseLastMove()
            END, dueTo = move(square)  
        
            ai.team = getTurnOfTeam(gameMoves)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                close = True
            if event.type == pygame.VIDEORESIZE:
                size = (event.w, event.h)
                configureScreen(gi,size)
        # Se establecen el frame rate (fps) 
        clock.tick(60)     

# -------------------------------------------------------------------   
# -------------Inicio de la Ejecución del Programa-------------------    

logging.basicConfig(level = logging.DEBUG)
logger = logging.getLogger(__name__)

# ------Screen configuration and display-----
# The (0,0)px screenCoord is located in the left-top corner
screenWidth = 1500
screenHeight = 800
screenSize = [screenWidth, screenHeight]
screen = pygame.display.set_mode(screenSize, pygame.RESIZABLE)
pygame.display.set_caption('Chess Game')

CLOSE = False
clock = pygame.time.Clock()

gi = ChessGI(screen)

logging.info(" Openning First Screen") 
if __name__ == "__main__": 
    # ----- Pantalla para elegir el modo que se va a jugar ------
    modeSelected = False
    buttons = []
    while not modeSelected and not CLOSE:
        screen.fill(GRAY)
        buttons = showOptions(gi)  
        pygame.display.update()        
        clock.tick(60)
        
        mouseCoords = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                CLOSE = True
            if event.type == pygame.VIDEORESIZE:
                size = (event.w, event.h)
                configureScreen(gi,size)
            if event.type == pygame.MOUSEBUTTONDOWN:
                for but in buttons:
                    if but.collidepoint(pygame.mouse.get_pos()):
                        if buttons.index(but) == 0:
                            practice_mode(gi,logger)
                        elif buttons.index(but) == 1:
                            local_mode_2players(gi,logger)
                        elif buttons.index(but) == 2:
                            online_mode(gi,logger)
                        elif buttons.index(but) == 3:
                            playerVsIA_mode(gi,logger)
                        elif buttons.index(but) == 4:
                            IAvsIA_mode(gi,logger)
                        break
    # Se cierra el Juego
    logger.info(" Closing Game")
    pygame.quit()