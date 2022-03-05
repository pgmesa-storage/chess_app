
from pathlib import Path

import pygame

from chessModule import *
from .chessPiece_class import ChessPiece


dir_ = Path(__file__).parent.parent.resolve()
sound_effects_dir = 'sound_effects'
chess_sprites_dir = "chess_sprites"

class ChessGI:
    screen = None
    
    squareSide = 0
    xi = 0
    yi = 0
    
    boardMatrix = [[]]
    squaresColor = [[]]
    squares = [[]]
    pieceImages = []
    
    indecesOfAvailableMovements = []
    originalSquaresColor = []
    checkPos = (0,0)
    check = False
    lastMove = () # lastMove sigue esta estructura((0,0),(0,0),"pieceChar","color")
    selectedPiece = None
    
    move_sound = None
    capture_sound = None
    castling_sound = None

    def __init__(self,screen):
        self.screen = screen
        # ------ Graphic Board size and position configuration-----
        self.__initBoardMatrix()
        self.__initSquaresColor()
        self.__adjustBoardOnScreen()
         # ------Sound effects loads-----
        pygame.mixer.init() 
        self.move_sound = pygame.mixer.Sound(str(dir_/(sound_effects_dir+"/move_sound.wav")))
        self.move_sound = pygame.mixer.Sound(str(dir_/(sound_effects_dir+"/move_sound.wav")))
        self.capture_sound = pygame.mixer.Sound(str(dir_/(sound_effects_dir+"/capture.wav")))
        self.castling_sound = pygame.mixer.Sound(str(dir_/(sound_effects_dir+"/castling_sound.wav")))

    def reset(self):
        self.indecesOfAvailableMovements = []
        self.checkPos = (0,0)
        self.check = False
        self.lastMove = ()
        self.selectedPiece = None
        self.__init__(self.screen)
#-----------------------------------------   
# --- Inicializaciones de las matrices ---
    def __initBoardMatrix(self):
        self.boardMatrix = [" "]*8
        for i in range(8):
            self.boardMatrix[i] = [" "]*8
            for j in range(8):
                self.boardMatrix[i][j] = ChessPiece("-",(i,j))
    
    def __initSquaresColor(self):
        self.squaresColor = [" "]*8
        for i in range(8):
            self.squaresColor[i] = [" "]*8
        for i in range (8):
            for j in range(8):
                if (j+i)%2 == 0:
                    self.squaresColor[i][j] = "W"
                else: 
                    self.squaresColor[i][j] = "B"
        self.originalSquaresColor = self.copyMatrix(self.squaresColor)
    
    def __adjustBoardOnScreen(self):
        screenWidth = self.screen.get_width()
        screenHeight = self.screen.get_height()
        size = (screenWidth,screenHeight)
        self.squareSide = int(screenHeight/10)
        self.xi = int((screenWidth - self.squareSide*8)/2)
        self.yi = self.squareSide
        self.__initSquares()
        self.__loadImages()
    
    def __initSquares(self):
        self.squares = [None]*8
        side = self.squareSide
        for i in range (8):
            self.squares[i] = [None]*8 
            for j in range(8): 
                self.squares[i][j] = (self.xi + (j+1)*side, self.yi +(i+1)*side)
    
    def __loadImages(self):
        self.pieceImages = []
        names = ["rook", "knight", "bishop", "queen", "king", "pawn"]
        color = "white"
        for _ in range(2):
            for name in names:
                path = dir_/chess_sprites_dir
                fname = color + "_" + name
                fname += "_sticker.png"
                image = pygame.image.load((path/fname).open())
                image = pygame.transform.scale(image, [self.squareSide, self.squareSide])
                self.pieceImages.append(image)     
            color = "black"
