from flask import Blueprint, render_template_string, request, send_file
from extensiones import db
from models import Evento
from io import BytesIO
from datetime import datetime
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
import fitz  # PyMuPDF
import requests
import os

generar_contrato_bp = Blueprint("generar_contrato", __name__)

# -----------------------------
# Diccionario de meses en español
# -----------------------------
MESES_ES = {
    "January": "ENERO","February": "FEBRERO","March": "MARZO","April": "ABRIL",
    "May": "MAYO","June": "JUNIO","July": "JULIO","August": "AGOSTO",
    "September": "SEPTIEMBRE","October": "OCTUBRE","November": "NOVIEMBRE","December": "DICIEMBRE"
}

# ============================================================
# FUNCIONES DE GENERACIÓN DE CONTRATOS
# ============================================================

def generar_contrato_pintacaritas(evento):
    """Genera el contrato tipo PINTACARITAS"""
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    # FOLIO
    can.setFont("Helvetica-Bold", 22)
    can.setFillColor(colors.red)
    can.drawString(436, 623, str(evento.folio_manual or ""))

    # FECHA
    mes = MESES_ES[evento.fecha_evento.strftime("%B")]
    fecha_larga = f"{evento.fecha_evento.day} DE {mes} DE {evento.fecha_evento.year}"
    can.setFont("Helvetica-Bold", 12)
    can.setFillColor(colors.blue)
    can.drawString(240, 543, fecha_larga)

    # HORARIOS
    can.drawString(240, 498, str(evento.hora_inicio or "").upper())
    can.drawString(295, 498, ("- " + str(evento.hora_termino or "")).upper())
    can.drawString(370, 498, ("(" + str(evento.cantidad_horas or "") + ")").upper())

    # SALÓN
    can.drawString(240, 452, ("(" + str(evento.nombre_salon or "") + ")").upper())

    # DIRECCIÓN
    texto_completo = f"{(evento.municipio or '').upper()} - {(evento.direccion or '').upper()}"
    can.drawString(240, 418, texto_completo)

    # SERVICIOS
    can.setFont("Helvetica-Bold", 10)
    texto = str(evento.servicios_interes or "").upper()
    lineas = texto.replace(',', '\n').split('\n')
    y_inicial = 386
    for i, linea in enumerate(lineas):
        can.drawString(240, y_inicial - i*10, linea.strip())

    can.drawString(390, 362, "(INCLUYE)")  # Personalízalo si tienes campo

    # CLIENTE
    can.setFont("Helvetica-Bold", 12)
    can.drawString(240, 320, str(evento.nombre_cliente or "").upper())
    can.drawString(240, 287, str(evento.whatsapp or "").upper())

    # MONTOS
    can.setFont("Helvetica-Bold", 12)
    can.setFillColor(colors.black)
    can.drawString(153, 215, str(evento.total or ""))
    can.drawString(278, 215, str(evento.anticipo or ""))
    can.drawString(403, 215, str(evento.restan or ""))
    can.save()

    # Combinar con plantilla
    packet.seek(0)
    overlay = PdfReader(packet)

    url = "https://drive.google.com/uc?export=download&id=1Y-WP09PuwrkBI9qWLKmiS1EsKjesu_aa"
    plantilla = PdfReader(BytesIO(requests.get(url).content))

    salida = PdfWriter()
    pagina = plantilla.pages[0]
    pagina.merge_page(overlay.pages[0])
    salida.add_page(pagina)

    output = BytesIO()
    salida.write(output)
    output.seek(0)
    return output


