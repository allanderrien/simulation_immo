"""
Simulation Investissement Immobilier — Application Streamlit
Achat résidence principale vs Location + Stratégie d'investissement
"""

import streamlit as st
from datetime import date

from simulation import Params, simulate, max_valeur_bien, mensualite_credit
from charts import (
    chart_patrimoine,
    chart_mensualites,
    chart_couts_cumules,
    chart_amortissement,
    chart_portefeuille,
)

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Simulation Immo",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.kpi-card {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 18px 20px 14px 20px;
    text-align: center;
}
.kpi-label {
    font-size: 0.72rem;
    color: #64748B;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.kpi-value {
    font-size: 1.55rem;
    font-weight: 700;
    color: #1E293B;
    margin: 4px 0 2px 0;
}
.kpi-sub {
    font-size: 0.72rem;
    color: #94A3B8;
}
.ok-banner {
    background: #F0FDF4;
    border: 1px solid #86EFAC;
    border-radius: 8px;
    padding: 10px 16px;
    margin-bottom: 12px;
    font-size: 0.9rem;
    color: #166534;
}
.warn-banner {
    background: #FFFBEB;
    border: 1px solid #FCD34D;
    border-radius: 8px;
    padding: 10px 16px;
    margin-bottom: 12px;
    font-size: 0.9rem;
    color: #92400E;
}
.section-title {
    font-size: 0.8rem;
    font-weight: 600;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 6px;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar — Paramètres
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("Paramètres")

    # ── Bien ──────────────────────────────────────────────────────────────
    with st.expander("🏠 Bien immobilier", expanded=True):
        valeur_bien = st.number_input(
            "Valeur du bien (€)", min_value=10_000, value=250_000, step=5_000,
            help="Prix net vendeur. Les frais d'agence et de notaire sont saisis séparément ci-dessous.",
        )
        frais_agence = st.number_input(
            "Frais d'agence (€)", min_value=0, value=7_500, step=500,
            help="Honoraires de l'agence immobilière. Finançables par la banque.",
        )
        frais_notaire = st.number_input(
            "Frais de notaire (€)", min_value=0, value=20_000, step=500,
            help=(
                "Comprend les droits de mutation (~5.8 % dans l'ancien), les émoluments du notaire "
                "et les débours. En pratique : ~7-8 % du prix dans l'ancien, ~3-4 % dans le neuf. "
                "Finançables par la banque."
            ),
        )
        appreciation_immo = st.slider(
            "Appréciation immo (%/an)", 0.0, 8.0, 2.5, 0.1,
            format="%.1f%%",
            help=(
                "Hausse annuelle estimée de la valeur du bien. En France, la moyenne long terme "
                "est d'environ 1.5–3 %/an selon les zones. Paramètre très sensible sur longue durée."
            ),
        ) / 100.0

    # ── Financement ───────────────────────────────────────────────────────
    with st.expander("💳 Financement", expanded=True):
        capital_depart = st.number_input(
            "Capital de départ (€)", min_value=0, value=129_000, step=1_000,
            help=(
                "Épargne totale disponible. Sera répartie entre **apport immobilier** "
                "et **portefeuille stratégie** (investi dès J0)."
            ),
        )
        # Apport minimum bancaire : ~10 % du coût total (bien + frais)
        total_cout = valeur_bien + frais_agence + frais_notaire
        apport_min = int(total_cout * 0.10)
        apport_max = int(capital_depart)
        apport_default = max(apport_min, min(apport_min, apport_max))

        if apport_min > capital_depart:
            st.warning(
                f"⚠️ Le capital de départ ({capital_depart:,.0f} €) est inférieur au minimum "
                f"bancaire estimé ({apport_min:,.0f} €, soit 10 % du coût total)."
            )
            apport = apport_max
        else:
            apport = st.slider(
                "Apport (€)",
                min_value=apport_min,
                max_value=apport_max,
                value=apport_default,
                step=1_000,
                format="%d €",
                help=(
                    f"**Minimum affiché : {apport_min:,.0f} €** (~10 % du coût total). "
                    "Les banques exigent généralement 10–20 % d'apport personnel. "
                    "Plus l'apport est élevé, moins vous empruntez, mais moins de capital "
                    "reste investi dans la stratégie dès le départ."
                ),
            )
        capital_strategie = capital_depart - apport
        st.caption(f"Capital conservé en stratégie dès J0 : **{capital_strategie:,.0f} €**")

        taux_credit = st.slider(
            "Taux crédit (%/an)", 0.5, 8.0, 3.5, 0.05,
            format="%.2f%%",
            help=(
                "Taux annuel nominal hors assurance (TANN). "
                "Taux moyens constatés en France en 2025 : ~3.0–4.5 % selon durée et profil."
            ),
        ) / 100.0
        duree_credit = st.slider(
            "Durée crédit (ans)", 5, 30, 20,
            help=(
                "Durée du prêt en années. Plus la durée est longue, plus la mensualité est "
                "faible mais plus les intérêts totaux sont élevés. Maximum légal en France : 25 ans "
                "(27 ans avec différé dans certains cas — HCSF 2021)."
            ),
        )
        taux_assurance = st.slider(
            "Assurance emprunteur (%/an)", 0.05, 0.80, 0.10, 0.01,
            format="%.2f%%",
            help=(
                "Calculée chaque mois sur le **capital restant dû** (méthode exacte). "
                "Taux moyen : 0.10–0.25 % pour un profil standard < 40 ans. "
                "Peut monter à 0.5 %+ selon âge et état de santé. "
                "Depuis la loi Lemoine (2022), libre choix de l'assureur dès la souscription."
            ),
        ) / 100.0

    # ── Location & Budget ─────────────────────────────────────────────────
    with st.expander("🏡 Location & Budget", expanded=True):
        loyer = st.number_input(
            "Loyer équivalent (€/mois)", min_value=100, value=1_100, step=50,
            help=(
                "Loyer mensuel d'un bien comparable (hors charges). "
                "Revalorisé chaque année selon l'inflation dans la simulation, "
                "à l'image de l'Indice de Référence des Loyers (IRL)."
            ),
        )
        budget_mensuel = st.number_input(
            "Budget mensuel alloué (€/mois)", min_value=100, value=2_500, step=100,
            help=(
                "Montant mensuel disponible pour **logement + investissement**. "
                "Ce qui n'est pas consommé par le logement est automatiquement investi "
                "dans la stratégie. Revalorisé avec l'inflation (pouvoir d'achat constant)."
            ),
        )

    # ── Charges proprio ───────────────────────────────────────────────────
    with st.expander("🔧 Charges propriétaire", expanded=False):
        impots_fonciers = st.number_input(
            "Taxe foncière (€/an)", min_value=0, value=1_000, step=100,
            help=(
                "Impôt local annuel dû par tout propriétaire, quel que soit l'usage du bien. "
                "Revalorisée chaque année avec l'inflation dans la simulation."
            ),
        )
        charges_diverses = st.number_input(
            "Charges diverses (€/an)", min_value=0, value=2_000, step=100,
            help=(
                "Charges de copropriété (non récupérables sur locataire), entretien courant, "
                "assurance habitation propriétaire. Revalorisation annuelle avec l'inflation."
            ),
        )

    # ── Stratégie & Macro ─────────────────────────────────────────────────
    with st.expander("📈 Stratégie & Macro-économie", expanded=True):
        rendement_strategie = st.slider(
            "Rendement stratégie (%/an)", 1.0, 30.0, 7.0, 0.5,
            format="%.1f%%",
            help=(
                "Rendement annuel **brut** de la stratégie d'investissement (ETF, portefeuille, etc.). "
                "Historique MSCI World dividendes réinvestis : ~9 %/an sur 30 ans. "
                "La flat tax de 30 % est appliquée sur les gains **à la liquidation finale** "
                "(simulation d'un portefeuille buy-and-hold)."
            ),
        ) / 100.0
        inflation = st.slider(
            "Inflation (%/an)", 0.0, 6.0, 2.0, 0.1,
            format="%.1f%%",
            help=(
                "Taux d'inflation annuel. Impact dans la simulation :\n"
                "- Loyer revalorisé chaque année (IRL ≈ inflation)\n"
                "- Charges propriétaire revalorisées\n"
                "- Budget mensuel revalorisé (pouvoir d'achat maintenu)\n"
                "- **Mensualité de crédit fixe** (avantage de l'endettement à taux fixe)\n"
                "Objectif BCE : 2 %/an. Inflation France 2024 : ~2.3 %."
            ),
        ) / 100.0

    # ── Horizon ───────────────────────────────────────────────────────────
    with st.expander("📅 Horizon de simulation", expanded=True):
        horizon_ans = st.slider("Horizon (ans)", 5, 40, 20)
        annee_depart = st.number_input(
            "Année d'achat", min_value=2020, max_value=2050,
            value=date.today().year, step=1,
            help="Année de l'achat (ou du début de la location). "
                 "Les axes des graphes affichent les années réelles.",
        )

# ─────────────────────────────────────────────────────────────────────────────
# Simulation
# ─────────────────────────────────────────────────────────────────────────────

params = Params(
    valeur_bien=float(valeur_bien),
    frais_agence=float(frais_agence),
    frais_notaire=float(frais_notaire),
    apport=float(apport),
    taux_credit=taux_credit,
    duree_credit=int(duree_credit),
    taux_assurance=taux_assurance,
    loyer=float(loyer),
    impots_fonciers=float(impots_fonciers),
    charges_diverses=float(charges_diverses),
    budget_mensuel=float(budget_mensuel),
    capital_depart=float(capital_depart),
    rendement_strategie=rendement_strategie,
    appreciation_immo=appreciation_immo,
    inflation=inflation,
    horizon_ans=int(horizon_ans),
    annee_depart=int(annee_depart),
)

res = simulate(params)
df_A = res["achat"]
df_B = res["location"]

# ─────────────────────────────────────────────────────────────────────────────
# En-tête
# ─────────────────────────────────────────────────────────────────────────────

st.title("Simulation : Achat vs Location + Stratégie")
st.caption(
    f"Résidence principale · France · Flat tax 30 % sur gains portefeuille · "
    f"Plus-value résidence principale exonérée · Horizon {annee_depart}–{annee_depart + horizon_ans}"
)

# ─── Bannière viabilité ───────────────────────────────────────────────────────

if not res["viable"]:
    st.markdown(
        f"""<div class="warn-banner">
        ⚠️ <b>Scénario achat non viable</b> — Le coût mensuel initial
        (<b>{res['cout_initial']:,.0f} €/mois</b>) dépasse le budget alloué
        (<b>{budget_mensuel:,.0f} €/mois</b>).
        Avec ces paramètres, le prix maximum finançable est
        <b>{res['max_bien']:,.0f} €</b>.
        Réduisez le prix du bien, augmentez l'apport ou allongez la durée.
        </div>""",
        unsafe_allow_html=True,
    )
else:
    delta_init = budget_mensuel - res["cout_initial"]
    st.markdown(
        f"""<div class="ok-banner">
        ✅ <b>Scénario achat viable</b> —
        Mensualité <b>{res['mensualite']:,.0f} €</b>
        + assurance <b>{res['assurance_init']:,.0f} €</b>
        + charges <b>{res['charges_init']:,.0f} €</b>
        = <b>{res['cout_initial']:,.0f} €/mois</b>.
        Delta investi en stratégie (an 1) : <b>{delta_init:,.0f} €/mois</b>.
        Prix max finançable : <b>{res['max_bien']:,.0f} €</b>.
        </div>""",
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
# Toggle euros constants / courants  (doit précéder les KPIs)
# ─────────────────────────────────────────────────────────────────────────────

reel = st.toggle(
    "Afficher en euros constants (pouvoir d'achat d'aujourd'hui, corrigés de l'inflation)",
    value=False,
    help=(
        "**Euros courants** : montants nominaux tels qu'ils seront encaissés/décaissés. "
        "**Euros constants** : tous les montants ramenés au pouvoir d'achat de l'année d'achat "
        "en divisant par le facteur d'inflation cumulé. Permet une comparaison économique réelle. "
        "Affecte les indicateurs ET les graphes."
    ),
)

# ─────────────────────────────────────────────────────────────────────────────
# KPI strip
# ─────────────────────────────────────────────────────────────────────────────

pat_col = "patrimoine_net_reel" if reel else "patrimoine_net_nominal"
annee_fin = annee_depart + horizon_ans
pat_A = df_A.iloc[-1][pat_col] if not df_A.empty else 0.0
pat_B = df_B.iloc[-1][pat_col] if not df_B.empty else 0.0
diff_pat = pat_A - pat_B
cum_int = df_A.iloc[-1]["cum_interets"] if not df_A.empty else 0.0
cout_A = df_A.iloc[-1]["cum_cout"] if not df_A.empty else 0.0
cout_B = df_B.iloc[-1]["cum_cout"] if not df_B.empty else 0.0
unite = "€ constants" if reel else "€ courants"

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        f"""<div class="kpi-card">
        <div class="kpi-label">Patrimoine Achat {annee_fin}</div>
        <div class="kpi-value" style="color:#2563EB">{pat_A:,.0f} €</div>
        <div class="kpi-sub">equity + portefeuille net flat tax · {unite}</div>
        </div>""",
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        f"""<div class="kpi-card">
        <div class="kpi-label">Patrimoine Location {annee_fin}</div>
        <div class="kpi-value" style="color:#16A34A">{pat_B:,.0f} €</div>
        <div class="kpi-sub">portefeuille net de flat tax · {unite}</div>
        </div>""",
        unsafe_allow_html=True,
    )

with col3:
    color = "#2563EB" if diff_pat >= 0 else "#16A34A"
    label = "Avantage Achat" if diff_pat >= 0 else "Avantage Location"
    st.markdown(
        f"""<div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value" style="color:{color}">{abs(diff_pat):,.0f} €</div>
        <div class="kpi-sub">différentiel · {unite}</div>
        </div>""",
        unsafe_allow_html=True,
    )

with col4:
    st.markdown(
        f"""<div class="kpi-card">
        <div class="kpi-label">Intérêts crédit payés</div>
        <div class="kpi-value" style="color:#EF4444">{cum_int:,.0f} €</div>
        <div class="kpi-sub">coût total du crédit</div>
        </div>""",
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Onglets
# ─────────────────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Patrimoine net",
    "💸 Mensualités & Coûts",
    "🏦 Amortissement",
    "📈 Portefeuille stratégie",
    "📋 Données",
])

