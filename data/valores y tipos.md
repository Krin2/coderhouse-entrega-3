# 2.1 Valores y tipos
Un valor es una de las cosas básicas que utiliza un programa, como una letra o un
número. Los valores que hemos visto hasta ahora han sido 1, 2, y “¡Hola, mundo!”
Esos valores pertenecen a tipos diferentes: 2 es un entero (int), y “¡Hola, mundo!”
es una cadena (string), que recibe ese nombre porque contiene una “cadena” de
letras. Tú (y el intérprete) podéis identificar las cadenas porque van encerradas
entre comillas.
Lasentencia print también funciona con enteros. Vamos a usar el comando python
para iniciar el intérprete.
```python
>>> print(4)
4
```
Si no estás seguro de qué tipo de valor estás manejando, el intérprete te lo puede
decir.
```python
>>> type(''¡Hola, mundo!)
<class 'str'>
>>> type(17)
<class 'int'>
Not surprisingly, strings belong to the type str and integers belong to the type
int. Less obviously, numbers with a decimal point belong to a type called float,
because these numbers are represented in a format called floating point.
>>> type(3.2)
<class 'float'>
```

¿Qué ocurre con valores como “17” y “3.2”? Parecen números, pero van entre
comillas como las cadenas.
```python
>>> type('17')
<class 'str'>
>>> type('3.2')
<class 'str'>
```
Son cadenas.
Cuando escribes un entero grande, puede que te sientas tentado a usar comas o
puntos para separarlo en grupos de tres dígitos, como en 1,000,000 1. Eso no es
un entero válido en Python, pero en cambio sí que resulta válido algo como:
```python
>>> print(1,000,000)
1 0 0
```
Bien, ha funcionado. ¡Pero eso no era lo que esperábamos!. Python interpreta
1,000,000 como una secuencia de enteros separados por comas, así que lo imprime
con espacios en medio.
Éste es el primer ejemplo que hemos visto de un error semántico: el código funciona sin producir ningún mensaje de error, pero no hace su trabajo “correctamente”.
