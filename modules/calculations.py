import math

def calculate_advanced_metrics(rz, xc, height_cm, weight_kg, age, gender):
    """
    MOTORE AREA199 - VERSIONE CLINICA CORRETTA (Sergi Formula H in cm)
    """
    if rz <= 0 or height_cm <= 0 or weight_kg <= 0:
        return {k: 0 for k in ["PhA", "TBW_L", "ECW_L", "ICW_L", "BCM_kg", "FM_perc", "FFM_kg"]}

    h_m = height_cm / 100.0
    bmi = weight_kg / (h_m ** 2)
    
    # DATI VETTORIALI
    if rz != 0: pha = math.degrees(math.atan(xc / rz))
    else: pha = 0.0
    
    # VARIABILE CHIAVE (H in CM)
    h2_rz = (height_cm ** 2) / rz

    # COMPARTIMENTI IDRICI (TBW Sun / ECW Sergi Corretta)
    if gender == "M":
        tbw = 1.2 + (0.45 * h2_rz) + (0.18 * weight_kg)
        ecw = 0.065 * h2_rz + 0.177 * weight_kg - 2.5 # Formula Sergi (H cm)
        ffm = -10.68 + (0.65 * h2_rz) + (0.26 * weight_kg) + (0.02 * rz)
    else:
        tbw = 3.75 + (0.45 * h2_rz) + (0.11 * weight_kg)
        ecw = 0.065 * h2_rz + 0.150 * weight_kg - 1.8
        ffm = -9.53 + (0.69 * h2_rz) + (0.17 * weight_kg) + (0.02 * rz)

    # SAFETY CHECK ACQUA
    if tbw > 0:
        if ecw < tbw * 0.30: ecw = tbw * 0.35 # Minimo fisiologico
        if ecw > tbw * 0.55: ecw = tbw * 0.50 # Massimo fisiologico

    icw = tbw - ecw
    
    # COMPARTIMENTI MASSA
    if ffm > weight_kg * 0.98: ffm = weight_kg * 0.98
    fm = weight_kg - ffm
    if fm < 0: fm = 0
    
    fm_perc = (fm / weight_kg) * 100
    ffm_perc = (ffm / weight_kg) * 100

    # SMM (Muscolo)
    sex_val = 1 if gender == "M" else 0
    smm = (0.401 * h2_rz) + (3.825 * sex_val) - (0.071 * age) + 5.102
    
    # BCM (Massa Cellulare)
    bcm_coeff = 0.50 + (0.02 * (pha - 5.0))
    bcm = ffm * bcm_coeff

    # BMR
    bmr = 500 + (22 * ffm)

    return {
        "Rz": rz, "Xc": xc, "PhA": round(pha, 2), "BMI": round(bmi, 1),
        "FFM_kg": round(ffm, 1), "FFM_perc": round(ffm_perc, 1),
        "FM_kg": round(fm, 1), "FM_perc": round(fm_perc, 1),
        "BCM_kg": round(bcm, 1), "SMM_kg": round(smm, 1),
        "TBW_L": round(tbw, 1), "TBW_perc": round((tbw/weight_kg)*100, 1),
        "ECW_L": round(ecw, 1), "ICW_L": round(icw, 1),
        "BMR_kcal": int(bmr)
    }