# ── Tab 1 : Patrimoine ────────────────────────────────────────────────────────
with tab1:
    st.plotly_chart(
        chart_patrimoine(df_A, df_B, reel=reel),
        use_container_width=True,
    )

    with st.expander("ℹ️ Comment lire ce graphe ?"):
        st.markdown("""
**Scénario Achat (bleu)**
Patrimoine = Valeur du bien appréciée + Portefeuille stratégie (net de flat tax).
La plus-value sur la résidence principale est **exonérée** d'impôts en France
(CGI art. 150 U II 1°), sous réserve que le bien soit la résidence principale au
moment de la vente. La valeur du bien est donc comptée à 100 % dans le patrimoine.

**Scénario Location + Stratégie (vert)**
Patrimoine = Portefeuille stratégie uniquement (net de flat tax).
Le capital de départ entier est investi dès J0. Chaque mois, la différence
entre le budget alloué et le loyer revalorisé est investie dans la stratégie.

**Flat tax (PFU 30 %)**
Appliquée sur les gains du portefeuille *à la liquidation* (fin de l'horizon simulé).
PFU = 12.8 % IR + 17.2 % prélèvements sociaux. Pour un PEA (> 5 ans), seuls
les 17.2 % PS s'appliquent — la simulation retient le cas général (CTO).

**Break-even (ligne orange)**
Première année où le patrimoine net de l'acheteur dépasse celui du locataire-investisseur.
        """)

