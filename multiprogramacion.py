import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import threading
import time
import random
import pandas as pd

# Configuración inicial
total_processes = []
running_processes = []
process_colors = {}
running = False
total_memory = 100  # Memoria total del sistema
allocated_memory = 0  # Memoria actualmente en uso

def generate_process(pid=None, burst_time=None, memory=None):
    pid = pid if pid else len(total_processes) + 1
    color = generate_unique_color()
    process_colors[pid] = color
    mem_required = memory if memory else random.randint(5, 20)
    burst_time = burst_time if burst_time else random.randint(3, 10)
    return {
        "PID": pid,
        "Burst Time": burst_time,
        "Remaining Time": burst_time,  # Para la lógica interna
        "Memory": mem_required,
        "Elapsed Time": 0  # Tiempo transcurrido que incrementará
    }

def generate_unique_color():
    while True:
        color = "rgb(" + ", ".join(map(str, (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))) + ")"
        if color not in process_colors.values():
            return color

def run_simulation():
    global running, allocated_memory
    while running:
        if running_processes:
            for process in running_processes:
                if process["Remaining Time"] > 0:
                    process["Remaining Time"] -= 1
                    process["Elapsed Time"] += 1
                elif process["Remaining Time"] == 0 and process["Memory"] > 0:
                    allocated_memory -= process["Memory"]  # Liberamos memoria cuando el proceso finaliza
                    process["Memory"] = 0  # Evitamos restar varias veces
        time.sleep(1)


# Crear la app Dash
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Simulación de Multiprogramación con Memoria"),
    
    html.Div([
        html.Button("Agregar Proceso Aleatorio", id="add-process", n_clicks=0),
        html.Button("Agregar Proceso Personalizado", id="add-custom-process", n_clicks=0),
        html.Button("Iniciar Simulación", id="start-simulation", n_clicks=0),
        html.Button("Detener Simulación", id="stop-simulation", n_clicks=0),
        html.Button("Limpiar Procesos", id="clear-processes", n_clicks=0)
    ]),
    
    html.Div([
        html.Label("Burst Time:"),
        dcc.Input(id="input-burst-time", type="number", min=1, step=1),
        html.Label("Memory (MB):"),
        dcc.Input(id="input-memory", type="number", min=1, step=1)
    ]),
    
    html.Label("Memoria Total (MB):"),
    dcc.Input(id="input-total-memory", type="number", value=100, step=1),
    html.Button("Actualizar Memoria", id="update-memory", n_clicks=0),
    
    dash_table.DataTable(
        id="process-table",
        columns=[
            {"name": "PID", "id": "PID"},
            {"name": "Burst Time", "id": "Burst Time"},
            {"name": "Tiempo restante", "id": "Tiempo_restante"},
            {"name": "Memory", "id": "Memory"}
        ],
        data=[]
    ),
    
    dcc.Interval(
        id="interval-update",
        interval=1000,
        n_intervals=0,
        disabled=True
    ),
    
    dcc.Graph(id="process-graph"),
    dcc.Graph(id="memory-graph")
])

@app.callback(
    [Output("process-table", "data"), Output("process-graph", "figure"), Output("memory-graph", "figure"), Output("interval-update", "disabled")],
    [Input("add-process", "n_clicks"), Input("add-custom-process", "n_clicks"), Input("start-simulation", "n_clicks"), Input("stop-simulation", "n_clicks"), Input("clear-processes", "n_clicks"), Input("update-memory", "n_clicks"), Input("interval-update", "n_intervals")],
    [State("input-burst-time", "value"), State("input-memory", "value"), State("input-total-memory", "value")]
)
def update_dashboard(add_clicks, add_custom_clicks, start_clicks, stop_clicks, clear_clicks, update_mem_clicks, n_intervals, burst_time, memory, new_total_memory):
    global running, allocated_memory, total_memory
    ctx = dash.callback_context
    if not ctx.triggered:
        return total_processes, update_graph(), update_memory_graph(), not running
    
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if trigger_id == "add-process":
        new_process = generate_process()
        if allocated_memory + new_process["Memory"] <= total_memory:
            total_processes.append(new_process)
            running_processes.append(new_process.copy())
            allocated_memory += new_process["Memory"]
    elif trigger_id == "add-custom-process" and burst_time and memory:
        new_process = generate_process(burst_time=burst_time, memory=memory)
        if allocated_memory + new_process["Memory"] <= total_memory:
            total_processes.append(new_process)
            running_processes.append(new_process.copy())
            allocated_memory += new_process["Memory"]
    elif trigger_id == "update-memory" and new_total_memory:
        total_memory = new_total_memory
    elif trigger_id == "start-simulation" and not running:
        running = True
        threading.Thread(target=run_simulation, daemon=True).start()
    elif trigger_id == "stop-simulation":
        running = False
    elif trigger_id == "clear-processes":
        total_processes.clear()
        running_processes.clear()
        process_colors.clear()
        allocated_memory = 0

    # Formatear los datos para la tabla
    table_data = []
    for process in total_processes:
        # Buscamos el proceso correspondiente en running_processes para obtener el tiempo actualizado
        running_process = next((p for p in running_processes if p["PID"] == process["PID"]), process)
        table_data.append({
            "PID": process["PID"],
            "Burst Time": process["Burst Time"],
            "Tiempo_restante": running_process["Remaining Time"],
            "Memory": process["Memory"]
        })
    
    return table_data, update_graph(), update_memory_graph(), not running

def update_graph():
    df = pd.DataFrame(running_processes)
    if df.empty:
        return go.Figure()
    
    fig = go.Figure(
        data=[go.Bar(x=df["PID"], y=df["Remaining Time"], name="Tiempo Restante", marker=dict(color=[process_colors[pid] for pid in df["PID"]]))],
        layout=go.Layout(
            title="Procesos en Ejecución",
            xaxis_title="ID del Proceso",
            yaxis_title="Tiempo Restante (s)",
            barmode="group"
        )
    )
    return fig

def update_memory_graph():
    used_memory = allocated_memory
    free_memory = total_memory - used_memory

    fig = go.Figure(
        data=[go.Pie(labels=["Usada", "Libre"], values=[used_memory, free_memory], hole=0.4, 
                     marker=dict(colors=["red", "green"]))],
        layout=go.Layout(title="Uso de Memoria", transition_duration=500)  # Agregamos animación
    )
    return fig


if __name__ == "__main__":
    app.run_server(debug=True)