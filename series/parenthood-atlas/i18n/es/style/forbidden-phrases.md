# Frases prohibidas — edición en español de *El atlas de la crianza*

Lista viva consumida por [`scripts/audit_manuscript.py`](../../../../../scripts/audit_manuscript.py) cuando `readability_targets.language: es`.
Cada frase entre comillas invertidas y comillas dobles se compara sin distinguir mayúsculas, solo como palabra o frase completa y solo en prosa
sin citar (se ignoran citas en bloque y diálogos entre comillas). Equivale en espíritu a `style/forbidden-phrases.md` (inglés).

## Violaciones epistémicas e instructivas universales
- `"debes"` / `"tienes que"` / `"hay que"` (tono instructivo o de autoayuda; solo se admite dentro de citas textuales)
- `"la ciencia dice"` / `"los estudios demuestran que"` / `"está científicamente probado"` (funde hallazgos empíricos con interpretación incondicional)
- `"daña de forma irreversible"` / `"arruina"` / `"destruye"` (alarmismo, determinismo)
- `"destino del desarrollo"` / `"destino parental"` (determinismo)

## Optimización y fabricación del hijo
- `"niño perfecto"` / `"hijo perfecto"` / `"niño ideal"` (narrativa de fabricación)
- `"crianza óptima"` / `"optimizar el desarrollo"` / `"optimizar a tu hijo"` (lógica de optimización)
- `"prueba cerebral de que"` / `"pruebas basadas en el cerebro"` (sensacionalismo neurocientífico)
- `"diseñado evolutivamente para"` / `"diseñado por la evolución"` (narración evolutiva sin evidencia)
- `"ventana crítica"` (salvo grado Alto y persistencia demostrada)

## Relleno y clichés de transición (calco del inglés y de la prosa de divulgación genérica)
- `"profundizar en"` / `"adentrarnos en"` / `"sumergirnos en"` (equivalentes de *delve*)
- `"tapiz"` / `"entramado de"` (cliché metafórico)
- `"cambia las reglas del juego"` / `"cambio de juego"` (*game changer*)
- `"papel crucial"` / `"papel fundamental"` / `"papel clave"` (*crucial role*)
- `"faro"` / `"baliza"` (*beacon*)
- `"testimonio de"` / `"es un testimonio"` (*testament*)
- `"en el vertiginoso mundo de"` / `"en el mundo actual"`

## Protocolo de revisión
Si aparece una frase prohibida, revisa para:
1. Calibrar la fuerza de la afirmación al grado de la ficha de evidencia OKF v0.2 (**demuestra** / **sugiere** / **se asocia con**).
2. Sustituir etiquetas deterministas por mecanismos concretos.
3. Volver al caso humano concreto.
