# Guía de la planilla de datos

Toda la parte "biológica" del juego se edita en una planilla. No hace falta tocar código ni el repo.

## Cómo se usa

1. Abrí `docs/bloodline_data.xlsx` (o pedile a Santi el link de la Google Sheet ya importada).
2. Si usás Google Sheets: **Archivo → Importar** el `.xlsx`, editá y compartila como **"Cualquier persona con el enlace: Lector"**.
3. Pasale el link a Santi. Él corre:
   ```bash
   python scripts/sheet_sync.py import --sheet-id <ID>
   ```
   El script valida todo antes de guardar. Si algo está mal, te dice qué.

No cambies los nombres de las pestañas ni de las columnas.

## Pestañas

### `genes`

Una fila por gen. Todos son genes con dos alelos: uno **dominante** (A) y uno **recesivo** (a).

| Columna | Qué es |
|---|---|
| `id` | Identificador corto, sin espacios (`d1`, `eyes`...). No cambiar los de los genes cosméticos. |
| `kind` | `disease` (enfermedad) o `cosmetic` (rasgo visible en el dibujo). |
| `name_es`, `name_en` | Nombre que ve el jugador en cada idioma. |
| `recessive_freq` | **q**: frecuencia del alelo recesivo en la población (entre 0 y 1). Para enfermedades es el alelo de la enfermedad. |
| `trait` | Solo cosméticos: qué parte del dibujo controla (`eyes`, `hair`, `freckles`). |
| `dominant`, `recessive` | Solo cosméticos: valor del rasgo con al menos una copia dominante, y con dos copias recesivas. |

Valores disponibles para el dibujo:
- `eyes`: `brown`, `blue`, `green`
- `hair`: `black`, `brown`, `blond`, `red`
- `freckles`: `TRUE` / `FALSE`

**Cómo elegir q para las enfermedades.** Con frecuencia q, en la población hay p² sanos sin copias, 2pq portadores y q² enfermos (Hardy-Weinberg, p = 1 − q). Con los valores actuales (0.30, 0.25, 0.35), un árbol armado al azar tiene ≈25% de riesgo, lo que hace el juego desafiante. Si suben q, el juego se pone más difícil.

### `game`

| Clave | Qué es |
|---|---|
| `generations` | 3 = bisabuelos (no cambiar por ahora). |
| `candidates_per_sex` | Candidatos de cada sexo por partida. |
| `tests_per_game` | Tests genéticos gratis. |
| `test_scope` | `single_disease` (cada test revela una enfermedad) o `all` (revela todas). |
| `siblings_min`, `siblings_max` | Cantidad de hermanos simulados para las pistas. |
| `fun_fact_probability` | Probabilidad de que la pista sea una anécdota en vez de un dato familiar. |
| `ranking_min_games` | Partidas mínimas para aparecer en el ranking de % y de riesgo. |

### `skin_tones`

Probabilidad de cada tono de piel en los bisabuelos (`light`, `medium`, `tan`, `dark`). Tienen que sumar 1. En esta versión la piel no es genética: cada hijo hereda la de uno de sus padres al azar.

### `names`

Nombres de mujer, de hombre y apellidos para los bisabuelos. Hace falta al menos `candidates_per_sex` nombres de cada sexo.

### `fun_facts`

Anécdotas graciosas en español y en inglés. No dan información genética.

## Las pistas de las cartas

Las pistas familiares **siempre son verdaderas**: el juego simula a los padres y hermanos de cada candidato con el mismo modelo genético y cuenta lo que pasó. Por ejemplo:

- "Su madre tenía la Enfermedad 2" → el candidato tiene al menos una copia (si está sano, es portador seguro).
- "2 de sus 4 hermanos tenían la Enfermedad 1" → sus padres eran portadores, así que si el candidato está sano tiene 2/3 de chances de ser portador.
