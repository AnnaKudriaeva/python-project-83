### Hexlet tests and linter status:
[![Actions Status](https://github.com/AnnaKudriaeva/python-project-83/actions/workflows/hexlet-check.yml/badge.svg)](https://github.com/AnnaKudriaeva/python-project-83/actions)
[![Maintainability](https://api.codeclimate.com/v1/badges/663ae78156db3ffdcfd3/maintainability)](https://codeclimate.com/github/AnnaKudriaeva/python-project-83/maintainability)


The Page Analyzer is a website that analyzes the specified pages for SEO suitability.
In case the site is available, we get its: 
- response code
- `<h1>` tag;
- `<title>` tag;
- `<meta name="description" content="...">` tag.
The project is based on **Flask**: HTTP-requests and routing. The results of the checks are recorded in the database.

## Instalation

```sh
git clone <package>
pip install poetry
make install
```