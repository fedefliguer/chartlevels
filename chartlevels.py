import numpy as np
import pandas as pd
__version__ = 'dev'

def calculo_historia(dataset, lags, rq = 0.03, l = False):
  '''
  Función que identifica cuáles son los puntos de soporte y resistencia (máximos y mínimos locales) y a través de recorrido_soportes_resistencias() devuelve dos dataframes con las pruebas de los soportes y las resistencias en la historia.
  '''
  i = 1
  while i < (lags+1): # Genera ventanas alrededor para analizar si es soporte
      colname = 'l%sb' % (i)
      dataset.loc[:,colname] = round(dataset['Close'].shift(i),2)
      colname = 'l%sf' % (i)
      dataset.loc[:,colname] = round(dataset['Close'].shift(-i),2)
      i = i + 1
  dataset.loc[:,'minb'] = round(dataset.filter(regex=("^l(.*)b$")).min(axis=1),2)
  dataset.loc[:,'minf'] = round(dataset.filter(regex=("^l(.*)f$")).min(axis=1),2)
  dataset.loc[:,'maxb'] = round(dataset.filter(regex=("^l(.*)b$")).max(axis=1),2)
  dataset.loc[:,'maxf'] = round(dataset.filter(regex=("^l(.*)f$")).max(axis=1),2)
  dataset.loc[:,'Soporte'] = np.where((dataset.index > lags) & (dataset['Close']<dataset['minb']) & (dataset['Close']<dataset['minf']), 1, 0)
  dataset.loc[:,'Soporte'] = dataset.Soporte * dataset['Close']
  dataset.loc[:,'Resistencia'] = np.where((dataset.index > lags) & (dataset['Close']>dataset['maxb']) & (dataset['Close']>dataset['maxf']), 1, 0)
  dataset.loc[:,'Resistencia'] = dataset.Resistencia * dataset['Close']
  dataset = dataset[['Date', 'Close', 'Low', 'High', 'Soporte', 'Resistencia']].copy()
  dataset.loc[:,'Date_vigencia'] = dataset.Date.shift(-lags)
  dataset.replace(0, np.nan, inplace=True)
  puntos_soporte = dataset[dataset.Soporte > 0]['Soporte'].to_numpy() # Lista de soportes
  fechas_soporte = dataset[dataset.Soporte > 0]['Date'].to_numpy() # Lista de fechas de soporte
  fechas_vigencia_soporte = dataset[dataset.Soporte > 0]['Date_vigencia'].to_numpy() # Lista de fechas de soporte
  print('EMPIEZA ANÁLISIS DE SOPORTES') if l else None
  dataset_all_soportes = pd.DataFrame()
  i = 0
  while i < len(puntos_soporte):  # Recorre la lista de soportes
    dataset_all_soportes = recorrido_soportes_resistencias(dataset, fechas_vigencia_soporte[i], puntos_soporte[i], rq, dataset_all_soportes, 1, Logging=l, clase='s')
    i = i + 1
  print('EMPIEZA ANÁLISIS DE RESISTENCIAS') if l else None
  puntos_resistencia = dataset[dataset.Resistencia > 0]['Resistencia'].to_numpy() # Lista de resistencia
  fechas_resistencia = dataset[dataset.Resistencia > 0]['Date'].to_numpy() # Lista de fechas de resistencia
  fechas_vigencia_resistencia = dataset[dataset.Resistencia > 0]['Date_vigencia'].to_numpy() # Lista de fechas de soporte
  dataset_all_resistencias = pd.DataFrame()
  i = 0
  while i < len(puntos_resistencia):  # Recorre la lista de resistencia
    print('ANALIZO EL PUNTO ', puntos_resistencia[i], ' DEL ', fechas_resistencia[i], ' QUE ENTRARÍA EN VIGENCIA EL ', fechas_vigencia_resistencia[i]) if l else None
    dataset_all_resistencias = recorrido_soportes_resistencias(dataset, fechas_vigencia_resistencia[i], puntos_resistencia[i], rq, dataset_all_resistencias, 1, Logging=l, clase='r')
    i = i + 1
  return dataset_all_soportes, dataset_all_resistencias

