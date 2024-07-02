import pandas as pd
import tti
import warnings
import numpy as np
import matplotlib.pyplot as plt
import requests
import io  # Para trabajar con archivos en memoria
from PIL import Image  # Para manejar imágenes en memoria
from urllib.parse import urlparse
import matplotlib.patches as mpatches

# Deshabilitar los avisos de FutureWarning
warnings.simplefilter(action='ignore', category=FutureWarning)

# Función para obtener los datos
def get_data(file_path):
    df = pd.read_csv(file_path)
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    df = df.set_index('Datetime')
    return df

# Función para calcular RSI con TTI
def calculate_rsi(data, period=20):
    rsi = tti.indicators.RelativeStrengthIndex(input_data=data, period=period).getTiData()
    return rsi['rsi']

# Función para determinar señal de entrada basada en RSI
def entry_rulersi(data):
    rsi = calculate_rsi(data)
    if rsi.iloc[-1] < 46:
        return True
    else:
        return False

# Función para determinar señal de salida basada en RSI
def exit_rulersi(data):
    rsi = calculate_rsi(data)
    if rsi.iloc[-1] > 70:
        return True
    else:
        return False

def send_message_with_image_to_telegram(message, image_path, chat_id, token):
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    files = {'photo': open(image_path, 'rb')}
    data = {'chat_id': chat_id, 'caption': message}
    response = requests.post(url, files=files, data=data)
    files['photo'].close()
    return response.json()

def plot_colored_line(x, y):
    colors = ['g' if y[i] >= y[i-1] else 'r' for i in range(1, len(y))]
    for i in range(len(colors)):
        plt.plot(x[i:i+2], y[i:i+2], color=colors[i])

# Configuración inicial
modecompra = True
entrada = 0
operaciones = 0
df = get_data('historical_data.csv')
saldo_inicial = 100  # Saldo inicial
saldo_actual = saldo_inicial  # Saldo actual, se actualiza durante el backtesting
compr= 0
fechacompra = 0
# Realiza el backtesting
print("Inicia backtesting:")
for index, row in df.iterrows():
    data = df.loc[:row.name]
    if len(data) > 50:
        precio_actual = row['Close']
        
        # Verifica si se debe realizar una compra
        if entry_rulersi(data) and modecompra:
            print("Compramos " + str(row['Close']))
            modecompra = False
            saldo_actual -= row['Close'] * 1.001  # Resta el precio de compra al saldo
            entrada = row['Close']  # Actualiza el precio de entrada
            
            plot_data = df.loc[:row.name]
            
            # Graficar el precio actual con la señal de compra
            fig, ax = plt.subplots(figsize=(10, 6))
            plot_colored_line(plot_data.index, plot_data['Close'])
            ax.scatter(row.name, row['Close'], marker='^', color='g', s=100, label='Compra', zorder=5)  # Marcador de compra más grande (s=100)
            ax.set_title('Compra realizada ' + str(row['Close']), color='white')
            ax.set_xlabel('Fecha', color='white')
            ax.set_ylabel('Precio', color='white')
            ax.legend()
            ax.grid(True, color='white', alpha=0.1)
            ax.set_facecolor('black')
            ax.tick_params(colors='white')
            nombr = row.name
            fechacompra = index
            # Guardar el gráfico temporalmente como archivo
            image_path = 'chart.png'  # Ruta relativa o absoluta válida en Windows
            plt.savefig(image_path, facecolor='black', bbox_inches='tight', pad_inches=0)
            plt.close()  # Cerrar la figura para liberar memoria
            
            send_message_with_image_to_telegram('🟢🟢🟢 Compra realizada: ' + str(row['Close']) + ' 🟢🟢🟢', image_path, '@orgempresarialbot', '6403909179:AAHYPFEsjp6Hj7t3o8_Wwzrcn55unSMZLfc')                
                        
        # Verifica si se debe realizar una venta
        elif (precio_actual < entrada * 0.97 or (precio_actual > entrada * 1.01 and exit_rulersi(data))) and not modecompra:
            print("Vendemos " + str(row['Close']))
            modecompra = True
            saldo_actual += row['Close'] * 0.999  # Suma el precio de venta al saldo
            operaciones += 1
            ganancia = (row['Close'] * 0.999)- entrada
            if(ganancia > 0):
                respuesta= "Ganancia"
            else:
                respuesta= "Perdida"
            plot_data = df.loc[:row.name]
            
            # Graficar el precio actual con la señal de venta y el marcador de compra
            fig, ax = plt.subplots(figsize=(10, 6))
            plot_colored_line(plot_data.index, plot_data['Close'])
            ax.scatter(row.name, row['Close'], marker='v', color='r', s=100, label='Venta', zorder=5)  # Marcador de venta más grande (s=100)
            ax.scatter(nombr, entrada, marker='^', color='g', s=100, label=f'Compra, {fechacompra}', zorder=5)  # Mostrar el marcador de compra también
            ax.set_title(f'Venta realizada, {respuesta}: {ganancia:.2f}', color='white')
            ax.set_xlabel('Fecha', color='white')
            ax.set_ylabel('Precio', color='white')
            ax.legend()
            ax.grid(True, color='white', alpha=0.1)
            ax.set_facecolor('black')
            ax.tick_params(colors='white')
            
            # Guardar el gráfico temporalmente como archivo
            image_path = 'chart.png'  # Ruta relativa o absoluta válida en Windows
            plt.savefig(image_path, facecolor='black', bbox_inches='tight', pad_inches=0)
            plt.close()  # Cerrar la figura para liberar memoria
            
            # Enviar la imagen a Telegram
            send_message_with_image_to_telegram('🔴🔴🔴 Venta realizada: ' + str(row['Close']) + ' 🔴🔴🔴', image_path, '@orgempresarialbot', '6403909179:AAHYPFEsjp6Hj7t3o8_Wwzrcn55unSMZLfc')    

# Calcular ganancia total
ganancia_total = saldo_actual - saldo_inicial
print("Ganancia total durante el backtesting:", ganancia_total)
print("Número de operaciones realizadas:", operaciones)
