# DammBuy — Contexto de producto e implementación

## 1. Contexto del hackathon

Estamos participando en el **Damm x Engineering HUB Hackathon 2026** y hemos decidido trabajar en el reto **DammBuy**, orientado al área de Compras.

El reto consiste en construir una herramienta que ayude a decidir si conviene:

- **comprar**,
- **esperar**,
- **cubrirse**,
- o **seguir monitorizando**,

para materias primas clave como:

- **aluminio**,
- **PET / vPET / rPET**,
- **energía**,
- **cebada**.

La herramienta debe combinar datos internos, datos estructurados de **Cala.ai** y fuentes externas para generar recomendaciones explicables, respaldadas por evidencias y útiles para la toma de decisiones.

El objetivo no es hacer un dashboard descriptivo ni una predicción exacta de precios. El objetivo es construir un **motor de decisión de compras**.

---

## 2. Concepto del producto

Nombre provisional:

# DammBuy

Frase de producto:

> DammBuy convierte precios, eventos, regulación, geopolítica, inventarios, energía, clima y señales externas en recomendaciones accionables para Compras: comprar, esperar, cubrirse o monitorizar.

Frase para la demo:

> Compras consulta muchas fuentes separadas. DammBuy las convierte en señales comparables, calcula un score de riesgo y genera una recomendación explicable con evidencias trazables.

---

## 3. Decisión estratégica

Hemos decidido apostar por **DammBuy**.

La razón es que, aunque MarketPulse era una opción más directa, DammBuy tiene más potencial diferencial y visual si se plantea como un cockpit de inteligencia de mercado.

La clave es no plantearlo como:

> “Una app que pregunta cosas a Cala.ai y muestra la respuesta.”

Sino como:

> “Un sistema que usa Cala.ai como capa de conocimiento estructurado, normaliza señales externas, calcula scores y genera recomendaciones de compra explicables.”

---

## 4. Papel de Cala.ai

Tenemos acceso a **Cala.ai Scale**, con 50.000 requests.

La skill de Cala indica que no debería usarse principalmente como un buscador genérico en lenguaje natural. Cala funciona mejor como una API de conocimiento estructurado.

Por tanto, hay que evitar depender de queries abiertas tipo:

```text
Find events in the last 90 days that could increase European aluminium prices.
```

Este tipo de query puede servir para exploración, pero no es la base ideal para una implementación robusta porque puede devolver resultados narrativos, difíciles de normalizar, con fechas ambiguas o sin schema estable.

### Uso correcto de Cala

Herramientas según la skill:

- `knowledge_query`: para queries estructuradas, filtros, listas y campos concretos.
- `knowledge_search`: para preguntas abiertas con citas, solo cuando haga falta.
- `entity_search`: para encontrar una entidad por nombre y obtener UUID.
- `retrieve_entity`: para recuperar propiedades concretas de una entidad.
- `entity_introspection`: para descubrir qué campos o relaciones existen en una entidad.

### Pipeline deseado con Cala

```text
Definir commodities y drivers
        ↓
Buscar entidades relevantes en Cala
        ↓
Hacer queries estructuradas por commodity y driver
        ↓
Normalizar resultados a un schema propio de señales
        ↓
Guardar señales en JSON / CSV / SQLite local
        ↓
Calcular scores y recomendaciones
        ↓
Mostrar cockpit interactivo
```

La demo debe funcionar con datos locales preprocesados aunque Cala falle o vaya lento durante la presentación.

---

## 5. Arquitectura conceptual

```text
Cala.ai / fuentes externas / dataset cebada
        ↓
Signal extraction pipeline
        ↓
Normalized Signal Lake
        ↓
Decision Engine
        ↓
Interactive DammBuy UI
```

Capas:

1. **Data acquisition**
   - Cala.ai.
   - Dataset de cebada.
   - Fuentes externas o datos mock/seed realistas si hace falta.

2. **Signal normalization**
   - Convertir todo a un schema común.

3. **Decision engine**
   - Calcular risk score, confidence, action, coverage y horizon.

4. **UI**
   - Procurement Radar.
   - Commodity Detail.
   - Evidence Board.
   - What-if Simulator.
   - Action Plan.

---

## 6. Dataset de cebada

Nos han proporcionado un dataset específico para cebada: `ordi_train_public.csv`.

Este dataset **sí debe usarse**, aunque sea solo para la materia prima cebada, porque aporta una capa cuantitativa real que diferencia cebada del resto de commodities.