def generar_contrato_glitter(evento):
    """Genera el contrato tipo GLITTER"""
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    # FOLIO
    can.setFont("Helvetica-Bold", 22)
    can.setFillColor(colors.black)
    can.drawString(430, 550, str(evento.folio_manual or ""))

    # FECHA
    mes = MESES_ES[evento.fecha_evento.strftime("%B")]
    fecha_larga = f"{evento.fecha_evento.day} DE {mes} DE {evento.fecha_evento.year}"
    can.setFont("Helvetica-Bold", 12)
    can.drawString(230, 492, fecha_larga)

    # HORARIOS
    texto_horario = f"{str(evento.hora_inicio or '').upper()} - {str(evento.hora_termino or '').upper()} ({str(evento.cantidad_horas or '')})"
    can.drawString(230, 445, texto_horario)

    # SALÓN Y DIRECCIÓN
    can.drawString(230, 390, ("(" + str(evento.nombre_salon or "") + ")").upper())
    texto_completo = f"{(evento.municipio or '').upper()} - {(evento.direccion or '').upper()}"
    can.drawString(230, 372, texto_completo)

    # SERVICIOS
    texto = str(evento.servicios_interes or "").upper()
    lineas = texto.replace(',', '\n').split('\n')
    y_inicial = 325
    for i, linea in enumerate(lineas):
        can.drawString(230, y_inicial - i*10, linea.strip())
    can.drawString(390, 312, "(INCLUYE)")

    # CLIENTE
    can.setFont("Helvetica-Bold", 12)
    can.drawString(230, 267, str(evento.nombre_cliente or "").upper())
    can.drawString(230, 247, str(evento.whatsapp or "").upper())

    # MONTOS
    can.drawString(123, 163, str(evento.total or ""))
    can.drawString(248, 163, str(evento.anticipo or ""))
    can.drawString(373, 163, str(evento.restan or ""))
    can.save()

    # Combinar con plantilla
    packet.seek(0)
    overlay = PdfReader(packet)
    url = "https://drive.google.com/uc?export=download&id=17njLY9vWvS2Vhv7Q0l1aXbcY94l5p_Sh"
    plantilla = PdfReader(BytesIO(requests.get(url).content))

    salida = PdfWriter()
    pagina = plantilla.pages[0]
    pagina.merge_page(overlay.pages[0])
    salida.add_page(pagina)

    output = BytesIO()
    salida.write(output)
    output.seek(0)
    return output


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def convertir_pdf_a_png(pdf_bytes, nombre_archivo):
    """Convierte un PDF (en memoria) a imagen PNG usando PyMuPDF (sin Poppler)."""
    pdf_bytes.seek(0)
    pdf_document = fitz.open(stream=pdf_bytes.read(), filetype="pdf")
    page = pdf_document.load_page(0)
    pix = page.get_pixmap(dpi=300)
    png_bytes = BytesIO(pix.tobytes("png"))
    png_bytes.seek(0)
    nombre_png = nombre_archivo.replace(".pdf", ".png")
    return png_bytes, nombre_png


# ============================================================
# VISTA WEB (HTML CON TAILWIND)
# ============================================================

