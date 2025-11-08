# base_de_datos.py
from flask import Blueprint, render_template_string, request, redirect, url_for, flash, send_file
from extensiones import db
from models import Evento
from io import BytesIO
from datetime import datetime
import csv
import math

# Intentar cargar pandas para exportar XLSX
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except Exception:
    PANDAS_AVAILABLE = False

base_de_datos_bp = Blueprint('base_de_datos', __name__, url_prefix='/base-de-datos')


# ---------------------------
# FILTROS
# ---------------------------
def aplicar_filtros(query, tipo_evento, fecha_desde, fecha_hasta, qsearch):
    if tipo_evento:
        query = query.filter(Evento.tipo_evento == tipo_evento)
    if fecha_desde:
        try:
            fd = datetime.strptime(fecha_desde, "%Y-%m-%d").date()
            query = query.filter(Evento.fecha_evento >= fd)
        except:
            pass
    if fecha_hasta:
        try:
            fh = datetime.strptime(fecha_hasta, "%Y-%m-%d").date()
            query = query.filter(Evento.fecha_evento <= fh)
        except:
            pass
    if qsearch:
        like = f"%{qsearch}%"
        query = query.filter(
            db.or_(
                Evento.nombre_cliente.ilike(like),
                Evento.nombre_salon.ilike(like),
                Evento.direccion.ilike(like)
            )
        )
    return query