### Inspección inicial del dataset

El fichero tiene:

- **Filas:** 1036
- **Columnas:** `['ds', 'y', 'covid']`
- **Rango temporal:** 2006-01-01 a 2025-11-02
- **Frecuencia:** weekly (7 days)
- **Variable `y`:**
  - mínimo: 124.000
  - máximo: 376.000
  - media: 197.993
- **Variable `covid`:**
  - valores con `covid = 1`: 68
  - rango aproximado covid: 2020-03-15 a 2021-06-27

### Interpretación prudente

Columnas detectadas:

| Columna | Interpretación probable | Cómo usarla |
|---|---|---|
| `ds` | fecha semanal | eje temporal |
| `y` | variable objetivo desconocida; probablemente precio, índice o valor de mercado de cebada | tratar como target cuantitativo de cebada |
| `covid` | flag de periodo COVID | feature explicativa / régimen especial |

Importante: **no sabemos con certeza qué representa `y`**. Por tanto, en código y en la demo conviene etiquetarla inicialmente como:

- `barley_target_value`,
- `barley_market_indicator`,
- o `barley_price_proxy`.

No llamarla “precio €/t” salvo que Damm confirme la unidad.

### Cómo usar el dataset de cebada

Para cebada, podemos añadir una capa cuantitativa específica:

- evolución histórica del valor `y`;
- momentum 4 semanas;
- momentum 12 semanas;
- media móvil corta vs larga;
- volatilidad reciente;
- z-score frente a histórico;
- detección de subidas o bajadas fuertes;
- forecast simple de corto plazo;
- comparación con señales externas de clima, cosecha, fertilizantes, exportaciones, etc.

Features sugeridas:

```text
barley_momentum_4w
barley_momentum_12w
barley_ma_4
barley_ma_12
barley_ma_26
barley_volatility_12w
barley_z_score
barley_covid_flag
barley_recent_trend
```

Target para modelo simple:

```text
target_up_4w = 1 si y dentro de 4 semanas > y actual + umbral
target_down_4w = 1 si y dentro de 4 semanas < y actual - umbral
```

Para el MVP basta con usarlo para alimentar:

```text
barley_quantitative_score
```

que luego se combina con señales externas:

```text
barley_final_score =
  0.50 * barley_quantitative_score +
  0.50 * barley_external_signal_score
```

Si no da tiempo a entrenar un modelo, usar reglas explicables:

```text
if momentum_12w > 0 and volatility high:
    aumentar risk_score
if y está muy por encima de media histórica:
    aumentar uncertainty o recomendar monitorizar
if y está bajando y señales externas son bajistas:
    recomendar esperar
```

---

## 7. Schema normalizado de señales

Cada señal debe transformarse a un formato común:

```json
{
  "id": "signal_001",
  "commodity": "aluminium",
  "driver": "energy",
  "event": "European power cost increase",
  "date": "2026-02-10",
  "region": "Europe",
  "direction": "bullish",
  "impact_score": 0.72,
  "confidence": 0.68,
  "horizon": "1-3 months",
  "source_name": "Cala / external source",
  "source_url": "https://...",
  "evidence": "Short explanation of the evidence",
  "mechanism": "Why this signal affects procurement prices",
  "used_in_score": true
}
```

Campos clave:

| Campo | Descripción |
|---|---|
| `commodity` | aluminium, PET, energy, barley |
| `driver` | energy, oil, PTA_MEG, weather, regulation, geopolitics, inventories, imports_exports, futures_prices, demand, supply |
| `direction` | bullish, bearish, neutral |
| `impact_score` | 0 a 1 |
| `confidence` | 0 a 1 |
| `horizon` | short_term, medium_term, long_term o texto |
| `source_name` | fuente |
| `source_url` | URL si existe |
| `mechanism` | explicación causal |
| `used_in_score` | si la señal entra en el cálculo |

---

## 8. Driver map

Todos los commodities comparten el mismo motor, pero con pesos distintos por driver.

| Driver | Aluminium | PET | Energy | Barley |
|---|---:|---:|---:|---:|
| energy | high | medium | high | low |
| oil | low | high | medium | low |
| PTA_MEG | low | high | low | low |
| weather | low | low | medium | high |
| regulation | medium | high | medium | medium |
| geopolitics | high | medium | high | medium |
| inventories | high | medium | high | high |
| imports_exports | high | high | medium | high |
| futures_prices | high | medium | high | medium |
| demand | medium | medium | medium | medium |
| supply | high | medium | high | high |

