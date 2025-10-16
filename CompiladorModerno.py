import re
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum
import threading

class TipoToken(Enum):
    """Tipos de tokens en Python"""
    PALABRA_RESERVADA = "PALABRA_RESERVADA"
    IDENTIFICADOR = "IDENTIFICADOR"
    NUMERO = "NUMERO"
    STRING = "STRING"
    OPERADOR = "OPERADOR"
    DELIMITADOR = "DELIMITADOR"
    COMENTARIO = "COMENTARIO"
    NUEVA_LINEA = "NUEVA_LINEA"
    INDENTACION = "INDENTACION"
    EOF = "EOF"

class TipoError(Enum):
    """Tipos de errores detectables"""
    LEXICO = "LÉXICO"
    SINTACTICO = "SINTÁCTICO"
    SEMANTICO = "SEMÁNTICO"

@dataclass
class Token:
    """Representación de un token"""
    tipo: TipoToken
    valor: str
    linea: int
    columna: int

@dataclass
class Error:
    """Representación de un error"""
    tipo: TipoError
    mensaje: str
    linea: int
    columna: int
    sugerencia: Optional[str] = None

class AnalizadorLexico:
    """
    ANALIZADOR LÉXICO COMPLETO CON REGLAS GRAMATICALES DE PYTHON
    ===========================================================
    """
    
    def __init__(self):
        # REGLAS GRAMATICALES OFICIALES DE PYTHON
        self.palabras_reservadas = {
            'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await',
            'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 
            'except', 'finally', 'for', 'from', 'global', 'if', 'import',
            'in', 'is', 'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise',
            'return', 'try', 'while', 'with', 'yield'
        }
        
        self.operadores = {
            '+', '-', '*', '**', '/', '//', '%', '@',
            '<<', '>>', '&', '|', '^', '~',
            '<', '>', '<=', '>=', '==', '!=',
            '=', '+=', '-=', '*=', '/=', '//=', '%=', '@=',
            '&=', '|=', '^=', '>>=', '<<=', '**='
        }
        
        self.delimitadores = {
            '(', ')', '[', ']', '{', '}',
            ',', ':', '.', ';', '@', '=', '->', 
            '+=', '-=', '*=', '/=', '//=', '%=', '@=',
            '&=', '|=', '^=', '>>=', '<<=', '**=', '=='
        }
        
        # Patrones de tokens válidos según gramática Python
        self.patron_identificador = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
        self.patron_numero_entero = re.compile(r'^[+-]?(?:0[bB][01]+|0[oO][0-7]+|0[xX][0-9a-fA-F]+|\d+)$')
        self.patron_numero_float = re.compile(r'^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$')
        self.patron_string = re.compile(r'^(?:""".*?"""|\'\'\'.*?\'\'\'|"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')$', re.DOTALL)
    
    def tokenizar(self, codigo: str) -> List[Token]:
        """Tokeniza el código siguiendo las reglas exactas de Python"""
        tokens = []
        errores = []
        lineas = codigo.split('\n')
        
        for num_linea, linea in enumerate(lineas, 1):
            tokens_linea, errores_linea = self._tokenizar_linea(linea, num_linea)
            tokens.extend(tokens_linea)
            errores.extend(errores_linea)
        
        return tokens, errores
    
    def _tokenizar_linea(self, linea: str, num_linea: int) -> tuple:
        """Tokeniza una línea específica"""
        tokens = []
        errores = []
        
        if not linea.strip():
            return tokens, errores
        
        # Detectar indentación
        indentacion = len(linea) - len(linea.lstrip())
        if indentacion > 0:
            if not indentacion % 4 == 0:
                errores.append(Error(
                    TipoError.LEXICO,
                    f"Indentación incorrecta: debe ser múltiplo de 4 espacios",
                    num_linea, 1,
                    "Use 4 espacios para cada nivel de indentación"
                ))
            tokens.append(Token(TipoToken.INDENTACION, ' ' * indentacion, num_linea, 1))
        
        contenido = linea.strip()
        i = 0
        
        while i < len(contenido):
            # Saltar espacios
            if contenido[i].isspace():
                i += 1
                continue
            
            # Comentarios
            if contenido[i] == '#':
                comentario = contenido[i:]
                tokens.append(Token(TipoToken.COMENTARIO, comentario, num_linea, i + 1))
                break
            
            # Strings
            if contenido[i] in ['"', "'"] or (i < len(contenido) - 2 and contenido[i:i+3] in ['"""', "'''"]):
                token_str, nueva_pos, error = self._extraer_string(contenido, i, num_linea)
                if error:
                    errores.append(error)
                else:
                    tokens.append(token_str)
                i = nueva_pos
                continue
            
            # Números
            if contenido[i].isdigit() or (contenido[i] == '.' and i + 1 < len(contenido) and contenido[i + 1].isdigit()):
                token_num, nueva_pos, error = self._extraer_numero(contenido, i, num_linea)
                if error:
                    errores.append(error)
                else:
                    tokens.append(token_num)
                i = nueva_pos
                continue
            
            # Identificadores y palabras reservadas
            if contenido[i].isalpha() or contenido[i] == '_':
                token_id, nueva_pos, error = self._extraer_identificador(contenido, i, num_linea)
                if error:
                    errores.append(error)
                else:
                    tokens.append(token_id)
                i = nueva_pos
                continue
            
            # Operadores y delimitadores
            token_op, nueva_pos, error = self._extraer_operador(contenido, i, num_linea)
            if error:
                errores.append(error)
            elif token_op:
                tokens.append(token_op)
                i = nueva_pos
                continue
            
            # Carácter no reconocido
            errores.append(Error(
                TipoError.LEXICO,
                f"Carácter no válido: '{contenido[i]}'",
                num_linea, i + 1,
                "Elimine o reemplace el carácter inválido"
            ))
            i += 1
        
        return tokens, errores
    
    def _extraer_string(self, contenido: str, inicio: int, num_linea: int) -> tuple:
        """Extrae strings siguiendo reglas de Python"""
        if inicio + 2 < len(contenido) and contenido[inicio:inicio+3] in ['"""', "'''"]:
            # String multilínea
            quote = contenido[inicio:inicio+3]
            i = inicio + 3
            valor = quote
            
            while i < len(contenido) - 2:
                if contenido[i:i+3] == quote:
                    valor += contenido[i:i+3]
                    return Token(TipoToken.STRING, valor, num_linea, inicio + 1), i + 3, None
                valor += contenido[i]
                i += 1
            
            return None, i, Error(
                TipoError.LEXICO,
                f"String multilínea sin cerrar",
                num_linea, inicio + 1,
                f"Cierre el string con {quote}"
            )
        else:
            # String normal
            quote = contenido[inicio]
            i = inicio + 1
            valor = quote
            
            while i < len(contenido):
                if contenido[i] == quote:
                    if i == 0 or contenido[i-1] != '\\':
                        valor += contenido[i]
                        return Token(TipoToken.STRING, valor, num_linea, inicio + 1), i + 1, None
                elif contenido[i] == '\n':
                    return None, i, Error(
                        TipoError.LEXICO,
                        "String sin cerrar antes de nueva línea",
                        num_linea, inicio + 1,
                        f"Cierre el string con {quote}"
                    )
                valor += contenido[i]
                i += 1
            
            return None, i, Error(
                TipoError.LEXICO,
                "String sin cerrar al final de línea",
                num_linea, inicio + 1,
                f"Cierre el string con {quote}"
            )
    
    def _extraer_numero(self, contenido: str, inicio: int, num_linea: int) -> tuple:
        """Extrae números siguiendo reglas de Python"""
        i = inicio
        valor = ""
        tiene_punto = False
        es_cientifico = False
        
        # Manejar signo
        if contenido[i] in '+-':
            valor += contenido[i]
            i += 1
        
        # Números especiales (binario, octal, hexadecimal)
        if i < len(contenido) - 1 and contenido[i] == '0':
            if contenido[i + 1].lower() in 'box':
                prefijo = contenido[i:i+2].lower()
                valor += contenido[i:i+2]
                i += 2
                
                if prefijo == '0b':
                    # Binario
                    while i < len(contenido) and contenido[i] in '01_':
                        if contenido[i] != '_':
                            valor += contenido[i]
                        i += 1
                elif prefijo == '0o':
                    # Octal
                    while i < len(contenido) and contenido[i] in '01234567_':
                        if contenido[i] != '_':
                            valor += contenido[i]
                        i += 1
                elif prefijo == '0x':
                    # Hexadecimal
                    while i < len(contenido) and contenido[i].lower() in '0123456789abcdef_':
                        if contenido[i] != '_':
                            valor += contenido[i]
                        i += 1
                
                if len(valor) == 2:  # Solo prefijo sin dígitos
                    return None, i, Error(
                        TipoError.LEXICO,
                        f"Número {prefijo} incompleto",
                        num_linea, inicio + 1,
                        f"Agregue dígitos después de {prefijo}"
                    )
                
                return Token(TipoToken.NUMERO, valor, num_linea, inicio + 1), i, None
        
        # Número decimal normal
        while i < len(contenido):
            char = contenido[i]
            
            if char.isdigit():
                valor += char
            elif char == '.' and not tiene_punto and not es_cientifico:
                valor += char
                tiene_punto = True
            elif char.lower() == 'e' and not es_cientifico:
                valor += char
                es_cientifico = True
                i += 1
                if i < len(contenido) and contenido[i] in '+-':
                    valor += contenido[i]
                    i += 1
                continue
            elif char == '_':
                # Separador de miles (válido en Python 3.6+)
                pass
            else:
                break
            i += 1
        
        # Validar formato del número
        numero_sin_separadores = valor.replace('_', '')
        
        if tiene_punto or es_cientifico:
            if not self.patron_numero_float.match(numero_sin_separadores):
                return None, i, Error(
                    TipoError.LEXICO,
                    f"Formato de número decimal inválido: {valor}",
                    num_linea, inicio + 1,
                    "Corrija el formato del número decimal"
                )
        else:
            if not self.patron_numero_entero.match(numero_sin_separadores):
                return None, i, Error(
                    TipoError.LEXICO,
                    f"Formato de número entero inválido: {valor}",
                    num_linea, inicio + 1,
                    "Corrija el formato del número entero"
                )
        
        return Token(TipoToken.NUMERO, valor, num_linea, inicio + 1), i, None
    
    def _extraer_identificador(self, contenido: str, inicio: int, num_linea: int) -> tuple:
        """Extrae identificadores siguiendo reglas de Python"""
        i = inicio
        valor = ""
        
        # Primer carácter debe ser letra o _
        if not (contenido[i].isalpha() or contenido[i] == '_'):
            return None, i + 1, Error(
                TipoError.LEXICO,
                f"Identificador inválido: no puede empezar con '{contenido[i]}'",
                num_linea, inicio + 1,
                "Los identificadores deben empezar con letra o guión bajo"
            )
        
        # Extraer el identificador completo
        while i < len(contenido) and (contenido[i].isalnum() or contenido[i] == '_'):
            valor += contenido[i]
            i += 1
        
        # Validar con expresión regular
        if not self.patron_identificador.match(valor):
            return None, i, Error(
                TipoError.LEXICO,
                f"Identificador inválido: {valor}",
                num_linea, inicio + 1,
                "Use solo letras, números y guiones bajos"
            )
        
        # Verificar si es palabra reservada
        tipo = TipoToken.PALABRA_RESERVADA if valor in self.palabras_reservadas else TipoToken.IDENTIFICADOR
        
        return Token(tipo, valor, num_linea, inicio + 1), i, None
    
    def _extraer_operador(self, contenido: str, inicio: int, num_linea: int) -> tuple:
        """Extrae operadores y delimitadores"""
        # Intentar operadores de 3 caracteres
        if inicio + 2 < len(contenido):
            tres_chars = contenido[inicio:inicio+3]
            if tres_chars in ['>>>', '<<=',' **=']:
                tipo = TipoToken.OPERADOR if tres_chars in self.operadores else TipoToken.DELIMITADOR
                return Token(tipo, tres_chars, num_linea, inicio + 1), inicio + 3, None
        
        # Intentar operadores de 2 caracteres
        if inicio + 1 < len(contenido):
            dos_chars = contenido[inicio:inicio+2]
            if dos_chars in self.operadores or dos_chars in self.delimitadores:
                tipo = TipoToken.OPERADOR if dos_chars in self.operadores else TipoToken.DELIMITADOR
                return Token(tipo, dos_chars, num_linea, inicio + 1), inicio + 2, None
        
        # Operadores de 1 carácter
        un_char = contenido[inicio]
        if un_char in self.operadores or un_char in self.delimitadores:
            tipo = TipoToken.OPERADOR if un_char in self.operadores else TipoToken.DELIMITADOR
            return Token(tipo, un_char, num_linea, inicio + 1), inicio + 1, None
        
        return None, inicio + 1, Error(
            TipoError.LEXICO,
            f"Símbolo no reconocido: '{un_char}'",
            num_linea, inicio + 1,
            "Use solo operadores y delimitadores válidos de Python"
        )

