# %% [markdown]
# # Curvas mexicanas
# El propósito de este documento es el de mostar los pasos para evaluar las cuvas de TIIE28 y de FTIIE respectivamente.
# 
# Se explicará el proceso que se usa para valuar estas curvas por medio de `QuantLib`, librería que se usa en la valuación y creación de instrumentos financieros. Se hará un ejemplo con las curvas del 19 de febrero de 2025 de acuerdo al modelo de CME. Este modelo se llama Boostrapping paramétrico, pues usa métodos numéricos para el ajuste de las curvas.
# 
# La curva TIIE28, FTIIE, y SOFR son curvas que se usan para calcular las tasas de los cupones variables de los swaps, ietras que la de curva de Descuento es para descontar los flujos del Swap. En el caso de la SOFR, se usa la mism curva como curva de descuento, pues es considerada una curva libre de riesgo (al ser muy líquida).
# 
# Los pasos a seguir para la creación de cada curva son los siguientes: (más info en el siguiente [paper](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2219548&download=yes) )
# - Definir los insumos necesarios 
# - Definir objetos para cada instrumento necesario para el ajuste de curvas
# - Hacer el bootstrapping 
# 
# Vamos a definir las curvas en el siguiente orden:  
# 1. Curva de TIIE28
# 2. Curva de FTIIE
# 3. Curva de Descuento MXN
# 4. Curva de SOFR

# %% [markdown]
# ## Curva de TIIE28  
# 
# ### Definción de Insumos
# Siguiendo los pasos antes mencionados, primero necesitamos definir los insumos que se necesitan para esta curva en específico. De acuerdo al modelo de CME, la curva de TIIE28 usa las tasas par de cierre para los siguientes nodos (expresados en 28 días):
# 
# - 1: 1 mes
# - 3: 3 meses
# - 6: 6 meses
# - 9: 9 meses
# - 13: 1 año
# - 26: 2 años
# - 39: 3 años
# - 52: 4 años
# - 65: 5 años
# - 91: 7 años
# - 130: 10 años
# - 195: 15 años
# - 260: 20 años
# - 390: 30 años
# 
# 
# 
# 
# 

# %%
# Librerías a utilizar
import numpy as np
import pandas as pd
import QuantLib as ql # versión 1.38 o superior

# Definición de insumos
# L es un mes de 28 días (mes lunar)

t_1L = 9.7638
t_3L = 9.643802
t_6L = 9.293893
t_9L = 9.066304
t_13L = 8.895611
t_26L = 8.719446
t_39L = 8.713905
t_52L = 8.764028
t_65L = 8.814004
t_91L = 8.938174
t_130L = 9.094733
t_195L = 9.276024
t_260L = 9.293577
t_390L = 9.2277

# Definición de tenors
tenors_tiie28 = [
    1, # 1 mes
    3, # 3 meses
    6, # 6 meses
    9, # 9 meses
    13, # 13 meses
    26, # 26 meses
    39, # 39 meses
    52, # 52 meses
    65, # 65 meses
    91, # 91 meses
    130, # 130 meses
    195, # 195 meses
    260, # 260 meses
    390  # 390 meses
]

# Definición de tasas
tasas_tiie28 = [
    t_1L,
    t_3L,
    t_6L,
    t_9L,
    t_13L,
    t_26L,
    t_39L,
    t_52L,
    t_65L,
    t_91L,
    t_130L,
    t_195L,
    t_260L,
    t_390L
]




# %% [markdown]
# ### Definición de Objetos
# En la librería QuantLib, se necesitan definir objetos tipo `helpers` para cada instrumento de la curva. En el caso de la curva de TIIE28, los ojetos que usaremos serán los siguientes:
# - `ql.DepositRatehelper`: objeto para tasas cero (la tasa par de un mes se puede definir como una tasa cero)
# - `ql.SwapRateHelper`: objeto para tasas par de swaps
# 
# Además de estos objetos, tambien es necesario definir el objeto `ql.IborIndex`, el cual contiene las especificacione sde la curva que se esta ajustando (tipo de conteo de días, manejo de días inhabiles, tasas fixing pasadas, entre otras). El objeto `ql.IborIndex` tiene por defecto la definición de las tasas fixing "in advance", es decir, que la tasa que se usará para el pago del cupón se define por completo antes de que empiece el cupón. Es por eso que la curva TIIE28 se considera "Ibor-like"
# Se definirá una función que creará todos los "helpers" necesarios para crear la curva. Esta función recibirá, 3 insumos: `tasas`, `tenors` y `curva de descuento`. Los primeros dos insumos ya los tenemos y el tercero se definirá en la sección de Curva de Descuento Mexicana