# ── Tab 2 : Mensualités ───────────────────────────────────────────────────────
with tab2:
    st.plotly_chart(chart_mensualites(df_A, df_B), use_container_width=True)
    st.plotly_chart(chart_couts_cumules(df_A, df_B), use_container_width=True)

    c1, c2 = st.columns(2)
    c1.metric(
        f"Cash total sorti — Achat sur {horizon_ans} ans",
        f"{cout_A:,.0f} €",
        help="Somme de toutes les mensualités, assurances, charges et taxes foncières sur l'horizon.",
    )
    c2.metric(
        f"Loyers cumulés — Location sur {horizon_ans} ans",
        f"{cout_B:,.0f} €",
        help="Somme de tous les loyers payés, revalorisés à l'inflation, sur l'horizon.",
    )

    with st.expander("ℹ️ Inflation & mensualité fixe — l'avantage de l'endettement"):
        st.markdown(f"""
La mensualité de crédit est **fixe en euros courants** ({res['mensualite']:,.0f} €/mois).
Avec une inflation à {inflation*100:.1f} %/an, son poids **réel** dans votre budget diminue
d'environ {inflation*100:.1f} % par an — soit une économie réelle cumulée significative sur {duree_credit} ans.

À l'inverse, le loyer est **revalorisé chaque année** selon l'IRL (Indice de Référence des Loyers),
qui suit l'inflation. Son coût nominal augmente, mais son coût réel reste stable.

Le graphe des deltas (pointillés) montre ce qui est effectivement investi chaque mois dans
la stratégie dans chaque scénario. Pour le scénario achat, ce delta augmente en termes réels
au fil du temps (la mensualité pèse moins dans un budget qui suit l'inflation).
        """)

