
import copy

class ChessPiece:
    
    char = None
    team = None
    row = None
    colum = None
    square = (row,colum)
    moves = [] 
    moveMatrix = [[]]
    inPassing = False
    
    def __init__(self,char,square,*inverted):
        if not len(inverted) == 0:
            self.inverted = inverted[0]
        self.char = char
        if self.char.islower():
            self.team = "black"
        elif self.char.isupper():
            self.team = "white"
        self.row = square[0]
        self.colum = square[1]
        self.square = square
        self.initMoveMartrix()  
        if self.char.lower() == 'k' or self.char.lower() == 'r':  
            self.castling = True  
    
    def initMoveMartrix(self):
        self.moveMatrix = [" "]*8
        for i in range(8):
            self.moveMatrix[i] = [" "]*8
    
    def addMove(self, move):
        self.moves.append(move)
        if not move == None:
            self.moveMatrix[move[0]][move[1]] = "+"
        
    def resetMoves(self):
        length = len(self.moves)
        for i in range(length):
            i = length -1 -i
            if not self.moves[i] == None:
                self.moveMatrix[self.moves[i][0]][self.moves[i][1]] = " "
            self.moves.pop(i)
        # No se porque no funciona bien lo de arriba para vaciar un array. Funciona si uso
        # lo de abajo
        self.moves = []
        
    def getMoves(self):
        return self.moves    
    
    def checkValidIndex(self,i,j):
        if i > 7 or j > 7 or i < 0 or j < 0:
            return False
        return True  
    
    def isEnemy(self,color):
        if self.char == "-":
            return False
        if not self.team == color:
            return True
        return False
    
    def getEnemyTeam(self):
        if self.team == "white":
            return "black"
        else: 
            return "white"
    
    def updateState(self,square):
        if self.char.lower() == 'p' and abs(self.row-square[0]) == 2:
            self.inPassing = True
        self.__init__(self.char,square, self.inverted)
        if self.char.lower() == 'k' or self.char.lower() == 'r':  
            self.castling = False
        self.resetMoves()
    
    def __str__(self):
        return self.char
    
    def legal(self,board,row,colum):
        if self.checkValidIndex(row,colum):
            if board[row][colum].char == "-":
                return (True,False)
            elif board[row][colum].isEnemy(self.team):
                return (True,True)
            else:
                return (False,True)
        else:
            return False,True
        
    def calcStraightLines(self, board):   
    # --- Vertical ---
        # Hacia abajo
        self.addMove(None)
        for i in range(self.row+1, 8):
            cond, end = self.legal(board,i,self.colum)
            if cond:
                self.addMove((i,self.colum))
                if end:
                    break
            else:
                break 
        # Añadimos un None para que la funcion de pintar movimientos sepa cuando dejar de pintar hacia esta direccion
        self.addMove(None)
        # Hacia arriba
        for i in range(8-self.row,8):
            cond, end = self.legal(board,7-i,self.colum)
            if cond:
                self.addMove((7-i,self.colum))
                if end:
                    break
            else:
                break 
    # --- Horizontal ---
        self.addMove(None)  
        # Hacia la derecha
        for j in range(self.colum+1, 8):
            cond, end = self.legal(board,self.row,j)
            if cond:
                self.addMove((self.row,j))
                if end:
                    break
            else:
                break
        self.addMove(None)
        # Hacia la izquierda (Desde la perspectiva de mirar al tablero)
        for j in range(8-self.colum,8):
            cond, end = self.legal(board,self.row,7-j)
            if cond:
                self.addMove((self.row,7-j))
                if end:
                    break
            else:
                break
        self.addMove(None)
        
        
    def calcDiagonalLines(self, board):
    # ---DIAGONAL 1---
        # Hacia abajo a la derecha
        if self.row >= self.colum:
            init = self.row
        else: 
            init = self.colum
        for i in range(1,8-init):
            cond, end = self.legal(board,self.row+i,self.colum+i)
            if cond:
                self.addMove((self.row+i,self.colum+i))
                if end:
                    break
            else:
                break 
        # Hacia arriba a la izquierda
        if self.row <= self.colum:
            init = self.row
        else: 
            init = self.colum
        for i in range(1,init+1):
            cond, end = self.legal(board,self.row-i,self.colum-i)
            if cond:
                self.addMove((self.row-i,self.colum-i))
                if end:
                    break
            else:
                break
    # ---DIAGONAL 2--- (Para esta diagonal hacemos un cambio de coordenadas y ponemos el 0,0 en la esquina 7,0,
    # los indices estan al reves hay que corregir)
        # Hacia abajo a la izquierda 
        row = self.row
        colum = 7 - self.colum
        if row >= colum:
            init = row
        else: 
            init = colum
        for i in range(1,8-init):
            newColum = 7 - colum - i
            newRow = row + i
            cond, end = self.legal(board,newRow,newColum)
            if cond:
                self.addMove((newRow,newColum))
                if end:
                    break
            else:
                break 
        # Hacia arriba a la derecha
        row = self.row
        colum = 7 - self.colum
        if row <= colum:
            init = row
        else: 
            init = colum   
        for i in range(1,init + 1):
            newColum = 7 - colum + i
            newRow = row - i
            cond, end = self.legal(board,newRow,newColum)
            if cond:
                self.addMove((newRow,newColum))
                if end:
                    break
            else:
                break
    def calcKnightMove(self,board):
        # Usando lineas Horizontales
        for i in range(2):
            if i == 1:
                i = -4
            for j in range(2):
                if j == 1:
                    j = -2
                cond, end = self.legal(board,self.row+1+j, self.colum+2+i)
                if cond:
                    self.addMove((self.row+1+j, self.colum+2+i))
        # Usando lineas Verticales
        for i in range(2):
            if i == 1:
                i = -4
            for j in range(2):
                if j == 1:
                    j = -2
                cond, end = self.legal(board,self.row+2+i, self.colum+1+j)
                if cond:
                    self.addMove((self.row+2+i, self.colum+1+j))
    
    def calcInPassing(self,board,colum):
        if self.char.lower() == 'p':
            if self.team == "white":
                validRow = 3
                if self.inverted:
                    validRow = 4
            else:
                validRow = 4
                if self.inverted:
                    validRow = 3
               
        if self.checkValidIndex(self.row,colum) and self.row == validRow:
            p = board[self.row][colum]
            if p.char.lower() == 'p' and self.isEnemy(p.team) and p.inPassing:
                return True
        return False
    
    def calcPawnMove(self,board):
        double = False
        ups = [-1,1]
        rows = [6,1]
        if self.inverted:
            ups = ups[::-1]
            rows = rows[::-1]
        if self.team == "black":
            up_down = ups[1]
            if self.row == rows[1]:
                double = True 
        else:
            up_down = ups[0]
            if self.row == rows[0]:
                double = True 
                 
        if self.checkValidIndex(self.row + up_down, self.colum - 1):
            if board[self.row + up_down][self.colum - 1].isEnemy(self.team) or self.calcInPassing(board,self.colum - 1):
                self.addMove((self.row + up_down, self.colum - 1))

        if self.checkValidIndex(self.row + up_down, self.colum):     
            if board[self.row + up_down][self.colum].char == "-":
                self.addMove((self.row + up_down, self.colum))
                if double and board[self.row+ up_down*2][self.colum].char == "-": 
                    self.addMove((self.row + up_down*2, self.colum))
            
        if self.checkValidIndex(self.row + up_down, self.colum + 1):
            if board[self.row + up_down][self.colum + 1].isEnemy(self.team) or self.calcInPassing(board, self.colum + 1):
                self.addMove((self.row + up_down, self.colum + 1))
                
    # Mira a ver si ha habido coronacion de algun peon.
    # Return -- Devuelve True si algun peon ha alcanzado la coronacion y un segundo valor indicando la representacion en char 
    # de la pieza por la que se va a coronar
    def checkCrown(self):
        crownPos = [0, 7]
        if self.inverted:
            crownPos = crownPos[::-1]
        if self.char.lower() == 'p':
            if self.team == "white":
                if self.square[0] == crownPos[0]:
                    return True, 'Q'
            else:
                if self.square[0] == crownPos[1]:
                    return True, 'q'
        return False, None
    
    def positionAttacked_by_enemyTeam(self,board,position):
        copyboard = copy.deepcopy(board)
        mycopy = copy.deepcopy(self)
        copyboard[position[0]][position[1]] = mycopy
        copyboard[self.row][self.colum] = ChessPiece("-",self.square)
        for i in range(8):
            for j in range(8):
                piece = copyboard[i][j]
                if not piece.char == "-" and piece.isEnemy(self.team):
                    if piece.char.lower() == 'k' and not piece == self:
                        piece.calcAreaKing()
                    else:        
                        piece.calcLegalMovesOnBoard(copyboard)     
                    possibleAttacks = piece.getMoves()                      
                    if position in possibleAttacks:
                        return True
        return False
    
    def calcAreaKing(self):
        self.resetMoves()
        for i in range(3):
            for j in range(3):
                row = self.row-1+i
                colum = self.colum-1+j
                if self.checkValidIndex(row,colum):  
                    self.addMove((row,colum))    
                             
    def calcCastling(self,board):
        # Enroque por la derecha e izquierda
        for k in range(2):
            notAttacked = 0
            piece = board[self.row][7*(1-k)]
            if piece.char.lower() == 'r' and piece.castling:
                for i in range(3):
                    if k == 1:
                        i = i*-1
                        if not board[self.row][7*(1-k)+1].char == "-":
                            break
                    row = self.row
                    colum = self.colum + i
                    if board[row][colum].char == "-" and not self.positionAttacked_by_enemyTeam(board,(row,colum)):
                        notAttacked += 1
                    else:
                        break
                    # Solo entrara aqui si las 3 casillas estan libres y no atacadas y colum sera dos casillas
                    # a la derecha o izquierda del rey
                    if notAttacked == 3:
                        self.addMove((row,colum))
    
    def calcKingMove(self,board):
        for i in range(3):
            for j in range(3):
                row = self.row-1+i
                colum = self.colum-1+j
                if row == self.row and colum == self.colum:
                    self.addMove(None)
                    continue
                cond, end = self.legal(board,row, colum)
                if cond:
                    attacked = self.positionAttacked_by_enemyTeam(board,(row, colum))
                    if not attacked:
                        self.addMove((row,colum))
                    else:
                        self.addMove(None)
                else:
                    self.addMove(None)
        if self.castling:
            self.calcCastling(board)
    
    def calcLegalMovesOnBoard (self, board):
        self.resetMoves()
        pieces = ['r','n','b','q','k', 'p']
        if self.char.lower() == 'r':
            self.calcStraightLines(board)

        elif self.char.lower() == 'q':
            self.calcDiagonalLines(board)
            self.calcStraightLines(board)
     
        elif self.char.lower() == 'b':
            self.calcDiagonalLines(board)
         
        elif self.char.lower() == 'p':
            self.calcPawnMove(board)
            
        elif self.char.lower() == 'k': 
            self.calcKingMove(board)
            
        elif self.char.lower() == 'n':
            self.calcKnightMove(board)
        