# %%
def TIIE28Helpers(tasas, tenors, curva_descuento):
    
    dias_liq = 1 # Dias de liquidación (1)
    cont_dias = ql.Actual360() # Forma de conteo de días 
    frecuencia = ql.EveryFourthWeek # Frecuencia de pagos
    # Cada 4 semanas (28 dias)
    ajuste_fec = ql.Following # Siempre se va al sig día 
    moneda = ql.MXNCurrency() # moneda a usar
    calendario = ql.Mexico() # Calendario de México
    ult_dia_mes = False # Si obliga a terminar al final de mes

    
    # Se define el objeto IborIndex que es el índice ``IBOR-like'' al que se quiere llegar
    ibor_MXNTIIE = ql.IborIndex(
        'TIIE', # Nombre del indice 
        ql.Period(13), # Se divide el año en 13 periodos
        dias_liq, # Días de liquidación 
        moneda, # Moneda usada
        calendario, 
        ajuste_fec,
        ult_dia_mes, 
        cont_dias)

    descuento = ql.RelinkableYieldTermStructureHandle() # Objeto para usar curvas
    descuento.linkTo(curva_descuento) # le agregamos la curva de descuento


    depositHelpers = [ql.DepositRateHelper( # Es una tasa de depósito
        ql.QuoteHandle(ql.SimpleQuote(r/100)), # Objeto para tasas
        ql.Period(t, ql.Months), # Periodo de la tasa
        dias_liq, # Días de liquidación
        calendario, # calendario usado
        ajuste_fec, # ajuste de fechas
        ult_dia_mes, # Si obliga a terminar al final de mes
        cont_dias) # conteo de días
        for (r, t) in zip([tasas[0]], [tenors[0]])] # Solo el primer elemento de tasas y tenors

    swapHelpers = [
        ql.SwapRateHelper( # Es una tasa par de Swap 
            ql.QuoteHandle(ql.SimpleQuote(r/100)), # Objeto para tasas
            ql.Period(t*4, ql.Weeks), # Periodo de la tasa
            calendario, # calendario usado
            frecuencia,  # frecuencia 
            ajuste_fec, # ajuste de fechas
            cont_dias, # conteo de días 
            ibor_MXNTIIE, # Indice a rellenar
            ql.QuoteHandle(), # Spread (0)
            ql.Period(), # Periodo de pago de cupón
            descuento) # curva de descuento
        for (r, t) in zip(tasas[1:], tenors[1:])]

    helpers = depositHelpers + swapHelpers # Unimos los helpers de tasas cero y swaps

    return helpers

# %% [markdown]
# Después de definir todos los helpers para cada curva, definiremos el bootstrap, pues es muy parecido para cada curva.

# %% [markdown]
# ## Curva de TIIE de Fondeo
# 
# Al igual que la cura de TIIE28, primero definiremos los insumos necesarios para el ajuste de curva. A diferencia de la TIIE28, tendremos mas de un tipo de instrumento. Para ajustar la curva de FTIIE o TIIE de fondeo, de acuerdo a la metodología de CME, son necesarios Futuros y Swaps de FTIIE. Además, para poder defnir los futuros de FTIIE, es necesario tener las tasas de TIIE de Fondeo a 1 día del mes vigente pulicadas por el Banco de México (Banxico). Estas rasas se obtienen de la página del [Banco de México](https://www.banxico.org.mx/).  
# 
# ### Definición de Insumos
# Para esta curva, se necesitan los dos primeros futuros de TIIE de Fondeo paa la parte corta de la curva y luego los swaps de los siguientes tenors:  
# 
# - 3: 3 meses
# - 6: 6 meses
# - 9: 9 meses
# - 13: 1 año
# - 26: 2 años
# - 39: 3 años
# - 52: 4 años
# - 65: 5 años
# - 91: 7 años
# - 130: 10 años
# - 195: 15 años
# - 260: 20 años
# - 390: 30 años
# 
# En este caso en particular, se usarán los futuros de febrero y marzo.
# 
# - feb2025: 28 días
# - mar2025: 31 días
# 

# %%
# Definición de tasas de futuros
tasa_fut_feb25 = 9.655
tasa_fut_mar25 = 9.495

# Tenors de futuros
tenors_futuros = [
    'Feb2025', # Febrero 2025
    'Mar2025'  # Marzo 2025
]

tasas_fut = [
    tasa_fut_feb25, # Tasa de futuro Febrero 2025   
    tasa_fut_mar25  # Tasa de futuro Marzo 2025
]

# Definición de tasas de swaps
t_3L = 9.27000000
t_6L = 8.94300000
t_9L = 8.74025000
t_13L = 8.59450000
t_26L = 8.45000000
t_39L = 8.45680000
t_52L = 8.51250000
t_65L = 8.56550000
t_91L = 8.69350000
t_130L = 8.85225000
t_195L = 9.03405000
t_260L = 9.05100000
t_390L = 8.98505000

# Definición de tenors 
tenors_ftiie = [
    3, # 3 meses
    6, # 6 meses
    9, # 9 meses
    13, # 13 meses
    26, # 26 meses
    39, # 39 meses
    52, # 52 meses
    65, # 65 meses
    91, # 91 meses
    130, # 130 meses
    195, # 195 meses
    260, # 260 meses
    390  # 390 meses
]
tasas_ftiie = [
    t_3L,
    t_6L,
    t_9L,
    t_13L,
    t_26L,
    t_39L,
    t_52L,
    t_65L,
    t_91L,
    t_130L,
    t_195L,
    t_260L,
    t_390L
]
# Obtenidas de https://www.banxico.org.mx/SieInternet/consultarDirectorioInternetAction.do?sector=18&accion=consultarCuadro&idCuadro=CF101&locale=es
fechas_banxico = [
    "31/01/2025",
    "04/02/2025",
    "05/02/2025",
    "06/02/2025",
    "07/02/2025",
    "10/02/2025",
    "11/02/2025",
    "12/02/2025",
    "13/02/2025",
    "14/02/2025",
    "17/02/2025",
    "18/02/2025"
]

tasas_banxico = [
    10.03,
    10.02,
    10.05,
    10.00,
    9.49,
    9.50,
    9.50,
    9.50,
    9.49,
    9.49,
    9.50,
    9.49
]