class AnalizadorSintactico:
    """
    ANALIZADOR SINTÁCTICO COMPLETO SEGÚN GRAMÁTICA DE PYTHON
    ========================================================
    """
    
    def __init__(self):
        self.tokens = []
        self.posicion = 0
        self.errores = []
        
        # Reglas sintácticas de Python
        self.estructuras_control = {'if', 'elif', 'else', 'for', 'while', 'try', 'except', 'finally', 'with'}
        self.declaraciones = {'def', 'class', 'import', 'from'}
        self.sentencias = {'return', 'break', 'continue', 'pass', 'raise', 'assert', 'del', 'global', 'nonlocal'}
    
    def analizar(self, tokens: List[Token]) -> List[Error]:
        """Analiza la sintaxis completa del código"""
        self.tokens = tokens
        self.posicion = 0
        self.errores = []
        
        if not tokens:
            return self.errores
        
        try:
            self._analizar_programa()
        except Exception as e:
            self.errores.append(Error(
                TipoError.SINTACTICO,
                f"Error crítico en análisis sintáctico: {str(e)}",
                1, 1,
                "Revise la estructura general del código"
            ))
        
        return self.errores
    
    def _token_actual(self) -> Optional[Token]:
        """Obtiene el token actual"""
        if self.posicion < len(self.tokens):
            return self.tokens[self.posicion]
        return None
    
    def _avanzar(self):
        """Avanza al siguiente token"""
        if self.posicion < len(self.tokens):
            self.posicion += 1
    
    def _token_siguiente(self) -> Optional[Token]:
        """Obtiene el siguiente token sin avanzar"""
        if self.posicion + 1 < len(self.tokens):
            return self.tokens[self.posicion + 1]
        return None
    
    def _analizar_programa(self):
        """Analiza el programa completo"""
        while self._token_actual():
            if self._token_actual().tipo == TipoToken.EOF:
                break
            
            if self._token_actual().tipo in [TipoToken.NUEVA_LINEA, TipoToken.INDENTACION, TipoToken.COMENTARIO]:
                self._avanzar()
                continue
            
            self._analizar_sentencia()
    
    def _analizar_sentencia(self):
        """Analiza una sentencia"""
        token = self._token_actual()
        if not token:
            return
        
        if token.tipo == TipoToken.PALABRA_RESERVADA:
            if token.valor == 'def':
                self._analizar_definicion_funcion()
            elif token.valor == 'class':
                self._analizar_definicion_clase()
            elif token.valor in ['if', 'elif']:
                self._analizar_if()
            elif token.valor == 'else':
                self._analizar_else()
            elif token.valor == 'for':
                self._analizar_for()
            elif token.valor == 'while':
                self._analizar_while()
            elif token.valor == 'try':
                self._analizar_try()
            elif token.valor == 'except':
                self._analizar_except()
            elif token.valor == 'finally':
                self._analizar_finally()
            elif token.valor == 'with':
                self._analizar_with()
            elif token.valor in ['import', 'from']:
                self._analizar_import()
            elif token.valor in self.sentencias:
                self._analizar_sentencia_simple()
            else:
                self._avanzar()
        else:
            # Expresión o asignación
            self._analizar_expresion_o_asignacion()
    
    def _analizar_definicion_funcion(self):
        """Analiza definición de función: def nombre(parámetros):"""
        self._avanzar()  # consumir 'def'
        
        # Verificar nombre de función
        token_nombre = self._token_actual()
        if not token_nombre or token_nombre.tipo != TipoToken.IDENTIFICADOR:
            self.errores.append(Error(
                TipoError.SINTACTICO,
                "Se esperaba nombre de función después de 'def'",
                token_nombre.linea if token_nombre else 1,
                token_nombre.columna if token_nombre else 1,
                "Agregue un nombre válido para la función"
            ))
            return
        
        self._avanzar()  # consumir nombre
        
        # Verificar paréntesis de apertura
        token_paren = self._token_actual()
        if not token_paren or token_paren.valor != '(':
            self.errores.append(Error(
                TipoError.SINTACTICO,
                "Se esperaba '(' después del nombre de función",
                token_paren.linea if token_paren else token_nombre.linea,
                token_paren.columna if token_paren else token_nombre.columna,
                "Agregue paréntesis de apertura '('"
            ))
            return
        
        self._avanzar()  # consumir '('
        
        # Analizar parámetros
        self._analizar_parametros_funcion()
        
        # Verificar paréntesis de cierre
        token_paren_cierre = self._token_actual()
        if not token_paren_cierre or token_paren_cierre.valor != ')':
            self.errores.append(Error(
                TipoError.SINTACTICO,
                "Se esperaba ')' para cerrar parámetros de función",
                token_paren_cierre.linea if token_paren_cierre else token_nombre.linea,
                token_paren_cierre.columna if token_paren_cierre else token_nombre.columna,
                "Agregue paréntesis de cierre ')'"
            ))
            return
        
        self._avanzar()  # consumir ')'
        
        # Verificar dos puntos
        token_colon = self._token_actual()
        if not token_colon or token_colon.valor != ':':
            self.errores.append(Error(
                TipoError.SINTACTICO,
                "Se esperaba ':' después de la definición de función",
                token_colon.linea if token_colon else token_nombre.linea,
                token_colon.columna if token_colon else token_nombre.columna,
                "Agregue dos puntos ':' al final de la definición"
            ))
            return
        
        self._avanzar()  # consumir ':'
    
    def _analizar_parametros_funcion(self):
        """Analiza parámetros de función"""
        while self._token_actual() and self._token_actual().valor != ')':
            token = self._token_actual()
            
            if token.tipo == TipoToken.IDENTIFICADOR:
                self._avanzar()
                
                # Verificar valor por defecto
                if self._token_actual() and self._token_actual().valor == '=':
                    self._avanzar()  # consumir '='
                    if not self._token_actual() or self._token_actual().valor in [',', ')']:
                        self.errores.append(Error(
                            TipoError.SINTACTICO,
                            "Se esperaba valor por defecto después de '='",
                            token.linea, token.columna,
                            "Proporcione un valor por defecto válido"
                        ))
                    else:
                        self._avanzar()  # consumir valor por defecto
                
                # Verificar coma separadora
                if self._token_actual() and self._token_actual().valor == ',':
                    self._avanzar()
                elif self._token_actual() and self._token_actual().valor != ')':
                    self.errores.append(Error(
                        TipoError.SINTACTICO,
                        "Se esperaba ',' entre parámetros",
                        self._token_actual().linea,
                        self._token_actual().columna,
                        "Separe los parámetros con comas"
                    ))
            else:
                self.errores.append(Error(
                    TipoError.SINTACTICO,
                    f"Parámetro inválido: {token.valor}",
                    token.linea, token.columna,
                    "Use identificadores válidos para parámetros"
                ))
                self._avanzar()
    
    def _analizar_definicion_clase(self):
        """Analiza definición de clase: class Nombre(bases):"""
        self._avanzar()  # consumir 'class'
        
        # Verificar nombre de clase
        token_nombre = self._token_actual()
        if not token_nombre or token_nombre.tipo != TipoToken.IDENTIFICADOR:
            self.errores.append(Error(
                TipoError.SINTACTICO,
                "Se esperaba nombre de clase después de 'class'",
                token_nombre.linea if token_nombre else 1,
                token_nombre.columna if token_nombre else 1,
                "Agregue un nombre válido para la clase"
            ))
            return
        
        # Verificar que empiece con mayúscula (convención)
        if not token_nombre.valor[0].isupper():
            self.errores.append(Error(
                TipoError.SINTACTICO,
                f"El nombre de clase '{token_nombre.valor}' debería empezar con mayúscula",
                token_nombre.linea, token_nombre.columna,
                "Use PascalCase para nombres de clase"
            ))
        
        self._avanzar()  # consumir nombre
        
        # Verificar herencia opcional
        if self._token_actual() and self._token_actual().valor == '(':
            self._avanzar()  # consumir '('
            
            # Analizar clases base
            while self._token_actual() and self._token_actual().valor != ')':
                if self._token_actual().tipo != TipoToken.IDENTIFICADOR:
                    self.errores.append(Error(
                        TipoError.SINTACTICO,
                        "Se esperaba nombre de clase base",
                        self._token_actual().linea,
                        self._token_actual().columna,
                        "Use nombres de clase válidos en herencia"
                    ))
                self._avanzar()
                
                if self._token_actual() and self._token_actual().valor == ',':
                    self._avanzar()
            
            if not self._token_actual() or self._token_actual().valor != ')':
                self.errores.append(Error(
                    TipoError.SINTACTICO,
                    "Se esperaba ')' para cerrar herencia",
                    token_nombre.linea, token_nombre.columna,
                    "Cierre la lista de herencia con ')'"
                ))
                return
            
            self._avanzar()  # consumir ')'
        
        # Verificar dos puntos
        if not self._token_actual() or self._token_actual().valor != ':':
            self.errores.append(Error(
                TipoError.SINTACTICO,
                "Se esperaba ':' después de la definición de clase",
                self._token_actual().linea if self._token_actual() else token_nombre.linea,
                self._token_actual().columna if self._token_actual() else token_nombre.columna,
                "Agregue dos puntos ':' al final de la definición"
            ))
            return
        
        self._avanzar()  # consumir ':'
    
    def _analizar_if(self):
        """Analiza estructura if/elif"""
        token_if = self._token_actual()
        self._avanzar()  # consumir 'if' o 'elif'
        
        # Debe seguir una expresión (condición)
        if not self._token_actual():
            self.errores.append(Error(
                TipoError.SINTACTICO,
                f"Se esperaba condición después de '{token_if.valor}'",
                token_if.linea, token_if.columna,
                "Agregue una expresión booleana como condición"
            ))
            return
        
        # Analizar condición (simplificado)
        self._analizar_expresion_simple()
        
        # Verificar dos puntos
        if not self._token_actual() or self._token_actual().valor != ':':
            self.errores.append(Error(
                TipoError.SINTACTICO,
                f"Se esperaba ':' después de la condición {token_if.valor}",
                self._token_actual().linea if self._token_actual() else token_if.linea,
                self._token_actual().columna if self._token_actual() else token_if.columna,
                "Agregue dos puntos ':' después de la condición"
            ))
            return
        
        self._avanzar()  # consumir ':'
    
    def _analizar_else(self):
        """Analiza estructura else"""
        self._avanzar()  # consumir 'else'
        
        # Verificar dos puntos
        if not self._token_actual() or self._token_actual().valor != ':':
            self.errores.append(Error(
                TipoError.SINTACTICO,
                "Se esperaba ':' después de 'else'",
                self._token_actual().linea if self._token_actual() else 1,
                self._token_actual().columna if self._token_actual() else 1,
                "Agregue dos puntos ':' después de 'else'"
            ))
            return
        
        self._avanzar()  # consumir ':'
    
    def _analizar_for(self):
        """Analiza bucle for"""
        self._avanzar()  # consumir 'for'
        
        # Variable del bucle
        if not self._token_actual() or self._token_actual().tipo != TipoToken.IDENTIFICADOR:
            self.errores.append(Error(
                TipoError.SINTACTICO,
                "Se esperaba variable después de 'for'",
                self._token_actual().linea if self._token_actual() else 1,
                self._token_actual().columna if self._token_actual() else 1,
                "Especifique una variable para el bucle"
            ))
            return
        
        self._avanzar()  # consumir variable
        
        # Palabra 'in'
        if not self._token_actual() or self._token_actual().valor != 'in':
            self.errores.append(Error(
                TipoError.SINTACTICO,
                "Se esperaba 'in' en bucle for",
                self._token_actual().linea if self._token_actual() else 1,
                self._token_actual().columna if self._token_actual() else 1,
                "Use 'in' para especificar el iterable"
            ))
            return
        
        self._avanzar()  # consumir 'in'
        
        # Expresión iterable
        if not self._token_actual():
            self.errores.append(Error(
                TipoError.SINTACTICO,
                "Se esperaba expresión iterable después de 'in'",
                1, 1,
                "Especifique un objeto iterable"
            ))
            return
        
        self._analizar_expresion_simple()
        
        # Verificar dos puntos
        if not self._token_actual() or self._token_actual().valor != ':':
            self.errores.append(Error(
                TipoError.SINTACTICO,
                "Se esperaba ':' después del bucle for",
                self._token_actual().linea if self._token_actual() else 1,
                self._token_actual().columna if self._token_actual() else 1,
                "Agregue dos puntos ':' después del bucle for"
            ))
            return
        
        self._avanzar()  # consumir ':'
    
    def _analizar_while(self):
        """Analiza bucle while"""
        self._avanzar()  # consumir 'while'
        
        # Condición
        if not self._token_actual():
            self.errores.append(Error(
                TipoError.SINTACTICO,
                "Se esperaba condición después de 'while'",
                1, 1,
                "Agregue una expresión booleana como condición"
            ))
            return
        
        self._analizar_expresion_simple()
        
        # Verificar dos puntos
        if not self._token_actual() or self._token_actual().valor != ':':
            self.errores.append(Error(
                TipoError.SINTACTICO,
                "Se esperaba ':' después de la condición while",
                self._token_actual().linea if self._token_actual() else 1,
                self._token_actual().columna if self._token_actual() else 1,
                "Agregue dos puntos ':' después de la condición"
            ))
            return
        
        self._avanzar()  # consumir ':'
    
    def _analizar_try(self):
        """Analiza bloque try"""
        self._avanzar()  # consumir 'try'
        
        # Verificar dos puntos
        if not self._token_actual() or self._token_actual().valor != ':':
            self.errores.append(Error(
                TipoError.SINTACTICO,
                "Se esperaba ':' después de 'try'",
                self._token_actual().linea if self._token_actual() else 1,
                self._token_actual().columna if self._token_actual() else 1,
                "Agregue dos puntos ':' después de 'try'"
            ))
            return
        
        self._avanzar()  # consumir ':'
    
    def _analizar_except(self):
        """Analiza bloque except"""
        self._avanzar()  # consumir 'except'
        
        # Opcionalmente tipo de excepción
        if (self._token_actual() and 
            self._token_actual().tipo == TipoToken.IDENTIFICADOR and 
            self._token_actual().valor != ':'):
            self._avanzar()  # consumir tipo de excepción
            
            # Opcionalmente 'as variable'
            if self._token_actual() and self._token_actual().valor == 'as':
                self._avanzar()  # consumir 'as'
                if not self._token_actual() or self._token_actual().tipo != TipoToken.IDENTIFICADOR:
                    self.errores.append(Error(
                        TipoError.SINTACTICO,
                        "Se esperaba nombre de variable después de 'as'",
                        self._token_actual().linea if self._token_actual() else 1,
                        self._token_actual().columna if self._token_actual() else 1,
                        "Especifique un nombre de variable válido"
                    ))
                    return
                self._avanzar()  # consumir variable
        
        # Verificar dos puntos
        if not self._token_actual() or self._token_actual().valor != ':':
            self.errores.append(Error(
                TipoError.SINTACTICO,
                "Se esperaba ':' después de 'except'",
                self._token_actual().linea if self._token_actual() else 1,
                self._token_actual().columna if self._token_actual() else 1,
                "Agregue dos puntos ':' después de 'except'"
            ))
            return
        
        self._avanzar()  # consumir ':'
    
    def _analizar_finally(self):
        """Analiza bloque finally"""
        self._avanzar()  # consumir 'finally'
        
        # Verificar dos puntos
        if not self._token_actual() or self._token_actual().valor != ':':
            self.errores.append(Error(
                TipoError.SINTACTICO,
                "Se esperaba ':' después de 'finally'",
                self._token_actual().linea if self._token_actual() else 1,
                self._token_actual().columna if self._token_actual() else 1,
                "Agregue dos puntos ':' después de 'finally'"
            ))
            return
        
        self._avanzar()  # consumir ':'
    
    def _analizar_with(self):
        """Analiza declaración with"""
        self._avanzar()  # consumir 'with'
        
        # Expresión
        if not self._token_actual():
            self.errores.append(Error(
                TipoError.SINTACTICO,
                "Se esperaba expresión después de 'with'",
                1, 1,
                "Especifique un objeto de contexto"
            ))
            return
        
        self._analizar_expresion_simple()
        
        # Opcionalmente 'as variable'
        if self._token_actual() and self._token_actual().valor == 'as':
            self._avanzar()  # consumir 'as'
            if not self._token_actual() or self._token_actual().tipo != TipoToken.IDENTIFICADOR:
                self.errores.append(Error(
                    TipoError.SINTACTICO,
                    "Se esperaba nombre de variable después de 'as'",
                    self._token_actual().linea if self._token_actual() else 1,
                    self._token_actual().columna if self._token_actual() else 1,
                    "Especifique un nombre de variable válido"
                ))
                return
            self._avanzar()  # consumir variable
        
        # Verificar dos puntos
        if not self._token_actual() or self._token_actual().valor != ':':
            self.errores.append(Error(
                TipoError.SINTACTICO,
                "Se esperaba ':' después de 'with'",
                self._token_actual().linea if self._token_actual() else 1,
                self._token_actual().columna if self._token_actual() else 1,
                "Agregue dos puntos ':' después de la declaración with"
            ))
            return
        
        self._avanzar()  # consumir ':'
    
    def _analizar_import(self):
        """Analiza declaraciones import"""
        token_import = self._token_actual()
        
        if token_import.valor == 'from':
            self._avanzar()  # consumir 'from'
            
            # Módulo de origen
            if not self._token_actual() or self._token_actual().tipo != TipoToken.IDENTIFICADOR:
                self.errores.append(Error(
                    TipoError.SINTACTICO,
                    "Se esperaba nombre de módulo después de 'from'",
                    self._token_actual().linea if self._token_actual() else token_import.linea,
                    self._token_actual().columna if self._token_actual() else token_import.columna,
                    "Especifique un nombre de módulo válido"
                ))
                return
            
            self._avanzar()  # consumir módulo
            
            # Palabra 'import'
            if not self._token_actual() or self._token_actual().valor != 'import':
                self.errores.append(Error(
                    TipoError.SINTACTICO,
                    "Se esperaba 'import' en declaración from-import",
                    self._token_actual().linea if self._token_actual() else token_import.linea,
                    self._token_actual().columna if self._token_actual() else token_import.columna,
                    "Use 'import' después del nombre del módulo"
                ))
                return
            
            self._avanzar()  # consumir 'import'
        else:
            self._avanzar()  # consumir 'import'
        
        # Nombres a importar
        if not self._token_actual() or self._token_actual().tipo != TipoToken.IDENTIFICADOR:
            self.errores.append(Error(
                TipoError.SINTACTICO,
                "Se esperaba nombre después de 'import'",
                self._token_actual().linea if self._token_actual() else token_import.linea,
                self._token_actual().columna if self._token_actual() else token_import.columna,
                "Especifique qué importar"
            ))
            return
        
        self._avanzar()  # consumir nombre
        
        # Opcionalmente 'as alias'
        if self._token_actual() and self._token_actual().valor == 'as':
            self._avanzar()  # consumir 'as'
            if not self._token_actual() or self._token_actual().tipo != TipoToken.IDENTIFICADOR:
                self.errores.append(Error(
                    TipoError.SINTACTICO,
                    "Se esperaba alias después de 'as'",
                    self._token_actual().linea if self._token_actual() else token_import.linea,
                    self._token_actual().columna if self._token_actual() else token_import.columna,
                    "Especifique un alias válido"
                ))
                return
            self._avanzar()  # consumir alias
    
    def _analizar_sentencia_simple(self):
        """Analiza sentencias simples como return, break, etc."""
        token = self._token_actual()
        self._avanzar()  # consumir palabra reservada
        
        # Algunas sentencias pueden tener expresiones
        if token.valor in ['return', 'raise', 'assert', 'del']:
            # Pueden tener expresión opcional
            if (self._token_actual() and 
                self._token_actual().tipo not in [TipoToken.NUEVA_LINEA, TipoToken.EOF, TipoToken.COMENTARIO]):
                self._analizar_expresion_simple()
    
    def _analizar_expresion_o_asignacion(self):
        """Analiza expresión o asignación"""
        # Simplificado: avanzar hasta encontrar operador de asignación o fin de línea
        inicio_pos = self.posicion
        tiene_asignacion = False
        
        while (self._token_actual() and 
               self._token_actual().tipo not in [TipoToken.NUEVA_LINEA, TipoToken.EOF, TipoToken.COMENTARIO]):
            
            if self._token_actual().valor == '=':
                tiene_asignacion = True
                self._avanzar()
                break
            
            self._avanzar()
            
            # Prevenir bucle infinito
            if self.posicion == inicio_pos:
                break
            inicio_pos = self.posicion
        
        if tiene_asignacion:
            # Verificar que hay algo después del =
            if (not self._token_actual() or 
                self._token_actual().tipo in [TipoToken.NUEVA_LINEA, TipoToken.EOF, TipoToken.COMENTARIO]):
                self.errores.append(Error(
                    TipoError.SINTACTICO,
                    "Asignación incompleta: falta valor después de '='",
                    self._token_actual().linea if self._token_actual() else 1,
                    self._token_actual().columna if self._token_actual() else 1,
                    "Proporcione un valor para la asignación"
                ))
            else:
                self._analizar_expresion_simple()
    
    def _analizar_expresion_simple(self):
        """Analiza una expresión simple"""
        # Simplificado: avanzar hasta encontrar delimitador o fin
        while (self._token_actual() and 
               self._token_actual().tipo not in [TipoToken.NUEVA_LINEA, TipoToken.EOF, TipoToken.COMENTARIO] and
               self._token_actual().valor not in [':', ',']):
            self._avanzar()

