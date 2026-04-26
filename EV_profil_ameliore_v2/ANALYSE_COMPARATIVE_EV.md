# Analyse comparative — Ancien vs Nouveau profil EV

## Résumé des différences

L'ancien profil avait son pic à 02h du matin — complètement irréaliste.
Le nouveau profil a son pic à 18h-19h — le retour du travail où tout le monde
branche sa voiture en même temps.

À 07h et 17h la valeur est 0 — la voiture est sur la route, elle ne peut pas charger.
La journée au bureau (09h-17h) montre une charge modérée via les bornes de travail
et fast charging.

Ces résultats sont cohérents avec le graphique EV_Charging_Profile.png fourni.

---

## Tableau de comparaison heure par heure

| Heure | Ancien profil | Nouveau profil | Puissance brute | Commentaire |
|-------|--------------|----------------|-----------------|-------------|
| 00h   | 0.80         | 0.3730         | 3.99 kW         | Charge domicile nuit |
| 01h   | 0.90         | 0.3730         | 3.99 kW         | Charge domicile nuit |
| 02h   | **1.00**     | 0.3730         | 3.99 kW         | Ancien pic ← irréaliste |
| 03h   | 0.95         | 0.3730         | 3.99 kW         | Charge domicile nuit |
| 04h   | 0.70         | 0.3730         | 3.99 kW         | Charge domicile nuit |
| 05h   | 0.40         | 0.3730         | 3.99 kW         | Charge domicile nuit |
| 06h   | 0.20         | 0.3730         | 3.99 kW         | Charge domicile nuit |
| 07h   | 0.10         | **0.0000**     | 0.00 kW         | Trajet matin — voiture indisponible |
| 08h   | 0.10         | **0.0000**     | 0.00 kW         | Pas encore branché au travail |
| 09h   | 0.10         | 0.1235         | 1.32 kW         | Borne travail active |
| 10h   | 0.15         | 0.1750         | 1.87 kW         | Travail + public elsewhere |
| 11h   | 0.20         | 0.1750         | 1.87 kW         | Travail + public elsewhere |
| 12h   | 0.20         | 0.5961         | 6.37 kW         | Travail + fast charging actif |
| 13h   | 0.20         | 0.5961         | 6.37 kW         | Travail + fast charging |
| 14h   | 0.15         | 0.5961         | 6.37 kW         | Travail + fast charging |
| 15h   | 0.10         | 0.5961         | 6.37 kW         | Travail + fast charging |
| 16h   | 0.15         | 0.5961         | 6.37 kW         | Travail + fast charging |
| 17h   | 0.30         | **0.0000**     | 0.00 kW         | Trajet soir — voiture indisponible |
| 18h   | 0.50         | **1.0000**     | 10.69 kW        | PIC — retour + tous canaux domicile |
| 19h   | 0.60         | **1.0000**     | 10.69 kW        | PIC — retour + tous canaux domicile |
| 20h   | 0.70         | 0.5274         | 5.64 kW         | Domicile + public near home termine |
| 21h   | 0.75         | 0.5274         | 5.64 kW         | Charge domicile |
| 22h   | 0.80         | 0.5274         | 5.64 kW         | Charge domicile |
| 23h   | 0.85         | 0.3730         | 3.99 kW         | Charge domicile nuit |

---

## Points clés

- Pic ancien profil : 02h du matin (valeur 1.00) — aucune justification physique
- Pic nouveau profil : 18h-19h (valeur 1.00, 10.69 kW brut) — retour du travail
- Heures à zéro : 07h et 17h — voiture en déplacement, charge impossible
- Puissance max réelle : 10.69 kW (home private + home socket + public near home actifs simultanément)

---

## Canaux actifs à 18h (heure du pic)

| Canal | Puissance | Part énergie | Contribution |
|-------|-----------|--------------|--------------|
| Home private | 7.4 kW | 52% | 3.85 kW |
| Home socket | 2.3 kW | 6% | 0.14 kW |
| Public near home | 11 kW | 15% | 1.65 kW |
| **Total** | | | **~10.69 kW** |

---

Équipe QA — Miriam Dahim
ISEP Project 2026 — Sprint 3