# ── Tab 3 : Amortissement ─────────────────────────────────────────────────────
with tab3:
    if res["viable"] and not df_A.empty:
        st.plotly_chart(chart_amortissement(df_A), use_container_width=True)

        with st.expander("ℹ️ Lecture du tableau d'amortissement"):
            st.markdown(f"""
**Equity immobilière (bleu foncé)**
= Valeur du bien appréciée − Capital restant dû.
C'est la part du bien qui vous appartient réellement. Elle augmente à la fois avec
le remboursement du capital et avec l'appréciation du bien ({appreciation_immo*100:.1f} %/an).

**Capital restant dû (bleu clair)**
Ce que vous devez encore à la banque. La somme des deux barres = valeur totale du bien.

**Intérêts cumulés (ligne rouge pointillée — axe droit)**
Au début du crédit, la quasi-totalité de la mensualité est constituée d'intérêts
(mécanique des annuités constantes). Le poids des intérêts diminue chaque mois
à mesure que le capital restant dû baisse.

Capital emprunté : **{res['capital_emprunt']:,.0f} €**
Mensualité fixe : **{res['mensualite']:,.0f} €/mois**
Durée : **{duree_credit} ans** · Intérêts totaux estimés : **{cum_int:,.0f} €**
            """)
    else:
        st.info("Scénario achat non viable avec les paramètres actuels.")