En código, convertir a pesos numéricos:

```json
{
  "high": 1.0,
  "medium": 0.6,
  "low": 0.25,
  "none": 0.0
}
```

---

## 9. Decision Engine

No buscamos predecir precio exacto. Queremos generar:

- `risk_score`: 0–100.
- `opportunity_score`: 0–100, opcional.
- `confidence`: 0–100.
- `recommended_action`: buy, wait, hedge, monitor.
- `suggested_coverage`: 0%, 20–40%, 40–60%, 60–80%.
- `suggested_horizon`: 2 weeks, 1 month, 1–3 months, 3–6 months.
- top bullish drivers.
- top bearish drivers.
- explicación de negocio.

### External signal score

```text
external_signal_score = sum(
  direction_sign * impact_score * confidence * driver_weight
)
```

Donde:

```text
bullish = +1
bearish = -1
neutral = 0
```

### Risk score

Normalizar el score final a 0–100.

Ejemplo conceptual:

```text
risk_score = normalize(external_signal_score + quantitative_score)
```

Para cebada, añadir el dataset:

```text
barley_final_score =
  0.50 * barley_quantitative_score +
  0.50 * barley_external_signal_score
```

Para el resto:

```text
final_score =
  0.70 * external_signal_score +
  0.30 * price_or_market_proxy_score
```

si hay datos de precios, o solo external score si no los hay.

### Uncertainty score

La incertidumbre puede calcularse con:

- señales contradictorias;
- baja confianza media;
- número pequeño de señales;
- volatilidad elevada si hay serie temporal;
- dispersión de impactos.

Ejemplo:

```text
uncertainty_score =
  conflicting_signals_ratio * 0.4 +
  low_confidence_penalty * 0.3 +
  volatility_component * 0.3
```

### Reglas de recomendación

```text
If risk_score >= 75 and uncertainty is high:
    action = "hedge"
    coverage = "40-60%"
    horizon = "1-3 months"

If risk_score >= 75 and uncertainty is low/medium:
    action = "buy_or_hedge"
    coverage = "60-80%"
    horizon = "1-3 months"

If risk_score between 55 and 75:
    action = "hedge_partial" or "monitor"
    coverage = "20-40%"
    horizon = "2-4 weeks"

If risk_score between 40 and 55:
    action = "monitor"
    coverage = "0-20%"
    horizon = "2 weeks"

If risk_score < 40:
    action = "wait"
    coverage = "0%"
    horizon = "review in 2-4 weeks"
```

---

## 10. Páginas de la app

La app debe parecer un cockpit de compras, no un Excel.

Flujo ideal:

```text
Home / Procurement Radar
        ↓
Commodity Detail
        ↓
Evidence Board
        ↓
What-if Simulator
        ↓
Action Plan
```

---

# Página 1 — Home / Procurement Radar

## Objetivo

Dar una vista ejecutiva de las cuatro materias primas y priorizar dónde debe mirar Compras primero.

Debe responder:

> ¿Qué commodity requiere atención hoy?

## Qué se ve

Arriba:

- DammBuy Decision Cockpit.
- Fecha de última actualización.
- Estado general del mercado: Stable / Watch / High Risk.
- Número de señales nuevas en últimas 24/48/72 horas.

Cards por commodity:

| Commodity | Recomendación | Riesgo subida | Confianza | Horizonte | Top driver |
|---|---|---:|---:|---|---|
| Aluminium | Hedge 40–60% | Alto | 74% | 1–3M | Energy + supply |
| PET | Monitorizar | Medio | 61% | 2–4W | Oil / PTA |
| Energy | Comprar parcial | Alto | 69% | 1M | Gas + weather |
| Barley | Esperar / monitorizar | Medio | 58% | 4–6W | Weather + dataset trend |

Visuales:

- semáforo por commodity;
- mini sparkline de score reciente;
- badge de acción recomendada;
- ranking “Top risks today”;
- alerta si una commodity cambió de recomendación.

## Interacciones

- Click en commodity para abrir detalle.
- Filtro por horizonte: 1M / 3M / 6M.
- Toggle: risk view / opportunity view.
- Botón: “What changed since last update?”

## Casos de uso

### Caso 1: reunión diaria de compras

