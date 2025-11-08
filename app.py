from flask import Flask, render_template_string, url_for
from extensiones import db
from formularios import formularios_bp
from base_de_datos import base_de_datos_bp
from generar_contrato import generar_contrato_bp
from models import Evento  # Asegura la creación de tablas


# ---------------------------
# CONFIGURACIÓN DE LA APP
# ---------------------------
app = Flask(__name__)
app.secret_key = "supersecretkey"
app.jinja_env.globals.update(str=str)


# ---------------------------
# CONFIGURACIÓN DE BASE DE DATOS (Render PostgreSQL)
# ---------------------------
app.config['SQLALCHEMY_DATABASE_URI'] = (
    "postgresql://pintacaritas_user:ChJEwe89MhHGB6ZAsznN3w5kOWDflkUS@"
    "dpg-d47pdpshg0os73frqtg0-a.oregon-postgres.render.com/pintacaritas"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar base de datos
db.init_app(app)
with app.app_context():
    db.create_all()


# ---------------------------
# REGISTRO DE BLUEPRINTS
# ---------------------------
app.register_blueprint(formularios_bp)
app.register_blueprint(base_de_datos_bp)
app.register_blueprint(generar_contrato_bp)


# ---------------------------
# RUTA PRINCIPAL (MENÚ)
# ---------------------------
@app.route('/')
def home():
    return render_template_string("""
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Panel de Control - Pintacaritas</title>
  <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
  <style>
    body {
      background-image: url('{{ url_for('static', filename='imagenes/pintacaritas_fondo.png') }}');
      background-size: contain;
      background-position: center;
      background-repeat: no-repeat;
      background-attachment: fixed;
      background-color: #9333ea;
    }
    .overlay {
      background-color: rgba(0,0,0,0.6);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 2rem;
    }
    .card {
      transition: transform 0.3s, box-shadow 0.3s;
    }
    .card:hover {
      transform: scale(1.05);
      box-shadow: 0 10px 25px rgba(0,0,0,0.4);
    }
  </style>
</head>
<body>
  <div class="overlay text-white rounded-2xl p-8 w-full max-w-5xl mx-auto">
    <div class="text-center">
      <h1 class="text-4xl font-bold mb-3">🎨 Panel de Control - Pintacaritas</h1>
      <p class="text-lg mb-10 opacity-90">Selecciona una opción para comenzar</p>

      <div class="grid grid-cols-1 sm:grid-cols-2 gap-8">

        <!-- Formulario -->
        <a href="{{ url_for('formularios.seleccionar_formulario') }}"
           class="card bg-blue-500 hover:bg-blue-600 rounded-2xl p-8 flex flex-col items-center shadow-xl">
          <div class="text-6xl mb-4">🎉</div>
          <h2 class="text-2xl font-semibold mb-2">Llenar formulario de evento</h2>
          <p class="text-sm opacity-90">Registra los detalles del evento de Pintacaritas o Glitter.</p>
        </a>

        <!-- Base de datos -->
        <a href="{{ url_for('base_de_datos.lista_eventos') }}"
           class="card bg-green-500 hover:bg-green-600 rounded-2xl p-8 flex flex-col items-center shadow-xl">
          <div class="text-6xl mb-4">📂</div>
          <h2 class="text-2xl font-semibold mb-2">Ver base de datos</h2>
          <p class="text-sm opacity-90">Consulta y edita los registros guardados.</p>
        </a>

        <!-- Generar contrato -->
        <a href="{{ url_for('generar_contrato.generar_contrato') }}"
           class="card bg-pink-500 hover:bg-pink-600 rounded-2xl p-8 flex flex-col items-center shadow-xl sm:col-span-2">
          <div class="text-6xl mb-4">📝</div>
          <h2 class="text-2xl font-semibold mb-2">Generar contrato</h2>
          <p class="text-sm opacity-90">Crea un contrato en formato PDF o PNG a partir del folio del evento.</p>
        </a>

      </div>
    </div>
  </div>
</body>
</html>
""")

# ---------------------------
# EJECUCIÓN DE LA APP
# ---------------------------
if __name__ == '__main__':
    app.run(debug=True, port=5000)