class AnalizadorSemantico:
    """
    ANALIZADOR SEMÁNTICO AVANZADO
    ============================
    """
    
    def __init__(self):
        # Funciones y módulos built-in de Python
        self.built_ins = {
            # Funciones básicas
            'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytearray', 'bytes',
            'callable', 'chr', 'classmethod', 'compile', 'complex', 'delattr',
            'dict', 'dir', 'divmod', 'enumerate', 'eval', 'exec', 'filter',
            'float', 'format', 'frozenset', 'getattr', 'globals', 'hasattr',
            'hash', 'help', 'hex', 'id', 'input', 'int', 'isinstance',
            'issubclass', 'iter', 'len', 'list', 'locals', 'map', 'max',
            'memoryview', 'min', 'next', 'object', 'oct', 'open', 'ord',
            'pow', 'print', 'property', 'range', 'repr', 'reversed', 'round',
            'set', 'setattr', 'slice', 'sorted', 'staticmethod', 'str', 'sum',
            'super', 'tuple', 'type', 'vars', 'zip',
            
            # Constantes
            'True', 'False', 'None', 'NotImplemented', 'Ellipsis',
            
            # Excepciones comunes
            'Exception', 'ValueError', 'TypeError', 'AttributeError', 'KeyError',
            'IndexError', 'NameError', 'SyntaxError', 'RuntimeError'
        }
        
        # Variables especiales de Python
        self.variables_especiales = {
            '__name__', '__main__', '__file__', '__doc__', '__dict__',
            '__class__', '__bases__', '__module__', '__version__'
        }
    
    def analizar(self, tokens: List[Token]) -> List[Error]:
        """Analiza la semántica del código"""
        errores = []
        
        # Recopilar definiciones en primera pasada
        definiciones = self._recopilar_definiciones(tokens)
        
        # Analizar uso en segunda pasada
        errores.extend(self._analizar_uso_variables(tokens, definiciones))
        errores.extend(self._analizar_uso_funciones(tokens, definiciones))
        errores.extend(self._analizar_llamadas_funciones(tokens, definiciones))
        
        return errores
    
    def _recopilar_definiciones(self, tokens: List[Token]) -> Dict[str, Set[str]]:
        """Primera pasada: recopila todas las definiciones"""
        definiciones = {
            'funciones': set(),
            'clases': set(),
            'variables': set(),
            'imports': set(),
            'parametros': set()
        }
        
        i = 0
        while i < len(tokens):
            token = tokens[i]
            
            if token.tipo == TipoToken.PALABRA_RESERVADA:
                if token.valor == 'def':
                    # Función
                    if i + 1 < len(tokens) and tokens[i + 1].tipo == TipoToken.IDENTIFICADOR:
                        func_name = tokens[i + 1].valor
                        definiciones['funciones'].add(func_name)
                        
                        # Recopilar parámetros
                        j = i + 2
                        if j < len(tokens) and tokens[j].valor == '(':
                            j += 1
                            while j < len(tokens) and tokens[j].valor != ')':
                                if tokens[j].tipo == TipoToken.IDENTIFICADOR:
                                    definiciones['parametros'].add(tokens[j].valor)
                                    definiciones['variables'].add(tokens[j].valor)
                                j += 1
                        i = j
                        continue
                
                elif token.valor == 'class':
                    # Clase
                    if i + 1 < len(tokens) and tokens[i + 1].tipo == TipoToken.IDENTIFICADOR:
                        definiciones['clases'].add(tokens[i + 1].valor)
                        i += 2
                        continue
                
                elif token.valor in ['import', 'from']:
                    # Import
                    if token.valor == 'from':
                        # from module import name
                        j = i + 1
                        while j < len(tokens) and tokens[j].valor != 'import':
                            j += 1
                        j += 1  # saltar 'import'
                        while j < len(tokens) and tokens[j].tipo == TipoToken.IDENTIFICADOR:
                            definiciones['imports'].add(tokens[j].valor)
                            j += 1
                            if j < len(tokens) and tokens[j].valor == ',':
                                j += 1
                        i = j
                        continue
                    else:
                        # import module
                        j = i + 1
                        while j < len(tokens) and tokens[j].tipo == TipoToken.IDENTIFICADOR:
                            definiciones['imports'].add(tokens[j].valor)
                            j += 1
                            if j < len(tokens) and tokens[j].valor == ',':
                                j += 1
                        i = j
                        continue
                
                elif token.valor == 'for':
                    # Variable de bucle for
                    if i + 1 < len(tokens) and tokens[i + 1].tipo == TipoToken.IDENTIFICADOR:
                        definiciones['variables'].add(tokens[i + 1].valor)
                        i += 2
                        continue
            
            # Asignaciones
            if (token.tipo == TipoToken.IDENTIFICADOR and 
                i + 1 < len(tokens) and 
                tokens[i + 1].valor == '='):
                definiciones['variables'].add(token.valor)
                i += 2
                continue
            
            i += 1
        
        return definiciones
    
    def _analizar_uso_variables(self, tokens: List[Token], definiciones: Dict[str, Set[str]]) -> List[Error]:
        """Analiza el uso de variables"""
        errores = []
        
        for i, token in enumerate(tokens):
            if token.tipo == TipoToken.IDENTIFICADOR:
                # Verificar si es una variable usada (no en contexto de definición)
                if not self._es_contexto_definicion(tokens, i):
                    if not self._esta_definida_variable(token.valor, definiciones):
                        # Verificar si no es una llamada a función
                        if not (i + 1 < len(tokens) and tokens[i + 1].valor == '('):
                            # Verificar que no sea parte de un atributo (ej: objeto.atributo)
                            if not (i > 0 and tokens[i - 1].valor == '.'):
                                errores.append(Error(
                                    TipoError.SEMANTICO,
                                    f"Variable '{token.valor}' utilizada sin definir",
                                    token.linea, token.columna,
                                    f"Define la variable '{token.valor}' antes de usarla o verifica si hay un error tipográfico"
                                ))
        
        return errores
    
    def _analizar_uso_funciones(self, tokens: List[Token], definiciones: Dict[str, Set[str]]) -> List[Error]:
        """Analiza el uso de funciones"""
        errores = []
        
        for i, token in enumerate(tokens):
            if (token.tipo == TipoToken.IDENTIFICADOR and 
                i + 1 < len(tokens) and 
                tokens[i + 1].valor == '('):
                
                # Es una llamada a función
                if not self._esta_definida_funcion(token.valor, definiciones):
                    # Verificar que no sea un método de objeto
                    if not (i > 0 and tokens[i - 1].valor == '.'):
                        errores.append(Error(
                            TipoError.SEMANTICO,
                            f"Función '{token.valor}()' no está definida",
                            token.linea, token.columna,
                            f"Define la función '{token.valor}' antes de usarla o verifica si hay un error tipográfico"
                        ))
        
        return errores
    
    def _analizar_llamadas_funciones(self, tokens: List[Token], definiciones: Dict[str, Set[str]]) -> List[Error]:
        """Analiza llamadas a funciones para verificar sintaxis básica"""
        errores = []
        
        for i, token in enumerate(tokens):
            if (token.tipo == TipoToken.IDENTIFICADOR and 
                i + 1 < len(tokens) and 
                tokens[i + 1].valor == '('):
                
                # Verificar que los paréntesis estén balanceados
                j = i + 1  # posición de '('
                nivel_parentesis = 1
                j += 1
                
                while j < len(tokens) and nivel_parentesis > 0:
                    if tokens[j].valor == '(':
                        nivel_parentesis += 1
                    elif tokens[j].valor == ')':
                        nivel_parentesis -= 1
                    j += 1
                
                if nivel_parentesis > 0:
                    errores.append(Error(
                        TipoError.SINTACTICO,
                        f"Paréntesis sin cerrar en llamada a función '{token.valor}'",
                        token.linea, token.columna,
                        "Agregue ')' para cerrar la llamada a función"
                    ))
        
        return errores
    
    def _es_contexto_definicion(self, tokens: List[Token], posicion: int) -> bool:
        """Verifica si estamos en un contexto de definición de variable"""
        # Asignación directa
        if (posicion + 1 < len(tokens) and 
            tokens[posicion + 1].valor in ['=', '+=', '-=', '*=', '/=', '//=', '%=', '**=']):
            return True
        
        # Variable en bucle for
        for j in range(max(0, posicion - 3), posicion):
            if (j < len(tokens) and 
                tokens[j].tipo == TipoToken.PALABRA_RESERVADA and 
                tokens[j].valor == 'for'):
                # Verificar si está entre 'for' e 'in'
                for k in range(j + 1, min(len(tokens), posicion + 3)):
                    if k < len(tokens) and tokens[k].valor == 'in':
                        if posicion < k:
                            return True
                        break
        
        # Parámetro de función
        for j in range(max(0, posicion - 10), posicion):
            if (j < len(tokens) and 
                tokens[j].tipo == TipoToken.PALABRA_RESERVADA and 
                tokens[j].valor == 'def'):
                # Buscar paréntesis de apertura
                for k in range(j + 1, min(len(tokens), posicion + 5)):
                    if k < len(tokens) and tokens[k].valor == '(':
                        # Buscar paréntesis de cierre
                        for l in range(k + 1, len(tokens)):
                            if l < len(tokens) and tokens[l].valor == ')':
                                if k < posicion < l:
                                    return True
                                break
                        break
                break
        
        # Variable en except
        for j in range(max(0, posicion - 5), posicion):
            if (j < len(tokens) and 
                tokens[j].tipo == TipoToken.PALABRA_RESERVADA and 
                tokens[j].valor == 'except'):
                # Buscar 'as'
                for k in range(j + 1, min(len(tokens), posicion + 2)):
                    if k < len(tokens) and tokens[k].valor == 'as':
                        if posicion == k + 1:
                            return True
                        break
        
        return False
    
    def _esta_definida_variable(self, nombre: str, definiciones: Dict[str, Set[str]]) -> bool:
        """Verifica si una variable está definida"""
        return (nombre in definiciones['variables'] or
                nombre in definiciones['parametros'] or
                nombre in definiciones['imports'] or
                nombre in definiciones['clases'] or
                nombre in self.built_ins or
                nombre in self.variables_especiales or
                nombre.startswith('_'))  # Variables privadas/especiales
    
    def _esta_definida_funcion(self, nombre: str, definiciones: Dict[str, Set[str]]) -> bool:
        """Verifica si una función está definida"""
        return (nombre in definiciones['funciones'] or
                nombre in definiciones['imports'] or
                nombre in definiciones['clases'] or  # Constructor de clase
                nombre in self.built_ins or
                nombre.startswith('_'))  # Funciones especiales

