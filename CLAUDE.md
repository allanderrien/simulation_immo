# Simulation Immobilière — Notes pour Claude

## Ce que fait ce projet
App Streamlit locale : simulation achat résidence principale vs location + stratégie d'investissement.
Repo : https://github.com/allanderrien/simulation_immo

## Lancement
```
streamlit run app.py
# ou double-clic lancer.bat
```

## Architecture
- `simulation.py` — modèle financier pur (pas de Streamlit)
- `charts.py` — fonctions Plotly, pas d'état
- `app.py` — UI Streamlit, appelle les deux modules ci-dessus

## Règles de calcul à ne jamais déroger

**Taux mensuels effectifs** — toujours `(1 + taux_annuel)^(1/12) - 1`, jamais `taux/12`.

**Patrimoine achat** = `equity + portfolio_net` où `equity = bien_value - capital_restant_dû`.
Ne jamais compter `bien_value` en entier — la dette bancaire doit être soustraite.

**Flat tax PFU 30%** appliquée à la liquidation finale uniquement (buy-and-hold).
Cost basis suivi par méthode proportionnelle lors des retraits.

**Plus-value résidence principale** : exonérée d'impôt (CGI art. 150 U II 1°).

**Frais d'agence et de notaire** : finançables par la banque.
Apport minimum = 10% du coût total (bien + frais).

**Inflation** : affecte loyer, charges, budget mensuel. La mensualité de crédit reste fixe.

## Comportement UI
- Le toggle "euros constants" doit être défini AVANT les KPIs — il conditionne la colonne utilisée.
- Pas de break-even (supprimé à la demande).
- Tooltips pédagogiques sur tous les paramètres sidebar.

## Priorité absolue
L'utilisateur vérifie les résultats contre ses propres tableaux.
Zéro approximation tolérée.