# %% [markdown]
# ### Definición de objetos
# 
# Ahora, al igual que en TIIE28, se definirá una función para crear los diferentes helpers necesarios para el ajuste de curvas. Recordemos que la curva de TIIE de Fondeo tiene la particularidad de que sus tasas so overight, es decir que los cupones o la tasa que se pagará en ls swaps o en los futuros se calculan componiendo todas las tasas de un día publcadas por Banxico. Es por eso que todos los instrumentos tienen "Overnight" en su nombre.
# - `ql.OvernightIndexFutureRateHelper`: Objeto para definir las tasas de futuros Overnight
# - `ql.OISRateHelper`: Objeto para definir swaps Overnight
# 
# En esta curva, al igual que en la de TIIE28, es necesario definir un objeto "index", pero en el caso de la TIIE de Fondeo ya no será un `ql.IborIndex`, sino un `ql.OvernightIndex`.
# 

# %%
# Helpers para los Swaps de FTIIE
def FTIIESwapHelpers(tasas, tenors, curva_descuento):
    """ Crea los helpers para los swaps FTIIE.
    
    Parameters
    ----------
    tasas : list
        Tasas de los swaps FTIIE.
    tenors : list
        Tenors de los swaps FTIIE.
    curva_descuento : ql.YieldTermStructureHandle
        Curva de descuento a usar.
    
    Returns
    -------
    list
        Lista de helpers para los swaps FTIIE.
    """
    
    dias_liq = 2 # Días de liquidación (2)
    cont_dias = ql.Actual360() # Forma de conteo de días 
    frecuencia = ql.EveryFourthWeek # Frecuencia de pagos
    # Cada 4 semanas (28 días)
    ajuste_fec = ql.Following # Siempre se va al siguiente día hábil
    moneda = ql.MXNCurrency() # moneda usada
    calendario = ql.Mexico() # Calendario de fechas
    ult_dia_mes = False # Si obliga a terminar al final de mes
    dias_pago = 2 # Días que tarda en pagar después del corte de cupón

    
    # Se define el objeto OvernightIndex que es el índice ``Overnight'' al que se quiere llegar
    # Es Overnight porque las tasas se componen diariamente
    index_MXNFTIIE = ql.OvernightIndex(
        'SWP_FTIIE',
        dias_liq, 
        moneda, calendario,  
        cont_dias)

    descuento = ql.RelinkableYieldTermStructureHandle() # Objeto para usar curvas
    descuento.linkTo(curva_descuento) # le agregamos la curva de descuento

    helpers = [ql.OISRateHelper( # Usamos un OIS Rate Helper porque usa una tasa diaria
        dias_liq,  # Días de liquidación
        ql.Period(t*4, ql.Weeks), # Period (en semanas)
        ql.QuoteHandle(ql.SimpleQuote(r/100)),  # Tasa (entre 100)
        index_MXNFTIIE,  # Índice a encontrar
        descuento, # Curva de descuento
        ult_dia_mes,  # Si termina en último día de vez
        dias_pago, # días de pago después del corte
        ajuste_fec, # Ajuste de fechas
        frecuencia,
        calendario) for r, t in zip(tasas, tenors)]

    


    return helpers

# Helpers para los Futuros FTIIE
def FTIIEFutureshelpers(tasas, tenors, fechas_banxico, tasas_banxico):
    """ Crea los helpers para los futuros FTIIE.

    Parameters
    ----------
    tasas : list
        Tasas de los futuros FTIIE.
    tenors : list
        Tenors de los futuros FTIIE.
    fechas_banxico : list
        Fechas de Banxico para los futuros FTIIE.
    tasas_banxico : list
        Tasas de Banxico para los futuros FTIIE.
    
    Returns
    -------
    list
        Lista de helpers para los futuros FTIIE.
    """


    dias_liq = 1 # Los futuros liquidan en t+1
    moneda = ql.MXNCurrency() # Moneda usada
    calendario = ql.Mexico() # Calendario de México
    cont_dias = ql.Actual360() # Forma de conteo de días
    
    index_MXNFTIIE = ql.OvernightIndex( # Se vuelve a definir el Overnight Index
        'FUT_FTIIE', # Le llamamos FUT para diferenciarlo
        dias_liq, 
        moneda, 
        calendario,  
        cont_dias)
        
    # Se debe de rellenar el overnight index con las tasas hasta la fecha de evaluación
    
    index_MXNFTIIE.clearFixings() # Quitamos todos los fixings que pueden haber
    fechas_banxico_ql = [ql.Date.from_date(pd.to_datetime(f,format = '%d/%m/%Y'))
                         for f in fechas_banxico] # Se pasan las fechas a formato QuantLib
    tasas_banxico = [t/100 for t in tasas_banxico]  # Se hacen tasas en decimales

    index_MXNFTIIE.addFixings(fechas_banxico_ql, tasas_banxico) # Se agregan las tasas al índice "FUT_FTIIE"

    dic_meses = { # Diccionario de meses y sus números
        'Ene': 1,
        'Feb': 2,
        'Mar': 3,
        'Abr': 4,
        'May': 5,
        'Jun': 6,
        'Jul': 7,
        'Ago': 8,
        'Sep': 9,
        'Oct': 10,
        'Nov': 11,
        'Dic': 12
    }   

    # Se crea una lista de helpers
    helpers = []
    
    # Para cada tasa, tenor y mes se crea un helper de futuro
    for r, t in zip(tasas, tenors):

        tasa_ql = ql.QuoteHandle(ql.SimpleQuote(r)) # Objeto tasa de QuantLib
        mes =  dic_meses[t[:3]] # Mes del futuro
        anio =  int(t[3:]) # año del futuro
         
        primer_dia = ql.Date(1, mes, anio) # Primer dia del mes y del futuro
        
        ult_dia = ql.Date(1, max(1,(mes+1)%13), 
                          anio+(mes == 12)) # primer dia siguiente mes
                                     
    
        helper = ql.OvernightIndexFutureRateHelper( # Futuro Overnight
            tasa_ql,  
            primer_dia, 
            ult_dia, 
            index_MXNFTIIE) # Indice con las tasas del mes

        helpers.append(helper)

    return helpers