class CompiladorPython:
    """Compilador Principal"""
    
    def __init__(self):
        self.analizador_lexico = AnalizadorLexico()
        self.analizador_sintactico = AnalizadorSintactico()
        self.analizador_semantico = AnalizadorSemantico()
    
    def compilar(self, codigo: str) -> Dict[str, Any]:
        """Compila el código con análisis completo"""
        try:
            # FASE 1: Análisis Léxico
            tokens, errores_lexicos = self.analizador_lexico.tokenizar(codigo)
            
            # FASE 2: Análisis Sintáctico (solo si no hay errores léxicos críticos)
            errores_sintacticos = []
            if not errores_lexicos:
                errores_sintacticos = self.analizador_sintactico.analizar(tokens)
            
            # FASE 3: Análisis Semántico (solo si no hay errores previos)
            errores_semanticos = []
            if not errores_lexicos and not errores_sintacticos:
                errores_semanticos = self.analizador_semantico.analizar(tokens)
            
            # Combinar todos los errores
            todos_errores = errores_lexicos + errores_sintacticos + errores_semanticos
            
            return {
                'tokens': tokens,
                'errores_lexicos': errores_lexicos,
                'errores_sintacticos': errores_sintacticos,
                'errores_semanticos': errores_semanticos,
                'total_errores': len(todos_errores),
                'exito': len(todos_errores) == 0
            }
        except Exception as e:
            return {
                'tokens': [],
                'errores_lexicos': [Error(TipoError.LEXICO, f"Error crítico: {str(e)}", 1, 1)],
                'errores_sintacticos': [],
                'errores_semanticos': [],
                'total_errores': 1,
                'exito': False
            }

