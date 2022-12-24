# chartlevels

Este repositorio incluye las funciones necesarias para calcular los soportes y las resistencias de cada registro de una serie de precios. Para levantarlo desde una notebook de jupyter se debe ejecutar

      !pip install git+https://github.com/fedefliguer/chartlevels@main#egg=chartlevels
      from chartlevels import *

La ejecución de la funcion calculador_soportes_resistencias llama a todo el resto de las funciones y devuelve el mismo dataset que sirve de primer parámetro a la función, pero con las columnas agregadas: para cada fila se indica el soporte y la resistencia más cercano, así como la cantidad de veces que para esa rueda ese soporte/resistencia había sido probado, y la cantidad de días de historia. El dataframe original debe contener las columnas 'Close' para el precio de cierre, 'High' para el máximo de la vela, 'Low' para el mínimo de la rueda y 'Ticker' con el símbolo.