# ── Tab 4 : Portefeuille ──────────────────────────────────────────────────────
with tab4:
    st.plotly_chart(chart_portefeuille(df_A, df_B), use_container_width=True)

    with st.expander("ℹ️ Mécanique du portefeuille dans chaque scénario"):
        st.markdown(f"""
**Scénario Achat**
Capital initial investi : capital de départ − apport = **{capital_depart - apport:,.0f} €**
Contributions mensuelles : budget − (mensualité + assurance + charges)
Après remboursement du crédit ({annee_depart + duree_credit}) : les contributions mensuelles
augmentent fortement (plus de mensualité à payer), ce qui crée un effet d'accélération visible.

**Scénario Location**
Capital initial investi : **{capital_depart:,.0f} €** (totalité du capital de départ)
Contributions mensuelles : budget − loyer revalorisé = **{budget_mensuel - loyer:,.0f} €/mois** à l'an 1

**Flat tax — méthode de calcul**
La flat tax est calculée à la liquidation finale sur : *gain = valeur finale − cost basis*.
Le cost basis est réduit proportionnellement lors de chaque retrait éventuel
(méthode légale française pour le PFU). Taux : 30 % (12.8 % IR + 17.2 % PS).

💡 Si vous investissez via un **PEA** (plafond 150 k€) détenu depuis plus de 5 ans,
seuls les 17.2 % de prélèvements sociaux s'appliquent — la simulation retient le cas
général (compte-titres ordinaire).
        """)