def FTIIEHelpers(tasas_fut, tenors_fut, tasas_swap, tenors_swap, 
                 curva_descuento, fechas_banxico, tasas_banxico):
    """
    Crea los helpers para los futuros FTIIE y los swaps FTIIE.
    
    Parameters
    ----------

    tasas_fut : list
        Tasas de los futuros FTIIE.
    tenors_fut : list
        Tenors de los futuros FTIIE.
    tasas_swap : list
        Tasas de los swaps FTIIE.
    tenors_swap : list
        Tenors de los swaps FTIIE.
    curva_descuento : ql.YieldTermStructureHandle
        Curva de descuento a usar.
    fechas_banxico : list
        Fechas de Banxico para los futuros FTIIE.
    tasas_banxico : list
        Tasas de Banxico para los futuros FTIIE.
    
    Returns
    -------
    list
        Lista de helpers para los futuros y swaps FTIIE.
    """
    
    # Helpers para futuros FTIIE
    helpers_fut = FTIIEFutureshelpers(tasas_fut, tenors_fut, fechas_banxico, tasas_banxico)
    
    # Helpers para swaps FTIIE
    helpers_swap = FTIIESwapHelpers(tasas_swap, tenors_swap, curva_descuento)
    
    return helpers_fut + helpers_swap


# %% [markdown]
# Cuando se terminen de definir los instrumentos para cada curva, se hará el bootstrapping
# 

# %% [markdown]
# ## Curva de Descuento en MXN
# 
# Esta curva, se crea a partir de un Bootstrapping doble de la curva SOFR y la curva de FTIIE usando los Cross Currency Basis Swaps de SOFR - TIIE. Se usa así porque como el mercado mexicano esta poco desarolloado, la curva e TIIE de Fondeo no puede ser considerada una curva de tasas libres de riesgo, siempre se tiene el riesgo país. Es por eso que por medio del dual-Bootstrapping se crea una curva en pesos mexicanos pero colateralizada en dólares americanos.   
# 
# ### Definición de Insumos
# 
# Para la creación de esta curva se necesitan los basis de cierre del Cross Currency Basis Swap FTIIE/SOFR, y los fwds de tipo de cambio MXN/USD. Los forwards se usarán en el corto plazo y a partir de los dos años se usan los basis de Cross Currency Basis Swaps. Los basis que se usan para esat curva son negativos, por lo que se aplican a las tasas de FTIIE.  
# 
# Para los forwards de tipo de cambio MXN/USD, usaremos los fwd basis points de los siguientes tenors:
# 
# - 1D: 1 día
# - 2D: 2 días
# - 1W: 1 semana
# - 1M: 1 mes
# - 2M: 2 meses
# - 3M: 3 meses
# - 6M: 6 meses
# - 9M: 9 meses
# - 1Y: 1 año
# 
# Usaremos la tasa Spot para a partir de ahí, sacar el tipo de cambio fwd para cada plazo.     
# 
# Por otro lado, para los Cross Currency Basis Swaps (XCCY Basis Swaps), se usaran los siguientes tenors (de 28 días):
# - 26: 2 años
# - 39: 3 años
# - 52: 4 años
# - 65: 5 años
# - 91: 7 años
# - 130: 10 años
# - 195: 15 años
# - 260: 20 años
# - 390: 30 años
# 

# %%
# Definicón de tasa de tipo de cambio MXN/USD Spot
t_mxn_usd_spot = 20.44245

# Definicion de fwds de tipo de cambio MXN/USD
fwd_1D = 30
fwd_2D = 31
fwd_1W = 216
fwd_1M = 877
fwd_2M = 1803
fwd_3M = 2623
fwd_6M = 5035
fwd_9M = 7420
fwd_1Y = 9770

# Definición de tenors de fwds de tipo de cambio

tenors_fwd_fx = [
    '1D',
    '2D',
    '1W',
    '1M',
    '2M',
    '3M',
    '6M',
    '9M',
    '1Y'
]

# Definición de XCCY basis de FTIIE-SOFR
basis_26L = 0.0115
basis_39L = -0.073
basis_52L = -0.1425
basis_65L = -0.194
basis_91L = -0.249
basis_130L = -0.294
basis_195L = -0.23101
basis_260L = -0.192
basis_390L = -0.185

# Definición de tenors de XCCY basis
tenors_xccy = [
    26, # 26 meses
    39, # 39 meses
    52, # 52 meses
    65, # 65 meses
    91, # 91 meses
    130, # 130 meses
    195, # 195 meses
    260, # 260 meses
    390  # 390 meses
]

tasas_fwd_fx = [
    fwd_1D,
    fwd_2D,
    fwd_1W,
    fwd_1M,
    fwd_2M,
    fwd_3M,
    fwd_6M,
    fwd_9M,
    fwd_1Y
]

tasas_xccy = [
    basis_26L,
    basis_39L,
    basis_52L,
    basis_65L,
    basis_91L,
    basis_130L,
    basis_195L,
    basis_260L,
    basis_390L
]




# %% [markdown]
# ### Definición de Objetos
# 
# El siguiente paso, sería crear los objetos helper para cada instrumento. En este caso, tenemos dos instrumentos principales, los fwds de tipo de cambio y los basis de Cross Currency Basis Swaps. Los objetos "helper" para cada uno de estos instrumentos son:
# - `ql.FXSwapRateHelper`: Tomaremos los forwards de tipo de cambio como Swaps de Fx USD/MXN
# - `ql.OISRateSwap`: Este helper admite sumar o restarle basis a su curva, por lo que simularemos que es una curva SOFR con basis para crear la de descuento mexicana
# Se definirán tres funciones: una para los helpers de tipo de cambio, una para los helpers de Cross Curency y una última que une a las dos anteriores.