# -------------------------
# --- Funciones utilies ---

    # Devuelve la fila y columna de la casilla donde ha pinchado el raton en el tablero. Devuelve None si se ha pinchado fuera de este
    def getSquare(self,screenCoords):
        for i in range(8):
            for j in range(8):
                cond1 = screenCoords[0] < self.squares[i][j][0] and screenCoords[1] < self.squares[i][j][1]
                cond2 = screenCoords[0] > self.xi and screenCoords[1] > self.yi
                if cond1 and cond2:
                    return (i,j)
        # Out of the board
        return None
    
    # Las imagenes deben tener las siguientes relaciones (editadas en paint 3D) para que se vean bien, 
    # suponiendo un squareSide = 80px:
    # Peones: height = 60px | Canvas 80x80 px  
    # Torre: height = 65px | Canvas 80x80 px 
    # Caballo: height = 67px | Canvas 80x80 px 
    # Rey y alfil: height = 70px | Canvas 80x80 px 
    # Reina: height = 75px | Canvas 80x80 px    
    def getPieceImage (self,c):
        charPieces = ['r','n','b','q','k', 'p']
        index = charPieces.index(c.lower())
        if c.islower():
            index += 6
        return self.pieceImages[index]

    def setScreen(self,screen):
        self.screen = screen
        self.__adjustBoardOnScreen()
    
    def checkValidIndex(self,i,j):
        if i > 7 or j > 7 or i < 0 or j < 0:
            return False
        return True        
               
    def copyMatrix(self, M):
        copy = [" "]*8
        for i in range(len(M)):
            copy[i] = [" "]*8
            for j in range(len(M[0])):
                copy[i][j] = M[i][j]
        return copy         
    
    def getCharBoard(self):
        board = [""]*8
        for i in range(8):
            board[i] = [""]*8
            for j in range(8):
                board[i][j] = self.boardMatrix[i][j].char
        return board
        
# --------------------------------------------
# --- Funciones para pintar en la pantalla ---

    def paintBoardOnScreen(self):
        WHITE = (226,188,157)
        BLACK = (148,96,81)
        DARK_GREEN = (100, 140, 0)
        LIGHT_GREEN = (141, 182, 0)
        YELLOW = (198,206,0)
        RED = (178,34,34)
        color = [WHITE, BLACK, DARK_GREEN, LIGHT_GREEN, YELLOW, RED]
        simbols = ["W", "B", "DG", "LG", "Y", "R"]
        side = self.squareSide
        for i in range (8):
            for j in range(8):
                col = color[simbols.index(self.squaresColor[j][i])]
                pygame.draw.rect(self.screen, col, [self.xi + i*side, self.yi + j*side,side,side])  
        
    def paintPiecesOnScreen(self):
        for i in range(8):
            for j in range(8):
                piece = self.boardMatrix[i][j]
                if not piece.char == "-":
                    image = self.getPieceImage(piece.char)
                    self.screen.blit(image, (self.xi + j*self.squareSide , self.yi + i*self.squareSide)) 
                    
    def updateBoardOnScreen(self):
        self.paintBoardOnScreen()
        self.paintPiecesOnScreen()
        