# ── Tab 5 : Données ───────────────────────────────────────────────────────────
with tab5:
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Scénario Achat", divider="blue")
        if not df_A.empty:
            disp_A = df_A[[
                "annee", "bien_value", "cap_restant_du", "equity_immo",
                "portfolio_net", "flat_tax", "patrimoine_net_nominal",
                "cout_mensuel", "delta_mensuel", "cum_interets",
            ]].copy()
            disp_A.columns = [
                "Année", "Valeur bien", "Cap. restant dû", "Equity immo",
                "Portef. net", "Flat tax", "Patrimoine net",
                "Coût mensuel", "Delta → Strat.", "Intérêts cumulés",
            ]
            st.dataframe(
                disp_A.style.format("{:,.0f}", subset=disp_A.columns[1:]),
                use_container_width=True, height=420,
            )

    with col_b:
        st.subheader("Scénario Location", divider="green")
        if not df_B.empty:
            disp_B = df_B[[
                "annee", "portfolio_net", "flat_tax",
                "patrimoine_net_nominal", "loyer_nominal", "delta_mensuel",
            ]].copy()
            disp_B.columns = [
                "Année", "Portef. net", "Flat tax",
                "Patrimoine net", "Loyer mensuel", "Delta → Strat.",
            ]
            st.dataframe(
                disp_B.style.format("{:,.0f}", subset=disp_B.columns[1:]),
                use_container_width=True, height=420,
            )

    st.divider()
    st.subheader("Paramètres de la simulation")
    params_display = {
        "Valeur du bien": f"{valeur_bien:,.0f} €",
        "Frais d'agence": f"{frais_agence:,.0f} €",
        "Frais de notaire": f"{frais_notaire:,.0f} €",
        "Capital emprunté": f"{res['capital_emprunt']:,.0f} €",
        "Apport": f"{apport:,.0f} €",
        "Taux crédit": f"{taux_credit*100:.2f} %/an",
        "Durée crédit": f"{duree_credit} ans",
        "Assurance emprunteur": f"{taux_assurance*100:.2f} %/an",
        "Loyer": f"{loyer:,.0f} €/mois",
        "Charges proprio": f"{impots_fonciers + charges_diverses:,.0f} €/an",
        "Budget mensuel alloué": f"{budget_mensuel:,.0f} €/mois",
        "Capital de départ": f"{capital_depart:,.0f} €",
        "Rendement stratégie": f"{rendement_strategie*100:.1f} %/an",
        "Appréciation immo": f"{appreciation_immo*100:.1f} %/an",
        "Inflation": f"{inflation*100:.1f} %/an",
        "Flat tax": "30 % (PFU)",
        "PV résidence principale": "Exonérée (CGI art. 150 U II 1°)",
        "Horizon": f"{horizon_ans} ans ({annee_depart} → {annee_depart + horizon_ans})",
    }
    st.json(params_display)
