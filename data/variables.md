# 2.2 Variables
Una de las características más potentes de un lenguaje de programación es la
capacidad de manipular variables. Una variable es un nombre que se refiere a un
valor.
Una sentencia de asignación crea variables nuevas y las da valores:
```python
>>> mensaje = 'Y ahora algo completamente diferente'
>>> n = 17
>>> pi = 3.1415926535897931
```
Este ejemplo hace tres asignaciones. La primera asigna una cadena a una variable
nueva llamada mensaje; la segunda asigna el entero 17 a n; la tercera asigna el
valor (aproximado) de π a pi.
Para mostrar el valor de una variable, se puede usar la sentencia print:
```python
>>> print(n)
17
>>> print(pi)
3.141592653589793
```
El tipo de una variable es el tipo del valor al que se refiere.
```python
>>> type(mensaje)
<class 'str'>
>>> type(n)
<class 'int'>
>>> type(pi)
<class 'float'>
```

# 2.3 Nombres de variables y palabras claves
Los programadores generalmente eligen nombres para sus variables que tengan
sentido y documenten para qué se usa esa variable.
Los nombres de las variables pueden ser arbitrariamente largos. Pueden contener
tanto letras como números, pero no pueden comenzar con un número. Se pueden
usar letras mayúsculas, pero es buena idea comenzar los nombres de las variables
con una letras minúscula (veremos por qué más adelante).
con
El carácter guión-bajo (_) puede utilizarse en un nombre. A menudo se utiliza en
nombres
múltiples
palabras,
como
en
mi_nombre
o
velocidad_de_golondrina_sin_carga. Los nombres de las variables pueden
comenzar con un carácter guión-bajo, pero generalmente se evita usarlo así a
menos que se esté escribiendo código para librerías que luego utilizarán otros.
Si se le da a una variable un nombre no permitido, se obtiene un error de sintaxis:
```python
>>> 76trombones = 'gran desfile'
SyntaxError: invalid syntax
>>> more@ = 1000000
SyntaxError: invalid syntax
>>> class = 'Teorema avanzado de Zymurgy'
SyntaxError: invalid syntax
```
76trombones es incorrecto porque comienza por un número. more@ es incorrecto
porque contiene un carácter no premitido, @. Pero, ¿qué es lo que está mal en
class?
Pues resulta que class es una de las palabras clave de Python. El intérprete
usa palabras clave para reconocer la estructura del programa, y esas palabras no
pueden ser utilizadas como nombres de variables.
Python reserva 33 palabras claves para su propio uso:
and
as
assert
break
class
del
elif
else
except
False
from
global
if
import
in
continue finally is
def
for
lambda
None
True
nonlocal try
not
or
pass
raise
return
while
with
yield
Puede que quieras tener esta lista a mano. Si el intérprete se queja por el nombre
de una de tus variables y no sabes por qué, comprueba si ese nombre está en esta
lista.