# %%
# FX Swap Helper
def FXSwapHelpers(tasas_fwd, tenors, t_mxn_usd_spot,  curva_descuento):

    """ Crea los helpers para los fwds de tipo de cambio.
    
    Parameters
    ----------
    tasas_fwd : list
        Tasas de los fwds de tipo de cambio.
    tenors : list
        Tenors de los fwds de tipo de cambio.
    curva_descuento : ql.YieldTermStructureHandle
        Curva de descuento a usar.
    
    Returns
    -------
    list
        Lista de helpers para los fwds de tipo de cambio.
    """
    
    dias_liq = 0 # Días de liquidación (0)
    ajuste_fec = ql.Following # Siempre se va al siguiente día hábil
    calendario = ql.Mexico() # Calendario de México
    ult_dia_mes = False # Si obliga a terminar al final de mes
    base_es_colateral = True # Si es colateralizado o no

    descuento = ql.RelinkableYieldTermStructureHandle() # Objeto para usar curvas
    descuento.linkTo(curva_descuento) # le agregamos la curva de descuento


    helpers = [
        ql.FxSwapRateHelper( # Es una tasa par de Swap Fx
            ql.QuoteHandle(ql.SimpleQuote(r/10000)), # Objeto para tasas (entre 10000)
            ql.QuoteHandle(ql.SimpleQuote(t_mxn_usd_spot)), # Spot del tipo de cambio
            ql.Period(t), # Periodo del swap (en días)
            dias_liq, # Días de liquidación (0)
            calendario, 
            ajuste_fec,
            ult_dia_mes, # Si termina en último día de vez
            base_es_colateral, # Si es colateralizado o no 
            descuento) # curva de descuento
        for (r, t) in zip(tasas_fwd, tenors)]
    
    return helpers

def XCCYBasisHelpers(basis_xccy, tasas_ftiie, tenors, curva_colateral):
    """ Crea los helpers para los XCCY basis.
    
    Parameters
    ----------
    basis_xccy : list
        Basis de los XCCY basis.
    tasas_ftiie: list
        tasas de FTIIE a las que les restamos los basis
    tenors : list
        Tenors de los XCCY basis.
    curva_descuento : ql.YieldTermStructureHandle
        Curva de descuento a usar.
    
    Returns
    -------
    list
        Lista de helpers para los XCCY basis.
    """
    
    dias_liq = 2 # Días de liquidación (2)
    calendario = ql.Mexico() # Calendario de México
    ajuste_fec = ql.Following # Siempre se va al siguiente día hábil
    ult_dia_mes = False # Si obliga a terminar al final de mes
    dias_pago = 2 # Días que tarda en pagar después del corte de cupón
    frecuencia = ql.EveryFourthWeek # Frecuencia de pagos cada 4 semanas (28 días)
    periodo_de_inicio = ql.Period('0D') # Periodo de inicio de los swaps (0)




    indice_xccy = ql.OvernightIndex(
        'XCCY_FTIIE', # Nombre del índice
        dias_liq, # Días de liquidación
        ql.MXNCurrency(), # Moneda usada
        calendario, 
        ql.Actual360()) # Forma de conteo de días
    



    descuento = ql.RelinkableYieldTermStructureHandle() # Objeto para usar curvas
    descuento.linkTo(curva_colateral) # le agregamos la curva de descuento


    helpers = [ 
        ql.OISRateHelper( # Usamos un OIS Rate Helper porque usa una tasa diaria
            dias_liq,  # Días de liquidación
            ql.Period(t*4, ql.Weeks), # Periodo (en semanas)
            ql.QuoteHandle(ql.SimpleQuote(rf/ 100)),  # Tasa (entre 100)
            indice_xccy,  # Índice a encontrar
            descuento, # Curva de descuento
            ult_dia_mes,  # Si termina en último día de vez
            dias_pago, # Días de pago después del corte
            ajuste_fec, # Ajuste de fechas
            frecuencia, # Frecuencia de pagos
            calendario, # Calendario de México
            periodo_de_inicio, # Periodo de inicio de los swaps
            -1*basis/100) # Basis del XCCY

        for (basis, rf, t) in zip(basis_xccy, tasas_ftiie, tenors)]
    
    return helpers


def FXAndXCCYHelpers(tasas_fwd, tenors_fwd, t_mxn_usd_spot, basis_xccy, tasas_ftiie,
                     tenors_xccy, curva_descuento):
    """ Crea los helpers para los fwds de tipo de cambio y los XCCY basis.
    
    Parameters
    ----------
    tasas_fwd : list
        Tasas de los fwds de tipo de cambio.
    tenors_fwd : list
        Tenors de los fwds de tipo de cambio.
    tasas_xccy : list
        Tasas de los XCCY basis.
    tenors_xccy : list
        Tenors de los XCCY basis.
    curva_descuento : ql.YieldTermStructureHandle
        Curva de descuento a usar.
    
    Returns
    -------
    list
        Lista de helpers para los fwds de tipo de cambio y los XCCY basis.
    """
    
    # Helpers para fwds de tipo de cambio
    helpers_fwd = FXSwapHelpers(tasas_fwd, tenors_fwd, t_mxn_usd_spot, curva_descuento)
    
    # Helpers para XCCY basis
    helpers_xccy = XCCYBasisHelpers(basis_xccy, tasas_ftiie,
                                    tenors_xccy, curva_descuento)
    
    return helpers_fwd + helpers_xccy




