# This is a comment
# Un programa en python que clacule el factorial de un numero

# Definimos la funcion factorial
def factorial(n):
    if n == 0:
        return 1
    else:
        return n * factorial(n-1)
# Pedimos al usuario que ingrese un numero
num = int(input("Ingrese un numero: "))
# Llamamos a la funcion factorial y mostramos el resultado
print(f"El factorial de {num} es {factorial(num)}")