# ---------------------------
# LISTA DE EVENTOS
# ---------------------------
@base_de_datos_bp.route('/', methods=['GET'])
def lista_eventos():
    tipo_evento = request.args.get('tipo_evento', '')
    fecha_desde = request.args.get('fecha_desde', '')
    fecha_hasta = request.args.get('fecha_hasta', '')
    qsearch = request.args.get('q', '')

    page = request.args.get('page', 1, type=int)
    per_page = 10

    query = Evento.query.order_by(Evento.fecha_evento.desc(), Evento.id.desc())
    query = aplicar_filtros(query, tipo_evento or None, fecha_desde or None, fecha_hasta or None, qsearch or None)

    total = query.count()
    pages = max(1, math.ceil(total / per_page))
    eventos = query.offset((page - 1) * per_page).limit(per_page).all()

    return render_template_string("""
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>📊 Base de Datos</title>
<link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
<style>
  body { background: linear-gradient(135deg, #bfdbfe, #93c5fd); min-height: 100vh; }
  .readonly { background-color: #f3f4f6; color: #4b5563; pointer-events: none; }
  .editable { background-color: #ffffff; color: #000000; }
  th { background-color: #e0f2fe; position: sticky; top: 0; }
</style>
<script>
function toggleEdit(rowId) {
  const row = document.getElementById('row-' + rowId);
  const inputs = row.querySelectorAll('input, textarea');
  const editBtn = row.querySelector('.btn-edit');
  const saveBtn = row.querySelector('.btn-save');

  inputs.forEach(el => {
    el.classList.toggle('readonly');
    el.classList.toggle('editable');
    el.readOnly = !el.readOnly;
  });
  editBtn.classList.toggle('hidden');
  saveBtn.classList.toggle('hidden');
}
</script>
</head>
<body class="p-6">
  <div class="max-w-7xl mx-auto bg-white p-6 rounded-2xl shadow-lg">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold text-blue-700">📋 Base de datos de eventos</h1>
      <div>
        <a href="{{ url_for('formularios.seleccionar_formulario') }}" class="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg mr-2">⬅️ Formularios</a>
        <a href="{{ url_for('base_de_datos.exportar', tipo_evento=tipo_evento, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta, q=qsearch) }}" class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg">📥 Exportar</a>
      </div>
    </div>

    <!-- FILTROS -->
    <form method="GET" class="bg-blue-50 p-4 rounded-lg shadow mb-4 grid grid-cols-1 md:grid-cols-6 gap-3">
      <div>
        <label class="block text-sm font-semibold text-gray-700">Tipo de evento</label>
        <select name="tipo_evento" class="mt-1 block w-full p-2 border rounded">
          <option value="">Todos</option>
          <option value="Pintacaritas" {% if tipo_evento == 'Pintacaritas' %}selected{% endif %}>Pintacaritas</option>
          <option value="Glitter" {% if tipo_evento == 'Glitter' %}selected{% endif %}>Glitter</option>
        </select>
      </div>
      <div><label class="block text-sm font-semibold text-gray-700">Desde</label><input type="date" name="fecha_desde" value="{{ fecha_desde }}" class="mt-1 block w-full p-2 border rounded"></div>
      <div><label class="block text-sm font-semibold text-gray-700">Hasta</label><input type="date" name="fecha_hasta" value="{{ fecha_hasta }}" class="mt-1 block w-full p-2 border rounded"></div>
      <div class="md:col-span-2"><label class="block text-sm font-semibold text-gray-700">Buscar</label><input type="text" name="q" value="{{ qsearch }}" placeholder="Cliente / dirección / salón" class="mt-1 block w-full p-2 border rounded"></div>
      <div class="flex items-end"><button type="submit" class="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded">Filtrar</button></div>
    </form>

    <div class="overflow-auto rounded-lg shadow">
      <table class="min-w-full divide-y divide-gray-200 text-sm">
        <thead>
          <tr>
            <th class="px-2 py-2 text-left">ID</th>
            <th class="px-2 py-2 text-left">Cliente</th>
            <th class="px-2 py-2 text-left">Tipo</th>
            <th class="px-2 py-2 text-left">Fecha</th>
            <th class="px-2 py-2 text-left">Horario</th>
            <th class="px-2 py-2 text-left">Ubicación</th>
            <th class="px-2 py-2 text-left">Folio</th>
            <th class="px-2 py-2 text-left">Total</th>
            <th class="px-2 py-2 text-left">Anticipo</th>
            <th class="px-2 py-2 text-left">Restan</th>
            <th class="px-2 py-2 text-left">Comentarios</th>
            <th class="px-2 py-2 text-center">Acciones</th>
          </tr>
        </thead>
        <tbody>
          {% for ev in eventos %}
          <tr id="row-{{ ev.id }}" class="hover:bg-blue-50">
            <form method="POST" action="{{ url_for('base_de_datos.editar_evento', evento_id=ev.id) }}">
              <td class="px-2 py-2">{{ ev.id }}</td>
              <td class="px-2 py-2">{{ ev.nombre_cliente }}</td>
              <td class="px-2 py-2">{{ ev.tipo_evento }}</td>
              <td class="px-2 py-2">{{ ev.fecha_evento.strftime('%Y-%m-%d') if ev.fecha_evento else '' }}</td>
              <td class="px-2 py-2">{{ ev.hora_inicio or '' }} - {{ ev.hora_termino or '' }}</td>
              <td class="px-2 py-2 text-xs">{{ ev.municipio or '' }}<br>{{ ev.nombre_salon or '' }}</td>
              <td class="px-2 py-2"><input name="folio_manual" value="{{ ev.folio_manual or '' }}" class="w-24 border rounded px-1 readonly" readonly></td>
              <td class="px-2 py-2"><input type="number" step="0.01" name="total" value="{{ ev.total if ev.total is not none else '' }}" class="w-20 border rounded px-1 readonly" readonly></td>
              <td class="px-2 py-2"><input type="number" step="0.01" name="anticipo" value="{{ ev.anticipo if ev.anticipo is not none else '' }}" class="w-20 border rounded px-1 readonly" readonly></td>
              <td class="px-2 py-2"><input type="number" step="0.01" name="restan" value="{{ ev.restan if ev.restan is not none else '' }}" class="w-20 border rounded px-1 readonly" readonly></td>
              <td class="px-2 py-2"><textarea name="comentarios" class="w-40 border rounded px-1 readonly" rows="1" readonly>{{ ev.comentarios or '' }}</textarea></td>
              <td class="px-2 py-2 text-center">
                <button type="button" onclick="toggleEdit({{ ev.id }})" class="btn-edit bg-yellow-500 hover:bg-yellow-600 text-white px-2 py-1 rounded text-xs">✏️ Editar</button>
                <button type="submit" class="btn-save bg-green-600 hover:bg-green-700 text-white px-2 py-1 rounded text-xs hidden">💾 Guardar</button>
              </td>
            </form>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>

    <div class="flex justify-between items-center mt-4 text-sm">
      {% if page > 1 %}
        <a href="{{ url_for('base_de_datos.lista_eventos', page=page-1, tipo_evento=tipo_evento, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta, q=qsearch) }}" class="px-3 py-1 bg-gray-200 rounded">« Anterior</a>
      {% else %}
        <span></span>
      {% endif %}
      <span>Página {{ page }} de {{ pages }}</span>
      {% if page < pages %}
        <a href="{{ url_for('base_de_datos.lista_eventos', page=page+1, tipo_evento=tipo_evento, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta, q=qsearch) }}" class="px-3 py-1 bg-gray-200 rounded">Siguiente »</a>
      {% endif %}
    </div>
  </div>
</body>
</html>
    """, eventos=eventos, total=total, page=page, pages=pages,
    tipo_evento=tipo_evento, fecha_desde=fecha_desde, fecha_hasta=fecha_hasta, qsearch=qsearch)