# ----------------------------------------------------------------------        
# --- Funciones para actualizar la matriz de colores de cada casilla ---

    def paintAvailableMovementsOf(self,piece):
        moves = piece.getMoves()
        self.indecesOfAvailableMovements = []
        self.squaresColor[piece.row][piece.colum] = "Y"
        self.indecesOfAvailableMovements.append((piece.row,piece.colum))
        if piece.char.lower() == 'p':
            if piece.team =="white":
                dr = -1
                if piece.inverted:
                    dr = 1
            else:
                dr = 1
                if piece.inverted:
                    dr = -1
            options = [(1*dr,0), (2*dr,0), (1*dr,-1), (1*dr,1)]
            colors = ["LG","DG","DG","DG"]
            for opt in options:
                row  = piece.row + opt[0]
                colum = piece.colum + opt[1]
                if self.checkValidIndex(row,colum) and ((row,colum) in moves):
                    i = options.index(opt)
                    self.squaresColor[row][colum] = colors[i]
                    self.indecesOfAvailableMovements.append((row,colum))
        if piece.char.lower() == 'r' or piece.char.lower() == 'q':
            ind = 0
            Nones = 0
            movesInBetweenNones = []
            lastIndex = moves.index(None)
            for i in range(4):
                index = moves.index(None,lastIndex+1)
                movesInBetweenNones.insert(0,index-lastIndex-1)
                lastIndex = index
            switch = 0
            for i in range(len(moves)):
                if Nones == 5:
                    break
                i = len(moves)-1-i
                if movesInBetweenNones[ind]%2 == 0:
                    if switch%2 == 0:
                        color = "DG"
                    else: 
                        color = "LG"
                else:
                    if switch%2 == 0:
                        color = "LG"
                    else: 
                        color = "DG"
                if not moves[i] == None:
                    row = moves[i][0]
                    colum = moves[i][1]
                    self.squaresColor[row][colum] = color
                    self.indecesOfAvailableMovements.append((row,colum))
                    switch += 1
                else:
                    Nones += 1 
                    if Nones - 2 < 0:
                        ind = 0
                    else:
                        ind += 1
                        switch = 0
                    
        if piece.char.lower() == 'b' or piece.char.lower() == 'n'or piece.char.lower() == 'q':
            for move in moves:
                if move == None:
                    break
                row = move[0]
                colum = move[1]
                self.squaresColor[row][colum] = "DG"
                self.indecesOfAvailableMovements.append((row,colum))
        elif piece.char.lower() == 'k':
            for move in moves:
                if not move == None:
                    row = move[0]
                    colum = move[1]
                    if not moves.index(move) > 8:
                        if moves.index(move)%2 == 0:
                            color = "DG"
                        else:
                            color = "LG"
                    else:
                        color = "DG"
                    self.squaresColor[row][colum] = color
                    self.indecesOfAvailableMovements.append((row,colum)) 

    def eraseAvailableMovements(self):
        for ind in self.indecesOfAvailableMovements:
            self.squaresColor[ind[0]][ind[1]] = self.originalSquaresColor[ind[0]][ind[1]]
        
    def paintLastMove(self):
        if not len(self.lastMove) == 0:
            self.squaresColor[self.lastMove[0][0]][self.lastMove[0][1]] = "Y"
            self.squaresColor[self.lastMove[1][0]][self.lastMove[1][1]] = self.lastMove[3]
    
    def eraseLastMove(self):
        if not len(self.lastMove) == 0:
            self.squaresColor[self.lastMove[0][0]][self.lastMove[0][1]] = self.originalSquaresColor[self.lastMove[0][0]][self.lastMove[0][1]]
            self.squaresColor[self.lastMove[1][0]][self.lastMove[1][1]] = self.originalSquaresColor[self.lastMove[1][0]][self.lastMove[1][1]]
      
    def paintCheck(self):
        self.squaresColor[self.checkPos[0]][self.checkPos[1]] = "R"
        
    def eraseCheck(self):
        self.squaresColor[self.checkPos[0]][self.checkPos[1]] = self.originalSquaresColor[self.checkPos[0]][self.checkPos[1]]
    
# -------------------------------------------------      
# --- Funciones para escribir texto en pantalla ---
         
    def showText(self,text,color, backgroundColor, x,y, fontSize, getRect):
        font = pygame.font.Font('freesansbold.ttf', fontSize)
        if backgroundColor == None:  
            text = font.render(text, True, color)
        else:
            text = font.render(text, True, color, backgroundColor)
        textRect = text.get_rect()
        textRect.center = (x, y)
        self.screen.blit(text,textRect)
        if getRect:
            return textRect
             
# -------------------------------------------------------------------    
# ----------------FUNCTIONS FOR PRINTING IN CONSOLE------------------
        
    def printMatrix(self,M):
        for row in M:
            print(row)
        print()
    
    def printChess(self):
        self.printMatrix(self.squaresColor)
        for i in range(8):
            row = []
            for j in range(8):
                row.append(str(self.boardMatrix[i][j]))
            print(row)
        print()

