# SYNOPSIS for isitfit

## `isitfit  --help`

```
Usage: isitfit [OPTIONS] COMMAND [ARGS]...

Options:
  --debug              Display more details to help with debugging
  --optimize           DEPRECATED: use "isitfit cost optimize" instead
  --version            DEPRECATED: use "isitfit version" instead
  --share-email TEXT   Share result to email address
  --skip-check-update  Skip step for checking for update
  --help               Show this message and exit.

Commands:
  cost     Evaluate AWS EC2 costs
  tags     Explore EC2 tags
  version  Show isitfit version
```


## `isitfit version --help`

```
Usage: isitfit version [OPTIONS]

  Show isitfit version

Options:
  --help  Show this message and exit.
```


## `isitfit cost --help`

```
Usage: isitfit cost [OPTIONS] COMMAND [ARGS]...

  Evaluate AWS EC2 costs

Options:
  --help  Show this message and exit.

Commands:
  analyze   Analyze AWS EC2 cost
  optimize  Generate recommendations of optimal EC2 sizes
```


## `isitfit cost optimize --help`

```
Usage: isitfit cost optimize [OPTIONS]

  Generate recommendations of optimal EC2 sizes

Options:
  --n INTEGER         number of underused ec2 optimizations to find before
                      stopping. Skip to get all optimizations
  --filter-tags TEXT  filter instances for only those carrying this value in
                      the tag name or value
  --help              Show this message and exit.
```


## `isitfit cost analyze --help`

```
Usage: isitfit cost analyze [OPTIONS]

  Analyze AWS EC2 cost

Options:
  --filter-tags TEXT  filter instances for only those carrying this value in
                      the tag name or value
  --help              Show this message and exit.
```


## `isitfit tags --help`

```
Usage: isitfit tags [OPTIONS] COMMAND [ARGS]...

  Explore EC2 tags

Options:
  --help  Show this message and exit.

Commands:
  dump     Dump existing EC2 tags in tabular form into a csv file
  push     Push EC2 tags from csv file
  suggest  Generate new tags suggested by isitfit for each EC2 instance
```


## `isitfit tags dump --help`

```
Usage: isitfit tags dump [OPTIONS]

  Dump existing EC2 tags in tabular form into a csv file

Options:
  --help  Show this message and exit.
```


## `isitfit tags suggest --help`

```
Usage: isitfit tags suggest [OPTIONS]

  Generate new tags suggested by isitfit for each EC2 instance

Options:
  --advanced  Get advanced suggestions of tags. Requires login
  --help      Show this message and exit.
```


## `isitfit tags push --help`

```
Usage: isitfit tags push [OPTIONS] CSV_FILENAME

  Push EC2 tags from csv file

Options:
  --not-dry-run  True for dry run (simulated push)
  --help         Show this message and exit.
```