# ---------------------------
# GUARDAR CAMBIOS
# ---------------------------
@base_de_datos_bp.route('/editar/<int:evento_id>', methods=['POST'])
def editar_evento(evento_id):
    ev = Evento.query.get_or_404(evento_id)

    def safe_float(v):
        try: return float(v)
        except: return None

    ev.folio_manual = request.form.get('folio_manual') or None
    ev.total = safe_float(request.form.get('total'))
    ev.anticipo = safe_float(request.form.get('anticipo'))
    ev.restan = safe_float(request.form.get('restan'))
    ev.comentarios = request.form.get('comentarios') or None

    if ev.restan is None and ev.total is not None and ev.anticipo is not None:
        ev.restan = ev.total - ev.anticipo

    try:
        db.session.commit()
        flash("✅ Cambios guardados correctamente", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Error: {e}", "error")

    return redirect(request.referrer or url_for('base_de_datos.lista_eventos'))


# ---------------------------
# EXPORTAR
# ---------------------------
@base_de_datos_bp.route('/exportar')
def exportar():
    tipo_evento = request.args.get('tipo_evento', '')
    fecha_desde = request.args.get('fecha_desde', '')
    fecha_hasta = request.args.get('fecha_hasta', '')
    qsearch = request.args.get('q', '')

    query = aplicar_filtros(Evento.query, tipo_evento or None, fecha_desde or None, fecha_hasta or None, qsearch or None)
    eventos = query.all()

    headers = [
        "id", "tipo_evento", "nombre_cliente", "whatsapp", "fecha_evento",
        "hora_inicio", "hora_termino", "cantidad_horas", "servicios_interes",
        "municipio", "nombre_salon", "direccion", "fecha_registro",
        "folio_manual", "total", "anticipo", "restan", "comentarios"
    ]

    if PANDAS_AVAILABLE:
        df = pd.DataFrame([{h: getattr(e, h) for h in headers} for e in eventos])
        bio = BytesIO()
        df.to_excel(bio, index=False)
        bio.seek(0)
        return send_file(bio, download_name=f"eventos_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx", as_attachment=True)

    bio = BytesIO()
    writer = csv.writer(bio)
    writer.writerow(headers)
    for e in eventos:
        writer.writerow([getattr(e, h) for h in headers])
    bio.seek(0)
    return send_file(bio, download_name=f"eventos_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", as_attachment=True)
