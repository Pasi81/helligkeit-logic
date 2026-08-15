# Helligkeits-Logik für Home Assistant

Diese Integration ersetzt komplexe FHEM-Logik zur Ermittlung von:
- Sonnig
- Wolkig
- Nacht

Basierend auf:
- Zwei Helligkeitssensoren
- Sonnenstand (Elevation)
- Dynamischen Schwellenwerten
- Hysterese (Zeitverzögerungen)

## Installation über HACS

1. HACS öffnen
2. „Custom Repositories“ auswählen
3. Repository hinzufügen:
4. Kategorie: **Integration**
5. Installieren
6. Home Assistant neu starten
7. Integration hinzufügen → „Helligkeits-Logik“

## Konfiguration

- Sensor 1 (Helligkeit)
- Sensor 2 (Helligkeit)
- Sensor Elevation
- Schwellenwerte Sonne/Wolke
- Zeitverzögerungen für Hysterese

## Zusätzliche Entitäten

Die Integration erstellt zusätzlich:

- eine Berechnete Helligkeit-Entität
- separate Entitäten für Nacht, Wolkig und Sonnig
- den vorhandenen Statuswert mit Text und Übergangs-Attributen