html_formulario = """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <title>Generar Contrato</title>
  <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
  <style>
    body {
      background: linear-gradient(135deg, #3b82f6, #9333ea);
      min-height: 100vh;
      display: flex;
      justify-content: center;
      align-items: center;
      font-family: 'Inter', sans-serif;
    }
    .card {
      transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .card:hover {
      transform: translateY(-4px);
      box-shadow: 0 10px 25px rgba(0,0,0,0.15);
    }
    #preview-container {
      display: none;
      margin-top: 2rem;
    }
    #preview {
      max-width: 100%;
      border-radius: 0.75rem;
      box-shadow: 0 5px 20px rgba(0,0,0,0.2);
    }
  </style>
</head>
<body>
  <div class="bg-white p-8 rounded-2xl shadow-2xl w-full max-w-lg card">
    <h1 class="text-3xl font-bold text-center text-indigo-600 mb-6">📝 Generar Contrato</h1>
    
    <form id="contrato-form" class="space-y-4">
      <div>
        <label class="font-semibold text-gray-700">Folio Manual:</label>
        <input type="text" name="folio_manual" required class="w-full mt-2 p-2 border rounded-lg focus:ring-2 focus:ring-indigo-400">
      </div>
      <div>
        <label class="font-semibold text-gray-700">Tipo de Evento:</label>
        <select name="tipo_evento" required class="w-full mt-2 p-2 border rounded-lg focus:ring-2 focus:ring-indigo-400">
          <option value="">Selecciona...</option>
          <option value="pintacaritas">🎨 Pintacaritas</option>
          <option value="glitter">✨ Glitter</option>
        </select>
      </div>
      <div>
        <label class="font-semibold text-gray-700">Formato:</label>
        <select name="formato" required class="w-full mt-2 p-2 border rounded-lg focus:ring-2 focus:ring-indigo-400">
          <option value="png">🖼️ PNG</option>
          <option value="pdf">📄 PDF</option>
        </select>
      </div>
      <button type="submit" class="w-full bg-indigo-600 text-white py-3 rounded-lg hover:bg-indigo-700 transition">Generar Contrato</button>
    </form>

    {% if mensaje %}
      <p class="mt-4 text-center text-red-600 font-semibold">{{ mensaje }}</p>
    {% endif %}

    <div id="preview-container" class="text-center">
      <h2 class="text-lg font-semibold text-gray-700 mb-3">Vista Previa:</h2>
      <img id="preview" alt="Vista previa del contrato">
      <div class="mt-4">
        <a id="download-btn" href="#" download class="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg hidden">📥 Descargar</a>
      </div>
    </div>
  </div>

  <script>
    document.getElementById('contrato-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const form = e.target;
      const formData = new FormData(form);
      const formato = formData.get('formato');
      const previewContainer = document.getElementById('preview-container');
      const preview = document.getElementById('preview');
      const downloadBtn = document.getElementById('download-btn');

      // Ocultar vista previa al comenzar
      previewContainer.style.display = 'none';
      downloadBtn.classList.add('hidden');

      const response = await fetch('/generar-contrato', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        alert('⚠️ Ocurrió un error al generar el contrato.');
        return;
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);

      if (formato === 'png') {
        // Mostrar vista previa de imagen
        preview.src = url;
        previewContainer.style.display = 'block';
        downloadBtn.href = url;
        downloadBtn.download = 'contrato.png';
        downloadBtn.classList.remove('hidden');
      } else {
        // Descargar directamente PDF
        const a = document.createElement('a');
        a.href = url;
        a.download = 'contrato.pdf';
        document.body.appendChild(a);
        a.click();
        a.remove();
      }
    });
  </script>
</body>
</html>
"""

# ============================================================
# RUTA PRINCIPAL DEL BLUEPRINT
# ============================================================

@generar_contrato_bp.route("/generar-contrato", methods=["GET", "POST"])
def generar_contrato():
    mensaje = None
    if request.method == "POST":
        folio_manual = request.form.get("folio_manual").strip().upper()
        tipo_evento = request.form.get("tipo_evento")
        formato = request.form.get("formato")

        evento = Evento.query.filter_by(folio_manual=folio_manual).first()
        if not evento:
            mensaje = f"❌ No se encontró el folio {folio_manual}"
        else:
            try:
                if tipo_evento == "pintacaritas":
                    output_pdf = generar_contrato_pintacaritas(evento)
                else:
                    output_pdf = generar_contrato_glitter(evento)

                nombre_archivo = f"{folio_manual}_{tipo_evento.upper()}_CONTRATO.pdf"

                if formato == "pdf":
                    return send_file(output_pdf, as_attachment=True, download_name=nombre_archivo, mimetype="application/pdf")

                elif formato == "png":
                    png_bytes, png_name = convertir_pdf_a_png(output_pdf, nombre_archivo)
                    return send_file(png_bytes, as_attachment=True, download_name=png_name, mimetype="image/png")

            except Exception as e:
                mensaje = f"⚠️ Error: {str(e)}"

    return render_template_string(html_formulario, mensaje=mensaje)