# -------------------------------------------------------------------    
# ----------------Functions for animating Moves----------------------
    # Realiza la accion de coger una pieza del tablero y que la accion aparezca en pantalla, pintando sus posibles movimientos
    # y observandose que la pieza ya no esta colocada en esa casilla
    def takePieceAt(self, square):
        # Se mira que pieza se va a coger
        piece = self.boardMatrix[square[0]][square[1]]
        if isRealPiece(piece):
            self.eraseLastMove()
            # Levantamos la Pieza para que no aparezca pintada en el tablero
            self.boardMatrix[square[0]][square[1]] = ChessPiece("-",square)
            # Calculamos sus posibles movimientos 
            piece.calcLegalMovesOnBoard(self.boardMatrix)
            # Filtramos los movimientos para que sean legales viendo si hay jaques o su mov puede provocar uno
            filterMoves(piece, self.boardMatrix)
            self.paintAvailableMovementsOf(piece)
            self.selectedPiece = piece

    # No mueve la pieza, la deja en su sitio, borra los posibles movimientos
    def dontMoveSelectedPice(self):
        square = self.selectedPiece.square
        self.boardMatrix[square[0]][square[1]] = self.selectedPiece
        self.eraseAvailableMovements()
        self.paintLastMove()
        if self.check:
            self.paintCheck()
        self.selectedPiece = None
    
    def moveSelectedPiece(self, finalSquare):
        # Se borran las casillas marcadas como posibles movimientos, se mira que pieza hay donde nos vamos a mover y se guarda la 
        # posicion inicial antes de mover
        self.eraseAvailableMovements()
        startSquare = self.selectedPiece.square
        # Se guarda aqui el char por si hay coronacion en makeMove() y el char cambia a reina u otro.
        charPiece = self.selectedPiece.char
        captured, castled = makeMove(self.selectedPiece, finalSquare, self.boardMatrix)    
        if captured:
            pygame.mixer.Sound.play(self.capture_sound)
            color = "LG"
        else:
            if castled:
                pygame.mixer.Sound.play(self.castling_sound)
            else:
                pygame.mixer.Sound.play(self.move_sound)      
            color = "DG"   
        self.squaresColor[finalSquare[0]][finalSquare[1]] = color
        # Si he movido o capturado significa que el movimiento era valido, y por tanto si el equipo de esta pieza estaba en
        # jaque ahora no lo puede estar
        if self.check:
            self.check = False
            self.eraseCheck()
        # Ahora se comprueba si el equipo de esta pieza esta dando jaque al enemigo debido a este movimiento
        self.check, checkPos = teamIsChekingEnemyKing(self.selectedPiece.team, self.boardMatrix)
        if self.check:
            self.checkPos = checkPos
            self.paintCheck()
        # Guardamos el ultimo movimiento en la clase ChessBoard y en la variable gameMoves y lo pintamos (Tambien almacenamos la
        # posicon del tablero de cada juagada)
        self.lastMove = (startSquare, finalSquare,charPiece,color)
        self.paintLastMove()
        self.selectedPiece = None

# -------------------------------------------------------------------------------------
# ----------------Functions for inverting the board on the screen----------------------

    def rotateMatrix_180(self, matrix):
        M = len(matrix)
        out = [""]*M
        for i in range(M):
            N = len(matrix[i])
            out[i] = [""]*N
            for j in range(N):
                out[i][N-1-j] = matrix[M-1-i][j]  
        return out
    
    def invert(self,inverted):
        # invertimos squaresColor y boardMatrix y ponemos a todas las piezas el invert a true o false y actualizamos
        # su posicion (tambien hay que invertir el Last Move)
        self.boardMatrix = self.rotateMatrix_180(self.boardMatrix)
        self.squaresColor = self.rotateMatrix_180(self.squaresColor)
        for row in self.boardMatrix:
            for p in row:
                if isRealPiece(p):
                    p.inverted = inverted
                    p.square = self.invertSquare(p.square)
                    p.row = p.square[0]
                    p.colum = p.square[1]
        self.lastMove = (self.invertSquare(self.lastMove[0]),self.invertSquare(self.lastMove[1]),self.lastMove[2], self.lastMove[3])
        self.checkPos = self.invertSquare(self.checkPos)
                    
    def invertSquare(self, move):
        newMove = (7 - move[0],7 - move[1])
        return newMove
        