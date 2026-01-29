from fpdf import FPDF
import datetime
import os

class BivaReportPDF(FPDF):
    def __init__(self, patient_name):
        super().__init__()
        self.patient_name = patient_name
        self.set_auto_page_break(auto=True, margin=35)
        self.add_page()
        
    def sanitize(self, text):
        if not isinstance(text, str): return str(text)
        return text.encode('latin-1', 'replace').decode('latin-1').replace('?', '')

    def header(self):
        if os.path.exists("logo_area199.png"):
            self.image("logo_area199.png", 10, 8, 40)
        elif os.path.exists("logo_dark.jpg"):
            self.image("logo_dark.jpg", 10, 8, 40)
        
        self.set_font('Arial', 'B', 10)
        self.set_text_color(50)
        self.set_xy(120, 10)
        self.cell(80, 5, 'AREA199 | PERFORMANCE LAB', 0, 1, 'R')
        self.set_font('Arial', '', 8)
        self.set_xy(120, 15)
        self.cell(80, 5, 'Dott. Antonio Petruzzi - Performance Specialist', 0, 1, 'R')
        self.ln(25)
        
        self.set_font('Arial', 'B', 16)
        self.set_text_color(0)
        self.cell(110, 8, self.sanitize(self.patient_name), 0, 0, 'L')
        self.set_font('Arial', '', 10)
        self.cell(80, 8, f"Data: {datetime.datetime.now().strftime('%d/%m/%Y')}", 0, 1, 'R')
        self.set_draw_color(226, 6, 19)
        self.set_line_width(0.4)
        self.line(10, 45, 200, 45)
        self.ln(5)

    def footer(self):
        if os.path.exists("logo_akern.png"):
            self.image("logo_akern.png", 160, 270, 25)
        self.set_y(-15)
        self.set_font('Arial', '', 7)
        self.set_text_color(150)
        self.cell(0, 10, f'AREA199 Performance Lab - Pagina {self.page_no()}', 0, 0, 'C')

    def section_title(self, title):
        self.ln(5)
        self.set_font('Arial', 'B', 11)
        self.set_fill_color(245)
        self.set_text_color(226, 6, 19)
        self.cell(0, 8, f"  {self.sanitize(title)}", 0, 1, 'L', fill=True)
        self.ln(3)

    def kpi_grid(self, data, prev_data=None):
        self.set_font('Arial', '', 9)
        self.set_text_color(0)
        self.set_draw_color(220)
        
        self.set_font('Arial', 'B', 8)
        self.set_fill_color(250)
        self.cell(50, 6, "PARAMETRO", 1, 0, 'L', True)
        self.cell(40, 6, "VALORE ATTUALE", 1, 0, 'C', True)
        
        date_prev = prev_data.get('Date', 'N/D') if prev_data else "N/D"
        self.cell(40, 6, f"PREC. ({date_prev})", 1, 0, 'C', True)
        self.cell(30, 6, "VARIAZIONE", 1, 1, 'C', True)

        def add_row(label, val_curr, unit, key_prev=None, data_key=None):
            self.set_font('Arial', '', 9)
            self.cell(50, 7, label, 1)
            self.set_font('Arial', 'B', 9)
            
            # Valore attuale
            val_c = data.get(data_key, val_curr) if data_key else val_curr
            self.cell(40, 7, f"{val_c} {unit}", 1, 0, 'C')
            
            # Storico
            if prev_data and key_prev and key_prev in prev_data:
                try:
                    val_prev = float(prev_data[key_prev])
                    val_curr_float = float(val_c)
                    delta = val_curr_float - val_prev
                    sign = "+" if delta > 0 else ""
                    self.set_font('Arial', '', 9)
                    self.cell(40, 7, f"{val_prev} {unit}", 1, 0, 'C')
                    self.set_font('Arial', 'B', 9)
                    self.set_text_color(0, 100, 0) if delta > 0 else self.set_text_color(150, 0, 0)
                    self.cell(30, 7, f"{sign}{delta:.1f}", 1, 1, 'C')
                    self.set_text_color(0)
                except:
                    self.cell(70, 7, "-", 1, 1, 'C')
            else:
                self.cell(70, 7, "-", 1, 1, 'C')

        # TUTTE LE RIGHE RICHIESTE
        add_row("Peso Corporeo", data.get('Weight', 0), "kg", 'Peso', 'Weight')
        add_row("Resistenza (Rz)", data.get('Rz', 0), "ohm", 'Rz', 'Rz')
        add_row("Reattanza (Xc)", data.get('Xc', 0), "ohm", 'Xc', 'Xc')
        add_row("Angolo di Fase (PhA)", data['PhA'], "deg", 'PhA')
        add_row("Idratazione (TBW)", data['TBW_L'], "L", 'TBW_L')
        add_row("Body Fat (BF%)", data['FM_perc'], "%", 'FM_perc')
        add_row("Massa Magra (FFM)", data['FFM_kg'], "kg", 'FFM_kg')
        add_row("Cellule (BCM)", data['BCM_kg'], "kg", 'BCM_kg')
        
        self.ln(5)

    def generate_body(self, data, graph1_path=None, graph2_path=None, body_map_path=None, previous_data=None):
        self.section_title("DATI BIOMETRICI")
        self.kpi_grid(data, previous_data)
        
        self.section_title("ANALISI STRUMENTALE")
        y = self.get_y()
        if graph1_path: self.image(graph1_path, x=10, y=y, w=60)
        if graph2_path: self.image(graph2_path, x=75, y=y, w=60)
        if body_map_path: self.image(body_map_path, x=140, y=y, w=50)
        
        self.ln(65)
        self.add_page()
        
        self.section_title("RELAZIONE TECNICA & STRATEGIA")
        self.ln(5)
        self.set_font('Arial', '', 10)
        self.set_text_color(0)
        
        text = data.get('Report_Text', '')
        self.multi_cell(0, 5, self.sanitize(text))