El comprador abre la app y ve que aluminium y energy tienen el mayor riesgo. Prioriza esas materias primas en la reunión.

### Caso 2: dirección necesita una foto rápida

Dirección quiere saber dónde está el riesgo. La home muestra el ranking de riesgo y la recomendación de acción.

### Caso 3: detección de cambios

Ayer PET estaba en “wait” y hoy pasa a “monitor”. La app destaca el cambio y el driver que lo causó.

---

# Página 2 — Commodity Detail / Driver Breakdown

## Objetivo

Explicar por qué la app recomienda comprar, esperar, cubrirse o monitorizar una materia prima concreta.

Debe responder:

> ¿Por qué recomienda esto?

## Qué se ve

Cabecera:

```text
Aluminium
Recommendation: Hedge partially
Suggested coverage: 40–60%
Horizon: 1–3 months
Confidence: 74%
```

Bloques principales:

### A. Price & Risk Trend

Gráfico temporal con:

- precio o índice si existe;
- score DammBuy;
- media móvil;
- volatilidad;
- eventos anotados.

Para cebada, este gráfico debe usar `ordi_train_public.csv`:

- `ds` como fecha;
- `y` como indicador cuantitativo;
- `covid` como flag/regime marker.

### B. Bullish vs Bearish Forces

Visual tipo balanza:

Bullish pressure:

- energía europea;
- inventarios bajos;
- disrupción de oferta;
- regulación / aranceles.

Bearish pressure:

- demanda débil;
- importaciones;
- FX favorable;
- caída de precios proxy.

### C. Driver Contribution

Waterfall o barras:

| Driver | Contribución |
|---|---:|
| Energy | +18 |
| Supply disruption | +12 |
| Inventories | +15 |
| Demand | -10 |
| FX | -3 |

### D. Explanation Card

Texto claro:

> La recomendación de cobertura parcial se basa en presión alcista por energía e inventarios, compensada parcialmente por señales de demanda débil. La incertidumbre es elevada, por lo que se recomienda cubrir parcialmente en lugar de comprar toda la exposición.

## Interacciones

- Cambiar horizonte.
- Filtrar señales alcistas/bajistas.
- Cambiar commodity desde dropdown.
- Click en driver para ver evidencias relacionadas.

## Casos de uso

### Caso 1: justificar una cobertura

Compras necesita explicar a Finanzas por qué cubrir aluminio. Esta página muestra que el score viene de energía, inventarios y disrupciones de oferta.

### Caso 2: entender una recomendación no obvia

El precio actual baja, pero la app recomienda cubrir porque las señales externas apuntan a riesgo alcista.

### Caso 3: analizar cebada con dato interno

Para cebada, el usuario ve la serie semanal del dataset y cómo el momentum reciente modifica el risk score.

---

# Página 3 — Evidence Board / Signal Traceability

## Objetivo

Mostrar las evidencias que alimentan la recomendación.

Debe responder:

> ¿De dónde sale esta recomendación?

## Qué se ve

Tabla de señales:

| Date | Commodity | Driver | Event | Direction | Impact | Confidence | Source | Used |
|---|---|---|---|---|---:|---:|---|---|
| 2026-02-10 | Aluminium | Energy | Power costs rising | Bullish | 0.72 | 0.68 | Cala/source | Yes |
| 2026-02-14 | PET | Oil/PTA | PTA pressure | Bullish | 0.61 | 0.64 | Cala/source | Yes |
| 2026-02-16 | Barley | Weather | Dry conditions | Bullish | 0.58 | 0.59 | Cala/source | Yes |

Cada fila expandible:

- resumen;
- mecanismo de impacto;
- fuente;
- fecha de extracción;
- horizonte;
- si se ha usado en el score.

Visuales adicionales:

- filtros por commodity;
- filtros por driver;
- timeline de señales;
- heatmap driver × commodity;
- contador bullish / bearish.

## Interacciones

- Buscar señales.
- Filtrar por commodity.
- Filtrar por fuente.
- Filtrar por impacto.
- Expandir evidencia.
- Marcar señal como relevante/no relevante.
- Recalcular score al activar/desactivar señales.

## Casos de uso

### Caso 1: auditoría interna

Un responsable quiere saber por qué la app recomienda comprar energía. Entra al Evidence Board y revisa fuentes, drivers y eventos.

### Caso 2: preparar comité de compras

El equipo extrae las cinco señales más importantes para justificar la recomendación semanal.

