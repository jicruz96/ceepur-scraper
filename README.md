# ceepur-scraper

Un programa para extraer todos los datos públicos del registro electoral de Puerto Rico, accesibles a través de [https://consulta.ceepur.org/](https://consulta.ceepur.org/).

El programa toma alrededor de 5 horas para bajar todos los datos posibles.

```bash
pip install ceepur-scraper
```

## Uso

Para correr el scraper, simplemente ejecute lo siguiente en tu terminal luego de instalar el paquete:

```bash
ceepur-scraper
```

Utiliza la opción `--help` para ver todas las opciones disponibles:

```bash
$ ceepur-scraper --help
usage: ceepur-scraper [-h] [--output OUTPUT_FILENAME] [--max-id MAX_ID] [--min-id MIN_ID]
                      [--reverse] [--max-concurrent-tasks MAX_CONCURRENT_TASKS]
                      [--continue-previous-scrape] [--save-descriptions] [--debug]

optional arguments:
  -h, --help            show this help message and exit
  --output OUTPUT_FILENAME, -o OUTPUT_FILENAME
                        The filename to write the scraped voter records to. Defaults to
                        voter_records.csv.
  --max-id MAX_ID       The maximum voter ID to scrape. Cannot be greater than 9,999,999.
  --min-id MIN_ID       The minimum voter ID to scrape. Cannot be less than 1.
  --reverse             Whether to scrape in reverse order.
  --max-concurrent-tasks MAX_CONCURRENT_TASKS
                        The maximum number of concurrent tasks to run. Defaults to 500.
  --continue-previous-scrape, -c
                        Whether to continue a previous scrape that was interrupted.
  --save-descriptions   Whether to save the descriptions of the voter's status and category. ⚠️
                        WARNING: This will significantly increase the size of the output file.
  --debug, -d           Run in debug mode.
```


Esto producirá un archivo llamado `voter_records.csv` en el directorio actual que se parecerá a esta tabla:

| `NumeroElectoral` | `Category` | `FechaNacimiento` | `Precinto` | `Status` | `Unidad` |
| ----------------- | ---------- | ----------------- | ---------- | -------- | -------- |
| `4980113`         | `1`        | `22-10-1926`      | `1`        | `E`      | `2`      |


### Descripción de `Category` y `Status`

El campo `Category` es un solo caracter.

Su significado depende del valor de `Status`.

Consulte la próxima sección para ver el significado de cada categoría.

#### Alternativamente puedes correr el scraper con la opción `--save-descriptions` para guardar una descripción de cada categoría en el archivo final (⚠️ ¡Esto aumentará el tamaño del archivo significativamente!).

<details>
<summary>Haz click para expandir...</summary>

El `Status` de un elector puede ser:

* `A`: Activo
* `I`: Inactivo
* `E`: Excluido

El campo `Category` da más información acerca del `Status` de un elector:

* Para electores con status `A`, el campo `Category` puede ser:
    * `1`: `VOTÓ EN NOVIEMBRE DE 2020`
    * `2`: `NO VOTÓ EN NOVIEMBRE DE 2020`
    * `3`: `INGRESÓ POR MEDIO DE NUEVA INSCRIPCIÓN`
    * `4`: `INGRESO POR MEDIO DE INSCRIPCIÓN ESPECIAL (Reactivación)`
    * `5`: `INGRESO POR MEDIO DE INCLUSIÓN (Administrativa)`
* Para electores con status `I`, el campo `Category` puede ser:
    * `1`: `INACTIVO EN LA DEPURACIÓN DE LISTAS POSTERIOR A LAS ELECCIONES GENERALES DE 1980`
    * `2`: `INACTIVO EN LA DEPURACIÓN DE LISTAS POSTERIOR A LAS ELECCIONES GENERALES DE 1984`
    * `3`: `INACTIVO EN LA DEPURACIÓN DE LISTAS POSTERIOR A LAS ELECCIONES GENERALES DE 1988`
    * `4`: `INACTIVO EN LA DEPURACIÓN DE LISTAS POSTERIOR A LAS ELECCIONES GENERALES DE 1992`
    * `5`: `INACTIVO EN LA DEPURACIÓN DE LISTAS POSTERIOR A LAS ELECCIONES GENERALES DE 1996`
    * `6`: `INACTIVO EN LA DEPURACIÓN DE LISTAS POSTERIOR A LAS ELECCIONES GENERALES 2000`
    * `7`: `INACTIVO EN LA DEPURACIÓN DE LISTAS POSTERIOR A LAS ELECCIONES GENERALES 2004`
    * `8`: `INACTIVO EN LA DEPURACIÓN DE LISTAS POSTERIOR A LAS ELECCIONES GENERALES 2008`
    * `9`: `INACTIVO EN LA DEPURACIÓN DE LISTAS POSTERIOR A LAS ELECCIONES GENERALES 2012`
    * `A`: `INACTIVO EN LA DEPURACIÓN DE LISTAS POSTERIOR A LAS ELECCIONES GENERALES 2020`
* Para electores con status `E`, el campo `Category` puede ser:
  * `A`: `EXCLUSIÓN ADMINISTRATIVA`
  * `C`: `NO ES CIUDADANO AMERICANO`
  * `D`: `DUPLICADO`
  * `E`: `NO TIENE 18 AÑOS DE EDAD`
  * `M`: `MUERTE`
  * `P`: `NO ES PERSONA EN PETICIÓN`
  * `R`: `NO ES RESIDENTE DEL PRECINTO`
  * `T`: `INCAPACITADO MENTAL`

</details>


### ¿Qué hacer si hay un error?

Puedes intentar de recorrer un "scrape" con la opción `--continue-previous-scrape` (o `-c`) para intentar continuar el scrape desde donde se quedó.

Si todavía hay fallos, usa la opción `--debug` (o `-d`) para ver el error completo. Si no sabes como resolverlo, [abre un issue](https://github.com/jicruz96/ceepur-scraper/issues/new) en este repositorio.

## Ejemplo

```bash
# Descargar electores 1-100 y guardar en "resultados.csv", incluyendo descripciones de categorías
ceepur-scraper --output resultados.csv --min-id 1 --max-id 100 --save-descriptions
```