class InterfazModerna:
    """
    INTERFAZ MODERNA DE DOS PANELES
    ==============================
    
    Editor a la izquierda, resultados a la derecha
    """
    
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("🐍 Compilador Python - Diseño Moderno")
        self.ventana.geometry("1600x1000")
        self.ventana.state('zoomed')
        
        # Colores modernos GitHub Dark
        self.colores = {
            'fondo': '#0d1117',           # Fondo principal
            'panel': '#161b22',           # Paneles
            'editor': '#0d1117',          # Editor
            'resultados': '#21262d',      # Resultados
            'texto': '#f0f6fc',           # Texto principal
            'texto_dim': '#8b949e',       # Texto secundario
            'azul': '#58a6ff',            # Azul GitHub
            'verde': '#3fb950',           # Verde GitHub
            'rojo': '#f85149',            # Rojo GitHub
            'amarillo': '#d29922',        # Amarillo GitHub
            'borde': '#30363d'            # Bordes
        }
        
        self.ventana.configure(bg=self.colores['fondo'])
        self.compilador = CompiladorPython()
        
        self.codigo_ejemplo = '''# 🧮 Calculadora Matemática Avanzada
def fibonacci(n):
    """Calcula el n-ésimo número de Fibonacci"""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def factorial(n):
    """Calcula el factorial de n"""
    if n <= 1:
        return 1
    return n * factorial(n-1)

def es_primo(n):
    """Verifica si un número es primo"""
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

# 🚀 Programa Principal
print("=" * 50)
print("🧮 CALCULADORA MATEMÁTICA AVANZADA")
print("=" * 50)

for i in range(1, 11):
    fib = fibonacci(i)
    fact = factorial(i) if i <= 7 else "Muy grande"
    primo = "✓" if es_primo(i) else "✗"
    
    print(f"N={i:2d} | Fib={fib:3d} | Fact={fact!s:>10} | Primo={primo}")

print("\\n🎉 ¡Cálculos completados exitosamente!")

# 🧪 Ejemplos de errores comentados:
# error_variable = variable_no_definida  # Error semántico
# funcion_inexistente()                  # Error semántico
# def función sin nombre():              # Error sintáctico
'''
        
        self.crear_interfaz()
    
    def crear_interfaz(self):
        """Crea la interfaz completa"""
        # Header principal
        self.crear_header()
        
        # Frame principal con dos paneles
        main_frame = tk.Frame(self.ventana, bg=self.colores['fondo'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))
        
        # PANEL IZQUIERDO - Editor
        self.crear_panel_editor(main_frame)
        
        # PANEL DERECHO - Resultados
        self.crear_panel_resultados(main_frame)
    
    def crear_header(self):
        """Crea el header principal"""
        header = tk.Frame(self.ventana, bg=self.colores['azul'], height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        # Título
        titulo = tk.Label(header,
                         text="🐍 COMPILADOR PYTHON",
                         font=("Segoe UI", 28, "bold"),
                         bg=self.colores['azul'],
                         fg='white')
        titulo.pack(side=tk.LEFT, padx=30, pady=20)
        
        # Subtítulo
        subtitulo = tk.Label(header,
                           text="Análisis Léxico • Sintáctico • Semántico",
                           font=("Segoe UI", 14),
                           bg=self.colores['azul'],
                           fg='white')
        subtitulo.pack(side=tk.LEFT, padx=(0, 30), pady=20)
        
        # Status
        self.status = tk.Label(header,
                              text="💡 Listo para compilar",
                              font=("Segoe UI", 12, "bold"),
                              bg=self.colores['azul'],
                              fg='white')
        self.status.pack(side=tk.RIGHT, padx=30, pady=20)
    
    def crear_panel_editor(self, parent):
        """Crea el panel editor (izquierda)"""
        # Frame del editor
        editor_frame = tk.Frame(parent, bg=self.colores['panel'], relief=tk.RAISED, bd=2)
        editor_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        
        # Header del editor
        editor_header = tk.Frame(editor_frame, bg=self.colores['verde'], height=50)
        editor_header.pack(fill=tk.X)
        editor_header.pack_propagate(False)
        
        tk.Label(editor_header,
                text="📝 EDITOR DE CÓDIGO",
                font=("Segoe UI", 16, "bold"),
                bg=self.colores['verde'],
                fg='white').pack(pady=12)
        
        # Frame del código con números de línea
        codigo_frame = tk.Frame(editor_frame, bg=self.colores['editor'])
        codigo_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Números de línea
        numeros_frame = tk.Frame(codigo_frame, bg=self.colores['borde'], width=60)
        numeros_frame.pack(side=tk.LEFT, fill=tk.Y)
        numeros_frame.pack_propagate(False)
        
        self.texto_numeros = tk.Text(numeros_frame,
                                   width=4,
                                   font=("Consolas", 12),
                                   bg=self.colores['borde'],
                                   fg=self.colores['amarillo'],
                                   state=tk.DISABLED,
                                   relief=tk.FLAT)
        self.texto_numeros.pack(fill=tk.BOTH, expand=True, padx=5)
        
        # Editor de código
        self.editor = scrolledtext.ScrolledText(codigo_frame,
                                              font=("Consolas", 12),
                                              bg=self.colores['editor'],
                                              fg=self.colores['texto'],
                                              insertbackground=self.colores['azul'],
                                              selectbackground=self.colores['azul'],
                                              relief=tk.FLAT,
                                              wrap=tk.NONE,
                                              undo=True)
        self.editor.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        self.editor.insert('1.0', self.codigo_ejemplo)
        
        # Vincular eventos
        self.editor.bind('<KeyRelease>', self.actualizar_numeros)
        self.editor.bind('<Button-1>', self.actualizar_numeros)
        self.editor.bind('<MouseWheel>', self.sincronizar_scroll)
        
        # Botones de control
        self.crear_botones_control(editor_frame)
        
        # Actualizar números inicial
        self.actualizar_numeros()
    
    def crear_botones_control(self, parent):
        """Crea los botones de control"""
        botones_frame = tk.Frame(parent, bg=self.colores['panel'], height=70)
        botones_frame.pack(fill=tk.X, padx=15, pady=(0, 15))
        botones_frame.pack_propagate(False)
        
        # Estilo de botones
        btn_config = {
            'font': ("Segoe UI", 12, "bold"),
            'relief': tk.FLAT,
            'cursor': 'hand2',
            'pady': 12,
            'padx': 25
        }
        
        # Botón Compilar
        btn_compilar = tk.Button(botones_frame,
                               text="🚀 COMPILAR",
                               bg=self.colores['verde'],
                               fg='white',
                               activebackground='#2ea043',
                               command=self.compilar_codigo,
                               **btn_config)
        btn_compilar.pack(side=tk.LEFT, padx=(0, 10))
        
        # Botón Limpiar
        btn_limpiar = tk.Button(botones_frame,
                              text="🧹 LIMPIAR",
                              bg=self.colores['amarillo'],
                              fg='white',
                              activebackground='#bf8700',
                              command=self.limpiar_codigo,
                              **btn_config)
        btn_limpiar.pack(side=tk.LEFT, padx=(0, 10))
        
        # Botón Ejemplo
        btn_ejemplo = tk.Button(botones_frame,
                              text="📝 EJEMPLO",
                              bg=self.colores['azul'],
                              fg='white',
                              activebackground='#1f6feb',
                              command=self.cargar_ejemplo,
                              **btn_config)
        btn_ejemplo.pack(side=tk.LEFT, padx=(0, 10))
        
        # Botón Ayuda
        btn_ayuda = tk.Button(botones_frame,
                            text="❓ AYUDA",
                            bg=self.colores['borde'],
                            fg=self.colores['texto'],
                            activebackground='#484f58',
                            command=self.mostrar_ayuda,
                            **btn_config)
        btn_ayuda.pack(side=tk.RIGHT)
    
    def crear_panel_resultados(self, parent):
        """Crea el panel de resultados (derecha)"""
        # Frame de resultados
        resultados_frame = tk.Frame(parent, bg=self.colores['panel'], relief=tk.RAISED, bd=2)
        resultados_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(8, 0))
        
        # Header de resultados
        resultados_header = tk.Frame(resultados_frame, bg=self.colores['rojo'], height=50)
        resultados_header.pack(fill=tk.X)
        resultados_header.pack_propagate(False)
        
        tk.Label(resultados_header,
                text="📊 RESULTADOS DEL ANÁLISIS",
                font=("Segoe UI", 16, "bold"),
                bg=self.colores['rojo'],
                fg='white').pack(pady=12)
        
        # Notebook para pestañas
        self.crear_notebook(resultados_frame)
    
    def crear_notebook(self, parent):
        """Crea el notebook con pestañas"""
        # Frame para notebook
        notebook_frame = tk.Frame(parent, bg=self.colores['panel'])
        notebook_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Configurar estilo del notebook
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Modern.TNotebook',
                       background=self.colores['panel'],
                       borderwidth=0)
        style.configure('Modern.TNotebook.Tab',
                       background=self.colores['borde'],
                       foreground=self.colores['texto'],
                       padding=[25, 12],
                       font=("Segoe UI", 11, "bold"))
        style.map('Modern.TNotebook.Tab',
                 background=[('selected', self.colores['azul']),
                           ('active', self.colores['azul'])],
                 foreground=[('selected', 'white'),
                           ('active', 'white')])
        
        # Crear notebook
        self.notebook = ttk.Notebook(notebook_frame, style='Modern.TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Crear pestañas
        self.crear_pestañas()
    
    def crear_pestañas(self):
        """Crea todas las pestañas"""
        # Pestaña Resumen
        frame_resumen = tk.Frame(self.notebook, bg=self.colores['resultados'])
        self.notebook.add(frame_resumen, text="📋 RESUMEN")
        self.texto_resumen = self.crear_area_texto(frame_resumen)
        
        # Pestaña Tokens
        frame_tokens = tk.Frame(self.notebook, bg=self.colores['resultados'])
        self.notebook.add(frame_tokens, text="🔤 TOKENS")
        self.texto_tokens = self.crear_area_texto(frame_tokens)
        
        # Pestaña Sintáctico
        frame_sintactico = tk.Frame(self.notebook, bg=self.colores['resultados'])
        self.notebook.add(frame_sintactico, text="🔧 SINTÁCTICO")
        self.texto_sintactico = self.crear_area_texto(frame_sintactico)
        
        # Pestaña Semántico
        frame_semantico = tk.Frame(self.notebook, bg=self.colores['resultados'])
        self.notebook.add(frame_semantico, text="🧠 SEMÁNTICO")
        self.texto_semantico = self.crear_area_texto(frame_semantico)
        
        # Pestaña Estadísticas
        frame_stats = tk.Frame(self.notebook, bg=self.colores['resultados'])
        self.notebook.add(frame_stats, text="📈 ESTADÍSTICAS")
        self.texto_stats = self.crear_area_texto(frame_stats)
    
    def crear_area_texto(self, parent):
        """Crea un área de texto para resultados"""
        area = scrolledtext.ScrolledText(parent,
                                       font=("Consolas", 11),
                                       bg=self.colores['resultados'],
                                       fg=self.colores['texto'],
                                       relief=tk.FLAT,
                                       wrap=tk.WORD)
        area.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        return area
    
    def actualizar_numeros(self, event=None):
        """Actualiza los números de línea"""
        try:
            contenido = self.editor.get('1.0', tk.END)
            lineas = contenido.count('\\n')
            numeros = '\\n'.join(str(i) for i in range(1, lineas + 1))
            
            self.texto_numeros.config(state=tk.NORMAL)
            self.texto_numeros.delete('1.0', tk.END)
            self.texto_numeros.insert('1.0', numeros)
            self.texto_numeros.config(state=tk.DISABLED)
            
            # Sincronizar scroll
            self.sincronizar_scroll()
        except:
            pass
    
    def sincronizar_scroll(self, event=None):
        """Sincroniza el scroll entre editor y números"""
        try:
            self.texto_numeros.yview_moveto(self.editor.yview()[0])
        except:
            pass
    
    def compilar_codigo(self):
        """Compila el código"""
        codigo = self.editor.get('1.0', tk.END).strip()
        
        if not codigo:
            messagebox.showwarning("⚠️ Advertencia", "Ingrese código para compilar")
            return
        
        # Actualizar status
        self.status.config(text="🔄 Compilando...", bg=self.colores['amarillo'])
        
        def compilar():
            try:
                resultado = self.compilador.compilar(codigo)
                self.ventana.after(0, lambda: self.mostrar_resultados(resultado))
            except Exception as e:
                self.ventana.after(0, lambda: messagebox.showerror("❌ Error", f"Error: {e}"))
        
        threading.Thread(target=compilar, daemon=True).start()
    
    def mostrar_resultados(self, resultado):
        """Muestra los resultados de la compilación"""
        # Limpiar todas las áreas
        for area in [self.texto_resumen, self.texto_tokens, self.texto_sintactico, 
                    self.texto_semantico, self.texto_stats]:
            area.delete('1.0', tk.END)
        
        # Actualizar status
        if resultado['exito']:
            self.status.config(text="✅ Compilación exitosa", bg=self.colores['verde'])
        else:
            self.status.config(text=f"❌ {resultado['total_errores']} errores", bg=self.colores['rojo'])
        
        # RESUMEN
        resumen = f"""
╔══════════════════════════════════════════════════════════════╗
║                    RESULTADOS DE LA COMPILACIÓN              ║
╚══════════════════════════════════════════════════════════════╝

📊 ESTADÍSTICAS GENERALES:
────────────────────────────────────────────────────────────────
• Tokens generados: {len(resultado['tokens'])}
• Errores léxicos: {len(resultado['errores_lexicos'])}
• Errores sintácticos: {len(resultado['errores_sintacticos'])}
• Errores semánticos: {len(resultado['errores_semanticos'])}
• Total de errores: {resultado['total_errores']}
• Estado: {'🎉 ÉXITO TOTAL' if resultado['exito'] else '⚠️ ERRORES ENCONTRADOS'}

"""
        
        if resultado['errores_lexicos']:
            resumen += """
🔤 ERRORES LÉXICOS:
────────────────────────────────────────────────────────────────
"""
            for i, error in enumerate(resultado['errores_lexicos'], 1):
                resumen += f"  {i}. 📍 Línea {error.linea}: {error.mensaje}\\n"
                if error.sugerencia:
                    resumen += f"     💡 {error.sugerencia}\\n"
        
        if resultado['errores_sintacticos']:
            resumen += """
🔧 ERRORES SINTÁCTICOS:
────────────────────────────────────────────────────────────────
"""
            for i, error in enumerate(resultado['errores_sintacticos'], 1):
                resumen += f"  {i}. 📍 Línea {error.linea}: {error.mensaje}\\n"
                if error.sugerencia:
                    resumen += f"     💡 {error.sugerencia}\\n"
        
        if resultado['errores_semanticos']:
            resumen += """
🧠 ERRORES SEMÁNTICOS:
────────────────────────────────────────────────────────────────
"""
            for i, error in enumerate(resultado['errores_semanticos'], 1):
                resumen += f"  {i}. 📍 Línea {error.linea}: {error.mensaje}\\n"
                if error.sugerencia:
                    resumen += f"     💡 {error.sugerencia}\\n"
        
        if resultado['exito']:
            resumen += """
🎉 ¡FELICITACIONES!
────────────────────────────────────────────────────────────────
Su código ha sido compilado exitosamente sin errores.
Todas las verificaciones léxicas, sintácticas y semánticas
han pasado correctamente.
"""
        
        self.texto_resumen.insert('1.0', resumen)
        
        # TOKENS
        tokens_info = """
╔══════════════════════════════════════════════════════════════╗
║                        ANÁLISIS LÉXICO                       ║
╚══════════════════════════════════════════════════════════════╝

"""
        
        if resultado['errores_lexicos']:
            tokens_info += "⚠️ ERRORES LÉXICOS ENCONTRADOS:\\n"
            tokens_info += "┌─────┬─────────┬──────────┬──────────────────────────────┐\\n"
            tokens_info += "│ No. │  Línea  │ Columna  │           Descripción        │\\n"
            tokens_info += "├─────┼─────────┼──────────┼──────────────────────────────┤\\n"
            for i, error in enumerate(resultado['errores_lexicos'], 1):
                linea = str(error.linea)
                columna = str(error.columna)
                desc = error.mensaje[:28] + "..." if len(error.mensaje) > 28 else error.mensaje
                tokens_info += f"│ {i:2d}  │  {linea:5s}  │   {columna:5s}  │ {desc:28s} │\\n"
            tokens_info += "└─────┴─────────┴──────────┴──────────────────────────────┘\\n\\n"
        
        if resultado['tokens']:
            tokens_info += "TOKENS IDENTIFICADOS:\\n"
            tokens_info += "┌─────┬──────────────────┬─────────────────────────┬──────┐\\n"
            tokens_info += "│ No. │       Tipo       │          Valor          │Línea │\\n"
            tokens_info += "├─────┼──────────────────┼─────────────────────────┼──────┤\\n"
            for i, token in enumerate(resultado['tokens'][:50]):  # Primeros 50
                tipo = token.tipo.value[:16]
                valor = str(token.valor)[:23]
                if len(str(token.valor)) > 23:
                    valor = str(token.valor)[:20] + "..."
                linea = str(token.linea)
                tokens_info += f"│{i+1:4d} │ {tipo:16s} │ {valor:23s} │ {linea:4s} │\\n"
            tokens_info += "└─────┴──────────────────┴─────────────────────────┴──────┘\\n"
            
            if len(resultado['tokens']) > 50:
                tokens_info += f"\\n📊 Mostrando los primeros 50 de {len(resultado['tokens'])} tokens totales\\n"
        else:
            tokens_info += "⚠️ No se generaron tokens válidos debido a errores léxicos.\\n"
        
        self.texto_tokens.insert('1.0', tokens_info)
        
        # SINTÁCTICO
        sintactico_info = """
╔══════════════════════════════════════════════════════════════╗
║                      ANÁLISIS SINTÁCTICO                     ║
╚══════════════════════════════════════════════════════════════╝

"""
        if resultado['errores_sintacticos']:
            sintactico_info += "ERRORES ENCONTRADOS:\\n"
            sintactico_info += "┌─────┬─────────┬──────────┬──────────────────────────────┐\\n"
            sintactico_info += "│ No. │  Línea  │ Columna  │           Descripción        │\\n"
            sintactico_info += "├─────┼─────────┼──────────┼──────────────────────────────┤\\n"
            for i, error in enumerate(resultado['errores_sintacticos'], 1):
                linea = str(error.linea)
                columna = str(error.columna)
                desc = error.mensaje[:28] + "..." if len(error.mensaje) > 28 else error.mensaje
                sintactico_info += f"│ {i:2d}  │  {linea:5s}  │   {columna:5s}  │ {desc:28s} │\\n"
            sintactico_info += "└─────┴─────────┴──────────┴──────────────────────────────┘\\n\\n"
            
            # Detalles de sugerencias
            sintactico_info += "💡 SUGERENCIAS:\\n"
            sintactico_info += "┌─────┬─────────────────────────────────────────────────────┐\\n"
            sintactico_info += "│ No. │                    Sugerencia                       │\\n"
            sintactico_info += "├─────┼─────────────────────────────────────────────────────┤\\n"
            for i, error in enumerate(resultado['errores_sintacticos'], 1):
                if error.sugerencia:
                    sug = error.sugerencia[:55] + "..." if len(error.sugerencia) > 55 else error.sugerencia
                    sintactico_info += f"│ {i:2d}  │ {sug:55s} │\\n"
                else:
                    sintactico_info += f"│ {i:2d}  │ {'Sin sugerencia disponible':55s} │\\n"
            sintactico_info += "└─────┴─────────────────────────────────────────────────────┘\\n"
        elif resultado['errores_lexicos']:
            sintactico_info += """⚠️ ANÁLISIS SINTÁCTICO OMITIDO
────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────┐
│                          MOTIVO                             │
├─────────────────────────────────────────────────────────────┤
│ El análisis sintáctico no se pudo completar debido a       │
│ errores en la fase léxica. Corrija primero los errores     │
│ léxicos para continuar con el análisis sintáctico.         │
└─────────────────────────────────────────────────────────────┘
"""
        else:
            sintactico_info += """✅ ANÁLISIS SINTÁCTICO EXITOSO
────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────┐
│                      VERIFICACIONES                        │
├─────────────────────────────────────────────────────────────┤
│ ✓ Declaraciones de funciones válidas                       │
│ ✓ Estructuras de control bien formadas                     │
│ ✓ Uso correcto de delimitadores                            │
│ ✓ Indentación apropiada                                    │
│ ✓ Sintaxis de Python correcta                              │
└─────────────────────────────────────────────────────────────┘
"""
        
        self.texto_sintactico.insert('1.0', sintactico_info)
        
        # SEMÁNTICO
        semantico_info = """
╔══════════════════════════════════════════════════════════════╗
║                      ANÁLISIS SEMÁNTICO                      ║
╚══════════════════════════════════════════════════════════════╝

"""
        if resultado['errores_semanticos']:
            semantico_info += "ERRORES ENCONTRADOS:\\n"
            semantico_info += "┌─────┬─────────┬──────────┬──────────────────────────────┐\\n"
            semantico_info += "│ No. │  Línea  │ Columna  │           Descripción        │\\n"
            semantico_info += "├─────┼─────────┼──────────┼──────────────────────────────┤\\n"
            for i, error in enumerate(resultado['errores_semanticos'], 1):
                linea = str(error.linea)
                columna = str(error.columna)
                desc = error.mensaje[:28] + "..." if len(error.mensaje) > 28 else error.mensaje
                semantico_info += f"│ {i:2d}  │  {linea:5s}  │   {columna:5s}  │ {desc:28s} │\\n"
            semantico_info += "└─────┴─────────┴──────────┴──────────────────────────────┘\\n\\n"
            
            # Detalles de sugerencias
            semantico_info += "💡 SUGERENCIAS:\\n"
            semantico_info += "┌─────┬─────────────────────────────────────────────────────┐\\n"
            semantico_info += "│ No. │                    Sugerencia                       │\\n"
            semantico_info += "├─────┼─────────────────────────────────────────────────────┤\\n"
            for i, error in enumerate(resultado['errores_semanticos'], 1):
                if error.sugerencia:
                    sug = error.sugerencia[:55] + "..." if len(error.sugerencia) > 55 else error.sugerencia
                    semantico_info += f"│ {i:2d}  │ {sug:55s} │\\n"
                else:
                    semantico_info += f"│ {i:2d}  │ {'Sin sugerencia disponible':55s} │\\n"
            semantico_info += "└─────┴─────────────────────────────────────────────────────┘\\n"
        elif resultado['errores_lexicos'] or resultado['errores_sintacticos']:
            semantico_info += """⚠️ ANÁLISIS SEMÁNTICO OMITIDO
────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────┐
│                          MOTIVO                             │
├─────────────────────────────────────────────────────────────┤
│ El análisis semántico no se pudo completar debido a        │
│ errores en las fases anteriores. Corrija primero los       │
│ errores léxicos y sintácticos para continuar.              │
└─────────────────────────────────────────────────────────────┘
"""
        else:
            semantico_info += """✅ ANÁLISIS SEMÁNTICO EXITOSO
────────────────────────────────────────────────────────────────

┌─────────────────────────────────────────────────────────────┐
│                      VERIFICACIONES                        │
├─────────────────────────────────────────────────────────────┤
│ ✓ Todas las variables están definidas antes de su uso      │
│ ✓ Todas las funciones están declaradas correctamente       │
│ ✓ No hay referencias a elementos inexistentes              │
│ ✓ Los tipos de datos son consistentes                      │
│ ✓ Uso correcto de funciones built-in                       │
└─────────────────────────────────────────────────────────────┘
"""
        
        self.texto_semantico.insert('1.0', semantico_info)
        
        # ESTADÍSTICAS
        palabras_reservadas = len([t for t in resultado['tokens'] if t.tipo == TipoToken.PALABRA_RESERVADA])
        identificadores = len([t for t in resultado['tokens'] if t.tipo == TipoToken.IDENTIFICADOR])
        numeros = len([t for t in resultado['tokens'] if t.tipo == TipoToken.NUMERO])
        strings = len([t for t in resultado['tokens'] if t.tipo == TipoToken.STRING])
        operadores = len([t for t in resultado['tokens'] if t.tipo == TipoToken.OPERADOR])
        delimitadores = len([t for t in resultado['tokens'] if t.tipo == TipoToken.DELIMITADOR])
        
        stats_info = f"""
╔══════════════════════════════════════════════════════════════╗
║                        ESTADÍSTICAS                          ║
╚══════════════════════════════════════════════════════════════╝

📈 MÉTRICAS DEL CÓDIGO:
┌──────────────────────────┬─────────┬────────────────────────┐
│          Tipo            │  Cant.  │      Porcentaje        │
├──────────────────────────┼─────────┼────────────────────────┤
│ Total de tokens          │ {len(resultado['tokens']):6d}  │        100.0%          │
│ Palabras reservadas      │ {palabras_reservadas:6d}  │ {(palabras_reservadas/max(len(resultado['tokens']),1)*100):20.1f}% │
│ Identificadores          │ {identificadores:6d}  │ {(identificadores/max(len(resultado['tokens']),1)*100):20.1f}% │
│ Números                  │ {numeros:6d}  │ {(numeros/max(len(resultado['tokens']),1)*100):20.1f}% │
│ Strings                  │ {strings:6d}  │ {(strings/max(len(resultado['tokens']),1)*100):20.1f}% │
│ Operadores               │ {operadores:6d}  │ {(operadores/max(len(resultado['tokens']),1)*100):20.1f}% │
│ Delimitadores            │ {delimitadores:6d}  │ {(delimitadores/max(len(resultado['tokens']),1)*100):20.1f}% │
└──────────────────────────┴─────────┴────────────────────────┘

📊 ANÁLISIS DE ERRORES:
┌──────────────────────────┬─────────┬────────────────────────┐
│      Fase de Análisis    │ Errores │       Estado           │
├──────────────────────────┼─────────┼────────────────────────┤
│ Análisis Léxico          │ {len(resultado['errores_lexicos']):6d}  │ {'✅ Correcto' if len(resultado['errores_lexicos'])==0 else '❌ Con errores':22s} │
│ Análisis Sintáctico      │ {len(resultado['errores_sintacticos']):6d}  │ {'✅ Correcto' if len(resultado['errores_sintacticos'])==0 else '❌ Con errores':22s} │
│ Análisis Semántico       │ {len(resultado['errores_semanticos']):6d}  │ {'✅ Correcto' if len(resultado['errores_semanticos'])==0 else '❌ Con errores':22s} │
├──────────────────────────┼─────────┼────────────────────────┤
│ TOTAL DE ERRORES         │ {resultado['total_errores']:6d}  │ {'🎉 ÉXITO TOTAL' if resultado['exito'] else '⚠️ REQUIERE CORRECCIÓN':22s} │
└──────────────────────────┴─────────┴────────────────────────┘

🎯 CALIDAD DEL CÓDIGO:
┌─────────────────────────────────────────────────────────────┐
│                         RESULTADO                           │
├─────────────────────────────────────────────────────────────┤
│ {('🏆 EXCELENTE - Su código está perfecto y listo para' if resultado['exito'] else '🔧 NECESITA MEJORAS - Corrija los errores antes de'):59s} │
│ {'    ejecutar sin problemas. ¡Felicitaciones!' if resultado['exito'] else '    continuar. Revise cada fase de análisis.':59s} │
└─────────────────────────────────────────────────────────────┘
"""
        
        self.texto_stats.insert('1.0', stats_info)
        
        # Seleccionar pestaña de resumen
        self.notebook.select(0)
    
    def limpiar_codigo(self):
        """Limpia el editor"""
        self.editor.delete('1.0', tk.END)
        self.actualizar_numeros()
        self.status.config(text="🧹 Editor limpiado", bg=self.colores['amarillo'])
    
    def cargar_ejemplo(self):
        """Carga el código de ejemplo"""
        self.editor.delete('1.0', tk.END)
        self.editor.insert('1.0', self.codigo_ejemplo)
        self.actualizar_numeros()
        self.status.config(text="📝 Ejemplo cargado", bg=self.colores['azul'])
    
    def mostrar_ayuda(self):
        """Muestra ayuda"""
        ayuda = """
🐍 COMPILADOR PYTHON - AYUDA

CARACTERÍSTICAS:
• Análisis léxico completo
• Verificación sintáctica
• Análisis semántico inteligente
• Detección precisa de errores
• Interfaz moderna de dos paneles

CONTROLES:
🚀 COMPILAR: Analiza el código
🧹 LIMPIAR: Borra el editor
📝 EJEMPLO: Carga código de ejemplo
❓ AYUDA: Muestra esta información

PESTAÑAS:
📋 RESUMEN: Vista general de resultados
🔤 TOKENS: Lista de tokens generados
🔧 SINTÁCTICO: Errores de sintaxis
🧠 SEMÁNTICO: Errores semánticos
📈 ESTADÍSTICAS: Métricas del código
"""
        messagebox.showinfo("❓ Ayuda", ayuda)
    
    def ejecutar(self):
        """Ejecuta la aplicación"""
        self.ventana.mainloop()

def main():
    """Función principal"""
    print("🚀 Iniciando Compilador Python con Interfaz Moderna...")
    try:
        app = InterfazModerna()
        app.ejecutar()
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()