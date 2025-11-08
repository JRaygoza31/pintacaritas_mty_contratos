from extensiones import db
from datetime import datetime
from sqlalchemy.sql import func

class Evento(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Folio automático
    tipo_evento = db.Column(db.String(50), nullable=False)  # Pintacaritas / Glitter
    nombre_cliente = db.Column(db.String(100), nullable=False)
    whatsapp = db.Column(db.String(50))
    fecha_evento = db.Column(db.Date, nullable=False)
    hora_inicio = db.Column(db.String(20))
    hora_termino = db.Column(db.String(20))
    cantidad_horas = db.Column(db.Float)
    servicios_interes = db.Column(db.Text)
    municipio = db.Column(db.String(50))
    nombre_salon = db.Column(db.String(100))
    direccion = db.Column(db.String(200))
    fecha_registro = db.Column(db.DateTime, default=func.now())  # Hora que se llenó el formulario

    # Campos administrativos (no se llenan en formulario)
    folio_manual = db.Column(db.String(50))
    total = db.Column(db.Float)
    anticipo = db.Column(db.Float)
    restan = db.Column(db.Float)
    comentarios = db.Column(db.Text)