# %% [markdown]
# ## Curva de SOFR
# 
# Por último, se definirán las tasas usadas para el ajuste de curva de SOFR. Estas tasas fueron obtenidas de Bloomberg al cierre del 19 de febrero de 2025.
# 
# ### Definición de Insumos
# Para SOFR, al igual que en FTIIE, se tienen tanto tasas par de Swaps como tasas de futuros. Los futuros de SOFr son pactados en fechas ya predeterminadas llamadas IMM (International Monetary Market). Los futuros son de 3 meses a partir de la fecha IMM vigente.
# 
# Los datos que se usarán para la cuva de SOFR, fueron obtenidos de Bloomberg. 

# %%
# Definición de la tasa cero
depo = 4.33

# Definción del tenor de la tasa cero
tenor_depo = 1 # 1 día

# Definición de tasas de SOFR
t_sofr_2Y = 4.147
t_sofr_3Y = 4.11665
t_sofr_4Y = 4.10919
t_sofr_5Y = 4.11125
t_sofr_6Y = 4.1187
t_sofr_7Y = 4.1279
t_sofr_8Y = 4.13713
t_sofr_9Y = 4.14073
t_sofr_10Y = 4.159
t_sofr_12Y = 4.1845
t_sofr_15Y = 4.2047
t_sofr_20Y = 4.214
t_sofr_25Y = 4.1491
t_sofr_30Y = 4.0518

# Definición de tenors de SOFR
tenors_sofr = [
    2, # 2 años
    3, # 3 años
    4, # 4 años
    5, # 5 años
    6, # 6 años
    7, # 7 años
    8, # 8 años
    9, # 9 años
    10, # 10 años
    12, # 12 años
    15, # 15 años
    20, # 20 años
    25, # 25 años
    30 # 30 años
]

# Definición de Futuros IMM de SOFR
fut_sofr_h5_px = 95.6825
fut_sofr_m5_px = 95.8
fut_sofr_u5_px = 95.915
fut_sofr_z5_px = 95.99
fut_sofr_h6_px = 96.03

# Definición de tenors de Futuros IMM de SOFR
tenors_fut_sofr = [
    'H5', # Marzo 2025
    'M5', # Junio 2025
    'U5', # Septiembre 2025
    'Z5', # Diciembre 2025
    'H6'  # Marzo 2026
]

sofr_futures = [
    fut_sofr_h5_px,
    fut_sofr_m5_px,
    fut_sofr_u5_px,
    fut_sofr_z5_px,
    fut_sofr_h6_px
]

sofr_swaps = [
    t_sofr_2Y,
    t_sofr_3Y,
    t_sofr_4Y,
    t_sofr_5Y,
    t_sofr_6Y,
    t_sofr_7Y,
    t_sofr_8Y,
    t_sofr_9Y,
    t_sofr_10Y,
    t_sofr_12Y,
    t_sofr_15Y,
    t_sofr_20Y,
    t_sofr_25Y,
    t_sofr_30Y]

# %% [markdown]
# ### Definición de objetos
# 
# Para la curva de SOFR, sencesitan tres tipos diferentes de instrumentos y por lo tanto de helpers. Para construir la curva se usarán los siguientes objetos de QuantLib:
# 
# - `ql.DepositRateHelper`: Deposit es tasa cero, es una helper para tasas cero
# - `ql.OISRateHelper`: Es la misma que hemos usado para la curva de FTIIE 
# - `ql.FutureRateHelper`: Este es un helper para futuros, en específico los IMM.
# 
# 

# %%
# Helpers de Futuros IMM de SOFR
def futureIMMHelpers(sofr_futures, tenors_fut_sofr):

    calendario = ql.UnitedStates(5) # Federal Reserve calendario
    fec_eval = ql.Settings.instance().evaluationDate # Fecha de evaluación
    dt_settlement = calendario.advance(fec_eval, ql.Period('2D')) # Fecha de liquidación (2 días)

    meses = 3 # numero de meses de los futuros IMM
    conteo_dias = ql.Actual360() # Forma de conteo de días
    ajuste_fec = ql.ModifiedFollowing # Ajuste de fechas (Si es fin de mes, se va al anterior día hábil)
    ult_dia_mes = True # Si obliga a terminar al final de mes

    # Calcular las siguientes fechas de vencimiento de los futuros IMM
    n_fut = len(tenors_fut_sofr)
    imm = ql.IMM.nextDate(dt_settlement) # Fecha de vencimiento inicial (próximo IMM)
    imm = dt_settlement
    # Se crea un diccionario para almacenar las fechas de vencimiento y sus tasas
    futures = {}
    for i in range(n_fut):
        imm = ql.IMM.nextDate(imm)
        futures[imm] = sofr_futures[i]

    
    futuresHelpers = [ql.FuturesRateHelper(
        ql.QuoteHandle(ql.SimpleQuote(futures[d])), 
        d, # Fecha de vencimiento del futuro 
        meses, # Número de meses del futuro
        calendario, # Calendario de USA
        ajuste_fec, # Ajuste de fechas
        ult_dia_mes, # Si termina en último día de vez
        conteo_dias) # Forma de conteo de días 
        for d in futures.keys()]
    
    return futuresHelpers