### Caso 3: validación experta

Un comprador experto detecta que una señal no aplica bien a Europa y la desactiva. El score se recalcula.

---

# Página 4 — What-if Simulator / Scenario Lab

## Objetivo

Permitir al usuario simular escenarios y ver cómo cambia la recomendación.

Debe ser el “wow moment” de la demo.

Debe responder:

> ¿Qué pasaría si cambia el mercado?

## Qué se ve

Selector:

```text
Commodity: Aluminium
Current recommendation: Hedge 40–60%
Current risk score: 74
```

Sliders / controles:

| Variable | Control |
|---|---|
| Energy cost shock | -20% a +30% |
| Oil shock | -20% a +30% |
| Supply disruption | none / mild / severe |
| Demand outlook | weak / neutral / strong |
| Inventory level | low / normal / high |
| FX impact | favorable / neutral / adverse |
| Geopolitical risk | low / medium / high |
| Weather risk | low / medium / high |
| Coverage already secured | 0% / 25% / 50% / 75% |

Resultado dinámico:

```text
New risk score: 86
Recommendation: Hedge 60–80%
Suggested horizon: 3 months
Reason: energy shock + supply disruption increase upside risk
```

Visuales:

- before vs after;
- score gauge;
- barras de impacto por variable;
- explicación automática.

## Interacciones

- Mover sliders.
- Guardar escenario.
- Comparar base / adverse / optimistic.
- Botón “Generate buying plan”.

## Casos de uso

### Caso 1: energía sube

Compras simula una subida del 15% en energía. El sistema pasa de cobertura 40–60% a 60–80%.

### Caso 2: disrupción de oferta

El comprador simula supply disruption severa y ve que conviene adelantar parte de la compra.

### Caso 3: cobertura ya asegurada

Si ya hay 50% cubierto, la app puede recomendar no comprar más y seguir monitorizando.

---

# Página 5 — Action Plan / Procurement Recommendation

## Objetivo

Convertir análisis en una decisión concreta y comunicable.

Debe responder:

> ¿Qué hacemos ahora?

## Qué se ve

Tabla priorizada:

| Priority | Commodity | Action | Coverage | Horizon | Reason | Confidence |
|---:|---|---|---|---|---|---:|
| 1 | Aluminium | Hedge partially | 40–60% | 1–3M | Supply + energy risk | 74% |
| 2 | Energy | Buy partial | 30–50% | 1M | Volatility + weather | 69% |
| 3 | PET | Monitor | — | 2W | Mixed signals | 61% |
| 4 | Barley | Monitor | — | 4W | Dataset trend + weather | 58% |

### Decision memo

Texto generado automáticamente:

> Esta semana DammBuy recomienda priorizar cobertura parcial en aluminio y energía. PET presenta señales mixtas y debería monitorizarse. Cebada muestra una señal cuantitativa moderada en el dataset, pero requiere confirmación con drivers externos de clima y cosecha.

### Follow-up triggers

Condiciones que cambiarían la recomendación:

- energía sube >10%;
- inventarios caen >15%;
- nueva restricción comercial;
- volatilidad supera umbral;
- cambio fuerte en `barley_market_indicator`;
- nueva señal climática adversa para cebada.

## Interacciones

- Exportar memo.
- Guardar decisión.
- Marcar acción como aprobada.
- Añadir comentario manual.
- Programar revisión.

## Casos de uso

### Caso 1: comité semanal

El equipo usa el Action Plan como resumen ejecutivo para decidir compras.

### Caso 2: trazabilidad

Se guarda la recomendación y las evidencias detrás de la decisión.

### Caso 3: seguimiento

Dos semanas después se compara la decisión con la evolución real del mercado.

---

## 11. MVP del hackathon

Prioridad de implementación:

1. Crear datos seed realistas basados en el schema de señales.
2. Leer y explotar `ordi_train_public.csv` para cebada.
3. Implementar decision engine.
4. Implementar Home / Procurement Radar.
5. Implementar Commodity Detail.
6. Implementar Evidence Board.
7. Implementar What-if Simulator.
8. Implementar Action Plan.
9. Integrar Cala.ai si da tiempo.
10. Asegurar que la demo funciona con datos locales.

La app debe ser robusta aunque las llamadas live a APIs fallen.

---

## 12. Estructura sugerida del repo

### Opción Python / Streamlit

