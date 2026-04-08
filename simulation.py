"""
Modèle financier — Simulation Achat vs Location + Stratégie
Tous les calculs sont exacts (pas d'approximations).
"""

from dataclasses import dataclass
import pandas as pd
import numpy as np


@dataclass
class Params:
    # Bien immobilier
    valeur_bien: float = 250_000.0
    frais_agence: float = 7_500.0
    frais_notaire: float = 20_000.0

    # Financement
    apport: float = 27_500.0
    taux_credit: float = 0.035        # taux annuel nominal
    duree_credit: int = 20            # ans
    taux_assurance: float = 0.0010    # %/an sur capital restant dû

    # Location
    loyer: float = 1_100.0            # €/mois (hors charges)

    # Charges propriétaire (annuelles)
    impots_fonciers: float = 1_000.0
    charges_diverses: float = 2_000.0

    # Budget & capital
    budget_mensuel: float = 2_500.0   # budget alloué logement + investissement
    capital_depart: float = 129_000.0

    # Rendements & macro
    rendement_strategie: float = 0.07
    appreciation_immo: float = 0.025
    inflation: float = 0.02

    # Simulation
    horizon_ans: int = 20
    annee_depart: int = 2025

    # Fiscalité (constantes légales France)
    flat_tax: float = 0.30            # PFU : 12.8% IR + 17.2% PS


# ─────────────────────────────────────────────────────────────────────────────
# Formules utilitaires
# ─────────────────────────────────────────────────────────────────────────────

def mensualite_credit(capital: float, taux_annuel: float, duree_ans: int) -> float:
    """Mensualité exacte à annuités constantes (formule fermée)."""
    r = taux_annuel / 12
    n = duree_ans * 12
    if r == 0:
        return capital / n
    return capital * r / (1.0 - (1.0 + r) ** (-n))


def max_valeur_bien(params: Params) -> float:
    """
    Prix maximum du bien tel que le coût mensuel initial ≤ budget_mensuel.
    Résolution exacte de : M(C) + assurance(C) + charges ≤ budget
    où C = capital emprunté = bien + frais - apport.
    """
    p = params
    charges_m = (p.impots_fonciers + p.charges_diverses) / 12.0
    budget_dispo = p.budget_mensuel - charges_m
    if budget_dispo <= 0:
        return 0.0
    r = p.taux_credit / 12.0
    n = p.duree_credit * 12
    if r == 0:
        coeff = 1.0 / n + p.taux_assurance / 12.0
    else:
        coeff = r / (1.0 - (1.0 + r) ** (-n)) + p.taux_assurance / 12.0
    capital_max = budget_dispo / coeff
    return max(0.0, capital_max + p.apport - p.frais_agence - p.frais_notaire)


# ─────────────────────────────────────────────────────────────────────────────
# Mise à jour du portefeuille avec suivi du cost basis (pour flat tax)
# ─────────────────────────────────────────────────────────────────────────────

def _update_portfolio(portfolio: float, cost_basis: float,
                      monthly_return: float, delta: float) -> tuple[float, float]:
    """
    Fait croître le portefeuille d'un mois, puis applique le delta (investissement ou retrait).
    Méthode proportionnelle pour le cost basis (PFU France).

    Retourne (portfolio, cost_basis) mis à jour.
    """
    # Croissance mensuelle
    portfolio *= (1.0 + monthly_return)

    if delta >= 0:
        portfolio += delta
        cost_basis += delta
    else:
        withdrawal = min(abs(delta), portfolio)
        if portfolio > 1e-6:
            # Réduction proportionnelle du cost basis
            cost_basis *= (portfolio - withdrawal) / portfolio
        portfolio = max(0.0, portfolio - withdrawal)

    return portfolio, cost_basis


def _portfolio_net_flat_tax(portfolio: float, cost_basis: float, flat_tax: float) -> tuple[float, float]:
    """Calcule le portfolio net de flat tax à la liquidation."""
    gain = max(0.0, portfolio - cost_basis)
    tax = gain * flat_tax
    return portfolio - tax, tax


# ─────────────────────────────────────────────────────────────────────────────
# Simulation principale
# ─────────────────────────────────────────────────────────────────────────────