# Helpers para swaps SOFR
def SOFRHelpers(tasas_sofr, tenors_sofr, depo, tenor_depo):
    """
    Crea los helpers para las tasas SOFR.

    Parameters
    ----------
    tasas_sofr : list
        Tasas de los swaps SOFR.
    tenors_sofr : list
        Tenors de los swaps SOFR.
    depo : float
        Tasa de depósito SOFR.
    tenor_depo : int
        Tenor del depósito SOFR (en días).

    Returns
    -------
    list
        Lista de helpers para las tasas SOFR.
    """

    dias_liq = 2 # Días de liquidación (2)
    calendario = ql.UnitedStates(5) # Calendario de USA
    cont_dias = ql.Actual360() # Forma de conteo de días
    frecuencia = ql.Annual # Frecuencia de pagos
    ajuste_fec = ql.ModifiedFollowing # Siempre se va al siguiente día hábil cuando no es fin de mes
    ult_dia_mes = False # Si obliga a terminar al final de mes
    dias_pago = 2 # Días que tarda en pagar después del corte de cupón

    indice = ql.Sofr()
    descuento = ql.RelinkableYieldTermStructureHandle() # Objeto para usar curvas
    descuento.linkTo(ql.FlatForward(0, calendario, ql.QuoteHandle(ql.SimpleQuote(0.0)), cont_dias)) # Curva de descuento plana inicializada a 0

    depositHelpers = [ql.DepositRateHelper( # Es una tasa de depósito
        ql.QuoteHandle(ql.SimpleQuote(depo/100)), # Objeto para tasas (entre 100)
        ql.Period(tenor_depo, ql.Days), # Periodo de la tasa (en días)
        dias_liq, # Días de liquidación     
        calendario, # Calendario de USA
        ajuste_fec, # Ajuste de fechas
        ult_dia_mes, # Si termina en último día de vez
        cont_dias) # Forma de conteo de días
        for depo, tenor_depo in zip([depo], [tenor_depo])]
    
    swapHelpers = [ql.OISRateHelper( # Es una tasa par de Swap
        dias_liq, # Días de liquidación (2)
        ql.Period(t, ql.Years), # Periodo de la tasa (en años)
        ql.QuoteHandle(ql.SimpleQuote(r/100)), # Objeto para tasas
        indice, # Índice SOFR
        descuento, # Curva de descuento
        ult_dia_mes, # Si termina en último día de vez
        dias_pago, # Días de pago después del corte
        ajuste_fec, # Ajuste de fechas
        frecuencia, # Frecuencia de pagos,
        calendario) # Calendario de USA
        for r, t in zip(tasas_sofr, tenors_sofr)]

    helpers = depositHelpers + swapHelpers # Unimos los helpers de tasas cero y swaps
    return helpers



# %% [markdown]
# ## Definción de curvas
# 
# Ahora que se tienen las funciones apra crear los helpers apra cada curva, comenzaremos a construirlas por medio de los construectores ` ql.PiecewiseLogLinearDiscount` y `ql.PiecewiseNaturalLogCubicDiscount` que nos devolveran curvas de descuento para cada curva antes definida.
# 
# ### Curva SOFR
# Se comenzará con la curva de SOFR

# %%


# %%
def genSOFR(sofr_futures, tenors_fut_sofr, sofr_swaps, tenors_sofr, depo, tenor_depo):
    """
    Crea la curva de descuento SOFR.

    Parameters
    ----------
    sofr_futures : list
        Tasas de los futuros SOFR.
    tenors_fut_sofr : list
        Tenors de los futuros SOFR.
    sofr_swaps : list
        Tasas de los swaps SOFR.
    tenors_sofr : list
        Tenors de los swaps SOFR.
    depo : float
        Tasa de depósito SOFR.
    tenor_depo : int
        Tenor del depósito SOFR (en días).

    Returns
    -------
    ql.PiecewiseLogLinearDiscount
        Curva de descuento SOFR.
    """

    # Definición de los helpers de tasas SOFR
    imm_helpers = futureIMMHelpers(sofr_futures, tenors_fut_sofr) # Helpers de futuros IMM de SOFR
    swap_helpers = SOFRHelpers(sofr_swaps, tenors_sofr, depo, tenor_depo) # Helpers de tasas SOFR
    
    # Definición de la curva de descuento de SOFR
    crvSOFR = ql.PiecewiseLogLinearDiscount(
        0, # Fecha de evaluación (hoy)
        ql.UnitedStates(5), # Calendario de USA
        imm_helpers + swap_helpers, # Helpers de tasas SOFR
        ql.Actual360()) # Forma de conteo de días
    crvSOFR.enableExtrapolation() # Habilita la extrapolación de la curva

    return crvSOFR
# Definición de la curva de descuento de SOFR
crvSOFR = genSOFR(sofr_futures, tenors_fut_sofr, sofr_swaps, tenors_sofr, depo, tenor_depo)


df_nodos = pd.DataFrame(crvSOFR.nodes()).rename(columns={0: 'Fecha', 1: 'Factor de Descuento'}) # DataFrame con los nodos de la curva de descuento de SOFR
df_nodos

# %% [markdown]
# ### Curva de descuento mexicana
# 
# Ahora se define la curva de descuento mexicana
# 
# 

# %%
def genDISCTIIE(t_mxn_usd_spot, tasas_fwd_fx, tenors_fwd_fx, tasas_xccy, tenors_xccy,
                tasas_ftiie,  curva_descuento):
    """
    Crea la curva de descuento TIIE.

    Parameters
    ----------
    t_mxn_usd_spot : float
        Tasa de tipo de cambio MXN/USD Spot.
    tasas_fwd_fx : list
        Tasas de los fwds de tipo de cambio.
    tenors_futuros : list
        Tenors de los fwds de tipo de cambio.
    tasas_xccy : list
        Tasas de los XCCY basis.
    tenors_xccy : list
        Tenors de los XCCY basis.
    tasas_tiie28 : list
        Tasas TIIE 28 días.
    tenors_tiie28 : list
        Tenors TIIE 28 días.
    curva_descuento : ql.YieldTermStructureHandle
        Curva de descuento a usar.

    Returns
    -------
    ql.PiecewiseLogLinearDiscount
        Curva de descuento TIIE.
    """


    # Definición de los helpers para fwds y XCCY basis
    helpers_disc = FXAndXCCYHelpers(
        tasas_fwd_fx, 
        tenors_fwd_fx, 
        t_mxn_usd_spot, 
        tasas_xccy, 
        tasas_ftiie,
        tenors_xccy, 
        curva_descuento)

    # Definición de la curva de descuento TIIE
    crvTIIE = ql.PiecewiseNaturalLogCubicDiscount( # Curva de descuento TIIE 
        0, # Fecha de evaluación (hoy)
        ql.Mexico(), # Calendario de México
        helpers_disc, # Helpers para TIIE y fwds/XCCY basis
        ql.Actual360()) # Forma de conteo de días
    
    crvTIIE.enableExtrapolation() # Habilita la extrapolación de la curva

    return crvTIIE