```text
smartbuy/
  app.py
  requirements.txt
  README.md
  CONTEXT.md
  data/
    signals.json
    commodities.json
    scenarios.json
    ordi_train_public.csv
  src/
    decision_engine.py
    signal_schema.py
    cala_client.py
    normalization.py
    barley_model.py
    mock_data.py
    visualizations.py
  pages/
    1_Procurement_Radar.py
    2_Commodity_Detail.py
    3_Evidence_Board.py
    4_What_If_Simulator.py
    5_Action_Plan.py
  docs/
    challenge_brief.pdf
    cala_skill.md
```

### Opción React / Next

```text
smartbuy/
  app/
    page.tsx
    commodity/[id]/page.tsx
    evidence/page.tsx
    simulator/page.tsx
    action-plan/page.tsx
  components/
    CommodityCard.tsx
    RiskBadge.tsx
    DriverBreakdown.tsx
    EvidenceTable.tsx
    ScenarioControls.tsx
    ActionPlanTable.tsx
    BarleyTrendChart.tsx
  lib/
    decisionEngine.ts
    barleyModel.ts
    data.ts
    types.ts
    calaClient.ts
  data/
    signals.json
    commodities.json
    ordi_train_public.csv
```

---

## 13. Estilo visual

La app debe tener estética de:

- market intelligence cockpit;
- procurement command center;
- dashboard ejecutivo;
- moderno y visual;
- con cards, badges, semáforos y gráficos claros;
- no parecer Excel.

Inspiración:

- Bloomberg-like, pero más limpio.
- Risk cockpit.
- Executive decision dashboard.
- Procurement control tower.

Elementos visuales clave:

- risk cards;
- bullish vs bearish forces;
- waterfall de drivers;
- evidence table;
- sliders de escenarios;
- decision memo;
- sparklines;
- gauges;
- heatmaps.

---

## 14. Demo story

Narrativa recomendada:

1. “Compras consulta muchas fuentes separadas.”
2. “DammBuy convierte esas fuentes en señales comparables.”
3. Home: “Hoy el mayor riesgo está en aluminium y energy.”
4. Commodity Detail: “Entramos en aluminium y vemos recomendación de cobertura parcial.”
5. Driver Breakdown: “La presión viene de energía, inventarios y supply disruption.”
6. Evidence Board: “Cada señal tiene fuente, fecha, impacto y confianza.”
7. Barley: “Para cebada usamos además un dataset real semanal, aunque todavía tratamos `y` como indicador sin unidad confirmada.”
8. Simulator: “Si energía sube 15%, la recomendación pasa a cubrir 60–80%.”
9. Action Plan: “El sistema genera una recomendación lista para comité.”

---

## 15. Qué NO queremos

- No queremos un dashboard descriptivo.
- No queremos una app que simplemente pregunte a Cala y muestre texto.
- No queremos predecir precio exacto como objetivo principal.
- No queremos acotar a una sola commodity.
- No queremos depender de llamadas live a APIs durante la demo.
- No queremos lógica opaca sin explicación de drivers.
- No queremos afirmar que `y` del dataset de cebada es precio con unidad concreta si no está confirmado.

---

## 16. Qué SÍ queremos

- Producto funcional.
- Recomendaciones accionables.
- Explicabilidad por drivers.
- Evidencias trazables.
- Simulación interactiva.
- Cobertura de las cuatro commodities.
- Uso específico del dataset de cebada.
- Integración Cala diseñada de forma estructurada.
- Demo robusta con datos locales.
- Diseño visual fuerte y convincente.

---

## 17. Prompt sugerido para Codex modo plan

Pegar en Codex:

```text
Read the challenge brief, the Cala skill, and CONTEXT.md. Do not implement yet.

First produce a detailed implementation plan for the MVP of DammBuy.

Include:
1. recommended tech stack,
2. file structure,
3. data model,
4. signal schema,
5. decision engine logic,
6. how to use ordi_train_public.csv for barley,
7. pages/components,
8. implementation order,
9. demo risks and mitigations,
10. what can be mocked vs what must be real.

Important constraints:
- The app must cover aluminium, PET, energy and barley.
- The app must work with local preprocessed data even if Cala.ai is unavailable.
- Cala.ai should be used as a structured knowledge layer, not as a generic natural language search box.
- The barley dataset must be used, but the meaning/unit of column y is unknown, so treat it as a neutral target/market indicator unless confirmed.
- The solution must be actionable, explainable and visually interactive.
```