def simulate(params: Params) -> dict:
    """
    Simule les deux scénarios mois par mois sur l'horizon défini.
    Retourne un dict avec DataFrames annuels et métriques clés.
    """
    p = params
    n_total = p.horizon_ans * 12
    n_credit = p.duree_credit * 12

    capital_emprunt = p.valeur_bien + p.frais_agence + p.frais_notaire - p.apport
    M = mensualite_credit(capital_emprunt, p.taux_credit, p.duree_credit)
    r_m = p.taux_credit / 12.0

    # Taux mensuels effectifs (préservent exactement le taux annuel déclaré)
    ret_m = (1.0 + p.rendement_strategie) ** (1.0 / 12.0) - 1.0
    app_m = (1.0 + p.appreciation_immo) ** (1.0 / 12.0) - 1.0
    inf_m = (1.0 + p.inflation) ** (1.0 / 12.0) - 1.0

    charges_m0 = (p.impots_fonciers + p.charges_diverses) / 12.0
    assurance_m0 = p.taux_assurance * capital_emprunt / 12.0
    cout_initial = M + assurance_m0 + charges_m0
    viable = cout_initial <= p.budget_mensuel

    # ── SCÉNARIO A : ACHAT ────────────────────────────────────────────────

    pf_A = float(p.capital_depart - p.apport)
    cb_A = pf_A
    cap_restant = float(capital_emprunt)
    bien_val = float(p.valeur_bien)

    cum_interets = 0.0
    cum_assurance = 0.0
    cum_cout_A = 0.0
    rows_A = []

    for m in range(1, n_total + 1):
        yr_idx = (m - 1) // 12

        # Inflation cumulée à ce mois
        inf_factor = (1.0 + p.inflation) ** (m / 12.0)
        budget_nom = p.budget_mensuel * inf_factor
        charges_m = charges_m0 * inf_factor

        # Crédit
        if m <= n_credit and cap_restant > 0.01:
            interets_m = cap_restant * r_m
            principal_m = M - interets_m
            assurance_m = p.taux_assurance * cap_restant / 12.0
            cap_restant = max(0.0, cap_restant - principal_m)
            cout_m = M + assurance_m + charges_m
            cum_interets += interets_m
            cum_assurance += assurance_m
        else:
            interets_m = principal_m = assurance_m = 0.0
            cout_m = charges_m

        cum_cout_A += cout_m
        delta = budget_nom - cout_m

        pf_A, cb_A = _update_portfolio(pf_A, cb_A, ret_m, delta)
        bien_val *= (1.0 + app_m)

        if m % 12 == 0:
            pf_net, tax_A = _portfolio_net_flat_tax(pf_A, cb_A, p.flat_tax)
            # Patrimoine réel = equity (valeur bien MOINS dette restante) + portefeuille
            # Au début du crédit l'essentiel du bien appartient encore à la banque
            equity = bien_val - cap_restant
            patrimoine_nom = equity + pf_net
            deflator = (1.0 + p.inflation) ** (yr_idx + 1)

            rows_A.append({
                "annee":                 p.annee_depart + yr_idx + 1,
                "yr":                    yr_idx + 1,
                "bien_value":            bien_val,
                "cap_restant_du":        cap_restant,
                "equity_immo":           equity,
                "portfolio_brut":        pf_A,
                "flat_tax":              tax_A,
                "portfolio_net":         pf_net,
                "patrimoine_net_nominal": patrimoine_nom,
                "patrimoine_net_reel":   patrimoine_nom / deflator,
                "cum_interets":          cum_interets,
                "cum_assurance":         cum_assurance,
                "cout_mensuel":          cout_m,
                "cum_cout":              cum_cout_A,
                "delta_mensuel":         delta,
                "total_investi":         cb_A,
            })

    # ── SCÉNARIO B : LOCATION ─────────────────────────────────────────────

    pf_B = float(p.capital_depart)
    cb_B = pf_B
    cum_cout_B = 0.0
    rows_B = []

    for m in range(1, n_total + 1):
        yr_idx = (m - 1) // 12

        inf_factor = (1.0 + p.inflation) ** (m / 12.0)
        loyer_nom = p.loyer * inf_factor
        budget_nom = p.budget_mensuel * inf_factor
        delta = budget_nom - loyer_nom
        cum_cout_B += loyer_nom

        pf_B, cb_B = _update_portfolio(pf_B, cb_B, ret_m, delta)

        if m % 12 == 0:
            pf_net, tax_B = _portfolio_net_flat_tax(pf_B, cb_B, p.flat_tax)
            deflator = (1.0 + p.inflation) ** (yr_idx + 1)

            rows_B.append({
                "annee":                 p.annee_depart + yr_idx + 1,
                "yr":                    yr_idx + 1,
                "portfolio_brut":        pf_B,
                "flat_tax":              tax_B,
                "portfolio_net":         pf_net,
                "patrimoine_net_nominal": pf_net,
                "patrimoine_net_reel":   pf_net / deflator,
                "loyer_nominal":         loyer_nom,
                "cum_cout":              cum_cout_B,
                "delta_mensuel":         delta,
                "total_investi":         cb_B,
            })

    df_A = pd.DataFrame(rows_A)
    df_B = pd.DataFrame(rows_B)

    return {
        "achat":            df_A,
        "location":         df_B,
        "viable":           viable,
        "cout_initial":     cout_initial,
        "mensualite":       M,
        "assurance_init":   assurance_m0,
        "charges_init":     charges_m0,
        "capital_emprunt":  capital_emprunt,
        "max_bien":         max_valeur_bien(p),
    }