crvDISCTIIE = genDISCTIIE(
    t_mxn_usd_spot,
    tasas_fwd_fx,
    tenors_fwd_fx,
    tasas_xccy,
    tenors_xccy,
    tasas_ftiie,
    crvSOFR)

df_nodos = pd.DataFrame(crvDISCTIIE.nodes()).rename(columns={0: 'Fecha', 1: 'Factor de Descuento'}) # DataFrame con los nodos de la curva de descuento de SOFR
df_nodos

# %% [markdown]
# ### Curvas de TIIE28 y FTIIE
# Por último la curva de TIIE28 y TIIE de Fondeo
# 

# %%
# Se definen la función que genera la curva de tasas TIIE 28 días y la curva de tasas FTIIE

def genTIIE28(tasas_tiie28, tenors_tiie28, curva_descuento):
    """
    Crea la curva de tasas TIIE 28 días.

    Parameters
    ----------
    tasas_ftiie : list
        Tasas FTIIE.
    tenors_ftiie : list
        Tenors FTIIE.
    curva_descuento : ql.YieldTermStructureHandle
        Curva de descuento a usar.

    Returns
    -------
    ql.PiecewiseLogLinearDiscount
        Curva de tasas TIIE 28 días.
    """

    # Definición de los helpers para TIIE 28 días
    helpers_tiiie = TIIE28Helpers(tasas_tiie28, tenors_tiie28, curva_descuento)

    # Definición de la curva de tasas TIIE 28 días
    crvTIIE28 = ql.PiecewiseNaturalLogCubicDiscount(
        0, # Fecha de evaluación (hoy)
        ql.Mexico(), # Calendario de México
        helpers_tiiie, # Helpers para TIIE 28 días
        ql.Actual360()) # Forma de conteo de días
    
    crvTIIE28.enableExtrapolation() # Habilita la extrapolación de la curva

    return crvTIIE28


def genFTIIE(tasas_fut, tenors_fut, tasas_ftiie, tenors_ftiie,
             curva_descuento, fechas_banxico, tasas_banxico):
    """
    Crea la curva de tasas FTIIE.

    Parameters
    ----------
    tasas_fut : list
        Tasas de los futuros FTIIE.
    tenors_fut : list
        Tenors de los futuros FTIIE.
    tasas_ftiie : list
        Tasas FTIIE.
    tenors_ftiie : list
        Tenors FTIIE.
    curva_descuento : ql.YieldTermStructureHandle
        Curva de descuento a usar.
    fechas_banxico : list
        Fechas de Banxico para los futuros FTIIE.
    tasas_banxico : list
        Tasas de Banxico para los futuros FTIIE.

    Returns
    -------
    ql.PiecewiseLogLinearDiscount
        Curva de tasas FTIIE.
    """

    # Definición de los helpers para FTIIE
    helpers_ftiie = FTIIEHelpers(tasas_fut, tenors_fut,
                                 tasas_ftiie, tenors_ftiie,
                                 curva_descuento, fechas_banxico, tasas_banxico)

    # Definición de la curva de tasas FTIIE
    crvFTIIE = ql.PiecewiseNaturalLogCubicDiscount(
        0, # Fecha de evaluación (hoy)
        ql.Mexico(), # Calendario de México
        helpers_ftiie, # Helpers para FTIIE
        ql.Actual360()) # Forma de conteo de días
    
    crvFTIIE.enableExtrapolation() # Habilita la extrapolación de la curva

    return crvFTIIE


# Ahora creamos las curvas de tasas TIIE 28 días y FTIIE
crvTIIE28 = genTIIE28(tasas_tiie28, tenors_tiie28, crvDISCTIIE) # Curva de tasas TIIE 28 días
df_nodos = pd.DataFrame(crvTIIE28.nodes()).rename(columns={0: 'Fecha', 1: 'Factor de Descuento'}) # DataFrame con los nodos de la curva de descuento de SOFR
df_nodos

# %%
# Ahora lo hacemos para FTIIE
crvFTIIE = genFTIIE(tasas_fut, tenors_futuros,
                    tasas_ftiie, tenors_ftiie, crvDISCTIIE,
                    fechas_banxico, tasas_banxico) # Curva de tasas FTIIE
# DataFrame con los nodos de la curva de descuento de FTIIE
df_nodos = pd.DataFrame(crvFTIIE.nodes()).rename(columns={0: 'Fecha', 1: 'Factor de Descuento'}) # DataFrame con los nodos de la curva de descuento de SOFR
df_nodos


# %% [markdown]
# A partir de estas curvas podemos calcular para cualquier día desado las tasas cero, los factores de descuento o las tasas forward. A partir de estas curvas podemos tambien crear y valuar swaps de TIIE de Fondeo y de TIIE28 asi como calcular su riesgo.

# %% [markdown]
# 