def recorrido_soportes_resistencias(dataset, fecha_empieza_vigencia, valor_soporte, rango_quebrado, df_all, prueba_nro, Logging, clase):
  '''
  Función que para cada soporte y resistencia establece su tiempo de vigencia y duración, entendida como el tiempo que pasó sin ser quebrado hacia arriba (si es resistencia) o hacia abajo (si es soporte).
  '''
  dataset = dataset[dataset.Date > fecha_empieza_vigencia].copy()
  if len(dataset) > 0:
    dataset.loc[:,'rango_quebrado_inicia'] = valor_soporte * (1-rango_quebrado)
    dataset.loc[:,'valor'] = valor_soporte
    dataset.loc[:,'rango_quebrado_termina'] = valor_soporte * (1+rango_quebrado)
    dataset.loc[:,'es_zona_prueba'] = np.where((dataset['Low'] < dataset['valor']) & (dataset['High'] > dataset['valor']), 1, 0)
    if clase == 's':
      dataset.loc[:,'es_zona_confirmacion'] = np.where((dataset['Close'] > dataset['rango_quebrado_termina']), 1, 0)
      dataset.loc[:,'es_zona_quiebre'] = np.where((dataset['Close'] < dataset['rango_quebrado_inicia']), 1, 0)
    elif clase == 'r':
      dataset.loc[:,'es_zona_quiebre'] = np.where((dataset['Close'] > dataset['rango_quebrado_termina']), 1, 0)
      dataset.loc[:,'es_zona_confirmacion'] = np.where((dataset['Close'] < dataset['rango_quebrado_inicia']), 1, 0)
    mascara_probado = (dataset.es_zona_prueba == 1)
    mascara_quebrado = (dataset.es_zona_quiebre == 1)
    if (len(dataset[mascara_probado]) == 0) & (len(dataset[mascara_quebrado]) == 0):
      resolucion = 'vigente'
      fecha_prueba = np.nan
      fecha_resolucion = np.nan
      print('La prueba número ', prueba_nro, 'nunca se realizó en la historia') if Logging else None
    elif len(dataset[mascara_probado]) == 0:
      resolucion = 'quebrado sin probarse nunca'
      fecha_prueba = np.nan
      fecha_resolucion = np.nan
      print('La prueba', prueba_nro, 'nunca se realizó, pero el valor fue quebrado') if Logging else None
    else:
      fecha_prueba = dataset[mascara_probado].iloc[0].Date
      resolucion = ''
      if len(dataset[mascara_quebrado]) > 0:
        fecha_quiebre = dataset[mascara_quebrado].iloc[0].Date
        if fecha_quiebre < fecha_prueba:      
          resolucion = 'quebrado'
          fecha_prueba = np.nan
          fecha_resolucion = fecha_quiebre
          print('La prueba', prueba_nro, 'fue quebrada antes de probarse') if Logging else None
      if resolucion != 'quebrado':
        print('La prueba número ', prueba_nro, 'empezó el día ', fecha_prueba, ' cuando el mínimo fue ', dataset[mascara_probado].iloc[0].Low, ' y el máximo fue ', dataset[mascara_probado].iloc[0].High) if Logging else None
        mascara_resuelto = ((dataset.Date > fecha_prueba)&(dataset.es_zona_confirmacion == 1))|((dataset.Date > fecha_prueba)&(dataset.es_zona_quiebre == 1))
        if len(dataset[mascara_resuelto]): # La prueba fue resuelta
          fecha_resolucion = dataset[mascara_resuelto].iloc[0].Date
          print('Fue resuelta el día ', fecha_resolucion, ' cuando el mínimo fue ', dataset[mascara_resuelto].iloc[0].Low, ' y el máximo fue ', dataset[mascara_resuelto].iloc[0].High) if Logging else None
          if (dataset[mascara_resuelto].iloc[0].es_zona_confirmacion == 1) & (dataset[mascara_resuelto].iloc[0].es_zona_quiebre == 1):
            resolucion = 'indeterminado por resolverse el mismo día'
            print('La prueba número ', prueba_nro, 'completó la historia sin ser determinada') if Logging else None
          elif dataset[mascara_resuelto].iloc[0].es_zona_confirmacion == 1:
            resolucion = 'probado'
            print('La prueba número ', prueba_nro, 'completó la historia probada el día ', fecha_resolucion) if Logging else None
          elif dataset[mascara_resuelto].iloc[0].es_zona_quiebre == 1:
            resolucion = 'quebrado'
            print('La prueba número ', prueba_nro, 'completó la historia quebrada el día ', fecha_resolucion) if Logging else None
        else:
          fecha_resolucion = np.nan
          resolucion = 'indeterminado por no resolverse nunca'
          print('No llegó a resolverse en el mes.') if Logging else None
    analisis_prueba_list = []
    analisis_prueba_list.append([str(round(valor_soporte,2)), valor_soporte, fecha_empieza_vigencia, prueba_nro, fecha_prueba, fecha_resolucion, resolucion])
    analisis_prueba = pd.DataFrame(analisis_prueba_list, columns = ["id_soporte", "valor", "fecha_ingreso_vigencia", "nro_prueba_historia", "fecha_prueba", "fecha_resolucion", "tipo_resolucion"])
    analisis_prueba['fecha_prueba'] = pd.to_datetime(analisis_prueba['fecha_prueba'])
    analisis_prueba['fecha_resolucion'] = pd.to_datetime(analisis_prueba['fecha_resolucion'])
    df_all = pd.concat([df_all, analisis_prueba], axis=0)
    if resolucion == 'probado':
      print('La prueba número ', prueba_nro, 'admite nuevas pruebas') if Logging else None
      prueba_nro = prueba_nro + 1
      dataset = dataset[dataset.Date > fecha_resolucion].copy()
      return recorrido_soportes_resistencias(dataset, fecha_empieza_vigencia, valor_soporte, rango_quebrado, df_all, prueba_nro, Logging, clase)
    else:
      return df_all
  else:
    return df_all

