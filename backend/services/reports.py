"""
services/reports.py - Generación de reportes PDF
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
import logging
from io import BytesIO

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generador de reportes en PDF"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
    
    def generate_detection_report(self, data: dict, output_path: str = None) -> BytesIO:
        """
        Generar reporte de detecciones
        
        Args:
            data: Dict con datos de detecciones
            output_path: Ruta para guardar (opcional)
            
        Returns:
            BytesIO con PDF generado
        """
        try:
            # Crear buffer
            buffer = BytesIO()
            
            # Crear documento PDF
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                topMargin=0.5*inch,
                bottomMargin=0.5*inch,
                leftMargin=0.75*inch,
                rightMargin=0.75*inch
            )
            
            # Elementos del PDF
            elements = []
            
            # Título
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=self.styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=30,
                alignment=1  # Center
            )
            
            title = Paragraph("REPORTE DE DETECCIONES - SISTEMA DE VIGILANCIA", title_style)
            elements.append(title)
            
            # Fecha
            fecha_texto = f"Generado: {datetime.utcnow().strftime('%d/%m/%Y %H:%M:%S')}"
            fecha = Paragraph(f"<b>{fecha_texto}</b>", self.styles['Normal'])
            elements.append(fecha)
            elements.append(Spacer(1, 0.3*inch))
            
            # Resumen
            summary_title = Paragraph("<b>RESUMEN GENERAL</b>", self.styles['Heading2'])
            elements.append(summary_title)
            
            summary_data = [
                ['Métrica', 'Cantidad'],
                ['Total Detecciones', str(data.get('total_detecciones', 0))],
                ['Personas Detectadas', str(data.get('total_personas', 0))],
                ['Vehículos Detectados', str(data.get('total_vehiculos', 0))],
                ['Cámaras Activas', str(data.get('camaras_activas', 0))]
            ]
            
            summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2196F3')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(summary_table)
            elements.append(Spacer(1, 0.3*inch))
            
            # Detalle de personas
            if data.get('personas', []):
                elements.append(PageBreak())
                personas_title = Paragraph("<b>PERSONAS DETECTADAS</b>", self.styles['Heading2'])
                elements.append(personas_title)
                
                personas_data = [['ID', 'Confianza', 'Detecciones', 'Última Vez']]
                for p in data['personas'][:20]:  # Máximo 20
                    personas_data.append([
                        str(p.get('id', 'N/A')),
                        f"{p.get('confidence', 0):.2f}",
                        str(p.get('times_detected', 0)),
                        p.get('detected_at', 'N/A')
                    ])
                
                personas_table = Table(personas_data, colWidths=[0.8*inch, 1.5*inch, 1.5*inch, 1.5*inch])
                personas_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey)
                ]))
                elements.append(personas_table)
            
            # Detalle de vehículos
            if data.get('vehiculos', []):
                elements.append(Spacer(1, 0.3*inch))
                vehiculos_title = Paragraph("<b>VEHÍCULOS DETECTADOS</b>", self.styles['Heading2'])
                elements.append(vehiculos_title)
                
                vehiculos_data = [['Placa', 'Modelo', 'Color', 'Confianza', 'Detecciones']]
                for v in data['vehiculos'][:20]:  # Máximo 20
                    vehiculos_data.append([
                        v.get('license_plate', 'NO DETECTADA'),
                        v.get('vehicle_model', 'N/A')[:20],
                        v.get('vehicle_color', 'N/A')[:15],
                        f"{v.get('confidence', 0):.2f}",
                        str(v.get('times_detected', 0))
                    ])
                
                vehiculos_table = Table(vehiculos_data, colWidths=[1.2*inch, 1.5*inch, 1*inch, 1*inch, 1*inch])
                vehiculos_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF9800')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey)
                ]))
                elements.append(vehiculos_table)
            
            # Footer
            elements.append(Spacer(1, 0.5*inch))
            footer = Paragraph(
                "<i>Este reporte fue generado automáticamente por el Sistema de Vigilancia Inteligente</i>",
                self.styles['Normal']
            )
            elements.append(footer)
            
            # Construir PDF
            doc.build(elements)
            buffer.seek(0)
            
            logger.info(" Reporte PDF generado exitosamente")
            
            # Guardar si se proporciona ruta
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(buffer.getvalue())
                logger.info(f"Reporte guardado en: {output_path}")
            
            return buffer
            
        except Exception as e:
            logger.error(f"Error generando reporte: {e}")
            raise


# Instancia global
report_generator = ReportGenerator()


def get_report_generator() -> ReportGenerator:
    """Obtener instancia del generador de reportes"""
    return report_generator
