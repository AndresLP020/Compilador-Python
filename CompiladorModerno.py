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
        """Crea los botones de control con barra deslizadora"""
        # Frame contenedor principal para los botones
        contenedor_botones = tk.Frame(parent, bg=self.colores['panel'], height=80)
        contenedor_botones.pack(fill=tk.X, padx=15, pady=(0, 15))
        contenedor_botones.pack_propagate(False)
        
        # Canvas para permitir scroll horizontal
        canvas_botones = tk.Canvas(contenedor_botones, 
                                 bg=self.colores['panel'], 
                                 height=70,
                                 highlightthickness=0)
        canvas_botones.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Scrollbar horizontal
        scrollbar_h = tk.Scrollbar(contenedor_botones, 
                                 orient=tk.HORIZONTAL, 
                                 command=canvas_botones.xview,
                                 bg=self.colores['borde'],
                                 troughcolor=self.colores['panel'],
                                 activebackground=self.colores['azul'])
        scrollbar_h.pack(side=tk.BOTTOM, fill=tk.X)
        canvas_botones.configure(xscrollcommand=scrollbar_h.set)
        
        # Frame interno para los botones
        botones_frame = tk.Frame(canvas_botones, bg=self.colores['panel'])
        canvas_botones.create_window((0, 0), window=botones_frame, anchor="nw")
        
        # Estilo de botones mejorado
        btn_config = {
            'font': ("Segoe UI", 11, "bold"),
            'relief': tk.FLAT,
            'cursor': 'hand2',
            'pady': 10,
            'padx': 20,
            'width': 12,  # Ancho fijo para consistencia
            'height': 2   # Altura fija
        }
        
        # Lista de botones con sus configuraciones
        botones_info = [
            {
                'text': "🚀 COMPILAR",
                'bg': self.colores['verde'],
                'fg': 'white',
                'active_bg': '#2ea043',
                'command': self.compilar_codigo,
                'tooltip': 'Analiza el código Python completo'
            },
            {
                'text': "🧹 LIMPIAR",
                'bg': self.colores['amarillo'],
                'fg': 'white',
                'active_bg': '#bf8700',
                'command': self.limpiar_codigo,
                'tooltip': 'Limpia todo el contenido del editor'
            },
            {
                'text': "📝 EJEMPLO",
                'bg': self.colores['azul'],
                'fg': 'white',
                'active_bg': '#1f6feb',
                'command': self.cargar_ejemplo,
                'tooltip': 'Carga código de ejemplo para probar'
            },
            {
                'text': "📚 REGLAS",
                'bg': '#6f42c1',  # Morado
                'fg': 'white',
                'active_bg': '#5a2d91',
                'command': self.mostrar_reglas_ventana,
                'tooltip': 'Muestra las reglas gramaticales en ventana separada'
            },
            {
                'text': "💾 GUARDAR",
                'bg': '#28a745',  # Verde oscuro
                'fg': 'white',
                'active_bg': '#1e7e34',
                'command': self.guardar_codigo,
                'tooltip': 'Guarda el código actual en un archivo'
            },
            {
                'text': "📂 ABRIR",
                'bg': '#17a2b8',  # Cyan
                'fg': 'white',
                'active_bg': '#138496',
                'command': self.abrir_codigo,
                'tooltip': 'Abre un archivo de código Python'
            },
            {
                'text': "❓ AYUDA",
                'bg': self.colores['borde'],
                'fg': self.colores['texto'],
                'active_bg': '#484f58',
                'command': self.mostrar_ayuda,
                'tooltip': 'Muestra información de ayuda'
            }
        ]
        
        # Crear botones
        self.botones = []
        for i, info in enumerate(botones_info):
            btn = tk.Button(botones_frame,
                          text=info['text'],
                          bg=info['bg'],
                          fg=info['fg'],
                          activebackground=info['active_bg'],
                          command=info['command'],
                          **btn_config)
            btn.pack(side=tk.LEFT, padx=(0, 10), pady=5)
            
            # Agregar tooltip
            self.crear_tooltip(btn, info['tooltip'])
            self.botones.append(btn)
        
        # Configurar el scroll region después de que todos los botones estén creados
        botones_frame.update_idletasks()
        canvas_botones.configure(scrollregion=canvas_botones.bbox("all"))
        
        # Bind para scroll con rueda del mouse
        def scroll_horizontal(event):
            canvas_botones.xview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas_botones.bind("<MouseWheel>", scroll_horizontal)
        botones_frame.bind("<MouseWheel>", scroll_horizontal)
    
    def crear_tooltip(self, widget, text):
        """Crea un tooltip para un widget"""
        def mostrar_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            tooltip.configure(bg=self.colores['borde'])
            
            label = tk.Label(tooltip, 
                           text=text,
                           bg=self.colores['borde'],
                           fg=self.colores['texto'],
                           font=("Segoe UI", 9),
                           relief=tk.SOLID,
                           borderwidth=1,
                           padx=5,
                           pady=3)
            label.pack()
            
            # Destruir tooltip después de 3 segundos
            tooltip.after(3000, tooltip.destroy)
        
        def ocultar_tooltip(event):
            pass
        
        widget.bind("<Enter>", mostrar_tooltip)
        widget.bind("<Leave>", ocultar_tooltip)
    
    def mostrar_reglas_ventana(self):
        """Muestra las reglas gramaticales en una ventana separada"""
        ventana_reglas = tk.Toplevel(self.ventana)
        ventana_reglas.title("📚 Reglas Gramaticales de Python")
        ventana_reglas.geometry("800x600")
        ventana_reglas.configure(bg=self.colores['fondo'])
        
        # Header
        header = tk.Frame(ventana_reglas, bg=self.colores['azul'], height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header,
                text="📚 REGLAS GRAMATICALES DE PYTHON",
                font=("Segoe UI", 16, "bold"),
                bg=self.colores['azul'],
                fg='white').pack(pady=15)
        
        # Área de texto con scroll
        texto_reglas = scrolledtext.ScrolledText(ventana_reglas,
                                               font=("Consolas", 10),
                                               bg=self.colores['resultados'],
                                               fg=self.colores['texto'],
                                               relief=tk.FLAT,
                                               wrap=tk.WORD)
        texto_reglas.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Contenido de reglas (reutilizando el mismo contenido)
        reglas_contenido = """
╔══════════════════════════════════════════════════════════════╗
║                 REGLAS GRAMATICALES DE PYTHON                ║
╚══════════════════════════════════════════════════════════════╝

📝 ESTRUCTURA GENERAL DEL LENGUAJE:
────────────────────────────────────────────────────────────────

🔹 PROGRAMA:
   programa ::= (declaracion | sentencia)*

🔹 DECLARACIONES:
   declaracion ::= def_funcion | def_clase | import_stmt
   
   def_funcion ::= 'def' IDENTIFICADOR '(' parametros ')' ':' bloque
   parametros  ::= (IDENTIFICADOR (',' IDENTIFICADOR)*)?
   
   def_clase   ::= 'class' IDENTIFICADOR ('(' herencia ')')? ':' bloque
   herencia    ::= IDENTIFICADOR (',' IDENTIFICADOR)*
   
   import_stmt ::= 'import' modulo | 'from' modulo 'import' nombres
   modulo      ::= IDENTIFICADOR ('.' IDENTIFICADOR)*
   nombres     ::= IDENTIFICADOR (',' IDENTIFICADOR)*

📐 ESTRUCTURAS DE CONTROL:
────────────────────────────────────────────────────────────────

🔹 CONDICIONALES:
   if_stmt   ::= 'if' expresion ':' bloque elif_clause* else_clause?
   elif_clause ::= 'elif' expresion ':' bloque
   else_clause ::= 'else' ':' bloque

🔹 BUCLES:
   for_stmt   ::= 'for' IDENTIFICADOR 'in' expresion ':' bloque
   while_stmt ::= 'while' expresion ':' bloque

🔹 MANEJO DE EXCEPCIONES:
   try_stmt     ::= 'try' ':' bloque except_clause+ finally_clause?
                  | 'try' ':' bloque finally_clause
   except_clause ::= 'except' (tipo_excepcion ('as' IDENTIFICADOR)?)? ':' bloque
   finally_clause ::= 'finally' ':' bloque

🔹 CONTEXTO:
   with_stmt ::= 'with' expresion ('as' IDENTIFICADOR)? ':' bloque

📊 EXPRESIONES Y OPERADORES:
────────────────────────────────────────────────────────────────

🔹 EXPRESIONES:
   expresion ::= expr_or
   expr_or   ::= expr_and ('or' expr_and)*
   expr_and  ::= expr_not ('and' expr_not)*
   expr_not  ::= 'not' expr_not | comparacion
   
   comparacion ::= expr_aritmetica (comp_op expr_aritmetica)*
   comp_op     ::= '<' | '>' | '==' | '>=' | '<=' | '!=' | 'in' | 'not' 'in' | 'is' | 'is' 'not'

🔹 OPERADORES ARITMÉTICOS:
   expr_aritmetica ::= termino (('+' | '-') termino)*
   termino        ::= factor (('*' | '/' | '//' | '%') factor)*
   factor         ::= ('+' | '-')? potencia
   potencia       ::= atom ('**' factor)?

🔹 ÁTOMICOS:
   atom ::= IDENTIFICADOR | NUMERO | STRING | 'True' | 'False' | 'None'
          | '(' expresion ')' | lista | diccionario | llamada_funcion

📚 TOKENS Y LEXEMAS:
────────────────────────────────────────────────────────────────

🔹 IDENTIFICADORES:
   IDENTIFICADOR ::= (letra | '_') (letra | digito | '_')*
   letra         ::= [a-zA-Z]
   digito        ::= [0-9]

🔹 NÚMEROS:
   NUMERO ::= ENTERO | DECIMAL | CIENTIFICO | BINARIO | OCTAL | HEXADECIMAL
   
   ENTERO     ::= digito+
   DECIMAL    ::= digito+ '.' digito* | '.' digito+
   CIENTIFICO ::= (ENTERO | DECIMAL) [eE] [+-]? digito+
   BINARIO    ::= '0' [bB] [01]+
   OCTAL      ::= '0' [oO] [0-7]+
   HEXADECIMAL::= '0' [xX] [0-9a-fA-F]+

🔹 CADENAS:
   STRING ::= STRING_SIMPLE | STRING_TRIPLE
   STRING_SIMPLE ::= ('"' contenido_simple '"') | ("'" contenido_simple "'")
   STRING_TRIPLE ::= ('"""' contenido_triple '"""') | ("'''" contenido_triple "'''")

🔹 PALABRAS RESERVADAS:
   False    None     True     and      as       assert   async    await
   break    class    continue def      del      elif     else     except
   finally  for      from     global   if       import   in       is
   lambda   nonlocal not      or       pass     raise    return   try
   while    with     yield

✅ REGLAS DE CORRECCIÓN:
────────────────────────────────────────────────────────────────

• Toda función debe terminar con ':' seguido de bloque indentado
• Toda estructura de control (if, for, while) requiere ':'
• Los paréntesis deben estar balanceados
• Las comillas de strings deben estar cerradas
• Los identificadores no pueden ser palabras reservadas
• La indentación debe ser consistente dentro del mismo bloque
• Las variables deben estar definidas antes de su uso
• Las funciones deben estar declaradas antes de ser llamadas
"""
        
        texto_reglas.insert('1.0', reglas_contenido)
        texto_reglas.config(state=tk.DISABLED)
    
    def guardar_codigo(self):
        """Guarda el código actual en un archivo"""
        from tkinter import filedialog
        
        archivo = filedialog.asksaveasfilename(
            title="Guardar código Python",
            defaultextension=".py",
            filetypes=[("Archivos Python", "*.py"), ("Todos los archivos", "*.*")]
        )
        
        if archivo:
            try:
                with open(archivo, 'w', encoding='utf-8') as f:
                    contenido = self.editor.get('1.0', tk.END)
                    f.write(contenido.rstrip())  # Remover salto de línea final extra
                
                messagebox.showinfo("✅ Éxito", f"Código guardado exitosamente en:\n{archivo}")
                self.status.config(text="💾 Código guardado", bg=self.colores['verde'])
            except Exception as e:
                messagebox.showerror("❌ Error", f"No se pudo guardar el archivo:\n{str(e)}")
    
    def abrir_codigo(self):
        """Abre un archivo de código Python"""
        from tkinter import filedialog
        
        archivo = filedialog.askopenfilename(
            title="Abrir código Python",
            filetypes=[("Archivos Python", "*.py"), ("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
        )
        
        if archivo:
            try:
                with open(archivo, 'r', encoding='utf-8') as f:
                    contenido = f.read()
                
                self.editor.delete('1.0', tk.END)
                self.editor.insert('1.0', contenido)
                self.actualizar_numeros()
                
                messagebox.showinfo("✅ Éxito", f"Archivo cargado exitosamente:\n{archivo}")
                self.status.config(text="📂 Archivo cargado", bg=self.colores['azul'])
            except Exception as e:
                messagebox.showerror("❌ Error", f"No se pudo abrir el archivo:\n{str(e)}")
    
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
        """Crea el notebook con pestañas mejorado con scroll"""
        # Frame principal para el notebook
        notebook_container = tk.Frame(parent, bg=self.colores['panel'])
        notebook_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Frame superior para pestañas con scroll
        pestañas_frame = tk.Frame(notebook_container, bg=self.colores['panel'], height=50)
        pestañas_frame.pack(fill=tk.X, pady=(0, 5))
        pestañas_frame.pack_propagate(False)
        
        # Canvas para scroll horizontal de pestañas
        canvas_pestañas = tk.Canvas(pestañas_frame, 
                                  bg=self.colores['panel'], 
                                  height=45,
                                  highlightthickness=0)
        canvas_pestañas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Scrollbar horizontal para pestañas
        scrollbar_pestañas = tk.Scrollbar(pestañas_frame, 
                                        orient=tk.HORIZONTAL, 
                                        command=canvas_pestañas.xview,
                                        bg=self.colores['borde'],
                                        troughcolor=self.colores['panel'],
                                        activebackground=self.colores['azul'])
        scrollbar_pestañas.pack(side=tk.BOTTOM, fill=tk.X)
        canvas_pestañas.configure(xscrollcommand=scrollbar_pestañas.set)
        
        # Frame interno para botones de pestañas
        botones_pestañas_frame = tk.Frame(canvas_pestañas, bg=self.colores['panel'])
        canvas_pestañas.create_window((0, 0), window=botones_pestañas_frame, anchor="nw")
        
        # Frame para contenido de pestañas
        self.contenido_frame = tk.Frame(notebook_container, bg=self.colores['resultados'])
        self.contenido_frame.pack(fill=tk.BOTH, expand=True)
        
        # Crear botones de pestañas y frames de contenido
        self.crear_pestañas_mejoradas(botones_pestañas_frame, canvas_pestañas)
    
    def crear_pestañas_mejoradas(self, parent_botones, canvas_pestañas):
        """Crea las pestañas con botones mejorados"""
        # Lista de pestañas con información
        pestañas_info = [
            {
                'id': 'resumen',
                'texto': '📋 RESUMEN',
                'descripcion': 'Vista general de resultados',
                'color': self.colores['verde'],
                'tipo': 'texto'
            },
            {
                'id': 'tokens',
                'texto': '🔤 TOKENS',
                'descripcion': 'Lista de tokens generados',
                'color': self.colores['azul'],
                'tipo': 'tabla',
                'columnas': ['No.', 'Tipo', 'Valor', 'Línea']
            },
            {
                'id': 'sintactico',
                'texto': '🔧 SINTÁCTICO',
                'descripcion': 'Errores de sintaxis',
                'color': self.colores['amarillo'],
                'tipo': 'mixto'
            },
            {
                'id': 'semantico',
                'texto': '🧠 SEMÁNTICO',
                'descripcion': 'Errores semánticos',
                'color': '#6f42c1',  # Morado
                'tipo': 'mixto'
            },
            {
                'id': 'reglas',
                'texto': '📚 REGLAS GRAM.',
                'descripcion': 'Reglas gramaticales de Python',
                'color': '#17a2b8',  # Cyan
                'tipo': 'texto'
            },
            {
                'id': 'estadisticas',
                'texto': '📈 ESTADÍSTICAS',
                'descripcion': 'Métricas del código',
                'color': self.colores['rojo'],
                'tipo': 'tabla',
                'columnas': ['Métrica', 'Valor', 'Porcentaje']
            }
        ]
        
        # Variables para manejo de pestañas
        self.pestañas_activa = 'resumen'
        self.botones_pestañas = {}
        self.frames_contenido = {}
        self.areas_texto = {}
        self.tablas = {}
        
        # Crear botones de pestañas
        for i, info in enumerate(pestañas_info):
            # Crear botón de pestaña
            btn = tk.Button(parent_botones,
                          text=info['texto'],
                          font=("Segoe UI", 10, "bold"),
                          bg=info['color'] if info['id'] == 'resumen' else self.colores['borde'],
                          fg='white' if info['id'] == 'resumen' else self.colores['texto'],
                          relief=tk.FLAT,
                          cursor='hand2',
                          padx=15,
                          pady=8,
                          width=15,
                          command=lambda x=info['id']: self.cambiar_pestaña(x))
            btn.pack(side=tk.LEFT, padx=(0, 5), pady=2)
            
            # Agregar tooltip
            self.crear_tooltip(btn, info['descripcion'])
            
            # Guardar referencia
            self.botones_pestañas[info['id']] = {
                'boton': btn,
                'color': info['color'],
                'info': info
            }
            
            # Crear frame de contenido
            frame_contenido = tk.Frame(self.contenido_frame, bg=self.colores['resultados'])
            if info['id'] == 'resumen':
                frame_contenido.pack(fill=tk.BOTH, expand=True)
            
            self.frames_contenido[info['id']] = frame_contenido
            
            # Crear área según el tipo
            if info['tipo'] == 'tabla':
                tabla, frame_tabla = self.crear_area_tabla(frame_contenido, info['columnas'])
                self.tablas[info['id']] = tabla
                self.areas_texto[info['id']] = None  # Para compatibilidad
            elif info['tipo'] == 'mixto':
                # Para pestañas mixtas, crear un notebook interno
                notebook_mixto = ttk.Notebook(frame_contenido)
                notebook_mixto.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
                
                # Frame para tabla
                frame_tabla_tab = tk.Frame(notebook_mixto, bg=self.colores['resultados'])
                notebook_mixto.add(frame_tabla_tab, text="📊 Tabla")
                
                # Frame para texto
                frame_texto_tab = tk.Frame(notebook_mixto, bg=self.colores['resultados'])
                notebook_mixto.add(frame_texto_tab, text="📝 Detalle")
                
                # Crear tabla
                if info['id'] == 'sintactico':
                    tabla, _ = self.crear_area_tabla(frame_tabla_tab, ['No.', 'Línea', 'Columna', 'Descripción'])
                else:  # semántico
                    tabla, _ = self.crear_area_tabla(frame_tabla_tab, ['No.', 'Línea', 'Columna', 'Descripción'])
                
                self.tablas[info['id']] = tabla
                
                # Crear área de texto para detalles
                area_texto = self.crear_area_texto(frame_texto_tab)
                self.areas_texto[info['id']] = area_texto
            else:
                # Crear área de texto normal
                area_texto = self.crear_area_texto(frame_contenido)
                self.areas_texto[info['id']] = area_texto
                self.tablas[info['id']] = None
        
        # Configurar scroll region
        parent_botones.update_idletasks()
        canvas_pestañas.configure(scrollregion=canvas_pestañas.bbox("all"))
        
        # Bind para scroll con rueda del mouse en pestañas
        def scroll_pestañas(event):
            canvas_pestañas.xview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas_pestañas.bind("<MouseWheel>", scroll_pestañas)
        parent_botones.bind("<MouseWheel>", scroll_pestañas)
        
        # Asignar las áreas de texto a las variables existentes para compatibilidad
        self.texto_resumen = self.areas_texto['resumen']
        self.texto_tokens = self.areas_texto['tokens']  # Será None, usaremos tabla
        self.texto_sintactico = self.areas_texto['sintactico']
        self.texto_semantico = self.areas_texto['semantico']
        self.texto_reglas = self.areas_texto['reglas']
        self.texto_stats = self.areas_texto['estadisticas']  # Será None, usaremos tabla
    
    def cambiar_pestaña(self, pestaña_id):
        """Cambia la pestaña activa"""
        # Ocultar frame actual
        if self.pestañas_activa in self.frames_contenido:
            self.frames_contenido[self.pestañas_activa].pack_forget()
            
            # Cambiar color del botón anterior a inactivo
            btn_anterior = self.botones_pestañas[self.pestañas_activa]['boton']
            btn_anterior.config(bg=self.colores['borde'], fg=self.colores['texto'])
        
        # Mostrar nueva pestaña
        if pestaña_id in self.frames_contenido:
            self.frames_contenido[pestaña_id].pack(fill=tk.BOTH, expand=True)
            
            # Cambiar color del botón nuevo a activo
            info_nueva = self.botones_pestañas[pestaña_id]
            btn_nuevo = info_nueva['boton']
            btn_nuevo.config(bg=info_nueva['color'], fg='white')
            
            # Actualizar pestaña activa
            self.pestañas_activa = pestaña_id
            
            # Actualizar status
            descripcion = info_nueva['info']['descripcion']
            self.status.config(text=f"📊 Viendo: {descripcion}", bg=info_nueva['color'])
    
    def poblar_tabla_tokens(self, tokens):
        """Pobla la tabla de tokens"""
        tabla = self.tablas['tokens']
        
        # Limpiar tabla
        for item in tabla.get_children():
            tabla.delete(item)
        
        # Agregar tokens
        for i, token in enumerate(tokens[:100], 1):  # Limitar a 100 tokens
            tabla.insert('', 'end', values=(
                i,
                token.tipo.value,
                str(token.valor)[:30] + ("..." if len(str(token.valor)) > 30 else ""),
                token.linea
            ))
    
    def poblar_tabla_errores(self, pestaña_id, errores):
        """Pobla la tabla de errores (sintáctico o semántico)"""
        tabla = self.tablas[pestaña_id]
        
        # Limpiar tabla
        for item in tabla.get_children():
            tabla.delete(item)
        
        # Agregar errores
        for i, error in enumerate(errores, 1):
            desc = error.mensaje[:50] + ("..." if len(error.mensaje) > 50 else "")
            tabla.insert('', 'end', values=(
                i,
                error.linea,
                error.columna,
                desc
            ))
    
    def poblar_tabla_estadisticas(self, resultado):
        """Pobla la tabla de estadísticas"""
        tabla = self.tablas['estadisticas']
        
        # Limpiar tabla
        for item in tabla.get_children():
            tabla.delete(item)
        
        # Calcular estadísticas
        total_tokens = len(resultado['tokens'])
        palabras_reservadas = len([t for t in resultado['tokens'] if t.tipo == TipoToken.PALABRA_RESERVADA])
        identificadores = len([t for t in resultado['tokens'] if t.tipo == TipoToken.IDENTIFICADOR])
        numeros = len([t for t in resultado['tokens'] if t.tipo == TipoToken.NUMERO])
        strings = len([t for t in resultado['tokens'] if t.tipo == TipoToken.STRING])
        operadores = len([t for t in resultado['tokens'] if t.tipo == TipoToken.OPERADOR])
        delimitadores = len([t for t in resultado['tokens'] if t.tipo == TipoToken.DELIMITADOR])
        
        # Datos para la tabla
        datos_estadisticas = [
            ("Total de tokens", str(total_tokens), "100.0%"),
            ("Palabras reservadas", str(palabras_reservadas), f"{(palabras_reservadas/max(total_tokens,1)*100):.1f}%"),
            ("Identificadores", str(identificadores), f"{(identificadores/max(total_tokens,1)*100):.1f}%"),
            ("Números", str(numeros), f"{(numeros/max(total_tokens,1)*100):.1f}%"),
            ("Strings", str(strings), f"{(strings/max(total_tokens,1)*100):.1f}%"),
            ("Operadores", str(operadores), f"{(operadores/max(total_tokens,1)*100):.1f}%"),
            ("Delimitadores", str(delimitadores), f"{(delimitadores/max(total_tokens,1)*100):.1f}%"),
            ("", "", ""),
            ("Errores léxicos", str(len(resultado['errores_lexicos'])), ""),
            ("Errores sintácticos", str(len(resultado['errores_sintacticos'])), ""),
            ("Errores semánticos", str(len(resultado['errores_semanticos'])), ""),
            ("Total errores", str(resultado['total_errores']), ""),
            ("", "", ""),
            ("Estado general", "✅ ÉXITO" if resultado['exito'] else "❌ CON ERRORES", "")
        ]
        
        # Agregar datos a la tabla
        for metrica, valor, porcentaje in datos_estadisticas:
            tabla.insert('', 'end', values=(metrica, valor, porcentaje))
    
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
    
    def crear_area_tabla(self, parent, columnas):
        """Crea un área con tabla profesional usando Treeview"""
        # Frame contenedor
        frame_tabla = tk.Frame(parent, bg=self.colores['resultados'])
        frame_tabla.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Estilo para el Treeview
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configurar colores del Treeview
        style.configure("Custom.Treeview",
                       background=self.colores['resultados'],
                       foreground=self.colores['texto'],
                       fieldbackground=self.colores['resultados'],
                       borderwidth=0,
                       font=("Segoe UI", 10))
        
        style.configure("Custom.Treeview.Heading",
                       background=self.colores['azul'],
                       foreground='white',
                       relief='flat',
                       font=("Segoe UI", 11, "bold"))
        
        style.map("Custom.Treeview",
                 background=[('selected', self.colores['azul'])],
                 foreground=[('selected', 'white')])
        
        # Crear Treeview
        tabla = ttk.Treeview(frame_tabla, 
                           columns=columnas,
                           show='tree headings',
                           style="Custom.Treeview",
                           height=15)
        
        # Configurar columnas
        tabla.heading('#0', text='', anchor='w')
        tabla.column('#0', width=0, stretch=False)  # Ocultar primera columna
        
        for col in columnas:
            tabla.heading(col, text=col, anchor='center')
            if col == 'Descripción' or col == 'Sugerencia':
                tabla.column(col, width=300, anchor='w')
            elif col == 'No.':
                tabla.column(col, width=50, anchor='center')
            else:
                tabla.column(col, width=100, anchor='center')
        
        # Scrollbars
        scrollbar_v = ttk.Scrollbar(frame_tabla, orient="vertical", command=tabla.yview)
        scrollbar_h = ttk.Scrollbar(frame_tabla, orient="horizontal", command=tabla.xview)
        tabla.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
        
        # Pack elementos
        tabla.pack(side="left", fill="both", expand=True)
        scrollbar_v.pack(side="right", fill="y")
        scrollbar_h.pack(side="bottom", fill="x")
        
        return tabla, frame_tabla
    
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
        # Limpiar todas las áreas de texto
        for area in [self.texto_resumen, self.texto_sintactico, 
                    self.texto_semantico, self.texto_reglas]:
            if area:
                area.delete('1.0', tk.END)
        
        # Limpiar todas las tablas
        for tabla_id, tabla in self.tablas.items():
            if tabla:
                for item in tabla.get_children():
                    tabla.delete(item)
        
        # Actualizar status
        if resultado['exito']:
            self.status.config(text="✅ Compilación exitosa", bg=self.colores['verde'])
        else:
            self.status.config(text=f"❌ {resultado['total_errores']} errores", bg=self.colores['rojo'])
        
        # Poblar tablas específicas
        if resultado['tokens']:
            self.poblar_tabla_tokens(resultado['tokens'])
        
        if resultado['errores_sintacticos']:
            self.poblar_tabla_errores('sintactico', resultado['errores_sintacticos'])
        
        if resultado['errores_semanticos']:
            self.poblar_tabla_errores('semantico', resultado['errores_semanticos'])
        
        self.poblar_tabla_estadisticas(resultado)
        
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
        
        if self.texto_resumen:
            self.texto_resumen.insert('1.0', resumen)
        
        # SINTÁCTICO (área de texto para detalles)
        if self.texto_sintactico:
            sintactico_detalle = """🔧 ANÁLISIS SINTÁCTICO DETALLADO\n\n"""
            if resultado['errores_sintacticos']:
                for i, error in enumerate(resultado['errores_sintacticos'], 1):
                    sintactico_detalle += f"ERROR #{i}: {error.mensaje}\n"
                    sintactico_detalle += f"Línea {error.linea}, Columna {error.columna}\n"
                    if error.sugerencia:
                        sintactico_detalle += f"Sugerencia: {error.sugerencia}\n"
                    sintactico_detalle += "\n"
            else:
                sintactico_detalle += "✅ Sin errores sintácticos detectados.\n"
            
            self.texto_sintactico.insert('1.0', sintactico_detalle)
        
        # SEMÁNTICO (área de texto para detalles)
        if self.texto_semantico:
            semantico_detalle = """🧠 ANÁLISIS SEMÁNTICO DETALLADO\n\n"""
            if resultado['errores_semanticos']:
                for i, error in enumerate(resultado['errores_semanticos'], 1):
                    semantico_detalle += f"ERROR #{i}: {error.mensaje}\n"
                    semantico_detalle += f"Línea {error.linea}, Columna {error.columna}\n"
                    if error.sugerencia:
                        semantico_detalle += f"Sugerencia: {error.sugerencia}\n"
                    semantico_detalle += "\n"
            else:
                semantico_detalle += "✅ Sin errores semánticos detectados.\n"
            
            self.texto_semantico.insert('1.0', semantico_detalle)
        
        # REGLAS GRAMATICALES (mantener como texto)
        if self.texto_reglas:
            reglas_info = """
╔══════════════════════════════════════════════════════════════╗
║                 REGLAS GRAMATICALES DE PYTHON                ║
╚══════════════════════════════════════════════════════════════╝

📝 ESTRUCTURA GENERAL DEL LENGUAJE:
────────────────────────────────────────────────────────────────
🔹 PROGRAMA: programa ::= (declaracion | sentencia)*
🔹 DECLARACIONES: def_funcion | def_clase | import_stmt
🔹 CONDICIONALES: if_stmt | elif_clause | else_clause  
🔹 BUCLES: for_stmt | while_stmt
🔹 EXCEPCIONES: try_stmt | except_clause | finally_clause
🔹 CONTEXTO: with_stmt

📚 TOKENS Y LEXEMAS:
────────────────────────────────────────────────────────────────
🔹 IDENTIFICADORES: (letra | '_') (letra | digito | '_')*
🔹 NÚMEROS: ENTERO | DECIMAL | CIENTIFICO | BINARIO | OCTAL | HEXADECIMAL
🔹 PALABRAS RESERVADAS: False, None, True, and, as, assert, async, await,
   break, class, continue, def, del, elif, else, except, finally, for,
   from, global, if, import, in, is, lambda, nonlocal, not, or, pass,
   raise, return, try, while, with, yield

✅ REGLAS DE CORRECCIÓN:
────────────────────────────────────────────────────────────────
• Toda función debe terminar con ':' seguido de bloque indentado
• Toda estructura de control requiere ':'
• Los paréntesis deben estar balanceados
• Las comillas de strings deben estar cerradas
• Los identificadores no pueden ser palabras reservadas
• La indentación debe ser consistente (4 espacios recomendado)
• Las variables deben estar definidas antes de su uso
• Las funciones deben estar declaradas antes de ser llamadas
"""
            if self.texto_reglas:
                self.texto_reglas.insert('1.0', reglas_info)
        
        # Seleccionar pestaña de resumen por defecto
        self.cambiar_pestaña('resumen')
        
        # TOKENS - Información básica
        tokens_info = "📊 RESUMEN DEL ANÁLISIS LÉXICO\\n\\n"
        if resultado['errores_lexicos']:
            tokens_info += f"⚠️ Se encontraron {len(resultado['errores_lexicos'])} errores léxicos\\n"
        if resultado['tokens']:
            tokens_info += f"✅ Se identificaron {len(resultado['tokens'])} tokens válidos\\n"
            if len(resultado['tokens']) > 50:
                tokens_info += f"� Mostrando los primeros 50 tokens en la tabla\\n"
        else:
            tokens_info += "⚠️ No se generaron tokens válidos debido a errores léxicos\\n"
        
        if self.texto_tokens:
            self.texto_tokens.insert('1.0', tokens_info)
        
        # SINTÁCTICO - Información básica
        
        # También llenar área de texto con información adicional
        sintactico_info = f"� RESUMEN DEL ANÁLISIS SINTÁCTICO\\n\\n"
        if resultado['errores_sintacticos']:
            sintactico_info += f"⚠️ Se encontraron {len(resultado['errores_sintacticos'])} errores sintácticos\\n"
            sintactico_info += f"💡 Consulte la tabla para ver detalles y sugerencias\\n"
        elif resultado['errores_lexicos']:
            sintactico_info += "⚠️ ANÁLISIS SINTÁCTICO OMITIDO\\n"
            sintactico_info += "──────────────────────────────\\n\\n"
            sintactico_info += "El análisis sintáctico no se pudo completar debido a\\n"
            sintactico_info += "errores en la fase léxica. Corrija primero los errores\\n"
            sintactico_info += "léxicos para continuar con el análisis sintáctico.\\n"
        else:
            sintactico_info += "✅ ANÁLISIS SINTÁCTICO EXITOSO\\n"
            sintactico_info += "─────────────────────────────\\n\\n"
            sintactico_info += "✓ Declaraciones de funciones válidas\\n"
            sintactico_info += "✓ Estructuras de control correctas\\n"
            sintactico_info += "✓ Expresiones bien formadas\\n"
            sintactico_info += "✓ Bloques correctamente delimitados\\n"
        
        if self.texto_sintactico:
            self.texto_sintactico.insert('1.0', sintactico_info)
        
        # SEMÁNTICO - Información básica
        
        # Contenido detallado para el área de texto
        semantico_info = f"🧠 ANÁLISIS SEMÁNTICO - REPORTE DETALLADO\\n"
        semantico_info += f"═══════════════════════════════════════\\n\\n"
        
        if resultado['errores_semanticos']:
            semantico_info += f"⚠️ Se detectaron {len(resultado['errores_semanticos'])} errores semánticos\\n\\n"
            semantico_info += "📋 ANÁLISIS DETALLADO:\\n"
            semantico_info += "─────────────────────\\n\\n"
            
            for i, error in enumerate(resultado['errores_semanticos'], 1):
                semantico_info += f"❌ Error #{i}:\\n"
                semantico_info += f"   📍 Ubicación: Línea {error.linea}, Columna {error.columna}\\n"
                semantico_info += f"   📝 Descripción: {error.mensaje}\\n"
                if hasattr(error, 'sugerencia') and error.sugerencia:
                    semantico_info += f"   💡 Sugerencia: {error.sugerencia}\\n"
                semantico_info += "\\n"
        else:
            semantico_info += "✅ ANÁLISIS SEMÁNTICO EXITOSO\\n"
            semantico_info += "────────────────────────────\\n\\n"
            semantico_info += "🎯 VALIDACIONES COMPLETADAS:\\n"
            semantico_info += "• Variables definidas antes de su uso\\n"
            semantico_info += "• Funciones declaradas correctamente\\n"
            semantico_info += "• Tipos de datos consistentes\\n"
            semantico_info += "• Ámbitos (scopes) respetados\\n"
            semantico_info += "• Referencias válidas\\n"
        
        if self.texto_semantico:
            self.texto_semantico.insert('1.0', semantico_info)
        
        # ESTADÍSTICAS - Información básica
        palabras_reservadas = len([t for t in resultado['tokens'] if t.tipo == TipoToken.PALABRA_RESERVADA])
        identificadores = len([t for t in resultado['tokens'] if t.tipo == TipoToken.IDENTIFICADOR])
        numeros = len([t for t in resultado['tokens'] if t.tipo == TipoToken.NUMERO])
        strings = len([t for t in resultado['tokens'] if t.tipo == TipoToken.STRING])
        operadores = len([t for t in resultado['tokens'] if t.tipo == TipoToken.OPERADOR])
        delimitadores = len([t for t in resultado['tokens'] if t.tipo == TipoToken.DELIMITADOR])
        
        stats_info = "📈 MÉTRICAS DEL CÓDIGO\\n"
        stats_info += "═══════════════════\\n\\n"
        stats_info += f"📊 Total de tokens: {len(resultado['tokens'])}\\n"
        stats_info += f"🔹 Palabras reservadas: {palabras_reservadas} ({(palabras_reservadas/max(len(resultado['tokens']),1)*100):.1f}%)\\n"
        stats_info += f"🔹 Identificadores: {identificadores} ({(identificadores/max(len(resultado['tokens']),1)*100):.1f}%)\\n"
        stats_info += f"🔹 Números: {numeros} ({(numeros/max(len(resultado['tokens']),1)*100):.1f}%)\\n"
        stats_info += f"🔹 Strings: {strings} ({(strings/max(len(resultado['tokens']),1)*100):.1f}%)\\n"
        stats_info += f"🔹 Operadores: {operadores} ({(operadores/max(len(resultado['tokens']),1)*100):.1f}%)\\n"
        stats_info += f"🔹 Delimitadores: {delimitadores} ({(delimitadores/max(len(resultado['tokens']),1)*100):.1f}%)\\n\\n"
        
        stats_info += "📊 ANÁLISIS DE ERRORES\\n"
        stats_info += "═══════════════════\\n\\n"
        stats_info += f"🔹 Errores Léxicos: {len(resultado['errores_lexicos'])} {'✅' if len(resultado['errores_lexicos'])==0 else '❌'}\\n"
        stats_info += f"🔹 Errores Sintácticos: {len(resultado['errores_sintacticos'])} {'✅' if len(resultado['errores_sintacticos'])==0 else '❌'}\\n"
        stats_info += f"🔹 Errores Semánticos: {len(resultado['errores_semanticos'])} {'✅' if len(resultado['errores_semanticos'])==0 else '❌'}\\n"
        stats_info += f"🔹 TOTAL: {resultado['total_errores']} errores {'🎉' if resultado['exito'] else '⚠️'}\\n\\n"
        
        if resultado['exito']:
            stats_info += "🎉 ¡COMPILACIÓN EXITOSA!\\n"
            stats_info += "Su código está listo para ejecutar.\\n"
        else:
            stats_info += "⚠️ Corrija los errores para continuar.\\n"
        
        if hasattr(self, 'texto_stats') and self.texto_stats:
            self.texto_stats.insert('1.0', stats_info)
        
        # REGLAS GRAMATICALES
        reglas_info = """
╔══════════════════════════════════════════════════════════════╗
║                 REGLAS GRAMATICALES DE PYTHON                ║
╚══════════════════════════════════════════════════════════════╝

📝 ESTRUCTURA GENERAL DEL LENGUAJE:
────────────────────────────────────────────────────────────────

🔹 PROGRAMA:
   programa ::= (declaracion | sentencia)*

🔹 DECLARACIONES:
   declaracion ::= def_funcion | def_clase | import_stmt
   
   def_funcion ::= 'def' IDENTIFICADOR '(' parametros ')' ':' bloque
   parametros  ::= (IDENTIFICADOR (',' IDENTIFICADOR)*)?
   
   def_clase   ::= 'class' IDENTIFICADOR ('(' herencia ')')? ':' bloque
   herencia    ::= IDENTIFICADOR (',' IDENTIFICADOR)*
   
   import_stmt ::= 'import' modulo | 'from' modulo 'import' nombres
   modulo      ::= IDENTIFICADOR ('.' IDENTIFICADOR)*
   nombres     ::= IDENTIFICADOR (',' IDENTIFICADOR)*

📐 ESTRUCTURAS DE CONTROL:
────────────────────────────────────────────────────────────────

🔹 CONDICIONALES:
   if_stmt   ::= 'if' expresion ':' bloque elif_clause* else_clause?
   elif_clause ::= 'elif' expresion ':' bloque
   else_clause ::= 'else' ':' bloque

🔹 BUCLES:
   for_stmt   ::= 'for' IDENTIFICADOR 'in' expresion ':' bloque
   while_stmt ::= 'while' expresion ':' bloque

🔹 MANEJO DE EXCEPCIONES:
   try_stmt     ::= 'try' ':' bloque except_clause+ finally_clause?
                  | 'try' ':' bloque finally_clause
   except_clause ::= 'except' (tipo_excepcion ('as' IDENTIFICADOR)?)? ':' bloque
   finally_clause ::= 'finally' ':' bloque

🔹 CONTEXTO:
   with_stmt ::= 'with' expresion ('as' IDENTIFICADOR)? ':' bloque

📊 EXPRESIONES Y OPERADORES:
────────────────────────────────────────────────────────────────

🔹 EXPRESIONES:
   expresion ::= expr_or
   expr_or   ::= expr_and ('or' expr_and)*
   expr_and  ::= expr_not ('and' expr_not)*
   expr_not  ::= 'not' expr_not | comparacion
   
   comparacion ::= expr_aritmetica (comp_op expr_aritmetica)*
   comp_op     ::= '<' | '>' | '==' | '>=' | '<=' | '!=' | 'in' | 'not' 'in' | 'is' | 'is' 'not'

🔹 OPERADORES ARITMÉTICOS:
   expr_aritmetica ::= termino (('+' | '-') termino)*
   termino        ::= factor (('*' | '/' | '//' | '%') factor)*
   factor         ::= ('+' | '-')? potencia
   potencia       ::= atom ('**' factor)?

🔹 ÁTOMICOS:
   atom ::= IDENTIFICADOR | NUMERO | STRING | 'True' | 'False' | 'None'
          | '(' expresion ')' | lista | diccionario | llamada_funcion

📚 TOKENS Y LEXEMAS:
────────────────────────────────────────────────────────────────

🔹 IDENTIFICADORES:
   IDENTIFICADOR ::= (letra | '_') (letra | digito | '_')*
   letra         ::= [a-zA-Z]
   digito        ::= [0-9]

🔹 NÚMEROS:
   NUMERO ::= ENTERO | DECIMAL | CIENTIFICO | BINARIO | OCTAL | HEXADECIMAL
   
   ENTERO     ::= digito+
   DECIMAL    ::= digito+ '.' digito* | '.' digito+
   CIENTIFICO ::= (ENTERO | DECIMAL) [eE] [+-]? digito+
   BINARIO    ::= '0' [bB] [01]+
   OCTAL      ::= '0' [oO] [0-7]+
   HEXADECIMAL::= '0' [xX] [0-9a-fA-F]+

🔹 CADENAS:
   STRING ::= STRING_SIMPLE | STRING_TRIPLE
   STRING_SIMPLE ::= ('"' contenido_simple '"') | ("'" contenido_simple "'")
   STRING_TRIPLE ::= ('"""' contenido_triple '"""') | ("'''" contenido_triple "'''")

🔹 PALABRAS RESERVADAS:
   False    None     True     and      as       assert   async    await
   break    class    continue def      del      elif     else     except
   finally  for      from     global   if       import   in       is
   lambda   nonlocal not      or       pass     raise    return   try
   while    with     yield

🔹 OPERADORES:
   ARITMÉTICOS: + - * / // % ** @
   COMPARACIÓN: < > <= >= == != 
   LÓGICOS:     and or not
   ASIGNACIÓN:  = += -= *= /= //= %= **= @= &= |= ^= >>= <<=
   BITWISE:     & | ^ ~ << >>
   PERTENENCIA: in not_in
   IDENTIDAD:   is is_not

🔹 DELIMITADORES:
   AGRUPACIÓN:  ( ) [ ] { }
   SEPARADORES: , : . ; ->
   DECORADORES: @

📏 REGLAS DE INDENTACIÓN:
────────────────────────────────────────────────────────────────

🔹 INDENTACIÓN:
   • Python usa indentación para delimitar bloques de código
   • Debe ser consistente (recomendado: 4 espacios)
   • Un bloque comienza después de ':' con mayor indentación
   • Un bloque termina cuando la indentación regresa al nivel anterior

🔹 ESTRUCTURA DE BLOQUE:
   bloque ::= NUEVA_LINEA INDENT sentencia+ DEDENT
   INDENT ::= aumento_indentacion
   DEDENT ::= disminucion_indentacion

📋 SENTENCIAS:
────────────────────────────────────────────────────────────────

🔹 SENTENCIAS SIMPLES:
   sentencia_simple ::= asignacion | expr_stmt | return_stmt | break_stmt |
                       continue_stmt | pass_stmt | del_stmt | yield_stmt |
                       raise_stmt | import_stmt | global_stmt | nonlocal_stmt |
                       assert_stmt
   
   asignacion   ::= target '=' expresion
   expr_stmt    ::= expresion
   return_stmt  ::= 'return' expresion?
   break_stmt   ::= 'break'
   continue_stmt::= 'continue'
   pass_stmt    ::= 'pass'
   del_stmt     ::= 'del' target_list
   yield_stmt   ::= 'yield' expresion?
   raise_stmt   ::= 'raise' (expresion ('from' expresion)?)?
   global_stmt  ::= 'global' IDENTIFICADOR (',' IDENTIFICADOR)*
   nonlocal_stmt::= 'nonlocal' IDENTIFICADOR (',' IDENTIFICADOR)*
   assert_stmt  ::= 'assert' expresion (',' expresion)?

🔹 SENTENCIAS COMPUESTAS:
   sentencia_compuesta ::= if_stmt | while_stmt | for_stmt | try_stmt |
                          with_stmt | def_funcion | def_clase

🎯 REGLAS DE PRECEDENCIA DE OPERADORES (de mayor a menor):
────────────────────────────────────────────────────────────────

1. **  (exponenciación) - Asociatividad derecha
2. +x, -x, ~x (unarios)
3. *, /, //, %
4. +, - (binarios)
5. <<, >>
6. &
7. ^
8. |
9. ==, !=, <, <=, >, >=, is, is not, in, not in
10. not
11. and
12. or
13. lambda
14. if...else (expresión condicional)

✅ REGLAS DE CORRECCIÓN:
────────────────────────────────────────────────────────────────

• Toda función debe terminar con ':' seguido de bloque indentado
• Toda estructura de control (if, for, while) requiere ':'
• Los paréntesis deben estar balanceados
• Las comillas de strings deben estar cerradas
• Los identificadores no pueden ser palabras reservadas
• La indentación debe ser consistente dentro del mismo bloque
• Las variables deben estar definidas antes de su uso
• Las funciones deben estar declaradas antes de ser llamadas
"""
        
        if self.texto_reglas:
            self.texto_reglas.insert('1.0', reglas_info)
        
        # Seleccionar pestaña de resumen por defecto
        self.cambiar_pestaña('resumen')
    
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