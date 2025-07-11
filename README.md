# homeassistant-oesterreichs-energie-smart-meter-adapter
Das ist ein Custom Component für Home Assistant um die Live-Daten des Smart Meter Adapters (SMA) von Oesterreichs Energie (https://oesterreichsenergie.at/publikationen/ueberblick/detailseite/smart-meter-adapter) und damit die offiziell gültigen Leistungs- und Energiedaten des Hausanschlusses in Home-Assistant darzustellen.

# Hinweise
Es handelt sich um eine "alpha" Version.

# Installation
1. Der SMA muss im Heimnetzwerk eingebunden sein.
2. Die JSON API muss im Backend aktiviert sein.
3. Installation der Dateien im Home-Assistant Verzeichnis "custom_component"
4. Anpassen der folgenden Konfigurationseinstellungen:
    - IP-Adresse des SMA
    - API-Key
5. In sensors.yaml muss folgende Zeile eingefügt werden.
```
- platform: oe_energie_smart_meter
```

# Ergebnis
Es werden die 8 Werte, die die JSON API liefert als Sensoren erstellt. Zusätzlich noch eine Sensor "Nettoleistung", bei dem der Leistungsbezug aus dem Netz positiv dargestellt wird. Die Leistungseinspeisung ins Netz wird negativ dargestellt. Die Sensoren können ins Energiemanagement von HA ohne Weiteres integriert werden. Die dargestellten Karten sind nur exemplarisch.

<img width="909" height="612" alt="image" src="https://github.com/user-attachments/assets/a9b7a86c-88fa-4896-af0f-28bc53f82a52" />