def seleccion_linea(dataset, fecha, precio, clase):
  '''
  Función que para cada rueda identifica el punto de soporte o resistencia más cercano y lo establece como el vigente.
  '''
  mascara_iniciados_antes = (dataset.fecha_ingreso_vigencia < fecha)
  mascara_vigentes_hoy = (dataset.tipo_resolucion == 'vigente')
  mascara_quebrados_despues = ((dataset.tipo_resolucion == 'quebrado') & (dataset.fecha_resolucion > fecha))|((dataset.tipo_resolucion == 'indeterminado por resolverse el mismo día') & (dataset.fecha_resolucion > fecha))
  vigentes = dataset[mascara_iniciados_antes & (mascara_vigentes_hoy|mascara_quebrados_despues)].sort_values(by=['fecha_ingreso_vigencia'])
  if clase == 's':
    try:
      valor = vigentes.iloc[vigentes['valor'].argmax()].valor
      pruebas = vigentes.iloc[vigentes['valor'].argmax()].nro_prueba_historia
      antiguedad = (fecha - (vigentes.iloc[vigentes['valor'].argmax()].fecha_ingreso_vigencia)).days
      return valor, pruebas, antiguedad
    except:
      return np.nan, np.nan, np.nan
  elif clase == 'r':
    try:
      valor = vigentes.iloc[vigentes['valor'].argmin()].valor
      pruebas = vigentes.iloc[vigentes['valor'].argmin()].nro_prueba_historia
      antiguedad = (fecha - (vigentes.iloc[vigentes['valor'].argmin()].fecha_ingreso_vigencia)).days
      return valor, pruebas, antiguedad
    except:
      return np.nan, np.nan, np.nan

def calculador_soportes_resistencias(dataset, lags = [10]):
  '''
  Función que consolida todas las anteriores calculando valor/antigüedad/número de pruebas de soporte y resistencia para todo el dataset. El parámetro lags es un array con los distintos intervalos para considerarse máximo o mínimo local, cuánto más grande más exigente (y por lo tanto menos frecuentes) los soportes y las resistencias. 
  '''
  datasets_soportes_resistencias = {}
  for num_lags in lags:
    dataset_soportes, dataset_resistencias = calculo_historia(dataset, num_lags, 0.03, l=False)
    dataset = dataset[dataset.columns.drop(list(dataset.filter(regex='l.*b|l.*f|minb|minf|maxb|maxf|Soporte|Resistencia')))].copy()
    lista_soportes_diarios = [seleccion_linea(dataset_soportes, f, p, 's') for f, p in zip(dataset['Date'], dataset['Close'])]
    dataset.loc[:,'soporte_%s_valor' % (num_lags)] = [a_tuple[0] for a_tuple in lista_soportes_diarios]
    dataset.loc[:,'soporte_%s_numero_pruebas' % (num_lags)] = [a_tuple[1] for a_tuple in lista_soportes_diarios]
    dataset.loc[:,'soporte_%s_dias_antiguedad' % (num_lags)] = [a_tuple[2] for a_tuple in lista_soportes_diarios]
    lista_resistencias_diarias  = [seleccion_linea(dataset_resistencias, f, p, 'r') for f, p in zip(dataset['Date'], dataset['Close'])]
    dataset.loc[:,'resistencia_%s_valor' % (num_lags)] = [a_tuple[0] for a_tuple in lista_resistencias_diarias]
    dataset.loc[:,'resistencia_%s_numero_pruebas' % (num_lags)] = [a_tuple[1] for a_tuple in lista_resistencias_diarias]
    dataset.loc[:,'resistencia_%s_dias_antiguedad' % (num_lags)] = [a_tuple[2] for a_tuple in lista_resistencias_diarias]
    datasets_soportes_resistencias["dataset_soportes_{0}".format(num_lags)] = dataset_soportes
    datasets_soportes_resistencias["dataset_resistencias_{0}".format(num_lags)] = dataset_resistencias
  dataset = dataset[dataset.columns.drop(list(dataset.filter(regex='l(.*)b')))]
  dataset = dataset[dataset.columns.drop(list(dataset.filter(regex='l(.*)f')))]
  dataset = dataset[dataset.columns.drop(list(dataset.filter(regex='maxf|maxb|minf|minb')))]
  return dataset
